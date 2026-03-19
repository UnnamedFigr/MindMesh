"""
MindMesh Backend Configuration.

All environment variables are loaded here via Pydantic Settings.
The app fails fast on startup if any required variable is missing.
"""

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

_ENV_FILE = str(Path(__file__).resolve().parent.parent / ".env")


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # ── Supabase ──────────────────────────────────────────────
    supabase_url: str
    supabase_service_key: str
    supabase_jwt_secret: str = ""  # Not used for verification; kept for reference

    # ── OpenAI ────────────────────────────────────────────────
    openai_api_key: str

    # ── Groq (primary LLM provider) ─────────────────────────────
    groq_api_key: str
    groq_base_url: str = "https://api.groq.com/openai/v1"

    # ── YouTube ───────────────────────────────────────────────
    youtube_api_key: str = ""  # Optional — for metadata enrichment

    # ── Stripe ────────────────────────────────────────────────
    stripe_secret_key: str = ""
    stripe_webhook_secret: str = ""

    # ── App Config ────────────────────────────────────────────
    allowed_origins: str = "http://localhost:3000"
    environment: str = "development"
    daily_spend_cap_usd: float = 50.0
    max_video_duration_seconds: int = 14400  # 4 hours
    sentry_dsn: str = ""  # Optional — set in production

    # ── Model Config ──────────────────────────────────────────
    triage_model: str = "llama-3.1-8b-instant"
    guide_model: str = "meta-llama/llama-4-scout-17b-16e-instruct"       # Groq — short videos
    guide_model_long: str = "gpt-4.1"                                       # OpenAI — long videos (30 min+)
    long_video_token_threshold: int = 13000                                # ~30 min of speech with timestamps
    quiz_model: str = "llama-3.1-8b-instant"
    embedding_model: str = "text-embedding-3-small"
    whisper_model: str = "whisper-large-v3-turbo"

    # ── Rate Limits ───────────────────────────────────────────
    max_concurrent_jobs_per_user: int = 1
    job_cooldown_seconds: int = 30
    job_timeout_seconds: int = 300  # 5 minutes

    model_config = SettingsConfigDict(
        env_file=_ENV_FILE,
        env_file_encoding="utf-8",
        case_sensitive=False,
    )


@lru_cache
def get_settings() -> Settings:
    """Cached singleton for application settings."""
    return Settings()
