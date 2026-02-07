from typing import List, Set, Dict, Any
import re
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models.glossary import GlossaryTerm, TermStatus

class GlossaryService:
    @staticmethod
    def get_relevant_terms(db: Session, project_id: int, text: str) -> List[GlossaryTerm]:
        """
        Efficiently retrieves only the terms relevant to the given text for a specific project.

        This method optimizes performance by:
        1. Fetching only ID and source_term for all approved terms using Core SQL (fast).
        2. Filtering terms in Python using simple substring matching (fast for <10k terms).
        3. Fetching full term objects only for the matches.

        This avoids instantiating full SQLAlchemy models for the majority of terms that are not present in the text.
        """
        if not text:
            return []

        # 1. Fetch lightweight data (ID, source_term)
        # We only care about APPROVED terms
        # OPTIMIZATION: Use SQLAlchemy Core execution to bypass ORM overhead.
        # This is faster than db.query(GlossaryTerm.id, GlossaryTerm.source_term)
        # as it avoids ORM object creation and processing.
        stmt = select(GlossaryTerm.id, GlossaryTerm.source_term).where(
            GlossaryTerm.project_id == project_id,
            GlossaryTerm.status == TermStatus.APPROVED
        )
        result = db.execute(stmt)

        # 2. Filter in Python
        text_lower = text.lower()
        matched_ids = []

        # Result yields tuples (id, source_term) directly from DB driver
        for row in result:
            term_id = row[0]
            source_term = row[1]
            if source_term and source_term.lower() in text_lower:
                matched_ids.append(term_id)

        if not matched_ids:
            return []

        # 3. Fetch full objects for matches
        # We return them unsorted here, caller can sort if needed.
        # But typically we want consistent order, e.g. by source_term length for replacement logic.
        relevant_terms = db.query(GlossaryTerm).filter(
            GlossaryTerm.id.in_(matched_ids)
        ).all()

        return relevant_terms

    @staticmethod
    def filter_terms_by_text(text: str, terms: List[GlossaryTerm]) -> List[GlossaryTerm]:
        """
        Filters glossary terms to return only those that appear in the text,
        plus any terms marked as 'always_on' (if we had such a flag, currently just checks presence).
        
        Uses regex for whole-word matching where appropriate to avoid false positives
        (e.g. matching "Cat" in "Caterpillar" if strict). 
        For now, we'll do case-insensitive substring matching for robustness, 
        sorted by length to prioritize longer phrases (though pure filtering doesn't strictly need sorting).
        """
        if not terms or not text:
            return []
            
        # Optimize: Pre-check simple presence to avoid regex overhead for everything
        # Converting text to lower once
        text_lower = text.lower()
        
        filtered_terms = []
        for term in terms:
            # Check source term presence
            # We assume source_term is the primary key to look for.
            # TODO: Add aliases support if Project model supports it.
            if term.source_term.lower() in text_lower:
                filtered_terms.append(term)
                
        return filtered_terms

    @staticmethod
    def sort_terms_by_priority(terms: List[GlossaryTerm]) -> List[GlossaryTerm]:
        """
        Sort terms by length (longest first) to ensure longer phrases are translated first
        if used in sequential replacement (though for LLM context, length merely helps prominence).
        """
        return sorted(terms, key=lambda t: len(t.source_term), reverse=True)
