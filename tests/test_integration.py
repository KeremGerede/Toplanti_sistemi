"""Gerçek model ile entegrasyon testleri. Kayıtlar için bkz. tests/data/README.md.

Çalıştırma: uv run pytest -m integration -rP   (-rP: gözlem satırlarını gösterir)
"""

import json
import time
from pathlib import Path

import pytest
import torch
from huggingface_hub import get_token

from diarization import Diarizer

pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(get_token() is None, reason="HF token yok: 'uv run hf auth login' ile giriş yapın"),
]

DATA = Path(__file__).parent / "data"
DEVICES = ["auto", "cpu"]
FILES = ["two_speakers_clean.wav", "three_speakers.wav", "short_utterances.wav", "overlap.wav"]


@pytest.fixture(scope="module")
def diarize():
    """Pipeline'ı cihaz başına bir kez yükler, sonuçları (cihaz, dosya) başına önbellekler."""
    diarizers, results = {}, {}

    def run(device, name):
        path = DATA / name
        if not path.is_file():
            pytest.skip(f"{name} yok (bkz. tests/data/README.md)")
        if (device, name) not in results:
            if device not in diarizers:
                diarizers[device] = Diarizer(device=device)
            started = time.perf_counter()
            segments = diarizers[device].diarize_file(path)
            elapsed = time.perf_counter() - started
            print(
                f"[{name} | {diarizers[device].device}] konuşmacı={len(speakers(segments))} "
                f"segment={len(segments)} kısa(<1.5s)={sum(s['end'] - s['start'] < 1.5 for s in segments)} "
                f"çakışan_çift={overlapping_pairs(segments)} süre={elapsed:.1f}s"
            )
            results[device, name] = segments
        return results[device, name]

    return run


def speakers(segments):
    return {s["speaker"] for s in segments}


def overlapping_pairs(segments):
    return sum(
        1
        for i, a in enumerate(segments)
        for b in segments[i + 1:]
        if a["speaker"] != b["speaker"] and b["start"] < a["end"]
    )


def assert_valid(segments):
    assert json.loads(json.dumps(segments)) == segments
    for s in segments:
        assert set(s) == {"speaker", "start", "end"}
        assert 0 <= s["start"] < s["end"]
    assert [s["start"] for s in segments] == sorted(s["start"] for s in segments)
    labels = sorted(speakers(segments))
    assert labels == [f"SPEAKER_{i:02d}" for i in range(len(labels))]


@pytest.mark.parametrize("device", DEVICES)
def test_two_speakers_clean(diarize, device):
    segments = diarize(device, "two_speakers_clean.wav")
    assert_valid(segments)
    assert len(speakers(segments)) == 2


@pytest.mark.parametrize("device", DEVICES)
def test_three_speakers(diarize, device):
    segments = diarize(device, "three_speakers.wav")
    assert_valid(segments)
    assert len(speakers(segments)) == 3


# Kısa konuşma ve overlap: bu aşamada gözlem/baseline; yalnızca çalışma ve şema zorunlu.
@pytest.mark.parametrize("device", DEVICES)
def test_short_utterances(diarize, device):
    segments = diarize(device, "short_utterances.wav")
    assert_valid(segments)
    assert segments


@pytest.mark.parametrize("device", DEVICES)
def test_overlap(diarize, device):
    segments = diarize(device, "overlap.wav")
    assert_valid(segments)
    assert segments


@pytest.mark.skipif(not torch.cuda.is_available(), reason="CUDA yok; auto zaten cpu")
@pytest.mark.parametrize("name", FILES)
def test_gpu_and_cpu_agree_on_speaker_count(diarize, name):
    assert len(speakers(diarize("auto", name))) == len(speakers(diarize("cpu", name)))
