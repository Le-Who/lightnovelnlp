from __future__ import annotations

import json
import logging
import time
import warnings
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any

from google import genai
from google.genai import types
import pytz

# Suppress Pydantic warnings from google-genai types
warnings.filterwarnings("ignore", category=UserWarning, module="pydantic")
logging.getLogger("google.genai.types").setLevel(logging.ERROR)
logging.getLogger("google_genai").setLevel(logging.ERROR)
# Additional suppression for the specific path observed in logs
warnings.filterwarnings("ignore", message=".*shadows an attribute.*", category=UserWarning)

logger = logging.getLogger(__name__)

from app.core.config import settings
from app.services.cache_service import cache_service


class GeminiClient:
    def __init__(self):
        self.api_keys = settings.GEMINI_API_KEYS
        self.model_limits = settings.GEMINI_MODEL_LIMITS
        self.threshold_percent = settings.GEMINI_API_LIMIT_THRESHOLD_PERCENT
        self.cooldown_hours = settings.GEMINI_API_COOLDOWN_HOURS
        self.reset_timezone = pytz.timezone(settings.GEMINI_API_RESET_TIMEZONE)
        self.current_key_index = 0
        # Глобальный минутный лимит (10 запросов/мин по всем ключам)
        self.per_minute_limit = 10
        self.models = ["gemini-3-flash-preview", "gemini-flash-latest", "gemini-2.5-flash"]  # Primary -> Fallback

        if not self.api_keys:
            raise ValueError("No Gemini API keys provided")

        # Инициализируем первый клиент
        self._set_current_key()

    def _set_current_key(self):
        """Устанавливает текущий API ключ и создает клиент."""
        if not self.api_keys:
            raise ValueError("No API keys available")

        self.client = genai.Client(api_key=self.api_keys[self.current_key_index])

    def _get_reset_date(self) -> str:
        """Получает дату сброса лимитов в формате YYYY-MM-DD по времени Mountain View."""
        now_mv = datetime.now(self.reset_timezone)
        return now_mv.strftime("%Y-%m-%d")

    def _get_key_usage_key(self, key: str, model_name: str) -> str:
        """Генерирует ключ для хранения статистики использования конкретной модели."""
        reset_date = self._get_reset_date()
        return f"gemini_usage:{key}:{model_name}:{reset_date}"

    def _get_key_cooldown_key(self, key: str) -> str:
        """Генерирует ключ для хранения времени кулдауна."""
        return f"gemini_cooldown:{key}"

    def _is_key_in_cooldown(self, key: str) -> bool:
        """Проверяет, находится ли ключ в кулдауне."""
        cooldown_key = self._get_key_cooldown_key(key)
        cooldown_until = cache_service.get(cooldown_key)

        if not cooldown_until:
            return False

        try:
            cooldown_time = datetime.fromisoformat(cooldown_until)
        except Exception:
            # Непредвиденный формат – считаем, что нет кулдауна
            return False

        # Сравниваем осознанно: приводим текущее время к той же таймзоне, что и cooldown_time
        now_dt = datetime.now(cooldown_time.tzinfo) if cooldown_time.tzinfo else datetime.now(self.reset_timezone)
        return now_dt < cooldown_time

    def _get_key_usage(self, key: str, model_name: str) -> int:
        """Получает количество использований ключа для конкретной модели за текущий день."""
        usage_key = self._get_key_usage_key(key, model_name)
        return cache_service.get(usage_key) or 0

    def _increment_key_usage(self, key: str, model_name: str):
        """Увеличивает счетчик использований ключа для конкретной модели."""
        usage_key = self._get_key_usage_key(key, model_name)
        current_usage = self._get_key_usage(key, model_name)
        
        # Рассчитываем TTL до следующего сброса
        now_mv = datetime.now(self.reset_timezone)
        tomorrow_mv = now_mv.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
        ttl_seconds = int((tomorrow_mv - now_mv).total_seconds())
        
        cache_service.set(usage_key, current_usage + 1, ttl=ttl_seconds)

    def _put_key_in_cooldown(self, key: str):
        """Помещает ключ в кулдаун до следующего сброса лимитов."""
        cooldown_key = self._get_key_cooldown_key(key)
        
        # Рассчитываем время до следующего сброса
        now_mv = datetime.now(self.reset_timezone)
        tomorrow_mv = now_mv.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
        cooldown_until = tomorrow_mv.isoformat()
        
        # TTL до следующего сброса + 1 час для безопасности
        ttl_seconds = int((tomorrow_mv - now_mv).total_seconds()) + 3600
        
        cache_service.set(cooldown_key, cooldown_until, ttl=ttl_seconds)

    def _is_model_at_limit(self, key: str, model_name: str) -> bool:
        """Проверяет, достигнут ли лимит для конкретной модели на этом ключе."""
        limit = self.model_limits.get(model_name, 0)
        if limit <= 0:
            return False  # Нет лимита или некорректно задан
            
        usage = self._get_key_usage(key, model_name)
        threshold = int(limit * self.threshold_percent / 100)
        return usage >= threshold

    def _find_available_key(self, model_name: str) -> str | None:
        """Находит доступный ключ для использования конкретной модели."""
        for i, key in enumerate(self.api_keys):
            if not self._is_key_in_cooldown(key):
                if not self._is_model_at_limit(key, model_name):
                    self.current_key_index = i
                    return key
        return None

    def _rotate_key(self, model_name: str):
        """Переключается на следующий доступный ключ для данной модели."""
        available_key = self._find_available_key(model_name)

        if not available_key:
            # Если для этой модели нет ключей, возможно они есть для других (но тут мы застряли)
            raise Exception(f"No available API keys for model {model_name}. All keys are either in cooldown or at limit.")

        self._set_current_key()

    def complete(self, prompt: str, max_tokens: int | None = None, generation_config: Dict[str, Any] = None, response_schema: Any = None) -> Any:
        # Если max_tokens не передан явно, берем из настроек
        effective_max_tokens = max_tokens if max_tokens is not None else settings.GEMINI_MAX_OUTPUT_TOKENS
        
        max_retries = len(self.api_keys) * 2

        for attempt in range(max_retries):
            try:
                # Глобальный троттлинг по минутному окну
                minute_key = f"gemini_rate:minute:{datetime.now(timezone.utc).strftime('%Y%m%d%H%M')}"
                current_minute_count = cache_service.increment_counter(minute_key, ttl=65)
                if current_minute_count > self.per_minute_limit:
                    from fastapi import HTTPException
                    raise HTTPException(
                        status_code=429,
                        detail="Rate limit exceeded: 10 req/min. Please retry shortly."
                    )

                # Выполняем запрос с повтором при временных ошибках
                last_error = None
                
                for model_name in self.models:
                    # Проверяем доступность текущего ключа ДЛЯ ЭТОЙ МОДЕЛИ
                    current_key = self.api_keys[self.current_key_index]
                    
                    if self._is_key_in_cooldown(current_key) or self._is_model_at_limit(current_key, model_name):
                        # Пробуем найти другой ключ для ЭТОЙ модели
                        try:
                            self._rotate_key(model_name)
                            current_key = self.api_keys[self.current_key_index]
                        except Exception:
                            # Для этой модели нет ключей, пробуем следующую по списку fallback
                            logger.warning(f"No keys available for model {model_name}, trying fallback...")
                            continue

                    try:
                        config_dict = generation_config.copy() if generation_config else {}
                        if effective_max_tokens:
                            config_dict['max_output_tokens'] = effective_max_tokens
                        
                        config_args = config_dict.copy()
                        if response_schema:
                            config_args['response_mime_type'] = 'application/json'
                            config_args['response_schema'] = response_schema

                        response = self.client.models.generate_content(
                            model=model_name,
                            contents=prompt,
                            config=types.GenerateContentConfig(**config_args) if config_args else None
                        )
                        
                        candidate = response.candidates[0]
                        if candidate.finish_reason == 'MAX_TOKENS':
                            logger.error(f"Response truncated due to MAX_TOKENS (limit {effective_max_tokens})")
                        elif candidate.finish_reason != 'STOP' and candidate.finish_reason != 'OTHER':
                            logger.warning(f"Unexpected finish reason: {candidate.finish_reason}")

                        # Если успех - увеличиваем счетчик для ЭТОЙ МОДЕЛИ
                        self._increment_key_usage(current_key, model_name)
                        
                        if hasattr(response, 'parsed') and response.parsed:
                            return response.parsed
                        
                        text_parts = []
                        if candidate.content and candidate.content.parts:
                            for part in candidate.content.parts:
                                if hasattr(part, 'text') and part.text:
                                    text_parts.append(part.text)
                        
                        result_text = "".join(text_parts)
                        logger.info(f"Gemini response length: {len(result_text)} chars. Model: {model_name}")
                        return result_text
                        
                    except Exception as model_e:
                        last_error = model_e
                        logger.warning(f"Model {model_name} failed with key index {self.current_key_index}: {model_e}")
                        # Если это rate limit (429), не пытаемся другие модели на этом ключе, меняем ключ
                        if "429" in str(model_e) or "RESOURCE_EXHAUSTED" in str(model_e):
                            # Можно пометить ключ как временно недоступный для этой модели
                            break
                        # Иначе пробуем следующую модель (fallback)
                        continue

                raise last_error or Exception("All models failed")

            except Exception as e:
                logger.error(f"Error with key {self.current_key_index}: {e}")
                current_key = self.api_keys[self.current_key_index]
                self._put_key_in_cooldown(current_key)

                # Переключаемся на следующий ключ перед повтором всей попытки
                try:
                    # Пытаемся найти ключ хоть для какой-то модели (flash-preview)
                    self._rotate_key(self.models[0])
                except Exception:
                    # Если уж совсем нет ключей
                    pass
                
                sleep_time = min(2 ** attempt, 10)
                time.sleep(sleep_time)

                if attempt == max_retries - 1:
                    raise Exception(f"All API keys failed after {max_retries} attempts: {e}")

        raise Exception("Failed to complete request with any available key")

    def get_usage_stats(self) -> Dict[str, Any]:
        """Получает статистику использования всех ключей по всем моделям."""
        stats = {
            "total_keys": len(self.api_keys),
            "current_key_index": self.current_key_index,
            "reset_timezone": settings.GEMINI_API_RESET_TIMEZONE,
            "current_time_mv": datetime.now(self.reset_timezone).isoformat(),
            "next_reset_mv": self._get_next_reset_time().isoformat(),
            "keys": []
        }

        for i, key in enumerate(self.api_keys):
            model_usages = {}
            for model in self.models:
                model_usages[model] = {
                    "usage": self._get_key_usage(key, model),
                    "limit": self.model_limits.get(model, 0),
                    "at_limit": self._is_model_at_limit(key, model)
                }

            key_stats = {
                "index": i,
                "models": model_usages,
                "in_cooldown": self._is_key_in_cooldown(key),
                "is_current": i == self.current_key_index
            }
            stats["keys"].append(key_stats)

        return stats

    def _get_next_reset_time(self) -> datetime:
        """Получает время следующего сброса лимитов."""
        now_mv = datetime.now(self.reset_timezone)
        tomorrow_mv = now_mv.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
        return tomorrow_mv


# Создаем глобальный экземпляр клиента
gemini_client = GeminiClient()
