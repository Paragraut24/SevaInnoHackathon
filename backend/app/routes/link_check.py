"""
Link + number check route — POST /api/link-check.

Accepts a list of URLs and/or phone numbers extracted from a suspicious message.
Returns flags per item. Never says "safe" — only "no flags found" or lists flags.
"""
from fastapi import APIRouter, Request
from pydantic import BaseModel, Field

from app.limiter import limiter, rate_limit
from app.links import check_phone, check_url
from app.normalize import extract_phones, extract_urls
from app.schemas import ErrorOut

router = APIRouter()

MAX_ITEMS = 10


class LinkCheckIn(BaseModel):
    text: str = Field(min_length=1, max_length=2000)


class ItemResult(BaseModel):
    value: str
    kind: str  # "url" | "phone"
    flags: list[str]


class LinkCheckOut(BaseModel):
    items: list[ItemResult]
    limits_note: str = (
        "This check uses offline pattern matching only. "
        "A clean result does not mean the link or number is safe."
    )


@router.post(
    "/api/link-check",
    response_model=LinkCheckOut,
    responses={422: {"model": ErrorOut}, 429: {"model": ErrorOut}},
)
@limiter.limit(rate_limit)
async def link_check(request: Request, body: LinkCheckIn) -> LinkCheckOut:
    """Extract URLs and phone numbers from text, run offline flag checks."""
    urls = list(extract_urls(body.text))[:MAX_ITEMS]
    phones = list(extract_phones(body.text))[:MAX_ITEMS]

    items: list[ItemResult] = []
    for url in urls:
        items.append(ItemResult(value=url, kind="url", flags=check_url(url)))
    for phone in phones:
        items.append(ItemResult(value=phone, kind="phone", flags=check_phone(phone)))

    return LinkCheckOut(items=items)

