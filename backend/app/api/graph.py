from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Any, Dict, List

from app.deps import get_db
from app.services.graph_service import graph_service

router = APIRouter()


@router.get("/{project_id}/graph/timeline", response_model=List[Dict[str, Any]])
def get_entity_timeline(
    project_id: int,
    term_id: int,
    as_of_chapter: int = Query(None, description="Filter relations active at this chapter"),
    db: Session = Depends(get_db),
):
    """Get the chronological relationship history for a specific term."""
    # We could verify project/term existence here
    return graph_service.get_entity_timeline(db, project_id, term_id, as_of_chapter)


@router.get("/{project_id}/graph/contradictions", response_model=List[Dict[str, Any]])
def get_contradictions(
    project_id: int,
    db: Session = Depends(get_db),
):
    """Detect temporal and semantic contradictions in the knowledge graph."""
    return graph_service.detect_contradictions(db, project_id)


@router.post("/{project_id}/graph/relationships/{relationship_id}/invalidate")
def invalidate_relationship(
    project_id: int,
    relationship_id: int,
    ended_at_chapter: int,
    superseded_by_id: int = Query(None),
    db: Session = Depends(get_db),
):
    """Mark a relationship as no longer valid from a given chapter."""
    res = graph_service.invalidate_relationship(
        db, relationship_id, ended_at_chapter, superseded_by_id
    )
    if "error" in res:
        raise HTTPException(status_code=404, detail=res["error"])
    return res


@router.get("/{project_id}/analytics/term-frequency", response_model=List[Dict[str, Any]])
def get_term_frequency(
    project_id: int,
    term_ids: List[int] = Query(None),
    top_n: int = Query(20),
    db: Session = Depends(get_db),
):
    """Get per-chapter frequency data for terms, suitable for sparklines."""
    return graph_service.get_term_frequency_timeline(db, project_id, term_ids, top_n)


@router.get("/{project_id}/analytics/threads", response_model=List[Dict[str, Any]])
def get_threads(
    project_id: int,
    min_chapters: int = Query(3),
    min_co_occurrence: int = Query(2),
    db: Session = Depends(get_db),
):
    """Auto-detect narrative threads from term co-occurrence patterns."""
    return graph_service.detect_narrative_threads(
        db, project_id, min_chapters, min_co_occurrence
    )
