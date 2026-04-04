import pytest

# spaCy → Celery pydantic.v1 → incompatible with Python 3.14 (local only).
# Guard prevents CollectionError; tests run on Python 3.12 (production).
try:
    from app.core.nlp_pipeline.term_extractor import term_extractor
    from app.models.project import ProjectGenre
    _SPACY_AVAILABLE = True
except Exception:
    _SPACY_AVAILABLE = False

if not _SPACY_AVAILABLE:
    pytest.skip("spaCy unavailable on this Python version", allow_module_level=True)



def test_term_extractor_parsing(mock_gemini):
    # Mock response
    mock_response = json.dumps({
        "terms": [
            {
                "source_term": "Eren Yeager",
                "translated_term": "Эрен Йегер",
                "category": "character",
                "context": "Main protagonist",
                "auto_approve": True,
                "confidence": 95
            },
            {
                "source_term": "Titan",
                "translated_term": "Титан",
                "category": "other",
                "confidence": 40
            }
        ]
    })
    
    mock_gemini.return_value = mock_response
    
    terms = term_extractor.extract_terms("Some text about Eren", ProjectGenre.FANTASY)
    
    assert len(terms) == 2
    assert terms[0]["source_term"] == "Eren Yeager"
    assert terms[0]["auto_approve"] is True
    assert terms[1]["source_term"] == "Titan"
    assert terms[1]["auto_approve"] is False  # Confidence < 80 and not character
