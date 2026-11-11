import re

import pytest

from app.fuse import fuse
from app.rules import GENERIC, RuleResult, evaluate, get_fallback
from app.schemas import LlmOut

DIGITAL_ARREST_MR = (
    "सायबर क्राईम सेलकडून तातडीची सूचना: तुमच्या आधार क्रमांकाविरुद्ध मनी लाँड्रिंग प्रकरणात "
    "एफआयआर नोंदवण्यात आली आहे. अटक टाळण्यासाठी लगेच 9876543210 वर व्हिडिओ कॉल करा."
)
CATEGORIES = [GENERIC, "digital_arrest", "investment", "kyc_bank", "family_emergency", "courier",
              "job_lottery", "loan_app", "sextortion", "otp_request", "utility_bill"]
SAFE_CLAIM_RE = re.compile(r"\bsafe\b|सुरक्षित आहे|सुरक्षित है", re.IGNORECASE)


def _llm(risk: str, reasons=("model reason",)) -> LlmOut:
    return LlmOut(risk=risk, scam_type="model type", reasons=list(reasons),
                  next_steps=["model step"], confidence=0.9)


def test_rule_floor_cannot_be_lowered_by_model():
    rule = evaluate(DIGITAL_ARREST_MR)
    out = fuse(rule, _llm("low"), "mr")
    assert out.risk == "high" and out.show_helpline and out.mode == "full"
    assert out.reasons[0] == get_fallback("digital_arrest", "mr")["reasons"][0]
    assert "model reason" in out.reasons and len(out.reasons) <= 3
    assert out.scam_type == get_fallback("digital_arrest", "mr")["scam_type"]


def test_model_can_raise_above_floor():
    rule = RuleResult(score=1, matched=[], top_category=None, floor="low", known_script=False)
    out = fuse(rule, _llm("high"), "en")
    assert out.risk == "high" and out.reasons == ["model reason"] and out.show_helpline


def test_without_known_script_model_risk_wins():
    rule = RuleResult(score=3, matched=[], top_category="investment", floor="medium", known_script=False)
    assert fuse(rule, _llm("low"), "en").risk == "low"


def test_quick_mode_uses_floor_and_static_text():
    out = fuse(evaluate(DIGITAL_ARREST_MR), None, "mr")
    assert out.mode == "quick" and out.risk == "high" and out.show_helpline
    assert out.scam_type == get_fallback("digital_arrest", "mr")["scam_type"]


def test_quick_mode_low_floor_uses_generic_text():
    rule = RuleResult(score=2, matched=[("investment", "money")], top_category="investment",
                      floor="low", known_script=False)
    out = fuse(rule, None, "en")
    assert out.risk == "low" and not out.show_helpline
    assert out.scam_type == get_fallback(None, "en")["scam_type"]


@pytest.mark.parametrize("lang", ["mr", "hi", "en"])
def test_fallback_text_never_claims_safe(lang):
    for category in CATEGORIES:
        fb = get_fallback(category, lang)
        text = " ".join([fb["scam_type"], *fb["reasons"], *fb["next_steps"]])
        assert not SAFE_CLAIM_RE.search(text), (category, lang)


@pytest.mark.parametrize("lang", ["mr", "hi"])
def test_fallback_text_is_mostly_devanagari(lang):
    for category in CATEGORIES:
        text = "".join(get_fallback(category, lang)["reasons"])
        deva = len(re.findall(r"[\u0900-\u097f]", text))
        letters = len(re.findall(r"[\u0900-\u097fA-Za-z]", text))
        assert deva / letters > 0.5, (category, lang)
