#!/usr/bin/env python3
"""
Скрипт для проверки конфигурации приложения
"""

import os
import sys
from typing import List

def check_required_env_vars():
    """Проверяет наличие обязательных переменных окружения"""
    required_vars = [
        'DATABASE_URL',
        'REDIS_URL',
        'GEMINI_API_KEYS_RAW'
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"❌ Отсутствуют обязательные переменные окружения: {', '.join(missing_vars)}")
        return False
    
    print("✅ Все обязательные переменные окружения найдены")
    return True

def check_gemini_keys():
    """Проверяет формат GEMINI_API_KEYS_RAW"""
    keys_str = os.getenv('GEMINI_API_KEYS_RAW', '')
    
    if not keys_str.strip():
        print("❌ GEMINI_API_KEYS_RAW пустая или не установлена")
        return False
    
    # Парсим ключи
    keys = [key.strip() for key in keys_str.split(',') if key.strip()]
    
    if not keys:
        print("❌ GEMINI_API_KEYS_RAW не содержит валидных ключей")
        return False
    
    print(f"✅ Найдено {len(keys)} ключей Gemini API")
    return True

def check_database_url():
    """Проверяет формат DATABASE_URL"""
    db_url = os.getenv('DATABASE_URL', '')
    
    if not db_url:
        print("❌ DATABASE_URL не установлена")
        return False
    
    if not db_url.startswith('postgresql://'):
        print("❌ DATABASE_URL должна начинаться с 'postgresql://'")
        return False
    
    print("✅ DATABASE_URL имеет правильный формат")
    return True

def check_redis_url():
    """Проверяет формат REDIS_URL"""
    redis_url = os.getenv('REDIS_URL', '')
    
    if not redis_url:
        print("❌ REDIS_URL не установлена")
        return False
    
    if not redis_url.startswith(('redis://', 'rediss://')):
        print("❌ REDIS_URL должна начинаться с 'redis://' или 'rediss://'")
        return False
    
    print("✅ REDIS_URL имеет правильный формат")
    return True

def main():
    """Основная функция проверки"""
    print("🔍 Проверка конфигурации приложения...")
    print("=" * 50)
    
    checks = [
        check_required_env_vars,
        check_gemini_keys,
        check_database_url,
        check_redis_url
    ]
    
    all_passed = True
    for check in checks:
        if not check():
            all_passed = False
        print()
    
    if all_passed:
        print("🎉 Все проверки пройдены успешно!")
        return 0
    else:
        print("❌ Некоторые проверки не пройдены")
        return 1

if __name__ == "__main__":
    sys.exit(main())
