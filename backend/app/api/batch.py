from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from datetime import datetime
from typing import List

from app.deps import get_db
from app.models.project import Chapter, Project
from app.models.glossary import (
    BatchJob, BatchJobItem, GlossaryTerm, TermStatus, TermCategory, TermRelationship
)
from app.core.nlp_pipeline.term_extractor import term_extractor
from app.core.nlp_pipeline.relationship_analyzer import relationship_analyzer
from app.core.nlp_pipeline.context_summarizer import context_summarizer
from app.core.translation_engine import translation_engine
from app.services.cache_service import cache_service

router = APIRouter()


def process_batch_analyze_sync(batch_job_id: int, db: Session = None):
    """Синхронная пакетная обработка глав для извлечения терминов."""
    # Открываем новую сессию для фоновой задачи
    from app.db import SessionLocal
    local_db = db or SessionLocal()
    
    try:
        # Получаем задачу
        batch_job = local_db.get(BatchJob, batch_job_id)
        if not batch_job:
            return {"error": "Batch job not found", "batch_job_id": batch_job_id}
        
        # Обновляем статус
        batch_job.status = "running"
        batch_job.started_at = datetime.utcnow()
        local_db.commit()
        
        # Получаем элементы задачи
        job_items = local_db.query(BatchJobItem).filter(
            BatchJobItem.batch_job_id == batch_job_id
        ).all()
        
        total_items = len(job_items)
        processed_items = 0
        failed_items = 0
        total_terms = 0
        total_auto_approved = 0
        total_pending = 0
        
        for job_item in job_items:
            try:
                # Обновляем статус элемента
                job_item.status = "processing"
                job_item.started_at = datetime.utcnow()
                local_db.commit()
                
                # Получаем главу и проект
                chapter = local_db.get(Chapter, job_item.item_id)
                if not chapter:
                    raise Exception("Chapter not found")
                
                project = local_db.get(Project, chapter.project_id)
                if not project:
                    raise Exception("Project not found")
                
                # Извлекаем термины с учетом жанра проекта
                from app.models.project import ProjectGenre
                project_genre = project.genre
                if isinstance(project_genre, str):
                    try:
                        project_genre = ProjectGenre(project_genre)
                    except Exception:
                        project_genre = ProjectGenre.OTHER
                extracted_terms = term_extractor.extract_terms_with_frequency(chapter.original_text, project_genre)
                
                # Сохраняем термины с автоматическим утверждением
                saved_terms = []
                auto_approved_count = 0
                
                for term_data in extracted_terms:
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
                
                # Анализируем связи
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
                
                # Создаем саммари
                chapter_summary = context_summarizer.summarize_context(
                    chapter.original_text,
                    chapter.title
                )
                
                # Обновляем главу
                chapter.summary = chapter_summary
                chapter.processed_at = datetime.utcnow()
                
                # Обновляем статистику
                total_terms += len(saved_terms)
                total_auto_approved += auto_approved_count
                total_pending += (len(saved_terms) - auto_approved_count)
                
                # Обновляем элемент задачи
                job_item.status = "completed"
                job_item.completed_at = datetime.utcnow()
                job_item.result = {
                    "extracted_terms": len(saved_terms),
                    "auto_approved_terms": auto_approved_count,
                    "pending_terms": len(saved_terms) - auto_approved_count,
                    "relationships": len(relationships) if 'relationships' in locals() else 0,
                    "summary_created": bool(chapter_summary)
                }
                
                processed_items += 1
                local_db.commit()
                
            except Exception as e:
                print(f"Error processing job item {job_item.id}: {e}")
                job_item.status = "failed"
                job_item.completed_at = datetime.utcnow()
                job_item.error_message = str(e)
                failed_items += 1
                local_db.commit()
        
        # Обновляем статус задачи
        batch_job.status = "completed"
        batch_job.completed_at = datetime.utcnow()
        batch_job.job_data = {
            "total_items": total_items,
            "processed_items": processed_items,
            "failed_items": failed_items,
            "total_terms": total_terms,
            "total_auto_approved": total_auto_approved,
            "total_pending": total_pending
        }
        local_db.commit()
        
        return {
            "batch_job_id": batch_job_id,
            "status": "completed",
            "total_items": total_items,
            "processed_items": processed_items,
            "failed_items": failed_items,
            "total_terms": total_terms,
            "total_auto_approved": total_auto_approved,
            "total_pending": total_pending
        }
        
    except Exception as e:
        if 'batch_job' in locals():
            batch_job.status = "failed"
            batch_job.completed_at = datetime.utcnow()
            batch_job.error_message = str(e)
            local_db.commit()
        
        return {"error": str(e), "batch_job_id": batch_job_id}
    finally:
        # Закрываем локальную сессию только если мы её создали
        if not db:
            local_db.close()


def process_batch_translate_sync(batch_job_id: int, db: Session = None):
    """Синхронная пакетная обработка глав для перевода."""
    # Открываем новую сессию для фоновой задачи
    from app.db import SessionLocal
    local_db = db or SessionLocal()
    
    try:
        # Получаем задачу
        batch_job = local_db.get(BatchJob, batch_job_id)
        if not batch_job:
            return {"error": "Batch job not found", "batch_job_id": batch_job_id}
        
        # Обновляем статус
        batch_job.status = "running"
        batch_job.started_at = datetime.utcnow()
        local_db.commit()
        
        # Получаем элементы задачи
        job_items = local_db.query(BatchJobItem).filter(
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
                local_db.commit()
                
                # Получаем главу
                chapter = local_db.get(Chapter, job_item.item_id)
                if not chapter:
                    raise Exception("Chapter not found")
                
                # Получаем утвержденные термины глоссария
                glossary_terms = local_db.query(GlossaryTerm).filter(
                    GlossaryTerm.project_id == chapter.project_id,
                    GlossaryTerm.status == TermStatus.APPROVED
                ).all()
                
                if not glossary_terms:
                    raise Exception("No approved glossary terms found")
                
                # Получаем общее саммари проекта (если есть)
                project_summary = None
                project_chapters = local_db.query(Chapter).filter(
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
                
                # Переводим текст
                translated_text = translation_engine.translate_with_glossary(
                    text=chapter.original_text,
                    glossary_terms=glossary_terms,
                    context_summary=chapter.summary,
                    project_summary=project_summary
                )
                
                # Сохраняем перевод
                chapter.translated_text = translated_text
                
                # Кэшируем перевод
                glossary_hash = cache_service.generate_glossary_hash([
                    {
                        "source_term": term.source_term,
                        "translated_term": term.translated_term,
                        "category": term.category
                    }
                    for term in glossary_terms
                ])
                cache_service.cache_translation(chapter.id, glossary_hash, translated_text)
                
                # Обновляем элемент задачи
                job_item.status = "completed"
                job_item.completed_at = datetime.utcnow()
                job_item.result = {
                    "translated": True,
                    "glossary_terms_used": len(glossary_terms),
                    "context_used": bool(chapter.summary),
                    "project_context_used": bool(project_summary)
                }
                
                processed_items += 1
                local_db.commit()
                
            except Exception as e:
                print(f"Error processing job item {job_item.id}: {e}")
                job_item.status = "failed"
                job_item.completed_at = datetime.utcnow()
                job_item.error_message = str(e)
                failed_items += 1
                local_db.commit()
        
        # Обновляем статус задачи
        batch_job.status = "completed"
        batch_job.completed_at = datetime.utcnow()
        batch_job.job_data = {
            "total_items": total_items,
            "processed_items": processed_items,
            "failed_items": failed_items
        }
        local_db.commit()
        
        return {
            "batch_job_id": batch_job_id,
            "status": "completed",
            "total_items": total_items,
            "processed_items": processed_items,
            "failed_items": failed_items
        }
        
    except Exception as e:
        if 'batch_job' in locals():
            batch_job.status = "failed"
            batch_job.completed_at = datetime.utcnow()
            batch_job.error_message = str(e)
            local_db.commit()
        
        return {"error": str(e), "batch_job_id": batch_job_id}
    finally:
        # Закрываем локальную сессию только если мы её создали
        if not db:
            local_db.close()


@router.post("/analyze", status_code=status.HTTP_200_OK)
def create_batch_analyze_job(
    chapter_ids: List[int],
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
) -> dict:
    """Создать задачу пакетного анализа глав."""
    if not chapter_ids:
        raise HTTPException(status_code=400, detail="No chapter IDs provided")
    
    # Проверяем, что все главы существуют
    chapters = db.query(Chapter).filter(Chapter.id.in_(chapter_ids)).all()
    if len(chapters) != len(chapter_ids):
        raise HTTPException(status_code=404, detail="Some chapters not found")
    
    # Получаем project_id из первой главы (все главы должны быть из одного проекта)
    project_id = chapters[0].project_id
    
    # Создаем задачу
    batch_job = BatchJob(
        project_id=project_id,
        job_type="analyze",
        status="pending",
        total_items=len(chapter_ids),
        created_at=datetime.utcnow()
    )
    db.add(batch_job)
    db.commit()
    
    # Создаем элементы задачи
    for chapter_id in chapter_ids:
        job_item = BatchJobItem(
            project_id=project_id,
            batch_job_id=batch_job.id,
            item_type="chapter",
            item_id=chapter_id,
            status="pending"
        )
        db.add(job_item)
    
    db.commit()
    
    # Запускаем обработку в фоне
    background_tasks.add_task(process_batch_analyze_sync, batch_job.id)
    
    return {
        "batch_job_id": batch_job.id,
        "status": "pending",
        "total_items": len(chapter_ids),
        "message": "Batch analysis job created"
    }


@router.post("/translate", status_code=status.HTTP_200_OK)
def create_batch_translate_job(
    chapter_ids: List[int],
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
) -> dict:
    """Создать задачу пакетного перевода глав."""
    if not chapter_ids:
        raise HTTPException(status_code=400, detail="No chapter IDs provided")
    
    # Проверяем, что все главы существуют
    chapters = db.query(Chapter).filter(Chapter.id.in_(chapter_ids)).all()
    if len(chapters) != len(chapter_ids):
        raise HTTPException(status_code=404, detail="Some chapters not found")
    
    # Получаем project_id из первой главы (все главы должны быть из одного проекта)
    project_id = chapters[0].project_id
    
    # Создаем задачу
    batch_job = BatchJob(
        project_id=project_id,
        job_type="translate",
        status="pending",
        total_items=len(chapter_ids),
        created_at=datetime.utcnow()
    )
    db.add(batch_job)
    db.commit()
    
    # Создаем элементы задачи
    for chapter_id in chapter_ids:
        job_item = BatchJobItem(
            project_id=project_id,
            batch_job_id=batch_job.id,
            item_type="chapter",
            item_id=chapter_id,
            status="pending"
        )
        db.add(job_item)
    
    db.commit()
    
    # Запускаем обработку в фоне
    background_tasks.add_task(process_batch_translate_sync, batch_job.id)
    
    return {
        "batch_job_id": batch_job.id,
        "status": "pending",
        "total_items": len(chapter_ids),
        "message": "Batch translation job created"
    }


@router.get("/jobs/{job_id}")
def get_batch_job_status(job_id: int, db: Session = Depends(get_db)) -> dict:
    """Получить статус пакетной задачи."""
    batch_job = db.get(BatchJob, job_id)
    if not batch_job:
        raise HTTPException(status_code=404, detail="Batch job not found")
    
    # Получаем элементы задачи
    job_items = db.query(BatchJobItem).filter(
        BatchJobItem.batch_job_id == job_id
    ).all()
    
    return {
        "batch_job_id": batch_job.id,
        "job_type": batch_job.job_type,
        "status": batch_job.status,
        "created_at": batch_job.created_at,
        "started_at": batch_job.started_at,
        "completed_at": batch_job.completed_at,
        "error": batch_job.error_message,
        "result": batch_job.job_data,
        "items": [
            {
                "item_id": item.item_id,
                "status": item.status,
                "started_at": item.started_at,
                "completed_at": item.completed_at,
                "error": item.error_message,
                "result": item.result
            }
            for item in job_items
        ]
    }
