# 🚨 РУЧНОЕ ПРИМЕНЕНИЕ МИГРАЦИИ 007

## 📋 Текущая ситуация
- ✅ Миграция 007 создана в коде
- ✅ Все переменные окружения настроены на Render.com
- ⚠️ **Миграция НЕ применена к базе данных Neon.tech**
- ❌ Нет доступа к shell на хостинге

## 🔧 Варианты применения миграции

### Вариант 1: Через Render.com Shell (если доступен)

1. **Войдите в Render.com Dashboard**
2. **Выберите ваш backend сервис**
3. **Перейдите в раздел "Shell"** (если доступен)
4. **Выполните команды:**
   ```bash
   cd /opt/render/project/src
   python run_migration.py
   ```

### Вариант 2: Через Neon.tech SQL Editor (рекомендуется)

Поскольку у вас нет доступа к shell, **самый надежный способ** - выполнить SQL команды напрямую в Neon.tech:

#### Шаг 1: Войдите в Neon.tech Dashboard
- Откройте [console.neon.tech](https://console.neon.tech)
- Выберите ваш проект
- Перейдите в **SQL Editor**

#### Шаг 2: Выполните SQL команды

**Добавление колонки `order`:**
```sql
ALTER TABLE chapters 
ADD COLUMN "order" INTEGER NOT NULL DEFAULT 0;
```

**Создание индекса:**
```sql
CREATE INDEX ix_chapters_order 
ON chapters (project_id, "order");
```

**Обновление версии Alembic:**
```sql
-- Сначала проверьте, существует ли таблица alembic_version
SELECT * FROM alembic_version;

-- Если таблица существует, обновите версию
UPDATE alembic_version 
SET version_num = '007' 
WHERE version_num = '006';

-- Если таблица не существует, создайте её
INSERT INTO alembic_version (version_num) VALUES ('007');
```

### Вариант 3: Через Render.com Deploy Trigger

1. **Сделайте небольшое изменение в коде** (например, добавьте комментарий)
2. **Закоммитьте и запушьте изменения**
3. **Render.com автоматически пересоберет и развернет приложение**
4. **В процессе сборки может выполниться миграция** (если настроен post-deploy hook)

### Вариант 4: Через Render.com Environment Variables

1. **Добавьте переменную окружения для автоматической миграции:**
   ```
   AUTO_MIGRATE=true
   ```
2. **Перезапустите сервис** (если у вас есть код для автоматической миграции)

## 📊 Проверка успешности миграции

### В Neon.tech SQL Editor выполните:

**Проверка колонки:**
```sql
SELECT column_name, data_type, is_nullable, column_default
FROM information_schema.columns 
WHERE table_name = 'chapters' 
AND column_name = 'order';
```

**Проверка индекса:**
```sql
SELECT indexname, indexdef
FROM pg_indexes 
WHERE tablename = 'chapters' 
AND indexname = 'ix_chapters_order';
```

**Проверка версии Alembic:**
```sql
SELECT version_num FROM alembic_version;
```

## 🚨 Возможные проблемы и решения

### Проблема 1: Ошибка "column already exists"
**Решение:** Колонка уже добавлена, пропустите этот шаг.

### Проблема 2: Ошибка "index already exists"
**Решение:** Индекс уже создан, пропустите этот шаг.

### Проблема 3: Ошибка "table alembic_version does not exist"
**Решение:** Создайте таблицу:
```sql
CREATE TABLE alembic_version (
    version_num VARCHAR(32) NOT NULL PRIMARY KEY
);
INSERT INTO alembic_version (version_num) VALUES ('007');
```

### Проблема 4: Ошибка прав доступа
**Решение:** Убедитесь, что пользователь базы данных имеет права на:
- ALTER TABLE
- CREATE INDEX
- INSERT/UPDATE/DELETE

## ✅ Последовательность действий

1. **Сейчас**: Миграция 007 в коде, но не в БД
2. **Следующий шаг**: Выполнить SQL команды в Neon.tech
3. **После успеха**: Проверить результат
4. **Результат**: Можно коммитить, все функции готовы

## 🎯 Рекомендуемый план

1. **Используйте Вариант 2** (Neon.tech SQL Editor)
2. **Выполните SQL команды по порядку**
3. **Проверьте результат каждой команды**
4. **После успеха - коммитьте изменения**

## 📝 Альтернатива: Создание миграционного скрипта

Если хотите автоматизировать процесс, можете добавить в код:

```python
# В main.py или отдельном файле
@app.on_event("startup")
async def run_migrations():
    if os.getenv("AUTO_MIGRATE") == "true":
        # Выполнить миграцию при запуске
        pass
```

---

**ВАЖНО**: После ручного применения миграции в Neon.tech, миграция 007 будет считаться примененной, и можно безопасно коммитить код!
