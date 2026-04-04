from __future__ import annotations

from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, computed_field


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True)

    # Database
    DATABASE_URL: str = Field(..., description="PostgreSQL connection string")

    # Redis
    REDIS_URL: str = Field(..., description="Redis connection string")
    # Upstash REST (опционально)
    UPSTASH_REDIS_REST_URL: str | None = Field(
        default=None, description="Upstash REST URL"
    )
    UPSTASH_REDIS_REST_TOKEN: str | None = Field(
        default=None, description="Upstash REST TOKEN"
    )

    # ──────────────────────────────────────────────
    # Gemini API Keys & Rotation
    # ──────────────────────────────────────────────
    GEMINI_API_KEYS_RAW: str = Field(
        ...,
        description="Comma-separated Gemini API keys (each key = separate GCP project)",
    )
    GEMINI_API_RESET_TIMEZONE: str = Field(
        default="America/Los_Angeles",
        description="Timezone for daily RPD reset (Mountain View, CA)",
    )
    GEMINI_API_COOLDOWN_MINUTES: int = Field(
        default=5, description="Soft cooldown minutes for a key after 429 from Google"
    )

    # ──────────────────────────────────────────────
    # Per-task Model Selection (defaults, overridable per-project in DB)
    # ──────────────────────────────────────────────
    GEMINI_MODEL_EXTRACTION: str = Field(
        default="gemini-3.1-flash-lite-preview", description="Model for term extraction"
    )
    GEMINI_MODEL_TRANSLATION: str = Field(
        default="gemini-3-flash-preview", description="Model for translation"
    )
    GEMINI_MODEL_SUMMARIZATION: str = Field(
        default="gemini-3.1-flash-lite-preview",
        description="Model for context summarization",
    )
    GEMINI_MODEL_RELATIONSHIPS: str = Field(
        default="gemini-3.1-flash-lite-preview",
        description="Model for relationship analysis",
    )
    GEMINI_MODEL_EMBEDDING: str = Field(
        default="gemini-embedding-2-preview", description="Model for embeddings"
    )

    # Fallback model chain (comma-separated, used when primary model fails)
    GEMINI_FALLBACK_MODELS: str = Field(
        default="gemini-2.5-flash,gemini-flash-latest",
        description="Comma-separated fallback model chain",
    )

    # ──────────────────────────────────────────────
    # Per-task ThinkingLevel (Gemini 3.x: thinkingLevel, Gemini 2.5.x: auto-mapped to thinkingBudget)
    # Values: minimal, low, medium, high
    # ──────────────────────────────────────────────
    GEMINI_THINKING_EXTRACTION: str = Field(
        default="medium", description="Thinking level for extraction tasks"
    )
    GEMINI_THINKING_TRANSLATION: str = Field(
        default="high", description="Thinking level for translation tasks"
    )
    GEMINI_THINKING_SUMMARIZATION: str = Field(
        default="medium", description="Thinking level for summarization"
    )
    GEMINI_THINKING_RELATIONSHIPS: str = Field(
        default="medium", description="Thinking level for relationship analysis"
    )

    # ──────────────────────────────────────────────
    # Per-model Rate Limits (per key, since each key = separate GCP project)
    # Format: "model1=N, model2=M"
    # ──────────────────────────────────────────────
    GEMINI_RPM_LIMITS: str = Field(
        default="gemini-3-flash-preview=10, gemini-3.1-flash-lite-preview=15, gemini-2.5-flash=10, gemini-flash-latest=10",
        description="RPM (requests per minute) limits per model per key",
    )
    GEMINI_RPD_LIMITS: str = Field(
        default="gemini-3-flash-preview=500, gemini-3.1-flash-lite-preview=1000, gemini-2.5-flash=500, gemini-flash-latest=500",
        description="RPD (requests per day) limits per model per key",
    )

    # ──────────────────────────────────────────────
    # Per-task max_output_tokens defaults
    # ──────────────────────────────────────────────
    GEMINI_MAX_TOKENS_EXTRACTION: int = Field(
        default=8192, description="Max output tokens for extraction"
    )
    GEMINI_MAX_TOKENS_TRANSLATION: int = Field(
        default=65536,
        description="Max output tokens for translation (Gemini 3 Flash limit)",
    )
    GEMINI_MAX_TOKENS_SUMMARIZATION: int = Field(
        default=2048, description="Max output tokens for summarization"
    )
    GEMINI_MAX_TOKENS_RELATIONSHIPS: int = Field(
        default=4096, description="Max output tokens for relationship analysis"
    )
    GEMINI_MAX_TOKENS_DEFAULT: int = Field(
        default=8192, description="Max output tokens fallback"
    )

    # ──────────────────────────────────────────────
    # Embedding Settings
    # ──────────────────────────────────────────────
    EMBEDDING_SIMILARITY_THRESHOLD: float = Field(
        default=0.75,
        description="Global default embedding similarity threshold (overridable per-project)",
    )

    # Environment
    ENVIRONMENT: str = Field(
        default="development", description="Environment (development/production)"
    )

    # CORS - храним как строку, парсим через computed_field
    ALLOWED_ORIGINS_RAW: str = Field(
        default="http://localhost:3000,http://localhost:5173",
        description="Raw allowed CORS origins string",
    )

    # ──────────────────────────────────────────────
    # Computed Fields
    # ──────────────────────────────────────────────

    @computed_field
    @property
    def GEMINI_API_KEYS(self) -> List[str]:
        """Парсит GEMINI_API_KEYS_RAW в список ключей."""
        if not self.GEMINI_API_KEYS_RAW.strip():
            return []
        return [
            key.strip() for key in self.GEMINI_API_KEYS_RAW.split(",") if key.strip()
        ]

    @computed_field
    @property
    def ALLOWED_ORIGINS(self) -> List[str]:
        """Парсит ALLOWED_ORIGINS_RAW в список origins."""
        if not self.ALLOWED_ORIGINS_RAW.strip():
            return ["http://localhost:3000", "http://localhost:5173"]
        return [
            origin.strip()
            for origin in self.ALLOWED_ORIGINS_RAW.split(",")
            if origin.strip()
        ]

    @computed_field
    @property
    def GEMINI_RPM_LIMITS_MAP(self) -> dict[str, int]:
        """Парсит GEMINI_RPM_LIMITS в словарь {model: rpm_limit}."""
        return self._parse_limits_string(self.GEMINI_RPM_LIMITS)

    @computed_field
    @property
    def GEMINI_RPD_LIMITS_MAP(self) -> dict[str, int]:
        """Парсит GEMINI_RPD_LIMITS в словарь {model: rpd_limit}."""
        return self._parse_limits_string(self.GEMINI_RPD_LIMITS)

    @computed_field
    @property
    def GEMINI_FALLBACK_MODELS_LIST(self) -> List[str]:
        """Парсит GEMINI_FALLBACK_MODELS в список моделей."""
        if not self.GEMINI_FALLBACK_MODELS.strip():
            return []
        return [m.strip() for m in self.GEMINI_FALLBACK_MODELS.split(",") if m.strip()]

    def _parse_limits_string(self, raw: str) -> dict[str, int]:
        """Общий парсер строки 'model1=N, model2=M' → dict."""
        limits: dict[str, int] = {}
        if not raw:
            return limits
        for part in raw.split(","):
            part = part.strip()
            if "=" in part:
                model, value = part.split("=", 1)
                try:
                    limits[model.strip()] = int(value.strip())
                except ValueError:
                    continue
        return limits

    def get_model_for_task(self, task_type: str) -> str:
        """Возвращает модель по умолчанию для задачи."""
        mapping = {
            "extraction": self.GEMINI_MODEL_EXTRACTION,
            "translation": self.GEMINI_MODEL_TRANSLATION,
            "summarization": self.GEMINI_MODEL_SUMMARIZATION,
            "relationships": self.GEMINI_MODEL_RELATIONSHIPS,
            "embedding": self.GEMINI_MODEL_EMBEDDING,
        }
        return mapping.get(task_type, self.GEMINI_MODEL_EXTRACTION)

    def get_thinking_for_task(self, task_type: str) -> str | None:
        """Возвращает thinkingLevel по умолчанию для задачи."""
        mapping = {
            "extraction": self.GEMINI_THINKING_EXTRACTION,
            "translation": self.GEMINI_THINKING_TRANSLATION,
            "summarization": self.GEMINI_THINKING_SUMMARIZATION,
            "relationships": self.GEMINI_THINKING_RELATIONSHIPS,
        }
        return mapping.get(task_type)

    def get_max_tokens_for_task(self, task_type: str) -> int:
        """Возвращает max_output_tokens по умолчанию для задачи."""
        mapping = {
            "extraction": self.GEMINI_MAX_TOKENS_EXTRACTION,
            "translation": self.GEMINI_MAX_TOKENS_TRANSLATION,
            "summarization": self.GEMINI_MAX_TOKENS_SUMMARIZATION,
            "relationships": self.GEMINI_MAX_TOKENS_RELATIONSHIPS,
        }
        return mapping.get(task_type, self.GEMINI_MAX_TOKENS_DEFAULT)

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT.lower() == "production"

    @property
    def is_development(self) -> bool:
        return self.ENVIRONMENT.lower() == "development"


# Создаем экземпляр настроек
settings = Settings()
