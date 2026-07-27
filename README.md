# Signal Shield

An audio post-processing API that protects voice recordings against AI voice cloning without degrading audio quality.

## The Problem

AI voice cloning tools can take a short audio clip of someone's voice and generate realistic speech that sounds like them. This creates risks for fraud, impersonation, and unauthorized use of someone's voice.

## How It Works

Signal Shield processes audio files to make them unusable for voice cloning while keeping them sounding identical to human ears.

### The Short Version

Sound has two properties at every frequency: **loudness** (how loud that frequency is) and **phase** (the timing offset of the sound wave). Human ears are sensitive to loudness but mostly deaf to phase, especially at high frequencies. Cloning models, however, use both. Signal Shield scrambles the phase above 10,000 Hz — humans can't hear the difference, but cloning models get corrupted input.

### The Full Pipeline

```
                    ┌─────────────────────────────────────────────────┐
                    │              Signal Shield Pipeline             │
                    │                                                 │
  Audio File        │   ┌───────┐    ┌──────────┐    ┌───────────┐    │   Protected
  (WAV/MP3)  ──────►│   │ STFT  │───►│  Phase   │───►│  iSTFT    │    │──► Audio
                    │   │       │    │  Invert  │    │           │    │   (WAV)
                    │   └───────┘    └──────────┘    └───────────┘    │
                    │   time→freq    modify phase    freq→time        │
                    └─────────────────────────────────────────────────┘
```

**Step 1 — STFT (Short-Time Fourier Transform):**
Converts the audio from a sequence of samples over time into a frequency map — a grid showing which frequencies are present at each moment. Think of it as switching from a waveform view to an equalizer view.

```
  Time Domain (input)              Frequency Domain (after STFT)

  amplitude                        frequency
  ▲                               ▲
  │   /\    /\    /\              │ ████
  │  /  \  /  \  /  \             │ ██████
  │ /    \/    \/    \            │ ████████░░░░░░░░
  │/                  \           │ ██████████░░░░░░  ← each cell has
  └──────────────────► time       └──────────────────► time   magnitude + phase
```

**Step 2 — Phase Inversion:**
Each cell in the frequency grid is a complex number with two parts: magnitude (loudness) and phase (wave timing). We leave magnitude untouched and flip the phase for everything above 10,000 Hz.

```
  Frequency
  ▲
  │ ░░░░░░░░░░░░░░░░░░░░  ← above 10kHz: PHASE INVERTED
  │ ░░░░░░░░░░░░░░░░░░░░    (cloning models get corrupted input)
  │ - - - - - - - - - - -  ← 10kHz threshold
  │ ████████████████████    (human-audible range: untouched)
  │ ████████████████████
  │ ████████████████████
  └──────────────────────► Time
```

**Step 3 — iSTFT (Inverse STFT):**
Converts the modified frequency grid back into a normal audio file. The result sounds the same to humans because magnitude (what we hear) was never changed.

### Current Approach vs. Future Approach

Signal Shield currently uses a **static DSP approach** — the same phase transformation is applied to every file. This is the MVP.

The planned upgrade is **adversarial optimization**: instead of a fixed transformation, the system would use a neural network to find the smallest possible perturbation that maximally disrupts a specific cloning model. This is more effective because it's tailored to exploit the model's weaknesses rather than relying on a general assumption about phase sensitivity.

```
  Static (current)                    Adversarial (planned)

  Audio ──► Fixed Phase Flip ──► Out   Audio ──┬──► Cloning Model ──► Loss
                                               │         ▲               │
                                               │         │    gradient   │
                                               │    perturbation ◄───────┘
                                               │         │
                                               └──► Add Perturbation ──► Out

  Same transformation every time.      Custom perturbation per file.
  Fast. May not beat all models.       Slower. Targeted and validated.
```

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
│   │       ├── dsp_engine.py  ← STFT phase-shift logic (the core product)
│   │       └── audio_io.py    ← Audio format conversion
│   └── tests/              ← DSP + API tests
│
├── frontend/               ← TypeScript (Next.js)
│   └── src/
│       ├── app/page.tsx    ← Upload page
│       ├── components/     ← UI components
│       └── lib/api.ts      ← Backend API client
```

### Request Flow

```
  Browser                    Frontend (Next.js)              Backend (FastAPI)
  ┌──────┐                   ┌──────────────┐               ┌──────────────┐
  │ User │                   │              │               │              │
  │ drops│  ── file ──────►  │  FileUploader│  ── POST ──►  │  /api/v1/    │
  │ file │                   │              │    (fetch)     │  protect     │
  │      │                   │  Processing  │               │              │
  │      │                   │  Status:     │               │  1. Validate │
  │      │                   │  spinner...  │               │  2. Load     │
  │      │                   │              │               │  3. STFT     │
  │      │                   │  Download    │  ◄── WAV ──   │  4. Phase inv│
  │      │  ◄─ click ──────  │  Button      │    (bytes)    │  5. iSTFT    │
  │      │                   │              │               │  6. Export   │
  └──────┘                   └──────────────┘               └──────────────┘
```

## Tech Stack

| Layer | Technology | Why |
|-------|-----------|-----|
| DSP | librosa + numpy | Industry-standard audio analysis, handles STFT/iSTFT natively |
| API | FastAPI | Async Python web framework with built-in validation and docs |
| Audio I/O | soundfile | Reads/writes WAV files via libsndfile |
| Frontend | Next.js + Tailwind | React framework with built-in routing, standalone build for Docker |
| Deployment | Railway + Docker | Two services from one repo, env var configuration |

## DSP Parameters

All configurable via `SS_`-prefixed environment variables.

| Parameter | Default | What it controls |
|-----------|---------|-----------------|
| `sample_rate` | 22050 Hz | Audio resampling rate. Nyquist limit = ~11kHz |
| `n_fft` | 4096 | STFT window size. Frequency resolution = sample_rate / n_fft ≈ 5.4 Hz per bin |
| `hop_length` | 1024 | STFT step size (n_fft / 4 = 75% overlap for smooth reconstruction) |
| `freq_threshold_hz` | 10000 | Phase inversion starts above this frequency |

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

Open `http://localhost:3000`, upload a `.wav` or `.mp3` file, and download the protected result.

## Tests

```bash
cd backend
python -m pytest tests/ -v
```

Tests verify:
- Output length matches input
- Magnitude spectrum is preserved (audio sounds the same)
- Phase is inverted above threshold (protection is applied)
- Output is not silence
- API returns correct status codes for valid files, bad formats, and oversized files

## Limitations

- **Static phase inversion may not defeat all cloning models.** Many modern cloners (RVC, XTTS) use mel spectrograms which discard phase information. The adversarial optimization upgrade (planned) addresses this by targeting specific model architectures.
- **50MB file size limit.** Processing a 50MB WAV uses ~40-60MB of peak memory.
- **Mono output.** Audio is converted to mono at 22050 Hz during processing.

## Roadmap

- [ ] Validate protection against real cloning tools (RVC, XTTS)
- [ ] PyTorch adversarial optimization (replace static DSP)
- [ ] Audio preview/playback in browser
- [ ] Configurable frequency threshold slider
- [ ] Rate limiting
- [ ] Batch file processing
