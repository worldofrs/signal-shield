# --- BACKEND DOCKERFILE ---
# A Dockerfile is a recipe. Each line is a step. Docker runs them top to bottom
# to build an "image" — a snapshot of a mini Linux computer with your app installed.

# Step 1: Start from a base image
# This is like choosing which computer to start with.
# python:3.12-slim is a small Linux with Python pre-installed.
# "slim" means it only includes the essentials (smaller = faster deploys).
FROM python:3.12-slim

# Step 2: Install system libraries our Python packages need
# libsndfile1 is a C library for reading/writing audio files.
# soundfile (our Python package) is just a wrapper around it — without this,
# "import soundfile" crashes.
# ffmpeg is needed for MP3 support — librosa uses it to decode MP3 files.
#
# apt-get is Linux's package manager (like pip but for system software).
# rm -rf /var/lib/apt/lists/* cleans up the download cache to keep the image small.
#
# YOUR TURN: Uncomment the lines below
# RUN apt-get update && \
#     apt-get install -y --no-install-recommends libsndfile1 ffmpeg && \
#     rm -rf /var/lib/apt/lists/*

# Step 3: Set the working directory
# All following commands will run from /app inside the container.
# Think of it like "cd /app" that persists for every subsequent step.
#
# YOUR TURN: Uncomment the line below
# WORKDIR /app

# Step 4: Copy requirements.txt and install Python dependencies
# We copy requirements.txt FIRST (before the rest of the code) because
# Docker caches each step. If requirements.txt hasn't changed, Docker
# skips the slow "pip install" step on rebuilds. If we copied everything
# at once, ANY code change would re-trigger pip install.
#
# YOUR TURN: Uncomment the lines below
# COPY requirements.txt .
# RUN pip install --no-cache-dir -r requirements.txt

# Step 5: Copy the rest of the application code
# Now we copy everything else. This step re-runs on every code change,
# but that's fast since it's just copying files.
#
# YOUR TURN: Uncomment the line below
# COPY . .

# Step 6: Tell Docker what command starts the app
# This is what runs when the container launches.
# 0.0.0.0 means "listen on all network interfaces" (required in containers).
# $PORT is an environment variable Railway sets automatically.
#
# YOUR TURN: Uncomment the line below
# CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
