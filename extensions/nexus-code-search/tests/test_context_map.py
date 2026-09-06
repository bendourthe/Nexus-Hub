"""Tests for the Phase 1 compiled context-map generator.

Covers the generator core, the MCP tool handler, and the extension CLI (which
is exactly what `nexus-hub map` forwards to). Fixtures build a real graph with
the ExtractionOrchestrator so the tests exercise the full read path.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

from nexus_code_search.config import CodeSearchConfig, index_dir_for
from nexus_code_search.contextmap import ContextMapResult, generate_context_map
from nexus_code_search.contextmap.cli import main as map_cli_main
from nexus_code_search.contextmap.tokens import count_tokens
from nexus_code_search.extraction import ExtractionOrchestrator
from nexus_code_search.server import _handle_generate_context_map

META_PREFIX = "<!-- nexus-context-map"


def _cfg() -> CodeSearchConfig:
    return CodeSearchConfig(hub_root=None)


def _index_dir(root: Path) -> Path:
    return index_dir_for(root, _cfg())


def _build_graph(root: Path) -> None:
    with ExtractionOrchestrator(root, _cfg(), _index_dir(root)) as orch:
        orch.run()


@pytest.fixture
def graph_repo(tmp_path: Path) -> Path:
    """A small indexed repo: two src modules (py + ts) and a root-level file."""
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.py").write_text(
        "def compute_total(items):\n    return sum(items)\n\n\n"
        "class Calculator:\n    def add(self, a, b):\n        return a + b\n",
        encoding="utf-8",
    )
    (tmp_path / "src" / "utils.ts").write_text(
        "export function greet(name: string) {\n  return `Hi ${name}`;\n}\n\n"
        "export class UserService {\n  findUser(id: number) { return null; }\n}\n",
        encoding="utf-8",
    )
    (tmp_path / "app.py").write_text("def run():\n    return 1\n", encoding="utf-8")
    _build_graph(tmp_path)
    return tmp_path


def _strip_meta(text: str) -> str:
    return "\n".join(
        line for line in text.split("\n") if not line.startswith(META_PREFIX)
    )


def _header_tokens(text: str) -> int:
    for line in text.splitlines():
        if line.startswith(META_PREFIX):
            match = re.search(r"tokens:\s*(\d+)", line)
            if match:
                return int(match.group(1))
    raise AssertionError("no token header found in document")


# --- Generation + structure -------------------------------------------------


def test_generates_map_and_articles(graph_repo: Path) -> None:
    result = generate_context_map(graph_repo, _index_dir(graph_repo))
    assert isinstance(result, ContextMapResult)
    assert not result.skipped
    assert result.files_indexed == 3
    assert result.symbols >= 4  # two classes + two functions at least

    nexus = graph_repo / ".nexus"
    assert (nexus / "CONTEXT-MAP.md").is_file()
    assert (nexus / "context" / "index.md").is_file()
    assert (nexus / "context" / "src.md").is_file()
    assert (nexus / "context" / "_root.md").is_file()


def test_map_has_required_sections(graph_repo: Path) -> None:
    generate_context_map(graph_repo, _index_dir(graph_repo))
    text = (graph_repo / ".nexus" / "CONTEXT-MAP.md").read_text(encoding="utf-8")
    for section in (
        "# Codebase Context Map",
        "## Overview",
        "## Module Structure",
        "## Most-Imported Files",
        "## Context Articles",
    ):
        assert section in text, f"missing section: {section}"
    assert "python" in text  # language line populated
    assert "`src`" in text  # module row present


def test_most_imported_section_present(graph_repo: Path) -> None:
    generate_context_map(graph_repo, _index_dir(graph_repo))
    text = (graph_repo / ".nexus" / "CONTEXT-MAP.md").read_text(encoding="utf-8")
    # Phase 4 fills this from import edges; the graph_repo fixture has no
    # cross-file imports, so it renders the empty-state note (not the old
    # Phase 1 "Not yet available" placeholder).
    assert "## Most-Imported Files" in text
    assert "Not yet available" not in text


def test_article_lists_files_and_symbols(graph_repo: Path) -> None:
    generate_context_map(graph_repo, _index_dir(graph_repo))
    article = (graph_repo / ".nexus" / "context" / "src.md").read_text(encoding="utf-8")
    assert "## Files" in article
    assert "## Key Symbols" in article
    assert "Calculator" in article
    assert "src/main.py" in article
    # Backlink to the map keeps the article set navigable (Phase 5 lint relies
    # on this).
    assert "../CONTEXT-MAP.md" in article


# --- Token-count header -----------------------------------------------------


def test_token_header_accurate_for_map(graph_repo: Path) -> None:
    generate_context_map(graph_repo, _index_dir(graph_repo))
    text = (graph_repo / ".nexus" / "CONTEXT-MAP.md").read_text(encoding="utf-8")
    assert _header_tokens(text) == count_tokens(_strip_meta(text))


def test_token_header_accurate_for_every_article(graph_repo: Path) -> None:
    generate_context_map(graph_repo, _index_dir(graph_repo))
    for article in (graph_repo / ".nexus" / "context").glob("*.md"):
        text = article.read_text(encoding="utf-8")
        assert _header_tokens(text) == count_tokens(_strip_meta(text)), article.name


# --- Neutral-path guarantee -------------------------------------------------


def test_writes_only_under_nexus(graph_repo: Path) -> None:
    before = {p for p in graph_repo.rglob("*") if p.is_file()}
    generate_context_map(graph_repo, _index_dir(graph_repo))
    after = {p for p in graph_repo.rglob("*") if p.is_file()}
    nexus = (graph_repo / ".nexus").resolve()
    new_outside = [p for p in (after - before) if not p.resolve().is_relative_to(nexus)]
    assert new_outside == [], f"wrote outside .nexus/: {new_outside}"


def test_never_writes_ai_config_files(graph_repo: Path) -> None:
    generate_context_map(graph_repo, _index_dir(graph_repo))
    for forbidden in ("CLAUDE.md", "AGENTS.md", ".cursorrules"):
        assert not (graph_repo / forbidden).exists()


# --- Content-hash no-op -----------------------------------------------------


def test_regeneration_is_noop_when_unchanged(graph_repo: Path) -> None:
    first = generate_context_map(graph_repo, _index_dir(graph_repo))
    assert not first.skipped
    map_path = graph_repo / ".nexus" / "CONTEXT-MAP.md"
    original = map_path.read_bytes()

    second = generate_context_map(graph_repo, _index_dir(graph_repo))
    assert second.skipped
    assert map_path.read_bytes() == original  # untouched


def test_force_regenerates_byte_identical(graph_repo: Path) -> None:
    generate_context_map(graph_repo, _index_dir(graph_repo))
    map_path = graph_repo / ".nexus" / "CONTEXT-MAP.md"
    before = map_path.read_bytes()

    forced = generate_context_map(graph_repo, _index_dir(graph_repo), force=True)
    assert not forced.skipped
    assert map_path.read_bytes() == before


def test_graph_change_invalidates_noop(graph_repo: Path) -> None:
    first = generate_context_map(graph_repo, _index_dir(graph_repo))
    (graph_repo / "src" / "extra.py").write_text(
        "def added():\n    return 2\n", encoding="utf-8"
    )
    _build_graph(graph_repo)  # re-index picks up the new file

    second = generate_context_map(graph_repo, _index_dir(graph_repo))
    assert not second.skipped
    assert second.source_hash != first.source_hash
    assert second.files_indexed == first.files_indexed + 1


# --- MCP tool + CLI ---------------------------------------------------------


def test_tool_handler_returns_summary(graph_repo: Path) -> None:
    res = _handle_generate_context_map({"root": str(graph_repo)}, _cfg())
    payload = json.loads(res[0].text)
    assert payload["files_indexed"] == 3
    assert payload["map_path"].endswith("CONTEXT-MAP.md")
    assert payload["total_tokens"] > 0


def test_tool_handler_rejects_missing_root(tmp_path: Path) -> None:
    with pytest.raises(ValueError):
        _handle_generate_context_map({"root": str(tmp_path / "nope")}, _cfg())


def test_tool_and_cli_produce_identical_map(graph_repo: Path) -> None:
    _handle_generate_context_map({"root": str(graph_repo), "force": True}, _cfg())
    via_tool = (graph_repo / ".nexus" / "CONTEXT-MAP.md").read_bytes()

    rc = map_cli_main([str(graph_repo), "--force"])
    assert rc == 0
    via_cli = (graph_repo / ".nexus" / "CONTEXT-MAP.md").read_bytes()

    assert via_tool == via_cli


def test_cli_json_output(graph_repo: Path, capsys: pytest.CaptureFixture) -> None:
    rc = map_cli_main([str(graph_repo), "--json"])
    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["map_path"].endswith("CONTEXT-MAP.md")
    assert payload["files_indexed"] == 3


def test_cli_missing_graph_exits_2(tmp_path: Path) -> None:
    # No graph index built for this repo -> exit code 2 with guidance.
    assert map_cli_main([str(tmp_path)]) == 2


def test_cli_missing_root_exits_1(tmp_path: Path) -> None:
    assert map_cli_main([str(tmp_path / "does-not-exist")]) == 1


# --- Degenerate graph -------------------------------------------------------


def test_empty_graph_produces_valid_map(tmp_path: Path) -> None:
    (tmp_path / "notes.txt").write_text("no code here\n", encoding="utf-8")
    _build_graph(tmp_path)  # builds an empty graph DB (no supported files)

    result = generate_context_map(tmp_path, _index_dir(tmp_path))
    assert result.files_indexed == 0
    text = (tmp_path / ".nexus" / "CONTEXT-MAP.md").read_text(encoding="utf-8")
    assert "No indexed files" in text
    assert _header_tokens(text) == count_tokens(_strip_meta(text))


def test_cli_empty_graph_prints_note(
    tmp_path: Path, capsys: pytest.CaptureFixture
) -> None:
    (tmp_path / "notes.txt").write_text("no code here\n", encoding="utf-8")
    _build_graph(tmp_path)  # empty graph DB exists, so the CLI proceeds
    assert map_cli_main([str(tmp_path)]) == 0
    assert "graph is empty" in capsys.readouterr().err


# --- Token counting (tiktoken preference + fallback) ------------------------


class _FakeEncoding:
    def encode(self, text: str) -> list[int]:
        # Deterministic, distinct from the heuristic so the path is observable.
        return [0] * (len(text.split()) + 7)


def test_count_tokens_prefers_tiktoken(monkeypatch: pytest.MonkeyPatch) -> None:
    import sys
    import types

    fake = types.ModuleType("tiktoken")
    fake.get_encoding = lambda name: _FakeEncoding()  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "tiktoken", fake)

    sample = "one two three"
    assert count_tokens(sample) == len(sample.split()) + 7


def test_count_tokens_falls_back_when_tiktoken_raises(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import sys
    import types

    def _boom(name: str):
        raise RuntimeError("offline vocab fetch failed")

    fake = types.ModuleType("tiktoken")
    fake.get_encoding = _boom  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "tiktoken", fake)

    # Falls back to the stdlib heuristic (word + punctuation runs), never raises.
    assert count_tokens("a, b, c") > 0


def test_count_tokens_empty_is_zero() -> None:
    assert count_tokens("") == 0
