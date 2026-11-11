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

