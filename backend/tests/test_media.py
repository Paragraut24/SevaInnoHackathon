"""Tests for media.py — verifies no "real"/"fake" strings and band logic."""
import pytest

from app.media import BAND_UNLIKELY, BAND_UNCLEAR, BAND_POSSIBLE_SYNTHETIC, LIMITS_NOTE, _band

FORBIDDEN = {"real", "fake", "genuine", "authentic", "deepfake"}


def test_band_unlikely():
    assert _band(0.0) == BAND_UNLIKELY
    assert _band(0.29) == BAND_UNLIKELY


def test_band_unclear():
    assert _band(0.3) == BAND_UNCLEAR
    assert _band(0.69) == BAND_UNCLEAR


def test_band_possible_synthetic():
    assert _band(0.7) == BAND_POSSIBLE_SYNTHETIC
    assert _band(1.0) == BAND_POSSIBLE_SYNTHETIC


def test_band_labels_contain_no_forbidden_words():
    for label in (BAND_UNLIKELY, BAND_UNCLEAR, BAND_POSSIBLE_SYNTHETIC):
        for word in FORBIDDEN:
            assert word not in label.lower(), f"Forbidden word '{word}' found in band label '{label}'"


def test_limits_note_contains_no_forbidden_words():
    for word in FORBIDDEN:
        assert word not in LIMITS_NOTE.lower(), f"Forbidden word '{word}' found in limits_note"


def test_media_check_unsupported_file_type(client):
    res = client.post(
        "/api/media-check",
        files={"file": ("test.pdf", b"%PDF-1.4...", "application/pdf")},
    )
    assert res.status_code == 422
    assert res.json()["error_code"] == "unsupported_file_type"


def test_media_check_file_too_large(client, monkeypatch):
    import app.routes.media_check as mc
    # Mock max bytes to 10 bytes for test
    monkeypatch.setattr(mc, "MAX_FILE_BYTES", 10)
    res = client.post(
        "/api/media-check",
        files={"file": ("photo.jpg", b"0123456789extra", "image/jpeg")},
    )
    assert res.status_code == 422
    assert res.json()["error_code"] == "file_too_large"


def test_media_check_api_key_missing_fallback(client, monkeypatch):
    from app.config import Settings
    monkeypatch.setattr("app.media.get_settings", lambda: Settings(sightengine_api_user="", sightengine_api_secret=""))
    res = client.post(
        "/api/media-check",
        files={"file": ("photo.jpg", b"\xff\xd8\xff\xe0testjpeg", "image/jpeg")},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["band"] == "could_not_check"
    assert data["reason"] == "api_key_missing"
    assert "limits_note" in data


