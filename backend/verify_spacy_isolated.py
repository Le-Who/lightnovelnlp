
import spacy
from collections import Counter
from typing import List, Dict
import logging

# Setup basic logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class IsolatedTermExtractor:
    def __init__(self):
        self.nlp_models = {}

    def _get_nlp(self, lang: str):
        if lang not in self.nlp_models:
            if lang == "ru":
                print("Loading spaCy model: ru_core_news_sm")
                self.nlp_models[lang] = spacy.load("ru_core_news_sm")
            else:
                print("Loading spaCy model: en_core_web_sm")
                self.nlp_models[lang] = spacy.load("en_core_web_sm")
        return self.nlp_models[lang]

    # Logic copied exactly from the refactored term_extractor.py
    def count_term_frequency(self, text: str, terms: List[str], source_language: str = "en") -> Dict[str, int]:
        if not terms or not text:
            return {}
        
        lang_code = "ru" if source_language == "ru" else "en"
        
        try:
            nlp = self._get_nlp(lang_code)
        except Exception as e:
            print(f"Failed to load NLP model: {e}")
            text_lower = text.lower()
            return {term: text_lower.count(term.lower()) for term in terms}

        doc = nlp(text, disable=["ner", "parser"])
        text_lemmas = [token.lemma_.lower() for token in doc if not token.is_punct and not token.is_space]
        lemma_counts = Counter(text_lemmas)
        
        frequency = {}
        for term in terms:
            term_doc = nlp(term, disable=["ner", "parser"])
            term_lemmas = [t.lemma_.lower() for t in term_doc if not t.is_punct and not t.is_space]
            
            if not term_lemmas:
                 frequency[term] = 0
                 continue
                 
            if len(term_lemmas) == 1:
                frequency[term] = lemma_counts.get(term_lemmas[0], 0)
            else:
                count = 0
                n = len(term_lemmas)
                for i in range(len(text_lemmas) - n + 1):
                    if text_lemmas[i:i+n] == term_lemmas:
                        count += 1
                frequency[term] = count
                
        return frequency

def run_tests():
    print("Running ISOLATED spaCy verification tests...")
    extractor = IsolatedTermExtractor()
    failures = 0

    # Test 1: English
    text_en = "The cats are running. One cat is fast."
    freq_en = extractor.count_term_frequency(text_en, ["cat"], "en")
    if freq_en.get("cat") != 2:
        print(f"FAIL: English 'cat' expected 2, got {freq_en.get('cat')}")
        failures += 1
    else:
         print("PASS: English 'cats' -> 'cat'")

    # Test 2: Russian
    text_ru = "Все люди братья. Этот человек мой друг."
    freq_ru = extractor.count_term_frequency(text_ru, ["человек"], "ru")
    if freq_ru.get("человек") != 2:
        print(f"FAIL: Russian 'человек' expected 2, got {freq_ru.get('человек')}")
        failures += 1
    else:
         print("PASS: Russian 'люди' -> 'человек'")

    # Test 3: Multi-word
    text_multi = "I ate a green apple. Green Apples are tasty."
    freq_multi = extractor.count_term_frequency(text_multi, ["Green Apple"], "en")
    if freq_multi.get("Green Apple") != 2:
         print(f"FAIL: 'Green Apple' expected 2, got {freq_multi.get('Green Apple')}")
         failures += 1
    else:
         print("PASS: 'Green Apple'")

    if failures == 0:
        print("ALL TESTS PASSED")
    else:
        import sys
        sys.exit(1)

if __name__ == "__main__":
    run_tests()
