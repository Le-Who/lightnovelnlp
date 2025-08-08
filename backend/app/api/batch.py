from __future__ import annotations

from typing import List
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session

from app.deps import get_db
from app.models.glossary import BatchJob, BatchJobItem
from app.models.project import Chapter
from app.schemas.glossary import (
    BatchJobCreate, 
    BatchJobRead, 
    BatchJobStatus
)
from app.core.nlp_pipeline.term_extractor import term_extractor
from app.core.nlp_pipeline.relationship_analyzer import relationship_analyzer
from app.core.nlp_pipeline.context_summarizer import context_summarizer
from app.models.glossary import GlossaryTerm, TermStatus, TermCategory, TermRelationship
from app.core.translation_engine import translation_engine
from app.services.cache_service import cache_service

router = APIRouter()


def process_batch_analyze_sync(batch_job_id: int, db: Session):
    """Синхронная пакетная обработка глав для анализа."""
    try:
        # Получаем задачу
        batch_job = db.get(BatchJob, batch_job_id)
        if not batch_job:
            return {"error": "Batch job not found", "batch_job_id": batch_job_id}
        
        # Обновляем статус
        batch_job.status = "running"
        batch_job.started_at = datetime.utcnow()
        db.commit()
        
        # Получаем элементы задачи
        job_items = db.query(BatchJobItem).filter(
            BatchJobItem.batch_job_id == batch_job_id
        ).all()
        
        total_items = len(job_items)
        processed_items = 0
        failed_items = 0
        
        for job_item in job_items:
            try:
                # Обновляем статус элемента
                job_item.status = "processing"
                job_item.started_at = datetime.utcnow()
                db.commit()
                
                # Получаем главу
                chapter = db.get(Chapter, job_item.item_id)
                if not chapter:
                    raise Exception("Chapter not found")
                
                # Извлекаем термины
                extracted_terms = term_extractor.extract_terms(chapter.original_text)
                
                # Сохраняем термины
                saved_terms = []
                for term_data in extracted_terms:
                    existing_term = db.query(GlossaryTerm).filter(
                        GlossaryTerm.project_id == chapter.project_id,
                        GlossaryTerm.source_term == term_data["source_term"]
                    ).first()
                    
                    if not existing_term:
                        term = GlossaryTerm(
                            project_id=chapter.project_id,
                            source_term=term_data["source_term"],
                            translated_term=term_data.get("translated_term", ""),
                            category=term_data.get("category", TermCategory.OTHER),
                            status=TermStatus.PENDING,
                            context=term_data.get("context", "")
                        )
                        db.add(term)
                        saved_terms.append(term)
                
                # Анализируем связи
                if len(saved_terms) > 1:
                    relationships = relationship_analyzer.analyze_relationships(
                        chapter.original_text,
                        [term.source_term for term in saved_terms]
                    )
                    
                    for rel_data in relationships:
                        relationship = TermRelationship(
                            project_id=chapter.project_id,
                            source_term=rel_data["source_term"],
                            target_term=rel_data["target_term"],
                            relationship_type=rel_data["relationship_type"],
                            confidence=rel_data.get("confidence", 0.5),
                            context=rel_data.get("context", "")
                        )
                        db.add(relationship)
                
                # Создаем саммари
                chapter_summary = context_summarizer.summarize_chapter(
                    chapter.original_text,
                    [term.source_term for term in saved_terms]
                )
                
                # Обновляем главу
                chapter.summary = chapter_summary
                chapter.processed_at = datetime.utcnow()
                
                # Обновляем элемент задачи
                job_item.status = "completed"
                job_item.completed_at = datetime.utcnow()
                job_item.result = {
                    "extracted_terms": len(saved_terms),
                    "relationships": len(relationships) if 'relationships' in locals() else 0,
                    "summary_created": bool(chapter_summary)
                }
                db.commit()
                
                processed_items += 1
                
            except Exception as e:
                # Обрабатываем ошибку
                job_item.status = "failed"
                job_item.completed_at = datetime.utcnow()
                job_item.error_message = str(e)
                db.commit()
                
                failed_items += 1
                print(f"Error processing chapter {job_item.item_id}: {e}")
            
            # Обновляем прогресс основной задачи
            progress_percentage = int((processed_items + failed_items) / total_items * 100)
            batch_job.processed_items = processed_items
            batch_job.failed_items = failed_items
            batch_job.progress_percentage = progress_percentage
            db.commit()
        
        # Завершаем задачу
        batch_job.status = "completed"
        batch_job.completed_at = datetime.utcnow()
        db.commit()
        
        return {
            "batch_job_id": batch_job_id,
            "status": "completed",
            "processed_items": processed_items,
            "failed_items": failed_items,
            "total_items": total_items
        }
        
    except Exception as e:
        db.rollback()
        return {"error": str(e), "batch_job_id": batch_job_id}


def process_batch_translate_sync(batch_job_id: int, db: Session):
    """Синхронная пакетная обработка глав для перевода."""
    try:
        # Получаем задачу
        batch_job = db.get(BatchJob, batch_job_id)
        if not batch_job:
            return {"error": "Batch job not found", "batch_job_id": batch_job_id}
        
        # Обновляем статус
        batch_job.status = "running"
        batch_job.started_at = datetime.utcnow()
        db.commit()
        
        # Получаем элементы задачи
        job_items = db.query(BatchJobItem).filter(
            BatchJobItem.batch_job_id == batch_job_id
        ).all()
        
        total_items = len(job_items)
        processed_items = 0
        failed_items = 0
        
        for job_item in job_items:
            try:
                # Обновляем статус элемента
                job_item.status = "processing"
                job_item.started_at = datetime.utcnow()
                db.commit()
                
                # Получаем главу
                chapter = db.get(Chapter, job_item.item_id)
                if not chapter:
                    raise Exception("Chapter not found")
                
                # Получаем утвержденные термины глоссария
                glossary_terms = db.query(GlossaryTerm).filter(
                    GlossaryTerm.project_id == chapter.project_id,
                    GlossaryTerm.status == TermStatus.APPROVED
                ).all()
                
                if not glossary_terms:
                    raise Exception("No approved glossary terms found")
                
                # Генерируем хеш глоссария для кэширования
                glossary_hash = cache_service.generate_glossary_hash([
                    {
                        "source_term": term.source_term,
                        "translated_term": term.translated_term,
                        "category": term.category,
                        "status": term.status
                    }
                    for term in glossary_terms
                ])
                
                # Проверяем кэш
                cached_translation = cache_service.get_cached_translation(chapter.id, glossary_hash)
                if cached_translation:
                    translated_text = cached_translation
                else:
                    # Выполняем перевод
                    translated_text = translation_engine.translate_chapter(
                        chapter.original_text,
                        glossary_terms,
                        chapter.project_id
                    )
                    
                    # Кэшируем результат
                    cache_service.cache_translation(chapter.id, glossary_hash, translated_text)
                
                # Обновляем главу
                chapter.translated_text = translated_text
                chapter.translated_at = datetime.utcnow()
                
                # Обновляем элемент задачи
                job_item.status = "completed"
                job_item.completed_at = datetime.utcnow()
                job_item.result = {
                    "translated": True,
                    "text_length": len(translated_text)
                }
                db.commit()
                
                processed_items += 1
                
            except Exception as e:
                # Обрабатываем ошибку
                job_item.status = "failed"
                job_item.completed_at = datetime.utcnow()
                job_item.error_message = str(e)
                db.commit()
                
                failed_items += 1
                print(f"Error translating chapter {job_item.item_id}: {e}")
            
            # Обновляем прогресс основной задачи
            progress_percentage = int((processed_items + failed_items) / total_items * 100)
            batch_job.processed_items = processed_items
            batch_job.failed_items = failed_items
            batch_job.progress_percentage = progress_percentage
            db.commit()
        
        # Завершаем задачу
        batch_job.status = "completed"
        batch_job.completed_at = datetime.utcnow()
        db.commit()
        
        return {
            "batch_job_id": batch_job_id,
            "status": "completed",
            "processed_items": processed_items,
            "failed_items": failed_items,
            "total_items": total_items
        }
        
    except Exception as e:
        db.rollback()
        return {"error": str(e), "batch_job_id": batch_job_id}


@router.post("/{project_id}/analyze-chapters", response_model=BatchJobRead, status_code=status.HTTP_201_CREATED)
def create_batch_analyze_job(
    project_id: int,
    payload: BatchJobCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
) -> BatchJob:
    """Создать задачу пакетного анализа глав (синхронно)."""
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
    
    # Запускаем обработку в фоновом режиме
    background_tasks.add_task(process_batch_analyze_sync, batch_job.id, db)
    
    return batch_job


@router.post("/{project_id}/translate-chapters", response_model=BatchJobRead, status_code=status.HTTP_201_CREATED)
def create_batch_translate_job(
    project_id: int,
    payload: BatchJobCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
) -> BatchJob:
    """Создать задачу пакетного перевода глав (синхронно)."""
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
    
    # Запускаем обработку в фоновом режиме
    background_tasks.add_task(process_batch_translate_sync, batch_job.id, db)
    
    return batch_job


@router.get("/{project_id}/jobs", response_model=List[BatchJobRead])
def list_batch_jobs(project_id: int, db: Session = Depends(get_db)) -> List[BatchJob]:
    """Получить список пакетных задач для проекта."""
    jobs = db.query(BatchJob).filter(BatchJob.project_id == project_id).all()
    return jobs


@router.get("/jobs/{job_id}", response_model=BatchJobRead)
def get_batch_job(job_id: int, db: Session = Depends(get_db)) -> BatchJob:
    """Получить детали пакетной задачи."""
    job = db.get(BatchJob, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Batch job not found")
    return job


@router.post("/jobs/{job_id}/cancel", response_model=BatchJobRead)
def cancel_batch_job(job_id: int, db: Session = Depends(get_db)) -> BatchJob:
    """Отменить пакетную задачу."""
    job = db.get(BatchJob, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Batch job not found")
    
    if job.status in ["completed", "failed", "cancelled"]:
        raise HTTPException(status_code=400, detail="Cannot cancel completed job")
    
    job.status = "cancelled"
    job.completed_at = datetime.utcnow()
    db.commit()
    
    return job
