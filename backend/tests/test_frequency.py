import pytest

# spaCy unavailable on Python 3.14 (local). Skipped here, runs on 3.12 (production).
try:
    from app.core.nlp_pipeline.term_extractor import term_extractor

    _SPACY_AVAILABLE = True
except Exception:
    _SPACY_AVAILABLE = False

if not _SPACY_AVAILABLE:
    pytest.skip("spaCy unavailable on this Python version", allow_module_level=True)


def test_frequency_english():
    text = "Hello world. Hello again."
    terms = ["Hello", "world"]
    # English matching is simple case-insensitive with word boundaries
    freq = term_extractor.count_term_frequency(text, terms, source_language="en")

    assert freq["Hello"] == 2
    assert freq["world"] == 1


def test_frequency_russian():
    # Uses spaCy lemmatization
    # So "Кошки" (plural) match "Кошка" (singular) via lemma
    text = "Кошки гуляли по крыше. Кошка увидела мышь."
    terms = ["Кошка", "Кошки"]

    freq = term_extractor.count_term_frequency(text, terms, source_language="ru")
    # Both terms reduce to lemma "кошка", and text has 2 instances of lemma "кошка"
    assert freq["Кошка"] == 2
    assert freq["Кошки"] == 2


def test_frequency_english_lemmatization():
    text = "The cats are running. The cat sits."
    terms = ["cat"]
    freq = term_extractor.count_term_frequency(text, terms, source_language="en")
    assert freq["cat"] == 2


def test_frequency_chinese():
    # Chinese typically needs specific tokenization, but our fallback is substring search
    text = "我爱北京天安门，天安门上太阳升"
    terms = ["天安门", "我爱"]

    freq = term_extractor.count_term_frequency(text, terms, source_language="zh")
    assert freq["天安门"] == 2
    assert freq["我爱"] == 1


def test_frequency_case_insensitive():
    text = "Test TEST test"
    terms = ["test"]
    freq = term_extractor.count_term_frequency(text, terms, source_language="en")
    assert freq["test"] == 3


def test_frequency_empty_inputs():
    assert term_extractor.count_term_frequency("", ["term"]) == {}
    assert term_extractor.count_term_frequency("text", []) == {}
    assert term_extractor.count_term_frequency("", []) == {}
    assert term_extractor.count_term_frequency(None, ["term"]) == {}


def test_frequency_terms_not_found():
    text = "Hello world"
    terms = ["missing", "absent"]
    freq = term_extractor.count_term_frequency(text, terms)
    assert freq["missing"] == 0
    assert freq["absent"] == 0


def test_frequency_word_boundaries():
    # "test" should not match inside "testing" or "attest"
    text = "test testing attest test"
    terms = ["test"]
    freq = term_extractor.count_term_frequency(text, terms)
    assert freq["test"] == 2


def test_frequency_special_characters_escaped():
    # Verify that special regex characters in terms are escaped and treated as literals
    # "a.b" -> matches "a" boundary "." boundary "b" in regex word boundary logic
    text = "a.b"
    terms = ["a.b"]
    freq = term_extractor.count_term_frequency(text, terms)
    assert freq["a.b"] == 1


def test_frequency_fallback_cjk_languages():
    # Verify ja and ko also use simple count
    text = "こんにちは世界"
    terms = ["世界"]
    freq = term_extractor.count_term_frequency(text, terms, source_language="ja")
    assert freq["世界"] == 1

    text = "안녕하세요 세계"
    terms = ["세계"]
    freq = term_extractor.count_term_frequency(text, terms, source_language="ko")
    assert freq["세계"] == 1
