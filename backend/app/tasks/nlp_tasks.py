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
    batch_job = None
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
            if job_item.status == "completed":
                processed_items += 1
                continue
            if job_item.status == "failed":
                failed_items += 1
                continue

            try:
                # Re-fetch item to ensure fresh state/session attachment if needed
                # (though here we use same session, it's safer for long running tasks)
                
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

                # Update progress
                batch_job.processed_items = processed_items
                if batch_job.total_items > 0:
                    batch_job.progress_percentage = round((processed_items + failed_items) / batch_job.total_items * 100)

                db.commit()
            except Exception as e:
                logger.error(f"Error processing job item {job_item.id}: {e}")
                job_item.status = "failed"
                job_item.error_message = str(e)
                failed_items += 1

                # Update progress
                batch_job.failed_items = failed_items
                if batch_job.total_items > 0:
                    batch_job.progress_percentage = round((processed_items + failed_items) / batch_job.total_items * 100)

                db.commit()
                
        batch_job.status = "completed"
        batch_job.completed_at = datetime.now(timezone.utc)
        batch_job.job_data = {"processed": processed_items, "failed": failed_items}

        # Ensure final counts are accurate
        batch_job.processed_items = processed_items
        batch_job.failed_items = failed_items
        if batch_job.total_items > 0:
            batch_job.progress_percentage = round((processed_items + failed_items) / batch_job.total_items * 100)

        db.commit()
        
        logger.info(f"Batch analysis job {batch_job_id} completed: {processed_items} processed, {failed_items} failed")
        
    except Exception as e:
        logger.error(f"CRITICAL ERROR in batch analyze {batch_job_id}: {e}", exc_info=True)
        try:
            # Try to recover batch_job object if session became invalid
            if not batch_job:
                 batch_job = db.get(BatchJob, batch_job_id)
            
            if batch_job:
                batch_job.status = "failed"
                batch_job.error_message = f"Critical job failure: {str(e)}"
                batch_job.completed_at = datetime.now(timezone.utc)
                db.commit()
        except Exception as db_e:
            logger.error(f"Failed to update batch job status to failed: {db_e}")
    finally:
        db.close()


def process_batch_translate_task(batch_job_id: int):
    """Синхронная задача пакетного перевода. Вызывается через BackgroundTasks."""
    logger.info(f"Starting batch translation job {batch_job_id}")
    db = SessionLocal()
    batch_job = None
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
            if item.status == "completed":
                processed += 1
                continue
            if item.status == "failed":
                failed += 1
                continue

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

                # Update progress
                batch_job.processed_items = processed
                if batch_job.total_items > 0:
                    batch_job.progress_percentage = round((processed + failed) / batch_job.total_items * 100)

                db.commit()
            except Exception as e:
                logger.error(f"Error translating item {item.id}: {e}")
                item.status = "failed"
                item.error_message = str(e)
                failed += 1

                # Update progress
                batch_job.failed_items = failed
                if batch_job.total_items > 0:
                    batch_job.progress_percentage = round((processed + failed) / batch_job.total_items * 100)

                db.commit()

        batch_job.status = "completed"
        batch_job.completed_at = datetime.now(timezone.utc)
        batch_job.job_data = {"processed": processed, "failed": failed}

        # Ensure final counts are accurate
        batch_job.processed_items = processed
        batch_job.failed_items = failed
        if batch_job.total_items > 0:
            batch_job.progress_percentage = round((processed + failed) / batch_job.total_items * 100)

        db.commit()
        
        logger.info(f"Batch translation job {batch_job_id} completed: {processed} processed, {failed} failed")
    except Exception as e:
        logger.error(f"CRITICAL ERROR in batch translate {batch_job_id}: {e}", exc_info=True)
        try:
            if not batch_job:
                 batch_job = db.get(BatchJob, batch_job_id)
            
            if batch_job:
                batch_job.status = "failed"
                batch_job.error_message = f"Critical job failure: {str(e)}"
                batch_job.completed_at = datetime.now(timezone.utc)
                db.commit()
        except Exception as db_e:
            logger.error(f"Failed to update batch job status to failed: {db_e}")
    finally:
        db.close()

