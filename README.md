# 📚 Light Novel NLP Translator

> Профессиональная система автоматизированного перевода и анализа ранобэ (Light Novels) с использованием Google Gemini AI.
> Проект реализует подход **RAG (Retrieval-Augmented Generation)** для сохранения контекста и терминологии на протяжении всего произведения.

![Project Status](https://img.shields.io/badge/Status-Active-success)
![Python](https://img.shields.io/badge/Backend-FastAPI-blue)
![React](https://img.shields.io/badge/Frontend-React%20%7C%20Vite-cyan)
![AI](https://img.shields.io/badge/AI-Google%20Gemini-orange)

---

## 🧠 Ментальная Карта Проекта

Проект решает главную проблему машинного перевода художественных текстов — **потерю контекста**.
Вместо прямого перевода, система работает в три этапа:
1.  **Анализ (Analysis)**: Чтение текста и выявление именованных сущностей (имена, ранги, локации, навыки).
2.  **Глоссарий (Glossary)**: Формирование базы знаний проекта, где пользователь может зафиксировать правильный перевод терминов.
3.  **Синтез (Translation)**: Перевод текста с жестким требованием использования утвержденных терминов из глоссария.

### Архитектура
*   **Frontend**: React SPA (Vite + TailwindCSS) для управления проектами и чтения.
*   **Backend**: FastAPI (Python) для REST API.
*   **Async Core**: Celery + Redis для очереди задач (анализ и перевод могут занимать минуты).
*   **Database**: PostgreSQL для хранения текстов и связей.

---

## 🚀 Основной Функционал

### 1. Управление Проектами
*   Создание проектов с указанием жанра (Xianxia, LitRPG, Romance и т.д.) для настройки промптов нейросети.
*   **Пакетная загрузка**: Импорт книг из `.txt` файлов с автоматической разбивкой на главы по регулярным выражениям.

### 2. Интеллектуальный Анализ (NLP)
*   **Entity Extraction**: Автоматический поиск неизвестных терминов в новых главах.
*   **Частотный анализ**: Подсчет, как часто термин встречается в тексте, для приоритизации перевода.
*   **Контекст**: Определение типа термина (Person, Location, Organization, Ability).

### 3. Перевод с Контекстом
*   Использование API Google Gemini (модели gemini-3-flash, gemini-2.5-flash, gemini-flash-latest).
*   Вставка релевантной части глоссария в контекст запроса на перевод.
*   Сохранение HTML-разметки (если есть) или чистого текста.

### 4. Рецензирование и Качество
*   **AI Review**: Отдельный режим, где нейросеть читает перевод и оригинал, указывая на стилистические ошибки или пропущенные термины.
*   Ручное редактирование перевода и глоссария.

---

## 🛠 Установка и Запуск

### Предварительные требования
*   Docker & Docker Compose (Рекомендуется)
*   ИЛИ Python 3.10+ и Node.js 18+
*   PostgreSQL
*   Redis
*   Ключ Google Gemini API

### Вариант 1: Локальный запуск (Development)

#### Backend
```bash
cd backend
# Создание виртуального окружения (рекомендуется)
python -m venv venv
# Windows:
venv\Scripts\activate
# Linux/Mac:
# source venv/bin/activate

# Установка зависимостей
pip install -r requirements.txt

# Настройка переменных окружения
# Создайте файл .env в папке backend или задайте переменные:
# export DATABASE_URL="postgresql://user:pass@localhost/dbname"
# export REDIS_URL="redis://localhost:6379"
# export GEMINI_API_KEY="your_key"

# Запуск сервера
uvicorn app.main:app --reload --port 8000
```
*Заметьте: При первом запуске приложение попытается автоматически создать таблицы в БД.*

#### Frontend
```bash
cd frontend
npm install
npm run dev
```
Интерфейс будет доступен по адресу: `http://localhost:5173`

#### Celery Worker (для асинхронных задач)
Обязательно запустите воркера в отдельном терминале (из папки backend):
```bash
# Windows (нужен eventlet или gevent, так как Celery официально не поддерживает Windows полностью, или используйте WSL)
celery -A app.worker.celery_app worker --loglevel=info -P gevent

# Linux/Mac/WSL
celery -A app.worker.celery_app worker --loglevel=info
```

### Вариант 2: Docker Compose (Рекомендуется)
```bash
docker-compose up --build -d
```
Это поднимет: Frontend, Backend, Postgres, Redis и Celery Worker.

---

## 📡 API Endpoints (Полный Список)

Полная интерактивная документация (Swagger UI) доступна по адресу `/docs` (например, `http://localhost:8000/docs`).

### 📂 Projects (Проекты)
| Метод | Путь | Описание |
|-------|------|----------|
| `GET` | `/api/v1/projects/` | Получить список всех проектов |
| `POST` | `/api/v1/projects/` | Создать новый проект |
| `GET` | `/api/v1/projects/{id}` | Получить детали проекта |
| `DELETE` | `/api/v1/projects/{id}` | Удалить проект |
| `POST` | `/api/v1/projects/{id}/upload_chapters` | Пакетная загрузка глав из файла |

### 📖 Chapters (Главы)
| Метод | Путь | Описание |
|-------|------|----------|
| `GET` | `/api/v1/projects/{id}/chapters` | Получить список глав проекта |
| `POST` | `/api/v1/projects/{id}/chapters` | Создать главу вручную |
| `GET` | `/api/v1/projects/chapters/{id}` | Получить текст и данные главы |
| `PUT` | `/api/v1/projects/chapters/{id}` | Обновить текст главы |
| `DELETE` | `/api/v1/projects/chapters/{id}` | Удалить главу |

### 🧠 Processing (Анализ)
| Метод | Путь | Описание |
|-------|------|----------|
| `POST` | `/api/v1/processing/chapters/{id}/analyze` | Запустить синхронный анализ |
| `POST` | `/api/v1/processing/chapters/{id}/analyze-async` | Запустить фоновый анализ терминов |

### 🌏 Translation (Перевод)
| Метод | Путь | Описание |
|-------|------|----------|
| `POST` | `/api/v1/translation/chapters/{id}/translate` | Запустить перевод главы |
| `POST` | `/api/v1/translation/chapters/{id}/translate-async` | Фоновый перевод |
| `GET` | `/api/v1/translation/chapters/{id}/translation-preview` | Предпросмотр перевода |
| `POST` | `/api/v1/translation/chapters/{id}/review` | Запросить AI рецензию на перевод |
| `GET` | `/api/v1/translation/chapters/{id}/review` | Получить готовую рецензию |

### 📚 Glossary (Глоссарий)
| Метод | Путь | Описание |
|-------|------|----------|
| `GET` | `/api/v1/glossary/{project_id}/terms` | Список терминов глоссария |
| `POST` | `/api/v1/glossary/terms` | Добавить термин вручную |
| `PUT` | `/api/v1/glossary/terms/{id}` | Изменить термин |
| `POST` | `/api/v1/glossary/terms/{id}/approve` | Подтвердить (правильность) термина |
| `DELETE` | `/api/v1/glossary/terms/{id}` | Удалить термин |

### 📦 Batch (Пакетные операции)
| Метод | Путь | Описание |
|-------|------|----------|
| `GET` | `/api/v1/batch/{project_id}/jobs` | Список пакетных задач |
| `GET` | `/api/v1/batch/jobs/{job_id}` | Статус конкретной задачи |
| `POST` | `/api/v1/batch/{project_id}/analyze-chapters` | Анализировать ВСЕ главы проекта |
| `POST` | `/api/v1/batch/{project_id}/translate-chapters` | Перевести ВСЕ главы проекта |


## 📂 Структура Проекта

```
.
├── backend/
│   ├── app/
│   │   ├── api/          # REST контроллеры (Batch, Projects, Glossary)
│   │   ├── core/         # Конфигурация (Config, Logging)
│   │   ├── models/       # SQLAlchemy модели (Project, Chapter, GlossaryTerm)
│   │   ├── services/     # Бизнес-логика (Gemini Client, Translation Service)
│   │   └── tasks/        # Celery задачи (Async translation/analysis)
│   ├── alembic/          # Миграции БД
│   └── tests/            # Pytest
├── frontend/
│   ├── src/
│   │   ├── components/   # UI Компоненты (ChapterManager, GlossaryEditor)
│   │   ├── pages/        # Страницы (Dashboard, Project)
│   │   └── services/     # API клиент (Axios)
└── docker-compose.yml
```

---

## 🔧 Конфигурация (.env)

| Переменная | Описание |
|------------|----------|
| `DATABASE_URL` | Строка подключения к PostgreSQL |
| `GEMINI_API_KEY` | Ключ или список ключей (через запятую) для Google AI |
| `REDIS_URL` | Адрес Redis сервера |
| `ENVIRONMENT` | `development` или `production` |
