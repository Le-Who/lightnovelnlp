from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import List, Optional
from fastapi import HTTPException

from app.models.project import Project, Chapter
from app.models.glossary import (
    GlossaryTerm, TermRelationship, GlossaryVersion, 
    BatchJob, BatchJobItem
)
from app.schemas.project import ProjectCreate, ProjectGenre

class ProjectService:
    @staticmethod
    def get_projects(db: Session) -> List[Project]:
        return db.query(Project).order_by(Project.created_at.desc()).all()

    @staticmethod
    def create_project(db: Session, payload: ProjectCreate) -> Project:
        exists = db.query(Project).filter(Project.name == payload.name).first()
        if exists:
            raise HTTPException(status_code=400, detail="Project with this name already exists")
        
        genre_value = getattr(payload.genre, "value", payload.genre)
        genre_value = getattr(payload.genre, "value", payload.genre)
        project = Project(
            name=payload.name, 
            genre=genre_value,
            custom_genre_instructions=payload.custom_genre_instructions
        )
        db.add(project)
        db.commit()
        db.refresh(project)
        return project

    @staticmethod
    def get_project(db: Session, project_id: int) -> Optional[Project]:
        return db.get(Project, project_id)

    @staticmethod
    def delete_project(db: Session, project_id: int) -> None:
        project = db.get(Project, project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        # Delete dependencies
        db.query(TermRelationship).filter(TermRelationship.project_id == project_id).delete(synchronize_session=False)
        db.query(GlossaryTerm).filter(GlossaryTerm.project_id == project_id).delete(synchronize_session=False)
        db.query(GlossaryVersion).filter(GlossaryVersion.project_id == project_id).delete(synchronize_session=False)
        db.query(BatchJobItem).filter(BatchJobItem.project_id == project_id).delete(synchronize_session=False)
        db.query(BatchJob).filter(BatchJob.project_id == project_id).delete(synchronize_session=False)
        db.query(Chapter).filter(Chapter.project_id == project_id).delete(synchronize_session=False)
        
        db.delete(project)
        db.commit()
