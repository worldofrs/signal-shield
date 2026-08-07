"""Adversarial protection engine using PGD (Projected Gradient Descent).

Instead of a static phase flip, this engine finds a custom, inaudible perturbation
for each audio file that maximally confuses speaker encoder models (x-vector,
ECAPA-TDNN, HuBERT).

The attack works by iteratively adjusting a small perturbation (delta) so that the
speaker embedding of (audio + delta) is as far as possible from the original embedding,
while keeping delta small enough to be imperceptible.
"""

import logging
import os
import time
from typing import Optional

import numpy as np
import torch
import torch.nn.functional as F
import torchaudio
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

# All speaker encoders expect 16 kHz input
_TARGET_SR = 16000

# Lazy-loaded encoder singletons — model weights only need to load once.
_xvector_encoder = None
_ecapa_encoder = None
_hubert_model = None


def _get_xvector_encoder():
    """Load the x-vector TDNN encoder once, on first use.

    Uses settings.xvector_model_path if set (for custom-trained models),
    otherwise falls back to SpeechBrain's pretrained HuggingFace model.
    """
    from speechbrain.inference.speaker import EncoderClassifier
    global _xvector_encoder
    if _xvector_encoder is None:
        source = settings.xvector_model_path or "speechbrain/spkrec-xvect-voxceleb"
        logger.info("Loading x-vector encoder from %s...", source)
        _xvector_encoder = EncoderClassifier.from_hparams(source=source)
        logger.info("X-vector encoder loaded")
    return _xvector_encoder

def _get_ecapa_encoder():
    """Load the ECAPA-TDNN encoder once, on first use.

    Uses settings.ecapa_model_path if set (for custom-trained models),
    otherwise falls back to SpeechBrain's pretrained HuggingFace model.
    """
    from speechbrain.inference.speaker import EncoderClassifier
    global _ecapa_encoder
    if _ecapa_encoder is None:
        source = settings.ecapa_model_path or "speechbrain/spkrec-ecapa-voxceleb"
        logger.info("Loading ECAPA-TDNN encoder from %s...", source)
        _ecapa_encoder = EncoderClassifier.from_hparams(source=source)
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
            "xvector",
            _get_xvector_encoder,
            lambda enc: lambda audio, e=enc: _get_xvector_embedding_differentiable(audio, e),
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


def _get_xvector_embedding_differentiable(
        audio: torch.Tensor, classifier
) -> torch.Tensor:
    """Compute x-vector embedding with gradients flowing through the audio.

    Calls SpeechBrain's internal modules directly (bypassing encode_batch which
    uses torch.no_grad), so PGD gradients can propagate back to the audio.
    """
    wavs = audio.unsqueeze(0)
    wav_lens = torch.tensor([1.0])

    feats = classifier.mods.compute_features(wavs)  # type: ignore
    feats = classifier.mods.mean_var_norm(feats, wav_lens)  # type: ignore
    embeddings = classifier.mods.embedding_model(feats)  # type: ignore

    embeddings = embeddings.squeeze()
    return embeddings / torch.norm(embeddings, p=2)

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

VALID_ENCODERS = {"xvector", "ecapa", "hubert"}


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

    # Resample to 16kHz if needed (all encoders expect 16kHz)
    audio_tensor = torch.from_numpy(y.copy()).float()
    if sr != _TARGET_SR:
        audio_tensor = torchaudio.functional.resample(
            audio_tensor, orig_freq=sr, new_freq=_TARGET_SR
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

    # Extract the learned perturbation (at 16kHz)
    with torch.no_grad():
        delta_16k = delta.detach()

        # Resample only the delta back to the original sample rate
        if sr != _TARGET_SR:
            delta_orig = torchaudio.functional.resample(
                delta_16k, orig_freq=_TARGET_SR, new_freq=sr
            ).numpy()
        else:
            delta_orig = delta_16k.numpy()

        # Match length to original audio
        if len(delta_orig) > len(y):
            delta_orig = delta_orig[: len(y)]
        elif len(delta_orig) < len(y):
            delta_orig = np.pad(delta_orig, (0, len(y) - len(delta_orig)))

        # Clamp to epsilon
        delta_orig = np.clip(delta_orig, -settings.pgd_epsilon, settings.pgd_epsilon)

        # Perceptual masking: scale perturbation by local audio amplitude
        # so quiet/silent regions get near-zero perturbation while loud
        # regions get full strength (where the audio masks it).
        window = int(0.03 * sr)  # 30ms smoothing window
        if window % 2 == 0:
            window += 1
        envelope = np.convolve(np.abs(y), np.ones(window) / window, mode="same")
        envelope_max = envelope.max() or 1.0
        mask = envelope / envelope_max  # 0..1: silent→loud
        delta_orig = delta_orig * mask

        original_peak = np.abs(y).max() or 1.0
        protected = y + delta_orig

        # Preserve original loudness — rescale so peak matches input
        if settings.preserve_loudness:
            protected_peak = np.abs(protected).max() or 1.0
            protected = protected * (original_peak / protected_peak)

    return protected.astype(np.float32)

def _apply_input_diversity(audio: torch.Tensor) -> torch.Tensor:
    audio = torch.roll(audio, torch.randint(-50, 51, (1,)).item())
    audio = audio + 0.001 * torch.randn_like(audio)
    audio = audio * torch.empty(1).uniform_(0.95, 1.05)
    return audio