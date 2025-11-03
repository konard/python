"""Application configuration using Pydantic settings"""
from typing import Optional, List
from pydantic import Field, field_validator
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
    secret_key: str = Field(default="dev-secret-key-change-in-production", alias="SECRET_KEY")

    # Database (SQLite for MVP, easily upgradable to PostgreSQL)
    database_url: str = Field(default="sqlite:///./youtube_analytics.db", alias="DATABASE_URL")

    # YouTube API - Multiple keys support
    # Can be comma-separated list: "key1,key2,key3"
    youtube_api_keys: str = Field(..., alias="YOUTUBE_API_KEYS")
    youtube_api_quota_limit: int = Field(default=10000, alias="YOUTUBE_API_QUOTA_LIMIT")

    # Cache TTL (seconds) - using in-memory cache for MVP
    cache_ttl_channel: int = Field(default=3600, alias="CACHE_TTL_CHANNEL")  # 1 hour
    cache_ttl_video: int = Field(default=3600, alias="CACHE_TTL_VIDEO")  # 1 hour
    cache_ttl_stats: int = Field(default=21600, alias="CACHE_TTL_STATS")  # 6 hours

    # Snapshot collection schedule (cron format)
    snapshot_schedule_cron: str = Field(default="0 2 * * *", alias="SNAPSHOT_SCHEDULE_CRON")  # 2 AM daily

    # Logging
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    # CORS
    cors_origins: list[str] = Field(
        default=["http://localhost:3000", "http://localhost:5173", "http://localhost:8000"],
        alias="CORS_ORIGINS"
    )

    @property
    def database_url_str(self) -> str:
        """Get database URL as string"""
        return self.database_url

    @property
    def youtube_api_keys_list(self) -> List[str]:
        """Parse comma-separated API keys"""
        return [key.strip() for key in self.youtube_api_keys.split(",") if key.strip()]


# Global settings instance
settings = Settings()
