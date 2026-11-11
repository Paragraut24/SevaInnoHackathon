import json
import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path

from app.normalize import normalize_text
from app.schemas import Lang, Risk

DATA_DIR = Path(__file__).resolve().parents[1] / "data"
LANGS: tuple[Lang, ...] = ("mr", "hi", "en")
GENERIC = "generic"
KNOWN_SCRIPT_GROUPS = {"authority", "money", "threat"}
NEGATION_RE = re.compile(r"do not|don['\u2019]?t|never|कधीही|नका|नको|मत|न करें|न करे|साझा न|शेयर न|नहीं")
NEGATION_WINDOW = 40


@dataclass(frozen=True)
class _Cue:
    category: str
    group: str
    weight: int
    guard: bool
    regexes: tuple[re.Pattern, ...]


@dataclass(frozen=True)
class RuleResult:
    score: int
    matched: list[tuple[str, str]]
    top_category: str | None
    floor: Risk
    known_script: bool


def _load() -> tuple[list[_Cue], dict[str, dict]]:
    cues, fallback = [], {}
    for lang in LANGS:
        data = json.loads((DATA_DIR / f"patterns_{lang}.json").read_text(encoding="utf-8"))
        for c in data["cues"]:
            regexes = tuple(
                re.compile(unicodedata.normalize("NFC", p), re.IGNORECASE) for p in c["patterns"]
            )
            cues.append(_Cue(c["category_id"], c["cue_group"], c["weight"], c.get("guard", False), regexes))
        fallback[lang] = data["fallback"]
    return cues, fallback


_CUES, _FALLBACK = _load()


def _matches(cue: _Cue, text: str) -> bool:
    """True if any pattern hits; guarded cues ignore hits near a negation (e.g. 'never share OTP')."""
    return any(
        not (cue.guard and NEGATION_RE.search(text[max(0, m.start() - NEGATION_WINDOW) : m.end() + NEGATION_WINDOW]))
        for rx in cue.regexes
        for m in rx.finditer(text)
    )


def evaluate(text: str) -> RuleResult:
    """Run all cues (every language, regardless of script) and derive the risk floor."""
    norm = normalize_text(text)
    hits: dict[tuple[str, str], int] = {}
    for cue in _CUES:
        if _matches(cue, norm):
            key = (cue.category, cue.group)
            hits[key] = max(hits.get(key, 0), cue.weight)

    groups = {group for _, group in hits}
    scores: dict[str, int] = {}
    for (category, _), weight in hits.items():
        if category != GENERIC:
            scores[category] = scores.get(category, 0) + weight

    top = max(scores, key=scores.get) if scores else None
    known = top is not None and len(groups) >= 2 and bool(groups & KNOWN_SCRIPT_GROUPS)
    floor: Risk = "high" if known else "medium" if len(groups) >= 2 else "low"
    return RuleResult(sum(hits.values()), sorted(hits), top, floor, known)


def get_fallback(category: str | None, lang: Lang) -> dict:
    """Static localized {scam_type, reasons, next_steps} for the rules-only (quick) answer."""
    table = _FALLBACK[lang]
    return table.get(category) or table[GENERIC]
