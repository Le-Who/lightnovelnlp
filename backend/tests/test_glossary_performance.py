
import pytest
from sqlalchemy.orm import attributes
from app.models.project import Project, Chapter
from app.models.glossary import GlossaryTerm
from app.api.glossary import get_glossary_terms

def test_glossary_terms_deferred_loading(db):
    """
    Verifies that get_glossary_terms uses load_only for chapter relationships,
    deferring heavy text fields.
    """
    # 1. Create Project
    project = Project(name="Perf Test Project")
    db.add(project)
    db.commit()
    db.refresh(project)

    # 2. Create Chapter with text
    chapter = Chapter(
        project_id=project.id,
        title="Chapter 1",
        original_text="Very long text " * 100,
        order=1
    )
    db.add(chapter)
    db.commit()
    db.refresh(chapter)

    # 3. Create GlossaryTerm
    term = GlossaryTerm(
        project_id=project.id,
        source_term="Test Term",
        translated_term="Test Trans",
        category="other",
        first_chapter_id=chapter.id,
        last_chapter_id=chapter.id
    )
    db.add(term)
    db.commit()

    # 4. Clear session to ensure we fetch from DB
    db.expire_all()

    # 5. Call API function with explicit arguments
    terms = get_glossary_terms(
        project_id=project.id,
        db=db,
        limit=50,
        offset=0,
        search=None,
        sort_by="id",
        order="asc"
    )

    assert len(terms) == 1
    loaded_term = terms[0]

    # 6. Verify first_chapter is loaded but text is deferred
    first_chapter = loaded_term.first_chapter
    assert first_chapter is not None
    assert first_chapter.id == chapter.id

    # Check that 'order' is loaded
    assert 'order' in first_chapter.__dict__

    # Check that 'original_text' is NOT loaded
    assert 'original_text' not in first_chapter.__dict__, "original_text should be deferred"

    # 7. Accessing original_text should load it
    text = first_chapter.original_text
    assert text == "Very long text " * 100
    assert 'original_text' in first_chapter.__dict__, "original_text should be loaded after access"
