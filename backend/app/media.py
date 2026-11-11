"""
Media authenticity check — Sightengine (image/video keyframes) + HF audio fallback.

Bands:
  unlikely      score < 0.3   — no strong signs detected
  unclear       0.3 <= score < 0.7
  possible_synthetic  score >= 0.7

The words "real", "fake", "genuine", "authentic", "deepfake" must NOT appear
in any band label or message string (enforced by test_media.py).

Sightengine free tier: 500 ops/day. A rolling day counter lives in a module-level
variable (process-lifetime). Past 450 ops the route returns could_not_check.

Video: not supported on free tier — keyframe path stubs to could_not_check.
Audio: Hugging Face Inference API, model facebook/wav2vec2-base; falls back to could_not_check.
"""
import asyncio
import logging
import os
import time
from pathlib import Path

import httpx

from app.config import get_settings

logger = logging.getLogger("sajag.media")

BAND_THRESHOLDS = (0.3, 0.7)
BAND_UNLIKELY = "unlikely"
BAND_UNCLEAR = "unclear"
BAND_POSSIBLE_SYNTHETIC = "possible_synthetic"
COULD_NOT_CHECK = "could_not_check"
LIMITS_NOTE = (
    "This check uses automated pattern detection only and may be incorrect. "
    "It cannot confirm whether media is manipulated or original. "
    "Use it as one data point, not as proof."
)

# Daily ops counter (resets on process restart — good enough for a demo)
_ops_today = 0
_ops_day = time.strftime("%Y-%m-%d")
DAILY_LIMIT = 450

SIGHTENGINE_API = "https://api.sightengine.com/1.0/check.json"
SIGHTENGINE_VIDEO_API = "https://api.sightengine.com/1.0/video/check-sync.json"
HF_API = "https://api-inference.huggingface.co/models/facebook/wav2vec2-base"

ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}
ALLOWED_AUDIO_TYPES = {"audio/wav", "audio/mpeg", "audio/mp4", "audio/ogg"}
MAX_FILE_BYTES = 10 * 1024 * 1024  # 10 MB


def _band(score: float) -> str:
    if score < BAND_THRESHOLDS[0]:
        return BAND_UNLIKELY
    if score < BAND_THRESHOLDS[1]:
        return BAND_UNCLEAR
    return BAND_POSSIBLE_SYNTHETIC


def _check_daily_limit() -> bool:
    """Returns True if we are within the daily quota."""
    global _ops_today, _ops_day
    today = time.strftime("%Y-%m-%d")
    if today != _ops_day:
        _ops_today = 0
        _ops_day = today
    return _ops_today < DAILY_LIMIT


def _record_op() -> None:
    global _ops_today
    _ops_today += 1


async def check_image(file_bytes: bytes, mime_type: str, tmp_path: Path) -> dict:
    """Score an image with Sightengine. Returns band + raw score."""
    if not _check_daily_limit():
        return {"band": COULD_NOT_CHECK, "limits_note": LIMITS_NOTE, "reason": "daily_limit_reached"}

    settings = get_settings()
    if not settings.sightengine_api_user or not settings.sightengine_api_secret:
        return {"band": COULD_NOT_CHECK, "limits_note": LIMITS_NOTE, "reason": "api_key_missing"}

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(
                SIGHTENGINE_API,
                data={
                    "models": "genai",
                    "api_user": settings.sightengine_api_user,
                    "api_secret": settings.sightengine_api_secret,
                },
                files={"media": (tmp_path.name, file_bytes, mime_type)},
            )
        _record_op()
        data = resp.json()
        score = float(data.get("type", {}).get("ai_generated", 0))
        return {"band": _band(score), "score": round(score, 3), "limits_note": LIMITS_NOTE}
    except Exception as exc:
        logger.warning("sightengine_failed type=%s", type(exc).__name__)
        return {"band": COULD_NOT_CHECK, "limits_note": LIMITS_NOTE, "reason": "api_error"}


async def check_audio(file_bytes: bytes, mime_type: str) -> dict:
    """Score audio via HF Inference API wav2vec2 classifier."""
    settings = get_settings()
    if not settings.hf_token:
        return {"band": COULD_NOT_CHECK, "limits_note": LIMITS_NOTE, "reason": "api_key_missing"}

    try:
        async with httpx.AsyncClient(timeout=20) as client:
            resp = await client.post(
                HF_API,
                headers={"Authorization": f"Bearer {settings.hf_token}"},
                content=file_bytes,
            )
        result = resp.json()
        # HF returns list of {label, score}; look for a "spoof" or "synthetic" label
        if isinstance(result, list):
            spoof_score = next(
                (r["score"] for r in result if "spoof" in r.get("label", "").lower()),
                0.0,
            )
            return {"band": _band(spoof_score), "score": round(spoof_score, 3), "limits_note": LIMITS_NOTE}
        return {"band": COULD_NOT_CHECK, "limits_note": LIMITS_NOTE, "reason": "unexpected_response"}
    except Exception as exc:
        logger.warning("hf_audio_failed type=%s", type(exc).__name__)
        return {"band": COULD_NOT_CHECK, "limits_note": LIMITS_NOTE, "reason": "api_error"}

