"""Tests for scripts/check_docs_retention.py (v3.18.0 Phase 4).

The checker reports per-version `development/history/` subtrees that are two or
more minors behind the current version and not yet archived. Only `history/` ages
out: the v3.18.0 Phase 5 archive pass found that `development/` also holds CI
fixtures a workflow executes and contract documents shipped hooks cite by path.

Two properties carry the weight here. It must **always exit 0**, on every path
including an absent tree and an unreadable version directory, because it is wired
into `make validate` and a non-zero exit would turn an advisory report into a
release blocker. And it must be **silent about versions inside the threshold**,
because a checker that warns about the current release is noise that gets muted,
and a muted checker reports nothing at all.

Run from the repo root:
    python -m pytest tests/validators/test_check_docs_retention.py -v
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

_SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "check_docs_retention.py"


def _run(root: Path, *extra: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(_SCRIPT), "--root", str(root), *extra],
        capture_output=True,
        text=True,
        timeout=120,
    )


def _make_repo(tmp_path: Path, version: str, minors: list[str]) -> Path:
    """A fixture repo with a canonical version and one development/ tree per minor."""
    root = tmp_path / "repo"
    plugin = root / ".claude-plugin"
    plugin.mkdir(parents=True)
    (plugin / "plugin.json").write_text(
        json.dumps({"name": "fixture", "version": version}), encoding="utf-8"
    )
    for minor in minors:
        major = minor.split(".")[0]
        history = root / "docs" / major / minor / "development" / "history"
        history.mkdir(parents=True)
        (history / "note.md").write_text("# note\n", encoding="utf-8")
    return root


def test_old_version_is_reported(tmp_path: Path) -> None:
    root = _make_repo(tmp_path, "3.17.6", ["v3.15"])

    proc = _run(root)

    assert proc.returncode == 0, proc.stderr
    assert "WARN" in proc.stdout, proc.stdout
    assert "docs/v3/v3.15/development/history" in proc.stdout
    assert "docs/archive/v3/v3.15/development/history/" in proc.stdout, (
        "the report must name the exact destination, or the reader has to derive it"
    )


def test_current_and_previous_minor_are_silent(tmp_path: Path) -> None:
    """One minor behind is inside the threshold; the previous release is still hot."""
    root = _make_repo(tmp_path, "3.17.6", ["v3.17", "v3.16"])

    proc = _run(root)

    assert proc.returncode == 0, proc.stderr
    assert "WARN" not in proc.stdout, proc.stdout
    assert "nothing due for archival" in proc.stdout


def test_threshold_boundary_is_exactly_two_minors(tmp_path: Path) -> None:
    """v3.15 is two behind v3.17 and reported; v3.16 is one behind and is not."""
    root = _make_repo(tmp_path, "3.17.6", ["v3.15", "v3.16"])

    proc = _run(root)

    assert "v3.15/development/history" in proc.stdout
    assert "v3.16/development/history" not in proc.stdout


def test_already_archived_version_is_not_reported(tmp_path: Path) -> None:
    """The report is about work outstanding, not about history that exists."""
    root = _make_repo(tmp_path, "3.17.6", ["v3.15"])
    (root / "docs" / "archive" / "v3" / "v3.15" / "development" / "history").mkdir(parents=True)

    proc = _run(root)

    assert proc.returncode == 0, proc.stderr
    assert "WARN" not in proc.stdout, proc.stdout


def test_older_major_is_reported_entirely(tmp_path: Path) -> None:
    """An earlier major is wholly historical; the two-minor distance does not apply."""
    root = _make_repo(tmp_path, "3.17.6", ["v2.4"])

    proc = _run(root)

    assert "docs/v2/v2.4/development/history" in proc.stdout
    assert "docs/archive/v2/v2.4/development/history/" in proc.stdout


def test_future_version_directory_is_not_reported(tmp_path: Path) -> None:
    """A v4 directory is planning, not history; archiving it would be nonsense."""
    root = _make_repo(tmp_path, "3.17.6", ["v4.0"])

    proc = _run(root)

    assert proc.returncode == 0, proc.stderr
    assert "WARN" not in proc.stdout, proc.stdout


def test_version_without_a_development_subtree_is_skipped(tmp_path: Path) -> None:
    """Only development/ ages out; plans/ and known-gaps.md never do."""
    root = _make_repo(tmp_path, "3.17.6", [])
    plans = root / "docs" / "v3" / "v3.10" / "plans"
    plans.mkdir(parents=True)
    (plans / "v3.10.0-thing.md").write_text("# plan\n", encoding="utf-8")
    (root / "docs" / "v3" / "v3.10" / "known-gaps.md").write_text("# gaps\n", encoding="utf-8")

    proc = _run(root)

    assert proc.returncode == 0, proc.stderr
    assert "WARN" not in proc.stdout, (
        "plans/ and known-gaps.md are exempt; only development/ is swept"
    )


def test_absent_docs_tree_exits_zero(tmp_path: Path) -> None:
    """A consuming project with no docs/ tree is not an error condition."""
    root = tmp_path / "bare"
    (root / ".claude-plugin").mkdir(parents=True)
    (root / ".claude-plugin" / "plugin.json").write_text(
        json.dumps({"version": "1.0.0"}), encoding="utf-8"
    )

    proc = _run(root)

    assert proc.returncode == 0, proc.stderr
    assert "no-op" in proc.stdout


def test_unreadable_canonical_version_exits_zero(tmp_path: Path) -> None:
    """Advisory means advisory: a missing version source degrades, never fails."""
    root = tmp_path / "noversion"
    (root / "docs" / "v3" / "v3.1" / "development").mkdir(parents=True)

    proc = _run(root)

    assert proc.returncode == 0, proc.stderr
    assert "skipped" in proc.stdout


def test_malformed_plugin_json_exits_zero(tmp_path: Path) -> None:
    root = tmp_path / "broken"
    (root / ".claude-plugin").mkdir(parents=True)
    (root / ".claude-plugin" / "plugin.json").write_text("{not json", encoding="utf-8")
    (root / "docs" / "v3" / "v3.1" / "development").mkdir(parents=True)

    proc = _run(root)

    assert proc.returncode == 0, proc.stderr


def test_quiet_suppresses_the_clean_line_but_not_warnings(tmp_path: Path) -> None:
    clean = _make_repo(tmp_path / "a", "3.17.6", ["v3.17"])
    dirty = _make_repo(tmp_path / "b", "3.17.6", ["v3.10"])

    assert _run(clean, "--quiet").stdout.strip() == ""
    assert "WARN" in _run(dirty, "--quiet").stdout


def test_nothing_is_moved_or_deleted(tmp_path: Path) -> None:
    """The checker is report-only. This is the property that makes it safe to run anywhere."""
    root = _make_repo(tmp_path, "3.17.6", ["v3.10"])
    before = sorted(p.relative_to(root).as_posix() for p in root.rglob("*"))

    _run(root)

    after = sorted(p.relative_to(root).as_posix() for p in root.rglob("*"))
    assert before == after, "the checker must never touch the filesystem"


@pytest.mark.parametrize("version", ["3.17.6", "3.17.6-rc1", "3.17"])
def test_version_parsing_tolerates_suffixes(tmp_path: Path, version: str) -> None:
    root = _make_repo(tmp_path / version.replace(".", "_"), version, ["v3.10"])

    proc = _run(root)

    assert proc.returncode == 0, proc.stderr
    assert "v3.10/development/history" in proc.stdout


def test_non_history_development_content_is_never_reported(tmp_path: Path) -> None:
    """The distinction the first archive pass forced.

    `development/` also holds CI fixtures a workflow executes and contract
    documents shipped hooks cite by path. A blanket rule would archive live
    inputs, so only `history/` ages out.
    """
    root = _make_repo(tmp_path, "3.17.6", [])
    for sub in ("fixtures", "worked-example"):
        d = root / "docs" / "v3" / "v3.12" / "development" / sub
        d.mkdir(parents=True)
        (d / "gen_fixtures.py").write_text("print('ci runs me')\n", encoding="utf-8")
    (root / "docs" / "v3" / "v3.12" / "development" / "a-contract.md").write_text(
        "# contract\n", encoding="utf-8"
    )

    proc = _run(root)

    assert proc.returncode == 0, proc.stderr
    assert "WARN" not in proc.stdout, (
        "only development/history/ ages out; fixtures, worked examples, and "
        "contract docs are live content"
    )
