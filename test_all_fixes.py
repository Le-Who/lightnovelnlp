#!/usr/bin/env python3
"""
Тестовый скрипт для проверки всех исправлений в API
"""

import requests
import json
import time

# Конфигурация
API_BASE_URL = "https://lightnovel-backend.onrender.com"

def make_request(url, method="GET", data=None):
    """Выполнить HTTP запрос"""
    try:
        if method == "GET":
            response = requests.get(url)
        elif method == "POST":
            response = requests.post(url, json=data)
        elif method == "PUT":
            response = requests.put(url, json=data)
        elif method == "DELETE":
            response = requests.delete(url)
        
        return {
            "success": response.status_code < 400,
            "status_code": response.status_code,
            "data": response.json() if response.content else None,
            "error": None
        }
    except Exception as e:
        return {
            "success": False,
            "status_code": None,
            "data": None,
            "error": str(e)
        }

def test_health_check():
    """Тест проверки здоровья API"""
    print("🔍 Тест 1: Проверка здоровья API")
    result = make_request(f"{API_BASE_URL}/health")
    print(f"   Статус: {'✅' if result['success'] else '❌'}")
    print(f"   Код ответа: {result['status_code']}")
    if result['data']:
        print(f"   Ответ: {result['data']}")
    print()

def test_project_creation():
    """Тест создания проекта"""
    print("🔍 Тест 2: Создание проекта")
    project_data = {
        "name": f"Тестовый проект {int(time.time())}"
    }
    result = make_request(f"{API_BASE_URL}/projects", method="POST", data=project_data)
    print(f"   Статус: {'✅' if result['success'] else '❌'}")
    print(f"   Код ответа: {result['status_code']}")
    if result['data']:
        print(f"   Создан проект: {result['data']}")
        return result['data']['id']
    print()
    return None

def test_chapter_creation(project_id):
    """Тест создания главы"""
    print("🔍 Тест 3: Создание главы")
    chapter_data = {
        "title": "Тестовая глава",
        "original_text": "これはテスト用のテキストです。主人公は勇者です。"
    }
    result = make_request(f"{API_BASE_URL}/projects/{project_id}/chapters", method="POST", data=chapter_data)
    print(f"   Статус: {'✅' if result['success'] else '❌'}")
    print(f"   Код ответа: {result['status_code']}")
    if result['data']:
        print(f"   Создана глава: {result['data']}")
        return result['data']['id']
    print()
    return None

def test_term_creation(project_id):
    """Тест создания термина"""
    print("🔍 Тест 4: Создание термина")
    term_data = {
        "project_id": project_id,
        "source_term": "主人公",
        "translated_term": "Главный герой",
        "category": "character",
        "context": "Тестовый контекст"
    }
    result = make_request(f"{API_BASE_URL}/glossary/terms", method="POST", data=term_data)
    print(f"   Статус: {'✅' if result['success'] else '❌'}")
    print(f"   Код ответа: {result['status_code']}")
    if result['data']:
        print(f"   Создан термин: {result['data']}")
        return result['data']['id']
    print()
    return None

def test_duplicate_term_creation(project_id):
    """Тест создания дубликата термина"""
    print("🔍 Тест 5: Попытка создания дубликата термина")
    term_data = {
        "project_id": project_id,
        "source_term": "主人公",  # Тот же термин
        "translated_term": "Другой перевод",
        "category": "character",
        "context": "Другой контекст"
    }
    result = make_request(f"{API_BASE_URL}/glossary/terms", method="POST", data=term_data)
    print(f"   Статус: {'✅' if not result['success'] else '❌'} (должен быть неуспешным)")
    print(f"   Код ответа: {result['status_code']} (должен быть 400)")
    if result['data']:
        print(f"   Ошибка: {result['data']}")
    print()

def test_term_approval(term_id):
    """Тест утверждения термина"""
    print("🔍 Тест 6: Утверждение термина")
    result = make_request(f"{API_BASE_URL}/glossary/terms/{term_id}/approve", method="POST")
    print(f"   Статус: {'✅' if result['success'] else '❌'}")
    print(f"   Код ответа: {result['status_code']}")
    if result['data']:
        print(f"   Термин утвержден: {result['data']}")
    print()

def test_term_rejection(term_id):
    """Тест отклонения термина"""
    print("🔍 Тест 7: Отклонение термина")
    result = make_request(f"{API_BASE_URL}/glossary/terms/{term_id}/reject", method="POST")
    print(f"   Статус: {'✅' if result['success'] else '❌'}")
    print(f"   Код ответа: {result['status_code']}")
    if result['data']:
        print(f"   Термин отклонен: {result['data']}")
    print()

def test_chapter_analysis(chapter_id):
    """Тест анализа главы"""
    print("🔍 Тест 8: Анализ главы")
    result = make_request(f"{API_BASE_URL}/processing/chapters/{chapter_id}/analyze", method="POST")
    print(f"   Статус: {'✅' if result['success'] else '❌'}")
    print(f"   Код ответа: {result['status_code']}")
    if result['data']:
        print(f"   Результат анализа: {result['data']}")
    print()

def test_get_pending_terms(project_id):
    """Тест получения терминов в ожидании"""
    print("🔍 Тест 9: Получение терминов в ожидании")
    result = make_request(f"{API_BASE_URL}/glossary/terms/{project_id}/pending")
    print(f"   Статус: {'✅' if result['success'] else '❌'}")
    print(f"   Код ответа: {result['status_code']}")
    if result['data']:
        print(f"   Найдено терминов в ожидании: {len(result['data'])}")
        for term in result['data']:
            print(f"     - {term['source_term']} -> {term['translated_term']} (статус: {term['status']})")
    print()

def main():
    """Основная функция тестирования"""
    print("🚀 Начинаем тестирование всех исправлений API")
    print("=" * 60)
    
    # Тест 1: Проверка здоровья
    test_health_check()
    
    # Тест 2: Создание проекта
    project_id = test_project_creation()
    if not project_id:
        print("❌ Не удалось создать проект. Прерываем тестирование.")
        return
    
    # Тест 3: Создание главы
    chapter_id = test_chapter_creation(project_id)
    if not chapter_id:
        print("❌ Не удалось создать главу. Прерываем тестирование.")
        return
    
    # Тест 4: Создание термина
    term_id = test_term_creation(project_id)
    if not term_id:
        print("❌ Не удалось создать термин. Прерываем тестирование.")
        return
    
    # Тест 5: Попытка создания дубликата
    test_duplicate_term_creation(project_id)
    
    # Тест 6: Утверждение термина
    test_term_approval(term_id)
    
    # Тест 7: Отклонение термина (создаем новый термин для этого теста)
    term_id2 = test_term_creation(project_id)
    if term_id2:
        test_term_rejection(term_id2)
    
    # Тест 8: Анализ главы
    test_chapter_analysis(chapter_id)
    
    # Тест 9: Получение терминов в ожидании
    test_get_pending_terms(project_id)
    
    print("🎉 Тестирование завершено!")
    print("=" * 60)

if __name__ == "__main__":
    main()
