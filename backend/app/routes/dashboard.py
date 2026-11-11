"""
Mock dashboard route — GET /api/dashboard.

Returns static synthetic district data with sample: true flag.
No real incident data is stored or served.
"""
import json
from pathlib import Path

from fastapi import APIRouter

router = APIRouter()

_DATA = json.loads(
    (Path(__file__).resolve().parents[2] / "data" / "dashboard_sample.json").read_text(encoding="utf-8")
)


@router.get("/api/dashboard")
def dashboard() -> dict:
    """Return static synthetic scam trend data for the demo dashboard."""
    return _DATA

