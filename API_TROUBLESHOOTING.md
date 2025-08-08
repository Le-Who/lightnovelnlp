# 🔧 Устранение неполадок API

## 📋 Обзор проблем

Этот документ содержит решения для наиболее распространенных проблем с API Light Novel NLP.

## 🚨 Известные проблемы и решения

### 1. Проблема: `/docs` возвращает "Not Found"

**Причина**: Ссылка на Swagger UI ведет на frontend домен вместо backend.

**Решение**: ✅ **ИСПРАВЛЕНО**
- Обновлена ссылка в `DashboardPage.jsx` для правильного перенаправления на backend
- Теперь ссылка динамически формируется: `https://lightnovel-backend.onrender.com/docs`

**Проверка**: Откройте `https://lightnovel-frontend.onrender.com` и нажмите "📚 Swagger Documentation"

     ### 2. Проблема: "Field required: project_id" при создании главы

     **Причина**: Конфликт между `ChapterCreate` schema (ожидает `project_id` в теле) и API endpoint (получает `project_id` из URL).

     **Решение**: ✅ **ИСПРАВЛЕНО**
     - Убран `project_id` из `ChapterCreate` schema
     - API endpoint: `POST /projects/{project_id}/chapters`
     - Тело запроса: `{"title": "...", "original_text": "..."}`

     **Проверка**: Используйте API Tools → "Создать главу" с правильным ID проекта

### 3. Проблема: "Method Not Allowed" при получении терминов

**Причина**: Неправильный endpoint для получения терминов.

**Решение**: ✅ **ИСПРАВЛЕНО**
- Правильный endpoint: `GET /glossary/terms/{project_id}`
- Обновлен в `api-tools.html`

**Проверка**: Используйте API Tools → "Получить термины" с ID проекта

### 4. Проблема: "Not Found" при анализе главы

**Причина**: Неправильный endpoint для анализа главы.

**Решение**: ✅ **ИСПРАВЛЕНО**
- Правильный endpoint: `POST /processing/chapters/{chapter_id}/analyze`
- Обновлен в `api-tools.html`

**Проверка**: Используйте API Tools → "Анализировать главу" с ID главы

     ### 5. Проблема: "NotNullViolation: null value in column project_id"

     **Причина**: `project_id` не парсится корректно из формы, приводя к `null` значению.

     **Решение**: ✅ **ИСПРАВЛЕНО**
     - Добавлена валидация `parseInt()` в `api-tools.html`
     - Проверка на `isNaN()` для всех ID полей
     - API endpoint: `POST /glossary/terms`
     - Тело запроса должно содержать валидный `project_id`

     **Проверка**: Используйте API Tools → "Создать термин" с числовым ID проекта

### 6. Проблема: Redis "Connection closed by server"

**Причина**: Upstash Redis закрывает соединения после периода неактивности.

**Решение**: ✅ **ИСПРАВЛЕНО**
- Добавлена автоматическая переподключение в `CacheService`
- Улучшена обработка ошибок Redis

**Проверка**: Используйте API Tools → "Статистика кэша"

### 7. Проблема: "UndefinedColumn: column glossary_terms.approved_at does not exist"

**Причина**: База данных не синхронизирована с моделью SQLAlchemy. Колонка `approved_at` была добавлена в модель, но не создана в базе данных.

**Решение**: ✅ **ТРЕБУЕТСЯ МИГРАЦИЯ**
- Выполните миграцию базы данных (см. DEPLOYMENT.md, раздел 4.4)
- Вариант A: `python run_migration.py` (через Alembic)
- Вариант B: `ALTER TABLE glossary_terms ADD COLUMN IF NOT EXISTS approved_at TIMESTAMP;` (прямой SQL)

**Проверка**: После миграции используйте API Tools → "Управление терминами"

### 8. Проблема: "UndefinedColumn: column chapters.processed_at does not exist"

**Причина**: База данных не синхронизирована с моделью SQLAlchemy. Колонка `processed_at` была добавлена в модель `Chapter`, но не создана в базе данных.

**Решение**: ✅ **ТРЕБУЕТСЯ МИГРАЦИЯ**
- Выполните миграцию базы данных (см. DEPLOYMENT.md, раздел 4.4)
- Вариант A: `python run_migration.py` (через Alembic)
- Вариант B: `ALTER TABLE chapters ADD COLUMN IF NOT EXISTS processed_at TIMESTAMP;` (прямой SQL)

**Проверка**: После миграции используйте API Tools → "Получить главы" и "Создать главу"

### 9. Проблема: "UndefinedColumn: column glossary_versions.version_name does not exist"

**Причина**: База данных не синхронизирована с моделью SQLAlchemy. Колонки `version_number` и `terms_snapshot` были переименованы в `version_name` и `terms_data` в модели, но не обновлены в базе данных.

**Решение**: ✅ **ТРЕБУЕТСЯ МИГРАЦИЯ**
- Выполните миграцию базы данных (см. DEPLOYMENT.md, раздел 4.4)
- Вариант A: `python run_migration.py` (через Alembic)
- Вариант B: Выполните SQL-скрипт `backend/sql/update_glossary_versions_table.sql`

**Проверка**: После миграции используйте API Tools → "Удалить проект" (должно работать без ошибок)

## 🧪 Тестирование API

### Автоматическое тестирование

Запустите тестовый скрипт:

```bash
python test_api_endpoints.py
```

### Ручное тестирование

1. **Проверка здоровья API**:
   ```bash
   curl https://lightnovel-backend.onrender.com/health
   ```

2. **Проверка информации**:
   ```bash
   curl https://lightnovel-backend.onrender.com/info
   ```

3. **Создание проекта**:
   ```bash
   curl -X POST https://lightnovel-backend.onrender.com/projects/ \
     -H "Content-Type: application/json" \
     -d '{"name": "Test Project"}'
   ```

4. **Создание главы**:
   ```bash
   curl -X POST https://lightnovel-backend.onrender.com/projects/1/chapters \
     -H "Content-Type: application/json" \
     -d '{"title": "Chapter 1", "original_text": "テストテキスト"}'
   ```

5. **Создание термина**:
   ```bash
   curl -X POST https://lightnovel-backend.onrender.com/glossary/terms \
     -H "Content-Type: application/json" \
     -d '{"project_id": 1, "source_term": "テスト", "translated_term": "Тест", "category": "other"}'
   ```

## 🔍 Диагностика проблем

### Проверка логов

1. **Backend логи** (Render Dashboard):
   - Откройте ваш backend сервис в Render
   - Перейдите в "Logs"
   - Ищите ошибки подключения к БД или Redis

2. **Frontend логи** (Браузер):
   - Откройте Developer Tools (F12)
   - Перейдите в Console
   - Ищите ошибки API запросов

### Проверка переменных окружения

1. **Backend переменные**:
   - `DATABASE_URL` - подключение к PostgreSQL
   - `REDIS_URL` - подключение к Redis
   - `GEMINI_API_KEYS_RAW` - ключи API

2. **Frontend переменные**:
   - `VITE_API_URL` - URL backend API

### Проверка сервисов

1. **PostgreSQL (Neon.tech)**:
   - Проверьте статус "Active"
   - Проверьте лимиты использования

2. **Redis (Upstash.com)**:
   - Проверьте статус "Active"
   - Проверьте количество команд/месяц

3. **Gemini API**:
   - Проверьте лимиты запросов
   - Проверьте валидность ключей

## 🛠️ Полезные инструменты

### API Tools (HTML формы)
- URL: `https://lightnovel-frontend.onrender.com/api-tools.html`
- Функции: Создание проектов, глав, терминов, анализ

### Swagger UI
- URL: `https://lightnovel-backend.onrender.com/docs`
- Функции: Полная документация API, интерактивное тестирование

### Postman Collection
- Файл: `Light_Novel_NLP_API.postman_collection.json`
- Функции: Готовые запросы для всех endpoints

## 📞 Поддержка

Если проблемы не решены:

1. **Проверьте логи** в Render Dashboard
2. **Запустите тестовый скрипт** `test_api_endpoints.py`
3. **Проверьте переменные окружения**
4. **Убедитесь в доступности внешних сервисов**

     ## 🔄 Обновления

     - **2024-01-XX**: Исправлены все известные проблемы с API endpoints
     - **2024-01-XX**: Добавлена автоматическая переподключение к Redis
     - **2024-01-XX**: Улучшена обработка ошибок
     - **2024-01-XX**: Создан тестовый скрипт для диагностики
     - **2024-01-XX**: Исправлен конфликт ChapterCreate schema
     - **2024-01-XX**: Добавлена валидация ID в api-tools.html
     - **2024-01-XX**: Исправлен URL Swagger docs
     - **2024-01-XX**: Добавлены миграции для новых колонок (approved_at, genre, processed_at)
     - **2024-01-XX**: Исправлена миграция для переименования колонок glossary_versions
