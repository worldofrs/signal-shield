from fastapi import APIRouter, HTTPException, UploadFile
from fastapi.responses import StreamingResponse
from io import BytesIO

from app.config import settings
from app.core.audio_io import load_audio, export_wav
from app.core.dsp_engine import apply_phase_protection

router = APIRouter()

ALLOWED_EXTENSIONS = {".wav", ".mp3"}


@router.post("/protect")
async def protect_audio(file: UploadFile):
    # Validate file extension
    filename = file.filename or ""
    ext = ""
    if "." in filename:
        ext = "." + filename.rsplit(".", 1)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        print("unsupported format")
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported format '{ext}'. Accepted: .wav, .mp3",
        )

    # Read file and validate size
    file_bytes = await file.read()
    max_bytes = settings.max_file_size_mb * 1024 * 1024
    if len(file_bytes) > max_bytes:
        print("file too large")
        raise HTTPException(
            status_code=413,
            detail=f"File exceeds {settings.max_file_size_mb}MB limit",
        )

    # Process: load -> phase protect -> export
    try:
        y, sr = load_audio(file_bytes, filename)
        protected = apply_phase_protection(y, sr)
        wav_bytes = export_wav(protected, sr)
        print("yay it worked!")
    except Exception as e:
        print("something went wrong")
        raise HTTPException(
            status_code=422,
            detail=f"Processing failed: {e}",
        )

    # Return protected WAV as a download
    safe_name = filename.rsplit(".", 1)[0] if "." in filename else "audio"
    print('returning response')
    return StreamingResponse(
        BytesIO(wav_bytes),
        media_type="audio/wav",
        headers={
            "Content-Disposition": f'attachment; filename="protected_{safe_name}.wav"'
        },
    )
