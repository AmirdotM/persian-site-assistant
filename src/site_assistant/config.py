"""Central application settings loaded from environment variables / .env."""

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration. Secrets belong in .env or the hosting provider's secret store."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    app_name: str = "دستیار هوشمند وب‌سایت"
    app_env: str = "development"
    api_prefix: str = "/api/v1"
    cors_origins: str = "http://127.0.0.1:5500,http://localhost:5500"
    public_demo_mode: bool = False
    public_demo_rate_limit_per_minute: int = 12

    llm_api_key: str | None = None
    llm_base_url: str | None = None
    llm_model: str | None = None
    llm_timeout_seconds: float = 30.0

    embedding_model: str = "intfloat/multilingual-e5-small"
    embedding_device: str = "cpu"
    retrieval_top_k: int = 4
    retrieval_min_score: float = 0.35

    chunk_size_chars: int = 900
    chunk_overlap_chars: int = 120
    data_dir: Path = Path("data")

    @property
    def cors_origins_list(self) -> list[str]:
        """Convert the comma-separated CORS setting into a list."""
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache

def get_settings() -> Settings:
    """Return cached settings so the app has one consistent configuration."""
    return Settings()


settings = get_settings()
