from __future__ import annotations

import json
from datetime import datetime, timedelta
from typing import List, Dict, Any

import google.generativeai as genai
import pytz

from app.core.config import settings
from app.services.cache_service import cache_service


class GeminiClient:
    def __init__(self):
        self.api_keys = settings.GEMINI_API_KEYS
        self.limit_per_key = settings.GEMINI_API_LIMIT_PER_KEY
        self.threshold_percent = settings.GEMINI_API_LIMIT_THRESHOLD_PERCENT
        self.cooldown_hours = settings.GEMINI_API_COOLDOWN_HOURS
        self.reset_timezone = pytz.timezone(settings.GEMINI_API_RESET_TIMEZONE)
        self.current_key_index = 0
        # Глобальный минутный лимит (10 запросов/мин по всем ключам)
        self.per_minute_limit = 10

        if not self.api_keys:
            raise ValueError("No Gemini API keys provided")

        # Инициализируем первый ключ
        self._set_current_key()

    def _set_current_key(self):
        """Устанавливает текущий API ключ."""
        if not self.api_keys:
            raise ValueError("No API keys available")

        genai.configure(api_key=self.api_keys[self.current_key_index])

    def _get_reset_date(self) -> str:
        """Получает дату сброса лимитов в формате YYYY-MM-DD по времени Mountain View."""
        now_mv = datetime.now(self.reset_timezone)
        return now_mv.strftime("%Y-%m-%d")

    def _get_key_usage_key(self, key: str) -> str:
        """Генерирует ключ для хранения статистики использования."""
        reset_date = self._get_reset_date()
        return f"gemini_usage:{key}:{reset_date}"

    def _get_key_cooldown_key(self, key: str) -> str:
        """Генерирует ключ для хранения времени кулдауна."""
        return f"gemini_cooldown:{key}"

    def _is_key_in_cooldown(self, key: str) -> bool:
        """Проверяет, находится ли ключ в кулдауне."""
        cooldown_key = self._get_key_cooldown_key(key)
        cooldown_until = cache_service.get(cooldown_key)

        if not cooldown_until:
            return False

        cooldown_time = datetime.fromisoformat(cooldown_until)
        return datetime.now() < cooldown_time

    def _get_key_usage(self, key: str) -> int:
        """Получает количество использований ключа за текущий день (по времени Mountain View)."""
        usage_key = self._get_key_usage_key(key)
        return cache_service.get(usage_key) or 0

    def _increment_key_usage(self, key: str):
        """Увеличивает счетчик использований ключа."""
        usage_key = self._get_key_usage_key(key)
        current_usage = self._get_key_usage(key)
        
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

    def _find_available_key(self) -> str | None:
        """Находит доступный ключ для использования."""
        for i, key in enumerate(self.api_keys):
            if not self._is_key_in_cooldown(key):
                usage = self._get_key_usage(key)
                threshold = int(self.limit_per_key * self.threshold_percent / 100)

                if usage < threshold:
                    self.current_key_index = i
                    return key

        return None

    def _rotate_key(self):
        """Переключается на следующий доступный ключ."""
        available_key = self._find_available_key()

        if not available_key:
            raise Exception("No available API keys. All keys are either in cooldown or at limit.")

        self._set_current_key()

    def complete(self, prompt: str, max_tokens: int = 4000) -> str:
        """Выполняет запрос к Gemini API с автоматической ротацией ключей."""
        max_retries = len(self.api_keys)

        for attempt in range(max_retries):
            try:
                # Глобальный троттлинг по минутному окну
                minute_key = f"gemini_rate:minute:{datetime.utcnow().strftime('%Y%m%d%H%M')}"
                current_minute_count = cache_service.increment_counter(minute_key, ttl=65)
                if current_minute_count > self.per_minute_limit:
                    # Превышен лимит – подождем до следующей минуты
                    # На free-tier Render спать в потоках ок, но избежим длинных пауз: бросаем понятную ошибку
                    raise Exception("Rate limit exceeded: 10 req/min. Please retry shortly.")

                # Проверяем доступность текущего ключа
                current_key = self.api_keys[self.current_key_index]

                if self._is_key_in_cooldown(current_key):
                    self._rotate_key()
                    continue

                usage = self._get_key_usage(current_key)
                threshold = int(self.limit_per_key * self.threshold_percent / 100)

                if usage >= threshold:
                    self._put_key_in_cooldown(current_key)
                    self._rotate_key()
                    continue

                # Выполняем запрос с повтором при временных ошибках
                model = genai.GenerativeModel('gemini-2.5-flash')
                # Добавим краткий повтор при внутренних ошибках сервиса
                try:
                    response = model.generate_content(prompt)
                except Exception as inner_e:
                    # Одна повторная попытка через этот же ключ
                    response = model.generate_content(prompt)

                # Увеличиваем счетчик использований
                self._increment_key_usage(current_key)

                return response.text

            except Exception as e:
                # Логируем, переводим ключ в кулдаун и пробуем следующий
                print(f"Error with key {self.current_key_index}: {e}")

                # Помещаем текущий ключ в кулдаун при ошибке
                current_key = self.api_keys[self.current_key_index]
                self._put_key_in_cooldown(current_key)

                # Переключаемся на следующий ключ
                self._rotate_key()

                if attempt == max_retries - 1:
                    raise Exception(f"All API keys failed after {max_retries} attempts: {e}")

        raise Exception("Failed to complete request with any available key")

    def get_usage_stats(self) -> Dict[str, Any]:
        """Получает статистику использования всех ключей."""
        stats = {
            "total_keys": len(self.api_keys),
            "current_key_index": self.current_key_index,
            "reset_timezone": settings.GEMINI_API_RESET_TIMEZONE,
            "current_time_mv": datetime.now(self.reset_timezone).isoformat(),
            "next_reset_mv": self._get_next_reset_time().isoformat(),
            "keys": []
        }

        for i, key in enumerate(self.api_keys):
            key_stats = {
                "index": i,
                "usage_today": self._get_key_usage(key),
                "limit": self.limit_per_key,
                "threshold": int(self.limit_per_key * self.threshold_percent / 100),
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
