-- Добавление недостающих колонок в batch таблицы (ручной SQL)

-- batch_jobs
ALTER TABLE IF EXISTS batch_jobs ADD COLUMN IF NOT EXISTS project_id INTEGER;
ALTER TABLE IF EXISTS batch_jobs ADD COLUMN IF NOT EXISTS total_items INTEGER;

-- batch_job_items
ALTER TABLE IF EXISTS batch_job_items ADD COLUMN IF NOT EXISTS project_id INTEGER;
ALTER TABLE IF EXISTS batch_job_items ADD COLUMN IF NOT EXISTS item_type VARCHAR(50);

-- Заполнение дефолтными значениями
UPDATE batch_jobs SET total_items = COALESCE(total_items, 0);
UPDATE batch_job_items SET item_type = COALESCE(item_type, 'chapter');


