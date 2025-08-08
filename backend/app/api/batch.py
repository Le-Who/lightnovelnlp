from __future__ import annotations

from typing import List
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.deps import get_db
from app.models.glossary import BatchJob, BatchJobItem
from app.models.project import Chapter
from app.schemas.glossary import (
    BatchJobCreate, 
    BatchJobRead, 
    BatchJobStatus
)
from app.tasks.celery_app import celery_app
from app.tasks.batch_processor import batch_analyze_chapters_task, batch_translate_chapters_task

router = APIRouter()


@router.post("/{project_id}/analyze-chapters", response_model=BatchJobRead, status_code=status.HTTP_201_CREATED)
def create_batch_analyze_job(
    project_id: int,
    payload: BatchJobCreate,
    db: Session = Depends(get_db)
) -> BatchJob:
    """Создать задачу пакетного анализа глав."""
    # Проверяем, что проект существует
    from app.models.project import Project
    project = db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Получаем главы для анализа
    chapters = db.query(Chapter).filter(
        Chapter.project_id == project_id
    ).all()
    
    if not chapters:
        raise HTTPException(
            status_code=400, 
            detail="No chapters found in project."
        )
    
    # Создаем задачу
    batch_job = BatchJob(
        project_id=project_id,
        job_type="analyze",
        status="pending",
        total_items=len(chapters),
        job_data=payload.job_data or {}
    )
    
    db.add(batch_job)
    db.commit()
    db.refresh(batch_job)
    
    # Создаем элементы задачи
    for chapter in chapters:
        job_item = BatchJobItem(
            batch_job_id=batch_job.id,
            item_type="chapter",
            item_id=chapter.id,
            status="pending"
        )
        db.add(job_item)
    
    db.commit()
    
    # Запускаем задачу в Celery
    celery_task = batch_analyze_chapters_task.delay(batch_job.id)
    
    # Обновляем задачу с ID Celery задачи
    batch_job.job_data = batch_job.job_data or {}
    batch_job.job_data["celery_task_id"] = celery_task.id
    db.commit()
    
    return batch_job


@router.post("/{project_id}/translate-chapters", response_model=BatchJobRead, status_code=status.HTTP_201_CREATED)
def create_batch_translate_job(
    project_id: int,
    payload: BatchJobCreate,
    db: Session = Depends(get_db)
) -> BatchJob:
    """Создать задачу пакетного перевода глав."""
    # Проверяем, что проект существует
    from app.models.project import Project
    project = db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Получаем главы для перевода (только те, которые еще не переведены)
    chapters = db.query(Chapter).filter(
        Chapter.project_id == project_id,
        Chapter.translated_text.is_(None)
    ).all()
    
    if not chapters:
        raise HTTPException(
            status_code=400, 
            detail="No untranslated chapters found in project."
        )
    
    # Создаем задачу
    batch_job = BatchJob(
        project_id=project_id,
        job_type="translate",
        status="pending",
        total_items=len(chapters),
        job_data=payload.job_data or {}
    )
    
    db.add(batch_job)
    db.commit()
    db.refresh(batch_job)
    
    # Создаем элементы задачи
    for chapter in chapters:
        job_item = BatchJobItem(
            batch_job_id=batch_job.id,
            item_type="chapter",
            item_id=chapter.id,
            status="pending"
        )
        db.add(job_item)
    
    db.commit()
    
    # Запускаем задачу в Celery
    celery_task = batch_translate_chapters_task.delay(batch_job.id)
    
    # Обновляем задачу с ID Celery задачи
    batch_job.job_data = batch_job.job_data or {}
    batch_job.job_data["celery_task_id"] = celery_task.id
    db.commit()
    
    return batch_job


@router.get("/{project_id}/jobs", response_model=List[BatchJobRead])
def list_batch_jobs(project_id: int, db: Session = Depends(get_db)) -> List[BatchJob]:
    """Получить список задач пакетной обработки для проекта."""
    jobs = db.query(BatchJob).filter(
        BatchJob.project_id == project_id
    ).order_by(BatchJob.created_at.desc()).all()
    
    return jobs


@router.get("/jobs/{job_id}", response_model=BatchJobRead)
def get_batch_job(job_id: int, db: Session = Depends(get_db)) -> BatchJob:
    """Получить конкретную задачу пакетной обработки."""
    job = db.get(BatchJob, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Batch job not found")
    
    return job


@router.get("/jobs/{job_id}/status", response_model=BatchJobStatus)
def get_batch_job_status(job_id: int, db: Session = Depends(get_db)) -> BatchJobStatus:
    """Получить статус задачи пакетной обработки."""
    job = db.get(BatchJob, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Batch job not found")
    
    # Рассчитываем оставшееся время (если задача выполняется)
    estimated_time_remaining = None
    if job.status == "running" and job.processed_items > 0:
        elapsed_time = (datetime.utcnow() - job.started_at).total_seconds()
        items_per_second = job.processed_items / elapsed_time
        remaining_items = job.total_items - job.processed_items
        estimated_time_remaining = int(remaining_items / items_per_second) if items_per_second > 0 else None
    
    return BatchJobStatus(
        job_id=job.id,
        status=job.status,
        progress_percentage=job.progress_percentage,
        processed_items=job.processed_items,
        total_items=job.total_items,
        failed_items=job.failed_items,
        estimated_time_remaining=estimated_time_remaining
    )


@router.get("/jobs/{job_id}/items")
def get_batch_job_items(job_id: int, db: Session = Depends(get_db)) -> dict:
    """Получить элементы задачи пакетной обработки."""
    job = db.get(BatchJob, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Batch job not found")
    
    items = db.query(BatchJobItem).filter(
        BatchJobItem.batch_job_id == job_id
    ).all()
    
    # Группируем по статусу
    items_by_status = {}
    for item in items:
        status = item.status
        if status not in items_by_status:
            items_by_status[status] = []
        items_by_status[status].append({
            "id": item.id,
            "item_type": item.item_type,
            "item_id": item.item_id,
            "status": item.status,
            "error_message": item.error_message,
            "started_at": item.started_at,
            "completed_at": item.completed_at
        })
    
    return {
        "job_id": job_id,
        "total_items": len(items),
        "items_by_status": items_by_status
    }


@router.delete("/jobs/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
def cancel_batch_job(job_id: int, db: Session = Depends(get_db)) -> None:
    """Отменить задачу пакетной обработки."""
    job = db.get(BatchJob, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Batch job not found")
    
    if job.status not in ["pending", "running"]:
        raise HTTPException(
            status_code=400, 
            detail="Cannot cancel job that is not pending or running"
        )
    
    # Отменяем Celery задачу, если есть
    if job.job_data and job.job_data.get("celery_task_id"):
        try:
            celery_app.control.revoke(job.job_data["celery_task_id"], terminate=True)
        except Exception as e:
            print(f"Error revoking Celery task: {e}")
    
    # Обновляем статус
    job.status = "cancelled"
    job.completed_at = datetime.utcnow()
    db.commit()
    
    return None
