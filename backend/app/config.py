"""
Application configuration management using Pydantic Settings.
All configuration is loaded from environment variables.
"""
from typing import Any, List
from pydantic import Field, field_validator, PostgresDsn, RedisDsn
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    APP_NAME: str = "YouTube Analytics"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "production"

    # API
    API_V1_PREFIX: str = "/api/v1"
    BACKEND_CORS_ORIGINS: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:8000"]
    )

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Any) -> List[str]:
        if isinstance(v, str):
            if v.startswith("["):
                import json
                return json.loads(v)
            return [i.strip() for i in v.split(",")]
        return v

    # Database
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str = "youtube_analytics"
    POSTGRES_PASSWORD: str = ""
    POSTGRES_DB: str = "youtube_analytics"
    DATABASE_URL: str | None = None

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def assemble_db_connection(cls, v: str | None, info: Any) -> str:
        if v:
            return v

        data = info.data
        return str(
            PostgresDsn.build(
                scheme="postgresql+asyncpg",
                username=data.get("POSTGRES_USER"),
                password=data.get("POSTGRES_PASSWORD"),
                host=data.get("POSTGRES_SERVER"),
                port=data.get("POSTGRES_PORT"),
                path=data.get("POSTGRES_DB"),
            )
        )

    # Redis
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_URL: str | None = None

    @field_validator("REDIS_URL", mode="before")
    @classmethod
    def assemble_redis_connection(cls, v: str | None, info: Any) -> str:
        if v:
            return v

        data = info.data
        return f"redis://{data.get('REDIS_HOST')}:{data.get('REDIS_PORT')}/{data.get('REDIS_DB')}"

    # Celery
    CELERY_BROKER_URL: str | None = None
    CELERY_RESULT_BACKEND: str | None = None

    @field_validator("CELERY_BROKER_URL", mode="before")
    @classmethod
    def assemble_celery_broker(cls, v: str | None, info: Any) -> str:
        if v:
            return v
        return info.data.get("REDIS_URL", "redis://localhost:6379/0")

    @field_validator("CELERY_RESULT_BACKEND", mode="before")
    @classmethod
    def assemble_celery_backend(cls, v: str | None, info: Any) -> str:
        if v:
            return v
        return info.data.get("REDIS_URL", "redis://localhost:6379/0")

    # YouTube Data API v3
    YOUTUBE_API_KEY: str = ""
    YOUTUBE_API_QUOTA_LIMIT: int = 10000
    YOUTUBE_API_QUOTA_RESET_HOUR: int = 0  # 0-23 in Pacific Time

    # Rate Limiting
    YOUTUBE_API_REQUESTS_PER_SECOND: int = 100
    YOUTUBE_API_REQUESTS_PER_DAY: int = 10000

    # Cache TTL (seconds)
    CACHE_TTL_CHANNEL_DETAILS: int = 3600  # 1 hour
    CACHE_TTL_VIDEO_DETAILS: int = 3600  # 1 hour
    CACHE_TTL_VIDEO_STATS: int = 1800  # 30 minutes
    CACHE_TTL_CHANNEL_STATS: int = 1800  # 30 minutes
    CACHE_TTL_COMMENTS: int = 7200  # 2 hours

    # Task Schedule
    UPDATE_STATS_CRON_HOUR: int = 2  # Hour to run daily stats update (0-23)
    CHECK_ALERTS_INTERVAL_MINUTES: int = 30  # How often to check alerts

    # Pagination
    DEFAULT_PAGE_SIZE: int = 20
    MAX_PAGE_SIZE: int = 100

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"  # json or text

    # Security
    SECRET_KEY: str = "please-change-this-secret-key-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Future features
    ENABLE_AI_FEATURES: bool = False
    AI_API_KEY: str = ""
    AI_MODEL_NAME: str = ""


# Global settings instance
settings = Settings()
