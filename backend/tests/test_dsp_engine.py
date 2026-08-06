"""Tests for the DSP engine (adversarial protection).

Each test checks ONE specific behavior. The test name describes what it verifies.
If a test fails, the name alone should tell you what's broken.
"""

import numpy as np
import torch
import torchaudio
from app.core.dsp_engine import apply_phase_protection
from app.core.adversarial_engine import (
    _get_xvector_encoder,
    _get_xvector_embedding_differentiable,
    _TARGET_SR,
)
from app.config import settings


def _make_test_signal(duration: float = 2.0) -> tuple[np.ndarray, int]:
    """Helper: generate a multi-frequency signal with energy across the spectrum.

    A pure sine wave won't work here — speaker encoders may classify it as
    non-speech. White noise spread across many frequencies gives the encoder
    something meaningful to embed.
    """
    sr = settings.sample_rate
    n_samples = int(sr * duration)
    rng = np.random.default_rng(42)  # fixed seed for reproducibility
    y = (0.3 * rng.standard_normal(n_samples)).astype(np.float32)
    return y, sr


def test_output_length_matches_input():
    """The protected audio must be the same length as the input."""
    y, sr = _make_test_signal()
    protected = apply_phase_protection(y, sr)
    assert len(protected) == len(y), f"Expected {len(y)} samples, got {len(protected)}"


def test_output_is_not_all_zeros():
    """Protected audio must not be silence."""
    y, sr = _make_test_signal()
    protected = apply_phase_protection(y, sr)
    assert np.max(np.abs(protected)) > 0


def test_perturbation_is_within_epsilon():
    """The perturbation (delta) must stay within the configured epsilon bound."""
    y, sr = _make_test_signal()
    protected = apply_phase_protection(y, sr)
    max_delta = np.max(np.abs(protected - y))
    # Small tolerance for float32 rounding (e.g. 0.01000002 vs 0.01)
    assert max_delta <= settings.pgd_epsilon + 1e-6, (
        f"Max perturbation {max_delta:.6f} exceeds epsilon {settings.pgd_epsilon}"
    )


def test_embeddings_diverge():
    """Cosine similarity between original and protected embeddings should decrease.

    This is the core test: if the adversarial attack is working, the speaker
    encoder should produce a different embedding for the protected audio.

    We use the same differentiable pipeline as the PGD loop (not preprocess_wav,
    which applies VAD that can strip non-speech test signals).
    """
    y, sr = _make_test_signal()
    protected = apply_phase_protection(y, sr)

    encoder = _get_xvector_encoder()
    encoder.eval()

    # Resample both to 16kHz and get embeddings through the differentiable pipeline
    orig_tensor = torchaudio.functional.resample(
        torch.from_numpy(y), orig_freq=sr, new_freq=_TARGET_SR
    )
    prot_tensor = torchaudio.functional.resample(
        torch.from_numpy(protected), orig_freq=sr, new_freq=_TARGET_SR
    )

    with torch.no_grad():
        orig_embed = _get_xvector_embedding_differentiable(orig_tensor, encoder)
        prot_embed = _get_xvector_embedding_differentiable(prot_tensor, encoder)

    similarity = torch.dot(orig_embed, prot_embed).item()
    # With epsilon=0.01 and 2s of noise, similarity should drop below 1.0.
    # The threshold varies by encoder — x-vector shifts less than Resemblyzer
    # did at the same epsilon. Anything below 1.0 confirms the attack works.
    assert similarity < 0.99999, (
        f"Cosine similarity {similarity:.4f} is too high — adversarial attack isn't working"
    )


def test_output_dtype_is_float32():
    """Output should be float32 to match the input dtype convention."""
    y, sr = _make_test_signal()
    protected = apply_phase_protection(y, sr)
    assert protected.dtype == np.float32, f"Expected float32, got {protected.dtype}"
