
import sys
from unittest.mock import MagicMock

# 1. Mock dependencies
sys.modules["app.services.gemini_client"] = MagicMock()
sys.modules["app.core.config"] = MagicMock() # Block config loading
# Also mock sqlalchemy stuff if needed, though translation_engine imports it only for type hints mostly?
# It imports Session from sqlalchemy.orm
sys.modules["sqlalchemy.orm"] = MagicMock()

from app.core.translation_engine import translation_engine

def test_context_injection():
    text = "Chapter 2 content."
    glossary_terms = []
    prev_context = "End of Chapter 1. The hero fell asleep."
    
    # The method _build_translation_prompt is pure logic, tested here
    prompt = translation_engine._build_translation_prompt(
        text=text,
        glossary_terms=glossary_terms,
        previous_context=previous_context
    )
    
    print("Generated Prompt Preview:")
    print(prompt[:500])
    
    # Assertions
    assert "КОНТЕКСТ ПРЕДЫДУЩЕЙ ГЛАВЫ" in prompt, "Context header missing"
    assert prev_context in prompt, "Previous context text missing in prompt"
    
    print("\nSUCCESS: Context injected correctly!")

if __name__ == "__main__":
    test_context_injection()
