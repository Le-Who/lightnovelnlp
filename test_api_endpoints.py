#!/usr/bin/env python3
"""
Тестовый скрипт для проверки API endpoints
"""

import requests
import json
import sys

# Конфигурация
API_BASE_URL = "https://lightnovel-backend.onrender.com"  # Замените на ваш URL

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
    print("🧪 Тестирование API endpoints")
    print("=" * 50)
    
    # Системные endpoints
    print("\n📊 Системные endpoints:")
    test_endpoint("GET", "/health")
    test_endpoint("GET", "/info")
    test_endpoint("GET", "/docs")
    
    # Проекты
    print("\n📁 Тестирование проектов:")
    test_endpoint("GET", "/projects/")
    
    # Создаем тестовый проект
    project_data = {"name": "Test Project API"}
    test_endpoint("POST", "/projects/", project_data, 201)
    
    # Получаем проекты снова
    test_endpoint("GET", "/projects/")
    
    # Глоссарий
    print("\n📚 Тестирование глоссария:")
    test_endpoint("GET", "/glossary/terms/1")  # Получить термины для проекта 1
    
    # Создаем тестовый термин
    term_data = {
        "project_id": 1,
        "source_term": "テスト",
        "translated_term": "Тест",
        "category": "other",
        "context": "Тестовый термин"
    }
    test_endpoint("POST", "/glossary/terms", term_data, 201)
    
    # Получаем термины снова
    test_endpoint("GET", "/glossary/terms/1")
    
    # Мониторинг
    print("\n📈 Тестирование мониторинга:")
    test_endpoint("GET", "/glossary/api-usage")
    test_endpoint("GET", "/glossary/cache-stats")
    
    print("\n" + "=" * 50)
    print("✅ Тестирование завершено!")

if __name__ == "__main__":
    main()
