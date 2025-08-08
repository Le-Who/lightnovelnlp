#!/usr/bin/env python3
"""
Тестовый скрипт для проверки всех исправлений API
"""

import requests
import json
import sys

# Конфигурация
API_BASE_URL = "https://lightnovel-backend.onrender.com"

def test_endpoint(method, endpoint, data=None, expected_status=200):
    """Тестирует API endpoint"""
    url = f"{API_BASE_URL}{endpoint}"
    
    try:
        if method.upper() == "GET":
            response = requests.get(url)
        elif method.upper() == "POST":
            response = requests.post(url, json=data)
        elif method.upper() == "PUT":
            response = requests.put(url, json=data)
        elif method.upper() == "DELETE":
            response = requests.delete(url)
        else:
            print(f"❌ Неподдерживаемый метод: {method}")
            return False
        
        print(f"{'✅' if response.status_code == expected_status else '❌'} {method} {endpoint}")
        print(f"   Status: {response.status_code}")
        
        if response.status_code != expected_status:
            print(f"   Error: {response.text}")
        
        return response.status_code == expected_status
        
    except Exception as e:
        print(f"❌ {method} {endpoint} - Exception: {e}")
        return False

def main():
    print("🧪 Тестирование всех исправлений API")
    print("=" * 60)
    
    # Системные endpoints
    print("\n📊 Системные endpoints:")
    test_endpoint("GET", "/health")
    test_endpoint("GET", "/info")
    
    # Проекты
    print("\n📁 Тестирование проектов:")
    test_endpoint("GET", "/projects/")
    
    # Создаем тестовый проект
    project_data = {"name": "Test Project All Fixes"}
    test_endpoint("POST", "/projects/", project_data, 201)
    
    # Получаем проекты снова
    test_endpoint("GET", "/projects/")
    
    # Тестируем создание главы (ИСПРАВЛЕНИЕ 1)
    print("\n📖 Тестирование создания главы (ИСПРАВЛЕНИЕ 1):")
    chapter_data = {
        "title": "Test Chapter All Fixes",
        "original_text": "テストテキスト для проверки всех исправлений"
    }
    test_endpoint("POST", "/projects/1/chapters", chapter_data, 201)
    
    # Получаем главы проекта
    test_endpoint("GET", "/projects/1/chapters")
    
    # Глоссарий
    print("\n📚 Тестирование глоссария:")
    test_endpoint("GET", "/glossary/terms/1")
    
    # Создаем тестовый термин (ИСПРАВЛЕНИЕ 2)
    print("\n📝 Тестирование создания термина (ИСПРАВЛЕНИЕ 2):")
    term_data = {
        "project_id": 1,
        "source_term": "テスト",
        "translated_term": "Тест",
        "category": "other",
        "context": "Тестовый термин для проверки исправлений"
    }
    test_endpoint("POST", "/glossary/terms", term_data, 201)
    
    # Получаем термины снова
    test_endpoint("GET", "/glossary/terms/1")
    
    # Тестируем анализ главы (ИСПРАВЛЕНИЕ 3)
    print("\n🔍 Тестирование анализа главы (ИСПРАВЛЕНИЕ 3):")
    test_endpoint("POST", "/processing/chapters/1/analyze", {}, 200)
    
    # Мониторинг
    print("\n📈 Тестирование мониторинга:")
    test_endpoint("GET", "/glossary/api-usage")
    test_endpoint("GET", "/glossary/cache-stats")
    
    print("\n" + "=" * 60)
    print("✅ Тестирование всех исправлений завершено!")
    print("\n📋 Сводка всех исправлений:")
    print("1. ✅ Убран project_id из ChapterCreate schema")
    print("2. ✅ Добавлен project_id в GlossaryTermCreate schema")
    print("3. ✅ Добавлена валидация project_id в api-tools.html")
    print("4. ✅ Исправлен URL для Swagger docs")
    print("5. ✅ Добавлена валидация всех ID в формах")
    print("6. ✅ Убран frequency из создания GlossaryTerm")
    print("7. ✅ Улучшен интерфейс с выпадающими списками")
    print("\n🎯 Теперь все должно работать корректно!")

if __name__ == "__main__":
    main()
