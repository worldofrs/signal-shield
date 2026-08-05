import asyncio
from io import BytesIO
import logging
import time

from fastapi import APIRouter, Form, HTTPException, UploadFile
from fastapi.responses import StreamingResponse

from app.config import settings
from app.core.audio_io import load_audio, export_wav
from app.core.adversarial_engine import VALID_ENCODERS
from app.core.dsp_engine import apply_phase_protection

logger = logging.getLogger("signal_shield.router")

router = APIRouter()

ALLOWED_EXTENSIONS = {".wav", ".mp3", ".m4a"}


def _run_protection(file_bytes: bytes, filename: str, encoder_list: list[str]) -> bytes:
    """CPU-bound load → protect → export pipeline (runs in a worker thread)."""
    y, sr = load_audio(file_bytes, filename)
    protected = apply_phase_protection(y, sr, encoders=encoder_list)
    return export_wav(protected, sr)


@router.post("/protect")
async def protect_audio(
    file: UploadFile,
    encoders: str = Form("resemblyzer"),
):
    # Parse and validate encoder names
    encoder_list = [e.strip() for e in encoders.split(",") if e.strip()]
    if not encoder_list:
        raise HTTPException(status_code=400, detail="At least one encoder must be selected.")
    invalid = set(encoder_list) - VALID_ENCODERS
    if invalid:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid encoder(s): {', '.join(sorted(invalid))}. Valid options: {', '.join(sorted(VALID_ENCODERS))}",
        )

    # Validate file extension
    filename = file.filename or ""
    ext = ""
    if "." in filename:
        ext = "." + filename.rsplit(".", 1)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        logger.warning("Rejected file with unsupported format: %s", ext)
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported format '{ext}'. Accepted: .wav, .mp3, .m4a",
        )

    # Read file and validate size
    file_bytes = await file.read()
    max_bytes = settings.max_file_size_mb * 1024 * 1024
    file_size_mb = len(file_bytes) / (1024 * 1024)
    if len(file_bytes) > max_bytes:
        logger.warning("Rejected file '%s' — %.1fMB exceeds %dMB limit", filename, file_size_mb, settings.max_file_size_mb)
        raise HTTPException(
            status_code=413,
            detail=f"File exceeds {settings.max_file_size_mb}MB limit",
        )

    # Offload CPU-bound work so /health and other requests stay responsive
    try:
        wav_bytes = await asyncio.to_thread(
            _run_protection, file_bytes, filename, encoder_list
        )
        print("yay it worked!")
    logger.info("Processing '%s' (%.1fMB) with encoders: %s", filename, file_size_mb, encoder_list)

    # Process: load -> phase protect -> export
    try:
        start = time.time()

        y, sr = load_audio(file_bytes, filename)
        logger.info("Audio loaded: %.1fs duration, sr=%d", len(y) / sr, sr)

        protected = apply_phase_protection(y, sr, encoders=encoder_list)
        logger.info("Protection complete in %.1fs", time.time() - start)

        wav_bytes = export_wav(protected, sr)
        logger.info("WAV export complete, %d bytes", len(wav_bytes))
    except Exception as e:
        logger.exception("Processing failed for '%s'", filename)
        raise HTTPException(
            status_code=422,
            detail=f"Processing failed: {e}",
        )

    # Return protected WAV as a download
    safe_name = filename.rsplit(".", 1)[0] if "." in filename else "audio"
    logger.info("Returning protected file: protected_%s.wav", safe_name)
    return StreamingResponse(
        BytesIO(wav_bytes),
        media_type="audio/wav",
        headers={
            "Content-Disposition": f'attachment; filename="protected_{safe_name}.wav"'
        },
    )
