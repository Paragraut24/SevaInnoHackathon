from fastapi import APIRouter, Request

from app import llm
from app.fuse import fuse
from app.limiter import limiter, rate_limit
from app.rules import evaluate
from app.schemas import ErrorOut, TriageIn, TriageOut

router = APIRouter()


@router.post(
    "/api/triage",
    response_model=TriageOut,
    responses={422: {"model": ErrorOut}, 429: {"model": ErrorOut}, 500: {"model": ErrorOut}},
)
@limiter.limit(rate_limit)
async def triage(request: Request, body: TriageIn) -> TriageOut:
    """Normalize and rule-check the message, ask Gemini, then fuse into one validated answer."""
    rule = evaluate(body.text)
    hints = [f"{category}:{group}" for category, group in rule.matched]
    result = fuse(rule, await llm.analyze(body.text, body.lang, hints), body.lang)
    request.state.log_extra = f"lang={result.lang} risk={result.risk} mode={result.mode}"
    return result
