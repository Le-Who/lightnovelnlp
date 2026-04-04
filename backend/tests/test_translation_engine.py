from app.core.translation_engine import translation_engine


def test_build_prompt_wuxia_genre():
    engine = translation_engine

    prompt = engine._build_translation_prompt(
        text="Hello", glossary_terms=[], genre="WUXIA"
    )

    # Wuxia style now in English: martial-arts genre
    assert "martial-arts genre" in prompt
    assert "Elevated tone" in prompt


def test_build_prompt_scifi_genre():
    engine = translation_engine

    prompt = engine._build_translation_prompt(
        text="Hello", glossary_terms=[], genre="scifi"
    )

    assert "science-fiction" in prompt


def test_build_prompt_no_genre():
    engine = translation_engine

    prompt = engine._build_translation_prompt(
        text="Hello", glossary_terms=[], genre=None
    )

    assert "<style>" not in prompt


def test_build_prompt_with_relationships():
    engine = translation_engine
    rels = [{"source": "A", "target": "B", "type": "enemy", "description": "Hates him"}]

    prompt = engine._build_translation_prompt(
        text="Hello", glossary_terms=[], relationships=rels
    )

    assert "<character_relationships>" in prompt
    assert "A" in prompt
    assert "B" in prompt
    assert "enemy" in prompt
