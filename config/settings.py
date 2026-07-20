"""Application settings loaded from environment variables.

All configuration is centralized here using pydantic-settings so that no
secret or environment-specific value is hardcoded anywhere in the codebase.
"""

from __future__ import annotations

from functools import lru_cache

from pydantic import Field, SecretStr, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Strongly-typed application configuration.

    Values are read from environment variables (and a local ``.env`` file
    during development). See ``.env.example`` for the full list.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # ---- Telegram ----
    bot_token: SecretStr = Field(..., alias="BOT_TOKEN")

    # ---- AI provider ----
    ai_provider: str = Field("gemini", alias="AI_PROVIDER")
    gemini_api_key: SecretStr = Field(..., alias="GEMINI_API_KEY")
    gemini_text_model: str = Field("gemini-1.5-flash", alias="GEMINI_TEXT_MODEL")
    gemini_vision_model: str = Field("gemini-1.5-flash", alias="GEMINI_VISION_MODEL")
    gemini_audio_model: str = Field("gemini-1.5-flash", alias="GEMINI_AUDIO_MODEL")

    # ---- Database (PostgreSQL) ----
    postgres_host: str = Field("localhost", alias="POSTGRES_HOST")
    postgres_port: int = Field(5432, alias="POSTGRES_PORT")
    postgres_user: str = Field("assistant", alias="POSTGRES_USER")
    postgres_password: SecretStr = Field(SecretStr("assistant"), alias="POSTGRES_PASSWORD")
    postgres_db: str = Field("assistant", alias="POSTGRES_DB")

    # ---- Redis ----
    redis_host: str = Field("localhost", alias="REDIS_HOST")
    redis_port: int = Field(6379, alias="REDIS_PORT")
    redis_db: int = Field(0, alias="REDIS_DB")

    # ---- App behaviour ----
    log_level: str = Field("INFO", alias="LOG_LEVEL")
    history_limit: int = Field(20, alias="HISTORY_LIMIT")
    rate_limit_seconds: float = Field(1.0, alias="RATE_LIMIT_SECONDS")
    rate_limit_max_requests: int = Field(20, alias="RATE_LIMIT_MAX_REQUESTS")
    max_input_chars: int = Field(4000, alias="MAX_INPUT_CHARS")

    @computed_field  # type: ignore[prop-decorator]
    @property
    def database_url(self) -> str:
        """Async SQLAlchemy connection URL for PostgreSQL."""
        password = self.postgres_password.get_secret_value()
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @computed_field  # type: ignore[prop-decorator]
    @property
    def redis_url(self) -> str:
        """Connection URL for Redis (used by aiogram FSM storage)."""
        return f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return a cached :class:`Settings` instance.

    The cache guarantees settings are parsed only once per process.
    """
    return Settings()  # type: ignore[call-arg]
