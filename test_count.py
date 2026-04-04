import sys
import os

os.environ["DATABASE_URL"] = "postgresql://a"
os.environ["REDIS_URL"] = "redis://b"
os.environ["GEMINI_API_KEYS_RAW"] = "c"

sys.path.append('e:/Projects/LightNovelNLP/lightnovelnlp/backend')

from app.core.nlp_pipeline.term_extractor import TermExtractor

extractor = TermExtractor()

text = "Lin Feng went to the mountain. Lin Feng was happy. Then Lin Feng fought."
terms = ["Lin Feng", "mountain"]

counts = extractor.count_term_frequency(text, terms, "en")
print("Counts EN:", counts)

counts = extractor.count_term_frequency(text, terms, "ru")
print("Counts RU:", counts)
