# 🚀 Пошаговый план деплоймента Light Novel NLP

## 📋 Обзор

Этот документ содержит пошаговые инструкции для деплоймента проекта Light Novel NLP на бесплатных тарифах Render.com, Neon.tech и Upstash.com.

## 🎯 Стратегия деплоймента

### **Ручное создание сервисов (рекомендуется для бесплатного деплоймента)**
- ✅ **Полный контроль** над каждым сервисом
- ✅ **Бесплатные планы** доступны для всех сервисов
- ✅ **Простота** настройки
- ✅ **Гибкость** конфигурации

## 📦 Подготовка

### 1.1 Создание базы данных на Neon.tech

1. **Регистрация**
   - Зайдите на [neon.tech](https://neon.tech)
   - Создайте аккаунт (можно через GitHub)

2. **Создание проекта**
   - Нажмите "Create New Project"
   - Выберите регион (ближайший к вам)
   - Введите имя проекта: `lightnovel-nlp`
   - Выберите **Free** план

3. **Получение connection string**
   - В Dashboard найдите "Connection Details"
   - Скопируйте connection string (формат: `postgresql://user:password@host/database`)
   - Сохраните для использования в переменных окружения

### 1.2 Создание Redis на Upstash.com (альтернатива Render Redis)

1. **Регистрация**
   - Зайдите на [upstash.com](https://upstash.com)
   - Создайте аккаунт

2. **Создание Redis database**
   - Нажмите "Create Database"
   - Выберите регион (ближайший к Render)
   - Выберите **Free** план
   - Введите имя: `lightnovel-redis`

3. **Получение connection string**
   - Скопируйте connection string (формат: `redis://user:password@host:port`)
   - Сохраните для использования

### 1.3 Получение Gemini API ключей

1. **Доступ к Google AI Studio**
   - Зайдите в [Google AI Studio](https://makersuite.google.com/app/apikey)
   - Войдите в Google аккаунт

2. **Создание API ключей**
   - Нажмите "Create API Key"
   - Создайте **2-3 ключа** для ротации
   - Скопируйте все ключи

3. **Подготовка для переменных окружения**
   - Объедините ключи через запятую: `key1,key2,key3`

## 🏗️ Деплоймент на Render.com

### 2.1 Подготовка репозитория

1. **Создание GitHub репозитория**
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git branch -M main
   git remote add origin https://github.com/yourusername/lightnovelnlp.git
   git push -u origin main
   ```

2. **Проверка файлов**
   - Убедитесь, что `render.yaml` находится в корне
   - Проверьте наличие `backend/requirements.txt`
   - Проверьте наличие `frontend/package.json`

### 2.2 Создание сервисов на Render

#### **Шаг 1: Redis (через Blueprint)**

1. **Запуск Blueprint**
   - Зайдите на [render.com](https://render.com)
   - Создайте аккаунт и подключите GitHub
   - Выберите "New Blueprint Instance"
   - Укажите путь к `render.yaml`
   - Нажмите "Apply"

2. **Проверка создания**
   - Blueprint создаст только Redis сервис
   - Скопируйте Redis connection string из Dashboard

#### **Шаг 2: Backend (ручное создание)**

1. **Создание Web Service**
   - В Render Dashboard нажмите "New"
   - Выберите "Web Service"
   - Подключите GitHub репозиторий

2. **Настройка сервиса**
   ```
   Name: lightnovel-backend
   Environment: Python
   Plan: Free
   Build Command: cd backend && pip install -r requirements.txt && python init_db.py
   Start Command: cd backend && uvicorn app.main:app --host 0.0.0.0 --port $PORT
   ```

3. **Настройка переменных окружения**
   ```
   DATABASE_URL=postgresql://user:password@host/database
   REDIS_URL=redis://user:password@host:port
   GEMINI_API_KEYS=key1,key2,key3
   GEMINI_API_LIMIT_PER_KEY=1000
   GEMINI_API_LIMIT_THRESHOLD_PERCENT=95
   GEMINI_API_COOLDOWN_HOURS=24
   ENVIRONMENT=production
   ALLOWED_ORIGINS=https://lightnovel-frontend.onrender.com
   ```

4. **Дополнительные настройки**
   - Health Check Path: `/health`
   - Auto-Deploy: Yes
   - Branch: main

#### **Шаг 3: Frontend (ручное создание)**

1. **Создание Static Site**
   - В Render Dashboard нажмите "New"
   - Выберите "Static Site"
   - Подключите GitHub репозиторий

2. **Настройка сервиса**
   ```
   Name: lightnovel-frontend
   Plan: Free
   Build Command: cd frontend && npm install && npm run build
   Publish Directory: frontend/dist
   ```

3. **Настройка переменных окружения**
   ```
   VITE_API_URL=https://lightnovel-backend.onrender.com
   ```

4. **Дополнительные настройки**
   - Auto-Deploy: Yes
   - Branch: main

## ✅ Проверка деплоймента

### 3.1 Проверка Backend

1. **Health Check**
   ```bash
   curl https://lightnovel-backend.onrender.com/health
   # Ожидаемый ответ: {"status": "healthy"}
   ```

2. **API Documentation**
   - Откройте: `https://lightnovel-backend.onrender.com/docs`
   - Проверьте доступность Swagger UI

3. **Info Endpoint**
   ```bash
   curl https://lightnovel-backend.onrender.com/info
   # Проверьте конфигурацию
   ```

### 3.2 Проверка Frontend

1. **Доступность**
   - Откройте: `https://lightnovel-frontend.onrender.com`
   - Проверьте загрузку приложения

2. **API Connection**
   - Проверьте консоль браузера на ошибки
   - Убедитесь, что frontend подключается к backend

### 3.3 Проверка Redis

1. **Connection Test**
   - В Render Dashboard откройте Redis сервис
   - Проверьте статус "Available"
   - Проверьте логи на ошибки подключения

## 🔧 Настройка и тестирование

### 4.1 Создание первого проекта

1. **Через API**
   ```bash
   curl -X POST https://lightnovel-backend.onrender.com/projects \
     -H "Content-Type: application/json" \
     -d '{"title": "Test Novel", "description": "Test project"}'
   ```

2. **Через Frontend**
   - Откройте приложение
   - Создайте новый проект
   - Загрузите тестовую главу

### 4.2 Тестирование функций

1. **Извлечение терминов**
   - Загрузите главу с японским текстом
   - Запустите анализ
   - Проверьте создание терминов в глоссарии

2. **Перевод**
   - Утвердите термины в глоссарии
   - Запустите перевод главы
   - Проверьте качество перевода

## 📊 Мониторинг и обслуживание

### 5.1 Мониторинг использования

1. **Render Dashboard**
   - Проверяйте Usage в каждом сервисе
   - Следите за логами
   - Мониторьте статус health checks

2. **Neon Dashboard**
   - Проверяйте Compute Hours
   - Мониторьте Storage usage
   - Следите за Traffic

3. **Upstash Dashboard**
   - Проверяйте количество запросов
   - Мониторьте Storage usage

### 5.2 Автоматическое перезапуск

1. **Health Checks**
   - Настройте внешний мониторинг (UptimeRobot)
   - Пингуйте `/health` каждые 5 минут

2. **Prevent Sleep**
   - Используйте cron job для пинга
   - Настройте автоматические запросы

### 5.3 Резервное копирование

1. **База данных**
   - Neon: автоматические бэкапы каждые 24 часа
   - Ручной экспорт: `pg_dump`

2. **Код**
   - GitHub: автоматическое версионирование
   - Локальные копии важных файлов

## 🚨 Устранение неполадок

### 6.1 Частые проблемы

1. **Build Failures**
   ```bash
   # Проверьте логи в Render Dashboard
   # Убедитесь в правильности requirements.txt
   # Проверьте версии Python/Node.js
   ```

2. **Database Connection Issues**
   ```bash
   # Проверьте DATABASE_URL
   # Убедитесь в доступности Neon
   # Проверьте SSL настройки
   ```

3. **Redis Connection Issues**
   ```bash
   # Проверьте REDIS_URL
   # Убедитесь в доступности Redis
   # Проверьте IP allow list
   ```

4. **API Key Issues**
   ```bash
   # Проверьте GEMINI_API_KEYS
   # Убедитесь в валидности ключей
   # Проверьте лимиты API
   ```

### 6.2 Логи и отладка

1. **Render Logs**
   - Dashboard → Service → Logs
   - Фильтруйте по уровню (Error, Warning, Info)

2. **Application Logs**
   - Проверьте логи FastAPI
   - Мониторьте Celery задачи (если используется)

## 🔄 Обновление приложения

### 7.1 Процесс обновления

1. **Push изменений**
   ```bash
   git add .
   git commit -m "Update description"
   git push origin main
   ```

2. **Автоматический деплой**
   - Render автоматически деплоит изменения
   - Проверьте статус в Dashboard

3. **Проверка**
   - Проверьте health checks
   - Протестируйте новые функции
   - Проверьте логи на ошибки

### 7.2 Rollback

1. **Откат к предыдущей версии**
   ```bash
   git revert HEAD
   git push origin main
   ```

2. **Ручной откат**
   - В Render Dashboard выберите предыдущий деплой
   - Нажмите "Rollback"

## 📈 Масштабирование

### 8.1 Переход на платные планы

1. **Когда переходить**
   - Превышение лимитов бесплатного плана
   - Необходимость в большей производительности
   - Коммерческое использование

2. **Планы Render**
   - Starter: $7/месяц за сервис
   - Standard: $25/месяц за сервис
   - Pro: $50/месяц за сервис

3. **Планы Neon**
   - Pro: $20/месяц
   - Scale: $100/месяц

### 8.2 Добавление Background Worker

1. **Создание Worker**
   - New → Background Worker
   - Plan: Starter ($7/месяц)
   - Build Command: `cd backend && pip install -r requirements.txt`
   - Start Command: `cd backend && celery -A app.tasks.celery_app worker --loglevel=info`

2. **Настройка переменных**
   - Те же переменные, что и для backend
   - Добавьте `CELERY_BROKER_URL=REDIS_URL`

## 🎯 Заключение

Этот план обеспечивает полный бесплатный деплоймент проекта Light Novel NLP с возможностью масштабирования в будущем. Все сервисы настроены для оптимальной работы в рамках бесплатных лимитов.

### **Ключевые моменты:**
- ✅ Ручное создание сервисов для максимального контроля
- ✅ Использование бесплатных планов всех сервисов
- ✅ Правильная настройка переменных окружения
- ✅ Мониторинг и обслуживание
- ✅ План масштабирования

**Удачного деплоймента! 🚀**
