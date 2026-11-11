from app.rules import RuleResult, get_fallback
from app.schemas import Lang, LlmOut, Risk, TriageOut

RANK: dict[Risk, int] = {"low": 0, "medium": 1, "high": 2}
QUICK_CONFIDENCE: dict[Risk, float] = {"low": 0.3, "medium": 0.5, "high": 0.7}
MAX_ITEMS = 3


def _build(risk: Risk, content: dict, confidence: float, lang: Lang, mode: str) -> TriageOut:
    return TriageOut(
        risk=risk,
        scam_type=content["scam_type"],
        reasons=content["reasons"][:MAX_ITEMS],
        next_steps=content["next_steps"][:MAX_ITEMS],
        confidence=confidence,
        lang=lang,
        mode=mode,
        show_helpline=risk == "high",
    )


def fuse(rule: RuleResult, llm: LlmOut | None, lang: Lang) -> TriageOut:
    """Combine rule floor and model output.

    A known scam script can be raised by the model but never lowered below the rule floor.
    Without a model answer, return the rules-only (quick) result with static localized text.
    """
    if llm is None:
        category = rule.top_category if rule.floor != "low" else None
        return _build(rule.floor, get_fallback(category, lang), QUICK_CONFIDENCE[rule.floor], lang, "quick")

    risk = max(rule.floor, llm.risk, key=RANK.get) if rule.known_script else llm.risk
    content = llm.model_dump()
    if RANK[llm.risk] < RANK[risk]:
        fb = get_fallback(rule.top_category, lang)
        content = {**fb, "reasons": [fb["reasons"][0], *llm.reasons]}
    return _build(risk, content, llm.confidence, lang, "full")
