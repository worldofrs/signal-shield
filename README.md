# Signal Shield

An audio post-processing API that protects voice recordings against AI voice cloning without degrading audio quality.

## The Problem

AI voice cloning tools can take a short audio clip of someone's voice and generate realistic speech that sounds like them. This creates risks for fraud, impersonation, and unauthorized use of someone's voice.

## How It Works

Signal Shield processes audio files to make them unusable for voice cloning while keeping them sounding identical to human ears.

### Adversarial Optimization (Current Approach)

Signal Shield uses **adversarial optimization** powered by PGD (Projected Gradient Descent) and a real speaker encoder model (Resemblyzer). Instead of a fixed transformation, the system finds the smallest possible perturbation for each audio file that maximally disrupts speaker recognition.

```
  Audio ──┬──► Speaker Encoder ──► Loss (cosine similarity)
          │         ▲                    │
          │         │        gradient    │
          │    perturbation ◄────────────┘
          │         │
          └──► Add Perturbation ──► Protected Audio

  Custom perturbation per file.
  Targeted, validated against a real model.
  Perturbation clamped to ±0.01 amplitude (inaudible).
```

### How PGD Works

1. **Get original embedding** — run the audio through Resemblyzer's speaker encoder to get a 256-dim vector representing "who this sounds like"
2. **Create perturbation** — start with a zero-valued delta tensor (same length as audio)
3. **Optimize** — for 50 iterations:
   - Compute the embedding of (audio + delta)
   - Measure cosine similarity to the original embedding
   - Backpropagate to find which direction to push each sample
   - Update delta by a small step in that direction
   - Clamp delta to [-epsilon, epsilon] so it stays inaudible
4. **Output** — return audio + optimized delta

### Making It Differentiable

Resemblyzer's `embed_utterance()` uses `torch.no_grad()`, which blocks gradient flow. To make PGD work, the engine reimplements the embedding pipeline using differentiable PyTorch ops:

- Mel spectrogram via `torchaudio.transforms.MelSpectrogram` (matching Resemblyzer's exact params: 16kHz, n_fft=400, hop=160, 40 mels)
- Splits audio into 160-frame partial utterance windows
- Calls the encoder's `forward()` directly (LSTM → Linear → ReLU → L2 normalize)
- Averages partial embeddings

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
│   │       ├── adversarial_engine.py  ← PGD optimization loop (the core product)
│   │       ├── dsp_engine.py          ← Public interface, delegates to adversarial engine
│   │       └── audio_io.py            ← Audio format conversion
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
| Speaker Encoder | Resemblyzer | Pretrained 3-layer LSTM, lightweight (~17MB), produces 256-dim embeddings |
| API | FastAPI | Async Python web framework with built-in validation and docs |
| Audio I/O | librosa + soundfile | Industry-standard audio loading and WAV export |
| Frontend | Next.js + Tailwind | React framework with standalone build for Docker |
| Deployment | Railway + Docker | Two services from one repo, env var configuration |

## Configuration

All configurable via `SS_`-prefixed environment variables.

| Parameter | Default | What it controls |
|-----------|---------|-----------------|
| `sample_rate` | 22050 Hz | Audio resampling rate |
| `n_fft` | 4096 | STFT window size |
| `hop_length` | 1024 | STFT step size |
| `freq_threshold_hz` | 10000 | Legacy parameter (kept for compatibility) |
| `pgd_steps` | 50 | Number of PGD optimization iterations |
| `pgd_epsilon` | 0.01 | Max perturbation amplitude (imperceptibility bound) |
| `pgd_alpha` | 0.001 | Step size per PGD iteration |

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

Open `http://localhost:3000`, upload a `.wav` or `.mp3` file, and download the protected result. The first request is slower (~30s) because the Resemblyzer model loads on first use.

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

- **Single surrogate model.** Protection is optimized against Resemblyzer's encoder. Cloning tools using different architectures may not be fully disrupted, though the perturbation generalizes somewhat across models.
- **Processing time.** 50 PGD iterations on a 2-second clip takes ~20-30 seconds on CPU. Longer audio takes proportionally more.
- **50MB file size limit.** Processing a 50MB WAV uses ~40-60MB of peak memory.
- **Mono output.** Audio is converted to mono at 22050 Hz during processing.

## Roadmap

- [x] PyTorch adversarial optimization (replace static DSP)
- [x] Dockerized deployment (Railway-ready)
- [ ] Validate protection against real cloning tools (RVC, XTTS)
- [ ] Add more surrogate models for better transferability
- [ ] Audio preview/playback in browser
- [ ] Rate limiting
- [ ] Batch file processing
