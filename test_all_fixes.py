#!/usr/bin/env python3
"""
Комплексный тестовый скрипт для проверки всех исправлений в API
"""

import requests
import json
import time
from typing import Dict, Any, List

# Конфигурация
API_BASE_URL = "https://lightnovel-backend.onrender.com"
# API_BASE_URL = "http://localhost:8000"  # Для локального тестирования

class APITester:
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.session = requests.Session()
        self.test_results = []
        
    def log_test(self, test_name: str, success: bool, details: str = ""):
        """Логирует результат теста"""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        if details:
            print(f"   {details}")
        self.test_results.append({
            "test": test_name,
            "success": success,
            "details": details
        })
        
    def make_request(self, method: str, endpoint: str, data: Dict = None) -> Dict[str, Any]:
        """Выполняет HTTP запрос"""
        url = f"{self.base_url}{endpoint}"
        headers = {"Content-Type": "application/json"}
        
        try:
            if method.upper() == "GET":
                response = self.session.get(url, headers=headers)
            elif method.upper() == "POST":
                response = self.session.post(url, headers=headers, json=data)
            elif method.upper() == "PUT":
                response = self.session.put(url, headers=headers, json=data)
            elif method.upper() == "DELETE":
                response = self.session.delete(url, headers=headers)
            else:
                raise ValueError(f"Unsupported method: {method}")
                
            return {
                "success": response.status_code < 400,
                "status_code": response.status_code,
                "data": response.json() if response.content else None,
                "error": None
            }
        except Exception as e:
            return {
                "success": False,
                "status_code": 0,
                "data": None,
                "error": str(e)
            }
    
    def test_health_check(self):
        """Тест проверки здоровья API"""
        result = self.make_request("GET", "/health")
        self.log_test(
            "Health Check",
            result["success"],
            f"Status: {result['status_code']}"
        )
        
    def test_create_project(self) -> int:
        """Тест создания проекта"""
        project_data = {
            "name": f"Test Project {int(time.time())}",
            "genre": "fantasy"
        }
        result = self.make_request("POST", "/projects/", project_data)
        
        success = result["success"] and result["data"] and "id" in result["data"]
        project_id = result["data"]["id"] if success else None
        
        self.log_test(
            "Create Project",
            success,
            f"Project ID: {project_id}" if success else f"Error: {result.get('error', result.get('data', {}).get('detail', 'Unknown'))}"
        )
        
        return project_id
    
    def test_create_chapter(self, project_id: int) -> int:
        """Тест создания главы"""
        chapter_data = {
            "title": "Test Chapter",
            "original_text": "This is a test chapter with some Japanese terms like 剣士 (kenshi) and 魔法 (mahou)."
        }
        result = self.make_request("POST", f"/projects/{project_id}/chapters", chapter_data)
        
        success = result["success"] and result["data"] and "id" in result["data"]
        chapter_id = result["data"]["id"] if success else None
        
        self.log_test(
            "Create Chapter",
            success,
            f"Chapter ID: {chapter_id}" if success else f"Error: {result.get('error', result.get('data', {}).get('detail', 'Unknown'))}"
        )
        
        return chapter_id
    
    def test_create_term(self, project_id: int) -> int:
        """Тест создания термина"""
        term_data = {
            "project_id": project_id,
            "source_term": "剣士",
            "translated_term": "Мечник",
            "category": "character",
            "context": "Test context"
        }
        result = self.make_request("POST", "/glossary/terms", term_data)
        
        success = result["success"] and result["data"] and "id" in result["data"]
        term_id = result["data"]["id"] if success else None
        
        self.log_test(
            "Create Term",
            success,
            f"Term ID: {term_id}" if success else f"Error: {result.get('error', result.get('data', {}).get('detail', 'Unknown'))}"
        )
        
        return term_id
    
    def test_get_terms(self, project_id: int):
        """Тест получения терминов"""
        result = self.make_request("GET", f"/glossary/terms/{project_id}")
        
        success = result["success"] and isinstance(result["data"], list)
        
        self.log_test(
            "Get Terms",
            success,
            f"Found {len(result['data'])} terms" if success else f"Error: {result.get('error', result.get('data', {}).get('detail', 'Unknown'))}"
        )
    
    def test_get_pending_terms(self, project_id: int):
        """Тест получения ожидающих терминов"""
        result = self.make_request("GET", f"/glossary/terms/{project_id}/pending")
        
        success = result["success"] and isinstance(result["data"], list)
        
        self.log_test(
            "Get Pending Terms",
            success,
            f"Found {len(result['data'])} pending terms" if success else f"Error: {result.get('error', result.get('data', {}).get('detail', 'Unknown'))}"
        )
    
    def test_approve_term(self, term_id: int):
        """Тест утверждения термина"""
        result = self.make_request("POST", f"/glossary/terms/{term_id}/approve")
        
        success = result["success"] and result["data"] and result["data"].get("status") == "approved"
        
        self.log_test(
            "Approve Term",
            success,
            f"Term status: {result['data'].get('status')}" if success else f"Error: {result.get('error', result.get('data', {}).get('detail', 'Unknown'))}"
        )
    
    def test_reject_term(self, term_id: int):
        """Тест отклонения термина"""
        result = self.make_request("POST", f"/glossary/terms/{term_id}/reject")
        
        success = result["success"] and result["data"] and result["data"].get("status") == "rejected"
        
        self.log_test(
            "Reject Term",
            success,
            f"Term status: {result['data'].get('status')}" if success else f"Error: {result.get('error', result.get('data', {}).get('detail', 'Unknown'))}"
        )
    
    def test_update_term(self, term_id: int):
        """Тест обновления термина"""
        update_data = {
            "translated_term": "Обновленный мечник",
            "category": "character",
            "context": "Обновленный контекст"
        }
        result = self.make_request("PUT", f"/glossary/terms/{term_id}", update_data)
        
        success = result["success"] and result["data"]
        
        self.log_test(
            "Update Term",
            success,
            f"Updated term: {result['data'].get('translated_term')}" if success else f"Error: {result.get('error', result.get('data', {}).get('detail', 'Unknown'))}"
        )
    
    def test_get_term_details(self, term_id: int):
        """Тест получения деталей термина"""
        result = self.make_request("GET", f"/glossary/terms/{term_id}/details")
        
        success = result["success"] and result["data"] and "id" in result["data"]
        
        self.log_test(
            "Get Term Details",
            success,
            f"Term: {result['data'].get('source_term')}" if success else f"Error: {result.get('error', result.get('data', {}).get('detail', 'Unknown'))}"
        )
    
    def test_analyze_chapter(self, chapter_id: int):
        """Тест анализа главы"""
        result = self.make_request("POST", f"/processing/chapters/{chapter_id}/analyze")
        
        success = result["success"]
        
        self.log_test(
            "Analyze Chapter",
            success,
            f"Analysis completed" if success else f"Error: {result.get('error', result.get('data', {}).get('detail', 'Unknown'))}"
        )
    
    def test_translate_chapter(self, chapter_id: int):
        """Тест перевода главы"""
        result = self.make_request("POST", f"/translation/chapters/{chapter_id}/translate")
        
        success = result["success"]
        
        self.log_test(
            "Translate Chapter",
            success,
            f"Translation completed" if success else f"Error: {result.get('error', result.get('data', {}).get('detail', 'Unknown'))}"
        )
    
    def test_get_chapters(self, project_id: int):
        """Тест получения глав"""
        result = self.make_request("GET", f"/projects/{project_id}/chapters")
        
        success = result["success"] and isinstance(result["data"], list)
        
        self.log_test(
            "Get Chapters",
            success,
            f"Found {len(result['data'])} chapters" if success else f"Error: {result.get('error', result.get('data', {}).get('detail', 'Unknown'))}"
        )
    
    def test_get_projects(self):
        """Тест получения проектов"""
        result = self.make_request("GET", "/projects/")
        
        success = result["success"] and isinstance(result["data"], list)
        
        self.log_test(
            "Get Projects",
            success,
            f"Found {len(result['data'])} projects" if success else f"Error: {result.get('error', result.get('data', {}).get('detail', 'Unknown'))}"
        )
    
    def test_api_usage(self):
        """Тест получения статистики API"""
        result = self.make_request("GET", "/glossary/api-usage")
        
        success = result["success"]
        
        self.log_test(
            "Get API Usage",
            success,
            f"API stats retrieved" if success else f"Error: {result.get('error', result.get('data', {}).get('detail', 'Unknown'))}"
        )
    
    def test_cache_stats(self):
        """Тест получения статистики кэша"""
        result = self.make_request("GET", "/glossary/cache-stats")
        
        success = result["success"]
        
        self.log_test(
            "Get Cache Stats",
            success,
            f"Cache stats retrieved" if success else f"Error: {result.get('error', result.get('data', {}).get('detail', 'Unknown'))}"
        )
    
    def test_duplicate_term_creation(self, project_id: int):
        """Тест создания дублирующегося термина"""
        term_data = {
            "project_id": project_id,
            "source_term": "剣士",  # Тот же термин
            "translated_term": "Другой мечник",
            "category": "character"
        }
        result = self.make_request("POST", "/glossary/terms", term_data)
        
        # Ожидаем ошибку 400 (дубликат)
        success = not result["success"] and result["status_code"] == 400
        
        self.log_test(
            "Duplicate Term Creation (should fail)",
            success,
            f"Correctly rejected duplicate" if success else f"Unexpected result: {result.get('status_code')}"
        )
    
    def run_all_tests(self):
        """Запускает все тесты"""
        print("🚀 Запуск комплексного тестирования API")
        print("=" * 50)
        
        # Базовые тесты
        self.test_health_check()
        self.test_get_projects()
        self.test_api_usage()
        self.test_cache_stats()
        
        # Создание тестовых данных
        project_id = self.test_create_project()
        if not project_id:
            print("❌ Не удалось создать проект. Прерываем тестирование.")
            return
            
        chapter_id = self.test_create_chapter(project_id)
        if not chapter_id:
            print("❌ Не удалось создать главу. Прерываем тестирование.")
            return
            
        term_id = self.test_create_term(project_id)
        if not term_id:
            print("❌ Не удалось создать термин. Прерываем тестирование.")
            return
        
        # Тесты глоссария
        self.test_get_terms(project_id)
        self.test_get_pending_terms(project_id)
        self.test_get_term_details(term_id)
        self.test_update_term(term_id)
        self.test_approve_term(term_id)
        
        # Создаем еще один термин для теста отклонения
        term_id2 = self.test_create_term(project_id)
        if term_id2:
            self.test_reject_term(term_id2)
        
        # Тест дубликатов
        self.test_duplicate_term_creation(project_id)
        
        # Тесты обработки
        self.test_analyze_chapter(chapter_id)
        self.test_translate_chapter(chapter_id)
        
        # Тесты получения данных
        self.test_get_chapters(project_id)
        
        # Итоговая статистика
        print("\n" + "=" * 50)
        print("📊 ИТОГОВАЯ СТАТИСТИКА")
        print("=" * 50)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["success"])
        failed_tests = total_tests - passed_tests
        
        print(f"Всего тестов: {total_tests}")
        print(f"✅ Успешно: {passed_tests}")
        print(f"❌ Провалено: {failed_tests}")
        print(f"📈 Успешность: {(passed_tests/total_tests)*100:.1f}%")
        
        if failed_tests > 0:
            print("\n❌ ПРОВАЛЕННЫЕ ТЕСТЫ:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"  - {result['test']}: {result['details']}")
        else:
            print("\n🎉 Все тесты прошли успешно!")

def main():
    """Главная функция"""
    tester = APITester(API_BASE_URL)
    tester.run_all_tests()

if __name__ == "__main__":
    main()
