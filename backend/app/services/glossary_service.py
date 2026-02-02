from typing import List, Set, Dict, Any
import re
from app.models.glossary import GlossaryTerm

class GlossaryService:
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
