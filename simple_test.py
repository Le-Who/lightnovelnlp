#!/usr/bin/env python3
"""
Простой тест для проверки доступности API
"""

import requests
import json

def test_api():
    """Тестирует доступность API"""
    base_url = "https://lightnovel-backend.onrender.com"
    
    print("🔍 Тестирование API...")
    print(f"URL: {base_url}")
    print("-" * 50)
    
    # Тест 1: Health check
    try:
        response = requests.get(f"{base_url}/health", timeout=10)
        print(f"✅ Health Check: {response.status_code}")
        if response.status_code == 200:
            print(f"   Ответ: {response.json()}")
        else:
            print(f"   Ошибка: {response.text}")
    except Exception as e:
        print(f"❌ Health Check: Ошибка подключения - {e}")
    
    # Тест 2: Info endpoint
    try:
        response = requests.get(f"{base_url}/info", timeout=10)
        print(f"✅ Info: {response.status_code}")
        if response.status_code == 200:
            print(f"   Ответ: {response.json()}")
        else:
            print(f"   Ошибка: {response.text}")
    except Exception as e:
        print(f"❌ Info: Ошибка подключения - {e}")
    
    # Тест 3: Projects endpoint
    try:
        response = requests.get(f"{base_url}/projects/", timeout=10)
        print(f"✅ Projects: {response.status_code}")
        if response.status_code == 200:
            projects = response.json()
            print(f"   Найдено проектов: {len(projects)}")
        else:
            print(f"   Ошибка: {response.text}")
    except Exception as e:
        print(f"❌ Projects: Ошибка подключения - {e}")
    
    print("-" * 50)
    print("🏁 Тестирование завершено")

if __name__ == "__main__":
    test_api()
