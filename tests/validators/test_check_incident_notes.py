"""Tests for scripts/check_incident_notes.py.

The guard exists to make one rule mechanical: an incident is closed by a change,
not by an explanation. These tests therefore assert it fails in BOTH directions --
a well-formed note passes, and each individual defect (missing section, unlinked
fix, wrong filename) fails with a non-zero exit. A gate proven only on the happy
path is the defect class the incidents it guards are about.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "scripts" / "check_incident_notes.py"

GOOD_NOTE = """# Incident: something broke

**Date**: 2026-08-09
**Audience**: maintainers / owning skill: [[incident-postmortem]]

## Summary

A thing failed.

## Public-Safe Shape

The abstracted, reusable pattern with no local paths.

## Durable fix

| Fix | Link |
|---|---|
| A CI gate that fails on the bad state | [`ci.yml`](../../.github/workflows/ci.yml) |
"""


def run(incidents_dir: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPT), "--incidents-dir", str(incidents_dir)],
        capture_output=True,
        text=True,
    )


def write(incidents_dir: Path, name: str, body: str) -> Path:
    path = incidents_dir / name
    path.write_text(body, encoding="utf-8")
    return path


def test_well_formed_note_passes(tmp_path):
    write(tmp_path, "a-real-failure-20260809.md", GOOD_NOTE)
    result = run(tmp_path)
    assert result.returncode == 0, result.stderr
    assert "a-real-failure-20260809.md" in result.stdout


def test_missing_directory_is_a_noop(tmp_path):
    result = run(tmp_path / "does-not-exist")
    assert result.returncode == 0
    assert "nothing to check" in result.stdout


def test_empty_directory_is_a_noop(tmp_path):
    result = run(tmp_path)
    assert result.returncode == 0
    assert "no incident notes yet" in result.stdout


def test_durable_fix_without_a_link_fails(tmp_path):
    """The load-bearing assertion: a prose 'fix' is not a fix."""
    body = GOOD_NOTE.split("## Durable fix")[0] + (
        "## Durable fix\n\nWe will all be more careful in future.\n"
    )
    write(tmp_path, "prose-fix-20260809.md", body)
    result = run(tmp_path)
    assert result.returncode == 1
    assert "contains no link" in result.stderr


@pytest.mark.parametrize(
    "missing_heading",
    ["## Public-Safe Shape", "## Durable fix"],
)
def test_missing_required_section_fails(tmp_path, missing_heading):
    body = "\n".join(
        line for line in GOOD_NOTE.splitlines() if line.strip() != missing_heading
    )
    write(tmp_path, "missing-section-20260809.md", body)
    result = run(tmp_path)
    assert result.returncode == 1
    assert missing_heading in result.stderr


def test_filename_not_following_the_convention_fails(tmp_path):
    write(tmp_path, "no-date-suffix.md", GOOD_NOTE)
    result = run(tmp_path)
    assert result.returncode == 1
    assert "convention" in result.stderr


@pytest.mark.parametrize("name", ["README.md", "TEMPLATE.md", "shapes.md"])
def test_non_note_files_are_exempt(tmp_path, name):
    """The template and index must not be held to the note contract."""
    write(tmp_path, name, "# Not an incident note\n\nNo required sections here.\n")
    result = run(tmp_path)
    assert result.returncode == 0


def test_one_bad_note_fails_the_whole_run(tmp_path):
    write(tmp_path, "good-note-20260809.md", GOOD_NOTE)
    write(
        tmp_path,
        "bad-note-20260809.md",
        GOOD_NOTE.split("## Durable fix")[0] + "## Durable fix\n\nno link here\n",
    )
    result = run(tmp_path)
    assert result.returncode == 1
    assert "bad-note-20260809.md" in result.stderr


def test_the_real_repo_incidents_pass():
    """The shipped notes must satisfy the contract they document."""
    result = subprocess.run(
        [sys.executable, str(SCRIPT)],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
    )
    assert result.returncode == 0, result.stderr
