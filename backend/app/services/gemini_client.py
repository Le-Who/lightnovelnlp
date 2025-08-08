from __future__ import annotations

import json
from datetime import datetime, timedelta
from typing import List, Dict, Any

import google.generativeai as genai
from app.core.config import settings
from app.services.cache_service import cache_service


class GeminiClient:
    def __init__(self):
        self.api_keys = settings.GEMINI_API_KEYS
        self.limit_per_key = settings.GEMINI_API_LIMIT_PER_KEY
        self.threshold_percent = settings.GEMINI_API_LIMIT_THRESHOLD_PERCENT
        self.cooldown_hours = settings.GEMINI_API_COOLDOWN_HOURS
        self.current_key_index = 0
        
        if not self.api_keys:
            raise ValueError("No Gemini API keys provided")
        
        # Инициализируем первый ключ
        self._set_current_key()
    
    def _set_current_key(self):
        """Устанавливает текущий API ключ."""
        if not self.api_keys:
            raise ValueError("No API keys available")
        
        genai.configure(api_key=self.api_keys[self.current_key_index])
    
    def _get_key_usage_key(self, key: str) -> str:
        """Генерирует ключ для хранения статистики использования."""
        today = datetime.now().strftime("%Y-%m-%d")
        return f"gemini_usage:{key}:{today}"
    
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
        """Получает количество использований ключа за сегодня."""
        usage_key = self._get_key_usage_key(key)
        return cache_service.get(usage_key) or 0
    
    def _increment_key_usage(self, key: str):
        """Увеличивает счетчик использований ключа."""
        usage_key = self._get_key_usage_key(key)
        current_usage = self._get_key_usage(key)
        cache_service.set(usage_key, current_usage + 1, ttl=86400)  # 24 часа
    
    def _put_key_in_cooldown(self, key: str):
        """Помещает ключ в кулдаун."""
        cooldown_key = self._get_key_cooldown_key(key)
        cooldown_until = (datetime.now() + timedelta(hours=self.cooldown_hours)).isoformat()
        cache_service.set(cooldown_key, cooldown_until, ttl=self.cooldown_hours * 3600)
    
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
                
                # Выполняем запрос
                model = genai.GenerativeModel('gemini-1.5-flash')
                response = model.generate_content(prompt)
                
                # Увеличиваем счетчик использований
                self._increment_key_usage(current_key)
                
                return response.text
                
            except Exception as e:
                print(f"Error with key {self.current_key_index}: {e}")
                
                # Помещаем текущий ключ в кулдаун при ошибке
                current_key = self.api_keys[self.current_key_index]
                self._put_key_in_cooldown(current_key)
                
                # Переключаемся на следующий ключ
                self._rotate_key()
                
                if attempt == max_retries - 1:
                    raise Exception(f"All API keys failed after {max_retries} attempts")
        
        raise Exception("Failed to complete request with any available key")
    
    def get_usage_stats(self) -> Dict[str, Any]:
        """Получает статистику использования всех ключей."""
        stats = {
            "total_keys": len(self.api_keys),
            "current_key_index": self.current_key_index,
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


# Создаем глобальный экземпляр клиента
gemini_client = GeminiClient()
