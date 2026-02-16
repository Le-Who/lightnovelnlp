from __future__ import annotations

from typing import List
import os

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, computed_field


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True
    )

    # Database
    DATABASE_URL: str = Field(..., description="PostgreSQL connection string")

    # Redis
    REDIS_URL: str = Field(..., description="Redis connection string")
    # Upstash REST (опционально)
    UPSTASH_REDIS_REST_URL: str | None = Field(default=None, description="Upstash REST URL")
    UPSTASH_REDIS_REST_TOKEN: str | None = Field(default=None, description="Upstash REST TOKEN")

    # Gemini API - храним как строку, парсим через computed_field
    GEMINI_API_KEYS_RAW: str = Field(..., description="Raw Gemini API keys string")
    GEMINI_API_LIMIT_PER_KEY: str = Field(default="gemini-3-flash-preview=18, gemini-flash-latest=18, gemini-2.5-flash=18", description="Daily limits per model (e.g. 'model1=100, model2=50')")
    GEMINI_API_LIMIT_THRESHOLD_PERCENT: int = Field(default=95, description="Threshold percentage for key rotation")
    GEMINI_API_COOLDOWN_HOURS: int = Field(default=24, description="Cooldown hours for used keys")
    GEMINI_API_RESET_TIMEZONE: str = Field(default="America/Los_Angeles", description="Timezone for daily limit reset (Mountain View, CA)")
    GEMINI_MAX_OUTPUT_TOKENS: int = Field(default=131072, description="Max output tokens for Gemini models")

    # Environment
    ENVIRONMENT: str = Field(default="development", description="Environment (development/production)")

    # File Upload
    MAX_UPLOAD_SIZE: int = Field(default=10 * 1024 * 1024, description="Max upload size in bytes (default 10MB)")

    # CORS - храним как строку, парсим через computed_field
    ALLOWED_ORIGINS_RAW: str = Field(
        default="http://localhost:3000,http://localhost:5173",
        description="Raw allowed CORS origins string"
    )

    @computed_field
    @property
    def GEMINI_API_KEYS(self) -> List[str]:
        """Парсит GEMINI_API_KEYS_RAW в список ключей"""
        if not self.GEMINI_API_KEYS_RAW.strip():
            return []
        return [key.strip() for key in self.GEMINI_API_KEYS_RAW.split(',') if key.strip()]

    @computed_field
    @property
    def ALLOWED_ORIGINS(self) -> List[str]:
        """Парсит ALLOWED_ORIGINS_RAW в список origins"""
        if not self.ALLOWED_ORIGINS_RAW.strip():
            return ["http://localhost:3000", "http://localhost:5173"]
        return [origin.strip() for origin in self.ALLOWED_ORIGINS_RAW.split(',') if origin.strip()]

    @computed_field
    @property
    def GEMINI_MODEL_LIMITS(self) -> dict[str, int]:
        """Парсит GEMINI_API_LIMIT_PER_KEY в словарь {model: limit}"""
        limits = {}
        if not self.GEMINI_API_LIMIT_PER_KEY:
            return limits
        
        parts = [p.strip() for p in self.GEMINI_API_LIMIT_PER_KEY.split(',') if p.strip()]
        for part in parts:
            if '=' in part:
                model, limit = part.split('=', 1)
                try:
                    limits[model.strip()] = int(limit.strip())
                except ValueError:
                    continue
        return limits



    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT.lower() == "production"

    @property
    def is_development(self) -> bool:
        return self.ENVIRONMENT.lower() == "development"


# Создаем экземпляр настроек
settings = Settings()
