# --- BACKEND DOCKERFILE ---
# A Dockerfile is a recipe. Each line is a step. Docker runs them top to bottom
# to build an "image" — a snapshot of a mini Linux computer with your app installed.

# Step 1: Start from a base image
# python:3.12-slim is a small Linux with Python pre-installed.
# "slim" means it only includes the essentials (smaller = faster deploys).
FROM python:3.12-slim

# Step 2: Install system libraries our Python packages need
# libsndfile1 is a C library for reading/writing audio files.
# soundfile (our Python package) is just a wrapper around it — without this,
# "import soundfile" crashes.
# ffmpeg is needed for MP3/M4A support — librosa uses it to decode those formats.
#
# apt-get is Linux's package manager (like pip but for system software).
# rm -rf /var/lib/apt/lists/* cleans up the download cache to keep the image small.
RUN apt-get update && \
    apt-get install -y --no-install-recommends libsndfile1 ffmpeg gcc python3-dev && \
    rm -rf /var/lib/apt/lists/*

# Step 3: Set the working directory
# All following commands will run from /app inside the container.
WORKDIR /app

# Cache dirs for Hugging Face / Torch / SpeechBrain weights baked into the image.
# HF_HOME covers transformers + hub downloads used by SpeechBrain.
ENV HF_HOME=/opt/ml-cache/huggingface \
    TORCH_HOME=/opt/ml-cache/torch \
    SS_ECAPA_SAVEDIR=/opt/ml-cache/speechbrain/spkrec-ecapa-voxceleb \
    HF_HUB_DISABLE_TELEMETRY=1

RUN mkdir -p "$HF_HOME" "$TORCH_HOME" "$SS_ECAPA_SAVEDIR"

# Step 4: Copy requirements.txt and install Python dependencies
# We copy requirements.txt FIRST (before the rest of the code) because
# Docker caches each step. If requirements.txt hasn't changed, Docker
# skips the slow "pip install" step on rebuilds.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Step 5: Prefetch encoder weights (separate layer so app code edits don't re-download)
COPY scripts/prefetch_models.py scripts/prefetch_models.py
RUN python scripts/prefetch_models.py

# Step 6: Copy the rest of the application code
COPY . .

# Step 7: Tell Docker what command starts the app
# 0.0.0.0 means "listen on all network interfaces" (required in containers).
# $PORT is an environment variable Railway sets automatically.
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --workers ${WEB_CONCURRENCY:-2}"]
