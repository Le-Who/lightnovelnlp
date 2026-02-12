import pytest
from sqlalchemy import event
from app.models.project import Project
from app.models.glossary import GlossaryTerm, TermStatus
from app.services.glossary_service import GlossaryService

@pytest.fixture
def query_counter(db):
    class QueryCounter:
        def __init__(self):
            self.count = 0
            self.queries = []
        def __call__(self, conn, cursor, statement, parameters, context, executemany):
            self.count += 1
            self.queries.append(statement)

    counter = QueryCounter()
    event.listen(db.bind, "before_cursor_execute", counter)
    yield counter
    event.remove(db.bind, "before_cursor_execute", counter)

def test_get_relevant_terms_deferred_loading(db, query_counter):
    # Setup
    project = Project(name="Opt Test Project", source_language="en", target_language="ru")
    db.add(project)
    db.commit()
    db.refresh(project)

    term = GlossaryTerm(
        project_id=project.id,
        source_term="Optimization",
        translated_term="Оптимизация",
        category="other",
        status=TermStatus.APPROVED,
        context="Very long context " * 100
    )
    db.add(term)
    db.commit()

    # Clear session to ensure we fetch from DB
    db.expire_all()

    query_counter.count = 0
    query_counter.queries = []

    # Execute
    terms = GlossaryService.get_relevant_terms(db, project.id, "We need Optimization here.")

    assert len(terms) == 1
    loaded_term = terms[0]

    # Verify that context is deferred
    # With load_only, deferred attributes are not in __dict__ until accessed
    assert 'context' not in loaded_term.__dict__, "Context should be deferred"

    # Accessing it should trigger a load (and put it in __dict__)
    _ = loaded_term.context
    assert 'context' in loaded_term.__dict__
