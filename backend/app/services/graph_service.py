"""
graph_service.py — Temporal Knowledge Graph Service

Provides:
  - Entity timeline queries (as-of-chapter relationship history)
  - Relationship invalidation (mark superseded)
  - Contradiction detection (conflicting relationship types for same pair)
  - Narrative thread auto-detection from TermOccurrence co-occurrence

This is a MemPalace-inspired adaptation: instead of a separate SQLite KG
we augment the existing term_relationships table with temporal columns.
"""

from __future__ import annotations

import logging
from typing import Any

from sqlalchemy.orm import Session

from app.models.glossary import (
    GlossaryTerm,
    NarrativeThread,
    TermOccurrence,
    TermRelationship,
    ThreadAnchor,
)
from app.models.project import Chapter

logger = logging.getLogger(__name__)

# Relationship types that are mutually exclusive for the same (subject, object) pair
# If both sides have a concurrent "active" relationship, that's a contradiction.
EXCLUSIVE_RELATION_GROUPS: dict[str, set[str]] = {
    "allegiance": {"friend/ally", "enemy/rival"},
    "power": {"master_student", "superior_subordinate"},
    "romance": {"lovers"},
}


class GraphService:
    """Service for temporal knowledge graph operations."""

    # ── Timeline Queries ─────────────────────────────────────────────────────

    def get_entity_timeline(
        self,
        db: Session,
        project_id: int,
        term_id: int,
        as_of_chapter: int | None = None,
    ) -> list[dict[str, Any]]:
        """
        Return the chronological relationship history for a term.

        When ``as_of_chapter`` is provided only relationships valid at that
        chapter order are returned (i.e. ones where valid_from ≤ as_of and
        valid_to IS NULL or valid_to ≥ as_of).
        """
        q = (
            db.query(TermRelationship)
            .filter(
                TermRelationship.project_id == project_id,
                (TermRelationship.source_term_id == term_id)
                | (TermRelationship.target_term_id == term_id),
            )
        )

        if as_of_chapter is not None:
            q = q.filter(
                (TermRelationship.valid_from_chapter.is_(None))
                | (TermRelationship.valid_from_chapter <= as_of_chapter),
                (TermRelationship.valid_to_chapter.is_(None))
                | (TermRelationship.valid_to_chapter >= as_of_chapter),
            )

        relationships = q.order_by(TermRelationship.valid_from_chapter).all()

        return [
            {
                "id": r.id,
                "source_term_id": r.source_term_id,
                "target_term_id": r.target_term_id,
                "relation_type": r.relation_type,
                "confidence": r.confidence,
                "context": r.context,
                "valid_from_chapter": r.valid_from_chapter,
                "valid_to_chapter": r.valid_to_chapter,
                "source_chapter_id": r.source_chapter_id,
                "superseded_by_id": r.superseded_by_id,
            }
            for r in relationships
        ]

    def get_active_relationships(
        self,
        db: Session,
        project_id: int,
        term_ids: list[int],
        as_of_chapter: int | None = None,
    ) -> list[dict[str, Any]]:
        """
        Retrieve currently-active relationships between a set of terms.

        Used by translation_service to inject only temporally-valid context.
        """
        if len(term_ids) < 2:
            return []

        q = (
            db.query(TermRelationship)
            .filter(
                TermRelationship.source_term_id.in_(term_ids),
                TermRelationship.target_term_id.in_(term_ids),
            )
        )

        if as_of_chapter is not None:
            q = q.filter(
                (TermRelationship.valid_from_chapter.is_(None))
                | (TermRelationship.valid_from_chapter <= as_of_chapter),
                (TermRelationship.valid_to_chapter.is_(None))
                | (TermRelationship.valid_to_chapter >= as_of_chapter),
            )

        term_map: dict[int, str] = {
            t.id: t.source_term
            for t in db.query(GlossaryTerm.id, GlossaryTerm.source_term)
            .filter(GlossaryTerm.id.in_(term_ids))
            .all()
        }

        return [
            {
                "source": term_map.get(int(r.source_term_id), "Unknown"),  # type: ignore
                "target": term_map.get(int(r.target_term_id), "Unknown"),  # type: ignore
                "type": r.relation_type,
                "description": r.context or "",
                "valid_from_chapter": r.valid_from_chapter,
                "valid_to_chapter": r.valid_to_chapter,
            }
            for r in q.all()
        ]

    # ── Modification Operations ──────────────────────────────────────────────

    def invalidate_relationship(
        self,
        db: Session,
        relationship_id: int,
        ended_at_chapter: int,
        superseded_by_id: int | None = None,
    ) -> dict[str, Any]:
        """
        Mark a relationship as no longer valid from a given chapter.
        Optionally link the relationship that superseded this one.
        """
        rel = db.get(TermRelationship, relationship_id)
        if not rel:
            return {"error": f"Relationship {relationship_id} not found"}

        rel.valid_to_chapter = ended_at_chapter  # type: ignore
        if superseded_by_id:
            rel.superseded_by_id = superseded_by_id  # type: ignore

        db.commit()
        logger.info(
            f"[GRAPH] Invalidated relationship {relationship_id} at chapter {ended_at_chapter}"
        )
        return {"success": True, "invalidated_id": relationship_id, "ended_at_chapter": ended_at_chapter}

    # ── Contradiction Detection ──────────────────────────────────────────────

    def detect_contradictions(
        self, db: Session, project_id: int
    ) -> list[dict[str, Any]]:
        """
        Find temporal and semantic contradictions in the knowledge graph.

        Two types:
        1. TEMPORAL: a relationship is superseded but valid_to is not set
           (i.e., a newer relationship exists but the old one is still "active").
        2. EXCLUSIVE: two concurrently-active relationships belong to an exclusive
           group (e.g., friend/ally AND enemy/rival for the same pair at the same time).
        """
        contradictions: list[dict[str, Any]] = []

        # All active relationships for the project
        active_rels = (
            db.query(TermRelationship)
            .filter(
                TermRelationship.project_id == project_id,
                TermRelationship.valid_to_chapter.is_(None),
            )
            .all()
        )

        # Index by (a, b) pair regardless of direction
        pair_rels: dict[tuple[int, int], list[TermRelationship]] = {}
        for r in active_rels:
            pair = (
                min(int(r.source_term_id), int(r.target_term_id)),  # type: ignore
                max(int(r.source_term_id), int(r.target_term_id)),  # type: ignore
            )
            pair_rels.setdefault(pair, []).append(r)

        # Check exclusive groups
        for pair, rels in pair_rels.items():
            types_present = {r.relation_type for r in rels}
            for group_name, exclusive_set in EXCLUSIVE_RELATION_GROUPS.items():
                found_exclusive = types_present & exclusive_set
                if len(found_exclusive) > 1:
                    contradictions.append({
                        "type": "EXCLUSIVE_CONFLICT",
                        "group": group_name,
                        "term_pair": list(pair),
                        "conflicting_types": list(found_exclusive),
                        "relationship_ids": [r.id for r in rels if r.relation_type in found_exclusive],
                        "severity": "high",
                        "description": (
                            f"Terms {pair[0]} and {pair[1]} are simultaneously "
                            f"{' and '.join(str(f) for f in found_exclusive)}"
                        ),
                    })

            # Check for superseded but still active (temporal contradiction)
            superseded_active = [r for r in rels if r.superseded_by_id is not None]
            for r in superseded_active:
                contradictions.append({
                    "type": "SUPERSEDED_STILL_ACTIVE",
                    "relationship_id": r.id,
                    "superseded_by_id": r.superseded_by_id,
                    "term_pair": list(pair),
                    "severity": "medium",
                    "description": (
                        f"Relationship {r.id} ({r.relation_type}) was superseded "
                        f"by {r.superseded_by_id} but valid_to_chapter is not set."
                    ),
                })

        logger.info(f"[GRAPH] Found {len(contradictions)} contradiction(s) for project {project_id}")
        return contradictions

    # ── Narrative Thread Detection ───────────────────────────────────────────

    def detect_narrative_threads(
        self,
        db: Session,
        project_id: int,
        min_chapters: int = 3,
        min_co_occurrence: int = 2,
    ) -> list[dict[str, Any]]:
        """
        Auto-detect narrative threads from TermOccurrence co-occurrence patterns.

        Algorithm:
        1. Load all TermOccurrences for the project (with chapter order).
        2. For each chapter, collect the set of terms appearing in it.
        3. For each pair of terms, count how many chapters they co-occur in.
        4. Pairs with >= min_co_occurrence chapters create candidate threads.
        5. Cluster overlapping pairs into threads.
        """
        occurrences = (
            db.query(TermOccurrence, Chapter.order, GlossaryTerm.source_term)
            .join(Chapter, TermOccurrence.chapter_id == Chapter.id)
            .join(GlossaryTerm, TermOccurrence.term_id == GlossaryTerm.id)
            .filter(TermOccurrence.project_id == project_id)
            .order_by(Chapter.order)
            .all()
        )

        if not occurrences:
            return []

        # Build chapter → terms mapping
        chapter_terms: dict[int, set[int]] = {}
        term_names: dict[int, str] = {}
        chapter_order_map: dict[int, int] = {}

        for occ, ch_order, term_name in occurrences:
            chapter_terms.setdefault(ch_order, set()).add(occ.term_id)
            term_names[occ.term_id] = term_name
            chapter_order_map[occ.chapter_id] = ch_order

        # Count pair co-occurrences
        pair_chapters: dict[tuple[int, int], list[int]] = {}
        for ch_order, terms in chapter_terms.items():
            term_list = sorted(terms)
            for i, t1 in enumerate(term_list):
                for t2 in term_list[i + 1:]:
                    pair = (t1, t2)
                    pair_chapters.setdefault(pair, []).append(ch_order)

        # Filter to significant pairs
        significant_pairs = [
            (pair, chapters)
            for pair, chapters in pair_chapters.items()
            if len(chapters) >= min_chapters and len(chapters) >= min_co_occurrence
        ]

        # Build thread suggestions
        threads = []
        for (t1_id, t2_id), chapters in significant_pairs:
            t1_name = term_names.get(t1_id, f"term_{t1_id}")
            t2_name = term_names.get(t2_id, f"term_{t2_id}")
            threads.append({
                "thread_name": f"{t1_name} & {t2_name} Arc",
                "thread_type": "character_arc",
                "term_ids": [t1_id, t2_id],
                "term_names": [t1_name, t2_name],
                "chapter_orders": sorted(chapters),
                "co_occurrence_count": len(chapters),
                "is_auto_detected": True,
            })

        # Sort by co-occurrence frequency (most prominent first)
        threads.sort(key=lambda x: int(x["co_occurrence_count"]), reverse=True)
        return threads[:20]  # Return top 20 candidates

    def create_thread(
        self,
        db: Session,
        project_id: int,
        thread_name: str,
        thread_type: str = "plot",
        is_auto_detected: bool = False,
    ) -> NarrativeThread:
        """Create and persist a new NarrativeThread."""
        thread = NarrativeThread(
            project_id=project_id,
            thread_name=thread_name,
            thread_type=thread_type,
            is_auto_detected=1 if is_auto_detected else 0,
        )
        db.add(thread)
        db.commit()
        db.refresh(thread)
        return thread

    def add_thread_anchor(
        self,
        db: Session,
        thread_id: int,
        chapter_id: int,
        term_id: int | None = None,
        anchor_text: str | None = None,
        anchor_type: str = "mention",
    ) -> ThreadAnchor:
        """Attach a chapter to a thread as an anchor point."""
        anchor = ThreadAnchor(
            thread_id=thread_id,
            chapter_id=chapter_id,
            term_id=term_id,
            anchor_text=anchor_text,
            anchor_type=anchor_type,
        )
        db.add(anchor)
        db.commit()
        db.refresh(anchor)
        return anchor

    # ── Analytics ────────────────────────────────────────────────────────────

    def get_term_frequency_timeline(
        self,
        db: Session,
        project_id: int,
        term_ids: list[int] | None = None,
        top_n: int = 20,
    ) -> list[dict[str, Any]]:
        """
        Return per-chapter frequency data for terms, suitable for sparklines.

        Returns: [
          {
            "term_id": int,
            "term_name": str,
            "data": [{"chapter_order": int, "frequency": int}, ...]
          }
        ]
        """
        q = (
            db.query(
                TermOccurrence.term_id,
                GlossaryTerm.source_term,
                GlossaryTerm.translated_term,
                Chapter.order.label("chapter_order"),
                TermOccurrence.frequency,
            )
            .join(GlossaryTerm, TermOccurrence.term_id == GlossaryTerm.id)
            .join(Chapter, TermOccurrence.chapter_id == Chapter.id)
            .filter(TermOccurrence.project_id == project_id)
        )

        if term_ids:
            q = q.filter(TermOccurrence.term_id.in_(term_ids))

        rows = q.order_by(TermOccurrence.term_id, Chapter.order).all()

        # Group by term
        term_data: dict[int, dict[str, Any]] = {}
        for row in rows:
            tid = row.term_id
            if tid not in term_data:
                term_data[tid] = {
                    "term_id": tid,
                    "term_name": row.source_term,
                    "translated_term": row.translated_term,
                    "data": [],
                    "total_frequency": 0,
                }
            term_data[tid]["data"].append({
                "chapter_order": row.chapter_order,
                "frequency": row.frequency,
            })
            term_data[tid]["total_frequency"] += row.frequency

        result = list(term_data.values())

        # If no filter, return top_n by total frequency
        if not term_ids:
            result.sort(key=lambda x: x["total_frequency"], reverse=True)
            result = result[:top_n]

        return result


graph_service = GraphService()
