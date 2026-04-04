from sqlalchemy.orm import Session
from app.services.glossary_service import GlossaryService
from app.models.glossary import GlossaryTerm, TermStatus
from app.models.project import Project


class MockTerm:
    def __init__(self, source_term, category="other"):
        self.source_term = source_term
        self.category = category


def test_filter_terms_exact_match():
    terms = [MockTerm("Eren"), MockTerm("Mikasa"), MockTerm("Levi")]
    text = "Eren and Mikasa went to the wall."

    filtered = GlossaryService.filter_terms_by_text(text, terms)

    assert len(filtered) == 2
    assert any(t.source_term == "Eren" for t in filtered)
    assert any(t.source_term == "Mikasa" for t in filtered)
    assert not any(t.source_term == "Levi" for t in filtered)


def test_filter_terms_case_insensitive():
    terms = [MockTerm("titan")]
    text = "Attack on Titan"

    filtered = GlossaryService.filter_terms_by_text(text, terms)

    assert len(filtered) == 1
    assert filtered[0].source_term == "titan"


def test_filter_terms_substring_safety():
    # Ensuring we match substrings (common for JP/CN names or compound words)
    terms = [MockTerm("Fire")]
    text = "Fireball"

    filtered = GlossaryService.filter_terms_by_text(text, terms)

    assert len(filtered) == 1
    assert filtered[0].source_term == "Fire"


def test_empty_input():
    assert GlossaryService.filter_terms_by_text("", [MockTerm("A")]) == []
    assert GlossaryService.filter_terms_by_text("Text", []) == []


def test_get_relevant_terms(db: Session):
    # Setup
    project = Project(name="Test Project", source_language="en", target_language="ru")
    db.add(project)
    db.commit()
    db.refresh(project)

    t1 = GlossaryTerm(
        project_id=project.id,
        source_term="Apple",
        translated_term="Яблоко",
        category="other",
        status=TermStatus.APPROVED,
    )
    t2 = GlossaryTerm(
        project_id=project.id,
        source_term="Banana",
        translated_term="Банан",
        category="other",
        status=TermStatus.APPROVED,
    )
    t3 = GlossaryTerm(
        project_id=project.id,
        source_term="Cherry",
        translated_term="Вишня",
        category="other",
        status=TermStatus.APPROVED,
    )
    t4 = GlossaryTerm(
        project_id=project.id,
        source_term="Draft",
        translated_term="Черновик",
        category="other",
        status=TermStatus.PENDING,
    )

    db.add_all([t1, t2, t3, t4])
    db.commit()

    text = "I like Apple and Banana pie."

    relevant = GlossaryService.get_relevant_terms(db, project.id, text)

    assert len(relevant) == 2
    sources = {t.source_term for t in relevant}
    assert "Apple" in sources
    assert "Banana" in sources
    assert "Cherry" not in sources
    assert "Draft" not in sources  # PENDING should be ignored


def test_get_relevant_terms_case_insensitive(db: Session):
    project = Project(name="Test Project 2", source_language="en", target_language="ru")
    db.add(project)
    db.commit()
    db.refresh(project)

    t1 = GlossaryTerm(
        project_id=project.id,
        source_term="magic sword",
        translated_term="меч",
        category="artifact",
        status=TermStatus.APPROVED,
    )
    db.add(t1)
    db.commit()

    text = "He found a Magic Sword."
    relevant = GlossaryService.get_relevant_terms(db, project.id, text)
    assert len(relevant) == 1
    assert relevant[0].source_term == "magic sword"
