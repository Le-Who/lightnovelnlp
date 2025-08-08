from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.deps import get_db
from app.models.project import Project, Chapter
from app.schemas.project import ProjectCreate, ProjectRead, ChapterCreate, ChapterRead
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
    db.delete(project)
    db.commit()


# Главы
@router.get("/{project_id}/chapters", response_model=List[ChapterRead])
def list_chapters(project_id: int, db: Session = Depends(get_db)) -> List[Chapter]:
    """Получить все главы проекта."""
    chapters = db.query(Chapter).filter(Chapter.project_id == project_id).all()
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
