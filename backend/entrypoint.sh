#!/bin/bash
set -e

echo "=== LightNovelNLP Backend Startup ==="

# Download spaCy models only if not already present (supports persistent volume)
for model in en_core_web_sm ru_core_news_sm; do
    if python -c "import spacy; spacy.load('$model')" 2>/dev/null; then
        echo "[spaCy] Model '$model' already available — skipping download"
    else
        echo "[spaCy] Downloading model: $model"
        python -m spacy download "$model" --direct
    fi
done

# Run Alembic migrations (idempotent — skips already-applied migrations)
echo "[Alembic] Running database migrations..."
alembic upgrade head
echo "[Alembic] Migrations complete"

# Start uvicorn (single worker for 0.2 vCPU / 512MB RAM environments)
echo "[Server] Starting uvicorn on port ${PORT:-8000}..."
exec uvicorn app.main:app \
    --host 0.0.0.0 \
    --port "${PORT:-8000}" \
    --workers 1 \
    --timeout-keep-alive 65
