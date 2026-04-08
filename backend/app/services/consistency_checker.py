"""
Consistency Checker

Audits the glossary for potential duplicates and contradictions using
semantic similarity (via pgvector) and lexical prefix overlap.
"""

from typing import Any, Dict, List

from sqlalchemy.orm import Session

from app.models.glossary import GlossaryTerm
from app.services.embedding_service import embedding_service


class ConsistencyChecker:
    """Detects duplicates and semantic collisions in the glossary."""

    def audit_project(
        self, db: Session, project_id: int, similarity_threshold: float = 0.85
    ) -> List[Dict[str, Any]]:
        """
        Scan all terms in a project to find potential duplicates.
        Returns a list of cluster proposals.
        """
        terms = (
            db.query(GlossaryTerm)
            .filter(
                GlossaryTerm.project_id == project_id,
                GlossaryTerm.embedding_vec.isnot(None),
            )
            .all()
        )

        clusters = []
        processed_ids = set()

        for term in terms:
            if term.id in processed_ids:
                continue

            # Assuming term.embedding_vec is stored as a list inside the ORM, depending on pgvector mapping.
            # If it's stored as a string or needs casting, handle accordingly.
            vec = term.embedding_vec
            if isinstance(vec, str):
                import json
                try:
                    vec = json.loads(vec)
                except Exception:
                    continue

            if not vec:
                continue

            similar = embedding_service.find_similar_terms(
                db_session=db,
                query_embedding=vec,
                project_id=project_id,
                limit=5,
                threshold=similarity_threshold,
            )

            # Filter out self and already processed
            similar_filtered = [
                s for s in similar if s["term_id"] != term.id and s["term_id"] not in processed_ids
            ]

            if similar_filtered:
                cluster = {
                    "base_term": {
                        "id": term.id,
                        "source_term": term.source_term,
                        "translated_term": term.translated_term,
                    },
                    "potential_duplicates": similar_filtered,
                    "confidence": max([s["similarity"] for s in similar_filtered]),
                    "match_type": "semantic",
                }
                clusters.append(cluster)
                
                processed_ids.add(term.id)
                for s in similar_filtered:
                    processed_ids.add(s["term_id"])

        # Sort by confidence descending
        clusters.sort(key=lambda x: x["confidence"], reverse=True)
        return clusters

    def check_new_term(
        self, db: Session, project_id: int, source_term: str, term_embedding: list[float] | None = None
    ) -> List[Dict[str, Any]]:
        """
        Check if a newly extracted term collides with existing glossary.
        Used at extraction time to group duplicates automatically before LLM approval.
        """
        duplicates = []
        
        # 1. Exact or lower-case match
        exact_match = (
            db.query(GlossaryTerm)
            .filter(GlossaryTerm.project_id == project_id)
            .filter(GlossaryTerm.source_term.ilike(source_term))
            .first()
        )
        if exact_match:
            duplicates.append({
                "term_id": exact_match.id,
                "source_term": exact_match.source_term,
                "similarity": 1.0,
                "match_type": "exact",
            })
            return duplicates  # No need to check semantic if exact match exists

        # 2. Semantic matching via pgvector
        if term_embedding:
            # We use a slightly lower threshold for new term detection to be safe
            semantic_matches = embedding_service.find_similar_terms(
                db_session=db,
                query_embedding=term_embedding,
                project_id=project_id,
                limit=3,
                threshold=0.85,
            )
            for sm in semantic_matches:
                sm["match_type"] = "semantic"
                duplicates.append(sm)

        # 3. Lexical prefix checking (e.g. "Azure Sect" vs "Azure Cloud Sect")
        # Find terms where one is a proper substring of another
        # (This is simplified; a robust version would use word boundary regex or pg_trgm)
        # Using SQLAlchemy ilike on the DB side
        # Be careful of very short terms
        if len(source_term) > 3:
            lexical_matches = (
                db.query(GlossaryTerm)
                .filter(GlossaryTerm.project_id == project_id)
                .filter(
                    (GlossaryTerm.source_term.ilike(f"%{source_term}%")) |
                    (source_term.lower().find(GlossaryTerm.source_term) != -1) # Not easily translatable to pure SQL without bind params for the string
                )
                .limit(5)
                .all()
            )
            
            # Since SQL ilike "%source_term%" handles one direction, we handle the other natively:
            # "source_term" contains existing term
            reverse_matches = (
                db.query(GlossaryTerm)
                .filter(GlossaryTerm.project_id == project_id)
                .all()
            )
            
            for lt in lexical_matches:
                if lt.source_term.lower() != source_term.lower() and not any(d["term_id"] == lt.id for d in duplicates):
                    duplicates.append({
                        "term_id": lt.id,
                        "source_term": lt.source_term,
                        "similarity": 0.8,
                        "match_type": "substring",
                    })
                    
            for rt in reverse_matches:
                if len(rt.source_term) > 3 and rt.source_term.lower() in source_term.lower():
                    if not any(d["term_id"] == rt.id for d in duplicates):
                        duplicates.append({
                            "term_id": rt.id,
                            "source_term": rt.source_term,
                            "similarity": 0.8,
                            "match_type": "superstring",
                        })

        # Sort duplicates by similarity
        duplicates.sort(key=lambda x: x["similarity"], reverse=True)
        return duplicates

    def merge_terms(self, db: Session, source_term_id: int, target_term_id: int) -> Dict[str, Any]:
        """
        Merge source_term_id INTO target_term_id.
        All occurrences and relationships referencing source are mapped to target.
        Source term is then deleted.
        """
        from app.models.glossary import TermOccurrence, TermRelationship
        
        source = db.get(GlossaryTerm, source_term_id)
        target = db.get(GlossaryTerm, target_term_id)
        
        if not source or not target:
            return {"error": "Term(s) not found"}
            
        if source.project_id != target.project_id:
            return {"error": "Terms belong to different projects"}

        # 1. Merge Occurrences
        source_occs = db.query(TermOccurrence).filter(TermOccurrence.term_id == source_term_id).all()
        for s_occ in source_occs:
            # Check if target already has an occurrence for this chapter
            t_occ = db.query(TermOccurrence).filter(
                TermOccurrence.term_id == target_term_id,
                TermOccurrence.chapter_id == s_occ.chapter_id
            ).first()
            if t_occ:
                t_occ.frequency += s_occ.frequency
                db.delete(s_occ)
            else:
                s_occ.term_id = target_term_id

        # 2. Merge Relationships (update source or target ends)
        # relationships where source_term is the subject
        subj_rels = db.query(TermRelationship).filter(TermRelationship.source_term_id == source_term_id).all()
        for rel in subj_rels:
            rel.source_term_id = target_term_id
            
        # relationships where source_term is the object
        obj_rels = db.query(TermRelationship).filter(TermRelationship.target_term_id == source_term_id).all()
        for rel in obj_rels:
            rel.target_term_id = target_term_id
            
        # 3. Update Term frequency
        target.frequency += source.frequency
        
        # 4. Delete source
        db.delete(source)
        db.commit()
        
        return {
            "success": True, 
            "merged_term_id": source_term_id, 
            "into_term_id": target_term_id,
            "new_frequency": target.frequency
        }

consistency_checker = ConsistencyChecker()
