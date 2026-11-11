from fastapi import Request
from fastapi.responses import JSONResponse

from app.schemas import ErrorOut, Lang

DEFAULT_LANG: Lang = "mr"
LANG_HEADER = "x-lang"

MESSAGES: dict[str, dict[Lang, str]] = {
    "invalid_input": {
        "mr": "संदेश अवैध किंवा रिकामा आहे.",
        "hi": "संदेश अमान्य या खाली है।",
        "en": "The message is invalid or empty.",
    },
    "text_too_long": {
        "mr": "संदेश खूप मोठा आहे (कमाल 2000 अक्षरे).",
        "hi": "संदेश बहुत लंबा है (अधिकतम 2000 अक्षर)।",
        "en": "The message is too long (maximum 2000 characters).",
    },
    "rate_limited": {
        "mr": "खूप विनंत्या आल्या. कृपया थोड्या वेळाने पुन्हा प्रयत्न करा.",
        "hi": "बहुत अधिक अनुरोध। कृपया थोड़ी देर बाद फिर कोशिश करें।",
        "en": "Too many requests. Please try again in a moment.",
    },
    "internal": {
        "mr": "काहीतरी चुकले. कृपया पुन्हा प्रयत्न करा.",
        "hi": "कुछ गलत हुआ। कृपया फिर कोशिश करें।",
        "en": "Something went wrong. Please try again.",
    },
}


def request_lang(request: Request) -> Lang:
    """Language for error text, taken from the X-Lang header (bodies may be unparsable)."""
    lang = request.headers.get(LANG_HEADER, DEFAULT_LANG)
    return lang if lang in ("mr", "hi", "en") else DEFAULT_LANG


def error_response(request: Request, status: int, code: str) -> JSONResponse:
    """Localized ErrorOut without stack traces or echoed input."""
    body = ErrorOut(error_code=code, message=MESSAGES[code][request_lang(request)])
    return JSONResponse(status_code=status, content=body.model_dump())
