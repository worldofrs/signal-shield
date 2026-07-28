"""Adversarial protection engine using PGD (Projected Gradient Descent).

Instead of a static phase flip, this engine finds a custom, inaudible perturbation
for each audio file that maximally confuses a speaker encoder model (Resemblyzer).

The attack works by iteratively adjusting a small perturbation (delta) so that the
speaker embedding of (audio + delta) is as far as possible from the original embedding,
while keeping delta small enough to be imperceptible.
"""

import numpy as np
import torch
import torch.nn.functional as F
import torchaudio
from resemblyzer import VoiceEncoder

from app.config import settings

# Resemblyzer's expected parameters (from hparams.py)
_RESEMBLYZER_SR = 16000
_MEL_N_FFT = 400
_MEL_HOP_LENGTH = 160
_MEL_N_MELS = 40
_PARTIALS_N_FRAMES = 160  # 1600ms per partial

# Lazy-loaded encoder singleton — the model weights are ~17MB and only need
# to load once. We keep it at module level so repeated calls reuse it.
_encoder: VoiceEncoder | None = None


def _get_encoder() -> VoiceEncoder:
    """Load the Resemblyzer encoder once, on first use."""
    global _encoder
    if _encoder is None:
        _encoder = VoiceEncoder(device="cpu")
    return _encoder


def _compute_mel_spectrogram(audio: torch.Tensor) -> torch.Tensor:
    """Compute a mel spectrogram using PyTorch ops (fully differentiable).

    Resemblyzer uses a linear-scale (not log) mel spectrogram with:
      - 16kHz sample rate, n_fft=400, hop=160, n_mels=40

    Args:
        audio: 1-D tensor of audio samples at 16kHz.

    Returns:
        Mel spectrogram of shape (n_frames, 40).
    """
    mel_spec_transform = torchaudio.transforms.MelSpectrogram(
        sample_rate=_RESEMBLYZER_SR,
        n_fft=_MEL_N_FFT,
        hop_length=_MEL_HOP_LENGTH,
        n_mels=_MEL_N_MELS,
        power=2.0,
    )
    # torchaudio expects (channel, time) or (time,) — we have (time,)
    mel = mel_spec_transform(audio)  # shape: (n_mels, n_frames)
    return mel.T  # shape: (n_frames, n_mels)


def _get_embedding_differentiable(
    audio: torch.Tensor, encoder: VoiceEncoder
) -> torch.Tensor:
    """Compute a speaker embedding with gradients flowing through the audio.

    Resemblyzer's embed_utterance() uses torch.no_grad(), which blocks gradients.
    This function reimplements the same pipeline using differentiable PyTorch ops:
      1. Compute mel spectrogram (differentiable via torchaudio)
      2. Split into partial utterances (160-frame windows)
      3. Call encoder.forward() directly (differentiable LSTM + linear + ReLU)
      4. Average partials and L2-normalize

    Args:
        audio: 1-D tensor of audio samples at 16kHz (may have requires_grad via delta).
        encoder: The loaded Resemblyzer VoiceEncoder.

    Returns:
        256-dim L2-normalized embedding tensor.
    """
    mel = _compute_mel_spectrogram(audio)  # (n_frames, 40)
    n_frames = mel.shape[0]

    # Split mel into partial utterances of 160 frames each (same as Resemblyzer)
    # Step size ~77 frames corresponds to rate=1.3 partials/sec
    frame_step = 77
    partials = []
    for start in range(0, max(1, n_frames - _PARTIALS_N_FRAMES + 1), frame_step):
        end = start + _PARTIALS_N_FRAMES
        if end <= n_frames:
            partials.append(mel[start:end])

    # If audio is too short for a full partial, pad and use the whole thing
    if len(partials) == 0:
        padded = F.pad(mel, (0, 0, 0, _PARTIALS_N_FRAMES - n_frames))
        partials.append(padded)

    mels_batch = torch.stack(partials)  # (n_partials, 160, 40)

    # Call the encoder's forward() directly — this IS differentiable
    partial_embeds = encoder(mels_batch)  # (n_partials, 256)

    # Average partials and L2-normalize (same as embed_utterance)
    raw_embed = partial_embeds.mean(dim=0)  # (256,)
    embedding = raw_embed / torch.norm(raw_embed, p=2)

    return embedding


def apply_adversarial_protection(y: np.ndarray, sr: int) -> np.ndarray:
    """Apply adversarial perturbation optimized to confuse speaker encoders.

    Uses PGD (Projected Gradient Descent) to find a small perturbation delta such
    that the speaker embedding of (y + delta) is maximally different from the
    embedding of y, while delta stays within [-epsilon, epsilon].

    Same signature as the old apply_phase_protection: (np.ndarray, int) → np.ndarray.

    Args:
        y: Audio samples as a 1-D float32 numpy array.
        sr: Sample rate of the audio.

    Returns:
        Protected audio as a 1-D float32 numpy array (same length as input).
    """
    encoder = _get_encoder()
    encoder.eval()

    # Resample to 16kHz if needed (Resemblyzer expects 16kHz)
    audio_tensor = torch.from_numpy(y.copy()).float()
    if sr != _RESEMBLYZER_SR:
        audio_tensor = torchaudio.functional.resample(
            audio_tensor, orig_freq=sr, new_freq=_RESEMBLYZER_SR
        )

    # Step 1: Get the original embedding (no gradients needed for this)
    with torch.no_grad():
        original_embedding = _get_embedding_differentiable(audio_tensor, encoder)

    # Step 2: Create the perturbation tensor — this is what we optimize
    delta = torch.zeros_like(audio_tensor, requires_grad=True)

    # Step 3: PGD loop — iteratively refine delta to maximize embedding distance
    for _ in range(settings.pgd_steps):
        # Forward pass: get embedding of perturbed audio
        perturbed_audio = audio_tensor + delta
        perturbed_embedding = _get_embedding_differentiable(perturbed_audio, encoder)

        # Loss: cosine similarity (we want to MINIMIZE this, i.e. push embeddings apart)
        loss = F.cosine_similarity(
            original_embedding.unsqueeze(0),
            perturbed_embedding.unsqueeze(0),
        )

        # Backward pass: compute gradient of loss w.r.t. delta
        loss.backward()

        # Update delta in the direction that DECREASES similarity
        # (gradient descent on cosine similarity = moving embeddings apart)
        with torch.no_grad():
            delta_update = delta - settings.pgd_alpha * delta.grad.sign()
            # Project back into epsilon-ball (clamp perturbation magnitude)
            delta_update = torch.clamp(delta_update, -settings.pgd_epsilon, settings.pgd_epsilon)
            delta.data = delta_update

        # Reset gradients for next iteration
        delta.grad.zero_()

    # Step 4: Apply the optimized perturbation
    with torch.no_grad():
        protected_16k = (audio_tensor + delta).numpy()

    # Resample back to original sample rate if we resampled earlier
    if sr != _RESEMBLYZER_SR:
        protected_tensor = torch.from_numpy(protected_16k)
        protected_tensor = torchaudio.functional.resample(
            protected_tensor, orig_freq=_RESEMBLYZER_SR, new_freq=sr
        )
        protected = protected_tensor.numpy()
    else:
        protected = protected_16k

    # Ensure output length matches input exactly
    if len(protected) > len(y):
        protected = protected[: len(y)]
    elif len(protected) < len(y):
        protected = np.pad(protected, (0, len(y) - len(protected)))

    # Clamp the final perturbation to epsilon. The resample round-trip
    # (22050→16000→22050) can amplify delta beyond epsilon due to sinc
    # interpolation overshoot, so we enforce the bound in output space.
    delta_final = protected - y
    delta_final = np.clip(delta_final, -settings.pgd_epsilon, settings.pgd_epsilon)
    protected = y + delta_final

    return protected.astype(np.float32)
