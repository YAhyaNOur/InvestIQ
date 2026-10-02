# app/core/config.py
from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # App
    app_name: str = "SmartStart"
    app_env: str  = "development"
    secret_key: str = "change-me-in-production-min-32-chars!!"
    algorithm: str  = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int   = 7

    # Database
    database_url: str = "postgresql+asyncpg://postgres:admin@localhost:5432/smartstart_db"

    # Google OAuth2
    google_client_id: str     = ""
    google_client_secret: str = ""
    google_redirect_uri: str  = "http://localhost:8000/auth/google/callback"

    # Frontend
    frontend_url: str = "http://localhost:4200"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # ML Service
    ml_service_url: str = "http://localhost:8001"

    # ── N8N Webhooks ──────────────────────────────────────────────────────────
    n8n_webhook_startuper_url: str = "http://localhost:5678/webhook-test/startuper-summary"

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()