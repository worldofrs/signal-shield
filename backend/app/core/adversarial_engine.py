"""Adversarial protection engine using PGD (Projected Gradient Descent).

Instead of a static phase flip, this engine finds a custom, inaudible perturbation
for each audio file that maximally confuses a speaker encoder model (Resemblyzer).

The attack works by iteratively adjusting a small perturbation (delta) so that the
speaker embedding of (audio + delta) is as far as possible from the original embedding,
while keeping delta small enough to be imperceptible.
"""

import gc
import logging
import os
import time
from typing import Optional

import numpy as np
import torch
import torch.nn.functional as F
import torchaudio
from resemblyzer import VoiceEncoder
from app.config import settings

logger = logging.getLogger("signal_shield.adversarial")

# Configure PyTorch thread count for parallel tensor operations
_thread_count = settings.torch_threads if settings.torch_threads > 0 else (os.cpu_count() or 4)
torch.set_num_threads(_thread_count)
logger.info("PyTorch using %d threads", _thread_count)

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
_encoder: Optional[VoiceEncoder] = None
_ecapa_encoder = None
_hubert_model = None

def _clear_model_cache(name: str):
    """Remove a model from the singleton cache to free memory."""
    global _encoder, _ecapa_encoder, _hubert_model
    if name == "resemblyzer":
        _encoder = None
    elif name == "ecapa":
        _ecapa_encoder = None
    elif name == "hubert":
        _hubert_model = None


def _get_encoder() -> VoiceEncoder:
    """Load the Resemblyzer encoder once, on first use."""
    global _encoder
    if _encoder is None:
        logger.info("Loading Resemblyzer encoder...")
        _encoder = VoiceEncoder(device="cpu")
        logger.info("Resemblyzer encoder loaded")
    return _encoder

def _get_ecapa_encoder():
    from speechbrain.inference.speaker import EncoderClassifier
    global _ecapa_encoder
    if _ecapa_encoder is None:
        logger.info("Loading ECAPA-TDNN encoder...")
        _ecapa_encoder = EncoderClassifier.from_hparams(
            source="speechbrain/spkrec-ecapa-voxceleb"
        )
        logger.info("ECAPA-TDNN encoder loaded")
    return _ecapa_encoder

def _get_hubert_model():
    from transformers import HubertModel
    global _hubert_model
    if _hubert_model is None:
        logger.info("Loading HuBERT encoder...")
        _hubert_model = HubertModel.from_pretrained("facebook/hubert-base-ls960")
        logger.info("HuBERT encoder loaded")
    return _hubert_model

def _encoder_factories() -> list:
    """Return a list of (name, loader_fn, embed_fn_factory) tuples.

    Each loader_fn() returns the model, and embed_fn_factory(model)
    returns the embedding function. Models are NOT loaded here —
    the caller decides when to load/unload.
    """
    return [
        (
            "resemblyzer",
            _get_encoder,
            lambda enc: lambda audio, e=enc: _get_embedding_differentiable(audio, e),
        ),
        (
            "ecapa",
            _get_ecapa_encoder,
            lambda enc: lambda audio, e=enc: _get_ecapa_embedding_differentiable(audio, e),
        ),
        (
            "hubert",
            _get_hubert_model,
            lambda enc: lambda audio, e=enc: _get_hubert_embedding_differentiable(audio, e),
        ),
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
        audio: torch.Tensor, classifier
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

def _get_hubert_embedding_differentiable(
        audio: torch.Tensor, model
) -> torch.Tensor:
    # Normalize (same as Wav2Vec2FeatureExtractor but differentiable)
    audio_normalized = (audio - audio.mean()) / (audio.std() + 1e-7)

    # Forward pass — returns frame-level features, not an embedding
    outputs = model(input_values=audio_normalized.unsqueeze(0))
    hidden_states = outputs.last_hidden_state  # (1, n_frames, 768)

    # Mean pool across frames to get a single vector
    embedding = hidden_states.mean(dim=1).squeeze()  # (768,)
    return embedding / torch.norm(embedding, p=2)

VALID_ENCODERS = {"resemblyzer", "ecapa", "hubert"}


def apply_adversarial_protection(
    y: np.ndarray, sr: int, encoders: Optional[list[str]] = None
) -> np.ndarray:
    """Apply adversarial perturbation optimized to confuse speaker encoders.

    Uses joint optimization: all selected encoders are loaded simultaneously,
    and a single PGD loop minimizes the sum of cosine similarities across all
    encoders. This produces better adversarial examples than sequential
    optimization and runs the full pgd_steps (not divided per encoder).

    Args:
        y: Audio samples as a 1-D float32 numpy array.
        sr: Sample rate of the audio.
        encoders: List of encoder names to use (subset of VALID_ENCODERS).
                  Defaults to all encoders when None.

    Returns:
        Protected audio as a 1-D float32 numpy array (same length as input).
    """
    factories = _encoder_factories()
    if encoders is not None:
        factories = [(n, l, e) for n, l, e in factories if n in encoders]

    encoder_names = [n for n, _, _ in factories]
    logger.info("Starting adversarial protection with encoders: %s, audio length: %d samples", encoder_names, len(y))

    # Resample to 16kHz if needed (Resemblyzer expects 16kHz)
    audio_tensor = torch.from_numpy(y.copy()).float()
    if sr != _RESEMBLYZER_SR:
        audio_tensor = torchaudio.functional.resample(
            audio_tensor, orig_freq=sr, new_freq=_RESEMBLYZER_SR
        )

    # --- Load all selected encoders at once ---
    loaded_encoders: list[tuple[str, object]] = []  # (name, embed_fn)
    load_start = time.time()
    for name, loader_fn, embed_fn_factory in factories:
        try:
            logger.info("Loading encoder '%s'...", name)
            model = loader_fn()
            model.eval()
            embed_fn = embed_fn_factory(model)
            loaded_encoders.append((name, embed_fn))
            logger.info("Encoder '%s' loaded", name)
        except Exception:
            logger.exception("Encoder '%s' failed to load, skipping", name)
    logger.info("Loaded %d/%d encoders in %.1fs", len(loaded_encoders), len(factories), time.time() - load_start)

    if not loaded_encoders:
        raise RuntimeError("No encoder could be loaded successfully")

    # --- Compute original embeddings for all encoders (no grad needed) ---
    original_embeddings: list[torch.Tensor] = []
    with torch.no_grad():
        for name, embed_fn in loaded_encoders:
            original_embeddings.append(embed_fn(audio_tensor))

    # --- Single joint PGD loop ---
    delta = torch.zeros_like(audio_tensor, requires_grad=True)
    pgd_start = time.time()
    logger.info("Running %d joint PGD steps across %d encoders", settings.pgd_steps, len(loaded_encoders))

    for step in range(settings.pgd_steps):
        perturbed_audio = audio_tensor + delta
        perturbed_audio = _apply_input_diversity(perturbed_audio)

        # Sum cosine similarities across all encoders
        total_loss = torch.tensor(0.0)
        for (name, embed_fn), orig_emb in zip(loaded_encoders, original_embeddings):
            pert_emb = embed_fn(perturbed_audio)
            total_loss = total_loss + F.cosine_similarity(
                orig_emb.unsqueeze(0), pert_emb.unsqueeze(0)
            )

        total_loss.backward()

        with torch.no_grad():
            delta_update = delta - settings.pgd_alpha * delta.grad.sign()  # type: ignore
            delta_update = torch.clamp(delta_update, -settings.pgd_epsilon, settings.pgd_epsilon)
            delta.data = delta_update

        delta.grad.zero_()  # type: ignore

    logger.info("Joint PGD complete in %.1fs", time.time() - pgd_start)

    # --- Unload all models to free memory ---
    loaded_encoder_names = [name for name, _ in loaded_encoders]
    del loaded_encoders, original_embeddings
    for name in loaded_encoder_names:
        _clear_model_cache(name)
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
    gc.collect()

    # Apply the optimized perturbation
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