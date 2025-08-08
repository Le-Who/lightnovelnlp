# Light Novel NLP - Система перевода с динамическим глоссарием

Полнофункциональная система для перевода ранобэ с использованием AI, включающая извлечение терминов, анализ связей, контекстные саммари и пакетную обработку.

## 🚀 Быстрый деплоймент на бесплатных тарифах

### Шаг 1: Подготовка сервисов

#### 1.1 Создание базы данных на Neon.tech
1. Зайдите на [neon.tech](https://neon.tech)
2. Создайте аккаунт и новый проект
3. Скопируйте connection string (формат: `postgresql://user:password@host/database`)

#### 1.2 Создание Redis на Upstash.com
1. Зайдите на [upstash.com](https://upstash.com)
2. Создайте аккаунт и новый Redis database
3. Скопируйте connection string (формат: `redis://user:password@host:port`)

#### 1.3 Получение Gemini API ключей
1. Зайдите в [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Создайте несколько API ключей (рекомендуется 2-3)
3. Скопируйте все ключи

### Шаг 2: Деплоймент на Render.com

#### 2.1 Подготовка репозитория
1. Создайте репозиторий на GitHub
2. Загрузите код проекта
3. Убедитесь, что файл `render.yaml` находится в корне

#### 2.2 Создание сервисов на Render
1. Зайдите на [render.com](https://render.com)
2. Создайте аккаунт и подключите GitHub репозиторий
3. Выберите "Blueprint" и укажите путь к `render.yaml`

#### 2.3 Настройка переменных окружения
После создания сервисов настройте переменные:

**Backend и Worker:**
- `GEMINI_API_KEYS`: ваши ключи через запятую (например: `key1,key2,key3`)
- `ALLOWED_ORIGINS`: `https://your-frontend-url.onrender.com`

**Frontend:**
- `VITE_API_URL`: `https://your-backend-url.onrender.com`

> 📖 **Подробные инструкции**: См. [ENVIRONMENT_SETUP.md](ENVIRONMENT_SETUP.md) для детальной настройки переменных окружения.

### Шаг 3: Проверка деплоймента

1. **Проверьте Backend**: `https://your-backend-url.onrender.com/health`
2. **Проверьте Frontend**: `https://your-frontend-url.onrender.com`
3. **Проверьте Worker**: логи в Render Dashboard

## 📋 Ограничения бесплатных тарифов

### Render.com
- **Web Services**: 750 часов/месяц (≈25 дней)
- **Worker Services**: 750 часов/месяц
- **Static Sites**: неограниченно
- **Sleep**: 15 минут бездействия
- **Free Postgres**: истекает через 30 дней

### Neon.tech
- **Compute**: 191.9 часов/месяц (достаточно для 0.25 CU 24/7)
- **Storage**: 3 GB
- **Autoscaling**: до 2 vCPU, 8 GB RAM
- **Read Replicas**: до 3 на проект
- **Scale to zero**: автоматическое масштабирование

### Upstash.com
- **Storage**: 10,000 записей
- **Requests**: 10,000/день
- **Bandwidth**: 1 GB/день

## 🔧 Оптимизация для бесплатных тарифов

### 1. Оптимизация Render
```yaml
# render.yaml оптимизации
services:
  - type: web
    name: lightnovel-backend
    plan: free
    # Добавляем health check для предотвращения сна
    healthCheckPath: /health
    healthCheckTimeout: 300
```

### 2. Оптимизация базы данных
```python
# Оптимизированные настройки подключения
engine = create_engine(
    settings.DATABASE_URL,
    pool_size=5,  # Ограничиваем пул соединений
    max_overflow=10,
    pool_pre_ping=True,
    pool_recycle=300,
)
```

### 3. Оптимизация Redis
```python
# Настройки кэширования
cache_service.set(key, value, ttl=3600)  # 1 час TTL
cache_service.set(key, value, ttl=86400)  # 24 часа для важных данных
```

## 🚨 Мониторинг и обслуживание

### 1. Мониторинг использования
- **Render**: Dashboard → Usage
- **Neon**: Dashboard → Metrics
- **Upstash**: Dashboard → Analytics

### 2. Автоматическое перезапуск
- Настройте cron job для пинга `/health` каждые 10 минут
- Используйте UptimeRobot для мониторинга

### 3. Резервное копирование
- Neon: автоматические бэкапы каждые 24 часа
- Экспорт данных: `pg_dump` для PostgreSQL

## 🔄 Обновление приложения

1. **Push в GitHub**: `git push origin main`
2. **Render автоматически деплоит** изменения
3. **Проверьте логи** в Render Dashboard
4. **Тестируйте** новые функции

## 🛠️ Локальная разработка

```bash
# Клонирование
git clone <your-repo>
cd lightnovelnlp

# Backend
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload

# Frontend
cd frontend
npm install
npm run dev

# Celery Worker
cd backend
celery -A app.tasks.celery_app worker --loglevel=info
```

## 📊 Структура проекта

```
lightnovelnlp/
├── backend/                 # FastAPI приложение
│   ├── app/
│   │   ├── api/            # API роутеры
│   │   ├── core/           # Конфигурация и ядро
│   │   ├── models/         # SQLAlchemy модели
│   │   ├── schemas/        # Pydantic схемы
│   │   ├── services/       # Бизнес-логика
│   │   └── tasks/          # Celery задачи
│   └── requirements.txt
├── frontend/               # React приложение
│   ├── src/
│   │   ├── components/     # React компоненты
│   │   ├── pages/          # Страницы
│   │   └── services/       # API клиент
│   └── package.json
├── render.yaml             # Конфигурация Render
├── README.md               # Основная документация
├── DEPLOYMENT.md           # Пошаговый план деплоймента
└── ENVIRONMENT_SETUP.md    # Настройка переменных окружения
```

## 🎯 Основные функции

- ✅ **Извлечение терминов** из текста
- ✅ **Анализ связей** между персонажами и объектами
- ✅ **Контекстные саммари** глав
- ✅ **Динамический глоссарий** с версионированием
- ✅ **Пакетная обработка** глав
- ✅ **Кэширование** результатов
- ✅ **Ротация API ключей** Gemini

## 📞 Поддержка

При возникновении проблем:
1. Проверьте логи в Render Dashboard
2. Убедитесь в правильности переменных окружения
3. Проверьте лимиты бесплатных тарифов
4. Создайте issue в GitHub репозитории

---

**Удачного деплоймента! 🚀**
