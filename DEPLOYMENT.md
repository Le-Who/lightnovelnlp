# 🚀 Пошаговый план деплоймента Light Novel NLP

## 📋 Обзор

Полный план деплоймента проекта Light Novel NLP на бесплатных тарифах с использованием:
- **Render.com** - Backend и Frontend
- **Neon.tech** - PostgreSQL база данных  
- **Upstash.com** - Redis кэширование
- **Google AI Studio** - Gemini API

## 🎯 Стратегия деплоймента

### **Ручное создание всех сервисов (рекомендуется)**
- ✅ **Полный контроль** над каждым сервисом
- ✅ **Бесплатные планы** доступны для всех сервисов
- ✅ **Лучшая производительность** Redis через Upstash
- ✅ **Простота** настройки и мониторинга

## 📦 Шаг 1: Подготовка внешних сервисов

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
   - **Сохраните для использования в переменных окружения**

### 1.2 Создание Redis на Upstash.com

1. **Регистрация**
   - Зайдите на [upstash.com](https://upstash.com)
   - Создайте аккаунт (можно через GitHub)

2. **Создание Redis database**
   - Нажмите "Create Database"
   - Выберите регион (ближайший к Render)
   - Выберите **Free** план
   - Введите имя: `lightnovel-redis`
   - Нажмите "Create"

3. **Получение connection string**
   - В Dashboard найдите "Connection Details"
   - Скопируйте connection string (формат: `redis://user:password@host:port`)
   - **Сохраните для использования в переменных окружения**

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
   - **Сохраните для использования**

## 🏗️ Шаг 2: Подготовка репозитория

### 2.1 Создание GitHub репозитория

1. **Создание репозитория**
   ```bash
   # Создайте новый репозиторий на GitHub
   # Название: lightnovel-nlp
   # Тип: Public или Private
   ```

2. **Загрузка кода**
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git branch -M main
   git remote add origin https://github.com/yourusername/lightnovel-nlp.git
   git push -u origin main
   ```

3. **Проверка файлов**
   - Убедитесь, что `render.yaml` находится в корне
   - Проверьте наличие `backend/requirements.txt`
   - Проверьте наличие `frontend/package.json`

## 🚀 Шаг 3: Деплоймент на Render.com

### 3.1 Создание аккаунта на Render

1. **Регистрация**
   - Зайдите на [render.com](https://render.com)
   - Создайте аккаунт
   - Подключите GitHub аккаунт

### 3.2 Создание Backend (Web Service)

1. **Создание сервиса**
   - В Render Dashboard нажмите "New"
   - Выберите "Web Service"
   - Подключите ваш GitHub репозиторий

2. **Настройка сервиса**
   ```
   Name: lightnovel-backend
   Environment: Docker
   Plan: Free
   Docker Image: будет собран автоматически из Dockerfile
   ```

3. **Настройка переменных окружения**
   ```
   DATABASE_URL=postgresql://user:password@host/database
   REDIS_URL=redis://user:password@host:port
   GEMINI_API_KEYS=key1,key2,key3
   GEMINI_API_LIMIT_PER_KEY=1000
   GEMINI_API_LIMIT_THRESHOLD_PERCENT=95
   GEMINI_API_COOLDOWN_HOURS=24
   GEMINI_API_RESET_TIMEZONE=America/Los_Angeles
   ENVIRONMENT=production
   ALLOWED_ORIGINS=https://lightnovel-frontend.onrender.com
   ```

4. **Дополнительные настройки**
   - Health Check Path: `/health`
   - Auto-Deploy: Yes
   - Branch: main

5. **Создание сервиса**
   - Нажмите "Create Web Service"
   - Дождитесь завершения деплоймента (10-15 минут для Docker сборки)

### 3.3 Создание Frontend (Static Site)

1. **Создание сервиса**
   - В Render Dashboard нажмите "New"
   - Выберите "Static Site"
   - Подключите ваш GitHub репозиторий

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

5. **Создание сервиса**
   - Нажмите "Create Static Site"
   - Дождитесь завершения деплоймента (3-5 минут)

## ✅ Шаг 4: Проверка деплоймента

### 4.1 Проверка Backend

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

### 4.2 Проверка Frontend

1. **Доступность**
   - Откройте: `https://lightnovel-frontend.onrender.com`
   - Проверьте загрузку приложения

2. **API Connection**
   - Проверьте консоль браузера на ошибки
   - Убедитесь, что frontend подключается к backend

### 4.3 Проверка Redis (Upstash)

1. **Connection Test**
   - В Upstash Dashboard откройте Redis database
   - Проверьте статус "Active"
   - Проверьте логи на ошибки подключения

### 4.4 Выполнение миграции базы данных

1. **Вариант A: Через Alembic (рекомендуется)**
   ```bash
   # В Render Dashboard -> Backend -> Shell
   cd /opt/render/project/src/backend
   python run_migration.py
   ```

2. **Вариант B: Прямой SQL (если Alembic не работает)**
   ```sql
   -- Выполните в Neon Dashboard -> SQL Editor
   -- Миграция 1: Добавление approved_at в glossary_terms
   ALTER TABLE glossary_terms 
   ADD COLUMN IF NOT EXISTS approved_at TIMESTAMP;
   
   -- Миграция 2: Добавление genre в projects
   ALTER TABLE projects 
   ADD COLUMN IF NOT EXISTS genre VARCHAR(50) DEFAULT 'other' NOT NULL;
   
   -- Миграция 3: Добавление processed_at в chapters
   ALTER TABLE chapters 
   ADD COLUMN IF NOT EXISTS processed_at TIMESTAMP;
   
   -- Миграция 4: Переименование колонок в glossary_versions
   ALTER TABLE glossary_versions RENAME COLUMN version_number TO version_name;
   ALTER TABLE glossary_versions ALTER COLUMN version_name TYPE VARCHAR(255);
   ALTER TABLE glossary_versions RENAME COLUMN terms_snapshot TO terms_data;
   ```

3. **Проверка миграции**
   ```sql
   -- Проверьте, что колонки добавлены
   SELECT column_name, data_type 
   FROM information_schema.columns 
   WHERE table_name = 'glossary_terms' 
   AND column_name = 'approved_at';
   
   SELECT column_name, data_type 
   FROM information_schema.columns 
   WHERE table_name = 'projects' 
   AND column_name = 'genre';
   
   SELECT column_name, data_type 
   FROM information_schema.columns 
   WHERE table_name = 'chapters' 
   AND column_name = 'processed_at';
   
   -- Проверка миграции 4: glossary_versions
   SELECT column_name, data_type 
   FROM information_schema.columns 
   WHERE table_name = 'glossary_versions' 
   AND column_name IN ('version_name', 'terms_data');
   ```

## 🔧 Шаг 5: Настройка и тестирование

### 5.1 Создание первого проекта

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

### 5.2 Тестирование функций

1. **Извлечение терминов**
   - Загрузите главу с японским текстом
   - Запустите анализ
   - Проверьте создание терминов в глоссарии

2. **Перевод**
   - Утвердите термины в глоссарии
   - Запустите перевод главы
   - Проверьте качество перевода

## 📊 Шаг 6: Мониторинг и обслуживание

### 6.1 Мониторинг использования

1. **Render Dashboard**
   - Проверяйте Usage в каждом сервисе
   - Следите за логами
   - Мониторьте статус health checks

2. **Neon Dashboard**
   - Проверяйте Compute Hours
   - Мониторьте Storage usage
   - Следите за Traffic

3. **Upstash Dashboard**
   - Проверяйте количество команд (500K/месяц)
   - Мониторьте Storage usage (256MB)
   - Следите за производительностью

### 6.2 Автоматическое перезапуск

1. **Health Checks**
   - Настройте внешний мониторинг (UptimeRobot)
   - Пингуйте `/health` каждые 5 минут

2. **Prevent Sleep**
   - Используйте cron job для пинга
   - Настройте автоматические запросы

### 6.3 Резервное копирование

1. **База данных**
   - Neon: автоматические бэкапы каждые 24 часа
   - Ручной экспорт: `pg_dump`

2. **Код**
   - GitHub: автоматическое версионирование
   - Локальные копии важных файлов

## 🚨 Шаг 7: Устранение неполадок

### 7.1 Частые проблемы

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
   # Убедитесь в доступности Upstash
   # Проверьте лимиты команд
   ```

4. **API Key Issues**
   ```bash
   # Проверьте GEMINI_API_KEYS
   # Убедитесь в валидности ключей
   # Проверьте лимиты API
   ```

### 7.2 Логи и отладка

1. **Render Logs**
   - Dashboard → Service → Logs
   - Фильтруйте по уровню (Error, Warning, Info)

2. **Application Logs**
   - Проверьте логи FastAPI
   - Мониторьте обработку задач

## 🔄 Шаг 8: Обновление приложения

### 8.1 Процесс обновления

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

### 8.2 Rollback

1. **Откат к предыдущей версии**
   ```bash
   git revert HEAD
   git push origin main
   ```

2. **Ручной откат**
   - В Render Dashboard выберите предыдущий деплой
   - Нажмите "Rollback"

## 📈 Шаг 9: Масштабирование

### 9.1 Переход на платные планы

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

4. **Планы Upstash**
   - Pay as you go: $0.25 за 100K команд
   - Pro: $25/месяц

### 9.2 Добавление Background Worker

1. **Создание Worker**
   - New → Background Worker
   - Plan: Starter ($7/месяц)
   - Build Command: `cd backend && pip install -r requirements.txt`
   - Start Command: `cd backend && celery -A app.tasks.celery_app worker --loglevel=info`

2. **Настройка переменных**
   - Те же переменные, что и для backend
   - Добавьте `CELERY_BROKER_URL=REDIS_URL`

## 🎯 Заключение

Этот план обеспечивает полный бесплатный деплоймент проекта Light Novel NLP с использованием лучших бесплатных сервисов. Все компоненты настроены для оптимальной работы в рамках бесплатных лимитов.

### **Ключевые преимущества:**
- ✅ **Upstash Redis** - лучшая производительность и лимиты
- ✅ **Neon PostgreSQL** - автоматическое масштабирование
- ✅ **Render** - простота деплоймента
- ✅ **Полный контроль** над каждым сервисом
- ✅ **Бесплатные планы** для всех компонентов

### **Лимиты бесплатных планов:**
- **Render**: 750 часов/месяц, 15 минут сна
- **Neon**: 191.9 часов/месяц, 0.5GB storage
- **Upstash**: 500K команд/месяц, 256MB storage

**Удачного деплоймента! 🚀**
