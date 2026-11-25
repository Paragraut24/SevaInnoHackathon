from typing import Literal
from pydantic import BaseModel, ConfigDict, Field

Risk = Literal["low", "medium", "high"]
Lang = Literal["mr", "hi", "en"]
Mode = Literal["full", "quick"]
MlModelStatus = Literal["loaded", "unavailable"]


class TriageIn(BaseModel):
    """Incoming message payload for scam triage."""

    model_config = ConfigDict(str_strip_whitespace=True)

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


class TokenWeight(BaseModel):
    """Single word-importance score from the occlusion explainer."""

    token: str
    weight: float


class TriageOut(LlmOut):
    """Final server response after 3-signal fusion."""

    lang: Lang
    mode: Mode
    show_helpline: bool
    ml_confidence: float | None = None
    top_tokens: list[TokenWeight] = Field(default_factory=list)


class ErrorOut(BaseModel):
    """Localized API error payload without stack traces."""

    error_code: str
    message: str


class HealthOut(BaseModel):
    status: Literal["ok"]
    ml_model: MlModelStatus = "unavailable"

