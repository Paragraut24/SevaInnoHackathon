"""Comprehensive tests for Sajag V2 ML classifier, word-occlusion explainer, and 3-signal fusion."""
import logging
import re
import sys
import time
from pathlib import Path

import numpy as np
import pytest
from fastapi.testclient import TestClient

from app import llm
from app.classifier import MlResult, OnnxScamClassifier, load_classifier
from app.explainer import MAX_TOKENS, explain_text
from app.fuse import _ML_FALLBACK, fuse
from app.main import app
from app.normalize import preprocess_for_ml
from app.rules import RuleResult, evaluate
from app.schemas import LlmOut, TriageOut

DIGITAL_ARREST_MR = (
    "सायबर क्राईम सेलकडून तातडीची सूचना: तुमच्या आधार क्रमांकाविरुद्ध मनी लाँड्रिंग प्रकरणात "
    "एफआयआर नोंदवण्यात आली आहे. अटक टाळण्यासाठी लगेच 9876543210 वर व्हिडिओ कॉल करा."
)
FORBIDDEN_WORDS_RE = re.compile(r"\b(safe|real|fake|genuine|authentic|deepfake)\b", re.IGNORECASE)


class _StubClassifier:
    """Deterministic stub classifier simulating ONNX scam/ham outputs for Phase D verification."""

    def __init__(self, scam_prob: float = 0.92, delay_s: float = 0.0, raise_on_predict: bool = False):
        self.scam_prob = scam_prob
        self.delay_s = delay_s
        self.raise_on_predict = raise_on_predict
        self.batch_calls = 0

    def predict(self, text: str) -> MlResult:
        if self.raise_on_predict:
            raise RuntimeError("stub failure")
        is_scam = self.scam_prob > 0.5
        conf = round(self.scam_prob if is_scam else 1.0 - self.scam_prob, 3)
        risk = "high" if self.scam_prob >= 0.85 else "medium" if self.scam_prob >= 0.55 else "low"
        return MlResult(is_scam=is_scam, scam_prob=self.scam_prob, confidence=conf, risk=risk)

    def predict_proba_batch(self, texts: list[str]) -> np.ndarray:
        self.batch_calls += 1
        if self.delay_s:
            time.sleep(self.delay_s)
        out = []
        for idx, t in enumerate(texts):
            # First item is original text; drop score slightly when key words are removed.
            if idx == 0:
                p = self.scam_prob
            else:
                p = max(0.05, self.scam_prob - 0.05 * ((idx % 5) + 1))
            out.append([1.0 - p, p])
        return np.array(out, dtype=np.float32)


def _stub_llm(monkeypatch, result: LlmOut | None) -> None:
    async def fake(*args, **kwargs):
        return result

    monkeypatch.setattr(llm, "analyze", fake)


def test_ml_unavailable_matches_two_signal_fusion():
    rule_high = evaluate(DIGITAL_ARREST_MR)
    llm_low = LlmOut(risk="low", scam_type="none", reasons=["no signs"], next_steps=["wait"], confidence=0.8)
    baseline_quick = fuse(rule_high, None, "mr")
    v2_quick = fuse(rule_high, None, "mr", ml=None)
    assert baseline_quick == v2_quick and v2_quick.ml_confidence is None and v2_quick.top_tokens == []

    baseline_full = fuse(rule_high, llm_low, "mr")
    v2_full = fuse(rule_high, llm_low, "mr", ml=None)
    assert baseline_full == v2_full


def test_ml_high_raises_above_low_rules_and_low_llm():
    rule_low = RuleResult(score=0, matched=[], top_category=None, floor="low", known_script=False)
    llm_low = LlmOut(risk="low", scam_type="unclear", reasons=["short text"], next_steps=["verify"], confidence=0.6)
    ml_high = MlResult(is_scam=True, scam_prob=0.94, confidence=0.94, risk="high")

    out = fuse(rule_low, llm_low, "en", ml=ml_high)
    assert out.risk == "high" and out.show_helpline and out.ml_confidence == 0.94
    assert "short text" in out.reasons and len(out.reasons) <= 3


def test_ml_confident_ham_cannot_lower_known_script_floor():
    rule_high = evaluate(DIGITAL_ARREST_MR)
    llm_low = LlmOut(risk="low", scam_type="none", reasons=["ok"], next_steps=["wait"], confidence=0.9)
    ml_ham = MlResult(is_scam=False, scam_prob=0.04, confidence=0.96, risk="low")

    out = fuse(rule_high, llm_low, "mr", ml=ml_ham)
    assert out.risk == "high" and out.show_helpline and out.ml_confidence == 0.96


def test_ml_confident_ham_never_triggers_known_script_branch():
    # D9: rules medium (known_script=False) + confident ham + LLM low must stay low (not escalated to medium).
    rule_med = RuleResult(score=3, matched=[("investment", "money")], top_category="investment",
                          floor="medium", known_script=False)
    llm_low = LlmOut(risk="low", scam_type="none", reasons=["benign"], next_steps=["ignore"], confidence=0.88)
    ml_ham = MlResult(is_scam=False, scam_prob=0.05, confidence=0.95, risk="low")

    out = fuse(rule_med, llm_low, "en", ml=ml_ham)
    assert out.risk == "low" and not out.show_helpline and out.ml_confidence == 0.95


def test_predict_exception_degrades_gracefully_to_200(client, monkeypatch):
    _stub_llm(monkeypatch, None)
    monkeypatch.setattr(app.state, "classifier", _StubClassifier(raise_on_predict=True), raising=False)

    res = client.post("/api/triage", json={"text": "hello friend", "lang": "en"})
    assert res.status_code == 200
    body = TriageOut.model_validate(res.json())
    assert body.ml_confidence is None and body.top_tokens == []


def test_explain_true_single_batch_max_six_tokens_and_budget(client, monkeypatch):
    _stub_llm(monkeypatch, None)
    stub = _StubClassifier(scam_prob=0.92)
    monkeypatch.setattr(app.state, "classifier", stub, raising=False)

    res = client.post(
        "/api/triage?explain=true",
        json={"text": "urgent kyc blocked click link immediately verify otp bank account now", "lang": "en"},
    )
    assert res.status_code == 200
    body = TriageOut.model_validate(res.json())
    assert 1 <= len(body.top_tokens) <= MAX_TOKENS
    assert stub.batch_calls == 1

    # Budget exceeded -> empty top_tokens, still 200 OK
    slow_stub = _StubClassifier(scam_prob=0.92, delay_s=0.15)
    assert explain_text("one two three four", slow_stub, budget_s=0.05) == []


def test_logs_contain_no_message_content_with_ml_on(client, monkeypatch, caplog):
    _stub_llm(monkeypatch, None)
    monkeypatch.setattr(app.state, "classifier", _StubClassifier(scam_prob=0.93), raising=False)
    caplog.set_level(logging.INFO)

    res = client.post("/api/triage?explain=true", json={"text": DIGITAL_ARREST_MR, "lang": "mr"})
    assert res.status_code == 200
    assert "ml_conf=0.93" in caplog.text
    for fragment in ["सायबर", "9876543210", "आधार", "एफआयआर"]:
        assert fragment not in caplog.text


def test_preprocess_for_ml_parity_with_prepare_dataset():
    scripts_dir = str(Path(__file__).resolve().parents[1] / "scripts")
    if scripts_dir not in sys.path:
        sys.path.insert(0, scripts_dir)
    import prepare_dataset  # noqa: E402

    samples = [
        "URGENT: Verify KYC at https://sbi-kyc.xyz/login now!",
        "Call +91 98765 43210 immediately or account blocked.",
        "तुमचा OTP कोणालाही देऊ नका. पिन सुरक्षित ठेवा.",
        "कॉल  करा \u200b९८७६५४३२१० वर किंवा bit.ly/3xAbc उघडा.",
        "आपका पीएनआर 4588915399 कन्फर्म है।",
        "Visit http://paytm-kyc.in/verify?id=12, call 098123-45678.",
        "   Hello   World   \n  Next   line  ",
        "Rs 5000 credited via UPI ref 123456789012.",
        "Dear customer click loan-fast.in.",
        "तुमचे खाते अपडेट करण्यासाठी +919123456789 वर संपर्क साधा.",
    ]
    for s in samples:
        once = preprocess_for_ml(s)
        assert once == prepare_dataset.preprocess_text(s)
        assert preprocess_for_ml(once) == once


def test_health_reports_ml_model_loaded_and_unavailable(monkeypatch):
    import app.main as app_main

    monkeypatch.setattr(app_main, "load_classifier", lambda **kwargs: None)
    with TestClient(app) as tc:
        # Missing/disabled model -> lifespan sets unavailable gracefully with HTTP 200
        res_unavail = tc.get("/api/health")
        assert res_unavail.status_code == 200
        assert res_unavail.json() == {"status": "ok", "ml_model": "unavailable"}

        monkeypatch.setattr(tc.app.state, "classifier", _StubClassifier(), raising=False)
        res_loaded = tc.get("/api/health")
        assert res_loaded.status_code == 200
        assert res_loaded.json() == {"status": "ok", "ml_model": "loaded"}


def test_onnx_classifier_wrapper_and_no_transformers_or_torch_imported(tmp_path):
    from tokenizers import Tokenizer, models, pre_tokenizers

    tok = Tokenizer(models.WordLevel({"[UNK]": 0, "[PAD]": 1, "urgent": 2, "[URL]": 3, "[PHONE]": 4}, unk_token="[UNK]"))
    tok.pre_tokenizer = pre_tokenizers.Whitespace()
    tok.enable_truncation(max_length=8)
    tok.enable_padding(pad_id=1, pad_token="[PAD]", length=8)

    class _FakeInp:
        def __init__(self, name):
            self.name = name

    class _FakeSession:
        def get_inputs(self):
            return [_FakeInp("input_ids"), _FakeInp("attention_mask"), _FakeInp("token_type_ids")]

        def run(self, _out, feeds):
            assert feeds["input_ids"].dtype == np.int64
            batch = feeds["input_ids"].shape[0]
            return [np.tile(np.array([[-1.5, 2.0]], dtype=np.float32), (batch, 1))]

    clf = OnnxScamClassifier(_FakeSession(), tok, max_length=8)
    res = clf.predict("URGENT click https://bit.ly/x call 9876543210")
    assert res.is_scam and res.risk == "high" and res.confidence > 0.9

    # Missing dir does not cache None and cleanly returns None; disabled flag returns None
    assert load_classifier(tmp_path / "missing", enabled=True) is None
    assert load_classifier(tmp_path, enabled=False) is None

    # Runtime invariant D3: transformers and torch must not be imported by backend app modules
    assert "transformers" not in sys.modules
    assert "torch" not in sys.modules


@pytest.mark.parametrize("lang", ["mr", "hi", "en"])
def test_ml_fallback_has_no_banned_words(lang):
    for risk in ("medium", "high"):
        entry = _ML_FALLBACK[lang][risk]
        combined = " ".join([entry["scam_type"], *entry["reasons"], *entry["next_steps"]])
        assert not FORBIDDEN_WORDS_RE.search(combined), (lang, risk)
