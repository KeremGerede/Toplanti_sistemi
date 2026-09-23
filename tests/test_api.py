import io
import json
from pathlib import Path

import numpy as np
import pytest
import soundfile as sf
import torch
from fastapi.testclient import TestClient
from huggingface_hub import get_token

from api import main

SEGMENTS = [
    {"speaker": "SPEAKER_00", "start": 0.0, "end": 1.0},
    {"speaker": "SPEAKER_01", "start": 1.2, "end": 2.0},
]
WORDS = [{"start": 0.1, "end": 0.5, "text": " Merhaba"}, {"start": 1.3, "end": 1.8, "text": " dünya"}]


class FakeDiarizer:
    device = torch.device("cpu")

    def diarize_file(self, path):
        sf.read(path)  # gerçek modül gibi dosyayı okur: ses değilse LibsndfileError
        self.seen_path = Path(path)
        return SEGMENTS


class FakeTranscriber:
    def transcribe_file(self, path):
        return WORDS


@pytest.fixture
def client(monkeypatch, tmp_path):
    monkeypatch.setattr(main, "OUTPUT_DIR", tmp_path / "outputs")
    monkeypatch.setattr(main.app.state, "diarizer", FakeDiarizer(), raising=False)
    monkeypatch.setattr(main.app.state, "transcriber", FakeTranscriber(), raising=False)
    return TestClient(main.app)  # context manager yok: lifespan (gerçek modeller) çalışmaz


def wav_bytes():
    buffer = io.BytesIO()
    sf.write(buffer, np.zeros(1600, dtype="float32"), 16000, format="WAV")
    return buffer.getvalue()


def upload(client, filename, content):
    return client.post("/diarize", files={"file": (filename, content, "audio/wav")})


def test_health(client):
    assert client.get("/health").json() == {"status": "ok", "device": "cpu"}


def test_diarize_returns_and_saves_transcript(client):
    response = upload(client, "toplanti.wav", wav_bytes())
    assert response.status_code == 200
    body = response.json()
    assert body == {
        "source_file": "toplanti.wav",
        "speaker_count": 2,
        "segments": [
            {"speaker": "SPEAKER_00", "start": 0.0, "end": 1.0, "text": "Merhaba"},
            {"speaker": "SPEAKER_01", "start": 1.2, "end": 2.0, "text": "dünya"},
        ],
        "output_file": body["output_file"],
    }
    saved = main.OUTPUT_DIR / body["output_file"]
    assert body["output_file"].endswith("_toplanti.json")
    assert json.loads(saved.read_text(encoding="utf-8")) == {k: v for k, v in body.items() if k != "output_file"}


def test_uploaded_audio_is_deleted(client):
    upload(client, "toplanti.wav", wav_bytes())
    assert not main.app.state.diarizer.seen_path.exists()


def test_missing_file_is_422(client):
    assert client.post("/diarize").status_code == 422


def test_unreadable_audio_is_400_and_nothing_saved(client):
    response = upload(client, "not_audio.wav", b"bu bir ses dosyasi degil")
    assert response.status_code == 400
    assert not main.OUTPUT_DIR.exists() or not any(main.OUTPUT_DIR.iterdir())


def test_filename_is_sanitized(client):
    response = upload(client, "../../kötü ad.wav", wav_bytes())
    body = response.json()
    assert body["source_file"] == "kötü ad.wav"
    assert body["output_file"].endswith("_kötü_ad.json")
    saved = [p.resolve() for p in main.OUTPUT_DIR.iterdir()]
    assert saved == [(main.OUTPUT_DIR / body["output_file"]).resolve()]


@pytest.mark.integration
def test_diarize_with_real_models(monkeypatch, tmp_path):
    path = Path(__file__).parent / "data" / "two_speakers_clean.wav"
    if get_token() is None or not path.is_file():
        pytest.skip("HF token veya two_speakers_clean.wav yok")
    monkeypatch.setattr(main, "OUTPUT_DIR", tmp_path)
    with TestClient(main.app) as client:  # lifespan: gerçek modeller yüklenir
        with path.open("rb") as f:
            response = client.post("/diarize", files={"file": (path.name, f, "audio/wav")})
    assert response.status_code == 200
    body = response.json()
    assert body["speaker_count"] == 2
    assert any(s["text"] for s in body["segments"])
    assert (tmp_path / body["output_file"]).is_file()
