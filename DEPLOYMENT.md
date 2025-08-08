# 🚀 Пошаговый план деплоймента Light Novel NLP

## 📋 Предварительные требования

- GitHub аккаунт
- Аккаунт на [Render.com](https://render.com)
- Аккаунт на [Neon.tech](https://neon.tech)
- Аккаунт на [Upstash.com](https://upstash.com)
- Google AI Studio аккаунт для Gemini API

## 🔧 Шаг 1: Подготовка сервисов

### 1.1 Создание базы данных PostgreSQL на Neon.tech

1. **Регистрация и создание проекта**
   - Зайдите на [neon.tech](https://neon.tech)
   - Создайте аккаунт
   - Создайте новый проект (например: `lightnovel-nlp`)

2. **Получение connection string**
   - В проекте перейдите в раздел "Connection Details"
   - Скопируйте connection string в формате:
     ```
     postgresql://user:password@host/database
     ```

### 1.2 Создание Redis на Upstash.com

1. **Регистрация и создание базы**
   - Зайдите на [upstash.com](https://upstash.com)
   - Создайте аккаунт
   - Создайте новую Redis database

2. **Получение connection string**
   - Скопируйте connection string в формате:
     ```
     redis://user:password@host:port
     ```

### 1.3 Получение Gemini API ключей

1. **Создание ключей**
   - Зайдите в [Google AI Studio](https://makersuite.google.com/app/apikey)
   - Создайте 2-3 API ключа (для ротации)
   - Скопируйте все ключи

## 🔄 Шаг 2: Подготовка репозитория

### 2.1 Создание GitHub репозитория

```bash
# Создайте новый репозиторий на GitHub
# Название: lightnovel-nlp
# Тип: Public или Private
```

### 2.2 Загрузка кода

```bash
# Клонируйте репозиторий
git clone https://github.com/your-username/lightnovel-nlp.git
cd lightnovel-nlp

# Убедитесь, что все файлы на месте
ls -la
# Должны быть: backend/, frontend/, render.yaml, README.md, DEPLOYMENT.md
```

## 🚀 Шаг 3: Деплоймент на Render.com

### 3.1 Создание аккаунта на Render

1. Зайдите на [render.com](https://render.com)
2. Создайте аккаунт
3. Подключите GitHub аккаунт

### 3.2 Создание Blueprint

1. **Создание нового Blueprint**
   - Нажмите "New +" → "Blueprint"
   - Подключите ваш GitHub репозиторий
   - Укажите путь к файлу: `render.yaml`

2. **Настройка переменных окружения**
   
   **Для Backend и Worker сервисов:**
   ```
   GEMINI_API_KEYS=your_key_1,your_key_2,your_key_3
   ALLOWED_ORIGINS=https://lightnovel-frontend.onrender.com
   ```
   
   **Для Frontend сервиса:**
   ```
   VITE_API_URL=https://lightnovel-backend.onrender.com
   ```

### 3.3 Запуск деплоймента

1. **Проверьте настройки**
   - Убедитесь, что все переменные окружения заполнены
   - Проверьте, что пути к файлам корректны

2. **Запустите деплоймент**
   - Нажмите "Apply" для создания всех сервисов
   - Дождитесь завершения деплоймента (5-10 минут)

## ✅ Шаг 4: Проверка деплоймента

### 4.1 Проверка Backend

```bash
# Проверьте health endpoint
curl https://lightnovel-backend.onrender.com/health
# Ожидаемый ответ: {"status": "healthy"}

# Проверьте info endpoint
curl https://lightnovel-backend.onrender.com/info
# Должен показать информацию о конфигурации
```

### 4.2 Проверка Frontend

1. Откройте URL фронтенда в браузере
2. Убедитесь, что страница загружается
3. Проверьте, что нет ошибок в консоли браузера

### 4.3 Проверка Worker

1. В Render Dashboard перейдите к Worker сервису
2. Проверьте логи на наличие ошибок
3. Убедитесь, что Celery worker запустился

## 🔧 Шаг 5: Настройка и тестирование

### 5.1 Создание первого проекта

1. Откройте фронтенд приложения
2. Создайте новый проект
3. Добавьте тестовую главу
4. Запустите анализ для извлечения терминов

### 5.2 Проверка функций

- ✅ Создание проектов
- ✅ Добавление глав
- ✅ Извлечение терминов
- ✅ Управление глоссарием
- ✅ Перевод глав
- ✅ Пакетная обработка

## 🚨 Шаг 6: Мониторинг и обслуживание

### 6.1 Настройка мониторинга

1. **UptimeRobot** (бесплатно)
   - Создайте аккаунт на [uptimerobot.com](https://uptimerobot.com)
   - Добавьте мониторинг для backend health endpoint
   - Настройте уведомления

2. **Render Dashboard**
   - Регулярно проверяйте логи сервисов
   - Мониторьте использование ресурсов

### 6.2 Автоматическое перезапуск

```bash
# Создайте cron job для пинга health endpoint
# Добавьте в crontab:
*/10 * * * * curl -f https://lightnovel-backend.onrender.com/health
```

## 📊 Оптимизация для бесплатных тарифов

### Render.com ограничения
- **750 часов/месяц** для web и worker сервисов
- **15 минут сна** при неактивности
- **512 MB RAM** на сервис
- **Free Postgres**: истекает через 30 дней

### Neon.tech ограничения
- **191.9 часов/месяц** compute (достаточно для 0.25 CU 24/7)
- **3 GB storage**
- **Autoscaling**: до 2 vCPU, 8 GB RAM
- **Read Replicas**: до 3 на проект
- **Scale to zero**: автоматическое масштабирование

### Upstash.com ограничения
- **10,000 записей**
- **10,000 запросов/день**
- **1 GB трафика/день**

## 🔄 Обновление приложения

### Автоматическое обновление
```bash
# Просто push в GitHub
git add .
git commit -m "Update application"
git push origin main
# Render автоматически деплоит изменения
```

### Ручное обновление
1. В Render Dashboard выберите сервис
2. Нажмите "Manual Deploy"
3. Выберите "Clear build cache & deploy"

## 🛠️ Устранение неполадок

### Частые проблемы

1. **Ошибка подключения к базе данных**
   - Проверьте `DATABASE_URL` в переменных окружения
   - Убедитесь, что Neon база активна

2. **Ошибка подключения к Redis**
   - Проверьте `REDIS_URL` в переменных окружения
   - Убедитесь, что Upstash база активна

3. **Ошибки Gemini API**
   - Проверьте `GEMINI_API_KEYS`
   - Убедитесь, что ключи активны и не превышены лимиты

4. **Frontend не подключается к Backend**
   - Проверьте `VITE_API_URL` в переменных окружения
   - Убедитесь, что CORS настроен правильно

### Просмотр логов

```bash
# В Render Dashboard:
# 1. Выберите сервис
# 2. Перейдите в "Logs"
# 3. Проверьте ошибки и предупреждения
```

## 📞 Поддержка

При возникновении проблем:

1. **Проверьте логи** в Render Dashboard
2. **Убедитесь в правильности** переменных окружения
3. **Проверьте лимиты** бесплатных тарифов
4. **Создайте issue** в GitHub репозитории

## 🎉 Готово!

Ваше приложение Light Novel NLP успешно развернуто на бесплатных тарифах!

**URLs:**
- Frontend: `https://lightnovel-frontend.onrender.com`
- Backend: `https://lightnovel-backend.onrender.com`
- API Docs: `https://lightnovel-backend.onrender.com/docs`

**Следующие шаги:**
1. Протестируйте все функции
2. Настройте мониторинг
3. Создайте первый проект перевода
4. Наслаждайтесь работой с системой! 🚀
