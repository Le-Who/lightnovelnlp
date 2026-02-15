from typing import List, Set, Dict, Any
import re
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models.glossary import GlossaryTerm, TermStatus
from app.services.cache_service import cache_service

class GlossaryService:
    @staticmethod
    def get_relevant_terms(db: Session, project_id: int, text: str) -> List[GlossaryTerm]:
        """
        Efficiently retrieves only the terms relevant to the given text for a specific project.
        Uses caching to avoid DB hits.

        This method optimizes performance by:
        1. Checking cache for project glossary.
        2. If miss, fetching all approved terms and caching them.
        3. Filtering terms in Python using simple substring matching.
        """
        if not text:
            return []

        # 1. Try to get terms from cache
        cached_terms = cache_service.get_cached_glossary(project_id)

        term_dicts = []
        if cached_terms is not None:
            term_dicts = cached_terms
        else:
            # 2. Cache miss: Fetch from DB
            # Fetch all approved terms
            terms = db.query(GlossaryTerm).filter(
                GlossaryTerm.project_id == project_id,
                GlossaryTerm.status == TermStatus.APPROVED
            ).all()

            # Convert to dicts for caching
            for term in terms:
                # Handle Enum values if present, otherwise use string
                category_val = getattr(term.category, "value", term.category)
                status_val = getattr(term.status, "value", term.status)

                term_dicts.append({
                    "id": term.id,
                    "project_id": term.project_id,
                    "source_term": term.source_term,
                    "translated_term": term.translated_term,
                    "category": category_val,
                    "status": status_val,
                    "context": term.context,
                    "frequency": term.frequency,
                })

            # Cache the result (TTL 1 hour)
            cache_service.cache_glossary(project_id, term_dicts)

        # 3. Filter in Python
        text_lower = text.lower()
        relevant_terms = []

        for term_data in term_dicts:
            source_term = term_data.get("source_term")
            if source_term and source_term.lower() in text_lower:
                # Reconstruct GlossaryTerm object (detached)
                term_obj = GlossaryTerm(**term_data)
                relevant_terms.append(term_obj)

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
