"""Adversarial protection engine using PGD (Projected Gradient Descent).

Instead of a static phase flip, this engine finds a custom, inaudible perturbation
for each audio file that maximally confuses a speaker encoder model (Resemblyzer).

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
from resemblyzer import VoiceEncoder
from app.config import settings

# Must match scripts/prefetch_models.py and Dockerfile ENV when set.
_ECAPA_SAVEDIR = os.environ.get(
    "SS_ECAPA_SAVEDIR",
    "pretrained_models/spkrec-ecapa-voxceleb",
)
logger = logging.getLogger("signal_shield.adversarial")

# Configure PyTorch thread count for parallel tensor operations
_thread_count = settings.torch_threads if settings.torch_threads > 0 else (os.cpu_count() or 4)
torch.set_num_threads(_thread_count)
logger.info("PyTorch using %d threads", _thread_count)

# Resemblyzer's expected parameters (from hparams.py)
_RESEMBLYZER_SR = 16000
_MEL_N_FFT = 400
_MEL_HOP_LENGTH = 160
_MEL_N_MELS = 40
_PARTIALS_N_FRAMES = 160  # 1600ms per partial

# Lazy-loaded encoder singletons
_encoder: Optional[VoiceEncoder] = None
_ecapa_encoder = None
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
            source="speechbrain/spkrec-ecapa-voxceleb",
            savedir=_ECAPA_SAVEDIR,
        )
        logger.info("ECAPA-TDNN encoder loaded")
    return _ecapa_encoder

def _get_hubert_model():
    from transformers import HubertModel
    global _hubert_model
    if _hubert_model is None:
        logger.info("Loading HuBERT encoder...")
        _hubert_model = HubertModel.from_pretrained("facebook/hubert-base-ls960")
        _hubert_model.requires_grad_(False)
        _hubert_model.eval()
        logger.info("HuBERT encoder loaded")
    return _hubert_model

def _encoder_factories() -> list:
    """Return a list of (name, loader_fn, embed_fn_factory) tuples."""
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
    """Compute a mel spectrogram using PyTorch ops (fully differentiable)."""
    mel_spec_transform = torchaudio.transforms.MelSpectrogram(
        sample_rate=_RESEMBLYZER_SR,
        n_fft=_MEL_N_FFT,
        hop_length=_MEL_HOP_LENGTH,
        n_mels=_MEL_N_MELS,
        power=2.0,
    )
    mel = mel_spec_transform(audio)  # shape: (n_mels, n_frames)
    return mel.T  # shape: (n_frames, n_mels)


def _get_embedding_differentiable(
    audio: torch.Tensor, encoder: VoiceEncoder
) -> torch.Tensor:
    """Compute a speaker embedding with gradients flowing through the audio."""
    mel = _compute_mel_spectrogram(audio)  # (n_frames, 40)
    n_frames = mel.shape[0]

    frame_step = 77
    partials = []
    for start in range(0, max(1, n_frames - _PARTIALS_N_FRAMES + 1), frame_step):
        end = start + _PARTIALS_N_FRAMES
        if end <= n_frames:
            partials.append(mel[start:end])

    if len(partials) == 0:
        padded = F.pad(mel, (0, 0, 0, _PARTIALS_N_FRAMES - n_frames))
        partials.append(padded)

    mels_batch = torch.stack(partials)  # (n_partials, 160, 40)
    partial_embeds = encoder(mels_batch)  # (n_partials, 256)

    raw_embed = partial_embeds.mean(dim=0)  # (256,)
    embedding = raw_embed / torch.norm(raw_embed, p=2)
    return embedding

def _get_ecapa_embedding_differentiable(
        audio: torch.Tensor, classifier
) -> torch.Tensor:
    wavs = audio.unsqueeze(0)
    wav_lens = torch.tensor([1.0])

    feats = classifier.mods.compute_features(wavs)  # type: ignore
    feats = classifier.mods.mean_var_norm(feats, wav_lens)  # type: ignore
    embeddings = classifier.mods.embedding_model(feats)  # type: ignore

    embeddings = embeddings.squeeze()
    return embeddings / torch.norm(embeddings, p=2)

def _get_hubert_embedding_differentiable(
        audio: torch.Tensor, model
) -> torch.Tensor:
    audio_normalized = (audio - audio.mean()) / (audio.std() + 1e-7)

    outputs = model(input_values=audio_normalized.unsqueeze(0))
    hidden_states = outputs.last_hidden_state  # (1, n_frames, 768)

    embedding = hidden_states.mean(dim=1).squeeze()  # (768,)
    return embedding / torch.norm(embedding, p=2)

VALID_ENCODERS = {"resemblyzer", "ecapa", "hubert"}

# ~1s of silence at 16kHz — enough to exercise each embed path at warmup.
_WARMUP_AUDIO = torch.zeros(16_000)


def warmup_encoders(names: Optional[list[str]] = None) -> None:
    """Load encoder weights into RAM and run a dummy forward pass."""
    factories = _encoder_factories()
    if names is not None:
        factories = [(n, l, e) for n, l, e in factories if n in names]

    for name, loader_fn, embed_fn_factory in factories:
        print(f"Warming up encoder: {name}")
        model = loader_fn()
        model.eval()
        embed_fn = embed_fn_factory(model)
        with torch.no_grad():
            embed_fn(_WARMUP_AUDIO)
        print(f"Encoder ready: {name}")


def apply_adversarial_protection(
    y: np.ndarray, sr: int, encoders: Optional[list[str]] = None
) -> np.ndarray:
    """Apply adversarial perturbation using joint PGD across all selected encoders."""
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

    # Extract the learned perturbation (at 16kHz)
    with torch.no_grad():
        delta_16k = delta.detach()

        # Resample only the delta back to the original sample rate.
        if sr != _RESEMBLYZER_SR:
            delta_orig = torchaudio.functional.resample(
                delta_16k, orig_freq=_RESEMBLYZER_SR, new_freq=sr
            ).numpy()
        else:
            delta_orig = delta_16k.numpy()

        # Match length to original audio
        if len(delta_orig) > len(y):
            delta_orig = delta_orig[: len(y)]
        elif len(delta_orig) < len(y):
            delta_orig = np.pad(delta_orig, (0, len(y) - len(delta_orig)))

        # Clamp to epsilon and apply to original (untouched) audio
        delta_orig = np.clip(delta_orig, -settings.pgd_epsilon, settings.pgd_epsilon)
        protected = y + delta_orig

    return protected.astype(np.float32)

def _apply_input_diversity(audio: torch.Tensor) -> torch.Tensor:
    audio = torch.roll(audio, torch.randint(-50, 51, (1,)).item())
    audio = audio + 0.001 * torch.randn_like(audio)
    audio = audio * torch.empty(1).uniform_(0.95, 1.05)
    return audio
