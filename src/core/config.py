# src/core/config.py

"""
Core configuration using Pydantic Settings
Supports multiple environments with proper validation.
"""

from functools import lru_cache
from typing import Any, Optional

from pydantic import Field, PostgresDsn, RedisDsn, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with environment-based configuration."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "Restaurant Fleet Platform"
    app_version: str = "1.0.0"
    environment: str = "development" # Options: development, staging, production
    debug: bool = False
    api_v1_prefix: str = "/api/v1"

    host: str = "0.0.0.0"
    port: int = 8000
    workers: int = 1
    reload: bool = True

    db_host: str = "localhost"
    db_port: int = 5432
    db_name: str
    db_user: str
    db_password: str
    
    db_pool_size: int = 20
    db_max_overflow: int = 0
    db_pool_timeout: int = 30
    db_pool_recycle: int = 3600
    db_echo: bool = False

    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_password: Optional[str] = None

    redis_pool_max_connections: int = 10
    redis_socket_timeout: int = 5
    redis_socket_connect_timeout: int = 5

    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    session_expire_seconds: int = 86400

    cookie_name: str = "access_token"
    cookie_httponly: bool = True
    cookie_secure: bool = False
    cookie_samesite: str = "lax"
    cookie_max_age: int = 1800

    allowed_origins: str = "*"
    cors_allow_credentials: bool = True
    cors_allow_methods: list[str] = ["*"]
    cors_allow_headers: list[str] = ["*"]

    log_level: str = "INFO"
    log_format: str = "json"
    log_file_path: Optional[str] = None
    log_rotation: str = "1 day"
    log_retention: str = "30 days"

    rate_limit_enabled: bool = True
    rate_limit_per_minute: int = 60

    default_page_size: int = 20
    max_page_size: int = 100

    max_upload_size: int = 10485760
    upload_dir: str = "uploads"
    allowed_extensions: str = "jpg,jpeg,png,gif,pdf,docx,xlsx"

    dunzo_api_key: Optional[str] = None
    dunzo_api_url: str = "https://api.dunzo.com"

    openai_api_key: Optional[str] = None

    email_from: str = "noreply@restaurant-fleet.com"

    enable_ai_recommendations: bool = True
    enable_external_delivery: bool = True

    aws_access_key_id: str
    aws_secret_access_key: str
    aws_region: str = "ap-south-1"

    s3_bucket_name: str

    @property
    def db_url(self) -> str:
        """Construct the database URL."""
        return f"postgresql+asyncpg://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"
    
    @property
    def redis_url(self) -> str:
        """Construct the Redis URL."""
        if self.redis_password:
            return f"redis://:{self.redis_password}@{self.redis_host}:{self.redis_port}"
        return f"redis://{self.redis_host}:{self.redis_port}"
    
    @property
    def cache_url(self) -> str:
        """Construct the cache URL (same as Redis URL)."""
        return self.redis_url + "/0"
    
    @property
    def celery_broker_url(self) -> str:
        """Construct the Celery broker URL (same as Redis URL)."""
        return self.redis_url + "/1"
    
    @property
    def celery_backend_url(self) -> str:
        """Construct the Celery backend URL (same as Redis URL)."""
        return self.redis_url + "/2"
    
    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.environment.lower() == "production"
    
    @property
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.environment.lower() == "development"
    
    @property
    def is_staging(self) -> bool:
        """Check if running in staging environment."""
        return self.environment.lower() == "staging"
    
    @property
    def cors_origins(self) -> list[str]:
        """Get list of allowed CORS origins."""
        if self.allowed_origins == "*":
            return ["*"]
        return [origin.strip() for origin in self.allowed_origins.split(",")]
    

@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance
    Use lru_cache to avoid reading .env file multiple times
    """
    return Settings()


# Global settings instance
settings = get_settings()
