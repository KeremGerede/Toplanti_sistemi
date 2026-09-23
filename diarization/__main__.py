"""CLI: python -m diarization <ses_dosyası> [--device auto|cpu|cuda]

JSON çıktı stdout'a, kullanılan cihaz stderr'e yazılır.
"""

import argparse
import json
import sys

from diarization.device import DEVICE_CHOICES
from diarization.diarizer import Diarizer


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="python -m diarization",
        description="Kayıtlı bir ses dosyasında speaker diarization çalıştırır.",
    )
    parser.add_argument("audio", help="ses dosyası yolu (WAV/FLAC)")
    parser.add_argument("--device", choices=DEVICE_CHOICES, default="auto")
    args = parser.parse_args()

    diarizer = Diarizer(device=args.device)
    print(f"device: {diarizer.device}", file=sys.stderr)
    segments = diarizer.diarize_file(args.audio)
    print(json.dumps(segments, indent=2))


if __name__ == "__main__":
    main()
