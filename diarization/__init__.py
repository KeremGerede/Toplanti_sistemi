"""Kayıtlı ses dosyaları için speaker diarization modülü."""

from diarization.device import resolve_device
from diarization.diarizer import Diarizer, SpeakerSegment

__all__ = ["Diarizer", "SpeakerSegment", "resolve_device"]
