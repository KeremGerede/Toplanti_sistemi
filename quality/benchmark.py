"""Kalite ölçüm CLI'ı: mevcut pipeline'ı (baseline) çalıştırır ve referansla (ground truth) karşılaştırır.

Kullanım:
  uv run python -m quality.benchmark tests/data/two_speakers_clean.wav --reference tests/data/two_speakers_clean.reference.json

Modeli yeniden çalıştırmadan, kayıtlı hipotezle yeniden puanlama:
  uv run python -m quality.benchmark tests/data/two_speakers_clean.wav --reference ... \
      --hypothesis tests/data/results/two_speakers_clean__baseline.hypothesis.json

Çıktılar varsayılan olarak tests/data/results/ altına yazılır (commit edilmez).
"""

import argparse
import json
import sys
import time
from pathlib import Path

from diarization import Diarizer
from diarization.device import DEVICE_CHOICES
from quality.metrics import evaluate
from transcription import Transcriber

RESULTS_DIR = Path("tests/data/results")
VARIANT = "baseline"


def run_baseline(audio: Path, device: str) -> dict:
    """Ürünün mevcut modelleri ve ayarlarıyla diarization segmentlerini ve Whisper kelimelerini üretir."""
    diarizer = Diarizer(device=device)
    transcriber = Transcriber(device=device)
    started = time.perf_counter()
    segments = diarizer.diarize_file(audio)
    diarization_seconds = time.perf_counter() - started
    started = time.perf_counter()
    words = transcriber.transcribe_file(audio)
    stt_seconds = time.perf_counter() - started
    return {
        "source_file": audio.name,
        "variant": VARIANT,
        "device": str(diarizer.device),
        "timings": {"diarization_seconds": round(diarization_seconds, 2), "stt_seconds": round(stt_seconds, 2)},
        "segments": segments,
        "words": words,
    }


def main() -> None:
    parser = argparse.ArgumentParser(prog="python -m quality.benchmark", description=__doc__.splitlines()[0])
    parser.add_argument("audio", type=Path, help="ses dosyası (WAV/FLAC)")
    parser.add_argument("--reference", type=Path, required=True, help="ground truth JSON (bkz. tests/data/README.md)")
    parser.add_argument("--hypothesis", type=Path, help="kayıtlı hipotez JSON'u; verilirse modeller çalıştırılmaz")
    parser.add_argument("--device", choices=DEVICE_CHOICES, default="auto")
    parser.add_argument("--output-dir", type=Path, default=RESULTS_DIR)
    args = parser.parse_args()

    reference = _read_json(args.reference)
    if reference["source_file"] != args.audio.name:
        print(f"UYARI: referans '{reference['source_file']}' için, ses '{args.audio.name}'", file=sys.stderr)

    args.output_dir.mkdir(parents=True, exist_ok=True)
    stem = f"{args.audio.stem}__{VARIANT}"
    if args.hypothesis:
        hypothesis = _read_json(args.hypothesis)
    else:
        hypothesis = run_baseline(args.audio, args.device)
        _write_json(args.output_dir / f"{stem}.hypothesis.json", hypothesis)

    report = {
        "source_file": args.audio.name,
        "reference_file": args.reference.name,
        "variant": hypothesis.get("variant", VARIANT),
        "device": hypothesis.get("device"),
        "timings": hypothesis.get("timings"),
        **evaluate(reference, hypothesis),
    }
    report_path = args.output_dir / f"{stem}.report.json"
    _write_json(report_path, report)
    print_summary(report)
    print(f"\nRapor: {report_path}")


def print_summary(report: dict) -> None:
    stt, diar = report["stt"], report["diarization"]
    bounds, short = diar["boundaries"], diar["short_turns"]
    oracle, attribution = report["alignment"]["oracle"], report["attribution"]

    print(f"== {report['source_file']} | {report['variant']} | {report['device']} ==")
    print(f"STT          WER {_pct(stt['wer'])}  (S {stt['substitutions']}, D {stt['deletions']}, "
          f"I {stt['insertions']} / {stt['reference_words']} referans kelime)")
    print(f"Diarization  konuşmacı: referans {diar['reference_speakers']}, hipotez {diar['hypothesis_speakers']} | "
          f"DER {_pct(diar['der'])} (kaçırılan {_pct(diar['missed'])}, yanlış alarm {_pct(diar['false_alarm'])}, "
          f"karışma {_pct(diar['confusion'])})")
    print(f"             sınır sapması: {bounds['reference_changes']} değişim, medyan {bounds['median']} sn, "
          f"maks {bounds['max']} sn, >0.5 sn: {bounds['over_window']}")
    print(f"             kısa turlar: {short['total']} | diarization yakaladı {short['diarization_caught']} | "
          f"STT yakaladı {short['stt_caught']}")
    print(f"Alignment    oracle diarization ile tur WER {_pct(oracle['turn_wer'])} | "
          f"kayan kelime {len(oracle['shifted_words'])} | atanamayan kelime {oracle['unassigned_words']}")
    for s in oracle["shifted_words"]:
        print(f"             kayan: '{s['word']}' @{s['start']:.2f} sn -> {s['assigned_speaker']} "
              f"(referansta {s['reference_speaker']})")
    print(f"Yardımcı     cpWER {_pct(attribution['cpwer'])} - STT WER {_pct(attribution['stt_wer'])} "
          f"= speaker attribution proxy {_pct(attribution['speaker_attribution_proxy'])} "
          f"(kesin atama hatası değildir)")
    if report.get("timings"):
        print(f"Süre         diarization {report['timings']['diarization_seconds']} sn, "
              f"STT {report['timings']['stt_seconds']} sn")

    print("\nTur karşılaştırması (referans | aynı aralıktaki kelimeler, hipotezin atadığı konuşmacıya göre):")
    for row in report["turns"]:
        hyp = " | ".join(f"{k}: {v}" for k, v in row["hypothesis"].items()) or "(kelime yok)"
        print(f"[{row['start']:7.2f}-{row['end']:7.2f}] {row['speaker']}: {row['reference_text']}")
        print(f"{'':19}-> {hyp}")


def _pct(value) -> str:
    return "—" if value is None else f"{value * 100:.1f}%"


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
