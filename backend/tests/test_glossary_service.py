from app.services.glossary_service import GlossaryService
from app.models.glossary import GlossaryTerm

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
