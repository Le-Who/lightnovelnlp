from __future__ import annotations

import json
import hashlib
import logging
from typing import Any, Optional
from datetime import datetime, timedelta

import redis
from app.core.config import settings


class CacheService:
    def __init__(self):
        self.redis_client = redis.from_url(settings.REDIS_URL)
        self.default_ttl = 3600  # 1 час по умолчанию
        self.logger = logging.getLogger("cache_service")

    def _generate_key(self, prefix: str, *args) -> str:
        """Генерирует ключ кэша на основе префикса и аргументов."""
        key_parts = [prefix] + [str(arg) for arg in args]
        key_string = ":".join(key_parts)
        return f"lightnovel:{key_string}"

    def _generate_content_hash(self, content: str) -> str:
        """Генерирует хеш содержимого для отслеживания изменений."""
        return hashlib.md5(content.encode()).hexdigest()

    def get(self, key: str) -> Optional[Any]:
        """Получить значение из кэша."""
        try:
            self._reconnect_if_needed()
            value = self.redis_client.get(key)
        except Exception as e:
            # Пытаемся переподключиться и повторить один раз
            self.logger.warning(f"Cache get error (will retry): {e}")
            self._reconnect_if_needed()
            try:
                value = self.redis_client.get(key)
            except Exception as e2:
                self.logger.error(f"Cache get failed after retry: {e2}")
                return None

        if value:
            # Для числовых значений возвращаем как int, для остальных как JSON
            try:
                return int(value.decode())
            except (ValueError, AttributeError):
                try:
                    return json.loads(value)
                except Exception:
                    return value
        return None

    def _reconnect_if_needed(self):
        """Переподключиться к Redis если соединение потеряно."""
        try:
            self.redis_client.ping()
        except Exception:
            try:
                self.redis_client = redis.from_url(settings.REDIS_URL)
            except Exception as e:
                print(f"Redis reconnection failed: {e}")

    def set(self, key: str, value: Any, ttl: int = None) -> bool:
        """Установить значение в кэш."""
        try:
            self._reconnect_if_needed()
            ttl = ttl or self.default_ttl
            
            # Для числовых значений сохраняем как строку, для остальных как JSON
            if isinstance(value, (int, float)):
                serialized_value = str(value)
            else:
                serialized_value = json.dumps(value, default=str)
            return bool(self.redis_client.setex(key, ttl, serialized_value))
        except Exception as e:
            self.logger.warning(f"Cache set error (will retry): {e}")
            self._reconnect_if_needed()
            try:
                return bool(self.redis_client.setex(key, ttl or self.default_ttl, serialized_value))
            except Exception as e2:
                self.logger.error(f"Cache set failed after retry: {e2}")
                return False

    def delete(self, key: str) -> bool:
        """Удалить значение из кэша."""
        try:
            return bool(self.redis_client.delete(key))
        except Exception as e:
            self.logger.warning(f"Cache delete error (will retry): {e}")
            self._reconnect_if_needed()
            try:
                return bool(self.redis_client.delete(key))
            except Exception as e2:
                self.logger.error(f"Cache delete failed after retry: {e2}")
                return False

    def delete_pattern(self, pattern: str) -> int:
        """Удалить все ключи по паттерну."""
        try:
            keys = self.redis_client.keys(pattern)
            if keys:
                return self.redis_client.delete(*keys)
            return 0
        except Exception as e:
            print(f"Cache delete pattern error: {e}")
            return 0

    # Кэширование переводов
    def get_translation_cache_key(self, chapter_id: int, glossary_hash: str) -> str:
        """Генерирует ключ кэша для перевода главы."""
        return self._generate_key("translation", chapter_id, glossary_hash)

    def get_cached_translation(self, chapter_id: int, glossary_hash: str) -> Optional[str]:
        """Получить кэшированный перевод."""
        key = self.get_translation_cache_key(chapter_id, glossary_hash)
        return self.get(key)

    def cache_translation(self, chapter_id: int, glossary_hash: str, translation: str, ttl: int = 86400) -> bool:
        """Кэшировать перевод (TTL 24 часа)."""
        key = self.get_translation_cache_key(chapter_id, glossary_hash)
        return self.set(key, translation, ttl)

    def invalidate_translation_cache(self, chapter_id: int) -> bool:
        """Инвалидировать кэш перевода для главы."""
        pattern = self._generate_key("translation", chapter_id, "*")
        return self.delete_pattern(pattern) > 0

    # Кэширование глоссария
    def get_glossary_cache_key(self, project_id: int) -> str:
        """Генерирует ключ кэша для глоссария проекта."""
        return self._generate_key("glossary", project_id)

    def get_cached_glossary(self, project_id: int) -> Optional[list]:
        """Получить кэшированный глоссарий."""
        key = self.get_glossary_cache_key(project_id)
        return self.get(key)

    def cache_glossary(self, project_id: int, glossary: list, ttl: int = 3600) -> bool:
        """Кэшировать глоссарий (TTL 1 час)."""
        key = self.get_glossary_cache_key(project_id)
        return self.set(key, glossary, ttl)

    def invalidate_glossary_cache(self, project_id: int) -> bool:
        """Инвалидировать кэш глоссария."""
        key = self.get_glossary_cache_key(project_id)
        return self.delete(key)

    # Кэширование саммари
    def get_summary_cache_key(self, chapter_id: int) -> str:
        """Генерирует ключ кэша для саммари главы."""
        return self._generate_key("summary", chapter_id)

    def get_cached_summary(self, chapter_id: int) -> Optional[str]:
        """Получить кэшированное саммари."""
        key = self.get_summary_cache_key(chapter_id)
        return self.get(key)

    def cache_summary(self, chapter_id: int, summary: str, ttl: int = 7200) -> bool:
        """Кэшировать саммари (TTL 2 часа)."""
        key = self.get_summary_cache_key(chapter_id)
        return self.set(key, summary, ttl)

    def invalidate_summary_cache(self, chapter_id: int) -> bool:
        """Инвалидировать кэш саммари."""
        key = self.get_summary_cache_key(chapter_id)
        return self.delete(key)

    # Кэширование связей
    def get_relationships_cache_key(self, project_id: int) -> str:
        """Генерирует ключ кэша для связей проекта."""
        return self._generate_key("relationships", project_id)

    def get_cached_relationships(self, project_id: int) -> Optional[list]:
        """Получить кэшированные связи."""
        key = self.get_relationships_cache_key(project_id)
        return self.get(key)

    def cache_relationships(self, project_id: int, relationships: list, ttl: int = 3600) -> bool:
        """Кэшировать связи (TTL 1 час)."""
        key = self.get_relationships_cache_key(project_id)
        return self.set(key, relationships, ttl)

    def invalidate_relationships_cache(self, project_id: int) -> bool:
        """Инвалидировать кэш связей."""
        key = self.get_relationships_cache_key(project_id)
        return self.delete(key)

    # Утилиты для работы с хешами
    def generate_glossary_hash(self, glossary_terms: list) -> str:
        """Генерирует хеш глоссария для отслеживания изменений."""
        # Сортируем термины для стабильного хеша
        sorted_terms = sorted(glossary_terms, key=lambda x: x.get('source_term', ''))
        terms_string = json.dumps(sorted_terms, sort_keys=True)
        return self._generate_content_hash(terms_string)

    def get_cache_stats(self) -> dict:
        """Получить статистику кэша."""
        try:
            info = self.redis_client.info()
            return {
                "used_memory": info.get("used_memory_human", "N/A"),
                "connected_clients": info.get("connected_clients", 0),
                "total_commands_processed": info.get("total_commands_processed", 0),
                "keyspace_hits": info.get("keyspace_hits", 0),
                "keyspace_misses": info.get("keyspace_misses", 0)
            }
        except Exception as e:
            print(f"Cache stats error: {e}")
            return {}


cache_service = CacheService()
