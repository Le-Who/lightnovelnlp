#!/usr/bin/env python3
"""
Тестовый файл для проверки функциональности Light Novel NLP системы
"""

import requests
import json
import time

# Конфигурация
BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/api/v1"

def test_api_health():
    """Проверка доступности API"""
    try:
        response = requests.get(f"{BASE_URL}/docs")
        print("✅ API доступен")
        return True
    except requests.exceptions.RequestException as e:
        print(f"❌ API недоступен: {e}")
        return False

def test_project_creation():
    """Тест создания проекта"""
    try:
        project_data = {
            "title": "Тестовый проект",
            "description": "Проект для тестирования функциональности",
            "genre": "fantasy"
        }
        
        response = requests.post(f"{API_BASE}/projects/", json=project_data)
        if response.status_code == 201:
            project = response.json()
            print(f"✅ Проект создан: {project['title']} (ID: {project['id']})")
            return project['id']
        else:
            print(f"❌ Ошибка создания проекта: {response.status_code}")
            print(response.text)
            return None
    except Exception as e:
        print(f"❌ Ошибка теста создания проекта: {e}")
        return None

def test_chapter_upload():
    """Тест загрузки глав из файла"""
    try:
        # Создаем тестовый текстовый файл
        test_content = """Введение
Это введение к роману.

Глава 1
Первая глава романа. Здесь происходит знакомство с главным героем.

Глава 2
Вторая глава. Герой отправляется в путешествие.

Глава 3
Третья глава. Начинаются приключения."""
        
        with open("test_chapters.txt", "w", encoding="utf-8") as f:
            f.write(test_content)
        
        print("✅ Тестовый файл создан")
        
        # Тестируем загрузку (требует существующий project_id)
        print("ℹ️ Для полного тестирования загрузки глав нужен существующий project_id")
        
    except Exception as e:
        print(f"❌ Ошибка теста загрузки глав: {e}")

def test_glossary_functionality():
    """Тест функциональности глоссария"""
    print("ℹ️ Тестирование глоссария требует существующего проекта с главами")
    print("ℹ️ Функции для тестирования:")
    print("  - Подсчет частоты терминов")
    print("  - Сортировка по частоте")
    print("  - Автоматическое утверждение терминов")

def test_translation_review():
    """Тест рецензирования перевода"""
    print("ℹ️ Тестирование рецензирования требует существующего перевода")
    print("ℹ️ Функции для тестирования:")
    print("  - Запрос рецензии у LLM")
    print("  - Отображение рецензии")
    print("  - Кэширование рецензий")

def main():
    """Основная функция тестирования"""
    print("🧪 Тестирование Light Novel NLP системы")
    print("=" * 50)
    
    # Проверяем доступность API
    if not test_api_health():
        return
    
    print("\n📋 Тестирование основных функций:")
    
    # Тест создания проекта
    project_id = test_project_creation()
    
    # Тест загрузки глав
    test_chapter_upload()
    
    # Тест глоссария
    test_glossary_functionality()
    
    # Тест рецензирования
    test_translation_review()
    
    print("\n" + "=" * 50)
    print("✅ Тестирование завершено")
    
    if project_id:
        print(f"📁 Создан тестовый проект с ID: {project_id}")
        print(f"🔗 Откройте в браузере: {BASE_URL}/docs")

if __name__ == "__main__":
    main()
