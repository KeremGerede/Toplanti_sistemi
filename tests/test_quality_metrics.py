import json

import pytest

from quality.metrics import (
    assign_words,
    attribution_proxy,
    boundary_deviation,
    diarization_errors,
    evaluate,
    normalize_text,
    oracle_alignment,
    short_turns,
    speaker_mapping,
    stt_errors,
    turn_comparison,
    word_errors,
)


def seg(speaker, start, end, text=""):
    return {"speaker": speaker, "start": start, "end": end, "text": text}


def word(start, end, text):
    return {"start": start, "end": end, "text": text}


def reference(*segments):
    return {"source_file": "test.wav", "speaker_count": len({s["speaker"] for s in segments}), "segments": list(segments)}


# --- Normalizasyon ---------------------------------------------------------

def test_normalize_turkish_dotted_and_dotless_i():
    assert normalize_text("IRMAK İzmir ILIK") == "ırmak izmir ılık"


def test_normalize_punctuation_and_whitespace():
    assert normalize_text("  Evet,   tamam!  Peki... ne?\n") == "evet tamam peki ne"


def test_normalize_apostrophe_is_removed_and_joins_word():
    assert normalize_text("Ahmet'in Ankara’ya") == "ahmetin ankaraya"


# --- STT -------------------------------------------------------------------

@pytest.mark.parametrize(
    ("ref", "hyp", "expected"),
    [
        ("bugün hava güzel", "bugün hava soğuk", (1, 0, 0)),
        ("bugün hava çok güzel", "bugün hava güzel", (0, 1, 0)),
        ("bugün hava güzel", "bugün hava çok güzel", (0, 0, 1)),
    ],
)
def test_word_errors_substitution_deletion_insertion(ref, hyp, expected):
    e = word_errors(ref, hyp)
    assert (e["substitutions"], e["deletions"], e["insertions"]) == expected
    assert e["wer"] == pytest.approx(1 / e["reference_words"])


def test_word_errors_ignore_case_and_punctuation():
    assert word_errors("Bugün hava güzel.", "bugün  HAVA güzel")["wer"] == 0


def test_word_errors_empty_texts():
    assert word_errors("", "")["wer"] is None
    assert word_errors("bir iki", "") == {
        "reference_words": 2, "substitutions": 0, "deletions": 2, "insertions": 0, "wer": 1.0,
    }
    assert word_errors("", "fazla")["insertions"] == 1


def test_stt_errors_use_time_order_and_ignore_speakers():
    ref = reference(seg("B", 3, 4, "dünya"), seg("A", 0, 2, "Merhaba"))
    assert stt_errors(ref, [word(0.1, 0.5, " merhaba"), word(3.1, 3.5, " dünya")])["wer"] == 0


# --- Diarization -----------------------------------------------------------

def test_speaker_mapping_and_perfect_diarization():
    ref = reference(seg("A", 0, 5), seg("B", 5, 10))
    hyp = [seg("SPEAKER_00", 5, 10), seg("SPEAKER_01", 0, 5)]
    assert speaker_mapping(ref, hyp) == {"SPEAKER_00": "B", "SPEAKER_01": "A"}
    d = diarization_errors(ref, hyp)
    assert (d["reference_speakers"], d["hypothesis_speakers"]) == (2, 2)
    assert d["der"] == pytest.approx(0)


def test_diarization_confusion_and_speaker_count_mismatch():
    ref = reference(seg("A", 0, 10), seg("B", 10, 20))
    hyp = [seg("S0", 0, 15), seg("S1", 15, 18), seg("S2", 18, 20)]
    d = diarization_errors(ref, hyp)
    assert d["hypothesis_speakers"] == 3
    assert d["missed"] == pytest.approx(0) and d["false_alarm"] == pytest.approx(0)
    assert d["confusion"] > 0.2
    assert speaker_mapping(ref, hyp)["S2"] == "?S2"  # eşlenemeyen fazla konuşmacı


def test_boundary_deviation():
    ref = reference(seg("A", 0, 5), seg("B", 5, 10), seg("A", 10, 15))
    hyp = [seg("S0", 0, 5.2), seg("S1", 5.2, 11), seg("S0", 11, 15)]
    b = boundary_deviation(ref, hyp, {"S0": "A", "S1": "B"})
    assert b == {"reference_changes": 2, "hypothesis_changes": 2, "median": 0.6, "max": 1.0, "over_window": 1}


def test_boundary_deviation_without_hypothesis_changes():
    ref = reference(seg("A", 0, 5), seg("B", 5, 10))
    b = boundary_deviation(ref, [seg("S0", 0, 10)], {"S0": "A"})
    assert b["median"] is None and b["over_window"] == 1


def test_short_turns_caught_by_diarization_and_stt():
    ref = reference(
        seg("A", 0, 5, "uzun konuşma"), seg("B", 5.2, 5.8, "evet"),
        seg("A", 6, 10, "devam"), seg("B", 10.2, 10.8, "tamam"),
    )
    hyp = [seg("S0", 0, 10.9), seg("S1", 5.1, 5.9)]
    words = [word(0.5, 1, " uzun"), word(5.3, 5.6, " evet"), word(6.5, 7, " devam")]
    r = short_turns(ref, hyp, words, {"S0": "A", "S1": "B"})
    assert (r["total"], r["diarization_caught"], r["stt_caught"]) == (2, 1, 1)
    assert [t["reference_text"] for t in r["turns"] if not t["stt_caught"]] == ["tamam"]


# --- Alignment -------------------------------------------------------------

def test_assign_words_follows_product_rule():
    segments = [seg("A", 0, 2), seg("B", 3, 5)]
    words = [word(0.5, 1, " a"), word(3.5, 4, " b"), word(7, 8, " uzak")]  # sonuncusu 0.5 sn toleransın dışında
    assert assign_words(segments, words) == [0, 1, None]


def boundary_example():
    ref = reference(seg("A", 0, 3, "bugün hava güzel"), seg("B", 3, 4, "ben de"))
    words = [
        word(0.1, 0.5, " bugün"), word(0.6, 1.0, " hava"), word(1.1, 1.5, " güzel"),
        word(2.8, 3.2, " ben"),  # iki tura eşit örtüşür → kural gereği öndeki A'ya gider
        word(3.3, 3.6, " de"),
    ]
    return ref, words


def test_oracle_alignment_detects_shifted_word():
    ref, words = boundary_example()
    o = oracle_alignment(ref, words)
    assert [(s["word"], s["assigned_speaker"], s["reference_speaker"]) for s in o["shifted_words"]] == [("ben", "A", "B")]
    assert [t["aligned_text"] for t in o["turns"]] == ["bugün hava güzel ben", "de"]
    assert [(t["insertions"], t["deletions"]) for t in o["turns"]] == [(1, 0), (0, 1)]
    assert o["turn_wer"] == pytest.approx(2 / 5)
    assert o["unassigned_words"] == 0


def test_oracle_alignment_ignores_words_away_from_boundary_and_counts_unassigned():
    ref = reference(seg("A", 0, 3, "bugün hava güzel"), seg("B", 3, 4, "ben de"))
    words = [word(1.0, 1.2, " ben"), word(10, 11, " uzak")]  # 'ben' turun ortasında; 'uzak' toleransın dışında
    o = oracle_alignment(ref, words)
    assert o["shifted_words"] == []
    assert o["unassigned_words"] == 1


def test_attribution_proxy():
    ref = reference(seg("A", 0, 2, "merhaba nasılsın"), seg("B", 2, 4, "iyiyim sağ ol"))
    words = [word(0.1, 0.5, " merhaba"), word(0.6, 1.5, " nasılsın"),
             word(2.1, 2.5, " iyiyim"), word(2.6, 3, " sağ"), word(3.1, 3.5, " ol")]
    mapping = {"S0": "A", "S1": "B"}

    perfect = {"segments": [seg("S0", 0, 2, "merhaba nasılsın"), seg("S1", 2, 4, "iyiyim sağ ol")]}
    assert attribution_proxy(ref, perfect, words, mapping)["speaker_attribution_proxy"] == pytest.approx(0)

    shifted = {"segments": [seg("S0", 0, 2, "merhaba nasılsın iyiyim"), seg("S1", 2, 4, "sağ ol")]}
    p = attribution_proxy(ref, shifted, words, mapping)
    assert p["stt_wer"] == pytest.approx(0)
    assert p["cpwer"] == pytest.approx(2 / 5)
    assert p["speaker_attribution_proxy"] == pytest.approx(2 / 5)


def test_turn_comparison_groups_words_by_hypothesis_speaker():
    ref = reference(seg("A", 0, 3, "bugün"), seg("B", 3, 4, "ben de"))
    hyp = [seg("S0", 0, 3.1), seg("S1", 3.1, 4)]
    words = [word(0.5, 1, " bugün"), word(2.9, 3.2, " ben"), word(3.3, 3.6, " de")]
    rows = turn_comparison(ref, hyp, words, {"S0": "A", "S1": "B"})
    assert [r["hypothesis"] for r in rows] == [{"A": "bugün"}, {"A": "ben", "B": "de"}]


def test_evaluate_report_is_json_serializable():
    ref, words = boundary_example()
    diarization = [{"speaker": "SPEAKER_00", "start": 0, "end": 3.1}, {"speaker": "SPEAKER_01", "start": 3.1, "end": 4}]
    hypothesis = {"segments": diarization, "words": words}
    report = evaluate(ref, hypothesis)
    assert set(report) == {"speaker_mapping", "stt", "diarization", "alignment", "attribution", "turns"}
    assert report["speaker_mapping"] == {"SPEAKER_00": "A", "SPEAKER_01": "B"}
    json.dumps(report, ensure_ascii=False)
