import os
from io import BytesIO
from pathlib import Path
from tempfile import NamedTemporaryFile

import librosa
import numpy as np
import soundfile as sf

from app.config import settings


def load_audio(file_bytes: bytes, filename: str) -> tuple[np.ndarray, int]:
    """Load audio bytes into a numpy array, resampled to mono at the configured sample rate."""
    suffix = Path(filename).suffix.lower() or ".wav"
    # Write to a named temp file so ffmpeg (via librosa/audioread) can
    # detect format from the extension — needed for .mp3 / .m4a.
    # delete=False + manual unlink: on Windows the file must be closed
    # before another process (ffmpeg) can open it.
    tmp = NamedTemporaryFile(suffix=suffix, delete=False)
    try:
        tmp.write(file_bytes)
        tmp.close()
        y, sr = librosa.load(tmp.name, sr=settings.sample_rate, mono=True)
    finally:
        os.unlink(tmp.name)
    return y, sr  # type: ignore


def export_wav(y: np.ndarray, sr: int) -> bytes:
    """Write a numpy audio array to WAV bytes."""
    buf = BytesIO()
    sf.write(buf, y, sr, format="WAV")
    buf.seek(0)
    return buf.read()
