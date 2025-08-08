from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.deps import get_db
from app.models.project import Chapter
from app.tasks.process_chapter import process_chapter_task

router = APIRouter()


@router.post("/chapters/{chapter_id}/analyze", status_code=status.HTTP_202_ACCEPTED)
def analyze_chapter(chapter_id: int, db: Session = Depends(get_db)) -> dict:
    """Запустить анализ главы для извлечения терминов."""
    # Проверяем, что глава существует
    chapter = db.get(Chapter, chapter_id)
    if not chapter:
        raise HTTPException(status_code=404, detail="Chapter not found")
    
    # Запускаем фоновую задачу
    task = process_chapter_task.delay(chapter_id)
    
    return {
        "message": "Analysis started",
        "task_id": task.id,
        "chapter_id": chapter_id
    }


@router.get("/tasks/{task_id}/status")
def get_task_status(task_id: str) -> dict:
    """Получить статус фоновой задачи."""
    from app.tasks.celery_app import celery_app
    
    task_result = celery_app.AsyncResult(task_id)
    
    return {
        "task_id": task_id,
        "status": task_result.status,
        "result": task_result.result if task_result.ready() else None
    }
