"""Application configuration using Pydantic settings"""
from typing import Optional
from pydantic import PostgresDsn, RedisDsn, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    # Application
    app_name: str = "YouTube Analytics"
    environment: str = Field(default="development", alias="ENVIRONMENT")
    debug: bool = Field(default=False, alias="DEBUG")
    secret_key: str = Field(..., alias="SECRET_KEY")

    # Database
    database_url: PostgresDsn = Field(..., alias="DATABASE_URL")

    # Redis
    redis_url: RedisDsn = Field(..., alias="REDIS_URL")

    # Celery
    celery_broker_url: Optional[str] = Field(default=None, alias="CELERY_BROKER_URL")
    celery_result_backend: Optional[str] = Field(default=None, alias="CELERY_RESULT_BACKEND")

    # YouTube API
    youtube_api_key: str = Field(..., alias="YOUTUBE_API_KEY")
    youtube_api_quota_limit: int = Field(default=10000, alias="YOUTUBE_API_QUOTA_LIMIT")

    # Cache TTL (seconds)
    cache_ttl_channel: int = Field(default=3600, alias="CACHE_TTL_CHANNEL")  # 1 hour
    cache_ttl_video: int = Field(default=3600, alias="CACHE_TTL_VIDEO")  # 1 hour
    cache_ttl_stats: int = Field(default=21600, alias="CACHE_TTL_STATS")  # 6 hours

    # Snapshot collection
    snapshot_default_schedule: str = Field(default="0 2 * * *", alias="SNAPSHOT_DEFAULT_SCHEDULE")  # 2 AM daily

    # Logging
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    # CORS
    cors_origins: list[str] = Field(
        default=["http://localhost:3000", "http://localhost:8000"],
        alias="CORS_ORIGINS"
    )

    @property
    def celery_broker(self) -> str:
        """Get Celery broker URL, fallback to Redis URL"""
        return self.celery_broker_url or str(self.redis_url)

    @property
    def celery_backend(self) -> str:
        """Get Celery result backend URL, fallback to Redis URL"""
        return self.celery_result_backend or str(self.redis_url)

    @property
    def database_url_str(self) -> str:
        """Get database URL as string"""
        return str(self.database_url)


# Global settings instance
settings = Settings()
