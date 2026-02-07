import pytest
from app.core.nlp_pipeline.term_extractor import TermExtractor
from app.models.project import ProjectGenre

@pytest.fixture
def extractor():
    return TermExtractor()

def test_build_extraction_prompt_default(extractor):
    text = "Some text"
    prompt = extractor._build_extraction_prompt(text, ProjectGenre.OTHER)

    # Check default language (en) instructions
    assert "Транскрибируй имена кириллицей" in prompt
    # Check default genre instructions
    assert "уникальные термины" in prompt
    # Check text presence
    assert text in prompt
    # Check genre label in header
    assert "OTHER" in prompt

def test_build_extraction_prompt_wuxia_zh(extractor):
    text = "Cultivation text"
    prompt = extractor._build_extraction_prompt(text, ProjectGenre.WUXIA, source_language="zh")

    # Check Chinese instructions
    assert "Транслитерируй имена пиньинем" in prompt
    # Check Wuxia instructions
    assert "мастера боевых искусств" in prompt
    # Check genre label
    assert "WUXIA" in prompt

def test_build_extraction_prompt_scifi_ja(extractor):
    text = "Space text"
    prompt = extractor._build_extraction_prompt(text, ProjectGenre.SCIFI, source_language="ja")

    # Check Japanese instructions
    assert "honorfics" in prompt # Matching the typo/spelling in the source code
    # Check Scifi instructions
    assert "технологии, планеты" in prompt
    # Check genre label
    assert "SCIFI" in prompt

def test_build_extraction_prompt_custom_instructions(extractor):
    text = "Custom text"
    custom = "Special instructions for this project"
    prompt = extractor._build_extraction_prompt(
        text,
        ProjectGenre.FANTASY,
        custom_instructions=custom
    )

    # Check custom instructions are present
    assert f"КАСТОМНЫЕ ИНСТРУКЦИИ:\n{custom}" in prompt
    # Check standard genre instructions are NOT present (custom overrides genre)
    assert "имена, магия, расы" not in prompt

def test_build_extraction_prompt_unknown_genre(extractor):
    text = "Unknown genre text"
    # Testing robust handling if passed a string that isn't in Enum
    prompt = extractor._build_extraction_prompt(text, "unknown_genre")

    # Should fallback to OTHER instructions
    assert "уникальные термины" in prompt

    # The label will be the passed string, uppercased
    assert "UNKNOWN_GENRE" in prompt

def test_build_extraction_prompt_unknown_language(extractor):
    text = "Unknown lang text"
    prompt = extractor._build_extraction_prompt(text, ProjectGenre.OTHER, source_language="fr")

    # Should fallback to EN instructions
    assert "Транскрибируй имена кириллицей" in prompt
