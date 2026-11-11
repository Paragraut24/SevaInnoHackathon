import csv
from pathlib import Path

import pytest

from app.rules import evaluate, get_fallback

MESSAGES = Path(__file__).resolve().parents[2] / "testset" / "messages.csv"
SAMPLES = list(csv.DictReader(MESSAGES.open(encoding="utf-8")))
# Messages the Phase 1 plan names explicitly as must-pass anchors.
MUST_HIGH = ["mr_01", "hi_01", "en_01"]
MUST_LOW = ["mr_08", "hi_08", "en_07"]


def _text(msg_id: str) -> str:
    return next(r["text"] for r in SAMPLES if r["id"] == msg_id)


@pytest.mark.parametrize("msg_id", MUST_HIGH)
def test_digital_arrest_scripts_are_high_known_script(msg_id):
    res = evaluate(_text(msg_id))
    assert res.floor == "high" and res.known_script
    assert res.top_category == "digital_arrest"


@pytest.mark.parametrize("msg_id", MUST_LOW)
def test_otp_warning_with_negation_stays_low(msg_id):
    res = evaluate(_text(msg_id))
    assert res.floor == "low" and not res.known_script
    assert ("otp_request", "link_otp") not in res.matched


def test_real_otp_request_is_detected():
    res = evaluate("Please share your OTP with our executive to verify your account")
    assert ("otp_request", "link_otp") in res.matched


def test_mixed_script_message_matches_across_languages():
    res = evaluate("Your खाते KYC pending आहे, account blocked होईल. http://bit.ly/x")
    assert res.known_script and res.top_category == "kyc_bank"


def test_genuine_messages_never_known_script():
    for row in SAMPLES:
        if row["label"] == "genuine":
            assert not evaluate(row["text"]).known_script, row["id"]


def test_empty_and_plain_text_is_low():
    assert evaluate("hello, see you at dinner").floor == "low"


@pytest.mark.parametrize("lang", ["mr", "hi", "en"])
def test_fallback_has_localized_content_for_every_category(lang):
    for category in [None, "digital_arrest", "investment", "kyc_bank", "family_emergency", "courier",
                     "job_lottery", "loan_app", "sextortion", "otp_request", "utility_bill"]:
        fb = get_fallback(category, lang)
        assert fb["scam_type"] and 1 <= len(fb["reasons"]) <= 3 and 1 <= len(fb["next_steps"]) <= 3


def test_fallback_unknown_category_uses_generic():
    assert get_fallback("nope", "en") == get_fallback(None, "en")

