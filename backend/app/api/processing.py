from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from datetime import datetime

from app.deps import get_db
from app.models.project import Chapter, Project
from app.core.nlp_pipeline.term_extractor import term_extractor
from app.core.nlp_pipeline.relationship_analyzer import relationship_analyzer
from app.core.nlp_pipeline.context_summarizer import context_summarizer
from app.models.glossary import GlossaryTerm, TermStatus, TermCategory, TermRelationship
from app.services.cache_service import cache_service

router = APIRouter()


def process_chapter_sync(chapter_id: int, db: Session = None):
    """Синхронная обработка главы для извлечения терминов."""
    # Открываем новую сессию для фоновой задачи
    from app.db import SessionLocal
    local_db = db or SessionLocal()
    
    try:
        # Получаем главу и проект
        chapter = local_db.get(Chapter, chapter_id)
        if not chapter:
            return {"error": "Chapter not found", "chapter_id": chapter_id}
        
        project = local_db.get(Project, chapter.project_id)
        if not project:
            return {"error": "Project not found", "chapter_id": chapter_id}
        
        # 1. Извлекаем термины с учетом жанра проекта
        # project.genre в БД хранится как строка; приведем к Enum при необходимости
        from app.models.project import ProjectGenre
        project_genre = project.genre
        if isinstance(project_genre, str):
            try:
                project_genre = ProjectGenre(project_genre)
            except Exception:
                project_genre = ProjectGenre.OTHER
        extracted_terms = term_extractor.extract_terms_with_frequency(chapter.original_text, project_genre)
        
        # Сохраняем термины в БД с автоматическим утверждением
        saved_terms = []
        auto_approved_count = 0
        
        for term_data in extracted_terms:
            # Проверяем, не существует ли уже такой термин
            existing_term = local_db.query(GlossaryTerm).filter(
                GlossaryTerm.project_id == chapter.project_id,
                GlossaryTerm.source_term == term_data["source_term"]
            ).first()
            
            if not existing_term:
                # Определяем статус на основе auto_approve флага
                auto_approve = term_data.get("auto_approve", False)
                initial_status = TermStatus.APPROVED if auto_approve else TermStatus.PENDING
                
                if auto_approve:
                    auto_approved_count += 1
                
                term = GlossaryTerm(
                    project_id=chapter.project_id,
                    source_term=term_data["source_term"],
                    translated_term=term_data.get("translated_term", ""),
                    category=term_data.get("category", TermCategory.OTHER),
                    status=initial_status,
                    context=term_data.get("context", ""),
                    frequency=term_data.get("frequency", 1),
                    approved_at=datetime.utcnow() if auto_approve else None
                )
                local_db.add(term)
                saved_terms.append(term)
        
        # 2. Анализируем связи между терминами
        relationships = []
        if len(saved_terms) > 1:
            relationships = relationship_analyzer.analyze_relationships(
                chapter.original_text, 
                saved_terms  # Pass GlossaryTerm objects, not strings
            )
            
            for rel_data in relationships:
                # Find the source and target terms by their source_term strings
                source_term_obj = local_db.query(GlossaryTerm).filter(
                    GlossaryTerm.project_id == chapter.project_id,
                    GlossaryTerm.source_term == rel_data["source_term"]
                ).first()
                
                target_term_obj = local_db.query(GlossaryTerm).filter(
                    GlossaryTerm.project_id == chapter.project_id,
                    GlossaryTerm.source_term == rel_data["target_term"]
                ).first()
                
                if source_term_obj and target_term_obj:
                    # Безопасно получаем relation_type, используя relation_type или relationType
                    relation_type = rel_data.get("relation_type") or rel_data.get("relationType") or "other"
                    confidence = rel_data.get("confidence", 50)  # По умолчанию 50%
                    context = rel_data.get("context", "")
                    
                    relationship = TermRelationship(
                        project_id=chapter.project_id,
                        source_term_id=source_term_obj.id,
                        target_term_id=target_term_obj.id,
                        relation_type=relation_type,
                        confidence=confidence,
                        context=context
                    )
                    local_db.add(relationship)
        
        # 3. Создаем саммари главы (с нормализацией исходного текста)
        normalized_text = chapter.original_text.replace('\r\n', '\n')
        # Удалим избыточные пустые строки
        lines = [ln.strip() for ln in normalized_text.split('\n')]
        compact_text = "\n".join([ln for ln in lines if ln != ""])  # убираем пустые строки
        chapter_summary = context_summarizer.summarize_context(
            compact_text,
            chapter.title
        )
        
        # Обновляем главу
        chapter.summary = chapter_summary
        chapter.processed_at = datetime.utcnow()
        
        # Сохраняем все изменения
        local_db.commit()
        
        # Инвалидируем кэш глоссария для проекта
        cache_service.invalidate_glossary_cache(chapter.project_id)
        
        return {
            "chapter_id": chapter_id,
            "extracted_terms": len(saved_terms),
            "auto_approved_terms": auto_approved_count,
            "pending_terms": len(saved_terms) - auto_approved_count,
            "relationships": len(relationships),
            "summary_created": bool(chapter_summary),
            "project_genre": getattr(project_genre, "value", project_genre)
        }
        
    except Exception as e:
        local_db.rollback()
        return {"error": str(e), "chapter_id": chapter_id}
    finally:
        # Закрываем локальную сессию только если мы её создали
        if not db:
            local_db.close()


@router.post("/chapters/{chapter_id}/analyze", status_code=status.HTTP_200_OK)
def analyze_chapter(
    chapter_id: int, 
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
) -> dict:
    """Запустить анализ главы для извлечения терминов (синхронно)."""
    # Проверяем, что глава существует
    chapter = db.get(Chapter, chapter_id)
    if not chapter:
        raise HTTPException(status_code=404, detail="Chapter not found")
    
    # Выполняем анализ синхронно
    result = process_chapter_sync(chapter_id, db)
    
    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])
    
    return result


@router.post("/chapters/{chapter_id}/analyze-async", status_code=status.HTTP_202_ACCEPTED)
def analyze_chapter_async(
    chapter_id: int, 
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
) -> dict:
    """Запустить анализ главы в фоновом режиме (если доступен)."""
    # Проверяем, что глава существует
    chapter = db.get(Chapter, chapter_id)
    if not chapter:
        raise HTTPException(status_code=404, detail="Chapter not found")
    
    # Добавляем задачу в фоновые задачи FastAPI
    background_tasks.add_task(process_chapter_sync, chapter_id)
    
    return {
        "message": "Analysis started in background",
        "chapter_id": chapter_id,
        "note": "Processing will continue in background. Check chapter status for updates."
    }


@router.get("/chapters/{chapter_id}/status")
def get_chapter_status(chapter_id: int, db: Session = Depends(get_db)) -> dict:
    """Получить статус обработки главы."""
    chapter = db.get(Chapter, chapter_id)
    if not chapter:
        raise HTTPException(status_code=404, detail="Chapter not found")
    
    # Подсчитываем количество терминов для этой главы
    terms_count = db.query(GlossaryTerm).filter(
        GlossaryTerm.project_id == chapter.project_id
    ).count()
    
    return {
        "chapter_id": chapter_id,
        "processed": chapter.processed_at is not None,
        "processed_at": chapter.processed_at,
        "summary": chapter.summary is not None,
        "terms_count": terms_count,
        "status": "completed" if chapter.processed_at else "pending"
    }
