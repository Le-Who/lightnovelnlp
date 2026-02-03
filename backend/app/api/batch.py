from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from datetime import datetime, timezone
from typing import List
import logging

logger = logging.getLogger(__name__)

from app.db import SessionLocal
from app.deps import get_db
from app.models.project import Chapter, Project
from app.models.glossary import (
    BatchJob, BatchJobItem, GlossaryTerm, TermStatus, TermCategory, TermRelationship
)
from app.core.nlp_pipeline.term_extractor import term_extractor
from app.core.nlp_pipeline.relationship_analyzer import relationship_analyzer
from app.core.nlp_pipeline.context_summarizer import context_summarizer
from app.core.translation_engine import translation_engine
from app.services.cache_service import cache_service
from app.tasks.nlp_tasks import process_batch_analyze_task, process_batch_translate_task

router = APIRouter()


# Sync processing functions removed in favor of Celery tasks


@router.post("/{project_id}/analyze", status_code=status.HTTP_200_OK)
def create_batch_analyze_job(
    project_id: int,
    chapter_ids: List[int],
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
) -> dict:
    """Создать задачу пакетного анализа глав."""
    if not chapter_ids:
        raise HTTPException(status_code=400, detail="No chapter IDs provided")
    
    # Проверяем, что все главы существуют
    chapters = db.query(Chapter).filter(Chapter.id.in_(chapter_ids)).all()
    if len(chapters) != len(chapter_ids):
        raise HTTPException(status_code=404, detail="Some chapters not found")
    
    # Получаем project_id из первой главы (все главы должны быть из одного проекта)
    project_id = chapters[0].project_id
    
    # Создаем задачу
    batch_job = BatchJob(
        project_id=project_id,
        job_type="analyze",
        status="pending",
        total_items=len(chapter_ids),
        created_at=datetime.now(timezone.utc)
    )
    db.add(batch_job)
    db.commit()
    
    # Создаем элементы задачи
    for chapter_id in chapter_ids:
        job_item = BatchJobItem(
            project_id=project_id,
            batch_job_id=batch_job.id,
            item_type="chapter",
            item_id=chapter_id,
            status="pending"
        )
        db.add(job_item)
    
    db.commit()
    
    # Запускаем обработку в фоне
    # Запускаем обработку в фоне (Async via Celery)
    process_batch_analyze_task.delay(batch_job.id)
    
    return {
        "batch_job_id": batch_job.id,
        "status": "pending",
        "total_items": len(chapter_ids),
        "message": "Batch analysis job created"
    }


@router.post("/{project_id}/translate", status_code=status.HTTP_200_OK)
def create_batch_translate_job(
    project_id: int,
    chapter_ids: List[int],
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
) -> dict:
    """Создать задачу пакетного перевода глав."""
    if not chapter_ids:
        raise HTTPException(status_code=400, detail="No chapter IDs provided")
    
    # Проверяем, что все главы существуют
    chapters = db.query(Chapter).filter(Chapter.id.in_(chapter_ids)).all()
    if len(chapters) != len(chapter_ids):
        raise HTTPException(status_code=404, detail="Some chapters not found")
    
    # Получаем project_id из первой главы (все главы должны быть из одного проекта)
    project_id = chapters[0].project_id
    
    # Создаем задачу
    batch_job = BatchJob(
        project_id=project_id,
        job_type="translate",
        status="pending",
        total_items=len(chapter_ids),
        created_at=datetime.now(timezone.utc)
    )
    db.add(batch_job)
    db.commit()
    
    # Создаем элементы задачи
    for chapter_id in chapter_ids:
        job_item = BatchJobItem(
            project_id=project_id,
            batch_job_id=batch_job.id,
            item_type="chapter",
            item_id=chapter_id,
            status="pending"
        )
        db.add(job_item)
    
    db.commit()
    
    # Запускаем обработку в фоне
    # Запускаем обработку в фоне (Async via Celery)
    process_batch_translate_task.delay(batch_job.id)
    
    return {
        "batch_job_id": batch_job.id,
        "status": "pending",
        "total_items": len(chapter_ids),
        "message": "Batch translation job created"
    }


@router.get("/jobs/{job_id}")
def get_batch_job_status(job_id: int, db: Session = Depends(get_db)) -> dict:
    """Получить статус пакетной задачи."""
    batch_job = db.get(BatchJob, job_id)
    if not batch_job:
        raise HTTPException(status_code=404, detail="Batch job not found")
    
    # Получаем элементы задачи
    job_items = db.query(BatchJobItem).filter(
        BatchJobItem.batch_job_id == job_id
    ).all()
    
    return {
        "batch_job_id": batch_job.id,
        "job_type": batch_job.job_type,
        "status": batch_job.status,
        "created_at": batch_job.created_at,
        "started_at": batch_job.started_at,
        "completed_at": batch_job.completed_at,
        "error": batch_job.error_message,
        "result": batch_job.job_data,
        "items": [
            {
                "item_id": item.item_id,
                "status": item.status,
                "started_at": item.started_at,
                "completed_at": item.completed_at,
                "error": item.error_message,
                "result": item.result
            }
            for item in job_items
        ]
    }
