-- =====================================================
-- ПОЛНОЕ ИСПРАВЛЕНИЕ БАЗЫ ДАННЫХ LIGHT NOVEL NLP
-- =====================================================
-- Этот скрипт исправляет все проблемы с синхронизацией
-- между кодом приложения и схемой базы данных
-- =====================================================

-- 1. ДОБАВЛЕНИЕ КОЛОНКИ frequency В glossary_terms
-- =====================================================
DO $$
BEGIN
    -- Проверяем, существует ли колонка frequency
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'glossary_terms' 
        AND column_name = 'frequency'
    ) THEN
        -- Добавляем колонку frequency
        ALTER TABLE glossary_terms 
        ADD COLUMN frequency INTEGER NOT NULL DEFAULT 1;
        
        RAISE NOTICE 'Колонка frequency добавлена в таблицу glossary_terms';
    ELSE
        RAISE NOTICE 'Колонка frequency уже существует в таблице glossary_terms';
    END IF;
END $$;

-- 2. ДОБАВЛЕНИЕ КОЛОНКИ order В chapters
-- =====================================================
DO $$
BEGIN
    -- Проверяем, существует ли колонка order
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'chapters' 
        AND column_name = 'order'
    ) THEN
        -- Добавляем колонку order
        ALTER TABLE chapters 
        ADD COLUMN "order" INTEGER NOT NULL DEFAULT 0;
        
        RAISE NOTICE 'Колонка order добавлена в таблицу chapters';
    ELSE
        RAISE NOTICE 'Колонка order уже существует в таблице chapters';
    END IF;
END $$;

-- 3. СОЗДАНИЕ ИНДЕКСА ДЛЯ chapters.order
-- =====================================================
DO $$
BEGIN
    -- Проверяем, существует ли индекс
    IF NOT EXISTS (
        SELECT 1 FROM pg_indexes 
        WHERE indexname = 'ix_chapters_order'
    ) THEN
        -- Создаем индекс для эффективной сортировки
        CREATE INDEX ix_chapters_order ON chapters (project_id, "order");
        
        RAISE NOTICE 'Индекс ix_chapters_order создан';
    ELSE
        RAISE NOTICE 'Индекс ix_chapters_order уже существует';
    END IF;
END $$;

-- 4. ОБНОВЛЕНИЕ ВЕРСИИ ALEMBIC
-- =====================================================
DO $$
BEGIN
    -- Проверяем, существует ли таблица alembic_version
    IF EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_name = 'alembic_version'
    ) THEN
        -- Обновляем версию до 007
        UPDATE alembic_version SET version_num = '007';
        
        IF FOUND THEN
            RAISE NOTICE 'Версия Alembic обновлена до 007';
        ELSE
            RAISE NOTICE 'Версия Alembic уже установлена на 007';
        END IF;
    ELSE
        -- Создаем таблицу alembic_version если её нет
        CREATE TABLE alembic_version (
            version_num VARCHAR(32) NOT NULL
        );
        INSERT INTO alembic_version (version_num) VALUES ('007');
        RAISE NOTICE 'Таблица alembic_version создана с версией 007';
    END IF;
END $$;

-- 5. ПРОВЕРКА РЕЗУЛЬТАТА
-- =====================================================
-- Показываем текущую структуру таблиц
SELECT 
    'glossary_terms' as table_name,
    column_name,
    data_type,
    is_nullable,
    column_default
FROM information_schema.columns 
WHERE table_name = 'glossary_terms' 
ORDER BY ordinal_position;

SELECT 
    'chapters' as table_name,
    column_name,
    data_type,
    is_nullable,
    column_default
FROM information_schema.columns 
WHERE table_name = 'chapters' 
ORDER BY ordinal_position;

-- Показываем индексы
SELECT 
    tablename,
    indexname,
    indexdef
FROM pg_indexes 
WHERE tablename IN ('glossary_terms', 'chapters')
ORDER BY tablename, indexname;

-- Показываем версию Alembic
SELECT 'alembic_version' as table_name, version_num FROM alembic_version;

-- =====================================================
-- СКРИПТ ЗАВЕРШЕН
-- =====================================================
-- Теперь все функции приложения должны работать корректно:
-- ✅ Удаление проектов
-- ✅ Анализ глав  
-- ✅ Перевод
-- ✅ Работа с глоссарием
-- ✅ Пакетное создание глав
-- ✅ Улучшенный глоссарий с частотой
-- ✅ Функция рецензирования перевода
-- =====================================================
