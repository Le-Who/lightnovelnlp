
import pytest
from app.core.nlp_pipeline.term_extractor import term_extractor

def test_frequency_english():
    text = "Hello world. Hello again."
    terms = ["Hello", "world"]
    # English matching is simple case-insensitive
    freq = term_extractor.count_term_frequency(text, terms, source_language="en")
    
    assert freq["Hello"] == 2
    assert freq["world"] == 1

def test_frequency_russian():
    # Russian uses pymorphy logic
    text = "Кошки гуляли по крыше. Кошка увидела мышь."
    terms = ["Кошка"]
    
    freq = term_extractor.count_term_frequency(text, terms, source_language="ru")
    assert freq["Кошка"] == 2  # Кошки (pl) + Кошка (sg) -> lemma match

def test_frequency_chinese():
    # Chinese typically needs specific tokenization, but our fallback is substring search
    text = "我爱北京天安门，天安门上太阳升"
    terms = ["天安门"]
    
    freq = term_extractor.count_term_frequency(text, terms, source_language="zh")
    assert freq["天安门"] == 2

def test_frequency_case_insensitive():
    text = "Test TEST test"
    terms = ["test"]
    freq = term_extractor.count_term_frequency(text, terms, source_language="en")
    assert freq["test"] == 3
