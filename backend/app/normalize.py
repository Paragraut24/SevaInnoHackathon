import re
import unicodedata
from typing import Literal

Script = Literal["deva", "latin", "mixed"]

ZERO_WIDTH = dict.fromkeys(map(ord, "\u200b\u200c\u200d\u2060\ufeff"))
DEVA_DIGITS = {ord(d): str(i) for i, d in enumerate("०१२३४५६७८९")}
TRANSLATION = {**ZERO_WIDTH, **DEVA_DIGITS}

DEVA_RE = re.compile(r"[\u0900-\u097f]")
LATIN_RE = re.compile(r"[a-z]")
DEVA_SHARE_MIN = 0.8
LATIN_SHARE_MIN = 0.8

TLDS = (
    "com|in|org|net|co|io|me|ly|gy|gl|xyz|top|info|gov|app|link|click|live|site|"
    "online|vip|win|loan|ee|cc|tk|ml|ga|cf|gq|us|biz|store|shop"
)
URL_RE = re.compile(
    r"https?://[^\s]+"
    rf"|(?<![@\w./-])(?:[a-z0-9-]+\.)+(?:{TLDS})(?![a-z0-9-])(?::[0-9]+)?(?:/[^\s]*)?"
)
URL_TRAILING = ".,;:!?)]}>'\"\u0964"

PHONE_RE = re.compile(r"(?<![0-9])(?:(?:\+?91|0)[ -]?)?([6-9](?:[ -]?[0-9]){9})(?![0-9])")


def normalize_text(s: str) -> str:
    """NFC, drop zero-width chars, ASCII digits, lowercase Latin, collapse whitespace."""
    s = unicodedata.normalize("NFC", s).translate(TRANSLATION).lower()
    return " ".join(s.split())


def detect_script(s: str) -> Script:
    """Classify by the share of Devanagari vs Latin letters."""
    s = normalize_text(s)
    deva, latin = len(DEVA_RE.findall(s)), len(LATIN_RE.findall(s))
    total = deva + latin
    if total == 0:
        return "latin"
    if deva / total >= DEVA_SHARE_MIN:
        return "deva"
    return "latin" if latin / total >= LATIN_SHARE_MIN else "mixed"


def extract_urls(s: str) -> list[str]:
    """URLs with scheme or bare domain.tld/path, de-duplicated in order of appearance."""
    urls = (m.group().rstrip(URL_TRAILING) for m in URL_RE.finditer(normalize_text(s)))
    return list(dict.fromkeys(urls))


def extract_phones(s: str) -> list[str]:
    """Indian mobile numbers as 10 digits (6-9 start), de-duplicated in order."""
    phones = (re.sub(r"\D", "", m.group(1)) for m in PHONE_RE.finditer(normalize_text(s)))
    return list(dict.fromkeys(phones))

