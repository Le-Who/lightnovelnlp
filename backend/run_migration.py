import os
import sys
import subprocess


def main() -> int:
    # Рабочая директория должна быть backend/
    here = os.path.dirname(os.path.abspath(__file__))
    os.chdir(here)
    try:
        # Выполняем alembic upgrade head
        return subprocess.call([sys.executable, '-m', 'alembic', 'upgrade', 'head'])
    except Exception as e:
        print(f"Migration failed: {e}")
        return 1


if __name__ == '__main__':
    sys.exit(main())

#!/usr/bin/env python3
"""
Скрипт для выполнения миграции базы данных.
Добавляет колонку approved_at в таблицу glossary_terms.
"""

import os
import sys
from pathlib import Path

# Добавляем путь к модулям приложения
sys.path.append(str(Path(__file__).parent))

from alembic import command
from alembic.config import Config
from app.core.config import settings


def run_migration():
    """Выполняет миграцию базы данных."""
    print("🔧 Выполнение миграции базы данных...")
    
    try:
        # Создаем конфигурацию Alembic
        alembic_cfg = Config("alembic.ini")
        alembic_cfg.set_main_option("sqlalchemy.url", settings.DATABASE_URL)
        
        # Выполняем миграцию
        print("📋 Применение миграции...")
        command.upgrade(alembic_cfg, "head")
        print("✅ Миграция выполнена успешно")
        
        print("🎉 База данных обновлена!")
        
    except Exception as e:
        print(f"❌ Ошибка выполнения миграции: {e}")
        sys.exit(1)


if __name__ == "__main__":
    run_migration()
