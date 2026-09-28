"""Tests for the exact-match legacy-span detector (v4.13.3 Phase 3.2).

The detector decides what the Phase 4 writer may offer to delete from a
user-owned file, so every fixture checks both what IS a candidate and what is
kept. A fixed fingerprint set keeps most cases independent of shipped history;
one case uses the real committed set.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.lib.installer import legacy_instruction_block as lib

START, END = "<!-- NEXUS_HUB_START -->", "<!-- NEXUS_HUB_END -->"
LEGACY = [
    "## Tech Stack",
    "- **Language**:",
    "## Key Commands",
    "# Nexus-Hub Skill Index",
    "| a | Workflow | \"x\" | catalog/skills/workflow/a/SKILL.md |",
    "**Total: 1 skills across 1 categories**",
]
KNOWN = {lib.line_hash(line) for line in LEGACY}


def _write(tmp_path: Path, lines: list[str], name: str = "CLAUDE.md", newline: str = "\n",
           bom: bool = False) -> Path:
    path = tmp_path / name
    data = (newline.join(lines) + newline).encode("utf-8")
    path.write_bytes((lib.BOM if bom else b"") + data)
    return path


def _span_text(path: Path, span: lib.LegacySpan) -> str:
    return path.read_bytes()[span.start_byte:span.end_byte].decode("utf-8")


def test_clean_managed_file_has_no_candidates(tmp_path: Path) -> None:
    path = _write(tmp_path, ["# Mine", START, *LEGACY, END])
    result = lib.detect(path, KNOWN)
    assert (result.status, result.spans, result.managed_span) == ("ok", [], (2, 9))


def test_observed_layout_splits_around_an_interleaved_user_edit(tmp_path: Path) -> None:
    lines = ["# Global", "", *LEGACY[:3], "- **Language**: Python 3.12", LEGACY[0], "",
             *LEGACY[3:], "", START, "managed", END]
    path = _write(tmp_path, lines)
    result = lib.detect(path, KNOWN)
    assert result.status == "ok"
    assert [(s.start_line, s.end_line) for s in result.spans] == [(3, 5), (7, 11)]
    assert result.kept_lines == [1, 6]
    assert _span_text(path, result.spans[1]) == "\n".join([LEGACY[0], "", *LEGACY[3:]]) + "\n"
    assert "Python 3.12" not in "".join(_span_text(path, s) for s in result.spans)


def test_identical_user_line_without_an_index_region_is_not_a_candidate(tmp_path: Path) -> None:
    path = _write(tmp_path, ["# Notes", LEGACY[0], LEGACY[1], LEGACY[2], START, *LEGACY[3:], END])
    result = lib.detect(path, KNOWN)
    assert result.spans == []
    assert result.kept_lines == [1]


def test_duplicate_candidate_text_in_two_files_needs_distinct_consent(tmp_path: Path) -> None:
    lines = [*LEGACY, START, END]
    a = lib.detect(_write(tmp_path, lines, "a.md"), KNOWN).spans[0]
    b = lib.detect(_write(tmp_path, lines, "b.md"), KNOWN).spans[0]
    assert a.sha256 == b.sha256
    assert a.consent_sha256 != b.consent_sha256


def test_consent_changes_when_the_file_changes(tmp_path: Path) -> None:
    path = _write(tmp_path, [*LEGACY, START, END])
    before = lib.detect(path, KNOWN).spans[0]
    path.write_bytes(path.read_bytes() + b"# appended later\n")
    after = lib.detect(path, KNOWN).spans[0]
    assert before.sha256 == after.sha256
    assert before.consent_sha256 != after.consent_sha256


def test_user_only_content_outside_markers(tmp_path: Path) -> None:
    path = _write(tmp_path, ["# Mine", "- rule one", START, "x", END, "- trailing rule"])
    result = lib.detect(path, KNOWN)
    assert (result.spans, result.kept_lines) == ([], [1, 2, 6])


def test_user_prose_directly_above_and_below_is_excluded(tmp_path: Path) -> None:
    path = _write(tmp_path, ["My intro.", *LEGACY, "My outro.", START, END])
    result = lib.detect(path, KNOWN)
    assert [(s.start_line, s.end_line, s.line_count) for s in result.spans] == [(2, 7, 6)]
    assert result.kept_lines == [1, 8]
    assert "My" not in _span_text(path, result.spans[0])


def test_quoted_markers_inside_the_block_use_first_start_last_end(tmp_path: Path) -> None:
    path = _write(tmp_path, [*LEGACY, START, f"quote: {END}", f"quote: {START}", END])
    result = lib.detect(path, KNOWN)
    assert result.status == "ok"
    assert result.managed_span == (7, 10)
    assert len(result.spans) == 1


@pytest.mark.parametrize("lines", [[START, "x"], ["x", END], [END, "x", START]],
                         ids=["start-only", "end-only", "reversed"])
def test_unbalanced_markers_are_malformed(tmp_path: Path, lines: list[str]) -> None:
    result = lib.detect(_write(tmp_path, [*LEGACY, *lines]), KNOWN)
    assert (result.status, result.spans) == ("markers-malformed", [])
    assert result.sha256


def test_missing_file_is_absent(tmp_path: Path) -> None:
    assert lib.detect(tmp_path / "nope.md", KNOWN).status == "absent"


def test_non_utf8_bytes_are_unreadable(tmp_path: Path) -> None:
    path = tmp_path / "bad.md"
    path.write_bytes(b"# ok\n\xff\xfe broken\n")
    result = lib.detect(path, KNOWN)
    assert (result.status, result.spans) == ("unreadable", [])


def test_missing_fingerprint_file_classifies_nothing(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(lib, "FINGERPRINTS", tmp_path / "absent.json")
    result = lib.detect(_write(tmp_path, [*LEGACY, START, END]))
    assert (result.status, result.spans) == ("no-fingerprints", [])


def test_unknown_fingerprint_schema_classifies_nothing(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    bad = tmp_path / "fp.json"
    bad.write_text(json.dumps({"schema": 99, "hashes": sorted(KNOWN)}), encoding="utf-8")
    monkeypatch.setattr(lib, "FINGERPRINTS", bad)
    assert lib.detect(_write(tmp_path, [*LEGACY, START, END])).status == "no-fingerprints"


def test_runs_under_three_non_blank_lines_are_not_candidates(tmp_path: Path) -> None:
    path = _write(tmp_path, [LEGACY[3], "", LEGACY[5], "user line", START, END])
    assert lib.detect(path, KNOWN).spans == []


@pytest.mark.parametrize(("newline", "bom"), [("\r\n", False), ("\n", True), ("\r\n", True)])
def test_byte_offsets_hold_under_crlf_and_bom(tmp_path: Path, newline: str, bom: bool) -> None:
    path = _write(tmp_path, ["Mine.", *LEGACY, START, END], newline=newline, bom=bom)
    span = lib.detect(path, KNOWN).spans[0]
    assert _span_text(path, span) == newline.join(LEGACY) + newline


def test_real_fingerprints_flag_the_shipped_skill_index(tmp_path: Path) -> None:
    index = (REPO_ROOT / "data" / "SKILL_INDEX.md").read_text(encoding="utf-8").splitlines()
    path = _write(tmp_path, ["# My rules", "- keep it short", "", *index, START, END])
    result = lib.detect(path)
    assert result.status == "ok"
    assert len(result.spans) == 1
    assert result.spans[0].start_line == 4
    assert result.kept_lines == [1, 2]
