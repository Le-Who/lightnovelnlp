import pytest
import re
import time
from app.core.regex_utils import safe_finditer

def test_safe_finditer_normal():
    """Test normal regex matching with multiple groups."""
    text = "Chapter 1: The Beginning\nChapter 2: The End"
    pattern = r"Chapter (\d+): ([^\n]+)"

    matches = list(safe_finditer(pattern, text, timeout=2.0))

    assert len(matches) == 2

    m1 = matches[0]
    # Check groups
    assert m1.group(0) == "Chapter 1: The Beginning"
    assert m1.group(1) == "1"
    assert m1.group(2) == "The Beginning"
    # Check spans
    assert m1.start() == 0
    assert m1.end() == 24
    assert m1.span() == (0, 24)

    m2 = matches[1]
    assert m2.group(1) == "2"

def test_safe_finditer_compiled_pattern():
    """Test using a compiled regex pattern."""
    text = "abc"
    pattern = re.compile(r"b", re.IGNORECASE)
    matches = list(safe_finditer(pattern, text))
    assert len(matches) == 1
    assert matches[0].group() == "b"

def test_safe_finditer_invalid_regex():
    """Test invalid regex syntax raises RuntimeError."""
    with pytest.raises(RuntimeError) as excinfo:
        list(safe_finditer(r"(", "text"))
    assert "Regex error" in str(excinfo.value)

def test_safe_finditer_timeout_redos():
    """Test that ReDoS patterns trigger a TimeoutError."""
    # Pattern known to cause catastrophic backtracking
    pattern = r"(a+)+$"
    content = "a" * 30 + "!" # Fail at the end

    start = time.time()
    with pytest.raises(TimeoutError) as excinfo:
        # Set a short timeout for the test
        list(safe_finditer(pattern, content, timeout=0.5))

    duration = time.time() - start
    # Should fail reasonably fast (around timeout + overhead)
    # We allow some buffer for process startup overhead
    assert duration < 2.0
    assert "timed out" in str(excinfo.value)

def test_safe_finditer_no_match():
    """Test no matches found."""
    text = "abc"
    pattern = "d"
    matches = list(safe_finditer(pattern, text))
    assert len(matches) == 0

def test_safe_finditer_large_output():
    """Test that passing large data back works correctly."""
    # Generate 1000 matches
    text = "a" * 1000
    pattern = "a"
    matches = list(safe_finditer(pattern, text, timeout=5.0))
    assert len(matches) == 1000
