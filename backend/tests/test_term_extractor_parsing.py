import json
import pytest
from app.core.nlp_pipeline.term_extractor import term_extractor
from app.schemas.nlp import TermExtractionResponse, Term

class MockSDKResponse:
    def __init__(self, terms):
        self.terms = terms

def test_parse_sdk_response():
    """Test parsing a response object that mimics the Google Generative AI SDK response."""
    # Create a list of Term objects (Pydantic models)
    terms_data = [
        Term(source_term="Hero", translated_term="Герой", category="character", context="Main", confidence=90),
        Term(source_term="Sword", translated_term="Меч", category="artifact", context="Weapon", confidence=85)
    ]
    mock_response = MockSDKResponse(terms=terms_data)

    extracted = term_extractor._parse_response(mock_response)

    assert len(extracted) == 2
    assert extracted[0]["source_term"] == "Hero"
    assert extracted[0]["auto_approve"] is True  # Character -> True
    assert extracted[1]["source_term"] == "Sword"
    assert extracted[1]["auto_approve"] is True  # Artifact + >80 conf -> True

def test_parse_string_response():
    """Test parsing a valid JSON string response."""
    json_data = {
        "terms": [
            {
                "source_term": "Village",
                "translated_term": "Деревня",
                "category": "location",
                "context": "Starting point",
                "confidence": 75
            }
        ]
    }
    response_str = json.dumps(json_data)

    extracted = term_extractor._parse_response(response_str)

    assert len(extracted) == 1
    assert extracted[0]["source_term"] == "Village"
    assert extracted[0]["auto_approve"] is False  # Location + <80 conf -> False

def test_parse_string_list_response():
    """Test parsing a JSON string that is a list of terms directly."""
    json_data = [
        {
            "source_term": "Skill1",
            "translated_term": "Навык1",
            "category": "skill",
            "confidence": 85
        }
    ]
    response_str = json.dumps(json_data)

    extracted = term_extractor._parse_response(response_str)

    assert len(extracted) == 1
    assert extracted[0]["source_term"] == "Skill1"
    assert extracted[0]["auto_approve"] is True # Skill + >80 conf -> True

def test_parse_string_cleanup():
    """Test that markdown code blocks are removed from string response."""
    json_data = {
        "terms": [
            {
                "source_term": "Magic",
                "translated_term": "Магия",
                "category": "skill",
                "confidence": 90
            }
        ]
    }
    # Wrap in markdown code block
    response_str = f"```json\n{json.dumps(json_data)}\n```"

    extracted = term_extractor._parse_response(response_str)

    assert len(extracted) == 1
    assert extracted[0]["source_term"] == "Magic"

def test_parse_dict_response():
    """Test parsing a dictionary response."""
    response_dict = {
        "terms": [
            {
                "source_term": "Guild",
                "translated_term": "Гильдия",
                "category": "other",
                "confidence": 95
            }
        ]
    }

    extracted = term_extractor._parse_response(response_dict)

    assert len(extracted) == 1
    assert extracted[0]["source_term"] == "Guild"
    assert extracted[0]["auto_approve"] is False  # Other -> False (even with high confidence)

def test_auto_approve_logic():
    """Test the auto-approve logic for different categories and confidence levels."""
    terms_input = {
        "terms": [
            # Character -> Always True
            {"source_term": "Char1", "translated_term": "C1", "category": "character", "confidence": 10},
            # Location/Skill/Artifact >= 80 -> True
            {"source_term": "Loc1", "translated_term": "L1", "category": "location", "confidence": 80},
            {"source_term": "Skill1", "translated_term": "S1", "category": "skill", "confidence": 85},
            {"source_term": "Art1", "translated_term": "A1", "category": "artifact", "confidence": 99},
            # Location/Skill/Artifact < 80 -> False
            {"source_term": "Loc2", "translated_term": "L2", "category": "location", "confidence": 79},
            # Other -> False
            {"source_term": "Other1", "translated_term": "Ot1", "category": "other", "confidence": 100},
        ]
    }

    extracted = term_extractor._parse_response(terms_input)

    results = {item["source_term"]: item["auto_approve"] for item in extracted}

    assert results["Char1"] is True
    assert results["Loc1"] is True
    assert results["Skill1"] is True
    assert results["Art1"] is True
    assert results["Loc2"] is False
    assert results["Other1"] is False

def test_error_handling_invalid_json():
    """Test handling of invalid JSON string."""
    response_str = "{invalid_json}"
    extracted = term_extractor._parse_response(response_str)
    assert extracted == []

def test_error_handling_unexpected_type():
    """Test handling of unexpected input type."""
    response_int = 12345
    extracted = term_extractor._parse_response(response_int)
    assert extracted == []

def test_empty_response():
    """Test handling of empty response."""
    extracted = term_extractor._parse_response("")
    assert extracted == []

    extracted = term_extractor._parse_response({})
    assert extracted == []
