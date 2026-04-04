from app.core.nlp_pipeline.term_extractor import term_extractor
import sys


def run_tests():
    print("Running verification tests...")
    failures = 0

    # Test 1: English (Case Insensitive)
    text_en = "Hello world. HELLO again."
    terms_en = ["Hello", "world"]
    freq_en = term_extractor.count_term_frequency(
        text_en, terms_en, source_language="en"
    )

    if freq_en.get("Hello") != 2:
        print(f"FAIL: English 'Hello' expected 2, got {freq_en.get('Hello')}")
        failures += 1
    else:
        print("PASS: English 'Hello'")

    if freq_en.get("world") != 1:
        print(f"FAIL: English 'world' expected 1, got {freq_en.get('world')}")
        failures += 1
    else:
        print("PASS: English 'world'")

    # Test 2: Russian (Morphology)
    text_ru = "Кошки гуляли. Кошка ушла."
    terms_ru = ["Кошка"]
    freq_ru = term_extractor.count_term_frequency(
        text_ru, terms_ru, source_language="ru"
    )

    # pymorphy should match 'Кошки' (pl) to 'Кошка' (sg)
    if freq_ru.get("Кошка") != 2:
        print(f"FAIL: Russian 'Кошка' expected 2, got {freq_ru.get('Кошка')}")
        failures += 1
    else:
        print("PASS: Russian 'Кошка' (Morphology check)")

    # Test 3: Chinese (Substring)
    text_zh = "我爱北京天安门，天安门上太阳升"
    terms_zh = ["天安门"]
    freq_zh = term_extractor.count_term_frequency(
        text_zh, terms_zh, source_language="zh"
    )

    if freq_zh.get("天安门") != 2:
        print(f"FAIL: Chinese '天安门' expected 2, got {freq_zh.get('天安门')}")
        failures += 1
    else:
        print("PASS: Chinese '天安门'")

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
