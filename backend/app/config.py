from functools import lru_cache
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT_ENV = Path(__file__).resolve().parents[2] / ".env"


class Settings(BaseSettings):
    """Application settings loaded from environment variables or root .env."""

    model_config = SettingsConfigDict(
        env_file=str(ROOT_ENV),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    gemini_api_key: str = ""
    gemini_model: str = "gemini-3.5-flash-lite"
    sightengine_api_user: str = ""
    sightengine_api_secret: str = ""
    hf_token: str = ""
    allowed_origin: str = "http://localhost:5173,https://seva-inno-hackathon-project.vercel.app"
    rate_limit_per_min: int = 20

    @property
    def cors_origins(self) -> list[str]:
        return [o.strip() for o in self.allowed_origin.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()

