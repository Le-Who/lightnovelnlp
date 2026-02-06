import pytest
import re
from app.core.regex_utils import safe_finditer, SafeMatch

def test_safe_finditer_simple():
    text = "\nChapter 1\nText\nChapter 2\nText"
    pattern = r"(\nChapter \d+)"
    matches = safe_finditer(pattern, text)

    assert len(matches) == 2
    assert matches[0].group(1) == "\nChapter 1"
    assert matches[0].group(0) == "\nChapter 1" # Group 0 should match full match
    assert matches[1].group(1) == "\nChapter 2"

    # Check start/end
    assert text[matches[0].start():matches[0].end()] == "\nChapter 1"

def test_safe_finditer_no_groups():
    """Test that it works even if pattern has no capturing groups"""
    text = "Chapter 1"
    pattern = r"Chapter \d+"
    matches = safe_finditer(pattern, text)

    assert len(matches) == 1
    assert matches[0].group(0) == "Chapter 1"
    assert matches[0].groups() == ()

    with pytest.raises(IndexError):
        matches[0].group(1)

def test_safe_finditer_multiple_groups():
    text = "A: 1, B: 2"
    pattern = r"([A-Z]): (\d+)"
    matches = safe_finditer(pattern, text)

    assert len(matches) == 2
    assert matches[0].group(0) == "A: 1"
    assert matches[0].group(1) == "A"
    assert matches[0].group(2) == "1"
    assert matches[0].groups() == ("A", "1")

def test_safe_finditer_timeout():
    # A classic ReDoS pattern: (a+)+$ matches aaaaaaaaaaaaaaaaaaaaaa!
    bad_pattern = r"(a+)+$"
    text = "a" * 30 + "!"

    # Should timeout quickly
    with pytest.raises(TimeoutError):
        safe_finditer(bad_pattern, text, timeout=0.5)
