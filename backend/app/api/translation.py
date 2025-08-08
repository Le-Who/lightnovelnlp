from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.deps import get_db
from app.models.project import Chapter
from app.models.glossary import GlossaryTerm, TermStatus
from app.core.translation_engine import translation_engine

router = APIRouter()


@router.post("/chapters/{chapter_id}/translate", status_code=status.HTTP_200_OK)
def translate_chapter(chapter_id: int, db: Session = Depends(get_db)) -> dict:
    """Перевести главу с использованием утвержденного глоссария."""
    # Получаем главу
    chapter = db.get(Chapter, chapter_id)
    if not chapter:
        raise HTTPException(status_code=404, detail="Chapter not found")
    
    # Получаем утвержденные термины глоссария для проекта
    glossary_terms = db.query(GlossaryTerm).filter(
        GlossaryTerm.project_id == chapter.project_id,
        GlossaryTerm.status == TermStatus.APPROVED
    ).all()
    
    if not glossary_terms:
        raise HTTPException(
            status_code=400, 
            detail="No approved glossary terms found. Please approve some terms first."
        )
    
    try:
        # Переводим текст
        translated_text = translation_engine.translate_with_glossary(
            text=chapter.original_text,
            glossary_terms=glossary_terms,
            context_summary=chapter.summary
        )
        
        # Сохраняем перевод в БД
        chapter.translated_text = translated_text
        db.commit()
        
        return {
            "chapter_id": chapter_id,
            "translated_text": translated_text,
            "glossary_terms_used": len(glossary_terms),
            "message": "Translation completed successfully"
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500, 
            detail=f"Translation failed: {str(e)}"
        )


@router.get("/chapters/{chapter_id}/translation-preview")
def preview_translation(chapter_id: int, db: Session = Depends(get_db)) -> dict:
    """Предварительный просмотр перевода (без сохранения)."""
    # Получаем главу
    chapter = db.get(Chapter, chapter_id)
    if not chapter:
        raise HTTPException(status_code=404, detail="Chapter not found")
    
    # Получаем утвержденные термины глоссария
    glossary_terms = db.query(GlossaryTerm).filter(
        GlossaryTerm.project_id == chapter.project_id,
        GlossaryTerm.status == TermStatus.APPROVED
    ).all()
    
    if not glossary_terms:
        return {
            "chapter_id": chapter_id,
            "preview_available": False,
            "message": "No approved glossary terms found. Please approve some terms first.",
            "glossary_terms_count": 0
        }
    
    try:
        # Создаем предварительный перевод
        translated_text = translation_engine.translate_with_glossary(
            text=chapter.original_text,
            glossary_terms=glossary_terms,
            context_summary=chapter.summary
        )
        
        return {
            "chapter_id": chapter_id,
            "preview_available": True,
            "original_text": chapter.original_text,
            "translated_text": translated_text,
            "glossary_terms_count": len(glossary_terms),
            "glossary_terms": [
                {
                    "source_term": term.source_term,
                    "translated_term": term.translated_term,
                    "category": term.category.value
                }
                for term in glossary_terms
            ]
        }
        
    except Exception as e:
        return {
            "chapter_id": chapter_id,
            "preview_available": False,
            "message": f"Preview generation failed: {str(e)}",
            "glossary_terms_count": len(glossary_terms)
        }
