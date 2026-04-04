from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from app.db import SessionLocal
from app.deps import get_db
from app.models.project import Chapter, Project, ProjectGenre, AnalysisStatus
from app.core.nlp_pipeline.term_extractor import term_extractor
from app.core.nlp_pipeline.relationship_analyzer import relationship_analyzer
from app.core.nlp_pipeline.context_summarizer import context_summarizer
from app.models.glossary import (
    GlossaryTerm,
    TermStatus,
    TermCategory,
    TermRelationship,
    TermOccurrence,
)
from app.services.cache_service import cache_service

router = APIRouter()


def process_chapter_sync(chapter_id: int, db: Session = None):
    """Синхронная обработка главы для извлечения терминов."""
    import logging

    logger = logging.getLogger(__name__)

    local_db = db or SessionLocal()

    try:
        # Получаем главу и проект
        logger.info(f"[STEP 1] Loading chapter {chapter_id}")
        chapter = local_db.get(Chapter, chapter_id)
        if not chapter:
            return {"error": "Chapter not found", "chapter_id": chapter_id}

        project = local_db.get(Project, chapter.project_id)
        if not project:
            return {"error": "Project not found", "chapter_id": chapter_id}

        logger.info(
            f"[STEP 2] Extracting terms for chapter '{chapter.title}', genre: {project.genre}"
        )

        # Обновляем статус: извлечение терминов
        chapter.analysis_status = AnalysisStatus.EXTRACTING.value
        chapter.analysis_error = None
        local_db.commit()

        # 1. Извлекаем термины с учетом жанра проекта
        project_genre = project.genre
        if isinstance(project_genre, str):
            try:
                project_genre = ProjectGenre(project_genre)
            except Exception:
                project_genre = ProjectGenre.OTHER
        extracted_terms = term_extractor.extract_terms_with_frequency(
            text=chapter.original_text,
            project_genre=project_genre,
            source_language=project.source_language,
            target_language=project.target_language,
            custom_instructions=project.custom_genre_instructions,
        )
        logger.info(f"[STEP 2 DONE] Extracted {len(extracted_terms)} terms")

        # Сохраняем термины в БД с автоматическим утверждением
        saved_terms = []
        auto_approved_count = 0

        # Optimization: Batch fetch existing terms to avoid N+1 queries
        # Normalize source_terms to lowercase for case-insensitive dedup (Bug 2 fix)
        source_terms_normalized = [t["source_term"].lower() for t in extracted_terms]
        # Also store lowercased keys in extracted_terms at this point
        for t in extracted_terms:
            t["source_term"] = t["source_term"].lower()

        existing_terms_query = (
            local_db.query(GlossaryTerm)
            .filter(
                GlossaryTerm.project_id == chapter.project_id,
                GlossaryTerm.source_term.in_(source_terms_normalized),
            )
            .all()
        )
        existing_terms_map = {term.source_term: term for term in existing_terms_query}

        # Optimization: Batch fetch occurrences for existing terms
        existing_term_ids = [term.id for term in existing_terms_query]
        existing_occurrences_map = {}
        if existing_term_ids:
            occurrences = (
                local_db.query(TermOccurrence)
                .filter(
                    TermOccurrence.chapter_id == chapter.id,
                    TermOccurrence.term_id.in_(existing_term_ids),
                )
                .all()
            )
            existing_occurrences_map = {occ.term_id: occ for occ in occurrences}

        for term_data in extracted_terms:
            # Проверяем, не существует ли уже такой термин
            existing_term = existing_terms_map.get(term_data["source_term"])

            if existing_term:
                new_frequency = term_data.get("frequency", 1)

                # Update TermOccurrence for this chapter
                occurrence = existing_occurrences_map.get(existing_term.id)

                if occurrence:
                    # Re-analysis of the same chapter: REPLACE, don't accumulate.
                    # Adjust the global frequency counter by the delta.
                    old_freq = occurrence.frequency
                    occurrence.frequency = new_frequency
                    existing_term.frequency += new_frequency - old_freq
                else:
                    # First time seeing this term in this specific chapter.
                    occurrence = TermOccurrence(
                        project_id=chapter.project_id,
                        term_id=existing_term.id,
                        chapter_id=chapter.id,
                        frequency=new_frequency,
                    )
                    local_db.add(occurrence)
                    existing_term.frequency += new_frequency
                    # Add to map so we don't try to create it again
                    existing_occurrences_map[existing_term.id] = occurrence

                # Обновляем first/last chapter (logic remains same)
                if existing_term.first_chapter_id:
                    # Check if current chapter order is lower
                    if chapter.order < (
                        existing_term.first_chapter.order
                        if existing_term.first_chapter
                        else float("inf")
                    ):
                        existing_term.first_chapter_id = chapter.id
                else:
                    existing_term.first_chapter_id = chapter.id

                if existing_term.last_chapter_id:
                    # Check if current chapter order is higher
                    if chapter.order > (
                        existing_term.last_chapter.order
                        if existing_term.last_chapter
                        else -1
                    ):
                        existing_term.last_chapter_id = chapter.id
                else:
                    existing_term.last_chapter_id = chapter.id

                # Можно также обновить контекст, если он пустой, но пока оставим как есть
                # existing_term.context = existing_term.context or term_data.get("context", "")
            else:
                # Определяем статус на основе auto_approve флага
                auto_approve = term_data.get("auto_approve", False)
                initial_status = (
                    TermStatus.APPROVED if auto_approve else TermStatus.PENDING
                )

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
                    approved_at=datetime.now(timezone.utc) if auto_approve else None,
                    first_chapter_id=chapter.id,
                    last_chapter_id=chapter.id,
                )
                local_db.add(term)
                local_db.flush()  # To get term.id

                occurrence = TermOccurrence(
                    project_id=chapter.project_id,
                    term_id=term.id,
                    chapter_id=chapter.id,
                    frequency=term_data.get("frequency", 1),
                )
                local_db.add(occurrence)

                saved_terms.append(term)

        logger.info(f"[STEP 3] Saved {len(saved_terms)} new terms to DB")

        # 2. Анализируем связи между терминами
        relationships = []
        if len(saved_terms) > 1:
            # Обновляем статус: анализ связей
            chapter.analysis_status = AnalysisStatus.RELATIONSHIPS.value
            local_db.commit()

            logger.info(
                f"[STEP 4] Analyzing relationships between {len(saved_terms)} terms"
            )
            try:
                relationships = relationship_analyzer.analyze_relationships(
                    chapter.original_text,
                    saved_terms,  # Pass GlossaryTerm objects, not strings
                    project_genre=getattr(project_genre, "value", project_genre),
                    target_language=project.target_language,
                )
                logger.info(f"[STEP 4 DONE] Found {len(relationships)} relationships")
            except Exception as rel_error:
                logger.error(
                    f"[STEP 4 ERROR] Relationship analysis failed: {rel_error}",
                    exc_info=True,
                )
                # Continue without relationships

            # Optimize: Pre-fetch all relevant terms in one query
            unique_terms = set()
            for rel in relationships:
                if "source_term" in rel:
                    unique_terms.add(rel["source_term"])
                if "target_term" in rel:
                    unique_terms.add(rel["target_term"])

            # Fetch terms
            terms = []
            if unique_terms:
                terms = (
                    local_db.query(GlossaryTerm)
                    .filter(
                        GlossaryTerm.project_id == chapter.project_id,
                        GlossaryTerm.source_term.in_(unique_terms),
                    )
                    .all()
                )

            # Create map for quick lookup
            term_map = {term.source_term: term for term in terms}

            for rel_data in relationships:
                try:
                    # Find the source and target terms from map
                    source_term_obj = term_map.get(rel_data.get("source_term"))
                    target_term_obj = term_map.get(rel_data.get("target_term"))

                    if source_term_obj and target_term_obj:
                        # Безопасно получаем relation_type, используя relation_type или relationType
                        relation_type = (
                            rel_data.get("relation_type")
                            or rel_data.get("relationType")
                            or "other"
                        )
                        confidence = rel_data.get("confidence", 50)  # По умолчанию 50%
                        context = rel_data.get("context", "")

                        relationship = TermRelationship(
                            project_id=chapter.project_id,
                            source_term_id=source_term_obj.id,
                            target_term_id=target_term_obj.id,
                            relation_type=relation_type,
                            confidence=confidence,
                            context=context,
                        )
                        local_db.add(relationship)
                except Exception as rel_save_error:
                    logger.warning(f"Failed to save relationship: {rel_save_error}")
        else:
            logger.info(
                f"[STEP 4] Skipping relationship analysis (only {len(saved_terms)} terms)"
            )

        # 3. Создаем саммари главы (с нормализацией исходного текста)
        # Обновляем статус: создание саммари
        chapter.analysis_status = AnalysisStatus.SUMMARIZING.value
        local_db.commit()

        logger.info("[STEP 5] Creating chapter summary")
        try:
            normalized_text = chapter.original_text.replace("\r\n", "\n")
            # Удалим избыточные пустые строки
            lines = [ln.strip() for ln in normalized_text.split("\n")]
            compact_text = "\n".join(
                [ln for ln in lines if ln != ""]
            )  # убираем пустые строки
            chapter_summary = context_summarizer.summarize_context(
                compact_text,
                chapter.title,
                target_language=project.target_language,
            )
            logger.info(
                f"[STEP 5 DONE] Summary created, length: {len(chapter_summary) if chapter_summary else 0}"
            )
        except Exception as sum_error:
            logger.error(
                f"[STEP 5 ERROR] Summary creation failed: {sum_error}", exc_info=True
            )
            chapter_summary = None

        # Обновляем главу
        logger.info("[STEP 6] Updating chapter with summary and processed_at")
        chapter.summary = chapter_summary
        chapter.processed_at = datetime.now(timezone.utc)
        chapter.analysis_status = AnalysisStatus.COMPLETED.value
        chapter.analysis_error = None

        # Сохраняем все изменения
        logger.info("[STEP 7] Committing all changes to DB")
        local_db.commit()
        logger.info("[STEP 7 DONE] Commit successful")

        # Инвалидируем кэш глоссария для проекта
        try:
            cache_service.invalidate_glossary_cache(chapter.project_id)
        except Exception as e:
            # Не фейлим весь запрос из-за кэша
            logger.warning(f"Cache invalidation failed (non-critical): {e}")

        result = {
            "chapter_id": chapter_id,
            "extracted_terms": len(saved_terms),
            "auto_approved_terms": auto_approved_count,
            "pending_terms": len(saved_terms) - auto_approved_count,
            "relationships": len(relationships),
            "summary_created": bool(chapter_summary),
            "project_genre": getattr(project_genre, "value", project_genre),
        }
        logger.info(f"[COMPLETE] Analysis result: {result}")
        return result

    except Exception as e:
        logger.error(f"[FATAL ERROR] process_chapter_sync failed: {e}", exc_info=True)
        try:
            # Помечаем как failed
            chapter = local_db.get(Chapter, chapter_id)
            if chapter:
                chapter.analysis_status = AnalysisStatus.FAILED.value
                chapter.analysis_error = str(e)
                local_db.commit()
        except Exception:
            local_db.rollback()
        return {"error": str(e), "chapter_id": chapter_id}
    finally:
        # Закрываем локальную сессию только если мы её создали
        if not db:
            local_db.close()


@router.post("/chapters/{chapter_id}/analyze", status_code=status.HTTP_200_OK)
def analyze_chapter(
    chapter_id: int, background_tasks: BackgroundTasks, db: Session = Depends(get_db)
) -> dict:
    """Запустить анализ главы для извлечения терминов (синхронно)."""
    import logging

    logger = logging.getLogger(__name__)

    # Проверяем, что глава существует
    chapter = db.get(Chapter, chapter_id)
    if not chapter:
        raise HTTPException(status_code=404, detail="Chapter not found")

    # Выполняем анализ синхронно
    logger.info(f"[API] Starting analysis for chapter {chapter_id}")
    result = process_chapter_sync(chapter_id, db)
    logger.info(f"[API] Analysis returned: {result}")

    if "error" in result:
        logger.error(f"[API] Analysis error: {result['error']}")
        raise HTTPException(status_code=500, detail=result["error"])

    logger.info(f"[API] Returning successful result for chapter {chapter_id}")
    return result


@router.post(
    "/chapters/{chapter_id}/analyze-async", status_code=status.HTTP_202_ACCEPTED
)
def analyze_chapter_async(
    chapter_id: int, background_tasks: BackgroundTasks, db: Session = Depends(get_db)
) -> dict:
    """Запустить анализ главы в фоновом режиме."""
    # Проверяем, что глава существует
    chapter = db.get(Chapter, chapter_id)
    if not chapter:
        raise HTTPException(status_code=404, detail="Chapter not found")

    # Устанавливаем начальный статус PENDING
    chapter.analysis_status = AnalysisStatus.PENDING.value
    chapter.analysis_error = None
    db.commit()

    # Добавляем задачу в фоновые задачи FastAPI
    background_tasks.add_task(process_chapter_sync, chapter_id)

    return {
        "message": "Analysis started in background",
        "chapter_id": chapter_id,
        "status": "pending",
    }


@router.get("/chapters/{chapter_id}/status")
def get_chapter_status(chapter_id: int, db: Session = Depends(get_db)) -> dict:
    """Получить статус обработки главы."""
    chapter = db.get(Chapter, chapter_id)
    if not chapter:
        raise HTTPException(status_code=404, detail="Chapter not found")

    # Подсчитываем количество терминов для этой главы
    terms_count = (
        db.query(GlossaryTerm)
        .filter(GlossaryTerm.project_id == chapter.project_id)
        .count()
    )

    return {
        "chapter_id": chapter_id,
        "title": chapter.title,
        "processed": chapter.processed_at is not None,
        "processed_at": chapter.processed_at,
        "has_summary": chapter.summary is not None,
        "has_translation": chapter.translated_text is not None,
        "terms_count": terms_count,
        "analysis_status": chapter.analysis_status,
        "analysis_error": chapter.analysis_error,
        "translation_status": chapter.translation_status,
        "translation_error": chapter.translation_error,
    }
