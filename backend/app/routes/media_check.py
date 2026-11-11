"""
Media check route — POST /api/media-check.

Accepts a multipart file upload (image or audio).
Video not supported on free tier — returns could_not_check.
Temp file is always deleted in a finally block.
"""
import tempfile
from pathlib import Path

from fastapi import APIRouter, File, Request, UploadFile
from fastapi.responses import JSONResponse

from app.limiter import limiter, rate_limit
from app.media import (
    ALLOWED_AUDIO_TYPES,
    ALLOWED_IMAGE_TYPES,
    COULD_NOT_CHECK,
    LIMITS_NOTE,
    MAX_FILE_BYTES,
    check_audio,
    check_image,
)

router = APIRouter()


@router.post("/api/media-check")
@limiter.limit(rate_limit)
async def media_check(request: Request, file: UploadFile = File(...)) -> JSONResponse:
    """Upload an image or audio file for authenticity band scoring."""
    mime = file.content_type or ""
    if mime not in ALLOWED_IMAGE_TYPES | ALLOWED_AUDIO_TYPES:
        return JSONResponse(
            status_code=422,
            content={
                "error_code": "unsupported_file_type",
                "message": f"Supported types: JPEG, PNG, WEBP, GIF, WAV, MP3, MP4 audio, OGG. Got: {mime}",
            },
        )

    file_bytes = await file.read()
    if len(file_bytes) > MAX_FILE_BYTES:
        return JSONResponse(
            status_code=422,
            content={"error_code": "file_too_large", "message": "Maximum file size is 10 MB."},
        )

    suffix = Path(file.filename or "upload").suffix or ".bin"
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    tmp_path = Path(tmp.name)
    try:
        tmp.write(file_bytes)
        tmp.close()

        if mime in ALLOWED_IMAGE_TYPES:
            result = await check_image(file_bytes, mime, tmp_path)
        else:
            result = await check_audio(file_bytes, mime)

        result["filename"] = file.filename
        result["mime_type"] = mime
        return JSONResponse(content=result)
    finally:
        tmp_path.unlink(missing_ok=True)

