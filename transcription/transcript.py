"""Whisper kelimelerini diarization segmentleriyle eşleştirir (saf fonksiyonlar, model gerektirmez)."""

from typing import TypedDict

# Hiçbir segmentle örtüşmeyen kelime, en yakın segmente en fazla bu kadar uzaksa ona atanır.
MAX_GAP_SECONDS = 0.5


class Word(TypedDict):
    start: float
    end: float
    text: str


class TranscriptSegment(TypedDict):
    speaker: str
    start: float
    end: float
    text: str


def attach_text(segments: list[dict], words: list[Word]) -> list[TranscriptSegment]:
    """Her kelimeyi zaman olarak en çok örtüştüğü segmentin `text` alanına ekler.

    Örtüşme eşitse listede önce gelen segment seçilir. Hiçbir segmentle örtüşmeyen kelime,
    en yakın segmente en fazla MAX_GAP_SECONDS uzaktaysa ona eklenir; değilse atlanır.
    Kelime almayan segment `text: ""` ile korunur.
    """
    texts: list[list[str]] = [[] for _ in segments]
    for word in words:
        index = _segment_index(segments, word)
        if index is not None:
            texts[index].append(word["text"])
    return [{**segment, "text": "".join(parts).strip()} for segment, parts in zip(segments, texts)]


def build_transcript(source_file: str, segments: list[dict], words: list[Word]) -> dict:
    """Projenin konuşmacılı transkript çıktısını üretir."""
    transcript_segments = attach_text(segments, words)
    return {
        "source_file": source_file,
        "speaker_count": len({s["speaker"] for s in transcript_segments}),
        "segments": transcript_segments,
    }


def _segment_index(segments: list[dict], word: Word) -> int | None:
    if not segments:
        return None
    # Pozitif skor örtüşme süresi, negatif skor segmente olan uzaklıktır (boşluk).
    scores = [round(min(s["end"], word["end"]) - max(s["start"], word["start"]), 3) for s in segments]
    best = max(range(len(segments)), key=scores.__getitem__)  # eşitlikte ilk segment
    return best if scores[best] >= -MAX_GAP_SECONDS else None
