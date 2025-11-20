# app/config.py

from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration settings."""
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    app_name: str = "Food fleet"
    app_version: str
    debug: bool = False
    api_v1_prefix: str = "/api/v1"

    db_name: str
    db_user: str
    db_password: str
    db_host: str
    db_port: int = 5432
    db_echo: bool = False

    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7
    password_reset_token_expire_minutes: int = 15

    two_fa_issuer: str = "Food Fleet"

    aws_region: Optional[str] = None
    aws_access_key_id: Optional[str] = None
    aws_secret_access_key: Optional[str] = None

    ses_sender_email: Optional[str] = None
    ses_sender_name: Optional[str] = None

    sns_sms_type: str = "Transactional"

    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_password: Optional[str] = None

    allowed_hosts: str = "*"

    @property
    def db_url(self) -> str:
        """Construct the database URL from individual components."""
        return (
            f"postgresql+asyncpg://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )
    
    @property
    def redis_url(self) -> str:
        """Construct the Redis URL from individual components."""
        if self.redis_password:
            return f"redis://:{self.redis_password}@{self.redis_host}:{self.redis_port}"
        return f"redis://{self.redis_host}:{self.redis_port}"
    
    @property
    def celery_broker_url(self) -> str:
        """Construct the Celery broker URL using Redis."""
        return f"{self.redis_url}/0"
    
    @property
    def celery_result_backend(self) -> str:
        """Construct the Celery result backend URL using Redis."""
        return f"{self.redis_url}/1"
    
    @property
    def cache_manager_url(self) -> str:
        """Construct the cache manager URL using Redis."""
        return f"{self.redis_url}/2"
    
    @property
    def cors_origins(self) -> list[str]:
        """Parse the allowed hosts into a list for CORS configuration."""
        return [origin.strip() for origin in self.allowed_hosts.split(",")]
    

settings = Settings()
