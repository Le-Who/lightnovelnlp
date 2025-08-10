-- =====================================================
-- МИГРАЦИЯ 007: Добавление колонки order в таблицу chapters
-- Выполните этот скрипт в Neon.tech SQL Editor
-- =====================================================

-- Шаг 1: Добавить колонку order в таблицу chapters
ALTER TABLE chapters 
ADD COLUMN "order" INTEGER NOT NULL DEFAULT 0;

-- Шаг 2: Создать индекс для эффективной сортировки
CREATE INDEX ix_chapters_order 
ON chapters (project_id, "order");

-- Шаг 3: Обновить версию Alembic
-- Сначала проверим, существует ли таблица alembic_version
DO $$
BEGIN
    -- Проверяем существование таблицы
    IF EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'alembic_version') THEN
        -- Таблица существует, обновляем версию
        UPDATE alembic_version SET version_num = '007' WHERE version_num = '006';
        
        -- Если обновление не затронуло строки, значит версия была другой
        IF NOT FOUND THEN
            -- Проверяем текущую версию
            IF EXISTS (SELECT 1 FROM alembic_version WHERE version_num = '007') THEN
                RAISE NOTICE 'Версия 007 уже установлена';
            ELSE
                -- Вставляем новую версию
                INSERT INTO alembic_version (version_num) VALUES ('007');
            END IF;
        END IF;
    ELSE
        -- Таблица не существует, создаем её
        CREATE TABLE alembic_version (
            version_num VARCHAR(32) NOT NULL PRIMARY KEY
        );
        INSERT INTO alembic_version (version_num) VALUES ('007');
    END IF;
END $$;

-- =====================================================
-- ПРОВЕРКА УСПЕШНОСТИ МИГРАЦИИ
-- =====================================================

-- Проверяем, что колонка order добавлена
SELECT 
    'Колонка order' as check_item,
    CASE 
        WHEN EXISTS (
            SELECT 1 FROM information_schema.columns 
            WHERE table_name = 'chapters' AND column_name = 'order'
        ) THEN '✅ ДОБАВЛЕНА' 
        ELSE '❌ НЕ ДОБАВЛЕНА' 
    END as status;

-- Проверяем, что индекс создан
SELECT 
    'Индекс ix_chapters_order' as check_item,
    CASE 
        WHEN EXISTS (
            SELECT 1 FROM pg_indexes 
            WHERE tablename = 'chapters' AND indexname = 'ix_chapters_order'
        ) THEN '✅ СОЗДАН' 
        ELSE '❌ НЕ СОЗДАН' 
    END as status;

-- Проверяем версию Alembic
SELECT 
    'Версия Alembic' as check_item,
    CASE 
        WHEN EXISTS (SELECT 1 FROM alembic_version WHERE version_num = '007') 
        THEN '✅ 007' 
        ELSE '❌ НЕ 007' 
    END as status;

-- Показываем текущую версию
SELECT 'Текущая версия Alembic:' as info, version_num as version 
FROM alembic_version;

-- =====================================================
-- МИГРАЦИЯ ЗАВЕРШЕНА
-- =====================================================
