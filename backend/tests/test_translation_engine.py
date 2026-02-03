from unittest.mock import MagicMock
from app.core.translation_engine import translation_engine
from app.models.glossary import GlossaryTerm
from app.models.project import ProjectGenre

def test_build_prompt_wuxia_genre():
    engine = translation_engine 
    # Mocking client is not strictly needed as we call _build_translation_prompt directly
    
    prompt = engine._build_translation_prompt(
        text="Hello",
        glossary_terms=[],
        genre="WUXIA"
    )
    
    # Wuxia now uses 'ушу' terminology instead of 'культивации'
    assert "терминологию ушу" in prompt
    assert "возвышенный тон" in prompt

def test_build_prompt_scifi_genre():
    engine = translation_engine
    
    prompt = engine._build_translation_prompt(
        text="Hello",
        glossary_terms=[],
        genre="scifi" 
    )
    
    assert "Технически точный язык" in prompt

def test_build_prompt_no_genre():
    engine = translation_engine
    
    prompt = engine._build_translation_prompt(
        text="Hello",
        glossary_terms=[],
        genre=None
    )
    
    assert "Стиль:" not in prompt

def test_build_prompt_with_relationships():
    engine = translation_engine
    rels = [{"source": "A", "target": "B", "type": "enemy", "description": "Hates him"}]
    
    prompt = engine._build_translation_prompt(
        text="Hello",
        glossary_terms=[],
        relationships=rels
    )
    
    assert "СВЯЗИ МЕЖДУ ПЕРСОНАЖАМИ" in prompt
    assert "A и B: enemy" in prompt
