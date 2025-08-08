from __future__ import annotations

import json
from typing import Any, Optional

import redis

from app.core.config import settings


class CacheService:
    def __init__(self, url: str | None = None) -> None:
        self._client = redis.Redis.from_url(url or settings.redis_url, decode_responses=True)

    def set_json(self, key: str, value: Any, ttl_seconds: Optional[int] = None) -> None:
        payload = json.dumps(value, ensure_ascii=False)
        if ttl_seconds is not None:
            self._client.setex(key, ttl_seconds, payload)
        else:
            self._client.set(key, payload)

    def get_json(self, key: str) -> Any | None:
        raw = self._client.get(key)
        if raw is None:
            return None
        return json.loads(raw)

    def incr(self, key: str, amount: int = 1) -> int:
        return int(self._client.incrby(key, amount))

    def get_client(self) -> redis.Redis:
        return self._client


cache_service = CacheService()
