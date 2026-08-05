import logging
from io import BytesIO

import librosa
import numpy as np
import soundfile as sf

from app.config import settings

logger = logging.getLogger("signal_shield.audio_io")


def load_audio(file_bytes: bytes, filename: str) -> tuple[np.ndarray, int]:
    """Load audio bytes into a numpy array, resampled to mono at the configured sample rate."""
    logger.info("Loading audio '%s' (%d bytes)", filename, len(file_bytes))
    buf = BytesIO(file_bytes)
    y, sr = librosa.load(buf, sr=settings.sample_rate, mono=True)
    logger.info("Audio loaded: %d samples, sr=%d, duration=%.1fs", len(y), sr, len(y) / sr)
    return y, sr # type: ignore


def export_wav(y: np.ndarray, sr: int) -> bytes:
    """Write a numpy audio array to WAV bytes."""
    buf = BytesIO()
    sf.write(buf, y, sr, format="WAV")
    buf.seek(0)
    wav_bytes = buf.read()
    logger.info("Exported WAV: %d bytes", len(wav_bytes))
    return wav_bytes
