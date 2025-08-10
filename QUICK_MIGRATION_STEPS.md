# 🚀 БЫСТРАЯ МИГРАЦИЯ 007

## ⚡ Что нужно сделать прямо сейчас

**Выполните эти SQL команды в Neon.tech SQL Editor:**

### 1. Добавить колонку `order`
```sql
ALTER TABLE chapters ADD COLUMN "order" INTEGER NOT NULL DEFAULT 0;
```

### 2. Создать индекс
```sql
CREATE INDEX ix_chapters_order ON chapters (project_id, "order");
```

### 3. Обновить версию Alembic
```sql
-- Проверить текущую версию
SELECT * FROM alembic_version;

-- Обновить на 007
UPDATE alembic_version SET version_num = '007' WHERE version_num = '006';
```

## 📍 Где выполнить

1. **Откройте** [console.neon.tech](https://console.neon.tech)
2. **Выберите ваш проект**
3. **Перейдите в SQL Editor**
4. **Выполните команды по порядку**

## ✅ Проверка успеха

```sql
-- Проверить колонку
SELECT column_name FROM information_schema.columns 
WHERE table_name = 'chapters' AND column_name = 'order';

-- Проверить индекс
SELECT indexname FROM pg_indexes 
WHERE tablename = 'chapters' AND indexname = 'ix_chapters_order';

-- Проверить версию
SELECT version_num FROM alembic_version;
```

## 🎉 После успеха

- ✅ Миграция применена
- ✅ Можно коммитить код
- ✅ Все три функции готовы к работе

---

**Время выполнения: ~5 минут**
