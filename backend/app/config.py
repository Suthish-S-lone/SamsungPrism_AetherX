"""Configuration settings for SmartGuide.

Loads environment variables for future LLM provider, embeddings, caching,
and retrieval thresholds without hardcoding secrets.
"""

from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

# Base repository directory
ROOT_DIR = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    """Application configuration settings."""

    APP_NAME: str = "SmartGuide Troubleshooting Engine"
    APP_VERSION: str = "0.1.0"
    APP_ENV: str = "development"
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # Future LLM Provider Configuration (Phase 3+)
    LLM_PROVIDER: str = "gemini"
    LLM_API_KEY: Optional[str] = None
    LLM_MODEL: str = "gemini-1.5-flash"
    LLM_TEMPERATURE: float = 0.2
    LLM_MAX_TOKENS: int = 2048

    # Embedding & Vector Retrieval Configuration (Phase 2.75)
    RETRIEVAL_VECTOR_MODE: str = "sentence_transformer"  # "sentence_transformer" or "tfidf"
    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"
    EMBEDDING_DIMENSION: int = 384

    # Future Retrieval & Semantic Cache Configuration (Phase 2+)
    SIMILARITY_THRESHOLD: float = 0.70
    CACHE_BACKEND: str = "memory"
    CACHE_TTL_SECONDS: int = 3600
    CACHE_SIMILARITY_THRESHOLD: float = 0.92

    # Development Dataset Directory
    DATA_DIR: Path = Field(default_factory=lambda: ROOT_DIR / "data" / "development")

    model_config = SettingsConfigDict(
        env_file=str(ROOT_DIR / ".env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


settings = Settings()
