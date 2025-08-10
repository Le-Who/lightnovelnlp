from typing import List

from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.deps import get_db
from app.models.project import Project, Chapter
from app.schemas.project import ProjectCreate, ProjectRead, ChapterCreate, ChapterRead, ChapterUpdate
import io
try:
    import PyPDF2
except Exception:
    PyPDF2 = None

from app.core.nlp_pipeline.context_summarizer import context_summarizer
import re

router = APIRouter()


@router.get("/", response_model=List[ProjectRead])
def list_projects(db: Session = Depends(get_db)) -> List[Project]:
    return db.query(Project).order_by(Project.created_at.desc()).all()


@router.post("/", response_model=ProjectRead, status_code=status.HTTP_201_CREATED)
def create_project(payload: ProjectCreate, db: Session = Depends(get_db)) -> Project:
    exists = db.query(Project).filter(Project.name == payload.name).first()
    if exists:
        raise HTTPException(status_code=400, detail="Project with this name already exists")
    # Учитываем жанр из payload (может прийти как Enum или как строка)
    genre_value = getattr(payload.genre, "value", payload.genre)
    project = Project(name=payload.name, genre=genre_value)
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


@router.get("/{project_id}", response_model=ProjectRead)
def get_project(project_id: int, db: Session = Depends(get_db)) -> Project:
    project = db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(project_id: int, db: Session = Depends(get_db)):
    project = db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Явно удаляем зависимые сущности, чтобы избежать обращения к отсутствующим колонкам
    from app.models.glossary import GlossaryTerm, TermRelationship, GlossaryVersion, BatchJob, BatchJobItem
    from app.models.project import Chapter

    db.query(TermRelationship).filter(TermRelationship.project_id == project_id).delete(synchronize_session=False)
    db.query(GlossaryTerm).filter(GlossaryTerm.project_id == project_id).delete(synchronize_session=False)
    db.query(GlossaryVersion).filter(GlossaryVersion.project_id == project_id).delete(synchronize_session=False)
    db.query(BatchJobItem).filter(BatchJobItem.project_id == project_id).delete(synchronize_session=False)
    db.query(BatchJob).filter(BatchJob.project_id == project_id).delete(synchronize_session=False)
    db.query(Chapter).filter(Chapter.project_id == project_id).delete(synchronize_session=False)

    # Теперь удаляем сам проект
    db.delete(project)
    db.commit()


# Главы
@router.get("/{project_id}/chapters", response_model=List[ChapterRead])
def list_chapters(
    project_id: int,
    db: Session = Depends(get_db),
    limit: int | None = Query(default=None, gt=0, le=1000),
    offset: int = Query(default=0, ge=0),
    search: str | None = None,
    sort_by: str = Query(default="id"),
    order: str = Query(default="asc")
) -> List[Chapter]:
    """Получить все главы проекта (пагинация/поиск/сортировка)."""
    q = db.query(Chapter).filter(Chapter.project_id == project_id)
    if search:
        s = f"%{search}%"
        from sqlalchemy import or_
        q = q.filter(or_(Chapter.title.ilike(s), Chapter.original_text.ilike(s)))
    sort_map = {
        "id": Chapter.id,
        "title": Chapter.title,
        "order": Chapter.order,
        "created_at": Chapter.created_at,
        "processed_at": Chapter.processed_at,
    }
    sort_col = sort_map.get(sort_by, Chapter.id)
    q = q.order_by(sort_col.desc() if order.lower() == "desc" else sort_col.asc())
    if offset:
        q = q.offset(offset)
    if limit:
        q = q.limit(limit)
    return q.all()


@router.post("/{project_id}/chapters", response_model=ChapterRead, status_code=status.HTTP_201_CREATED)
def create_chapter(
    project_id: int,
    payload: ChapterCreate,
    db: Session = Depends(get_db)
) -> Chapter:
    """Создать новую главу в проекте."""
    # Проверяем, что проект существует
    project = db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Определяем порядок новой главы
    max_order = db.query(func.max(Chapter.order)).filter(Chapter.project_id == project_id).scalar() or 0
    
    chapter = Chapter(
        project_id=project_id,
        title=payload.title,
        original_text=payload.original_text,
        order=max_order + 1
    )
    
    db.add(chapter)
    db.commit()
    db.refresh(chapter)
    return chapter


@router.post("/{project_id}/chapters/upload", response_model=ChapterRead, status_code=status.HTTP_201_CREATED)
def create_chapter_from_file(
    project_id: int,
    title: str = "Глава 1", # Default title for uploaded chapters
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
) -> Chapter:
    """Создать главу из файла (txt, pdf, rtf, doc - простая поддержка)."""
    project = db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    content_bytes = file.file.read()
    text = ""
    filename = (file.filename or "").lower()
    if filename.endswith(".txt"):
        text = content_bytes.decode(errors="ignore")
    elif filename.endswith(".pdf") and PyPDF2 is not None:
        try:
            reader = PyPDF2.PdfReader(io.BytesIO(content_bytes))
            pages = [page.extract_text() or "" for page in reader.pages]
            text = "\n".join(pages)
        except Exception:
            raise HTTPException(status_code=400, detail="Failed to parse PDF")
    elif filename.endswith(".rtf"):
        # Простейшее извлечение: удалим RTF теги
        raw = content_bytes.decode(errors="ignore")
        text = re.sub(r"\\[a-zA-Z]+[0-9]* ?|[{}]", "", raw)
    elif filename.endswith(".doc"):
        # .doc без внешних зависимостей корректно не парсится; попытаемся как текст
        text = content_bytes.decode(errors="ignore")
    else:
        raise HTTPException(status_code=400, detail="Unsupported file type. Use txt/pdf/rtf/doc")

    if not text.strip():
        raise HTTPException(status_code=400, detail="File has no extractable text")

    # Определяем порядок новой главы
    max_order = db.query(func.max(Chapter.order)).filter(Chapter.project_id == project_id).scalar() or 0
    
    chapter = Chapter(
        project_id=project_id,
        title=title,
        original_text=text,
        order=max_order + 1
    )
    db.add(chapter)
    db.commit()
    db.refresh(chapter)
    return chapter


@router.post("/{project_id}/upload_chapters")
def upload_chapters_from_file(
    project_id: int,
    file: UploadFile = File(...),
    chapter_pattern: str = "Глава \\d+",
    db: Session = Depends(get_db)
):
    """Загрузить главы из текстового файла."""
    # Проверяем существование проекта
    project = db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Проверяем тип файла
    if not file.filename.endswith('.txt'):
        raise HTTPException(
            status_code=400, 
            detail="Only .txt files are supported"
        )
    
    try:
        # Читаем содержимое файла
        content = file.file.read().decode('utf-8')
        
        # Разделяем текст на главы по паттерну
        pattern = re.compile(f"\\n({chapter_pattern})", re.IGNORECASE)
        # Находим все совпадения с их позициями
        matches = list(pattern.finditer(content))
        
        if not matches:
            raise HTTPException(
                status_code=400,
                detail="No chapters found with the specified pattern"
            )
        
        created_chapters = []
        
        # Обрабатываем текст до первой главы
        first_match = matches[0]
        if first_match.start() > 0:
            intro_text = content[:first_match.start()].strip()
            if intro_text:
                intro_chapter = Chapter(
                    project_id=project_id,
                    title="Введение",
                    original_text=intro_text,
                    order=0
                )
                db.add(intro_chapter)
                created_chapters.append(intro_chapter)
        
        # Обрабатываем найденные главы
        for i, match in enumerate(matches):
            chapter_title = match.group(1)
            
            # Определяем конец главы (до следующей главы или до конца файла)
            if i + 1 < len(matches):
                next_match = matches[i + 1]
                chapter_content = content[match.end():next_match.start()].strip()
            else:
                chapter_content = content[match.end():].strip()
            
            if chapter_content:  # Пропускаем пустые главы
                chapter = Chapter(
                    project_id=project_id,
                    title=chapter_title,
                    original_text=chapter_content,
                    order=len(created_chapters)
                )
                db.add(chapter)
                created_chapters.append(chapter)
        
        db.commit()
        
        return {
            "project_id": project_id,
            "chapters_created": len(created_chapters),
            "total_chapters": len(created_chapters),
            "pattern_used": chapter_pattern,
            "chapters": [
                {
                    "title": ch.title,
                    "order": ch.order,
                    "content_length": len(ch.original_text)
                }
                for ch in created_chapters
            ]
        }
        
    except UnicodeDecodeError:
        raise HTTPException(
            status_code=400,
            detail="File encoding error. Please use UTF-8 encoding."
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Error processing file: {str(e)}"
        )
    finally:
        file.file.close()


@router.get("/{project_id}/chapters/{chapter_id}/download")
def download_chapter(
    project_id: int,
    chapter_id: int,
    db: Session = Depends(get_db)
):
    """Скачать переведенную главу в формате TXT."""
    from fastapi.responses import Response
    
    # Проверяем, что проект и глава существуют
    project = db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    chapter = db.get(Chapter, chapter_id)
    if not chapter or chapter.project_id != project_id:
        raise HTTPException(status_code=404, detail="Chapter not found")
    
    if not chapter.translated_text:
        raise HTTPException(status_code=404, detail="Chapter not translated yet")
    
    # Формируем содержимое файла
    content = f"""Перевод главы: {chapter.title}
Проект: {project.name}
Жанр: {project.genre}

{chapter.translated_text}

---
Оригинальный текст:
{chapter.original_text}
"""
    
    # Подготавливаем безопасные заголовки для скачивания (RFC 5987)
    # Основной filename должен быть ASCII-совместимым, а полный UTF-8 — через filename*
    try:
        from urllib.parse import quote
    except Exception:
        quote = None

    safe_filename = f"chapter_{chapter_id}.txt"
    full_filename = f"chapter_{chapter_id}_{project.name}_{chapter.title}.txt"
    if quote is not None:
        encoded_full = "UTF-8''" + quote(full_filename, safe='')
    else:
        # Fallback: заменяем не-ASCII символы на '_'
        encoded_full = "UTF-8''" + ''.join(ch if ord(ch) < 128 else '_' for ch in full_filename)

    content_disposition = f"attachment; filename=\"{safe_filename}\"; filename*={encoded_full}"

    return Response(
        content=content,
        media_type="text/plain; charset=utf-8",
        headers={
            "Content-Disposition": content_disposition
        }
    )


@router.get("/chapters/{chapter_id}", response_model=ChapterRead)
def get_chapter(chapter_id: int, db: Session = Depends(get_db)) -> Chapter:
    """Получить главу по ID."""
    chapter = db.get(Chapter, chapter_id)
    if not chapter:
        raise HTTPException(status_code=404, detail="Chapter not found")
    return chapter


@router.delete("/chapters/{chapter_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_chapter(chapter_id: int, db: Session = Depends(get_db)):
    """Удалить главу."""
    chapter = db.get(Chapter, chapter_id)
    if not chapter:
        raise HTTPException(status_code=404, detail="Chapter not found")
    
    db.delete(chapter)
    db.commit()


@router.put("/chapters/{chapter_id}", response_model=ChapterRead)
def update_chapter(chapter_id: int, payload: ChapterUpdate, db: Session = Depends(get_db)) -> Chapter:
    """Обновить поля главы (название, тексты)."""
    chapter = db.get(Chapter, chapter_id)
    if not chapter:
        raise HTTPException(status_code=404, detail="Chapter not found")

    updates = payload.dict(exclude_unset=True)
    for field, value in updates.items():
        setattr(chapter, field, value)

    db.commit()
    db.refresh(chapter)
    return chapter


# API для создания общего саммари проекта
@router.post("/{project_id}/generate-summary")
def generate_project_summary(project_id: int, db: Session = Depends(get_db)) -> dict:
    """Создать общее саммари проекта на основе всех глав."""
    # Проверяем, что проект существует
    project = db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Получаем все главы проекта с саммари
    chapters = db.query(Chapter).filter(
        Chapter.project_id == project_id,
        Chapter.summary.isnot(None)
    ).order_by(Chapter.id).all()
    
    if not chapters:
        raise HTTPException(
            status_code=400, 
            detail="No chapters with summaries found. Please analyze chapters first."
        )
    
    try:
        # Подготавливаем данные для создания саммари
        chapters_data = [
            {
                "title": chapter.title,
                "summary": chapter.summary,
                "original_text": chapter.original_text
            }
            for chapter in chapters
        ]
        
        # Создаем общее саммари
        project_summary = context_summarizer.create_project_summary(chapters_data)
        
        return {
            "project_id": project_id,
            "summary": project_summary,
            "chapters_used": len(chapters),
            "message": "Project summary generated successfully"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate project summary: {str(e)}"
        )
