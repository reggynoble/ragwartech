from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"

# Ensure the application data directory exists before SQLite is initialized.
DATA_DIR.mkdir(parents=True, exist_ok=True)


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    app_name: str = "Portfolio AI/RAG API"
    app_version: str = "0.2.0"

    database_url: str = f"sqlite:///{DATA_DIR / 'portfolio.db'}"

    cors_origins: str = ""

    # AI configuration
    ai_provider: str = "openai"
    ai_model: str = "gpt-5.6-luna"
    embedding_model: str = "text-embedding-3-small"
    openai_api_key: str = ""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
