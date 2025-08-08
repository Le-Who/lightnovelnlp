# 🔧 Настройка переменных окружения

## 📋 Обязательные переменные окружения

### Backend и Worker сервисы

#### 1. DATABASE_URL
**Источник**: Neon.tech PostgreSQL база данных
**Формат**: `postgresql://user:password@host/database`

**Как получить:**
1. Зайдите на [neon.tech](https://neon.tech)
2. Создайте новый проект
3. В разделе "Connection Details" скопируйте connection string
4. Пример: `postgresql://lightnovel_user:password@ep-cool-forest-123456.us-east-2.aws.neon.tech/lightnovel`

#### 2. REDIS_URL
**Источник**: Upstash.com Redis база данных
**Формат**: `redis://user:password@host:port`

**Как получить:**
1. Зайдите на [upstash.com](https://upstash.com)
2. Создайте новую Redis database
3. Скопируйте connection string
4. Пример: `redis://default:password@ep-cool-forest-123456.us-east-2.aws.upstash.io:12345`

#### 3. GEMINI_API_KEYS
**Источник**: Google AI Studio
**Формат**: `key1,key2,key3` (несколько ключей через запятую)

**Как получить:**
1. Зайдите в [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Создайте 2-3 API ключа для ротации
3. Скопируйте все ключи и объедините через запятую
4. Пример: `AIzaSyC1234567890abcdef,AIzaSyD0987654321fedcba,AIzaSyE1111111111111111`

#### 4. ALLOWED_ORIGINS
**Значение**: URL вашего фронтенда
**Формат**: `https://your-frontend-url.onrender.com`

**Пример**: `https://lightnovel-frontend.onrender.com`

### Frontend сервис

#### 1. VITE_API_URL
**Значение**: URL вашего backend API
**Формат**: `https://your-backend-url.onrender.com`

**Пример**: `https://lightnovel-backend.onrender.com`

## 🔧 Настройка в Render Dashboard

### Шаг 1: Откройте сервис
1. Зайдите в [Render Dashboard](https://dashboard.render.com)
2. Выберите ваш сервис (backend, frontend или worker)

### Шаг 2: Перейдите в Environment
1. В меню слева выберите "Environment"
2. Нажмите "Add Environment Variable"

### Шаг 3: Добавьте переменные

**Для Backend и Worker:**
```
DATABASE_URL = postgresql://user:password@host/database
REDIS_URL = redis://user:password@host:port
GEMINI_API_KEYS = key1,key2,key3
ALLOWED_ORIGINS = https://lightnovel-frontend.onrender.com
```

**Для Frontend:**
```
VITE_API_URL = https://lightnovel-backend.onrender.com
```

### Шаг 4: Сохраните и перезапустите
1. Нажмите "Save Changes"
2. Перейдите в "Manual Deploy"
3. Выберите "Clear build cache & deploy"

## ⚠️ Важные замечания

### Безопасность
- **Никогда не коммитьте** API ключи в Git
- Используйте **переменные окружения** для всех секретов
- Регулярно **ротируйте** API ключи

### Neon.tech особенности
- **Compute**: 191.9 часов/месяц (достаточно для 0.25 CU 24/7)
- **Autoscaling**: автоматически масштабируется до 2 vCPU, 8 GB RAM
- **Scale to zero**: автоматически останавливается при неактивности

### Render.com особенности
- **Free Postgres**: истекает через 30 дней - **НЕ ИСПОЛЬЗУЙТЕ**
- **Sleep**: 15 минут бездействия
- **Health checks**: предотвращают сон сервисов

## 🧪 Проверка настроек

### Проверка Backend
```bash
curl https://your-backend-url.onrender.com/info
```

Ожидаемый ответ:
```json
{
  "environment": "production",
  "database_configured": true,
  "redis_configured": true,
  "gemini_keys_count": 3
}
```

### Проверка Frontend
1. Откройте URL фронтенда
2. Проверьте консоль браузера на ошибки
3. Убедитесь, что API запросы работают

## 🚨 Устранение проблем

### Ошибка "DATABASE_URL not configured"
1. Проверьте, что переменная добавлена в Environment
2. Убедитесь, что Neon база активна
3. Проверьте правильность connection string

### Ошибка "REDIS_URL not configured"
1. Проверьте, что переменная добавлена в Environment
2. Убедитесь, что Upstash база активна
3. Проверьте правильность connection string

### Ошибка "GEMINI_API_KEYS not configured"
1. Проверьте, что переменная добавлена в Environment
2. Убедитесь, что ключи активны в Google AI Studio
3. Проверьте формат (ключи через запятую)

### CORS ошибки
1. Проверьте `ALLOWED_ORIGINS` в backend
2. Убедитесь, что URL фронтенда правильный
3. Проверьте `VITE_API_URL` во фронтенде

## 📞 Поддержка

При возникновении проблем:
1. Проверьте логи в Render Dashboard
2. Убедитесь в правильности всех переменных
3. Проверьте активность внешних сервисов (Neon, Upstash)
4. Создайте issue в GitHub репозитории
