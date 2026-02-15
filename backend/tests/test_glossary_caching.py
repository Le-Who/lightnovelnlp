import pytest
from unittest.mock import MagicMock, patch
from sqlalchemy.orm import Session
from app.models.glossary import GlossaryTerm, TermStatus
from app.services.glossary_service import GlossaryService

def test_get_relevant_terms_cache_hit(db: Session):
    """Verify that cached terms are used if available."""
    project_id = 999
    text = "Hello world, this is a test."

    # Mock cached data
    cached_terms = [
        {
            "id": 101,
            "project_id": project_id,
            "source_term": "world",
            "translated_term": "mundo",
            "category": "common",
            "status": "approved",
            "context": "global",
            "frequency": 5
        },
        {
            "id": 102,
            "project_id": project_id,
            "source_term": "foo",
            "translated_term": "bar",
            "category": "common",
            "status": "approved",
            "context": "test",
            "frequency": 1
        }
    ]

    # Patch cache_service inside glossary_service module
    with patch('app.services.glossary_service.cache_service') as mock_cache:
        mock_cache.get_cached_glossary.return_value = cached_terms

        # Act
        results = GlossaryService.get_relevant_terms(db, project_id, text)

        # Assert
        # "world" is in text, "foo" is not
        assert len(results) == 1
        assert results[0].id == 101
        assert results[0].source_term == "world"
        assert results[0].translated_term == "mundo"

        # Verify cache was checked
        mock_cache.get_cached_glossary.assert_called_once_with(project_id)

        # Verify result is a detached GlossaryTerm object (has attributes but not in session)
        assert isinstance(results[0], GlossaryTerm)
        # Note: checking detachment is tricky with in-memory SQLite and fake objects,
        # but the logic implies no DB query if cache hit.

def test_get_relevant_terms_cache_miss_populates_cache(db: Session):
    """Verify that cache miss triggers DB query and populates cache."""
    project_id = 888
    text = "Hello galaxy."

    # Create term in DB
    term = GlossaryTerm(
        id=201,
        project_id=project_id,
        source_term="galaxy",
        translated_term="galaxia",
        category="space",
        status=TermStatus.APPROVED,
        context="milky way",
        frequency=10
    )
    db.add(term)
    db.commit()

    with patch('app.services.glossary_service.cache_service') as mock_cache:
        mock_cache.get_cached_glossary.return_value = None

        # Act
        results = GlossaryService.get_relevant_terms(db, project_id, text)

        # Assert
        assert len(results) == 1
        assert results[0].source_term == "galaxy"

        # Verify cache was checked
        mock_cache.get_cached_glossary.assert_called_once_with(project_id)

        # Verify cache was populated
        mock_cache.cache_glossary.assert_called_once()
        args, _ = mock_cache.cache_glossary.call_args
        cached_pid, cached_list = args
        assert cached_pid == project_id
        assert len(cached_list) == 1
        assert cached_list[0]['source_term'] == "galaxy"
        assert cached_list[0]['translated_term'] == "galaxia"
        assert cached_list[0]['category'] == "space"
