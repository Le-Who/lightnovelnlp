from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.deps import get_db
from app.models.project import Project, Chapter
from app.schemas.project import ProjectCreate, ProjectRead, ChapterCreate, ChapterRead, ChapterUpdate
from fastapi import File, UploadFile, Form
import io
try:
    import PyPDF2
except Exception:
    PyPDF2 = None

from app.core.nlp_pipeline.context_summarizer import context_summarizer

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
def list_chapters(project_id: int, db: Session = Depends(get_db)) -> List[Chapter]:
    """Получить все главы проекта, отсортированные по времени создания (возрастание ID)."""
    chapters = (
        db.query(Chapter)
        .filter(Chapter.project_id == project_id)
        .order_by(Chapter.id.asc())
        .all()
    )
    return chapters


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
    
    chapter = Chapter(
        project_id=project_id,
        title=payload.title,
        original_text=payload.original_text
    )
    
    db.add(chapter)
    db.commit()
    db.refresh(chapter)
    return chapter


@router.post("/{project_id}/chapters/upload", response_model=ChapterRead, status_code=status.HTTP_201_CREATED)
def create_chapter_from_file(
    project_id: int,
    title: str = Form(...),
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
        import re
        text = re.sub(r"\\[a-zA-Z]+[0-9]* ?|[{}]", "", raw)
    elif filename.endswith(".doc"):
        # .doc без внешних зависимостей корректно не парсится; попытаемся как текст
        text = content_bytes.decode(errors="ignore")
    else:
        raise HTTPException(status_code=400, detail="Unsupported file type. Use txt/pdf/rtf/doc")

    if not text.strip():
        raise HTTPException(status_code=400, detail="File has no extractable text")

    chapter = Chapter(
        project_id=project_id,
        title=title,
        original_text=text
    )
    db.add(chapter)
    db.commit()
    db.refresh(chapter)
    return chapter


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
