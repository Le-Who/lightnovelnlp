from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks
from sqlalchemy.orm import Session

from app.db import SessionLocal
from app.deps import get_db
from app.models.project import Chapter, TranslationStatus
from app.services.translation_service import TranslationService
from app.services.cache_service import cache_service

router = APIRouter()


def translate_chapter_background(chapter_id: int):
    """Фоновая задача для перевода главы с tracking статуса."""
    import logging

    logger = logging.getLogger(__name__)

    db = SessionLocal()
    try:
        chapter = db.get(Chapter, chapter_id)
        if not chapter:
            return

        # Устанавливаем статус TRANSLATING
        chapter.translation_status = TranslationStatus.TRANSLATING.value
        chapter.translation_error = None
        db.commit()

        logger.info(f"[TRANSLATE] Starting translation for chapter {chapter_id}")

        result = TranslationService.translate_chapter(db, chapter_id, use_glossary=True)

        if "error" in result:
            chapter.translation_status = TranslationStatus.FAILED.value
            chapter.translation_error = result["error"]
        else:
            chapter.translation_status = TranslationStatus.COMPLETED.value
            chapter.translation_error = None

        db.commit()
        logger.info(
            f"[TRANSLATE] Translation completed for chapter {chapter_id}: {result}"
        )

    except Exception as e:
        logger.error(
            f"[TRANSLATE] Translation failed for chapter {chapter_id}: {e}",
            exc_info=True,
        )
        try:
            chapter = db.get(Chapter, chapter_id)
            if chapter:
                chapter.translation_status = TranslationStatus.FAILED.value
                chapter.translation_error = str(e)
                db.commit()
        except Exception:
            db.rollback()
    finally:
        db.close()


@router.post("/chapters/{chapter_id}/translate", status_code=status.HTTP_200_OK)
def translate_chapter(
    chapter_id: int,
    db: Session = Depends(get_db),
    use_glossary: bool = Query(default=True),
) -> dict:
    """Перевести главу с использованием утвержденного глоссария и контекста."""
    try:
        result = TranslationService.translate_chapter(db, chapter_id, use_glossary)

        if "error" in result:
            raise HTTPException(
                status_code=result.get("status_code", 400), detail=result["error"]
            )

        return result

    except HTTPException:
        raise
    except Exception as e:
        # В случае проблем с внешним API или кэшем избегаем краха транзакции
        try:
            db.rollback()
        except Exception:
            pass
        raise HTTPException(status_code=502, detail=f"Translation failed: {str(e)}")


@router.post(
    "/chapters/{chapter_id}/translate-with-review", status_code=status.HTTP_200_OK
)
def translate_chapter_with_review(
    chapter_id: int,
    db: Session = Depends(get_db),
    max_retries: int = Query(
        default=1, description="Max correction passes to run if violations found"
    ),
) -> dict:
    """Оркестрация перевода главы с автоматическим ревью и исправлением нарушений глоссария."""
    try:
        result = TranslationService.translate_with_review(db, chapter_id, max_retries)

        if "error" in result:
            raise HTTPException(
                status_code=result.get("status_code", 400), detail=result["error"]
            )

        return result

    except HTTPException:
        raise
    except Exception as e:
        try:
            db.rollback()
        except Exception:
            pass
        raise HTTPException(
            status_code=502, detail=f"Translation with review failed: {str(e)}"
        )


@router.post(
    "/chapters/{chapter_id}/translate-async", status_code=status.HTTP_202_ACCEPTED
)
def translate_chapter_async(
    chapter_id: int, background_tasks: BackgroundTasks, db: Session = Depends(get_db)
) -> dict:
    """Запустить перевод главы в фоновом режиме."""
    chapter = db.get(Chapter, chapter_id)
    if not chapter:
        raise HTTPException(status_code=404, detail="Chapter not found")

    # Устанавливаем начальный статус PENDING
    chapter.translation_status = TranslationStatus.PENDING.value
    chapter.translation_error = None
    db.commit()

    # Добавляем задачу в фоновые задачи FastAPI
    background_tasks.add_task(translate_chapter_background, chapter_id)

    return {
        "message": "Translation started in background",
        "chapter_id": chapter_id,
        "status": "pending",
    }


@router.get("/chapters/{chapter_id}/translation-preview")
def preview_translation(chapter_id: int, db: Session = Depends(get_db)) -> dict:
    """Предварительный просмотр перевода (без сохранения)."""
    try:
        result = TranslationService.preview_translation(db, chapter_id)

        if "error" in result:
            raise HTTPException(
                status_code=result.get("status_code", 404), detail=result["error"]
            )

        return result

    except Exception as e:
        return {
            "chapter_id": chapter_id,
            "preview_available": False,
            "message": f"Preview generation failed: {str(e)}",
            "glossary_terms_count": 0,
        }


@router.post("/chapters/{chapter_id}/review")
def review_translation(chapter_id: int, db: Session = Depends(get_db)) -> dict:
    """Запросить рецензирование перевода главы у LLM."""
    try:
        result = TranslationService.review_translation(db, chapter_id)

        if "error" in result:
            raise HTTPException(
                status_code=result.get("status_code", 400), detail=result["error"]
            )

        return result

    except Exception as e:
        return {
            "chapter_id": chapter_id,
            "review_available": False,
            "message": f"Review generation failed: {str(e)}",
        }


@router.get("/chapters/{chapter_id}/review")
def get_translation_review(chapter_id: int) -> dict:
    """Получить рецензию перевода главы."""
    # Проверяем кэш на наличие рецензии
    review_key = f"translation_review:{chapter_id}"
    review_text = cache_service.get(review_key)

    if not review_text:
        return {
            "chapter_id": chapter_id,
            "review_available": False,
            "message": "No review found. Please generate a review first.",
        }

    return {
        "chapter_id": chapter_id,
        "review_available": True,
        "review_text": review_text,
        "message": "Review retrieved from cache",
    }
