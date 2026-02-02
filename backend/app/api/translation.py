from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.deps import get_db
from app.models.project import Chapter
from app.services.translation_service import TranslationService
from app.services.cache_service import cache_service

router = APIRouter()


@router.post("/chapters/{chapter_id}/translate", status_code=status.HTTP_200_OK)
def translate_chapter(
    chapter_id: int,
    db: Session = Depends(get_db),
    use_glossary: bool = Query(default=True)
) -> dict:
    """Перевести главу с использованием утвержденного глоссария и контекста."""
    try:
        result = TranslationService.translate_chapter(db, chapter_id, use_glossary)
        
        if "error" in result:
            raise HTTPException(status_code=result.get("status_code", 400), detail=result["error"])
            
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        # В случае проблем с внешним API или кэшем избегаем краха транзакции
        try:
            db.rollback()
        except Exception:
            pass
        raise HTTPException(
            status_code=502,
            detail=f"Translation failed: {str(e)}"
        )


@router.get("/chapters/{chapter_id}/translation-preview")
def preview_translation(chapter_id: int, db: Session = Depends(get_db)) -> dict:
    """Предварительный просмотр перевода (без сохранения)."""
    try:
        result = TranslationService.preview_translation(db, chapter_id)
        
        if "error" in result:
            raise HTTPException(status_code=result.get("status_code", 404), detail=result["error"])
            
        return result
        
    except Exception as e:
        return {
            "chapter_id": chapter_id,
            "preview_available": False,
            "message": f"Preview generation failed: {str(e)}",
            "glossary_terms_count": 0
        }


@router.post("/chapters/{chapter_id}/review")
def review_translation(
    chapter_id: int,
    db: Session = Depends(get_db)
) -> dict:
    """Запросить рецензирование перевода главы у LLM."""
    try:
        result = TranslationService.review_translation(db, chapter_id)
        
        if "error" in result:
            raise HTTPException(status_code=result.get("status_code", 400), detail=result["error"])
            
        return result
        
    except Exception as e:
        return {
            "chapter_id": chapter_id,
            "review_available": False,
            "message": f"Review generation failed: {str(e)}"
        }


@router.get("/chapters/{chapter_id}/review")
def get_translation_review(chapter_id: int) -> dict:
    """Получить рецензию перевода главы."""
    # Проверяем кэш на наличие рецензии
    review_key = f"translation_review:{chapter_id}"
    review_text = cache_service.get_cache(review_key)
    
    if not review_text:
        return {
            "chapter_id": chapter_id,
            "review_available": False,
            "message": "No review found. Please generate a review first."
        }
    
    return {
        "chapter_id": chapter_id,
        "review_available": True,
        "review_text": review_text,
        "message": "Review retrieved from cache"
    }
