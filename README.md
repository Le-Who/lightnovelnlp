# 📚 Light Novel NLP Translator

> Профессиональная система автоматизированного перевода и анализа ранобэ (Light Novels) с использованием Google Gemini AI.
> Проект реализует подход **RAG (Retrieval-Augmented Generation)** для сохранения контекста и терминологии на протяжении всего произведения.

![Project Status](https://img.shields.io/badge/Status-Active-success)
![Python](https://img.shields.io/badge/Backend-FastAPI-blue)
![React](https://img.shields.io/badge/Frontend-React%20%7C%20Vite-cyan)
![AI](https://img.shields.io/badge/AI-Google%20Gemini%203.x-orange)
![Architecture](https://img.shields.io/badge/Architecture-v2.3.2-purple)
![Testing](https://img.shields.io/badge/Testing-AAA%20Pattern%20%7C%20130%2B%20Tests-brightgreen)
![Linting](https://img.shields.io/badge/Code%20Quality-Ruff%20%7C%20ESLint-yellow)

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
*   **Пакетная загрузка**: Импорт книг из `.txt` и `.epub` файлов с автоматической разбивкой на главы (по регулярным выражениям для txt, по структуре spine для epub).
*   **Per-project Gemini настройки**: Каждый проект может переопределить модель, уровень thinking, язык и порог эмбеддинга для extraction/translation/summarization.
*   **Динамический выбор языков**: Настраиваемая пара `source_language` / `target_language` на уровне проекта (zh/ja/ko/en → ru/en).
*   **Автокалибровка порога эмбеддинга**: `POST /projects/{id}/calibrate-threshold` вычисляет оптимальный порог cosine similarity по распределению попарных расстояний.

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
*   **AI Review Feedback Loop**: Отдельный режим, где нейросеть (AI Reviewer) читает перевод и оригинал, собирая нарушения глоссария в структурированный JSON.
*   **Auto-Correction**: При нахождении нарушений терминологии автоматически запускается корректировочный проход (retranslation) с внедрением исправлений.
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
| `GET` | `/api/v1/projects/{id}/settings` | Настройки модели/thinking/языков для проекта |
| `PATCH` | `/api/v1/projects/{id}/settings` | Обновить настройки проекта |
| `POST` | `/api/v1/projects/{id}/calibrate-threshold` | Автокалибровка порога эмбеддинга |
| `GET` | `/api/v1/projects/models/available` | Список доступных моделей и языков для UI |

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
│   ├── alembic/          # Миграции БД (016 миграций)
│   ├── scripts/          # Утилиты (calibrate_threshold.py)
│   └── tests/            # Pytest suite (AAA pattern, 130+ тестов)
├── frontend/
│   ├── src/
│   │   ├── components/   # UI Компоненты (ChapterManager, GlossaryEditor)
│   │   ├── pages/        # Страницы (Dashboard, Project)
│   │   └── services/     # API клиент (Axios)
└── docker-compose.yml
```

---

## 🧪 Тестирование (Testing Architecture)

Проект использует паттерн **AAA (Arrange-Act-Assert)** для всех тестов, гарантируя высокую надежность и изоляцию стейта.

Запуск осуществляется через `pytest`. Тесты разделены на маркеры:

```bash
cd backend

# Локальный запуск: unit и SQLite-интеграционные тесты (быстро, ~6 сек)
pytest

# Запуск только unit тестов (без базы)
pytest -m unit

# Интеграционные тесты (FastAPI + TestClient + in-memory SQLite)
pytest -m integration

# Полный прогон с pgvector (используется в CI)
pytest -m postgres --postgres-url=postgresql://user:pass@localhost:5432/testdb
```

*Все `postgres` тесты автоматически пропускаются при локальном запуске без явной передачи `--postgres-url`.*

---

## 🔧 Конфигурация (.env)

### Подключения

**Supabase PostgreSQL** — использовать **Session pooler** (порт **5432**):
```
# Supabase Dashboard → Project Settings → Database → Connection String → URI
# Выбрать: Session mode (порт 5432), НЕ Transaction mode (6543)
DATABASE_URL=postgresql://postgres.[ref]:[PASSWORD]@aws-0-eu-west-1.pooler.supabase.com:5432/postgres
```

**Redis Labs** — брать из Redis Cloud Console:
```
REDIS_URL=redis://default:[PASSWORD]@[HOST]:[PORT]
```

---

### Маппинг Старых → Новых Переменных (v1→v2)

| Старая переменная | Статус | Замена / Примечание |
|-------------------|--------|---------------------|
| `DATABASE_URL` | ✅ Без изменений | — |
| `REDIS_URL` | ✅ Без изменений | — |
| `GEMINI_API_KEYS_RAW` | ✅ Без изменений | — |
| `ENVIRONMENT` | ✅ Без изменений | — |
| `ALLOWED_ORIGINS_RAW` | ✅ Без изменений | — |
| `GEMINI_API_RESET_TIMEZONE` | ✅ Без изменений | — |
| `UPSTASH_REDIS_REST_URL` | ⚠️ Опционально | Только для Upstash REST API |
| `UPSTASH_REDIS_REST_TOKEN` | ⚠️ Опционально | Только для Upstash REST API |
| `GEMINI_API_LIMIT_PER_KEY` | ❌ Удалено | → `GEMINI_RPD_LIMITS` per-model |
| `GEMINI_API_LIMIT_THRESHOLD_PERCENT` | ❌ Удалено | Не используется |
| `GEMINI_MAX_OUTPUT_TOKENS` | ❌ Удалено | → `GEMINI_MAX_TOKENS_*` per-task |

---

### Обязательные
| Переменная | Описание |
|------------|----------|
| `DATABASE_URL` | PostgreSQL connection string (Session mode, port 5432) |
| `REDIS_URL` | Redis connection string |
| `GEMINI_API_KEYS_RAW` | Ключи Google AI через запятую (каждый ключ = отдельный GCP проект) |

### Приложение
| Переменная | Default | Описание |
|------------|---------|----------|
| `ENVIRONMENT` | `development` | `development` или `production` |
| `ALLOWED_ORIGINS_RAW` | `http://localhost:3000,http://localhost:5173` | CORS origins через запятую |

### Gemini — Ротация Ключей
| Переменная | Default | Описание |
|------------|---------|----------|
| `GEMINI_API_RESET_TIMEZONE` | `America/Los_Angeles` | Таймзона сброса RPD (Google сбрасывает в полночь по Лос-Анджелесу) |
| `GEMINI_API_COOLDOWN_MINUTES` | `5` | Мягкий таймаут ключа после 429 (в минутах) |

### Gemini — Модели по Задаче
| Переменная | Default | Описание |
|------------|---------|----------|
| `GEMINI_MODEL_EXTRACTION` | `gemini-3.1-flash-lite-preview` | Модель для extraction |
| `GEMINI_MODEL_TRANSLATION` | `gemini-3-flash-preview` | Модель для перевода |
| `GEMINI_MODEL_SUMMARIZATION` | `gemini-3.1-flash-lite-preview` | Модель для суммаризации |
| `GEMINI_MODEL_RELATIONSHIPS` | `gemini-3.1-flash-lite-preview` | Модель для анализа связей |
| `GEMINI_MODEL_EMBEDDING` | `gemini-embedding-2-preview` | Модель эмбеддингов (768-dim MRL) |
| `GEMINI_FALLBACK_MODELS` | `gemini-2.5-flash,gemini-flash-latest` | Резервные модели через запятую |

### Gemini — Уровень Мышления
| Переменная | Default | Допустимые значения |
|------------|---------|---------------------|
| `GEMINI_THINKING_EXTRACTION` | `medium` | `minimal` / `low` / `medium` / `high` |
| `GEMINI_THINKING_TRANSLATION` | `high` | `minimal` / `low` / `medium` / `high` |
| `GEMINI_THINKING_SUMMARIZATION` | `medium` | `minimal` / `low` / `medium` / `high` |
| `GEMINI_THINKING_RELATIONSHIPS` | `medium` | `minimal` / `low` / `medium` / `high` |

> Для Gemini 2.5.x `thinkingBudget` устанавливается автоматически: `minimal`→0, `low`→1024, `medium`→8192, `high`→24576.

### Gemini — Rate Limits
| Переменная | Default | Формат |
|------------|---------|--------|
| `GEMINI_RPM_LIMITS` | `gemini-3-flash-preview=10, gemini-3.1-flash-lite-preview=15, ...` | `"model=N, model=M"` |
| `GEMINI_RPD_LIMITS` | `gemini-3-flash-preview=500, gemini-3.1-flash-lite-preview=1000, ...` | `"model=N, model=M"` |

### Gemini — Токены по Задаче
| Переменная | Default | Описание |
|------------|---------|----------|
| `GEMINI_MAX_TOKENS_EXTRACTION` | `8192` | Макс. токенов ответа для extraction |
| `GEMINI_MAX_TOKENS_TRANSLATION` | `65536` | Макс. токенов для перевода |
| `GEMINI_MAX_TOKENS_SUMMARIZATION` | `2048` | Макс. токенов для суммаризации |
| `GEMINI_MAX_TOKENS_RELATIONSHIPS` | `4096` | Макс. токенов для анализа связей |
| `GEMINI_MAX_TOKENS_DEFAULT` | `8192` | Fallback |

### Опционально
| Переменная | Описание |
|------------|----------|
| `UPSTASH_REDIS_REST_URL` | Upstash REST endpoint (только если используется Upstash) |
| `UPSTASH_REDIS_REST_TOKEN` | Upstash REST token (только если используется Upstash) |

---

### Шаблон для Production

```env
# ── Обязательные ───────────────────────────────────────────
DATABASE_URL=postgresql://postgres.[ref]:[PWD]@aws-0-eu-west-1.pooler.supabase.com:5432/postgres
REDIS_URL=redis://default:[PWD]@[HOST]:[PORT]
GEMINI_API_KEYS_RAW=AIza...,AIza...,AIza...

# ── Приложение ─────────────────────────────────────────────
ENVIRONMENT=production
ALLOWED_ORIGINS_RAW=https://your-frontend.northflank.app

# ── Gemini ─────────────────────────────────────────────────
GEMINI_API_RESET_TIMEZONE=America/Los_Angeles
GEMINI_API_COOLDOWN_MINUTES=5
GEMINI_RPM_LIMITS=gemini-3-flash-preview=10,gemini-3.1-flash-lite-preview=15
GEMINI_RPD_LIMITS=gemini-3-flash-preview=500,gemini-3.1-flash-lite-preview=1000
```

