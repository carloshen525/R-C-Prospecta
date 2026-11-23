from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional
import os

class Settings(BaseSettings):
    # App
    ENVIRONMENT: str = "development"
    APP_NAME: str = "Prospect AI"
    SECRET_KEY: str = "prospect_ai_super_secret_jwt_key_change_in_production_32chars_min"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440

    # PostgreSQL
    DATABASE_URL: str = "postgresql://prospect_user:prospect_secret_pass@localhost:5432/prospect_ai_db"

    # Redis & Celery
    REDIS_URL: str = "redis://localhost:6379/0"
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/1"

    # Regras de Campanha e Envio
    DAILY_CONTACT_LIMIT: int = 20
    TIMEZONE: str = "America/Sao_Paulo"
    SENDING_START_HOUR: int = 7
    SENDING_START_MINUTE: int = 0
    SENDING_END_HOUR: int = 18
    SENDING_END_MINUTE: int = 30
    MIN_INTERVAL_BETWEEN_CONTACTS_SEC: int = 180
    MAX_INTERVAL_BETWEEN_CONTACTS_SEC: int = 360
    FOLLOWUP_1_DELAY_HOURS: int = 24
    FOLLOWUP_2_DELAY_HOURS: int = 48

    # Evolution API
    EVOLUTION_API_URL: Optional[str] = ""
    EVOLUTION_API_KEY: Optional[str] = ""
    EVOLUTION_INSTANCE_NAME: Optional[str] = ""
    EVOLUTION_WEBHOOK_SECRET: Optional[str] = ""

    # Google Maps / Places API
    GOOGLE_MAPS_API_KEY: Optional[str] = ""

    # IA Providers
    DEFAULT_AI_PROVIDER: str = "gemini"
    FALLBACK_AI_PROVIDER: str = "groq"
    OPENAI_API_KEY: Optional[str] = ""
    OPENAI_MODEL: str = "gpt-4o-mini"
    GROQ_API_KEY: Optional[str] = ""
    GROQ_MODEL: str = "llama-3.3-70b-versatile"
    GEMINI_API_KEY: Optional[str] = ""
    GEMINI_MODEL: str = "gemini-1.5-flash"

    # CORS
    BACKEND_CORS_ORIGINS: list[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
