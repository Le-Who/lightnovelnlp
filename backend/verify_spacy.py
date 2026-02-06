
from app.core.nlp_pipeline.term_extractor import term_extractor
import sys

def run_tests():
    print("Running spaCy verification tests...")
    
    # Pre-load models (optional, happens lazily in code)
    # term_extractor._get_nlp("en")
    
    failures = 0

    # Test 1: English Lemmatization & Counting
    print("Test 1: English 'cats' -> 'cat'")
    text_en = "The cats are running. One cat is fast."
    terms_en = ["cat"]
    # Should find 'cats' and 'cat' -> total 2
    freq_en = term_extractor.count_term_frequency(text_en, terms_en, source_language="en")
    
    if freq_en.get("cat") != 2:
        print(f"FAIL: English 'cat' expected 2, got {freq_en.get('cat')}")
        failures += 1
    else:
        print("PASS: English 'cat' (lemmatization works)")

    # Test 2: Russian Lemmatization & Counting
    print("Test 2: Russian 'люди' -> 'человек'") 
    # Note: spacy ru model lemmatizes "люди" to "человек" usually
    text_ru = "Все люди братья. Этот человек мой друг."
    terms_ru = ["человек"]
    
    freq_ru = term_extractor.count_term_frequency(text_ru, terms_ru, source_language="ru")
    
    if freq_ru.get("человек") != 2:
        print(f"FAIL: Russian 'человек' expected 2, got {freq_ru.get('человек')}")
        failures += 1
    else:
        print("PASS: Russian 'человек'")

    # Test 3: Multi-word term
    print("Test 3: Multi-word 'Green Apple'")
    text_multi = "I ate a green apple. Green Apples are tasty."
    terms_multi = ["Green Apple"]
    
    freq_multi = term_extractor.count_term_frequency(text_multi, terms_multi, source_language="en")
    
    if freq_multi.get("Green Apple") != 2:
         print(f"FAIL: 'Green Apple' expected 2, got {freq_multi.get('Green Apple')}")
         failures += 1
    else:
         print("PASS: 'Green Apple'")

    if failures == 0:
        print("ALL TESTS PASSED")
    else:
        print(f"{failures} TESTS FAILED")
        sys.exit(1)

if __name__ == "__main__":
    try:
        run_tests()
    except Exception as e:
        print(f"Execution Error: {e}")
        import traceback
        traceback.print_exc()
