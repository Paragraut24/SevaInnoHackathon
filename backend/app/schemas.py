from typing import Literal
from pydantic import BaseModel, Field

Risk = Literal["low", "medium", "high"]
Lang = Literal["mr", "hi", "en"]
Mode = Literal["full", "quick"]


class TriageIn(BaseModel):
    """Incoming message payload for scam triage."""

    text: str = Field(min_length=1, max_length=2000)
    lang: Lang = "mr"


class LlmOut(BaseModel):
    """Flat structured JSON schema returned by Gemini Interactions API."""

    risk: Risk = Field(description="Risk level: low, medium, or high.")
    scam_type: str = Field(description="Short category label in target language.")
    reasons: list[str] = Field(
        max_length=3,
        description="Up to 3 concise plain-language reasons in target language.",
    )
    next_steps: list[str] = Field(
        max_length=3,
        description="Up to 3 actionable next steps in target language.",
    )
    confidence: float = Field(ge=0.0, le=1.0, description="Model confidence 0..1.")


class TriageOut(LlmOut):
    """Final server response after rule-floor fusion."""

    lang: Lang
    mode: Mode
    show_helpline: bool


class ErrorOut(BaseModel):
    """Localized API error payload without stack traces."""

    error_code: str
    message: str


class HealthOut(BaseModel):
    status: Literal["ok"]

