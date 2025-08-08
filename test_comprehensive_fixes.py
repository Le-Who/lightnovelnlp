#!/usr/bin/env python3
"""
Комплексный тест всех исправлений в системе Light Novel NLP
"""

import requests
import json
import time
from typing import Dict, Any

class ComprehensiveTester:
    def __init__(self, base_url: str = "https://lightnovel-backend.onrender.com"):
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
        
    def test_health_check(self) -> bool:
        """Тест проверки здоровья API"""
        try:
            response = self.session.get(f"{self.base_url}/health")
            success = response.status_code == 200
            self.log_test("Health Check", success, f"Status: {response.status_code}")
            return success
        except Exception as e:
            self.log_test("Health Check", False, f"Error: {e}")
            return False
            
    def test_api_usage_stats(self) -> bool:
        """Тест статистики API"""
        try:
            response = self.session.get(f"{self.base_url}/glossary/api-usage")
            success = response.status_code == 200
            if success:
                data = response.json()
                keys_count = len(data.get("keys", []))
                self.log_test("API Usage Stats", success, f"Found {keys_count} API keys")
            else:
                self.log_test("API Usage Stats", False, f"Status: {response.status_code}")
            return success
        except Exception as e:
            self.log_test("API Usage Stats", False, f"Error: {e}")
            return False
            
    def test_cache_stats(self) -> bool:
        """Тест статистики кэша"""
        try:
            response = self.session.get(f"{self.base_url}/glossary/cache-stats")
            success = response.status_code == 200
            if success:
                data = response.json()
                memory_usage = data.get("used_memory", "N/A")
                self.log_test("Cache Stats", success, f"Memory: {memory_usage}")
            else:
                self.log_test("Cache Stats", False, f"Status: {response.status_code}")
            return success
        except Exception as e:
            self.log_test("Cache Stats", False, f"Error: {e}")
            return False
            
    def test_project_creation(self) -> tuple[bool, int]:
        """Тест создания проекта"""
        try:
            project_data = {
                "name": f"Test Project {int(time.time())}",
                "genre": "fantasy"
            }
            response = self.session.post(f"{self.base_url}/projects/", json=project_data)
            success = response.status_code == 201
            project_id = None
            if success:
                data = response.json()
                project_id = data.get("id")
                self.log_test("Project Creation", success, f"Project ID: {project_id}")
            else:
                self.log_test("Project Creation", False, f"Status: {response.status_code}")
            return success, project_id
        except Exception as e:
            self.log_test("Project Creation", False, f"Error: {e}")
            return False, None
            
    def test_chapter_creation(self, project_id: int) -> tuple[bool, int]:
        """Тест создания главы"""
        try:
            chapter_data = {
                "title": "Test Chapter",
                "original_text": "This is a test chapter with some content for analysis."
            }
            response = self.session.post(f"{self.base_url}/projects/{project_id}/chapters", json=chapter_data)
            success = response.status_code == 201
            chapter_id = None
            if success:
                data = response.json()
                chapter_id = data.get("id")
                self.log_test("Chapter Creation", success, f"Chapter ID: {chapter_id}")
            else:
                self.log_test("Chapter Creation", False, f"Status: {response.status_code}")
            return success, chapter_id
        except Exception as e:
            self.log_test("Chapter Creation", False, f"Error: {e}")
            return False, None
            
    def test_chapter_analysis(self, chapter_id: int) -> bool:
        """Тест анализа главы"""
        try:
            response = self.session.post(f"{self.base_url}/processing/chapters/{chapter_id}/analyze")
            success = response.status_code == 200
            if success:
                data = response.json()
                terms_count = data.get("extracted_terms", 0)
                self.log_test("Chapter Analysis", success, f"Extracted {terms_count} terms")
            else:
                error_detail = response.text if response.status_code != 200 else ""
                self.log_test("Chapter Analysis", False, f"Status: {response.status_code}, Error: {error_detail}")
            return success
        except Exception as e:
            self.log_test("Chapter Analysis", False, f"Error: {e}")
            return False
            
    def test_chapter_translation(self, chapter_id: int) -> bool:
        """Тест перевода главы"""
        try:
            response = self.session.post(f"{self.base_url}/translation/chapters/{chapter_id}/translate")
            success = response.status_code == 200
            if success:
                data = response.json()
                has_translation = bool(data.get("translated_text"))
                self.log_test("Chapter Translation", success, f"Translation created: {has_translation}")
            else:
                error_detail = response.text if response.status_code != 200 else ""
                self.log_test("Chapter Translation", False, f"Status: {response.status_code}, Error: {error_detail}")
            return success
        except Exception as e:
            self.log_test("Chapter Translation", False, f"Error: {e}")
            return False
            
    def test_download_endpoint(self, project_id: int, chapter_id: int) -> bool:
        """Тест endpoint для скачивания"""
        try:
            response = self.session.get(f"{self.base_url}/projects/{project_id}/chapters/{chapter_id}/download")
            success = response.status_code == 200
            if success:
                content_length = len(response.content)
                self.log_test("Download Endpoint", success, f"Content length: {content_length} bytes")
            else:
                self.log_test("Download Endpoint", False, f"Status: {response.status_code}")
            return success
        except Exception as e:
            self.log_test("Download Endpoint", False, f"Error: {e}")
            return False
            
    def test_updated_api_usage(self) -> bool:
        """Тест обновленной статистики API после операций"""
        try:
            response = self.session.get(f"{self.base_url}/glossary/api-usage")
            success = response.status_code == 200
            if success:
                data = response.json()
                total_usage = sum(key.get("usage_today", 0) for key in data.get("keys", []))
                self.log_test("Updated API Usage", success, f"Total usage: {total_usage}")
            else:
                self.log_test("Updated API Usage", False, f"Status: {response.status_code}")
            return success
        except Exception as e:
            self.log_test("Updated API Usage", False, f"Error: {e}")
            return False
            
    def run_comprehensive_test(self):
        """Запускает комплексный тест всех функций"""
        print("🚀 Запуск комплексного тестирования Light Novel NLP")
        print("=" * 60)
        
        # 1. Базовые проверки
        if not self.test_health_check():
            print("❌ Health check failed, stopping tests")
            return
            
        self.test_api_usage_stats()
        self.test_cache_stats()
        
        # 2. Создание проекта и главы
        project_success, project_id = self.test_project_creation()
        if not project_success or not project_id:
            print("❌ Project creation failed, stopping tests")
            return
            
        chapter_success, chapter_id = self.test_chapter_creation(project_id)
        if not chapter_success or not chapter_id:
            print("❌ Chapter creation failed, stopping tests")
            return
            
        # 3. Анализ и перевод
        print("\n📊 Тестирование анализа и перевода...")
        analysis_success = self.test_chapter_analysis(chapter_id)
        
        if analysis_success:
            # Ждем немного для обработки
            time.sleep(2)
            translation_success = self.test_chapter_translation(chapter_id)
            
            if translation_success:
                # 4. Тест скачивания
                print("\n📥 Тестирование скачивания...")
                self.test_download_endpoint(project_id, chapter_id)
        
        # 5. Финальная проверка статистики
        print("\n📈 Финальная проверка статистики...")
        self.test_updated_api_usage()
        
        # 6. Итоговая статистика
        print("\n" + "=" * 60)
        print("📋 ИТОГОВАЯ СТАТИСТИКА ТЕСТОВ")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["success"])
        failed_tests = total_tests - passed_tests
        
        print(f"Всего тестов: {total_tests}")
        print(f"✅ Успешно: {passed_tests}")
        print(f"❌ Провалено: {failed_tests}")
        print(f"📊 Успешность: {(passed_tests/total_tests)*100:.1f}%")
        
        if failed_tests > 0:
            print("\n❌ ПРОБЛЕМНЫЕ ТЕСТЫ:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"  - {result['test']}: {result['details']}")
        else:
            print("\n🎉 Все тесты прошли успешно!")

if __name__ == "__main__":
    tester = ComprehensiveTester()
    tester.run_comprehensive_test()
