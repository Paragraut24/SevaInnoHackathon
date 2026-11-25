"""Pure-numpy word-occlusion importance explainer for Sajag V2 (replaces heavy LIME dependency)."""
import logging
import time
from typing import Any

import numpy as np

from app.schemas import TokenWeight

logger = logging.getLogger("sajag.explainer")

MAX_VARIANTS = 100
MAX_TOKENS = 6
EXPLAIN_BUDGET_S = 2.0
MIN_WEIGHT = 1e-4


def explain_text(
    text: str,
    classifier: Any,
    max_tokens: int = MAX_TOKENS,
    budget_s: float = EXPLAIN_BUDGET_S,
) -> list[TokenWeight]:
    """Compute top word-occlusion importance weights in a single batched ONNX call."""
    if classifier is None:
        return []

    words = text.split()
    if len(words) <= 1:
        return []

    unique_words = list(dict.fromkeys(words))[: MAX_VARIANTS - 1]
    variants = [" ".join(w for w in words if w != target) or " " for target in unique_words]

    start = time.monotonic()
    try:
        probs = classifier.predict_proba_batch([text, *variants])
    except Exception as exc:
        logger.warning("word_occlusion_failed type=%s", type(exc).__name__)
        return []

    if time.monotonic() - start > budget_s:
        logger.warning("word_occlusion_budget_exceeded budget_s=%s", budget_s)
        return []

    base_scam_prob = float(probs[0, 1])
    variant_scam_probs = np.asarray(probs[1:, 1], dtype=np.float64)
    deltas = base_scam_prob - variant_scam_probs

    ranked_indices = np.argsort(np.abs(deltas))[::-1]
    top: list[TokenWeight] = []
    for idx in ranked_indices:
        weight = round(float(deltas[idx]), 4)
        if abs(weight) < MIN_WEIGHT:
            continue
        top.append(TokenWeight(token=unique_words[int(idx)], weight=weight))
        if len(top) >= max_tokens:
            break
    return top
