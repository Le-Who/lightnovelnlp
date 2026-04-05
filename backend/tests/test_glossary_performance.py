import time

import pytest
from sqlalchemy import event

from app.api.glossary import get_glossary_terms
from app.models.glossary import GlossaryTerm, TermOccurrence, TermRelationship
from app.models.project import Chapter, Project


@pytest.fixture
def query_counter(db):
    class QueryCounter:
        def __init__(self):
            self.count = 0

        def __call__(self, conn, cursor, statement, parameters, context, executemany):
            self.count += 1

    counter = QueryCounter()
    event.listen(db.bind, "before_cursor_execute", counter)
    yield counter
    event.remove(db.bind, "before_cursor_execute", counter)


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
        order=1,
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
        last_chapter_id=chapter.id,
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
        order="asc",
    )

    assert len(terms) == 1
    loaded_term = terms[0]

    # 6. Verify first_chapter is loaded but text is deferred
    first_chapter = loaded_term.first_chapter
    assert first_chapter is not None
    assert first_chapter.id == chapter.id

    # Check that 'order' is loaded
    assert "order" in first_chapter.__dict__

    # Check that 'original_text' is NOT loaded
    assert "original_text" not in first_chapter.__dict__, (
        "original_text should be deferred"
    )

    # 7. Accessing original_text should load it
    text = first_chapter.original_text
    assert text == "Very long text " * 100
    assert "original_text" in first_chapter.__dict__, (
        "original_text should be loaded after access"
    )


def test_glossary_terms_query_count(db, query_counter):
    # Setup
    project = Project(name="Perf Test")
    db.add(project)
    db.commit()
    db.refresh(project)

    chapter = Chapter(project_id=project.id, title="Ch1", original_text="...", order=1)
    db.add(chapter)
    db.commit()
    db.refresh(chapter)

    terms = []
    for i in range(50):
        term = GlossaryTerm(
            project_id=project.id,
            source_term=f"Term {i}",
            translated_term=f"Trans {i}",
            category="other",
            frequency=10,
            first_chapter_id=chapter.id,
            last_chapter_id=chapter.id,
        )
        db.add(term)
        terms.append(term)
    db.commit()

    # Add relationships
    # Create relationships for the first 10 terms to ensure they have counts
    for i in range(10):
        term = terms[i]
        # 5 outgoing relationships
        for j in range(5):
            rel = TermRelationship(
                project_id=project.id,
                source_term_id=term.id,
                target_term_id=terms[(i + j + 1) % 50].id,
                relation_type="related",
            )
            db.add(rel)

        # Add occurrence
        occ = TermOccurrence(
            project_id=project.id, term_id=term.id, chapter_id=chapter.id, frequency=5
        )
        db.add(occ)

    db.commit()

    # Clear session to ensure clean fetch from DB
    db.expire_all()

    # Reset counter
    query_counter.count = 0

    # Measure
    start_time = time.time()
    results = get_glossary_terms(
        project_id=project.id,
        db=db,
        limit=50,
        offset=0,
        search=None,
        sort_by="id",
        order="asc",
    )
    end_time = time.time()

    _elapsed = end_time - start_time  # measured but not asserted (benchmark only)

    # Validate result correctness
    assert len(results) == 50

    # Check centrality score for the first term
    term_0 = next(t for t in results if t.source_term == "Term 0")
    assert term_0.centrality_score >= 5

    # Verify fields populated
    assert term_0.occurrences_data is not None
    assert term_0.first_chapter_order == 1

    # Baseline was 7 queries. Optimized to 5.
    assert query_counter.count <= 5
