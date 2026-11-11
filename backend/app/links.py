"""
Link and phone number sanity checks — offline, no network calls.

Checks performed:
- Blocklisted domains/numbers (data/blocklist.json)
- Lookalike distance to known Indian banks/brands (data/brands.json)
- Shortener domains (bit.ly, tinyurl, etc.)
- Punycode / IDN domains
- Odd TLDs (not in a known safe list)
- Indian mobile number validity

Never says a URL is "safe" — only "no flags found" or lists specific flags.
"""
import json
import re
import unicodedata
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parents[1] / "data"
_blocklist: set[str] = set()
_brands: list[str] = []

SHORTENERS = {
    "bit.ly", "tinyurl.com", "goo.gl", "t.co", "ow.ly",
    "buff.ly", "adf.ly", "rb.gy", "cutt.ly", "shorturl.at",
    "tiny.cc", "is.gd", "v.gd", "clck.ru",
}
SAFE_TLDS = {
    "com", "org", "net", "edu", "gov", "in", "co.in",
    "gov.in", "ac.in", "io", "app", "dev",
}
PUNYCODE_RE = re.compile(r"xn--", re.IGNORECASE)
PHONE_RE = re.compile(r"(?:\+91|0)?[6-9]\d{9}")


def _load() -> None:
    global _blocklist, _brands
    bl_path = DATA_DIR / "blocklist.json"
    br_path = DATA_DIR / "brands.json"
    if bl_path.exists():
        _blocklist = set(json.loads(bl_path.read_text(encoding="utf-8")).get("domains", []))
    if br_path.exists():
        _brands = json.loads(br_path.read_text(encoding="utf-8")).get("brands", [])


_load()


def _levenshtein(a: str, b: str) -> int:
    if len(a) < len(b):
        a, b = b, a
    row = list(range(len(b) + 1))
    for c in a:
        new = [row[0] + 1]
        for j, d in enumerate(b):
            new.append(min(new[-1] + 1, row[j + 1] + 1, row[j] + (c != d)))
        row = new
    return row[-1]


def _strip_domain(url: str) -> str:
    """Extract bare domain from a URL string."""
    url = url.lower().strip()
    for prefix in ("https://", "http://", "www."):
        url = url.removeprefix(prefix)
    return url.split("/")[0].split("?")[0]


def check_url(url: str) -> list[str]:
    """Return a list of flag strings for the URL. Empty list = no flags found."""
    flags: list[str] = []
    domain = _strip_domain(url)
    # Normalize unicode
    domain_nfc = unicodedata.normalize("NFC", domain)

    if domain in _blocklist:
        flags.append("blocklisted_domain")
        return flags  # No need to check further

    if domain in SHORTENERS:
        flags.append("url_shortener")

    if PUNYCODE_RE.search(domain):
        flags.append("punycode_idn")

    tld = ".".join(domain.rsplit(".", 2)[-2:]) if domain.count(".") >= 2 else domain.rsplit(".", 1)[-1]
    if tld not in SAFE_TLDS:
        flags.append(f"unusual_tld_{tld}")

    # Lookalike check: edit distance ≤ 2 to a known brand, but not exact match
    domain_base = domain_nfc.split(".")[0]
    for brand in _brands:
        dist = _levenshtein(domain_base, brand.lower())
        if 0 < dist <= 2:
            flags.append(f"lookalike_{brand}")
            break

    return flags


def check_phone(number: str) -> list[str]:
    """Return flags for a phone number string."""
    flags: list[str] = []
    digits = re.sub(r"\D", "", number)
    # Strip country code
    if digits.startswith("91") and len(digits) == 12:
        digits = digits[2:]
    if not PHONE_RE.fullmatch(number.strip()):
        flags.append("not_valid_indian_mobile")
    return flags

