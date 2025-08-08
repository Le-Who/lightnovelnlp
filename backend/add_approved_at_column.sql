-- Добавление колонки approved_at в таблицу glossary_terms
-- Выполните этот SQL скрипт в вашей базе данных PostgreSQL

ALTER TABLE glossary_terms 
ADD COLUMN IF NOT EXISTS approved_at TIMESTAMP;
