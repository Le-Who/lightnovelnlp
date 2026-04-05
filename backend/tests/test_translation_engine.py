"""
Unit tests — TranslationEngine._build_translation_prompt.

Level: Unit (pure function, no DB or network).
Covers:
  - Wuxia genre → prompt contains martial-arts genre cue and elevated-tone instruction.
  - Sci-fi genre → prompt contains science-fiction cue.
  - No genre → prompt contains no <style> tag.
  - Character relationships supplied → prompt embeds <character_relationships> block.
"""

import pytest

from app.core.translation_engine import translation_engine


@pytest.mark.unit
class TestBuildTranslationPrompt:
    def test_wuxia_genre_injects_martial_arts_style_cues(self):
        # Arrange
        engine = translation_engine

        # Act
        prompt = engine._build_translation_prompt(
            text="Hello", glossary_terms=[], genre="WUXIA"
        )

        # Assert
        assert "martial-arts genre" in prompt
        assert "Elevated tone" in prompt

    def test_scifi_genre_injects_science_fiction_style_cue(self):
        # Arrange
        engine = translation_engine

        # Act
        prompt = engine._build_translation_prompt(
            text="Hello", glossary_terms=[], genre="scifi"
        )

        # Assert
        assert "science-fiction" in prompt

    def test_no_genre_omits_style_xml_tag(self):
        # Arrange
        engine = translation_engine

        # Act
        prompt = engine._build_translation_prompt(
            text="Hello", glossary_terms=[], genre=None
        )

        # Assert — style block must be absent when genre is not provided
        assert "<style>" not in prompt

    def test_relationships_inject_character_relationships_block(self):
        # Arrange
        engine = translation_engine
        relationships = [
            {"source": "A", "target": "B", "type": "enemy", "description": "Hates him"}
        ]

        # Act
        prompt = engine._build_translation_prompt(
            text="Hello", glossary_terms=[], relationships=relationships
        )

        # Assert
        assert "<character_relationships>" in prompt
        assert "A" in prompt
        assert "B" in prompt
        assert "enemy" in prompt
