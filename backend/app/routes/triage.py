import asyncio
import logging

from fastapi import APIRouter, Query, Request

from app import llm
from app.explainer import EXPLAIN_BUDGET_S, explain_text
from app.fuse import fuse
from app.limiter import limiter, rate_limit
from app.rules import evaluate
from app.schemas import ErrorOut, TriageIn, TriageOut

logger = logging.getLogger("sajag.triage")
router = APIRouter()


@router.post(
    "/api/triage",
    response_model=TriageOut,
    responses={422: {"model": ErrorOut}, 429: {"model": ErrorOut}, 500: {"model": ErrorOut}},
)
@limiter.limit(rate_limit)
async def triage(request: Request, body: TriageIn, explain: bool = Query(False)) -> TriageOut:
    """Normalize, rule-check, run optional ONNX ML signal, ask Gemini, then fuse into one answer."""
    rule = evaluate(body.text)
    hints = [f"{category}:{group}" for category, group in rule.matched]

    classifier = getattr(request.app.state, "classifier", None)
    ml = None
    if classifier is not None:
        try:
            ml = await asyncio.to_thread(classifier.predict, body.text)
        except Exception as exc:
            logger.warning("ml_predict_failed type=%s", type(exc).__name__)

    llm_result = await llm.analyze(body.text, body.lang, hints)
    result = fuse(rule, llm_result, body.lang, ml=ml)

    if explain and classifier is not None and ml is not None:
        try:
            result.top_tokens = await asyncio.wait_for(
                asyncio.to_thread(explain_text, body.text, classifier),
                timeout=EXPLAIN_BUDGET_S,
            )
        except (asyncio.TimeoutError, Exception) as exc:
            logger.warning("ml_explain_skipped type=%s", type(exc).__name__)

    request.state.log_extra = (
        f"lang={result.lang} risk={result.risk} mode={result.mode} ml_conf={result.ml_confidence}"
    )
    return result
