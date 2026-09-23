import pytest
import torch

from diarization.device import resolve_device


@pytest.fixture
def cuda_available(monkeypatch):
    monkeypatch.setattr(torch.cuda, "is_available", lambda: True)


@pytest.fixture
def cuda_unavailable(monkeypatch):
    monkeypatch.setattr(torch.cuda, "is_available", lambda: False)


def test_auto_uses_cuda_when_available(cuda_available):
    assert resolve_device("auto") == torch.device("cuda")


def test_auto_falls_back_to_cpu(cuda_unavailable):
    assert resolve_device("auto") == torch.device("cpu")


def test_default_is_auto(cuda_unavailable):
    assert resolve_device() == torch.device("cpu")


@pytest.mark.parametrize("available", [True, False])
def test_cpu_always_cpu(monkeypatch, available):
    monkeypatch.setattr(torch.cuda, "is_available", lambda: available)
    assert resolve_device("cpu") == torch.device("cpu")


def test_cuda_when_available(cuda_available):
    assert resolve_device("cuda") == torch.device("cuda")


def test_cuda_when_unavailable_raises(cuda_unavailable):
    with pytest.raises(RuntimeError, match="CUDA"):
        resolve_device("cuda")


@pytest.mark.parametrize("value", ["gpu", "CUDA", "cuda:1", ""])
def test_invalid_value_raises(value):
    with pytest.raises(ValueError, match="Geçersiz device"):
        resolve_device(value)
