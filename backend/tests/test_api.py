"""Tests for the API endpoint.

These use FastAPI's TestClient, which lets you make fake HTTP requests
to your app without actually starting a server. It's like curl but in Python.
"""

import importlib
from io import BytesIO

import numpy as np
import soundfile as sf
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def _make_wav_bytes() -> bytes:
    """Helper: create a small valid WAV file in memory."""
    sr = 22050
    t = np.linspace(0, 0.5, int(sr * 0.5), endpoint=False)
    y = (0.5 * np.sin(2 * np.pi * 440 * t)).astype(np.float32)
    buf = BytesIO()
    sf.write(buf, y, sr, format="WAV")
    buf.seek(0)
    return buf.read()


# --- EXAMPLE TEST ---


def test_health_returns_ok():
    """The /health endpoint should return 200 with {"status": "ok"}.

    Why this matters: health checks are how deployment platforms (Railway)
    know your service is alive. If this fails, your app won't deploy.
    """
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_cors_uses_configured_allowed_origins(monkeypatch):
    """CORS should honor the configured origin list from the environment."""
    monkeypatch.setenv("SS_ALLOWED_ORIGINS", "https://example.com")
    import app.config as config_module
    import app.main as main_module

    importlib.reload(config_module)
    importlib.reload(main_module)

    cors_client = TestClient(main_module.app)
    response = cors_client.get(
        "/health",
        headers={"Origin": "https://example.com"},
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "https://example.com"


# --- YOUR TURN ---
# Run tests with: python3 -m pytest tests/test_api.py -v
#
# Test 2: test_protect_returns_wav
#   POST a valid WAV to /api/v1/protect and check:
#   - status_code == 200
#   - response content-type is "audio/wav"
#   - response body has length > 0 (you got actual audio back)
#   Hint for sending a file with TestClient:
#     response = client.post("/api/v1/protect", files={"file": ("test.wav", wav_bytes, "audio/wav")})
#   Why it matters: this is the happy path — the core thing the API does

def test_protect_returns_wav():
    wav_bytes = _make_wav_bytes()
    response = client.post("/api/v1/protect", files={"file": ("test.wav", wav_bytes, "audio/wav")})
    assert response.status_code == 200
    assert response.headers["content-type"] == "audio/wav"
    assert len(response.content) > 0

#
# Test 3: test_reject_bad_extension
#   POST a file named "test.txt" and check you get status_code == 400
#   Hint: files={"file": ("test.txt", b"fake content", "text/plain")}
#   Why it matters: we don't want to waste CPU trying to process non-audio files

def test_reject_bad_extension():
    response = client.post("/api/v1/protect", files={"file": ("test.txt", b"fake content", "text/plain")})
    assert response.status_code == 400

#
# Test 4: test_reject_oversized_file
#   POST a file that's larger than the max size and check you get 413.
#   Hint: create fake bytes with b"\x00" * (51 * 1024 * 1024) for 51MB
#   Use files={"file": ("big.wav", big_bytes, "audio/wav")}
#   Why it matters: prevents someone from uploading a 500MB file and crashing the server

def test_reject_oversized_file():
    response = client.post("/api/v1/protect", files={"file": ("big.wav", b"\x00" * (51 * 1024 * 1024), "audio/wav")})
    assert response.status_code == 413