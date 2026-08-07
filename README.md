# Signal Shield

An audio post-processing API that protects voice recordings against AI voice cloning without degrading audio quality.

## The Problem

AI voice cloning tools can take a short audio clip of someone's voice and generate realistic speech that sounds like them. This creates risks for fraud, impersonation, and unauthorized use of someone's voice.

## How It Works

Signal Shield processes audio files to make them unusable for voice cloning while keeping them sounding identical to human ears.

### Adversarial Optimization (Current Approach)

Signal Shield uses **adversarial optimization** powered by PGD (Projected Gradient Descent) and multiple speaker encoder models. Instead of a fixed transformation, the system finds the smallest possible perturbation for each audio file that maximally disrupts speaker recognition.

```
                    ┌──► X-Vector Encoder ──────┐
  Audio ──┬─────────┤                           ├──► Loss (sum of cosine similarities)
          │         └──► ECAPA-TDNN Encoder ────┘              │
          │                    ▲                    gradient    │
          │                    │                               │
          │               perturbation ◄───────────────────────┘
          │                    │
          └──► Add Perturbation ──► Protected Audio

  Custom perturbation per file.
  Joint optimization across multiple encoder architectures.
  Perturbation clamped to ±0.0005 amplitude (inaudible).
  Perceptual masking shapes perturbation to follow audio envelope.
```

### How PGD Works

1. **Get original embeddings** — run the audio through all selected encoders to get speaker embedding vectors
2. **Create perturbation** — start with a zero-valued delta tensor (same length as audio)
3. **Optimize** — for 30 iterations:
   - Compute embeddings of (audio + delta) across all encoders
   - Sum cosine similarities to original embeddings
   - Backpropagate to find which direction to push each sample
   - Update delta by a small step in that direction
   - Clamp delta to [-epsilon, epsilon] so it stays inaudible
4. **Perceptual masking** — scale the perturbation by the audio's local amplitude envelope so quiet/silent regions get near-zero perturbation while loud regions retain full adversarial strength
5. **Output** — return audio + masked perturbation at the original sample rate

### Custom-Trained Models

The bundled x-vector and ECAPA-TDNN models were trained from scratch on **LibriSpeech train-clean-360** (~921 speakers, 10 epochs each) using the [SpeechBrain](https://github.com/speechbrain/speechbrain) speaker verification recipes. Training was performed on Vast.ai GPU instances.

Using custom-trained models instead of the default VoxCeleb-pretrained weights ensures the model weights are trained exclusively on permissively licensed data (see [Licensing](#licensing) below).

### Making It Differentiable

SpeechBrain's `encode_batch()` uses `torch.no_grad()`, which blocks gradient flow. To make PGD work, the engine calls the encoder's internal modules directly:

- `compute_features` — Fbank feature extraction
- `mean_var_norm` — input normalization
- `embedding_model` — the TDNN/ECAPA-TDNN encoder

This bypasses the no-grad wrapper so gradients propagate back to the audio tensor.

## Architecture

Two services, one repo:

```
signal-shield/
├── backend/                ← Python (FastAPI)
│   ├── app/
│   │   ├── main.py         ← API server, CORS, health check
│   │   ├── config.py       ← All settings (env var configurable)
│   │   ├── api/v1/
│   │   │   └── router.py   ← POST /api/v1/protect endpoint
│   │   └── core/
│   │       ├── adversarial_engine.py  ← PGD optimization loop (the core engine)
│   │       ├── dsp_engine.py          ← Public interface, delegates to adversarial engine
│   │       └── audio_io.py            ← Audio loading and WAV export
│   ├── models/
│   │   ├── xvector/        ← Custom-trained x-vector checkpoint (~19MB)
│   │   └── ecapa/          ← Custom-trained ECAPA-TDNN checkpoint (~80MB)
│   ├── training/           ← Scripts to reproduce model training (see training/README.md)
│   ├── tests/              ← Adversarial + API tests
│   ├── Dockerfile          ← Production container
│   └── requirements.txt
│
├── frontend/               ← TypeScript (Next.js)
│   ├── src/
│   │   ├── app/page.tsx    ← Upload page
│   │   ├── components/     ← UI components
│   │   └── lib/api.ts      ← Backend API client
│   └── Dockerfile          ← Multi-stage production container
```

### Request Flow

```
  Browser                    Frontend (Next.js)              Backend (FastAPI)
  ┌──────┐                   ┌──────────────┐               ┌──────────────┐
  │ User │                   │              │               │              │
  │ drops│  ── file ──────►  │  FileUploader│  ── POST ──►  │  /api/v1/    │
  │ file │                   │              │    (fetch)    │  protect     │
  │      │                   │  Processing  │               │              │
  │      │                   │  Status:     │               │  1. Validate │
  │      │                   │  spinner...  │               │  2. Load     │
  │      │                   │              │               │  3. Resample │
  │      │                   │  Download    │  ◄── WAV ──   │  4. PGD loop │
  │      │  ◄─ click ──────  │  Button      │    (bytes)    │  5. Export   │
  │      │                   │              │               │              │
  └──────┘                   └──────────────┘               └──────────────┘
```

## Tech Stack

| Layer | Technology | Why |
|-------|-----------|-----|
| Adversarial ML | PyTorch + torchaudio | Differentiable computation graph for gradient-based optimization |
| Speaker Encoders | SpeechBrain (x-vector + ECAPA-TDNN) | Custom-trained on LibriSpeech, joint optimization across architectures |
| API | FastAPI | Async Python web framework with built-in validation and docs |
| Audio I/O | librosa + soundfile | Industry-standard audio loading and WAV export |
| Frontend | Next.js + Tailwind | React framework with standalone build for Docker |
| Deployment | Railway + Docker | Two services from one repo, env var configuration |

## Configuration

All configurable via `SS_`-prefixed environment variables.

| Parameter | Default | What it controls |
|-----------|---------|-----------------|
| `pgd_steps` | 30 | Number of PGD optimization iterations |
| `pgd_epsilon` | 0.0005 | Max perturbation amplitude (imperceptibility bound) |
| `pgd_alpha` | 0.0001 | Step size per PGD iteration |
| `xvector_model_path` | `models/xvector` | Path to x-vector checkpoint directory |
| `ecapa_model_path` | `models/ecapa` | Path to ECAPA-TDNN checkpoint directory |
| `preserve_loudness` | true | Rescale output to match input peak amplitude |

## Running Locally

**Backend:**
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:3000`, upload a `.wav` or `.mp3` file, and download the protected result. The first request is slower because the encoder models load on first use; subsequent requests reuse the warm models.

## Tests

```bash
cd backend
python3 -m pytest tests/ -v
```

Tests verify:
- Output length matches input
- Output is not silence
- Perturbation stays within epsilon bound (inaudible)
- Speaker embeddings diverge (cosine similarity decreases)
- Output dtype is float32
- API returns correct status codes for valid files, bad formats, and oversized files

## Deploying to Railway

Both services deploy from the same repo using their respective Dockerfiles.

**Backend service:**
- Root directory: `backend`
- Set `SS_ALLOWED_ORIGINS` to the frontend's Railway URL

**Frontend service:**
- Root directory: `frontend`
- Set `NEXT_PUBLIC_API_URL` to the backend's Railway URL (build-time variable)

The backend uses CPU-only PyTorch builds to keep the Docker image small (~500MB vs ~2.5GB with CUDA).

## Limitations

- **Surrogate-based protection.** Protection is optimized against x-vector and ECAPA-TDNN encoders. Cloning tools using different architectures may not be fully disrupted, though joint optimization across multiple architectures improves transferability.
- **Mono output.** Stereo audio is mixed to mono during processing.
- **50MB file size limit.** Processing a 50MB WAV uses ~40-60MB of peak memory.

## Licensing

Signal Shield uses only permissively licensed components:

| Component | License | Notes |
|-----------|---------|-------|
| [SpeechBrain](https://github.com/speechbrain/speechbrain) | Apache 2.0 | Training framework and model architectures |
| [LibriSpeech](https://www.openslr.org/12) | CC BY 4.0 | Training data (derived from LibriVox public domain audiobooks) |
| Model weights (bundled) | Trained from scratch | No VoxCeleb data or pretrained weights used; all weights derived from LibriSpeech training |

The bundled x-vector and ECAPA-TDNN checkpoints in `backend/models/` were trained from scratch on LibriSpeech train-clean-360. They do **not** use or derive from VoxCeleb-pretrained weights, avoiding the licensing ambiguity of VoxCeleb's research-only dataset.

## Roadmap

- [x] PyTorch adversarial optimization (replace static DSP)
- [x] Dockerized deployment (Railway-ready)
- [x] Custom-trained models on permissively licensed data
- [x] Joint multi-encoder optimization
- [x] Perceptual masking for audio quality
- [ ] Validate protection against real cloning tools (RVC, XTTS)
- [ ] Audio preview/playback in browser
- [ ] Rate limiting
- [ ] Batch file processing
