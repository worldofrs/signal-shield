from io import BytesIO

import librosa
import numpy as np
import soundfile as sf

from app.config import settings


def load_audio(file_bytes: bytes, filename: str) -> tuple[np.ndarray, int]:
    """Load audio bytes into a numpy array, resampled to mono at the configured sample rate."""
    buf = BytesIO(file_bytes)
    y, sr = librosa.load(buf, sr=settings.sample_rate, mono=True)
    return y, sr # type: ignore


def export_wav(y: np.ndarray, sr: int) -> bytes:
    """Write a numpy audio array to WAV bytes."""
    buf = BytesIO()
    sf.write(buf, y, sr, format="WAV")
    buf.seek(0)
    return buf.read()
