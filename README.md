# Light Novel NLP — перевод ранобэ с динамическим глоссарием

Система для анализа и перевода глав ранобэ с применением Gemini API, динамического глоссария и контекстной обработки. Оптимизирована под бесплатные тарифы Render.com, Neon.tech и Upstash.com.

## 🎯 Возможности

- Извлечение терминов (по жанру проекта) и автоматическое утверждение «очевидных» терминов
- Анализ связей между терминами
- Генерация саммари главы и агрегированного саммари по проекту
- Перевод главы с принудительным применением утверждённого глоссария
- Редактирование/удаление глав; скачивание перевода
- Управление терминами: просмотр pending, редактирование перед утверждением, approve/reject, версии глоссария
- Пакетный анализ и пакетный перевод выбранных глав с прогрессом
- Кэширование (переводы, глоссарий, саммари) на Upstash REST с fallback на TCP Redis
- Учёт использования ключей Gemini (ежедневно, с авто‑сбросом по America/Los_Angeles) и глобальный троттлинг 10 req/min

## 🏗 Архитектура

### Backend (FastAPI)
- FastAPI, SQLAlchemy ORM, Pydantic Settings
- Эндпоинты: `projects`, `processing`, `translation`, `glossary`, `batch`
- БД: PostgreSQL (Neon.tech)
- Кэш: Upstash Redis REST (предпочтительно) + TCP fallback
- NLP: Gemini (`gemini-2.5-flash`) через единый клиент с ротацией ключей, дневным учётом и минутным троттлингом
- Миграции: Alembic (автозапуск через Docker Command)

### Frontend
- React + Vite (SPA)
- Страница инструментов `frontend/public/api-tools.html` — полный контроль API без сборки фронтенда
  - Порядок блоков: 1) Системная информация, 2) Управление проектами, 3) Управление главами,
    4) Обработка и перевод, 5) Редактирование и удаление глав, 6) Управление терминами,
    7) Редактирование терминов, 8) Управление глоссарием, 9) Мониторинг

## 🔄 Как работает пайплайн

1) Анализ главы
- Извлечение терминов (1 вызов LLM)
- Анализ связей (1 вызов LLM, если терминов ≥ 2)
- Создание саммари (1 вызов LLM)
- Термины сохраняются (pending/approved), связи записываются, саммари кэшируется

2) Перевод
- Используются только утверждённые термины проекта
- Формируются: глоссарий для промпта, саммари главы и (при наличии) проектное саммари
- Перевод (1 вызов LLM; кэш учитывается)

3) Пакетные операции
- Создаётся `BatchJob` и `BatchJobItem` по главам
- Выполняется последовательно в фоне (FastAPI BackgroundTasks), UI опрашивает статус
- Соблюдается лимит 10 req/min (глобальный счётчик на стороне бэкенда)

## ⚙️ Переменные окружения (ключевые)

- DATABASE_URL — строка подключения Postgres (Neon)
- REDIS_URL — URL Redis (Upstash TCP, как резерв)
- UPSTASH_REDIS_REST_URL / UPSTASH_REDIS_REST_TOKEN — REST Upstash (основной клиент)
- GEMINI_API_KEYS_RAW — список ключей Gemini (строка, парсится в список)
- ALLOWED_ORIGINS_RAW — список доменов для CORS
- GEMINI_API_RESET_TIMEZONE — America/Los_Angeles (Mountain View) для дневного сброса

Подробности см. `ENVIRONMENT_SETUP.md`.

## 🚀 Деплой (бесплатные тарифы)

- Render.com: ручной Docker‑деплой без Blueprint/Background Worker
- Backend Docker Command: выполнить миграции и запустить сервер, например:

```sh
python run_migration.py && uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

- Neon.tech: создать БД и получить `DATABASE_URL`
- Upstash: создать Redis, сохранить REST URL/TOKEN и (опционально) TCP URL

Пошагово: `DEPLOYMENT.md`.

## 🧪 Быстрый старт локально

### Docker Compose
```bash
git clone <repository-url>
cd lightnovelnlp
docker-compose up -d
docker-compose logs -f backend
```

### Без Docker
```bash
# Backend
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload

# Frontend (SPA)
cd frontend
npm install
npm run dev

# API Tools (без сборки):
# открыть frontend/public/api-tools.html в браузере
```

## 📚 Документация и инструменты

- API Tools: `https://lightnovel-frontend.onrender.com/api-tools.html`
- Swagger UI: `https://lightnovel-backend.onrender.com/docs`
- Postman: `Light_Novel_NLP_API.postman_collection.json`
- Траблшутинг: `API_TROUBLESHOOTING.md`
- Процесс авто‑утверждения терминов: `TERM_APPROVAL_PROCESS.md`
- Обновления и улучшения: `IMPROVEMENTS_SUMMARY.md`

## 📈 Мониторинг

- `GET /glossary/api-usage` — агрегированная статистика по ключам Gemini (usage_today, порог, кулдаун)
- `GET /glossary/cache-stats` — проверка доступности кэша (REST/TCP)

## 📝 Примечания

- Контекст терминов (поле `context`) не влияет на перевод напрямую — в промпт передаются пары терминов и саммари главы/проекта
- Модель по умолчанию: `gemini-2.5-flash`
- Пакетный режим через Gemini Batch API осознанно не используется из‑за UX и сложностей мэппинга; реализован пакетный режим на стороне сервера с соблюдением лимитов

## 📄 Лицензия

MIT License — см. LICENSE
