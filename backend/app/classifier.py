"""Lightweight ONNX + tokenizers runtime classifier for Sajag V2 (no transformers/torch)."""
import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np

from app.config import ML_CONFIDENCE_HIGH, ML_CONFIDENCE_MEDIUM, ML_MAX_LENGTH
from app.normalize import preprocess_for_ml
from app.schemas import Risk

logger = logging.getLogger("sajag.classifier")

DEFAULT_MODEL_DIR = Path(__file__).resolve().parents[1] / "model"
ONNX_FILENAME = "model_quantized.onnx"
TOKENIZER_FILENAME = "tokenizer.json"
CONFIG_FILENAME = "config.json"


@dataclass(frozen=True)
class MlResult:
    """Prediction result from the ONNX scam classifier."""

    is_scam: bool
    scam_prob: float
    confidence: float
    risk: Risk


def _softmax(logits: np.ndarray) -> np.ndarray:
    shifted = logits - np.max(logits, axis=-1, keepdims=True)
    exp = np.exp(shifted)
    return exp / np.sum(exp, axis=-1, keepdims=True)


class OnnxScamClassifier:
    """Thread-safe wrapper around ONNX Runtime session and fast Rust tokenizer."""

    def __init__(self, session: Any, tokenizer: Any, max_length: int = ML_MAX_LENGTH) -> None:
        self._session = session
        self._tokenizer = tokenizer
        self._max_length = max_length
        self._input_names = {inp.name for inp in session.get_inputs()}

    def predict_proba_batch(self, texts: list[str]) -> np.ndarray:
        """Return (N, 2) probabilities [ham, scam] for raw texts using shared ML preprocessing."""
        if not texts:
            return np.empty((0, 2), dtype=np.float32)

        processed = [preprocess_for_ml(t) for t in texts]
        encodings = self._tokenizer.encode_batch(processed)

        ort_inputs: dict[str, np.ndarray] = {
            "input_ids": np.array([enc.ids for enc in encodings], dtype=np.int64),
            "attention_mask": np.array([enc.attention_mask for enc in encodings], dtype=np.int64),
        }
        if "token_type_ids" in self._input_names:
            ort_inputs["token_type_ids"] = np.array([enc.type_ids for enc in encodings], dtype=np.int64)

        logits = self._session.run(None, ort_inputs)[0]
        return _softmax(np.asarray(logits, dtype=np.float32))

    def predict(self, text: str) -> MlResult:
        """Predict binary scam probability, confidence, and mapped risk level for one message."""
        probs = self.predict_proba_batch([text])[0]
        scam_prob = float(probs[1])
        is_scam = scam_prob > 0.5
        confidence = round(scam_prob if is_scam else 1.0 - scam_prob, 3)

        if scam_prob >= ML_CONFIDENCE_HIGH:
            risk: Risk = "high"
        elif scam_prob >= ML_CONFIDENCE_MEDIUM:
            risk = "medium"
        else:
            risk = "low"

        return MlResult(
            is_scam=is_scam,
            scam_prob=round(scam_prob, 4),
            confidence=confidence,
            risk=risk,
        )


def load_classifier(model_dir: Path | None = None, enabled: bool = True) -> OnnxScamClassifier | None:
    """Load quantized ONNX model and tokenizer.json once at startup; returns None if unavailable."""
    if not enabled:
        logger.info("ml_classifier_disabled")
        return None

    resolved_dir = model_dir or DEFAULT_MODEL_DIR
    onnx_path = resolved_dir / ONNX_FILENAME
    tokenizer_path = resolved_dir / TOKENIZER_FILENAME
    if not onnx_path.exists() or not tokenizer_path.exists():
        logger.warning("ml_model_unavailable dir=%s", resolved_dir)
        return None

    try:
        import onnxruntime as ort
        from tokenizers import Tokenizer

        max_length = ML_MAX_LENGTH
        pad_id = 0
        config_path = resolved_dir / CONFIG_FILENAME
        if config_path.exists():
            cfg = json.loads(config_path.read_text(encoding="utf-8"))
            max_length = int(cfg.get("max_length", ML_MAX_LENGTH))
            pad_id = int(cfg.get("pad_token_id", 0))

        opts = ort.SessionOptions()
        opts.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
        opts.intra_op_num_threads = 1
        opts.inter_op_num_threads = 1

        session = ort.InferenceSession(
            str(onnx_path),
            providers=["CPUExecutionProvider"],
            sess_options=opts,
        )
        tokenizer = Tokenizer.from_file(str(tokenizer_path))
        tokenizer.enable_truncation(max_length=max_length)
        tokenizer.enable_padding(pad_id=pad_id, length=max_length)
        logger.info("ml_model_loaded max_length=%s", max_length)
        return OnnxScamClassifier(session, tokenizer, max_length=max_length)
    except Exception as exc:
        logger.error("ml_model_load_failed type=%s", type(exc).__name__)
        return None
