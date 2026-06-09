"""Tests for the AST-aware CodeCompressor (Phase 3 T010).

Covers the stability-gate assertions (Python + TypeScript signature/import
preservation with body elision) plus the regex/structural fallback, the CCR
round-trip for elided bodies, determinism, the keep-small-bodies rule, the
control-flow guard in the brace fallback, and graceful degradation when the AST
infra is unavailable.
"""

from __future__ import annotations

import pytest

from nexus_context_compressor.ccr.marker import find_all_markers, find_marker
from nexus_context_compressor.ccr.retrieve import NOT_FOUND, retrieve
from nexus_context_compressor.ccr.store import CCRStore
from nexus_context_compressor.transforms import code_compressor as cc
from nexus_context_compressor.transforms.code_compressor import (
    CodeCompressorConfig,
    compress_code,
)

PY = """import os
from sys import argv

@decorator
def foo(a, b):
    x = a + b
    y = x * 2
    z = x - y
    return z

class Bar:
    def method(self, n):
        total = 0
        for i in range(n):
            total += i
        return total
"""

TS = """import { A } from "./a";

export function add(a: number, b: number): number {
  const sum = a + b;
  const doubled = sum * 2;
  return doubled;
}

class Widget {
  render(): string {
    const html = "<div>";
    const wrapped = html + "</div>";
    return wrapped;
  }
}
"""

CFG = CodeCompressorConfig(min_body_lines=2, ccr_min_lines=3)


@pytest.fixture
def force_regex(monkeypatch):
    """Force the regex/structural fallback by making the AST loader report absent."""
    original = cc._load_ast
    original.cache_clear()  # drop any cached AST handle so the patch takes effect
    monkeypatch.setattr(cc, "_load_ast", lambda: None)
    yield
    # Clear the real (now-restored-after-teardown) loader's cache, not the lambda's.
    original.cache_clear()


# --- Stability gate: AST path preserves structure, elides bodies --------------


def test_python_ast_preserves_structure_and_elides_bodies():
    result = compress_code(PY, "python", config=CFG)
    assert result.strategy == "ast"
    code = result.code
    assert "import os" in code
    assert "from sys import argv" in code
    assert "@decorator" in code
    assert "def foo(a, b):" in code
    assert "class Bar:" in code
    assert "def method(self, n):" in code
    # Bodies are gone.
    assert "a + b" not in code
    assert "total += i" not in code
    assert result.kept_lines < result.original_lines


def test_typescript_ast_preserves_signatures_and_imports():
    result = compress_code(TS, "typescript", config=CFG)
    assert result.strategy == "ast"
    code = result.code
    assert 'import { A } from "./a";' in code
    assert "export function add(a: number, b: number): number {" in code
    assert "class Widget {" in code
    assert "render(): string {" in code
    assert "const sum = a + b;" not in code
    assert "const html" not in code
    # Brace structure stays balanced: a closing brace per kept opener.
    assert code.count("{") == code.count("}")


def test_filename_and_extension_hints_resolve_language():
    by_ext = compress_code(PY, ".py", config=CFG)
    by_file = compress_code(PY, "module.py", config=CFG)
    by_name = compress_code(PY, "python", config=CFG)
    assert by_ext.code == by_file.code == by_name.code
    assert by_ext.strategy == "ast"


# --- CCR reversibility --------------------------------------------------------


def test_elided_body_is_reversible_via_ccr_store(tmp_path):
    store = CCRStore(tmp_path / "ccr.db")
    try:
        result = compress_code(PY, "python", config=CFG, store=store)
        assert result.dropped
        marker = find_marker(result.code)
        assert marker is not None
        original = retrieve(marker.hash, store=store)
        assert original is not NOT_FOUND
        # The first elided body is foo's; its lines round-trip exactly.
        assert original == result.dropped[0].lines
    finally:
        store.close()


def test_all_markers_resolve(tmp_path):
    store = CCRStore(tmp_path / "ccr.db")
    try:
        result = compress_code(PY, "python", config=CFG, store=store)
        markers = find_all_markers(result.code)
        assert len(markers) == len(result.dropped)
        for marker in markers:
            assert retrieve(marker.hash, store=store) is not NOT_FOUND
    finally:
        store.close()


def test_store_none_has_no_side_effects(tmp_path):
    # A store passed elsewhere stays empty when compress_code is called without it.
    store = CCRStore(tmp_path / "ccr.db")
    try:
        compress_code(PY, "python", config=CFG)  # no store arg
        assert len(store) == 0
    finally:
        store.close()


# --- Determinism --------------------------------------------------------------


def test_compression_is_deterministic():
    first = compress_code(PY, "python", config=CFG)
    second = compress_code(PY, "python", config=CFG)
    assert first.code == second.code
    assert [d.hash for d in first.dropped] == [d.hash for d in second.dropped]


def test_marker_hashes_are_stable_content_hashes():
    # Same body text in two files yields the same hash (content-addressed).
    a = compress_code(PY, "python", config=CFG)
    b = compress_code(PY, ".py", config=CFG)
    assert [d.hash for d in a.dropped] == [d.hash for d in b.dropped]


# --- Regex / structural fallback ---------------------------------------------


def test_regex_fallback_python_when_ast_absent(force_regex):
    src = "import os\n\ndef foo(a, b):\n    x = a + b\n    y = x * 2\n    return x + y\n"
    result = compress_code(src, "python", config=CFG)
    assert result.strategy == "regex"
    assert "def foo(a, b):" in result.code
    assert "import os" in result.code
    assert "a + b" not in result.code


def test_regex_fallback_for_unsupported_brace_language():
    # .js is not covered by nexus-code-search -> regex BRACE fallback.
    js = (
        "import { A } from './a';\n\n"
        "function add(a, b) {\n"
        "  const sum = a + b;\n"
        "  const doubled = sum * 2;\n"
        "  return doubled;\n"
        "}\n"
    )
    result = compress_code(js, "javascript", config=CFG)
    assert result.strategy == "regex"
    assert "function add(a, b) {" in result.code
    assert "const sum" not in result.code


def test_brace_fallback_does_not_elide_control_flow():
    js = (
        "function run() {\n"
        "  const a = 1;\n"
        "  const b = 2;\n"
        "  return a + b;\n"
        "}\n\n"
        "if (x) {\n"
        "  doThing();\n"
        "  doOther();\n"
        "}\n"
    )
    result = compress_code(js, "javascript", config=CFG)
    # The function body is elided; the top-level if-block body is not.
    assert "const a = 1;" not in result.code
    assert "doThing();" in result.code


# --- Body-size policy ---------------------------------------------------------


def test_small_body_is_kept_verbatim():
    # A one-line body is below min_body_lines and is left intact.
    src = "def tiny():\n    return 1\n"
    result = compress_code(src, "python", config=CodeCompressorConfig(min_body_lines=2))
    assert result.code == src
    assert result.dropped == []
    assert result.strategy == "none"


def test_medium_body_gets_plain_non_retrievable_elision():
    # Body length in [min_body_lines, ccr_min_lines) -> plain note, not a CCR marker.
    src = "def mid():\n    a = 1\n    b = 2\n    return a + b\n"
    result = compress_code(src, "python", config=CodeCompressorConfig(min_body_lines=2, ccr_min_lines=5))
    assert "lines elided" in result.code
    assert find_marker(result.code) is None
    assert result.dropped == []


# --- Degenerate / unsupported inputs -----------------------------------------


def test_unknown_language_returns_source_unchanged():
    src = "the quick brown fox jumps over the lazy dog\n" * 3
    result = compress_code(src, "klingon", config=CFG)
    assert result.code == src
    assert result.strategy == "none"


def test_empty_source_does_not_crash():
    result = compress_code("", "python", config=CFG)
    assert result.code == ""
    assert result.dropped == []


def test_non_string_source_is_coerced():
    result = compress_code(12345, "python", config=CFG)  # type: ignore[arg-type]
    assert isinstance(result.code, str)


# --- Language resolution ------------------------------------------------------


def test_language_sniffed_from_content_when_no_hint():
    # No language given: Python is sniffed from def/import structure.
    result = compress_code(PY, None, config=CFG)
    assert result.language == "python"
    assert result.strategy in ("ast", "regex")
    assert "a + b" not in result.code


def test_prose_with_no_language_is_unchanged():
    prose = "the quick brown fox\njumps over\nthe lazy dog\n"
    result = compress_code(prose, None, config=CFG)
    assert result.code == prose
    assert result.strategy == "none"


def test_generic_family_language_elides_via_ast():
    # Ruby is AST-supported but neither indent- nor brace-delimited (def...end):
    # the GENERIC family keeps the node's first line and elides the rest.
    ruby = (
        "def greet(name)\n"
        "  prefix = 'Hello, '\n"
        "  message = prefix + name\n"
        "  puts message\n"
        "end\n"
    )
    result = compress_code(ruby, "ruby", config=CFG)
    if result.strategy == "ast":  # only assert when the ruby grammar is present
        assert "def greet(name)" in result.code
        assert "prefix = 'Hello, '" not in result.code
