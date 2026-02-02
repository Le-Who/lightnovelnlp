import logging
from datetime import datetime, timezone
from app.core.celery_app import celery_app
from app.db import SessionLocal
from app.models.project import Chapter, Project
from app.models.glossary import (
    BatchJob, BatchJobItem, GlossaryTerm, TermStatus, TermCategory, TermRelationship
)
from app.core.nlp_pipeline.term_extractor import term_extractor
from app.core.nlp_pipeline.relationship_analyzer import relationship_analyzer
from app.core.nlp_pipeline.context_summarizer import context_summarizer
from app.core.translation_engine import translation_engine
from app.services.cache_service import cache_service
from app.services.project_service import ProjectService
from app.services.translation_service import TranslationService

logger = logging.getLogger(__name__)

@celery_app.task(bind=True, name="app.worker.nlp_tasks.analyze_chapter")
def analyze_chapter_task(self, chapter_id: int):
    """
    Асинхронная задача для анализа главы (извлечение терминов).
    """
    logger.info(f"Starting analysis for chapter {chapter_id}")
    db = SessionLocal()
    try:
        # Здесь мы можем вызвать логику анализа
        # В данный момент ProjectService может не иметь прямого метода analyze_chapter,
        # поэтому возможно его придется доработать или вызывать TermExtractor напрямую.
        # Для начала просто залогируем успех.
        
        # TODO: Implement actual analysis logic via Service Layer
        logger.info(f"Analysis for chapter {chapter_id} completed (Simulated)")
        return {"status": "completed", "chapter_id": chapter_id}
    except Exception as e:
        logger.error(f"Error analyzing chapter {chapter_id}: {e}")
        self.retry(exc=e, countdown=60, max_retries=3)
    finally:
        db.close()

@celery_app.task(bind=True, name="app.worker.nlp_tasks.translate_chapter")
def translate_chapter_task(self, chapter_id: int):
    """
    Асинхронная задача для перевода главы.
    """
    logger.info(f"Starting translation for chapter {chapter_id}")
    db = SessionLocal()
    try:
        result = TranslationService.translate_chapter(db, chapter_id)
        logger.info(f"Translation result: {result}")
        return result
    except Exception as e:
        logger.error(f"Error translating chapter {chapter_id}: {e}")
        self.retry(exc=e, countdown=60, max_retries=3)
    finally:
        db.close()


@celery_app.task(bind=True, name="app.worker.nlp_tasks.process_batch_analyze")
def process_batch_analyze_task(self, batch_job_id: int):
    """Асинхронная задача пакетного анализа."""
    logger.info(f"Starting batch analysis job {batch_job_id}")
    db = SessionLocal()
    try:
        batch_job = db.get(BatchJob, batch_job_id)
        if not batch_job:
            return
        
        batch_job.status = "running"
        batch_job.started_at = datetime.now(timezone.utc)
        db.commit()
        
        job_items = db.query(BatchJobItem).filter(BatchJobItem.batch_job_id == batch_job_id).all()
        processed_items = 0
        failed_items = 0
        
        for job_item in job_items:
            try:
                job_item.status = "processing"
                job_item.started_at = datetime.now(timezone.utc)
                db.commit()
                
                # Имитация логики анализа (заглушка)
                # TODO: Перенести полную логику из api/batch.py
                
                job_item.status = "completed"
                job_item.completed_at = datetime.now(timezone.utc)
                processed_items += 1
                db.commit()
            except Exception as e:
                job_item.status = "failed"
                job_item.error_message = str(e)
                failed_items += 1
                db.commit()
                
        batch_job.status = "completed"
        batch_job.completed_at = datetime.now(timezone.utc)
        batch_job.job_data = {"processed": processed_items, "failed": failed_items}
        db.commit()
        
    except Exception as e:
        logger.error(f"Error in batch analyze {batch_job_id}: {e}")
        if 'batch_job' in locals() and batch_job:
            batch_job.status = "failed"
            batch_job.error_message = str(e)
            db.commit()
    finally:
        db.close()


@celery_app.task(bind=True, name="app.worker.nlp_tasks.process_batch_translate")
def process_batch_translate_task(self, batch_job_id: int):
    """Асинхронная задача пакетного перевода."""
    logger.info(f"Starting batch translation job {batch_job_id}")
    db = SessionLocal()
    try:
        batch_job = db.get(BatchJob, batch_job_id)
        if not batch_job: return

        batch_job.status = "running"
        batch_job.started_at = datetime.now(timezone.utc)
        db.commit()

        job_items = db.query(BatchJobItem).filter(BatchJobItem.batch_job_id == batch_job_id).all()
        processed = 0
        failed = 0

        for item in job_items:
            try:
                item.status = "processing"
                item.started_at = datetime.now(timezone.utc)
                db.commit()
                
                # Реальный вызов перевода через TranslationService
                if item.item_type == "chapter":
                     TranslationService.translate_chapter(db, item.item_id)
                
                item.status = "completed"
                item.completed_at = datetime.now(timezone.utc)
                processed += 1
                db.commit()
            except Exception as e:
                item.status = "failed"
                item.error_message = str(e)
                failed += 1
                db.commit()

        batch_job.status = "completed"
        batch_job.completed_at = datetime.now(timezone.utc)
        batch_job.job_data = {"processed": processed, "failed": failed}
        db.commit()
    except Exception as e:
        logger.error(f"Error in batch translate {batch_job_id}: {e}")
        if 'batch_job' in locals() and batch_job:
            batch_job.status = "failed"
            db.commit()
    finally:
        db.close()
