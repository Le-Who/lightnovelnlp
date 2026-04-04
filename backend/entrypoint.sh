#!/bin/bash
set -e

echo "=== LightNovelNLP Backend Startup ==="

# Download spaCy models only if not already present (supports persistent volume)
for model in en_core_web_sm ru_core_news_sm; do
    if python -c "import spacy; spacy.load('$model')" 2>/dev/null; then
        echo "[spaCy] Model '$model' already available — skipping download"
    else
        echo "[spaCy] Downloading model: $model"
        python -m spacy download "$model"
    fi
done

# Run Alembic migrations (idempotent — skips already-applied migrations)
echo "[Alembic] Running database migrations..."

# Guard: if the DB already has tables but no alembic_version rows (pre-Alembic
# bootstrap), stamp the current head so Alembic doesn't try to re-create
# tables that already exist.  The check uses pg_tables which is always present.
python - <<'PYEOF'
import os, sys
import sqlalchemy as sa

url = os.environ.get("DATABASE_URL", "")
if not url:
    print("[Alembic] No DATABASE_URL — skipping stamp check")
    sys.exit(0)

engine = sa.create_engine(url)
with engine.connect() as conn:
    # Check if alembic_version table exists and has any rows
    try:
        result = conn.execute(sa.text(
            "SELECT COUNT(*) FROM alembic_version"
        )).scalar()
        version_rows = result
    except Exception:
        version_rows = 0  # table doesn't exist yet

    # Check if the projects table already exists (pre-Alembic schema)
    try:
        conn.execute(sa.text("SELECT 1 FROM projects LIMIT 1"))
        projects_exists = True
    except Exception:
        projects_exists = False

if version_rows == 0 and projects_exists:
    print("[Alembic] Detected pre-Alembic schema — stamping head to skip re-creation")
    import subprocess
    subprocess.run(["alembic", "stamp", "head"], check=True)
else:
    print(f"[Alembic] Schema state OK (version_rows={version_rows}, projects_exists={projects_exists})")
PYEOF

alembic upgrade head
echo "[Alembic] Migrations complete"


# Start uvicorn (single worker for 0.2 vCPU / 512MB RAM environments)
echo "[Server] Starting uvicorn on port ${PORT:-8000}..."
exec uvicorn app.main:app \
    --host 0.0.0.0 \
    --port "${PORT:-8000}" \
    --workers 1 \
    --timeout-keep-alive 65
