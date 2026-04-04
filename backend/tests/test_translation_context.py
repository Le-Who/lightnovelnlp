"""
Unit tests — TranslationService._get_relevant_relationships

Level: Unit (real SQLite in-memory DB, no external dependencies).
Behavior under test:
  - Both endpoint terms present → relationship is returned.
  - Only one term present → empty list (not enough context).
  - Two terms present but no relationship → empty list.
  - Relationship exists but for a different pair → empty list.

Original violation: four independent scenarios crammed into one function,
violating AAA and making failure diagnosis cryptic. Each scenario is now
a dedicated, self-contained test.
"""

import pytest

from app.models.glossary import GlossaryTerm, TermRelationship, TermStatus
from app.models.project import Project, ProjectGenre
from app.services.translation_service import TranslationService

# ── Fixtures ──────────────────────────────────────────────────────────────────


@pytest.fixture()
def project(db):
    """A minimal persisted project."""
    p = Project(name="Relationship Test Project", genre=ProjectGenre.FANTASY)
    db.add(p)
    db.commit()
    db.refresh(p)
    return p


@pytest.fixture()
def alice(db, project):
    t = GlossaryTerm(
        project_id=project.id,
        source_term="Alice",
        translated_term="Алиса",
        category="character",
        status=TermStatus.APPROVED,
    )
    db.add(t)
    db.commit()
    db.refresh(t)
    return t


@pytest.fixture()
def bob(db, project):
    t = GlossaryTerm(
        project_id=project.id,
        source_term="Bob",
        translated_term="Боб",
        category="character",
        status=TermStatus.APPROVED,
    )
    db.add(t)
    db.commit()
    db.refresh(t)
    return t


@pytest.fixture()
def charlie(db, project):
    t = GlossaryTerm(
        project_id=project.id,
        source_term="Charlie",
        translated_term="Чарли",
        category="character",
        status=TermStatus.APPROVED,
    )
    db.add(t)
    db.commit()
    db.refresh(t)
    return t


@pytest.fixture()
def alice_bob_relationship(db, project, alice, bob):
    """A 'friends' relationship from Alice to Bob."""
    rel = TermRelationship(
        project_id=project.id,
        source_term_id=alice.id,
        target_term_id=bob.id,
        relation_type="friends",
        context="Childhood friends",
    )
    db.add(rel)
    db.commit()
    return rel


# ── Tests ─────────────────────────────────────────────────────────────────────


class TestGetRelevantRelationships:
    def test_returns_relationship_when_both_endpoint_terms_are_present(
        self, db, alice, bob, alice_bob_relationship
    ):
        # Arrange — relationship already created by fixture; both terms in input list

        # Act
        result = TranslationService._get_relevant_relationships(db, [alice, bob])

        # Assert
        assert len(result) == 1
        assert result[0]["source"] == "Alice"
        assert result[0]["target"] == "Bob"
        assert result[0]["type"] == "friends"

    def test_returns_empty_list_when_only_one_endpoint_term_is_present(
        self, db, alice, bob, alice_bob_relationship
    ):
        # Arrange — relationship exists but only Alice is passed in

        # Act
        result = TranslationService._get_relevant_relationships(db, [alice])

        # Assert — need both terms to establish context
        assert result == []

    def test_returns_empty_list_when_single_term_provided(self, db, alice):
        # Arrange — only one term, no relationship can be detected

        # Act
        result = TranslationService._get_relevant_relationships(db, [alice])

        # Assert
        assert result == []

    def test_returns_empty_list_when_terms_present_but_no_relationship_exists(
        self, db, alice, charlie
    ):
        # Arrange — Alice and Charlie exist but have no relationship between them

        # Act
        result = TranslationService._get_relevant_relationships(db, [alice, charlie])

        # Assert
        assert result == []

    def test_returns_empty_list_when_input_is_empty(self, db):
        # Arrange — no terms at all

        # Act
        result = TranslationService._get_relevant_relationships(db, [])

        # Assert
        assert result == []

    def test_does_not_return_relationship_when_one_endpoint_term_is_absent_from_input(
        self, db, alice, bob, charlie, alice_bob_relationship
    ):
        # Arrange — Bob is absent from input (Alice and Charlie only); Alice-Bob rel exists

        # Act
        result = TranslationService._get_relevant_relationships(db, [alice, charlie])

        # Assert — Alice-Bob rel should NOT appear because Bob is not in input set
        assert result == []
