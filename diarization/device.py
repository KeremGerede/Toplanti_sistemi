"""Hesaplama cihazı seçimi: auto / cpu / cuda."""

import torch

DEVICE_CHOICES = ("auto", "cpu", "cuda")


def resolve_device(device: str = "auto") -> torch.device:
    """`auto`: CUDA varsa cuda, yoksa cpu. `cuda` açıkça istenip yoksa sessizce CPU'ya düşmez."""
    if device not in DEVICE_CHOICES:
        raise ValueError(f"Geçersiz device: {device!r}. Seçenekler: {', '.join(DEVICE_CHOICES)}")
    if device == "auto":
        return torch.device("cuda" if torch.cuda.is_available() else "cpu")
    if device == "cuda" and not torch.cuda.is_available():
        raise RuntimeError("device='cuda' istendi ancak CUDA kullanılabilir değil.")
    return torch.device(device)
