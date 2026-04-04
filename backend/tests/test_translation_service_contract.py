"""
Integration tests — TranslationService.translate_chapter service contract.

Level: Integration (SQLite in-memory DB via `db` fixture, mocked Gemini + cache).

Covers:
  - Chapter not found → returns dict with 'error' key and status_code 404.
    (Documents the KNOWN design smell: service conflates error signals with HTTP
     codes instead of raising HTTPException. This test pins the CURRENT CONTRACT
     so any unintended breakage is caught immediately.)
  - Chapter found, valid glossary → translation persisted to DB.
  - Cached translation returned when glossary hash matches cache.
  - Translation result includes correct glossary_terms_used count.

Design note: We mock the cache_service and translation_engine directly because
they touch Redis and Gemini respectively — both are out-of-scope for service-level
integration tests. The goal is to test the orchestration logic, not the providers.
"""

from unittest.mock import patch

import pytest
from conftest import make_chapter, make_glossary_term, make_project

STUB_TRANSLATED = "Переведённый текст."


@pytest.mark.integration
class TestTranslateChapterContract:
    @patch("app.services.translation_service.cache_service")
    def test_returns_error_dict_with_status_404_for_missing_chapter(
        self, mock_cache, db
    ):
        """
        Pins the CURRENT contract: service returns a dict (not raises HTTPException)
        for a missing chapter. This is a documented design smell — do not change
        the assertion shape until the architecture is refactored.
        """
        # Arrange
        mock_cache.generate_glossary_hash.return_value = "hash"
        mock_cache.get_cached_translation.return_value = None
        from app.services.translation_service import TranslationService

        # Act — chapter_id 99999 does not exist
        result = TranslationService.translate_chapter(db, 99999)

        # Assert — current contract is to return a dict, not raise
        assert "error" in result
        assert result.get("status_code") == 404

    @patch("app.services.translation_service.cache_service")
    @patch("app.services.translation_service.translation_engine")
    def test_persists_translated_text_to_db_after_successful_translation(
        self, mock_engine, mock_cache, db
    ):
        # Arrange
        project = make_project(db)
        chapter = make_chapter(db, project.id, original_text="Original text here.")
        mock_cache.generate_glossary_hash.return_value = "hash_abc"
        mock_cache.get_cached_translation.return_value = None  # cache miss
        mock_cache.cache_translation.return_value = None
        mock_engine.translate_with_glossary.return_value = STUB_TRANSLATED
        from app.services.translation_service import TranslationService

        # Act
        result = TranslationService.translate_chapter(db, chapter.id)

        # Assert — result is correct
        assert result["chapter_id"] == chapter.id
        assert result["translated_text"] == STUB_TRANSLATED
        assert "error" not in result

        # Assert — DB state persisted
        db.refresh(chapter)
        assert chapter.translated_text == STUB_TRANSLATED

    @patch("app.services.translation_service.cache_service")
    def test_returns_cached_translation_without_calling_engine(
        self, mock_cache, db
    ):
        # Arrange
        project = make_project(db)
        chapter = make_chapter(db, project.id, original_text="Text for caching.")
        mock_cache.generate_glossary_hash.return_value = "hash_xyz"
        mock_cache.get_cached_translation.return_value = "Кэшированный текст."
        from app.services.translation_service import TranslationService

        with patch(
            "app.services.translation_service.translation_engine"
        ) as mock_engine:
            # Act
            result = TranslationService.translate_chapter(db, chapter.id)

            # Assert — engine must NOT have been called (served from cache)
            mock_engine.translate_with_glossary.assert_not_called()
            assert result["translated_text"] == "Кэшированный текст."
            assert result.get("cached") is True

    @patch("app.services.translation_service.cache_service")
    @patch("app.services.translation_service.translation_engine")
    def test_glossary_terms_used_count_reflects_matching_approved_terms(
        self, mock_engine, mock_cache, db
    ):
        # Arrange — 2 APPROVED terms, both present in text; 1 PENDING (excluded)
        project = make_project(db)
        make_glossary_term(db, project.id, source_term="Sword", translated_term="Меч")
        make_glossary_term(db, project.id, source_term="Hero", translated_term="Герой")
        make_glossary_term(
            db,
            project.id,
            source_term="Guild",
            translated_term="Гильдия",
            status="pending",
        )
        chapter = make_chapter(
            db,
            project.id,
            original_text="The Hero picked up the Sword from the Guild.",
        )
        mock_cache.generate_glossary_hash.return_value = "h"
        mock_cache.get_cached_translation.return_value = None
        mock_cache.cache_translation.return_value = None
        mock_engine.translate_with_glossary.return_value = STUB_TRANSLATED
        from app.services.translation_service import TranslationService

        # Act
        result = TranslationService.translate_chapter(db, chapter.id)

        # Assert — only 2 APPROVED terms, PENDING excluded from count
        assert result["glossary_terms_used"] == 2
