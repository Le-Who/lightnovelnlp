from __future__ import annotations

from celery import shared_task


@shared_task(name="process_chapter")
def process_chapter_task(chapter_id: int) -> dict:
    # Заглушка: здесь будет вызов NLP-пайплайна
    return {"chapter_id": chapter_id, "status": "queued"}
