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
from speechbrain.inference.speaker import EncoderClassifier
from app.config import settings

class _EncoderWrapper:
    """Uniform interface for different speaker encoder architectures."""
    def __init__(self, name, model, embed_fn):
        self.name = name
        self.model = model
        self.embed_fn = embed_fn  # function: (audio_tensor) -> embedding_tensor

    def eval(self):
        self.model.eval()

    def get_embedding(self, audio):
        return self.embed_fn(audio)

# Resemblyzer's expected parameters (from hparams.py)
_RESEMBLYZER_SR = 16000
_MEL_N_FFT = 400
_MEL_HOP_LENGTH = 160
_MEL_N_MELS = 40
_PARTIALS_N_FRAMES = 160  # 1600ms per partial

# Lazy-loaded encoder singleton — the model weights are ~17MB and only need
# to load once. We keep it at module level so repeated calls reuse it.
_encoder: VoiceEncoder | None = None
_ecapa_encoder = None

def _get_encoder() -> VoiceEncoder:
    """Load the Resemblyzer encoder once, on first use."""
    global _encoder
    if _encoder is None:
        _encoder = VoiceEncoder(device="cpu")
    return _encoder

def _get_ecapa_encoder():
    global _ecapa_encoder
    if _ecapa_encoder is None:
        _ecapa_encoder = EncoderClassifier.from_hparams(
            source="speechbrain/spkrec-ecapa-voxceleb"
        )
    return _ecapa_encoder

def _get_encoders() -> list:
    encoder = _get_encoder()
    ecapa_encoder = _get_ecapa_encoder()
    return [
        _EncoderWrapper(
            name="resemblyzer",
            model=encoder,
            embed_fn=lambda audio, enc=encoder: _get_embedding_differentiable(audio, enc)
        ),
        _EncoderWrapper(
            name="ecapa",
            model=ecapa_encoder,
            embed_fn=lambda audio, enc=ecapa_encoder: _get_ecapa_embedding_differentiable(audio, enc)
        )
    ]


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

def _get_ecapa_embedding_differentiable(
        audio: torch.Tensor, classifier: EncoderClassifier
) -> torch.Tensor:
    # SpeechBrain expects (batch, time) — audio is 1D, so unsqueeze
    wavs = audio.unsqueeze(0)
    wav_lens = torch.tensor([1.0])

    # Call internal modules directly (differentiable)
    feats = classifier.mods.compute_features(wavs)  # type: ignore
    feats = classifier.mods.mean_var_norm(feats, wav_lens)  # type: ignore
    embeddings = classifier.mods.embedding_model(feats)  # type: ignore

    # Squeeze out batch/extra dims and L2-normalize
    embeddings = embeddings.squeeze()
    return embeddings / torch.norm(embeddings, p=2)



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
    encoders = _get_encoders()
    for enc in encoders:                                                                                
        enc.eval()

    # Resample to 16kHz if needed (Resemblyzer expects 16kHz)
    audio_tensor = torch.from_numpy(y.copy()).float()
    if sr != _RESEMBLYZER_SR:
        audio_tensor = torchaudio.functional.resample(
            audio_tensor, orig_freq=sr, new_freq=_RESEMBLYZER_SR
        )

    # Step 1: Get the original embedding (no gradients needed for this)
    with torch.no_grad():
        original_embeddings = [enc.get_embedding(audio_tensor) for enc in encoders]

    # Step 2: Create the perturbation tensor — this is what we optimize
    delta = torch.zeros_like(audio_tensor, requires_grad=True)

    # Step 3: PGD loop — iteratively refine delta to maximize embedding distance
    for _ in range(settings.pgd_steps):
        # Forward pass: get embedding of perturbed audio
        perturbed_audio = audio_tensor + delta
        perturbed_audio = _apply_input_diversity(perturbed_audio)
        perturbed_embeddings = [enc.get_embedding(perturbed_audio) for enc in encoders]

        # Loss: cosine similarity (we want to MINIMIZE this, i.e. push embeddings apart)
        loss = torch.tensor(0.0)
        for orig_emb, pert_emb in zip(original_embeddings, perturbed_embeddings):
            loss = loss + F.cosine_similarity(orig_emb.unsqueeze(0), pert_emb.unsqueeze(0))

        # Backward pass: compute gradient of loss w.r.t. delta
        loss.backward()

        # Update delta in the direction that DECREASES similarity
        # (gradient descent on cosine similarity = moving embeddings apart)
        with torch.no_grad():
            delta_update = delta - settings.pgd_alpha * delta.grad.sign() # type: ignore
            # Project back into epsilon-ball (clamp perturbation magnitude)
            delta_update = torch.clamp(delta_update, -settings.pgd_epsilon, settings.pgd_epsilon)
            delta.data = delta_update

        # Reset gradients for next iteration
        delta.grad.zero_() # type: ignore

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
    # can amplify delta beyond epsilon, so we enforce the bound in output space.
    delta_final = protected - y
    delta_final = np.clip(delta_final, -settings.pgd_epsilon, settings.pgd_epsilon)
    protected = y + delta_final

    return protected.astype(np.float32)

def _apply_input_diversity(audio: torch.Tensor) -> torch.Tensor:
    audio = torch.roll(audio, torch.randint(-50, 51, (1,)).item())
    audio = audio + 0.001 * torch.randn_like(audio)
    audio = audio * torch.empty(1).uniform_(0.95, 1.05)
    return audio