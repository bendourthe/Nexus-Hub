"""Tests for scripts/check_docs_conventions.py (v3.19.2 Phase 2)."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

# v4.0.0: `ci.yml` calls scripts/ci/run.py rather than naming each guard in its
# own `run:` step, so CI reachability is resolved through the profile
# definitions. See tests/validators/_ci_reachability.py for why greping the
# YAML would be both wrong and dangerous to "fix".
from tests.validators._ci_reachability import assert_wired_into_ci

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "scripts" / "check_docs_conventions.py"
MAKEFILE = REPO_ROOT / "Makefile"
CI = REPO_ROOT / ".github" / "workflows" / "ci.yml"


def run(root: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), "--root", str(root)],
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )


def test_clean_tree_passes(tmp_path: Path) -> None:
    docs = tmp_path / "docs" / "guide"
    docs.mkdir(parents=True)
    (docs / "intro.md").write_text("[next](next.md)\n", encoding="utf-8")
    (docs / "next.md").write_text("# next\n", encoding="utf-8")
    proc = run(tmp_path)
    assert proc.returncode == 0, proc.stderr


def test_wrong_case_relative_link_fails(tmp_path: Path) -> None:
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "Page.md").write_text("# Page\n", encoding="utf-8")
    (docs / "index.md").write_text("[p](page.md)\n", encoding="utf-8")
    proc = run(tmp_path)
    assert proc.returncode == 1
    assert "case-mismatch" in proc.stderr
    assert "page.md" in proc.stderr


def test_missing_relative_link_fails(tmp_path: Path) -> None:
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "index.md").write_text("[gone](no-such.md)\n", encoding="utf-8")
    proc = run(tmp_path)
    assert proc.returncode == 1
    assert "missing relative target" in proc.stderr


def test_empty_directory_fails(tmp_path: Path) -> None:
    (tmp_path / "docs" / "empty").mkdir(parents=True)
    (tmp_path / "docs" / "ok.md").write_text("# ok\n", encoding="utf-8")
    proc = run(tmp_path)
    assert proc.returncode == 1
    assert "empty directory" in proc.stderr


def test_non_kebab_directory_fails(tmp_path: Path) -> None:
    bad = tmp_path / "docs" / "Not_Kebab"
    bad.mkdir(parents=True)
    (bad / "x.md").write_text("# x\n", encoding="utf-8")
    proc = run(tmp_path)
    assert proc.returncode == 1
    assert "kebab-case" in proc.stderr


def test_http_links_are_ignored(tmp_path: Path) -> None:
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "index.md").write_text("[ext](https://example.invalid/x)\n", encoding="utf-8")
    proc = run(tmp_path)
    assert proc.returncode == 0, proc.stderr


def test_historical_version_trees_are_not_scanned(tmp_path: Path) -> None:
    old = tmp_path / "docs" / "v3" / "v3.18"
    old.mkdir(parents=True)
    (old / "broken.md").write_text("[gone](no-such.md)\n", encoding="utf-8")
    current = tmp_path / "docs" / "v3" / "v3.20"
    current.mkdir(parents=True)
    (current / "ok.md").write_text("# ok\n", encoding="utf-8")
    proc = run(tmp_path)
    assert proc.returncode == 0, proc.stderr
    assert "v3.20" in proc.stdout


def test_newest_minor_is_scanned_not_a_pinned_path(tmp_path: Path) -> None:
    older = tmp_path / "docs" / "v3" / "v3.19"
    older.mkdir(parents=True)
    (older / "ok.md").write_text("# ok\n", encoding="utf-8")
    newest = tmp_path / "docs" / "v3" / "v3.20"
    newest.mkdir(parents=True)
    (newest / "broken.md").write_text("[gone](no-such.md)\n", encoding="utf-8")
    proc = run(tmp_path)
    assert proc.returncode == 1
    assert "missing relative target" in proc.stderr


def test_canonical_minor_beats_a_future_major(tmp_path: Path) -> None:
    """docs/v4 must not steal the scan while plugin.json still says 3.20.x."""
    plugin = tmp_path / ".claude-plugin"
    plugin.mkdir()
    (plugin / "plugin.json").write_text('{"version": "3.20.2"}\n', encoding="utf-8")
    future = tmp_path / "docs" / "v4" / "v4.1"
    future.mkdir(parents=True)
    (future / "ok.md").write_text("# ok\n", encoding="utf-8")
    current = tmp_path / "docs" / "v3" / "v3.20"
    current.mkdir(parents=True)
    (current / "broken.md").write_text("[gone](no-such.md)\n", encoding="utf-8")
    proc = run(tmp_path)
    assert proc.returncode == 1
    assert "missing relative target" in proc.stderr


def test_future_major_broken_links_do_not_fail_the_canonical_minor(tmp_path: Path) -> None:
    plugin = tmp_path / ".claude-plugin"
    plugin.mkdir()
    (plugin / "plugin.json").write_text('{"version": "3.20.2"}\n', encoding="utf-8")
    future = tmp_path / "docs" / "v4" / "v4.1"
    future.mkdir(parents=True)
    (future / "broken.md").write_text("[gone](no-such.md)\n", encoding="utf-8")
    current = tmp_path / "docs" / "v3" / "v3.20"
    current.mkdir(parents=True)
    (current / "ok.md").write_text("# ok\n", encoding="utf-8")
    proc = run(tmp_path)
    assert proc.returncode == 0, proc.stderr
    assert "v3.20" in proc.stdout


def test_archive_trees_are_not_scanned(tmp_path: Path) -> None:
    archive = tmp_path / "docs" / "archive" / "old"
    archive.mkdir(parents=True)
    (archive / "broken.md").write_text("[gone](no-such.md)\n", encoding="utf-8")
    (tmp_path / "docs" / "ok.md").write_text("# ok\n", encoding="utf-8")
    proc = run(tmp_path)
    assert proc.returncode == 0, proc.stderr


def test_missing_root_fails(tmp_path: Path) -> None:
    proc = run(tmp_path / "no-such")
    assert proc.returncode == 1
    assert "MISS" in proc.stderr


def test_makefile_and_ci_invoke_the_guard() -> None:
    makefile = MAKEFILE.read_text(encoding="utf-8")
    assert "scripts/check_docs_conventions.py" in makefile
    assert_wired_into_ci("check_docs_conventions.py")
