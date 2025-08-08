import os
from typing import List

class Settings:
    def __init__(self) -> None:
        self.database_url: str = os.getenv(
            "DATABASE_URL", "postgresql+psycopg2://postgres:postgres@postgres:5432/ranobe"
        )
        self.redis_url: str = os.getenv("REDIS_URL", "redis://redis:6379/0")

        allowed = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173").split(",")
        self.allowed_origins: List[str] = [o.strip() for o in allowed if o.strip()]

        self.gemini_api_keys: List[str] = [
            k.strip() for k in os.getenv("GEMINI_API_KEYS", "").split(",") if k.strip()
        ]
        self.gemini_model: str = os.getenv("GEMINI_MODEL", "gemini-2.5-pro")
        self.gemini_daily_limit: int = int(os.getenv("GEMINI_DAILY_LIMIT", "1000"))
        self.gemini_rotation_threshold_percent: int = int(
            os.getenv("GEMINI_ROTATION_THRESHOLD_PERCENT", "95")
        )

settings = Settings()
