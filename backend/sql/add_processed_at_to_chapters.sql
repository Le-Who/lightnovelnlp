-- Add processed_at column to chapters table
-- This script can be run manually in your database if Alembic migration fails

ALTER TABLE chapters ADD COLUMN processed_at TIMESTAMP;
