"""Whisper (turbo) ile kelime zaman damgalı Türkçe transkripsiyon."""

from pathlib import Path

import soundfile as sf
import torch
import torchaudio.functional as AF
import whisper

from diarization.device import resolve_device
from transcription.transcript import Word

MODEL_NAME = "turbo"
LANGUAGE = "tr"


class Transcriber:
    """Whisper modelini bir kez yükler; aynı instance birden çok dosya için kullanılabilir."""

    def __init__(self, device: str = "auto"):
        self.device = resolve_device(device)
        # İlk çalıştırmada ağırlıklar (~1.5 GB) %USERPROFILE%\.cache\whisper altına iner.
        self._model = whisper.load_model(MODEL_NAME, device=self.device)

    def transcribe_file(self, path: str | Path) -> list[Word]:
        path = Path(path)
        if not path.is_file():
            raise FileNotFoundError(f"Ses dosyası bulunamadı: {path}")
        data, sample_rate = sf.read(path, dtype="float32", always_2d=True)  # (örnek, kanal)
        mono = torch.from_numpy(data.T.copy()).mean(dim=0)
        audio = AF.resample(mono, sample_rate, whisper.audio.SAMPLE_RATE).numpy()  # FFmpeg gerekmez
        result = self._model.transcribe(
            audio, language=LANGUAGE, word_timestamps=True, fp16=self.device.type == "cuda"
        )
        return [
            {"start": round(float(w["start"]), 3), "end": round(float(w["end"]), 3), "text": w["word"]}
            for segment in result["segments"]
            for w in segment["words"]
        ]
