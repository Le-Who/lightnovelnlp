from __future__ import annotations

from typing import List
import os

from pydantic_settings import BaseSettings
from pydantic import Field, field_validator


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = Field(..., description="PostgreSQL connection string")

    # Redis
    REDIS_URL: str = Field(..., description="Redis connection string")

    # Gemini API
    GEMINI_API_KEYS: List[str] = Field(default_factory=list, description="List of Gemini API keys")
    GEMINI_API_LIMIT_PER_KEY: int = Field(default=1000, description="Daily limit per API key")
    GEMINI_API_LIMIT_THRESHOLD_PERCENT: int = Field(default=95, description="Threshold percentage for key rotation")
    GEMINI_API_COOLDOWN_HOURS: int = Field(default=24, description="Cooldown hours for used keys")
    GEMINI_API_RESET_TIMEZONE: str = Field(default="America/Los_Angeles", description="Timezone for daily limit reset (Mountain View, CA)")

    # Environment
    ENVIRONMENT: str = Field(default="development", description="Environment (development/production)")

    # CORS
    ALLOWED_ORIGINS: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:5173"],
        description="Allowed CORS origins"
    )

    @field_validator('GEMINI_API_KEYS', mode='before')
    @classmethod
    def parse_gemini_keys(cls, v):
        if isinstance(v, str):
            if not v.strip():
                return []
            # Разделяем по запятой и убираем пробелы
            return [key.strip() for key in v.split(',') if key.strip()]
        return v

    @field_validator('ALLOWED_ORIGINS', mode='before')
    @classmethod
    def parse_allowed_origins(cls, v):
        if isinstance(v, str):
            if not v.strip():
                return ["http://localhost:3000", "http://localhost:5173"]
            # Разделяем по запятой и убираем пробелы
            return [origin.strip() for origin in v.split(',') if origin.strip()]
        return v

    class Config:
        env_file = ".env"
        case_sensitive = True

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT.lower() == "production"

    @property
    def is_development(self) -> bool:
        return self.ENVIRONMENT.lower() == "development"


# Создаем экземпляр настроек
settings = Settings()
