from __future__ import annotations

import datetime as dt
from typing import List, Optional

import google.generativeai as genai

from app.core.config import settings
from app.services.cache_service import cache_service


class KeyRotator:
    def __init__(self, api_keys: List[str], daily_limit: int, threshold_percent: int) -> None:
        self.api_keys = api_keys
        self.daily_limit = daily_limit
        self.threshold = int(daily_limit * (threshold_percent / 100))
        self.redis = cache_service.get_client()

    @property
    def _day_key(self) -> str:
        return dt.datetime.utcnow().strftime("%Y-%m-%d")

    def _key_state_hash(self, key: str) -> str:
        return f"gemini:key:{key}:state:{self._day_key}"

    def _ensure_day_reset(self) -> None:
        # If stored day != today, reset counters for all keys
        day_marker_key = "gemini:day_marker"
        stored = self.redis.get(day_marker_key)
        if stored != self._day_key:
            pipe = self.redis.pipeline()
            for key in self.api_keys:
                hkey = self._key_state_hash(key)
                pipe.hset(hkey, mapping={"used": 0, "cooldown": 0})
                pipe.expireat(hkey, int(dt.datetime.utcnow().replace(hour=23, minute=59, second=59, microsecond=0).timestamp()))
            pipe.set(day_marker_key, self._day_key)
            pipe.execute()

    def _get_state(self, key: str) -> tuple[int, int]:
        hkey = self._key_state_hash(key)
        used = int(self.redis.hget(hkey, "used") or 0)
        cooldown = int(self.redis.hget(hkey, "cooldown") or 0)
        return used, cooldown

    def _set_state(self, key: str, *, used: Optional[int] = None, cooldown: Optional[int] = None) -> None:
        hkey = self._key_state_hash(key)
        mapping = {}
        if used is not None:
            mapping["used"] = int(used)
        if cooldown is not None:
            mapping["cooldown"] = int(cooldown)
        if mapping:
            self.redis.hset(hkey, mapping=mapping)

    def acquire_key(self) -> str:
        if not self.api_keys:
            raise RuntimeError("No Gemini API keys configured")

        self._ensure_day_reset()

        # Prefer the first key below threshold and not on cooldown
        candidate: Optional[str] = None
        lowest_used = 10**12
        for key in self.api_keys:
            used, cooldown = self._get_state(key)
            if cooldown:
                continue
            if used < self.threshold:
                return key
            # Track the lowest used non-cooldown key as fallback
            if used < lowest_used:
                lowest_used = used
                candidate = key

        # If no key is below threshold, use the least used non-cooldown key if still under absolute limit
        if candidate is not None:
            used, _ = self._get_state(candidate)
            if used < self.daily_limit:
                return candidate

        raise RuntimeError("All Gemini API keys are exhausted or on cooldown for today")

    def increment_usage(self, key: str, amount: int = 1) -> None:
        self._ensure_day_reset()
        used, _ = self._get_state(key)
        new_used = used + amount
        self._set_state(key, used=new_used)
        if new_used >= self.threshold:
            # Put key into cooldown (until day reset)
            self._set_state(key, cooldown=1)


class GeminiClient:
    def __init__(self) -> None:
        self.rotator = KeyRotator(
            api_keys=settings.gemini_api_keys,
            daily_limit=settings.gemini_daily_limit,
            threshold_percent=settings.gemini_rotation_threshold_percent,
        )
        self.model_name = settings.gemini_model

    def _configure(self) -> str:
        key = self.rotator.acquire_key()
        genai.configure(api_key=key)
        return key

    def get_model(self):
        key = self._configure()
        try:
            model = genai.GenerativeModel(self.model_name)
            return key, model
        except Exception:
            # In case of an error also bump usage to avoid hot-looping a bad key
            self.rotator.increment_usage(key)
            raise

    def complete(self, prompt: str) -> str:
        key, model = self.get_model()
        try:
            response = model.generate_content(prompt)
            self.rotator.increment_usage(key)
            return response.text or ""
        except Exception:
            self.rotator.increment_usage(key)
            raise


gemini_client = GeminiClient()
