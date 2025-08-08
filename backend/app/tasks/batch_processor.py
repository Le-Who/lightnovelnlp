from __future__ import annotations

from datetime import datetime
from typing import List

from celery import shared_task
from sqlalchemy.orm import Session

from app.db import SessionLocal
from app.models.glossary import BatchJob, BatchJobItem
from app.models.project import Chapter
from app.tasks.process_chapter import process_chapter_task
from app.core.translation_engine import translation_engine
from app.models.glossary import GlossaryTerm, TermStatus
from app.services.cache_service import cache_service


@shared_task(name="batch_analyze_chapters")
def batch_analyze_chapters_task(batch_job_id: int) -> dict:
    """Пакетный анализ глав для извлечения терминов и связей."""
    db = SessionLocal()
    
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
                
                # Выполняем анализ главы
                result = process_chapter_task(job_item.item_id)
                
                # Обновляем элемент задачи
                job_item.status = "completed"
                job_item.completed_at = datetime.utcnow()
                job_item.result = result
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
        # Обрабатываем общую ошибку
        if batch_job:
            batch_job.status = "failed"
            batch_job.error_message = str(e)
            batch_job.completed_at = datetime.utcnow()
            db.commit()
        
        return {
            "batch_job_id": batch_job_id,
            "status": "failed",
            "error": str(e)
        }
    finally:
        db.close()


@shared_task(name="batch_translate_chapters")
def batch_translate_chapters_task(batch_job_id: int) -> dict:
    """Пакетный перевод глав с использованием глоссария."""
    db = SessionLocal()
    
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
                    # Получаем контекст (если есть)
                    project_summary = None
                    project_chapters = db.query(Chapter).filter(
                        Chapter.project_id == chapter.project_id,
                        Chapter.summary.isnot(None)
                    ).order_by(Chapter.id).all()
                    
                    if len(project_chapters) > 1:
                        from app.core.nlp_pipeline.context_summarizer import context_summarizer
                        chapters_data = [
                            {
                                "title": ch.title,
                                "summary": ch.summary,
                                "original_text": ch.original_text
                            }
                            for ch in project_chapters[:5]
                        ]
                        project_summary = context_summarizer.create_project_summary(chapters_data)
                    
                    # Выполняем перевод
                    translated_text = translation_engine.translate_with_glossary(
                        text=chapter.original_text,
                        glossary_terms=glossary_terms,
                        context_summary=chapter.summary,
                        project_summary=project_summary
                    )
                    
                    # Кэшируем результат
                    cache_service.cache_translation(chapter.id, glossary_hash, translated_text)
                
                # Сохраняем перевод
                chapter.translated_text = translated_text
                db.commit()
                
                # Обновляем элемент задачи
                job_item.status = "completed"
                job_item.completed_at = datetime.utcnow()
                job_item.result = {
                    "translated_text": translated_text,
                    "glossary_terms_used": len(glossary_terms),
                    "cached": cached_translation is not None
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
        # Обрабатываем общую ошибку
        if batch_job:
            batch_job.status = "failed"
            batch_job.error_message = str(e)
            batch_job.completed_at = datetime.utcnow()
            db.commit()
        
        return {
            "batch_job_id": batch_job_id,
            "status": "failed",
            "error": str(e)
        }
    finally:
        db.close()
