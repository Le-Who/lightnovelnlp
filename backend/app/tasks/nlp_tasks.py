import logging
from app.core.celery_app import celery_app
from app.db import SessionLocal
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
