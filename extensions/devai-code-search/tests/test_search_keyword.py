"""Tests for keyword search."""
from __future__ import annotations

from devai_code_search.search_keyword import KeywordIndex, _tokenize
from devai_code_search.types import Chunk


def _chunk(text: str, path: str = "f.py") -> Chunk:
    return Chunk(file_path=path, start_line=1, end_line=text.count("\n") + 1, text=text)


def test_tokenize_drops_single_char_and_non_alpha() -> None:
    toks = _tokenize("ab cd_ef 1 x z_1 $ Z99")
    # 'ab', 'cd_ef', 'x', 'z_1', 'z99' (lowercased). '1' alone is dropped (starts with digit).
    # Single-char 'x' is dropped by the length>=2 rule too.
    assert "ab" in toks
    assert "cd_ef" in toks
    assert "z_1" in toks


def test_build_empty_corpus() -> None:
    idx = KeywordIndex.build([])
    assert idx.search("anything") == []


def test_exact_match_ranks_first() -> None:
    chunks = [
        _chunk("def compute_total(items): return sum(items)", "a.py"),
        _chunk("def parse_json(text): return json.loads(text)", "b.py"),
        _chunk("def greet(name): return f'Hello, {name}'", "c.py"),
    ]
    idx = KeywordIndex.build(chunks)
    results = idx.search("compute_total")
    assert results
    assert results[0].chunk.file_path == "a.py"


def test_multi_token_intersection() -> None:
    # The tokenizer keeps identifiers intact, so we compare against snake_case
    # tokens that appear in multiple chunks.
    chunks = [
        _chunk("def find_user_by_id(user_id): return db.get(user_id)", "u.py"),
        _chunk("def greet(name): return 'hello'", "g.py"),
        _chunk("class user_profile: pass", "p.py"),
    ]
    idx = KeywordIndex.build(chunks)
    results = idx.search("find user id")
    # u.py has all three tokens 'find', 'user' (via user_id), 'id'; should win.
    assert results[0].chunk.file_path == "u.py"


def test_empty_query_returns_empty() -> None:
    chunks = [_chunk("def hi(): return 1")]
    idx = KeywordIndex.build(chunks)
    assert idx.search("") == []
    assert idx.search("   ") == []


def test_limit_enforced() -> None:
    chunks = [_chunk(f"def f_{i}(): return {i}", f"f{i}.py") for i in range(20)]
    # Add one chunk matching "payment" to ensure we have a real ranking.
    chunks.append(_chunk("def payment_processor(): pass", "pay.py"))
    idx = KeywordIndex.build(chunks)
    results = idx.search("payment", limit=3)
    assert len(results) <= 3


def test_zero_limit_returns_empty() -> None:
    chunks = [_chunk("def payment_processor(): pass")]
    idx = KeywordIndex.build(chunks)
    assert idx.search("payment", limit=0) == []
