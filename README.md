# Light Novel NLP - Система перевода с динамическим глоссарием

Полнофункциональная система для перевода лайт-новел с использованием AI и динамического глоссария для обеспечения консистентности терминов.

## 🚀 Быстрый старт

### Локальная разработка с Docker

```bash
# Клонируйте репозиторий
git clone <repository-url>
cd lightnovelnlp

# Запустите с Docker Compose
docker-compose up -d

# Проверьте статус
docker-compose ps

# Просмотрите логи
docker-compose logs -f backend
```

### Локальная разработка без Docker

```bash
# Backend
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload

# Frontend
cd frontend
npm install
npm run dev
```

## 🎯 Основные функции

- ✅ **Извлечение терминов** из текста с помощью Gemini API
- ✅ **Анализ связей** между персонажами и объектами
- ✅ **Контекстные саммари** глав
- ✅ **Динамический глоссарий** с версионированием
- ✅ **Пакетная обработка** глав
- ✅ **Кэширование** результатов
- ✅ **Ротация API ключей** Gemini
- ✅ **Бесплатный деплоймент** на Render.com

## 🚀 Быстрый старт с API

### 1. Проверка работоспособности
```bash
# Проверка здоровья API
curl https://lightnovel-backend.onrender.com/health

# Информация о системе
curl https://lightnovel-backend.onrender.com/info
```

### 2. Создание проекта
```bash
curl -X POST https://lightnovel-backend.onrender.com/projects/ \
  -H "Content-Type: application/json" \
  -d '{"name": "Мой первый проект"}'
```

### 3. Создание главы
```bash
curl -X POST https://lightnovel-backend.onrender.com/projects/1/chapters \
  -H "Content-Type: application/json" \
  -d '{"title": "Глава 1", "original_text": "主人公は冒険に出発した。"}'
```

### 4. Интерактивные инструменты
- **API Tools**: `https://lightnovel-frontend.onrender.com/api-tools.html`
- **Swagger UI**: `https://lightnovel-backend.onrender.com/docs`
- **Postman Collection**: Скачайте `Light_Novel_NLP_API.postman_collection.json`

## 🏗️ Архитектура

### Backend (FastAPI)
- **Python 3.11+** с FastAPI
- **PostgreSQL** для основной БД (Neon.tech)
- **Redis** для кэширования (Render/Upstash)
- **Gemini API** для NLP обработки
- **Синхронная обработка** (без Celery для бесплатного деплоймента)

### Frontend (React)
- **React 18** с Vite
- **React Router** для навигации
- **Axios** для API запросов
- **Современный UI** с адаптивным дизайном

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
│   │   └── tasks/          # Фоновые задачи (синхронные)
│   └── requirements.txt
├── frontend/               # React приложение
│   ├── src/
│   │   ├── components/     # React компоненты
│   │   ├── pages/          # Страницы
│   │   └── services/       # API клиент
│   ├── public/
│   │   ├── api-tools.html  # HTML формы для API
│   │   └── *.json          # Postman collection
│   └── package.json
├── render.yaml             # Конфигурация Render
├── README.md               # Основная документация
├── DEPLOYMENT.md           # Пошаговый план деплоймента
├── ENVIRONMENT_SETUP.md    # Настройка переменных окружения
├── API_TROUBLESHOOTING.md  # Устранение неполадок
└── test_api_endpoints.py   # Тестовый скрипт
```

## 🚀 Бесплатный деплоймент

### Поддерживаемые сервисы:
- ✅ **Render.com** - Web сервисы (backend, frontend)
- ✅ **Neon.tech** - PostgreSQL база данных
- ✅ **Upstash.com** - Redis

### Ограничения бесплатного плана:
- ⏰ **Web сервисы "засыпают"** после 15 минут неактивности
- 📊 **Ограниченное количество** запросов в месяц

### 🛠️ Доступ к функциям (Вариант B - API + Swagger UI):
- 📝 **API Tools** - HTML формы для быстрого тестирования
- 📚 **Swagger UI** - Полная документация API
- 📦 **Postman Collection** - Готовые запросы для всех endpoints
- ⏱️ **Ограниченное время** выполнения запросов
- 🔄 **Синхронная обработка** (без background worker)

### Для продакшена рекомендуется:
- 💰 **Платные планы** для больших нагрузок
- 🔧 **Background Worker** для длительных задач
- 📡 **Внешние сервисы** для очередей (Upstash QStash)

## 📞 Поддержка

При возникновении проблем:
1. Проверьте логи в Render Dashboard
2. Убедитесь, что все переменные окружения настроены
3. Проверьте статус внешних сервисов (Neon, Upstash)
4. Обратитесь к документации в `DEPLOYMENT.md`

## 🔧 Разработка

### Добавление новых функций:
1. Создайте модель в `backend/app/models/`
2. Добавьте схему в `backend/app/schemas/`
3. Создайте API endpoint в `backend/app/api/`
4. Обновите frontend компоненты
5. Протестируйте локально
6. Деплойте через Render Blueprint

### Тестирование:
```bash
# Backend тесты
cd backend
pytest

# Frontend тесты
cd frontend
npm test
```

## 📄 Лицензия

MIT License - см. файл LICENSE для деталей.
