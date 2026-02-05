
import sys
from unittest.mock import MagicMock

# 1. Mock dependencies BEFORE importing the target module
mock_gemini = MagicMock()
sys.modules["app.services.gemini_client"] = mock_gemini
sys.modules["app.core.config"] = MagicMock()

# Mocking internal imports that might trigger config loading
mock_gemini.gemini_client = MagicMock()

# 2. Import target
# We need to ensure we can import term_extractor even if it imports gemini_client
from app.core.nlp_pipeline.term_extractor import term_extractor

def test_morphology_counting():
    # Текст с терминами в разных падежах
    text = "Рыцарь достал свой меч. Ударом меча он поразил врага. О мече слагали легенды."
    terms = ["рыцарь", "меч", "щит"]
    
    # Ожидание
    frequencies = term_extractor.count_term_frequency(text, terms)
    
    print(f"Text: {text}")
    print(f"Terms: {terms}")
    print(f"Result: {frequencies}")
    
    assert frequencies["рыцарь"] == 1, f"Expected 1, got {frequencies['рыцарь']}"
    assert frequencies["меч"] == 3, f"Expected 3, got {frequencies['меч']}"
    assert frequencies["щит"] == 0, f"Expected 0, got {frequencies['щит']}"
    
    print("SUCCESS: Morphology test passed!")

if __name__ == "__main__":
    test_morphology_counting()
