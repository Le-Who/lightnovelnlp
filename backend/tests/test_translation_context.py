from app.services.translation_service import TranslationService
from app.models.glossary import GlossaryTerm, TermRelationship, TermStatus
from app.models.project import Project, ProjectGenre

def test_get_relevant_relationships(db):
    # Setup Data
    project = Project(name="Test Project", genre=ProjectGenre.FANTASY)
    db.add(project)
    db.commit()

    alice = GlossaryTerm(project_id=project.id, source_term="Alice", translated_term="Алиса", category="character", status=TermStatus.APPROVED)
    bob = GlossaryTerm(project_id=project.id, source_term="Bob", translated_term="Боб", category="character", status=TermStatus.APPROVED)
    charlie = GlossaryTerm(project_id=project.id, source_term="Charlie", translated_term="Чарли", category="character", status=TermStatus.APPROVED)
    db.add_all([alice, bob, charlie])
    db.commit()

    rel = TermRelationship(
        project_id=project.id,
        source_term_id=alice.id,
        target_term_id=bob.id,
        relation_type="friends",
        context="Childhood friends"
    )
    db.add(rel)
    db.commit()

    # Test 1: Both present -> Should return relationship
    rels = TranslationService._get_relevant_relationships(db, [alice, bob])
    assert len(rels) == 1
    assert rels[0]["source"] == "Alice"
    assert rels[0]["target"] == "Bob"
    assert "friends" in rels[0]["type"]

    # Test 2: Only one present -> Should return empty (need both for context)
    rels_single = TranslationService._get_relevant_relationships(db, [alice])
    assert len(rels_single) == 0

    # Test 3: Two present but no relationship -> Empty
    rels_none = TranslationService._get_relevant_relationships(db, [alice, charlie])
    assert len(rels_none) == 0

    # Test 4: Relationship exists but one term missing from input -> Empty
    rels_missing = TranslationService._get_relevant_relationships(db, [alice, charlie]) # Bob missing
    assert len(rels_missing) == 0
