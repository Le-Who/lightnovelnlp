"""
Unit tests — TranslationService._parse_review_json

Level: Unit (pure function, no DB or network).
Covers:
  - Valid JSON object → parsed correctly.
  - JSON wrapped in markdown code fences → stripped and parsed.
  - Missing optional fields → defaults applied.
  - Empty string → safe fallback with parse_error key.
  - Malformed JSON → safe fallback, no exception raised.
  - Score coerced to int.
  - violations list preserved as list.

Critical behavior: The parser must NEVER raise an exception — it is the last
guard between a hallucinating LLM and a broken production pipeline. Any failure
to parse must silently return a safe fallback dictionary.
"""

from app.services.translation_service import TranslationService

_parse = TranslationService._parse_review_json


class TestParseReviewJsonHappyPath:
    def test_parses_complete_valid_json(self):
        # Arrange
        raw = (
            '{"score": 8, "passed": true, "violations": [], "style_notes": "Good job"}'
        )

        # Act
        result = _parse(raw)

        # Assert
        assert result["score"] == 8
        assert result["passed"] is True
        assert result["violations"] == []
        assert result["style_notes"] == "Good job"

    def test_parses_json_with_nonempty_violations(self):
        # Arrange
        raw = (
            '{"score": 4, "passed": false, '
            '"violations": [{"source_term": "修炼", "expected": "Cultivation",'
            ' "found": "Training", "excerpt": "...after Training..."}],'
            ' "style_notes": ""}'
        )

        # Act
        result = _parse(raw)

        # Assert
        assert result["passed"] is False
        assert len(result["violations"]) == 1
        assert result["violations"][0]["source_term"] == "修炼"
        assert result["violations"][0]["expected"] == "Cultivation"

    def test_strips_markdown_json_fence_before_parsing(self):
        # Arrange — LLM wraps output in ```json ... ``` despite instructions
        raw = '```json\n{"score": 7, "passed": true, "violations": []}\n```'

        # Act
        result = _parse(raw)

        # Assert
        assert result["score"] == 7
        assert "parse_error" not in result


class TestParseReviewJsonMissingFields:
    def test_applies_default_score_when_missing(self):
        # Arrange
        raw = '{"passed": true, "violations": []}'

        # Act
        result = _parse(raw)

        # Assert
        assert result["score"] == 5  # defined default

    def test_applies_default_passed_when_missing(self):
        # Arrange
        raw = '{"score": 6, "violations": []}'

        # Act
        result = _parse(raw)

        # Assert
        assert result["passed"] is True  # safe default = no blocking violations

    def test_applies_empty_violations_when_missing(self):
        # Arrange
        raw = '{"score": 6, "passed": true}'

        # Act
        result = _parse(raw)

        # Assert
        assert result["violations"] == []

    def test_applies_empty_style_notes_when_missing(self):
        # Arrange
        raw = '{"score": 6, "passed": true, "violations": []}'

        # Act
        result = _parse(raw)

        # Assert
        assert result["style_notes"] == ""


class TestParseReviewJsonFailureFallback:
    def test_returns_safe_dict_on_empty_string_input(self):
        # Act
        result = _parse("")

        # Assert — must never raise; must return usable fallback
        assert isinstance(result, dict)
        assert "parse_error" in result
        assert result["violations"] == []
        assert result["passed"] is True  # safe default: don't block pipeline

    def test_returns_safe_dict_on_malformed_json(self):
        # Act
        result = _parse("{invalid: json]")

        # Assert
        assert isinstance(result, dict)
        assert "parse_error" in result
        assert result["violations"] == []

    def test_returns_safe_dict_on_none_input(self):
        # Act
        result = _parse(None)

        # Assert
        assert isinstance(result, dict)
        assert result["violations"] == []

    def test_does_not_raise_on_completely_wrong_type(self):
        # Act & Assert — must never propagate exceptions to the caller
        result = _parse(12345)
        assert isinstance(result, dict)


class TestParseReviewJsonTypeCoercion:
    def test_coerces_score_string_to_int(self):
        # Arrange — some models return score as string "8" instead of int 8
        raw = '{"score": "8", "passed": true, "violations": []}'

        # Act
        result = _parse(raw)

        # Assert
        assert isinstance(result["score"], int)
        assert result["score"] == 8

    def test_coerces_passed_int_to_bool(self):
        # Arrange — some models return 1/0 instead of true/false
        raw = '{"score": 7, "passed": 0, "violations": []}'

        # Act
        result = _parse(raw)

        # Assert
        assert isinstance(result["passed"], bool)
        assert result["passed"] is False
