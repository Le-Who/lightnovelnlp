import pytest
import re
import time
from app.core.regex_utils import safe_finditer, SafeMatch

def test_safe_finditer_normal():
    text = "\nГлава 1\nТекст главы 1.\nГлава 2\nТекст главы 2."
    pattern = r"\n(Глава \d+)"

    matches = safe_finditer(pattern, text)
    assert len(matches) == 2
    assert matches[0].group(1) == "Глава 1"
    assert matches[1].group(1) == "Глава 2"

    # Check start and end
    m0 = matches[0]
    assert text[m0.start():m0.end()] == "\nГлава 1"

def test_safe_finditer_timeout():
    # Evil regex that causes catastrophic backtracking
    # Pattern: (a+)+$ matches the end of string.
    # Text: a...a! (exclamation mark prevents match at the end)

    pattern = r"(a+)+$"
    text = "a" * 25 + "!"

    # We expect a TimeoutError
    with pytest.raises(TimeoutError):
        # Set a very short timeout for testing
        safe_finditer(pattern, text, timeout=0.1)

def test_safe_finditer_invalid_regex():
    with pytest.raises(re.error):
        safe_finditer(r"(unclosed group", "text")

def test_safe_finditer_groups():
    text = "abc 123"
    pattern = r"([a-z]+) (\d+)"
    matches = safe_finditer(pattern, text)
    assert len(matches) == 1
    m = matches[0]
    assert m.group(0) == "abc 123"
    assert m.group(1) == "abc"
    assert m.group(2) == "123"
    assert m.groups() == ("abc", "123")
