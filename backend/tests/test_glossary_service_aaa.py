"""
Unit tests — GlossaryService pure logic (filter_terms_by_text, sort_terms_by_priority).
Integration tests — GlossaryService.get_relevant_terms (real SQLite in-memory DB).

Level: Unit for pure functions, Integration for DB-dependent methods.
Covers:
  - filter_terms_by_text: case-insensitive substring matching, empty inputs, no matches.
  - sort_terms_by_priority: longest terms first.
  - get_relevant_terms: only APPROVED terms, case-insensitive, PENDING excluded.

Original issues in test_glossary_service.py:
  - act+assert merged in one-liners in test_empty_input (assert filter(...) == []).
  - No separation between Arrange, Act, Assert sections.
  - test_filter_terms_substring_safety misleadingly named (it tests substring match, not safety).
"""

from conftest import make_glossary_term, make_project
from sqlalchemy.orm import Session

from app.services.glossary_service import GlossaryService

# ── Helper mock for filter_terms_by_text (pure function tests) ────────────────


class _MockTerm:
    """Minimal stand-in for GlossaryTerm, carrying only source_term."""

    def __init__(self, source_term: str):
        self.source_term = source_term


# ── filter_terms_by_text ──────────────────────────────────────────────────────


class TestFilterTermsByText:
    def test_returns_only_terms_present_in_text(self):
        # Arrange
        terms = [_MockTerm("Eren"), _MockTerm("Mikasa"), _MockTerm("Levi")]
        text = "Eren and Mikasa went to the wall."

        # Act
        result = GlossaryService.filter_terms_by_text(text, terms)

        # Assert
        result_names = {t.source_term for t in result}
        assert result_names == {"Eren", "Mikasa"}
        assert "Levi" not in result_names

    def test_matching_is_case_insensitive(self):
        # Arrange
        terms = [_MockTerm("titan")]
        text = "Attack on Titan"

        # Act
        result = GlossaryService.filter_terms_by_text(text, terms)

        # Assert
        assert len(result) == 1
        assert result[0].source_term == "titan"

    def test_matches_substring_within_word(self):
        # Arrange — GlossaryService uses substring match (not word-boundary)
        terms = [_MockTerm("Fire")]
        text = "Fireball"

        # Act
        result = GlossaryService.filter_terms_by_text(text, terms)

        # Assert
        assert len(result) == 1

    def test_returns_empty_list_for_empty_text(self):
        # Arrange
        terms = [_MockTerm("Something")]
        text = ""

        # Act
        result = GlossaryService.filter_terms_by_text(text, terms)

        # Assert
        assert result == []

    def test_returns_empty_list_for_empty_terms(self):
        # Arrange
        terms = []
        text = "Non-empty text with content"

        # Act
        result = GlossaryService.filter_terms_by_text(text, terms)

        # Assert
        assert result == []

    def test_returns_empty_list_when_no_terms_found_in_text(self):
        # Arrange
        terms = [_MockTerm("Dragon"), _MockTerm("Knight")]
        text = "A quiet village with no fantasy elements."

        # Act
        result = GlossaryService.filter_terms_by_text(text, terms)

        # Assert
        assert result == []


# ── sort_terms_by_priority ─────────────────────────────────────────────────────


class TestSortTermsByPriority:
    def test_sorts_longer_terms_first(self):
        # Arrange
        terms = [_MockTerm("A"), _MockTerm("ABCDE"), _MockTerm("ABC")]

        # Act
        result = GlossaryService.sort_terms_by_priority(terms)

        # Assert — longest first
        lengths = [len(t.source_term) for t in result]
        assert lengths == sorted(lengths, reverse=True)

    def test_preserves_all_terms(self):
        # Arrange
        terms = [_MockTerm("Dragon"), _MockTerm("Empire"), _MockTerm("Sword")]

        # Act
        result = GlossaryService.sort_terms_by_priority(terms)

        # Assert
        assert len(result) == len(terms)

    def test_returns_unchanged_list_when_already_sorted(self):
        # Arrange
        terms = [_MockTerm("Cultivation"), _MockTerm("Pill"), _MockTerm("Qi")]

        # Act
        result = GlossaryService.sort_terms_by_priority(terms)

        # Assert — "Cultivation" is longest and should remain first
        assert result[0].source_term == "Cultivation"


# ── get_relevant_terms (integration — real DB) ────────────────────────────────


class TestGetRelevantTerms:
    def test_returns_only_approved_terms_present_in_text(self, db: Session):
        # Arrange
        project = make_project(db)
        make_glossary_term(
            db, project.id, source_term="Apple", translated_term="Яблоко"
        )
        make_glossary_term(
            db, project.id, source_term="Banana", translated_term="Банан"
        )
        make_glossary_term(
            db, project.id, source_term="Cherry", translated_term="Вишня"
        )
        text = "I like Apple and Banana pie."

        # Act
        result = GlossaryService.get_relevant_terms(db, project.id, text)

        # Assert
        result_names = {t.source_term for t in result}
        assert result_names == {"Apple", "Banana"}
        assert "Cherry" not in result_names

    def test_excludes_pending_terms_from_results(self, db: Session):
        # Arrange
        project = make_project(db)
        make_glossary_term(db, project.id, source_term="PendingTerm", status="pending")
        text = "This text contains PendingTerm."

        # Act
        result = GlossaryService.get_relevant_terms(db, project.id, text)

        # Assert — PENDING terms must never appear in translation context
        assert result == []

    def test_matching_is_case_insensitive(self, db: Session):
        # Arrange
        project = make_project(db)
        make_glossary_term(
            db, project.id, source_term="magic sword", translated_term="меч"
        )
        text = "He found a Magic Sword in the dungeon."

        # Act
        result = GlossaryService.get_relevant_terms(db, project.id, text)

        # Assert
        assert len(result) == 1
        assert result[0].source_term == "magic sword"

    def test_returns_empty_list_when_text_is_empty(self, db: Session):
        # Arrange
        project = make_project(db)
        make_glossary_term(db, project.id, source_term="Dragon")
        text = ""

        # Act
        result = GlossaryService.get_relevant_terms(db, project.id, text)

        # Assert
        assert result == []

    def test_returns_empty_list_when_glossary_is_empty(self, db: Session):
        # Arrange
        project = make_project(db)
        # No terms added
        text = "Dragon appeared from the sky."

        # Act
        result = GlossaryService.get_relevant_terms(db, project.id, text)

        # Assert
        assert result == []
