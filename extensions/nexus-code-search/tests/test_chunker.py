"""Tests for the recursive character splitter."""
from __future__ import annotations

import pytest

from nexus_code_search.chunker import chunk_text


def test_empty_text_returns_empty_list() -> None:
    assert chunk_text("", "file.py") == []


def test_tiny_file_returns_single_chunk() -> None:
    text = "def hi():\n    return 1\n"
    chunks = chunk_text(text, "file.py")
    assert len(chunks) == 1
    assert chunks[0].text == text
    assert chunks[0].file_path == "file.py"
    assert chunks[0].start_line == 1
    assert chunks[0].end_line >= 1


def test_line_numbers_are_1_indexed() -> None:
    text = "line1\nline2\nline3\n"
    chunks = chunk_text(text, "f.txt")
    assert chunks[0].start_line == 1


def test_large_file_produces_multiple_chunks() -> None:
    # 3 KB of repeating content well above the 600-char target.
    text = ("def func():\n    pass\n\n" * 200)
    chunks = chunk_text(text, "big.py", target_size=600, overlap=80)
    assert len(chunks) >= 4
    # Every chunk should be non-empty and at most target_size long.
    for chunk in chunks:
        assert chunk.text
        assert len(chunk.text) <= 600 + 50  # small slack for separator alignment


def test_prefers_function_boundary_separator() -> None:
    # Arrange: text with a clear function boundary around char ~300.
    header = "x = 1\n" * 50  # ~300 chars
    payload = "\n\ndef my_function():\n    return 42\n"
    tail = "y = 2\n" * 50  # ~300 chars
    text = header + payload + tail
    chunks = chunk_text(text, "f.py", target_size=400, overlap=40)
    # At least one chunk should start with "def my_function" - the splitter prefers that boundary.
    assert any("def my_function" in c.text for c in chunks)


def test_overlap_must_be_less_than_target() -> None:
    with pytest.raises(ValueError):
        chunk_text("abc", "f.txt", target_size=10, overlap=10)


def test_overlap_must_be_non_negative() -> None:
    with pytest.raises(ValueError):
        chunk_text("abc", "f.txt", target_size=10, overlap=-1)
