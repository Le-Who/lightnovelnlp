import pytest
from app.core.regex_utils import safe_finditer
import time

def test_safe_finditer_valid():
    """Test that valid regex works correctly."""
    content = "\nChapter 1\nText\nChapter 2\nText"
    # Note: user code adds \n(...) wrapper, but safe_finditer takes the full pattern
    pattern = r"\n(Chapter \d+)"
    matches = safe_finditer(pattern, content)
    assert len(matches) == 2
    assert matches[0].group(1) == "Chapter 1"
    assert matches[1].group(1) == "Chapter 2"
    assert matches[0].start() == 0
    assert matches[1].start() == 15 # \n(1) + Chapter 1(9) + \nText(5) = 15?
    # 0: \nChapter 1
    # 10: \nText
    # 15: \nChapter 2

    # \nChapter 1 (length 10) -> 0 to 10
    # \nText (length 5) -> 10 to 15
    # \nChapter 2 -> start at 15

    assert matches[1].start() == 15

def test_safe_finditer_redos():
    """Test that ReDoS attempt is caught."""
    # Malicious pattern: ((a+)+)$ matches a sequence of 'a's until end of string
    # We construct it such that it fits the usage in projects.py if the user provided ((a+)+)$
    # projects.py: f"\\n({chapter_pattern})"
    # So full pattern: \n(((a+)+)$)

    evil_pattern = r"\n(((a+)+)$)"

    # Text: \n followed by many 'a's and then '!' which forces backtracking
    content = "\n" + "a" * 25 + "!"

    start = time.time()
    with pytest.raises(TimeoutError):
        # reduced timeout for test speed
        safe_finditer(evil_pattern, content, timeout=1.0)
    end = time.time()
    assert end - start < 2.0 # Ensure it actually stopped reasonably fast

def test_safe_finditer_invalid_regex():
    """Test handling of invalid regex."""
    with pytest.raises(ValueError):
        safe_finditer(r"(", "content")
