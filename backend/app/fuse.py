from app.classifier import MlResult
from app.config import ML_TRUST_THRESHOLD
from app.rules import RuleResult, get_fallback
from app.schemas import Lang, LlmOut, Risk, TriageOut

RANK: dict[Risk, int] = {"low": 0, "medium": 1, "high": 2}
QUICK_CONFIDENCE: dict[Risk, float] = {"low": 0.3, "medium": 0.5, "high": 0.7}
MAX_ITEMS = 3

_ML_FALLBACK: dict[Lang, dict[Risk, dict]] = {
    "mr": {
        "medium": {
            "scam_type": "संशयास्पद संदेश (AI तपासणी)",
            "reasons": ["भाषा नमुन्यांच्या AI तपासणीत काही संशयास्पद चिन्हे आढळली आहेत."],
            "next_steps": [
                "अनोळखी लिंकवर क्लिक करू नका; OTP, पिन किंवा पासवर्ड देऊ नका.",
                "अधिकृत नंबर किंवा ॲपवरून खात्री करा.",
            ],
        },
        "high": {
            "scam_type": "उच्च धोका फसवणूक संकेत (AI तपासणी)",
            "reasons": ["भाषा नमुन्यांच्या AI तपासणीत फसवणुकीची तीव्र चिन्हे आढळली आहेत."],
            "next_steps": [
                "लिंकवर क्लिक करू नका आणि पैसे, OTP किंवा बँक माहिती देऊ नका.",
                "पैशाचे नुकसान झाल्यास तात्काळ १९३० वर कॉल करा.",
            ],
        },
    },
    "hi": {
        "medium": {
            "scam_type": "संदिग्ध संदेश (AI जांच)",
            "reasons": ["भाषा पैटर्न की AI जांच में कुछ संदिग्ध संकेत मिले हैं।"],
            "next_steps": [
                "अनजान लिंक पर क्लिक न करें; OTP, पिन या पासवर्ड न दें।",
                "आधिकारिक नंबर या ऐप से पुष्टि करें।",
            ],
        },
        "high": {
            "scam_type": "ऊंचा खतरा ठगी संकेत (AI जांच)",
            "reasons": ["भाषा पैटर्न की AI जांच में ठगी के मजबूत संकेत मिले हैं।"],
            "next_steps": [
                "लिंक पर क्लिक न करें और पैसे, OTP या बैंक जानकारी न दें।",
                "पैसे कटे हों तो तुरंत 1930 पर कॉल करें।",
            ],
        },
    },
    "en": {
        "medium": {
            "scam_type": "Suspicious message (AI check)",
            "reasons": ["The language pattern classifier flagged suspicious warning signs."],
            "next_steps": [
                "Do not click unknown links or share OTP, PIN, or passwords.",
                "Verify with the sender using an official number or app.",
            ],
        },
        "high": {
            "scam_type": "High-risk scam signal (AI check)",
            "reasons": ["The language pattern classifier found strong signs of a scam."],
            "next_steps": [
                "Do not click links or send money, OTP, or bank details.",
                "Call 1930 immediately if money has left your account.",
            ],
        },
    },
}


def _ml_fallback(risk: Risk, lang: Lang) -> dict:
    return _ML_FALLBACK[lang]["high" if risk == "high" else "medium"]


def _build(
    risk: Risk,
    content: dict,
    confidence: float,
    lang: Lang,
    mode: str,
    ml_confidence: float | None = None,
) -> TriageOut:
    return TriageOut(
        risk=risk,
        scam_type=content["scam_type"],
        reasons=content["reasons"][:MAX_ITEMS],
        next_steps=content["next_steps"][:MAX_ITEMS],
        confidence=confidence,
        lang=lang,
        mode=mode,
        show_helpline=risk == "high",
        ml_confidence=ml_confidence,
    )


def fuse(rule: RuleResult, llm: LlmOut | None, lang: Lang, ml: MlResult | None = None) -> TriageOut:
    """Combine rule floor, optional ML signal, and LLM output into one validated result.

    Rule floor can never be lowered. Only a confident scam prediction from ML (is_scam and
    confidence >= ML_TRUST_THRESHOLD) may raise the risk floor; confident ham never lowers
    the rule floor and never triggers the known-script escalation branch.
    """
    ml_active = ml is not None and ml.is_scam and ml.confidence >= ML_TRUST_THRESHOLD
    ml_floor: Risk = ml.risk if ml_active else "low"
    ml_conf = ml.confidence if ml is not None else None

    effective_floor_rank = max(RANK[rule.floor], RANK[ml_floor])
    effective_floor: Risk = next(r for r, v in RANK.items() if v == effective_floor_rank)

    if llm is None:
        if ml_active and RANK[ml_floor] > RANK[rule.floor] and rule.floor == "low":
            content = _ml_fallback(effective_floor, lang)
        else:
            category = rule.top_category if rule.floor != "low" else None
            content = get_fallback(category, lang)
        return _build(effective_floor, content, QUICK_CONFIDENCE[effective_floor], lang, "quick", ml_conf)

    if rule.known_script or ml_active:
        risk = max(effective_floor, llm.risk, key=RANK.get)
    else:
        risk = llm.risk

    content = llm.model_dump()
    if RANK[llm.risk] < RANK[risk]:
        if rule.known_script and RANK[rule.floor] >= RANK[ml_floor]:
            fb = get_fallback(rule.top_category, lang)
        else:
            fb = _ml_fallback(risk, lang)
        content = {**fb, "reasons": [fb["reasons"][0], *llm.reasons]}
    return _build(risk, content, llm.confidence, lang, "full", ml_conf)
