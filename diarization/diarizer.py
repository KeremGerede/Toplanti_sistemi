"""Kayıtlı ses dosyaları için speaker diarization (pyannote community-1)."""

from pathlib import Path
from typing import TypedDict

import soundfile as sf
import torch
from huggingface_hub.errors import RepositoryNotFoundError
from pyannote.audio import Pipeline
from pyannote.audio.telemetry import set_telemetry_metrics
from pyannote.core import Annotation

from diarization.device import resolve_device

MODEL_ID = "pyannote/speaker-diarization-community-1"

_ACCESS_HELP = (
    f"'{MODEL_ID}' modeli yüklenemedi: Hugging Face erişimi yok.\n"
    f"1) https://huggingface.co/{MODEL_ID} sayfasında kullanım koşullarını kabul edin.\n"
    "2) https://hf.co/settings/tokens adresinden 'read' yetkili bir token oluşturun.\n"
    "3) 'uv run hf auth login' ile giriş yapın ya da kullanıcı düzeyinde HF_TOKEN ortam değişkeni tanımlayın."
)


class SpeakerSegment(TypedDict):
    speaker: str
    start: float
    end: float


def normalize(annotation: Annotation) -> list[SpeakerSegment]:
    """pyannote çıktısını projenin JSON uyumlu çıktı sözleşmesine çevirir.

    Segmentler başlangıç zamanına göre sıralanır, süreler 3 ondalığa yuvarlanır.
    Etiketler ilk konuşma sırasına göre SPEAKER_00, SPEAKER_01 … olarak yeniden atanır.
    Farklı konuşmacılara ait çakışan segmentler korunur.
    """
    tracks = sorted(
        ((turn.start, turn.end, label) for turn, _, label in annotation.itertracks(yield_label=True)),
        key=lambda track: (track[0], track[1], str(track[2])),
    )
    speakers: dict = {}
    segments: list[SpeakerSegment] = []
    for start, end, label in tracks:
        speaker = speakers.setdefault(label, f"SPEAKER_{len(speakers):02d}")
        segments.append({"speaker": speaker, "start": round(float(start), 3), "end": round(float(end), 3)})
    return segments


class Diarizer:
    """Pipeline'ı bir kez yükler; aynı instance birden çok dosya için kullanılabilir."""

    def __init__(self, device: str = "auto", token: str | None = None):
        self.device = resolve_device(device)
        set_telemetry_metrics(False)
        try:
            # token=None: huggingface_hub, 'hf auth login' önbelleğini veya HF_TOKEN'ı kullanır.
            pipeline = Pipeline.from_pretrained(MODEL_ID, token=token)
        except RepositoryNotFoundError as exc:  # gated/401 hataları dahil
            raise RuntimeError(_ACCESS_HELP) from exc
        if pipeline is None:
            raise RuntimeError(_ACCESS_HELP)
        self._pipeline = pipeline.to(self.device)

    def diarize_file(self, path: str | Path) -> list[SpeakerSegment]:
        path = Path(path)
        if not path.is_file():
            raise FileNotFoundError(f"Ses dosyası bulunamadı: {path}")
        data, sample_rate = sf.read(path, dtype="float32", always_2d=True)  # (örnek, kanal)
        waveform = torch.from_numpy(data.T.copy())  # (kanal, örnek)
        return self._diarize(waveform, sample_rate)

    def _diarize(self, waveform: torch.Tensor, sample_rate: int) -> list[SpeakerSegment]:
        # Dosyadan bağımsız çekirdek: ileride canlı ses de buraya bellekteki sesle gelebilir.
        output = self._pipeline({"waveform": waveform, "sample_rate": sample_rate})
        return normalize(output.speaker_diarization)
