"""Tests for the DSP engine.

Each test checks ONE specific behavior. The test name describes what it verifies.
If a test fails, the name alone should tell you what's broken.
"""

import numpy as np
import librosa
from app.core.dsp_engine import apply_phase_protection
from app.config import settings


def _make_test_signal(duration: float = 1.0) -> tuple[np.ndarray, int]:
    """Helper: generate a simple sine wave for testing.

    This is not a test itself (no 'test_' prefix) — it's a helper that tests call
    to avoid repeating signal-generation code. Helpers like this are called 'fixtures'
    in testing jargon.
    """
    sr = settings.sample_rate
    t = np.linspace(0, duration, int(sr * duration), endpoint=False)
    y = (0.5 * np.sin(2 * np.pi * 440 * t)).astype(np.float32)
    return y, sr


# --- EXAMPLE TEST (study this pattern) ---


def test_output_length_matches_input():
    """The protected audio must be the same length as the input.

    Why this matters: if the output is shorter or longer, it means the
    iSTFT reconstruction went wrong. The user would get a file that's
    a different duration than what they uploaded.
    """
    y, sr = _make_test_signal()
    protected = apply_phase_protection(y, sr)
    assert len(protected) == len(y), f"Expected {len(y)} samples, got {len(protected)}"


# --- YOUR TURN: write the tests below ---
# Run tests with: python3 -m pytest tests/test_dsp_engine.py -v
#
# Test 2: test_magnitude_is_preserved
#   STFT the original and the protected audio. Check that the magnitudes
#   (np.abs of the STFT result) are close to each other.
#   Hint: use np.allclose(..., atol=1e-1) — not exact due to round-trip math
#   Why it matters: if magnitudes change, the audio sounds different

def test_magnitude_is_preserved():
    y, sr = _make_test_signal()
    protected = apply_phase_protection(y, sr)
    original_D = librosa.stft(y, n_fft=settings.n_fft, hop_length=settings.hop_length)
    protected_D = librosa.stft(protected, n_fft=settings.n_fft, hop_length=settings.hop_length)
    assert np.allclose(np.abs(original_D), np.abs(protected_D), atol=1e-1)
#
# Test 3: test_phase_is_inverted_above_threshold
#   STFT the original, separate magnitude/phase with librosa.magphase().
#   Make a copy of phase, then run apply_phase_protection on the original.
#   STFT the result and get its phase. Check that phase DIFFERS above the
#   threshold bin. Use: assert not np.allclose(phase_orig[bin:], phase_prot[bin:])
#   Why it matters: this IS the product — if phase isn't changing, protection isn't working

def test_phase_is_inverted_above_threshold():
    y, sr = _make_test_signal()
    original_D = librosa.stft(y, n_fft=settings.n_fft, hop_length=settings.hop_length)
    o_mag, o_phase = librosa.magphase(original_D)
    o_phase_copy = o_phase.copy()
    protected = apply_phase_protection(y, sr)
    protected_D = librosa.stft(protected, n_fft=settings.n_fft, hop_length=settings.hop_length)
    p_mag, p_phase = librosa.magphase(protected_D)
    freqs = librosa.fft_frequencies(sr=sr, n_fft=settings.n_fft)
    threshold_bin = np.searchsorted(freqs, settings.freq_threshold_hz)
    assert not np.allclose(o_phase[threshold_bin:], p_phase[threshold_bin:])

#
# Test 4: test_output_is_not_all_zeros
#   Run apply_phase_protection and check the output isn't silence.
#   Hint: assert np.max(np.abs(protected)) > 0
#   Why it matters: a common bug is returning an empty/silent array
def test_output_is_not_all_zeros():
    y, sr = _make_test_signal()
    protected = apply_phase_protection(y, sr)
    assert np.max(np.abs(protected)) > 0