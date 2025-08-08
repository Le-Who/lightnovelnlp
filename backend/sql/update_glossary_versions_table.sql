-- Обновление таблицы glossary_versions
-- Переименование колонок для соответствия модели

-- Переименовываем version_number в version_name
ALTER TABLE glossary_versions RENAME COLUMN version_number TO version_name;
ALTER TABLE glossary_versions ALTER COLUMN version_name TYPE VARCHAR(255);

-- Переименовываем terms_snapshot в terms_data
ALTER TABLE glossary_versions RENAME COLUMN terms_snapshot TO terms_data;
