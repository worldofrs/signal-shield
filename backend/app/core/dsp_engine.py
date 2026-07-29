import librosa
import numpy as np

from app.config import settings


def apply_phase_protection(y: np.ndarray, sr: int) -> np.ndarray:
    """Apply high-frequency phase inversion to immunize audio against voice cloning.

    The magnitude spectrum is left untouched (preserving perceived audio quality),
    while phase coherence above the frequency threshold is destroyed.
    """
    # STFT: convert time-domain audio into a complex spectrogram
    D = librosa.stft(y, n_fft=settings.n_fft, hop_length=settings.hop_length)
    print("converting")
    # Separate magnitude and phase
    magnitude, phase = librosa.magphase(D)

    # Find which frequency bin corresponds to the threshold
    freqs = librosa.fft_frequencies(sr=sr, n_fft=settings.n_fft)
    threshold_bin = np.searchsorted(freqs, settings.freq_threshold_hz)
    print("still converting")

    # Invert phase above the threshold (pi-radian shift)
    phase[threshold_bin:, :] *= -1

    # Reconstruct time-domain audio from modified spectrogram
    protected = librosa.istft(magnitude * phase, hop_length=settings.hop_length, length=len(y))
    print("file protected!")

    return protected
