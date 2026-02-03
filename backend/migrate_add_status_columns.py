"""Migration script to add analysis_status and translation_status columns to chapters table."""
import sqlite3
import os

# Путь к базе данных
db_path = os.path.join(os.path.dirname(__file__), "lightnovelnlp.db")

if not os.path.exists(db_path):
    print(f"Database not found at {db_path}")
    exit(1)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Проверяем, существуют ли колонки
cursor.execute("PRAGMA table_info(chapters)")
columns = [col[1] for col in cursor.fetchall()]

migrations = []

if "analysis_status" not in columns:
    migrations.append(
        "ALTER TABLE chapters ADD COLUMN analysis_status VARCHAR(20) DEFAULT 'idle' NOT NULL"
    )
    
if "analysis_error" not in columns:
    migrations.append(
        "ALTER TABLE chapters ADD COLUMN analysis_error TEXT"
    )
    
if "translation_status" not in columns:
    migrations.append(
        "ALTER TABLE chapters ADD COLUMN translation_status VARCHAR(20) DEFAULT 'idle' NOT NULL"
    )
    
if "translation_error" not in columns:
    migrations.append(
        "ALTER TABLE chapters ADD COLUMN translation_error TEXT"
    )

if not migrations:
    print("All columns already exist. Nothing to migrate.")
else:
    for sql in migrations:
        print(f"Running: {sql}")
        cursor.execute(sql)
    
    conn.commit()
    print(f"Migration completed! Added {len(migrations)} columns.")

conn.close()
