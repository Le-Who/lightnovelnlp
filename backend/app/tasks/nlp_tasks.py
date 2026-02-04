import logging
from datetime import datetime, timezone
from app.db import SessionLocal
from app.models.glossary import BatchJob, BatchJobItem
from app.api.processing import process_chapter_sync
from app.services.translation_service import TranslationService

logger = logging.getLogger(__name__)


def analyze_chapter_task(chapter_id: int):
    """
    Sync task for chapter analysis (term extraction).
    Called via BackgroundTasks. Delegates to process_chapter_sync.
    """
    logger.info(f"Starting analysis for chapter {chapter_id}")
    db = SessionLocal()
    try:
        result = process_chapter_sync(chapter_id, db)
        if "error" in result:
            return {"status": "error", "chapter_id": chapter_id, "error": result["error"]}
        return {"status": "completed", "chapter_id": chapter_id, **result}
    except Exception as e:
        logger.error(f"Error analyzing chapter {chapter_id}: {e}")
        return {"status": "error", "chapter_id": chapter_id, "error": str(e)}
    finally:
        db.close()


def translate_chapter_task(chapter_id: int):
    """
    Синхронная задача для перевода главы.
    Вызывается через BackgroundTasks.
    """
    logger.info(f"Starting translation for chapter {chapter_id}")
    db = SessionLocal()
    try:
        result = TranslationService.translate_chapter(db, chapter_id)
        logger.info(f"Translation result: {result}")
        return result
    except Exception as e:
        logger.error(f"Error translating chapter {chapter_id}: {e}")
        return {"status": "error", "chapter_id": chapter_id, "error": str(e)}
    finally:
        db.close()


def process_batch_analyze_task(batch_job_id: int):
    """Синхронная задача пакетного анализа. Вызывается через BackgroundTasks."""
    logger.info(f"Starting batch analysis job {batch_job_id}")
    db = SessionLocal()
    try:
        batch_job = db.get(BatchJob, batch_job_id)
        if not batch_job:
            logger.warning(f"Batch job {batch_job_id} not found")
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
                
                # Use shared process_chapter_sync for chapter analysis
                if job_item.item_type == "chapter":
                    result = process_chapter_sync(job_item.item_id, db)
                    if "error" in result:
                        raise Exception(result["error"])
                    job_item.result = result
                
                job_item.status = "completed"
                job_item.completed_at = datetime.now(timezone.utc)
                processed_items += 1
                db.commit()
            except Exception as e:
                logger.error(f"Error processing job item {job_item.id}: {e}")
                job_item.status = "failed"
                job_item.error_message = str(e)
                failed_items += 1
                db.commit()
                
        batch_job.status = "completed"
        batch_job.completed_at = datetime.now(timezone.utc)
        batch_job.job_data = {"processed": processed_items, "failed": failed_items}
        db.commit()
        
        logger.info(f"Batch analysis job {batch_job_id} completed: {processed_items} processed, {failed_items} failed")
        
    except Exception as e:
        logger.error(f"Error in batch analyze {batch_job_id}: {e}")
        if 'batch_job' in locals() and batch_job:
            batch_job.status = "failed"
            batch_job.error_message = str(e)
            db.commit()
    finally:
        db.close()


def process_batch_translate_task(batch_job_id: int):
    """Синхронная задача пакетного перевода. Вызывается через BackgroundTasks."""
    logger.info(f"Starting batch translation job {batch_job_id}")
    db = SessionLocal()
    try:
        batch_job = db.get(BatchJob, batch_job_id)
        if not batch_job:
            logger.warning(f"Batch job {batch_job_id} not found")
            return

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
                    result = TranslationService.translate_chapter(db, item.item_id)
                    item.result = result
                
                item.status = "completed"
                item.completed_at = datetime.now(timezone.utc)
                processed += 1
                db.commit()
            except Exception as e:
                logger.error(f"Error translating item {item.id}: {e}")
                item.status = "failed"
                item.error_message = str(e)
                failed += 1
                db.commit()

        batch_job.status = "completed"
        batch_job.completed_at = datetime.now(timezone.utc)
        batch_job.job_data = {"processed": processed, "failed": failed}
        db.commit()
        
        logger.info(f"Batch translation job {batch_job_id} completed: {processed} processed, {failed} failed")
    except Exception as e:
        logger.error(f"Error in batch translate {batch_job_id}: {e}")
        if 'batch_job' in locals() and batch_job:
            batch_job.status = "failed"
            batch_job.error_message = str(e)
            db.commit()
    finally:
        db.close()

