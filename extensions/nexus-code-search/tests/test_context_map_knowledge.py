"""Phase 6 tests: knowledge-map extractor."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from nexus_code_search.contextmap.cli import main as map_cli_main
from nexus_code_search.contextmap.knowledge import generate_knowledge_map
from nexus_code_search.server import _handle_generate_knowledge_map

FIXTURE_NOTES = Path(__file__).parent / "fixtures" / "knowledge"

# Expected classification for each committed fixture note (zero misclassification).
_EXPECTED_CATEGORY = {
    "adr-0001-database.md": "decision",
    "meeting-2026-07-01.md": "meeting",
    "retro-sprint-5.md": "retro",
    "spec-search.md": "spec",
    "research-caching.md": "research",
    "onboarding.md": "note",
}


@pytest.fixture
def repo_with_notes(tmp_path: Path) -> Path:
    """A repo whose `notes/` folder is a copy of the committed knowledge fixtures."""
    notes = tmp_path / "notes"
    shutil.copytree(FIXTURE_NOTES, notes)
    return tmp_path


def _knowledge_text(root: Path) -> str:
    return (root / ".nexus" / "KNOWLEDGE.md").read_text(encoding="utf-8")


def test_classifies_every_note_correctly(repo_with_notes: Path) -> None:
    from nexus_code_search.contextmap.knowledge import (
        _classify,
        _read,
        _split_frontmatter,
    )
    import re

    heading_re = re.compile(r"^#{1,6}\s+(.*\S)\s*$", re.MULTILINE)
    notes_dir = repo_with_notes / "notes"
    for name, expected in _EXPECTED_CATEGORY.items():
        text = _read(notes_dir / name)
        _fm, body = _split_frontmatter(text)
        headings = heading_re.findall(body)
        assert _classify(name, headings, body) == expected, name


def test_generates_knowledge_map(repo_with_notes: Path) -> None:
    result = generate_knowledge_map(repo_with_notes, repo_with_notes / "notes")
    assert not result.skipped
    assert result.note_count == 6
    assert result.decision_count == 1
    assert result.open_question_count >= 3
    assert (repo_with_notes / ".nexus" / "KNOWLEDGE.md").is_file()


def test_extracts_decision_statement(repo_with_notes: Path) -> None:
    generate_knowledge_map(repo_with_notes, repo_with_notes / "notes")
    text = _knowledge_text(repo_with_notes)
    assert "Choose the primary datastore" in text  # frontmatter title
    assert "PostgreSQL over MySQL" in text  # the decision statement


def test_extracts_open_questions(repo_with_notes: Path) -> None:
    generate_knowledge_map(repo_with_notes, repo_with_notes / "notes")
    text = _knowledge_text(repo_with_notes)
    assert "Which ranking model do we adopt?" in text
    assert "Do we need typo tolerance in v1?" in text
    assert "add SSO setup instructions." in text  # a standalone TODO


def test_categorized_index(repo_with_notes: Path) -> None:
    generate_knowledge_map(repo_with_notes, repo_with_notes / "notes")
    text = _knowledge_text(repo_with_notes)
    for section in (
        "### Decisions",
        "### Meetings",
        "### Retrospectives",
        "### Specs",
        "### Research",
        "### Notes",
    ):
        assert section in text, section


def test_writes_only_under_nexus(repo_with_notes: Path) -> None:
    before = {p for p in repo_with_notes.rglob("*") if p.is_file()}
    generate_knowledge_map(repo_with_notes, repo_with_notes / "notes")
    after = {p for p in repo_with_notes.rglob("*") if p.is_file()}
    nexus = (repo_with_notes / ".nexus").resolve()
    new_outside = [p for p in (after - before) if not p.resolve().is_relative_to(nexus)]
    assert new_outside == []


def test_noop_and_change_invalidation(repo_with_notes: Path) -> None:
    first = generate_knowledge_map(repo_with_notes, repo_with_notes / "notes")
    assert not first.skipped
    assert generate_knowledge_map(repo_with_notes, repo_with_notes / "notes").skipped
    (repo_with_notes / "notes" / "adr-0002.md").write_text(
        "# ADR 2\n\n## Decision\n\nWe will add a cache layer.\n", encoding="utf-8"
    )
    second = generate_knowledge_map(repo_with_notes, repo_with_notes / "notes")
    assert not second.skipped
    assert second.source_hash != first.source_hash
    assert second.decision_count == 2


def test_cli_knowledge_mode(
    repo_with_notes: Path, capsys: pytest.CaptureFixture
) -> None:
    rc = map_cli_main(
        [str(repo_with_notes), "--knowledge", str(repo_with_notes / "notes"), "--json"]
    )
    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["note_count"] == 6
    assert payload["decision_count"] == 1


def test_mcp_generate_knowledge_map_handler(repo_with_notes: Path) -> None:
    res = _handle_generate_knowledge_map(
        {"root": str(repo_with_notes), "notes_path": str(repo_with_notes / "notes")}
    )
    payload = json.loads(res[0].text)
    assert payload["note_count"] == 6
    assert payload["knowledge_path"].endswith("KNOWLEDGE.md")
