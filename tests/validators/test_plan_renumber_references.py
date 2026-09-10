"""Tests for the residual-reference check that proves a renumber is complete.

A renumber rewrites version identity that merged pull requests and published
documentation already reference. A single surviving reference is a broken link
or a stale tracker row, so the check fails on one.

Two traps are pinned here because both have actually occurred in this
repository: a bare section number that merely looks like a version must not be
treated as one, and a deliberately historical claim is repaired with a dated
note rather than a silent restatement.
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from enumerate_plan_queue import find_residual_references, main


def write(root: Path, rel: str, body: str) -> Path:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")
    return path


def test_clean_renumber_leaves_nothing(tmp_path: Path) -> None:
    write(tmp_path, "docs/releases/v4/v4.11/plans/v4.11.0-x.md", "**Version**: v4.11.0\n")
    write(tmp_path, "docs/todos.md", "| v4.11.0 tasks | 0 | 1 | 1 |\n")

    assert find_residual_references(tmp_path, "v4.10.0") == []
    assert main(["--root", str(tmp_path), "--check-residual", "v4.10.0"]) == 0


def test_a_single_survivor_fails(tmp_path: Path) -> None:
    # One is enough. The check is not a threshold.
    write(tmp_path, "docs/a.md", "all good here\n")
    write(tmp_path, "docs/b.md", "line one\nsee v4.10.0 for details\n")

    findings = find_residual_references(tmp_path, "v4.10.0")

    assert len(findings) == 1
    assert findings[0][0] == "docs/b.md"
    assert findings[0][1] == 2
    assert main(["--root", str(tmp_path), "--check-residual", "v4.10.0"]) == 1


def test_surviving_relative_link_fails(tmp_path: Path) -> None:
    write(
        tmp_path,
        "docs/releases/v4/v4.9/plans/v4.9.0-a.md",
        "See the [plan](../../v4.10/plans/v4.10.0-x.md).\n",
    )

    assert find_residual_references(tmp_path, "v4.10") != []


def test_surviving_link_reference_definition_fails(tmp_path: Path) -> None:
    # A link-text-only scan misses this entirely, which is why it is pinned.
    write(
        tmp_path,
        "docs/c.md",
        "Body text citing [the plan][N8].\n\n"
        "[N8]: ../../../../../docs/releases/v4/v4.10/plans/v4.10.0-x.md\n",
    )

    findings = find_residual_references(tmp_path, "v4.10")

    assert any("[N8]:" in line for _, _, line in findings)


def test_surviving_tracker_row_fails(tmp_path: Path) -> None:
    write(tmp_path, "docs/todos.md", "| v4.10.0 implementation tasks | 0 | 26 | 26 |\n")

    assert find_residual_references(tmp_path, "v4.10.0") != []


def test_bare_section_number_is_not_a_version(tmp_path: Path) -> None:
    # "#### 4.10 - Publication and integration" is a Phase 4 subsection heading.
    # A 4.10 -> 4.12 substitution corrupts it. Only v-prefixed forms count.
    write(
        tmp_path,
        "docs/plan.md",
        "#### 4.10 - Publication and integration\n\n"
        "Record the remaining proof as owned by 4.10 rather than ticking it here.\n",
    )

    assert find_residual_references(tmp_path, "v4.10") == []
    assert main(["--root", str(tmp_path), "--check-residual", "v4.10"]) == 0


def test_historical_claim_with_a_dated_note_is_accepted(tmp_path: Path) -> None:
    # The correct repair for a dated statement is a note, never a restatement.
    write(
        tmp_path,
        "docs/comparison.md",
        "The user confirmed v4.10.0 as the adoption target on 2026-09-09. "
        "It was renumbered to v4.11.0 on 2026-09-10.\n",
    )

    assert find_residual_references(tmp_path, "v4.10.0") == []


def test_historical_claim_without_a_note_still_fails(tmp_path: Path) -> None:
    # The exemption is earned by the note, not by the line being old.
    write(
        tmp_path,
        "docs/comparison.md",
        "The user confirmed v4.10.0 as the adoption target on 2026-09-09.\n",
    )

    assert find_residual_references(tmp_path, "v4.10.0") != []


def test_longer_version_is_not_a_false_positive(tmp_path: Path) -> None:
    write(tmp_path, "docs/d.md", "v4.100 is a different thing\n")

    assert find_residual_references(tmp_path, "v4.10") == []


def test_prefix_match_catches_the_patch_form(tmp_path: Path) -> None:
    # Checking the minor must catch references to its patch releases, because a
    # tree move renames the directory and every file under it.
    write(tmp_path, "docs/e.md", "the v4.10.0 adoption plan\n")

    assert find_residual_references(tmp_path, "v4.10") != []


def test_skip_prefixes_are_honoured(tmp_path: Path) -> None:
    write(tmp_path, "docs/archives/old.md", "v4.10.0 shipped\n")

    assert find_residual_references(tmp_path, "v4.10.0") != []
    assert find_residual_references(tmp_path, "v4.10.0", skip=("docs/archives/",)) == []


def test_dot_directories_are_ignored(tmp_path: Path) -> None:
    # Generated evidence under .nexus/ is not a reference that needs repairing.
    write(tmp_path, ".nexus/evidence/report.md", "v4.10.0 everywhere\n")

    assert find_residual_references(tmp_path, "v4.10.0") == []
