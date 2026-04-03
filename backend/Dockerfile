# Production Dockerfile — LightNovelNLP Backend
FROM python:3.12-slim

# System dependencies for psycopg2, spaCy C extensions
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies (cached layer)
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Entrypoint handles: spaCy model download (with persistent volume check) + migrations + server
COPY entrypoint.sh .
RUN chmod +x entrypoint.sh

# Non-root user for security
RUN useradd --create-home --shell /bin/bash app && \
    chown -R app:app /app
USER app

# spaCy models directory (mount persistent volume here in production)
ENV SPACY_DATA=/app/spacy_models
RUN mkdir -p /app/spacy_models

EXPOSE 8000

CMD ["./entrypoint.sh"]
