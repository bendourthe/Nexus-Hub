"""Tests for scripts/generate_release_changelog.py.

Covers conventional-commit bump detection from a fixture commit set and the
Keep-a-Changelog section formatting, plus a CLI smoke through --commits-from.
"""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "scripts" / "generate_release_changelog.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("generate_release_changelog", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


g = _load_module()


def parse(*messages: str) -> list[dict]:
    return [g.parse_commit(m) for m in messages]


# --- bump detection ----------------------------------------------------------


def test_breaking_bang_is_major():
    commits = parse("feat(api)!: drop v1", "fix: small")
    assert g.determine_bump(commits) == "major"


def test_breaking_footer_is_major():
    commits = parse("refactor: rework\n\nBREAKING CHANGE: config moved")
    assert g.determine_bump(commits) == "major"


def test_feat_is_minor():
    commits = parse("feat: add thing", "docs: note it", "chore: deps")
    assert g.determine_bump(commits) == "minor"


def test_fix_only_is_patch():
    commits = parse("fix(auth): expiry", "perf: faster loop")
    assert g.determine_bump(commits) == "patch"


def test_perf_is_patch():
    assert g.determine_bump(parse("perf: tighten")) == "patch"


def test_non_release_types_yield_none():
    commits = parse("docs: tidy", "chore: bump", "style: format", "test: add")
    assert g.determine_bump(commits) is None


def test_non_conventional_commits_yield_none():
    commits = parse("Merge branch 'x'", "WIP random message")
    assert g.determine_bump(commits) is None


# --- version arithmetic ------------------------------------------------------


def test_bump_version_major():
    assert g.bump_version("1.2.3", "major") == "2.0.0"


def test_bump_version_minor():
    assert g.bump_version("1.2.3", "minor") == "1.3.0"


def test_bump_version_patch():
    assert g.bump_version("1.2.3", "patch") == "1.2.4"


def test_bump_version_tolerates_leading_v():
    assert g.bump_version("v2.4.0", "minor") == "2.5.0"


def test_bump_version_rejects_garbage():
    try:
        g.bump_version("not-a-version", "patch")
    except ValueError:
        return
    raise AssertionError("expected ValueError for a non-semver input")


# --- changelog formatting ----------------------------------------------------


def test_section_groups_and_bolds_scope():
    commits = parse("feat(api): add list", "fix(db): null guard")
    out = g.render_changelog_section("1.1.0", "2026-05-31", commits)
    assert "## [1.1.0] - 2026-05-31" in out
    assert "### Added" in out
    assert "- **api**: add list" in out
    assert "### Fixed" in out
    assert "- **db**: null guard" in out


def test_breaking_entry_is_flagged_and_in_changed():
    out = g.render_changelog_section("2.0.0", "2026-05-31", parse("feat!: drop legacy"))
    assert "### Changed" in out
    assert "**BREAKING**: drop legacy" in out


def test_security_keyword_routes_to_security_section():
    out = g.render_changelog_section("1.0.1", "2026-05-31", parse("fix: patch CVE-2026-9 in parser"))
    assert "### Security" in out
    assert "### Fixed" not in out


def test_empty_sections_are_omitted():
    out = g.render_changelog_section("1.1.0", "2026-05-31", parse("feat: only an addition"))
    assert "### Added" in out
    assert "### Changed" not in out
    assert "### Fixed" not in out


def test_no_conventional_commits_renders_placeholder():
    out = g.render_changelog_section("1.0.0", "2026-05-31", parse("just a note", "another note"))
    assert "_No conventional-commit changes since the last tag._" in out


# --- CLI smoke ---------------------------------------------------------------


def test_cli_reads_blank_line_fixture(tmp_path: Path):
    fixture = tmp_path / "commits.txt"
    fixture.write_text(
        "feat(ui): new panel\n\nfix: crash on resize\n\nchore: deps\n",
        encoding="utf-8",
    )
    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--commits-from",
            str(fixture),
            "--current-version",
            "3.1.4",
            "--date",
            "2026-05-31",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert "## [3.2.0] - 2026-05-31" in result.stdout  # feat -> minor
    assert "Proposed bump: minor -> 3.2.0" in result.stderr
    assert "- **ui**: new panel" in result.stdout
    assert "- crash on resize" in result.stdout


def test_cli_writes_out_file(tmp_path: Path):
    fixture = tmp_path / "commits.txt"
    fixture.write_text("fix: a patch\n", encoding="utf-8")
    out_file = tmp_path / "section.md"
    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--commits-from",
            str(fixture),
            "--current-version",
            "0.9.0",
            "--date",
            "2026-05-31",
            "--out",
            str(out_file),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert out_file.is_file()
    body = out_file.read_text(encoding="utf-8")
    assert "## [0.9.1] - 2026-05-31" in body  # fix -> patch
    assert "### Fixed" in body


def test_cli_missing_version_is_usage_error(tmp_path: Path):
    fixture = tmp_path / "commits.txt"
    fixture.write_text("feat: x\n", encoding="utf-8")
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--commits-from", str(fixture)],
        capture_output=True,
        text=True,
        check=False,
    )
    # No --current-version and no tag to derive from -> usage error.
    assert result.returncode == 2
    assert "current version" in result.stderr.lower()
