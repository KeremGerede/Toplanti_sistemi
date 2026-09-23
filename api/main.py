"""Yerel FastAPI backend: ses yükle → diarization + transkripsiyon + eşleme → outputs/ altına JSON.

Çalıştırma (yalnızca yerel): uv run uvicorn api.main:app --host 127.0.0.1 --port 8000
"""

import json
import os
import re
import shutil
import tempfile
import threading
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path

import soundfile as sf
from fastapi import FastAPI, File, HTTPException, UploadFile

from diarization import Diarizer
from transcription import Transcriber, build_transcript

OUTPUT_DIR = Path(__file__).resolve().parent.parent / "outputs"

# GPU'da aynı anda tek istek işlenir.
_lock = threading.Lock()


@asynccontextmanager
async def lifespan(app: FastAPI):
    device = os.environ.get("APP_DEVICE", "auto")
    app.state.diarizer = Diarizer(device=device)
    app.state.transcriber = Transcriber(device=device)
    yield


app = FastAPI(title="Toplantı Asistanı", lifespan=lifespan)


@app.get("/health")
def health():
    return {"status": "ok", "device": str(app.state.diarizer.device)}


@app.post("/diarize")
def diarize(file: UploadFile = File(...)):
    source_file = Path(file.filename or "audio").name
    # Yüklenen ses yalnızca işlem süresince geçici dosyada tutulur.
    with tempfile.NamedTemporaryFile(suffix=Path(source_file).suffix, delete=False) as tmp:
        shutil.copyfileobj(file.file, tmp)
    try:
        with _lock:
            segments = app.state.diarizer.diarize_file(tmp.name)
            words = app.state.transcriber.transcribe_file(tmp.name)
    except sf.LibsndfileError as exc:
        raise HTTPException(status_code=400, detail="Ses dosyası okunamadı (WAV/FLAC bekleniyor).") from exc
    finally:
        os.unlink(tmp.name)
    transcript = build_transcript(source_file, segments, words)
    output_path = _save(transcript, source_file)
    return {**transcript, "output_file": output_path.name}


def _save(transcript: dict, source_file: str) -> Path:
    stem = re.sub(r"[^\w-]", "_", Path(source_file).stem)[:50]
    OUTPUT_DIR.mkdir(exist_ok=True)
    path = OUTPUT_DIR / f"{datetime.now():%Y%m%d-%H%M%S-%f}_{stem}.json"
    path.write_text(json.dumps(transcript, ensure_ascii=False, indent=2), encoding="utf-8")
    return path
