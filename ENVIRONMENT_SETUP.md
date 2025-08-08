# 🔧 Настройка переменных окружения

## 📋 Обзор

Этот документ содержит подробные инструкции по настройке переменных окружения для всех сервисов проекта Light Novel NLP.

## 🎯 Переменные окружения по сервисам

### Backend (Web Service)

#### **Обязательные переменные:**

1. **DATABASE_URL**
   - **Источник**: Neon.tech
   - **Формат**: `postgresql://user:password@host/database`
   - **Пример**: `postgresql://lightnovel_user:password123@ep-cool-forest-123456.us-east-2.aws.neon.tech/lightnovel_db`
   - **Где найти**: Neon Dashboard → Project → Connection Details → Connection String

2. **REDIS_URL**
   - **Источник**: Upstash.com
   - **Формат**: `redis://user:password@host:port`
   - **Пример**: `redis://default:password123@ep-cool-forest-123456.us-east-2.aws.upstash.io:12345`
   - **Где найти**: Upstash Dashboard → Database → Connection Details → Connection String

3. **GEMINI_API_KEYS**
   - **Источник**: Google AI Studio
   - **Формат**: `key1,key2,key3` (через запятую)
   - **Пример**: `AIzaSyC1234567890abcdef,AIzaSyD0987654321fedcba,AIzaSyE111222333444555`
   - **Где найти**: [Google AI Studio](https://makersuite.google.com/app/apikey) → Create API Key

#### **Дополнительные переменные:**

4. **GEMINI_API_LIMIT_PER_KEY**
   - **Значение**: `1000`
   - **Описание**: Дневной лимит запросов на один ключ

5. **GEMINI_API_LIMIT_THRESHOLD_PERCENT**
   - **Значение**: `95`
   - **Описание**: Процент лимита для ротации ключей

6. **GEMINI_API_COOLDOWN_HOURS**
   - **Значение**: `24`
   - **Описание**: Время кулдауна для использованных ключей

7. **ENVIRONMENT**
   - **Значение**: `production`
   - **Описание**: Окружение приложения

8. **ALLOWED_ORIGINS**
   - **Значение**: `https://lightnovel-frontend.onrender.com`
   - **Описание**: Разрешенные CORS origins
   - **Примечание**: Замените на ваш реальный frontend URL

### Frontend (Static Site)

#### **Обязательные переменные:**

1. **VITE_API_URL**
   - **Значение**: `https://lightnovel-backend.onrender.com`
   - **Описание**: URL backend API
   - **Примечание**: Замените на ваш реальный backend URL

## 🔧 Пошаговая настройка

### Шаг 1: Получение DATABASE_URL (Neon.tech)

1. **Войдите в Neon Dashboard**
   - Зайдите на [neon.tech](https://neon.tech)
   - Войдите в свой аккаунт

2. **Откройте проект**
   - Выберите ваш проект `lightnovel-nlp`
   - Перейдите в Dashboard

3. **Получите connection string**
   - В левом меню найдите "Connection Details"
   - Скопируйте "Connection String"
   - Формат: `postgresql://user:password@host/database`

4. **Проверьте SSL настройки**
   - Убедитесь, что строка содержит `?sslmode=require`
   - Если нет, добавьте в конец: `?sslmode=require`

### Шаг 2: Получение REDIS_URL (Upstash.com)

1. **Войдите в Upstash Dashboard**
   - Зайдите на [upstash.com](https://upstash.com)
   - Войдите в свой аккаунт

2. **Откройте Redis database**
   - Выберите ваш database `lightnovel-redis`
   - Перейдите в Dashboard

3. **Получите connection string**
   - В разделе "Connection Details"
   - Скопируйте "Connection String"
   - Формат: `redis://user:password@host:port`

4. **Проверьте доступность**
   - Убедитесь, что database имеет статус "Active"
   - Проверьте лимиты: 500K команд/месяц, 256MB storage

### Шаг 3: Получение GEMINI_API_KEYS

1. **Войдите в Google AI Studio**
   - Зайдите в [Google AI Studio](https://makersuite.google.com/app/apikey)
   - Войдите в Google аккаунт

2. **Создайте API ключи**
   - Нажмите "Create API Key"
   - Создайте **2-3 ключа** для ротации
   - Скопируйте каждый ключ

3. **Объедините ключи**
   - Соедините ключи через запятую
   - Пример: `key1,key2,key3`
   - **Не добавляйте пробелы!**

4. **Проверьте лимиты**
   - Каждый ключ: 1000 запросов/день
   - Общий лимит: 2000-3000 запросов/день

### Шаг 4: Настройка в Render Dashboard

#### **Backend (Web Service):**

1. **Откройте сервис**
   - В Render Dashboard выберите ваш backend сервис
   - Перейдите в "Environment"

2. **Добавьте переменные**
   ```
   DATABASE_URL=postgresql://user:password@host/database?sslmode=require
   REDIS_URL=redis://user:password@host:port
   GEMINI_API_KEYS=key1,key2,key3
   GEMINI_API_LIMIT_PER_KEY=1000
   GEMINI_API_LIMIT_THRESHOLD_PERCENT=95
   GEMINI_API_COOLDOWN_HOURS=24
   ENVIRONMENT=production
   ALLOWED_ORIGINS=https://lightnovel-frontend.onrender.com
   ```

3. **Сохраните изменения**
   - Нажмите "Save Changes"
   - Дождитесь перезапуска сервиса

#### **Frontend (Static Site):**

1. **Откройте сервис**
   - В Render Dashboard выберите ваш frontend сервис
   - Перейдите в "Environment"

2. **Добавьте переменную**
   ```
   VITE_API_URL=https://lightnovel-backend.onrender.com
   ```

3. **Сохраните изменения**
   - Нажмите "Save Changes"
   - Дождитесь перезапуска сервиса

## 🔍 Проверка настроек

### Проверка Backend

1. **Health Check**
   ```bash
   curl https://lightnovel-backend.onrender.com/health
   # Ожидаемый ответ: {"status": "healthy"}
   ```

2. **Info Endpoint**
   ```bash
   curl https://lightnovel-backend.onrender.com/info
   # Проверьте конфигурацию
   ```

3. **Проверка логов**
   - В Render Dashboard → Logs
   - Ищите ошибки подключения к БД или Redis

### Проверка Frontend

1. **Откройте приложение**
   - Перейдите на frontend URL
   - Проверьте консоль браузера на ошибки

2. **Проверка API подключения**
   - Откройте Developer Tools → Console
   - Ищите ошибки CORS или API

## 🚨 Устранение проблем

### Проблемы с DATABASE_URL

1. **Ошибка подключения**
   ```
   Error: connection to server at "host" failed
   ```
   - Проверьте правильность connection string
   - Убедитесь, что Neon database активна
   - Проверьте SSL настройки

2. **SSL ошибки**
   ```
   Error: SSL connection required
   ```
   - Добавьте `?sslmode=require` в конец URL
   - Проверьте SSL сертификаты

### Проблемы с REDIS_URL

1. **Ошибка подключения**
   ```
   Error: Redis connection failed
   ```
   - Проверьте правильность connection string
   - Убедитесь, что Upstash database активна
   - Проверьте лимиты команд

2. **Превышение лимитов**
   ```
   Error: Quota exceeded
   ```
   - Проверьте использование в Upstash Dashboard
   - Рассмотрите переход на платный план

### Проблемы с GEMINI_API_KEYS

1. **Ошибка аутентификации**
   ```
   Error: Invalid API key
   ```
   - Проверьте правильность ключей
   - Убедитесь, что ключи активны
   - Проверьте лимиты API

2. **Превышение лимитов**
   ```
   Error: Quota exceeded
   ```
   - Проверьте использование в Google AI Studio
   - Добавьте больше ключей для ротации

### Проблемы с CORS

1. **CORS ошибки**
   ```
   Error: CORS policy blocked
   ```
   - Проверьте ALLOWED_ORIGINS
   - Убедитесь, что URL frontend правильный
   - Проверьте протокол (http/https)

## 🔒 Безопасность

### Важные моменты:

1. **Никогда не коммитьте** переменные окружения в Git
2. **Используйте разные ключи** для разных окружений
3. **Регулярно ротируйте** API ключи
4. **Мониторьте использование** всех сервисов

### Рекомендации:

1. **Backup переменных**
   - Сохраните копии в безопасном месте
   - Используйте password manager

2. **Мониторинг**
   - Регулярно проверяйте лимиты
   - Настройте алерты при превышении

3. **Обновление**
   - Регулярно обновляйте API ключи
   - Следите за изменениями в сервисах

## 📞 Поддержка

При возникновении проблем:

1. **Проверьте логи** в Render Dashboard
2. **Убедитесь в правильности** всех переменных
3. **Проверьте лимиты** бесплатных планов
4. **Обратитесь к документации** сервисов

**Удачной настройки! 🚀**
