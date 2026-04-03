# 📚 Light Novel NLP Translator

> Профессиональная система автоматизированного перевода и анализа ранобэ (Light Novels) с использованием Google Gemini AI.
> Проект реализует подход **RAG (Retrieval-Augmented Generation)** для сохранения контекста и терминологии на протяжении всего произведения.

![Project Status](https://img.shields.io/badge/Status-Active-success)
![Python](https://img.shields.io/badge/Backend-FastAPI-blue)
![React](https://img.shields.io/badge/Frontend-React%20%7C%20Vite-cyan)
![AI](https://img.shields.io/badge/AI-Google%20Gemini%203.x-orange)
![Architecture](https://img.shields.io/badge/Architecture-v2.0-purple)

---

## 🎨 UI & Design Systems

Проект поддерживает сменные темы оформления, с основным фокусом на "Neon Operator" — высокотехнологичный киберпанк-интерфейс.

### Neon Operator Theme (Default)
> *"High contrast, Data-Dense, Glowing"*

*   **Command Center Dashboard**: Главная панель выполнена в стиле терминала управления, с "живыми" статусами и метриками.
*   **Mission Briefing Projects**: Страница проекта стилизована под брифинг миссии с HUD-элементами.
*   **Terminal Reader**: Режим чтения имитирует хакерский терминал с моноширинными шрифтами и CRT-эффектами для максимального погружения.
*   **Технологии**: Tailwind CSS v4, CSS Variables, Lucide Icons, Glassmorphism.

---

## 🧠 Ментальная Карта Проекта

Проект решает главную проблему машинного перевода художественных текстов — **потерю контекста**.
Вместо прямого перевода, система работает в три этапа:
1.  **Анализ (Analysis)**: Чтение текста и выявление именованных сущностей (имена, ранги, локации, навыки).
2.  **Глоссарий (Glossary)**: Формирование базы знаний проекта, где пользователь может зафиксировать правильный перевод терминов.
3.  **Синтез (Translation)**: Перевод текста с жестким требованием использования утвержденных терминов из глоссария.

### Архитектура (v2.0)
*   **Frontend**: React SPA (Vite + TailwindCSS) для управления проектами и чтения.
*   **Backend**: FastAPI (Python) для REST API.
*   **AI Engine**: Google Gemini 3.x / 2.5.x с автоопределением ThinkingConfig и per-task model routing.
*   **Async Core**: Celery + Redis для очереди задач (анализ и перевод могут занимать минуты).
*   **Database**: PostgreSQL + pgvector для хранения текстов, связей и семантических эмбеддингов.
*   **Rate Limiting**: Per-key per-model RPM/RPD трекинг через Redis с ротацией ключей и soft cooldown.

---

## 🚀 Основной Функционал

### 1. Управление Проектами
*   Создание проектов с указанием жанра (Xianxia, LitRPG, Romance и т.д.) для настройки промптов нейросети.
*   **Пакетная загрузка**: Импорт книг из `.txt` файлов с автоматической разбивкой на главы по регулярным выражениям.
*   **Per-project Gemini настройки**: Каждый проект может переопределить модель и уровень thinking для extraction/translation/summarization.

### 2. Интеллектуальный Анализ (NLP)
*   **Entity Extraction**: Автоматический поиск неизвестных терминов в новых главах (task_type="extraction").
*   **Частотный анализ**: Подсчет, как часто термин встречается в тексте, для приоритизации перевода.
*   **Контекст**: Определение типа термина (Person, Location, Organization, Ability).
*   **Semantic Memory (LTM)**: pgvector эмбеддинги (gemini-embedding-2-preview, 768-dim MRL) для семантического поиска связанных терминов.

### 3. Перевод с Контекстом
*   **Task-aware model routing**: Разные модели для разных стадий (gemini-3.1-flash-lite для extraction, gemini-3-flash для translation).
*   **ThinkingConfig autodetect**: Gemini 3.x → thinkingLevel, Gemini 2.5.x → thinkingBudget.
*   Вставка релевантной части глоссария в контекст запроса на перевод.
*   Сохранение HTML-разметки (если есть) или чистого текста.

### 4. Рецензирование и Качество
*   **AI Review**: Отдельный режим, где нейросеть читает перевод и оригинал, указывая на стилистические ошибки или пропущенные термины.
*   Ручное редактирование перевода и глоссария.

### 5. Надежность и Масштабируемость
*   **Thread-safe GeminiClient**: Ephemeral `genai.Client()` per-request, без мутабельного состояния.
*   **Multi-key rotation**: Каждый ключ = отдельный GCP проект с независимыми лимитами.
*   **Soft cooldown**: 429 → 5 мин блокировка ключа (вместо 24h), автоматический fallback на следующий ключ/модель.
*   **Stage-aware observability**: `[GEMINI:{task_type}]` логирование, per-model RPM/RPD/stage Redis counters.

---

## 🛠 Установка и Запуск

### Предварительные требования
*   Docker & Docker Compose (Рекомендуется)
*   ИЛИ Python 3.10+ и Node.js 18+
*   PostgreSQL (+ pgvector extension для semantic search)
*   Redis
*   Один или несколько ключей Google Gemini API

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

# Настройка переменных окружения (см. таблицу ниже)
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
# Windows (нужен eventlet или gevent)
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
| `GET` | `/api/v1/projects/{id}/settings` | Настройки модели/thinking для проекта |
| `PATCH` | `/api/v1/projects/{id}/settings` | Обновить настройки проекта |
| `GET` | `/api/v1/projects/models/available` | Список доступных моделей для UI |

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
| `GET` | `/api/v1/glossary/api-usage` | Статистика использования API ключей |

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
│   │   ├── core/         # Конфигурация (Config, Logging, NLP Pipeline)
│   │   ├── models/       # SQLAlchemy модели (Project, Chapter, GlossaryTerm)
│   │   ├── services/     # Бизнес-логика (GeminiClient v2, EmbeddingService, CacheService)
│   │   └── tasks/        # Celery задачи (Async translation/analysis)
│   ├── alembic/          # Миграции БД (015 миграций)
│   ├── scripts/          # Утилиты (calibrate_threshold.py)
│   └── tests/            # Pytest (77 тестов)
├── frontend/
│   ├── src/
│   │   ├── components/   # UI Компоненты (ChapterManager, GlossaryEditor)
│   │   ├── pages/        # Страницы (Dashboard, Project)
│   │   └── services/     # API клиент (Axios)
└── docker-compose.yml
```

---

## 🔧 Конфигурация (.env)

### Обязательные
| Переменная | Описание |
|------------|----------|
| `DATABASE_URL` | Строка подключения к PostgreSQL |
| `REDIS_URL` | Адрес Redis сервера |
| `GEMINI_API_KEYS_RAW` | Ключи Google AI (через запятую) |

### Gemini — Per-task модели (опционально)
| Переменная | Default | Описание |
|------------|---------|----------|
| `GEMINI_MODEL_EXTRACTION` | `gemini-3.1-flash-lite-preview` | Модель для extraction |
| `GEMINI_MODEL_TRANSLATION` | `gemini-3-flash-preview` | Модель для перевода |
| `GEMINI_MODEL_SUMMARIZATION` | `gemini-3.1-flash-lite-preview` | Модель для саммари |
| `GEMINI_MODEL_RELATIONSHIPS` | `gemini-3.1-flash-lite-preview` | Модель для связей |
| `GEMINI_MODEL_EMBEDDING` | `gemini-embedding-2-preview` | Модель для эмбеддингов |

### Gemini — Per-task thinking levels
| Переменная | Default | Описание |
|------------|---------|----------|
| `GEMINI_THINKING_EXTRACTION` | `medium` | Уровень thinking для extraction |
| `GEMINI_THINKING_TRANSLATION` | `high` | Уровень thinking для перевода |

### Gemini — Rate Limiting
| Переменная | Default | Формат |
|------------|---------|--------|
| `GEMINI_RPM_LIMITS` | `gemini-3-flash-preview=10, ...` | `"model=limit, model=limit"` |
| `GEMINI_RPD_LIMITS` | `gemini-3-flash-preview=500, ...` | `"model=limit, model=limit"` |
| `GEMINI_API_COOLDOWN_MINUTES` | `5` | Минуты мягкого cooldown при 429 |
| `GEMINI_API_RESET_TIMEZONE` | `America/Los_Angeles` | Таймзона сброса дневных лимитов |
