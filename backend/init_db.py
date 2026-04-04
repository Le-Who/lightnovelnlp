#!/usr/bin/env python3
"""
Скрипт для инициализации базы данных.
Создает все таблицы и выполняет миграции.
"""

import sys
from pathlib import Path

# Добавляем путь к модулям приложения
sys.path.append(str(Path(__file__).parent))

from app.db import engine, Base  # noqa: E402
from app.core.config import settings  # noqa: E402


def init_database():
    """Инициализирует базу данных."""
    print("🔧 Инициализация базы данных...")

    try:
        # Создаем все таблицы
        print("📋 Создание таблиц...")
        Base.metadata.create_all(bind=engine)
        print("✅ Таблицы созданы успешно")

        # Проверяем подключение
        print("🔍 Проверка подключения...")
        with engine.connect() as conn:
            conn.execute("SELECT 1")
            print("✅ Подключение к базе данных работает")

        print("🎉 База данных инициализирована успешно!")

    except Exception as e:
        print(f"❌ Ошибка инициализации базы данных: {e}")
        sys.exit(1)


def check_environment():
    """Проверяет переменные окружения."""
    print("🔍 Проверка переменных окружения...")

    required_vars = ["DATABASE_URL", "REDIS_URL", "GEMINI_API_KEYS_RAW"]

    missing_vars = []
    for var in required_vars:
        if not getattr(settings, var, None):
            missing_vars.append(var)

    # Проверяем, что GEMINI_API_KEYS парсится корректно
    if not settings.GEMINI_API_KEYS:
        missing_vars.append("GEMINI_API_KEYS (парсинг)")

    if missing_vars:
        print(
            f"❌ Отсутствуют обязательные переменные окружения: {', '.join(missing_vars)}"
        )
        print("💡 Убедитесь, что все переменные окружения настроены правильно")
        return False

    print("✅ Все переменные окружения настроены")
    return True


if __name__ == "__main__":
    print("🚀 Запуск инициализации Light Novel NLP...")

    # Проверяем переменные окружения
    if not check_environment():
        sys.exit(1)

    # Инициализируем базу данных
    init_database()

    print("✨ Инициализация завершена!")
