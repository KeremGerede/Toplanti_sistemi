"""Transkript kalite metrikleri (saf fonksiyonlar, model gerektirmez).

Amaç üç hata kaynağını ayrı ölçmek:
- STT: konuşmacıdan bağımsız WER.
- Diarization: konuşmacı sayısı, DER bileşenleri, sınır sapması, kısa tur yakalama.
- Alignment: referans segmentler (oracle diarization) üzerinde ürünün `attach_text` davranışı.

Referans (ground truth) biçimi: {"source_file", "speaker_count", "segments": [{speaker, start, end, text}]}.
Referans etiketleri serbesttir (A/B/...); hipotez etiketleri DER'in optimal eşlemesiyle referansa bağlanır.
"""

import re
import statistics

import jiwer
from pyannote.core import Annotation, Segment, Timeline
from pyannote.metrics.diarization import DiarizationErrorRate

from transcription.transcript import attach_text, build_transcript

SHORT_TURN_SECONDS = 1.5        # bundan kısa referans turları "kısa tur" sayılır
BOUNDARY_WINDOW_SECONDS = 0.5   # sınır sapması eşiği ve kayan kelime penceresi
STT_CATCH_MARGIN_SECONDS = 0.3  # kısa turda kelime aranırken referans zamanlarına eklenen pay
DER_COLLAR_SECONDS = 0.5        # pyannote'ta toplam genişlik: referans sınırlarının ±0.25 sn'si değerlendirilmez

_APOSTROPHES = "'’‘`"


def normalize_text(text: str) -> str:
    """Türkçe küçük harf, kesme işareti silinir ("Ahmet'in" → "ahmetin"), noktalama boşluk olur."""
    text = text.replace("I", "ı").replace("İ", "i").lower()
    text = re.sub(f"[{_APOSTROPHES}]", "", text)
    text = re.sub(r"[^\w\s]", " ", text)
    return " ".join(text.split())


def word_errors(reference: str, hypothesis: str) -> dict:
    """Normalize edilmiş metinler arasında kelime hataları. Referansta kelime yoksa `wer` None'dır."""
    ref, hyp = normalize_text(reference), normalize_text(hypothesis)
    n = len(ref.split())
    if ref or hyp:
        out = jiwer.process_words(ref, hyp)
        s, d, i = out.substitutions, out.deletions, out.insertions
    else:
        s = d = i = 0
    return {
        "reference_words": n,
        "substitutions": s,
        "deletions": d,
        "insertions": i,
        "wer": (s + d + i) / n if n else None,
    }


def stt_errors(reference: dict, words: list[dict]) -> dict:
    """STT hatası: konuşmacı ve eşlemeden bağımsız, tüm referans metni ile Whisper kelimeleri."""
    ref_text = " ".join(s["text"] for s in _by_time(reference["segments"]))
    return word_errors(ref_text, " ".join(w["text"] for w in words))


def speaker_mapping(reference: dict, hyp_segments: list[dict]) -> dict:
    """Hipotez etiketi → referans etiketi (DER'in optimal eşlemesi). Eşlenemeyen etiket '?' önekiyle kalır."""
    ref_ann, hyp_ann = _annotation(reference["segments"]), _annotation(hyp_segments)
    uem = _uem(reference["segments"] + hyp_segments)
    mapping = DiarizationErrorRate(collar=DER_COLLAR_SECONDS).optimal_mapping(ref_ann, hyp_ann, uem=uem)
    return {s["speaker"]: mapping.get(s["speaker"], f"?{s['speaker']}") for s in hyp_segments}


def diarization_errors(reference: dict, hyp_segments: list[dict]) -> dict:
    ref_ann, hyp_ann = _annotation(reference["segments"]), _annotation(hyp_segments)
    uem = _uem(reference["segments"] + hyp_segments)
    d = DiarizationErrorRate(collar=DER_COLLAR_SECONDS)(ref_ann, hyp_ann, uem=uem, detailed=True)
    total = d["total"]
    return {
        "reference_speakers": len(ref_ann.labels()),
        "hypothesis_speakers": len(hyp_ann.labels()),
        "der": d["diarization error rate"],
        "missed": d["missed detection"] / total,
        "false_alarm": d["false alarm"] / total,
        "confusion": d["confusion"] / total,
    }


def boundary_deviation(reference: dict, hyp_segments: list[dict], mapping: dict) -> dict:
    """Her referans konuşmacı değişimine en yakın hipotez değişiminin uzaklığı (sn)."""
    ref_changes = _change_points(reference["segments"], lambda s: s["speaker"])
    hyp_changes = _change_points(hyp_segments, lambda s: mapping[s["speaker"]])
    deviations = [min(abs(r - h) for h in hyp_changes) for r in ref_changes] if hyp_changes else []
    return {
        "reference_changes": len(ref_changes),
        "hypothesis_changes": len(hyp_changes),
        "median": round(statistics.median(deviations), 3) if deviations else None,
        "max": round(max(deviations), 3) if deviations else None,
        # hipotezde hiç değişim yoksa referanstaki tüm değişimler kaçırılmış sayılır
        "over_window": sum(d > BOUNDARY_WINDOW_SECONDS for d in deviations) if hyp_changes else len(ref_changes),
    }


def short_turns(reference: dict, hyp_segments: list[dict], words: list[dict], mapping: dict) -> dict:
    """Kısa referans turları diarization (doğru konuşmacı) ve STT (herhangi bir kelime) tarafından yakalandı mı?"""
    rows = []
    for turn in _by_time(reference["segments"]):
        if turn["end"] - turn["start"] >= SHORT_TURN_SECONDS:
            continue
        lo, hi = turn["start"] - STT_CATCH_MARGIN_SECONDS, turn["end"] + STT_CATCH_MARGIN_SECONDS
        rows.append({
            **_turn(turn),
            "diarization_caught": any(
                mapping[h["speaker"]] == turn["speaker"] and _overlap(h, turn) > 0 for h in hyp_segments
            ),
            "stt_caught": any(w["end"] > lo and w["start"] < hi for w in words),
        })
    return {
        "total": len(rows),
        "diarization_caught": sum(r["diarization_caught"] for r in rows),
        "stt_caught": sum(r["stt_caught"] for r in rows),
        "turns": rows,
    }


def assign_words(segments: list[dict], words: list[dict]) -> list[int | None]:
    """Ürünün eşleme kuralını (`attach_text`) kelime kelime uygular: atanan segment indeksi veya None."""
    indices = []
    for word in words:
        texts = [s["text"] for s in attach_text(segments, [word])]
        indices.append(next((i for i, text in enumerate(texts) if text), None))
    return indices


def oracle_alignment(reference: dict, words: list[dict]) -> dict:
    """Diarization kusursuz olsaydı (referans segmentler) mevcut eşleme kelimeleri doğru tura koyar mıydı?"""
    turns = _by_time(reference["segments"])
    oracle = [{"speaker": t["speaker"], "start": t["start"], "end": t["end"]} for t in turns]
    assigned = assign_words(oracle, words)
    ref_tokens = [set(normalize_text(t["text"]).split()) for t in turns]

    aligned: list[list[str]] = [[] for _ in turns]
    shifted = []
    for word, i in zip(words, assigned):
        if i is None:
            continue
        aligned[i].append(word["text"])
        neighbour = _shifted_from(word, i, turns, ref_tokens)
        if neighbour is not None:
            shifted.append({"word": word["text"].strip(), "start": word["start"], "end": word["end"],
                            "assigned_speaker": turns[i]["speaker"], "reference_speaker": turns[neighbour]["speaker"]})

    rows = [
        {**_turn(t), "aligned_text": "".join(parts).strip(), **word_errors(t["text"], "".join(parts))}
        for t, parts in zip(turns, aligned)
    ]
    errors = sum(r["substitutions"] + r["deletions"] + r["insertions"] for r in rows)
    n = sum(r["reference_words"] for r in rows)
    return {
        "turn_wer": errors / n if n else None,
        "shifted_words": shifted,
        "unassigned_words": sum(i is None for i in assigned),
        "turns": rows,
    }


def attribution_proxy(reference: dict, transcript: dict, words: list[dict], mapping: dict) -> dict:
    """cpWER − WER: yalnızca yardımcı bir 'speaker attribution proxy'; kesin atama hatası değildir."""
    ref_by_speaker: dict[str, list[str]] = {}
    hyp_by_speaker: dict[str, list[str]] = {}
    for s in _by_time(reference["segments"]):
        ref_by_speaker.setdefault(s["speaker"], []).append(s["text"])
    for s in _by_time(transcript["segments"]):
        hyp_by_speaker.setdefault(mapping.get(s["speaker"], f"?{s['speaker']}"), []).append(s["text"])

    errors = n = 0
    for speaker in ref_by_speaker.keys() | hyp_by_speaker.keys():
        e = word_errors(" ".join(ref_by_speaker.get(speaker, [])), " ".join(hyp_by_speaker.get(speaker, [])))
        errors += e["substitutions"] + e["deletions"] + e["insertions"]
        n += e["reference_words"]
    cpwer = errors / n if n else None
    stt_wer = stt_errors(reference, words)["wer"]
    return {
        "cpwer": cpwer,
        "stt_wer": stt_wer,
        "speaker_attribution_proxy": cpwer - stt_wer if cpwer is not None and stt_wer is not None else None,
    }


def turn_comparison(reference: dict, hyp_segments: list[dict], words: list[dict], mapping: dict) -> list[dict]:
    """Her referans turu için aynı zaman aralığındaki kelimeler, hipotezin atadığı (eşlenmiş) konuşmacıya göre."""
    assigned = assign_words(hyp_segments, words)
    rows = []
    for turn in _by_time(reference["segments"]):
        by_speaker: dict[str, list[str]] = {}
        for word, i in zip(words, assigned):
            if turn["start"] <= (word["start"] + word["end"]) / 2 < turn["end"]:
                speaker = mapping[hyp_segments[i]["speaker"]] if i is not None else "(atanmadı)"
                by_speaker.setdefault(speaker, []).append(word["text"])
        rows.append({**_turn(turn), "hypothesis": {k: "".join(v).strip() for k, v in by_speaker.items()}})
    return rows


def evaluate(reference: dict, hypothesis: dict) -> dict:
    """Tüm metrikler. `hypothesis`: {"segments": diarization segmentleri, "words": Whisper kelimeleri}."""
    segments, words = hypothesis["segments"], hypothesis["words"]
    mapping = speaker_mapping(reference, segments)
    transcript = build_transcript(reference["source_file"], segments, words)
    return {
        "speaker_mapping": mapping,
        "stt": stt_errors(reference, words),
        "diarization": {
            **diarization_errors(reference, segments),
            "boundaries": boundary_deviation(reference, segments, mapping),
            "short_turns": short_turns(reference, segments, words, mapping),
        },
        "alignment": {"oracle": oracle_alignment(reference, words)},
        "attribution": attribution_proxy(reference, transcript, words, mapping),
        "turns": turn_comparison(reference, segments, words, mapping),
    }


def _shifted_from(word: dict, i: int, turns: list[dict], ref_tokens: list[set]) -> int | None:
    """Kelime i. tura atanmış ama aslında komşu (farklı konuşmacılı) turun referansındaysa o komşunun indeksi."""
    tokens = normalize_text(word["text"]).split()
    if not tokens or any(t in ref_tokens[i] for t in tokens):
        return None
    middle = (word["start"] + word["end"]) / 2
    if min(abs(middle - turns[i]["start"]), abs(middle - turns[i]["end"])) > BOUNDARY_WINDOW_SECONDS:
        return None
    for j in (i - 1, i + 1):
        if 0 <= j < len(turns) and turns[j]["speaker"] != turns[i]["speaker"]:
            if all(t in ref_tokens[j] for t in tokens):
                return j
    return None


def _turn(turn: dict) -> dict:
    return {"speaker": turn["speaker"], "start": turn["start"], "end": turn["end"], "reference_text": turn["text"]}


def _by_time(segments: list[dict]) -> list[dict]:
    return sorted(segments, key=lambda s: (s["start"], s["end"]))


def _change_points(segments: list[dict], speaker_of) -> list[float]:
    ordered = _by_time(segments)
    return [b["start"] for a, b in zip(ordered, ordered[1:]) if speaker_of(a) != speaker_of(b)]


def _overlap(a: dict, b: dict) -> float:
    return min(a["end"], b["end"]) - max(a["start"], b["start"])


def _annotation(segments: list[dict]) -> Annotation:
    annotation = Annotation()
    for i, s in enumerate(segments):
        annotation[Segment(s["start"], s["end"]), i] = s["speaker"]
    return annotation


def _uem(segments: list[dict]) -> Timeline:
    return Timeline([Segment(0, max(s["end"] for s in segments))])
