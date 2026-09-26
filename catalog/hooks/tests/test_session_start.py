"""Tests for the truthful, lean session-start banner (v4.13.3 Phase 2).

The banner states only facts read from real files: the version from
`${NEXUS_HOME:-$HOME/.nexus-hub}/VERSION` when it is one bounded semver line, the
full skill index path under the same home, and one git line. Values are asserted
against fixture files, never literals, and every assertion runs on both the `.sh`
and the `.ps1` implementation.
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

import pytest

HOOKS = Path(__file__).resolve().parents[1]
REMOVED = ("/search-skills", "/commands-cheatsheet", "skills,", "commands.", "v1.1.5", "Quick navigation")


@pytest.fixture(params=["sh", "ps1"])
def start(request, bash_bin: str, powershell_bin: str, tmp_path: Path):
    """Run session-start in a directory with a throwaway NEXUS_HOME."""
    home = tmp_path / "nexus-home"
    home.mkdir()
    work = tmp_path / "work"
    work.mkdir()

    def _run(version: bytes | None = None, cwd: Path | None = None) -> tuple[list[str], int]:
        if version is not None:
            (home / "VERSION").write_bytes(version)
        if request.param == "sh":
            argv = [bash_bin, str(HOOKS / "session-start.sh")]
        else:
            argv = [powershell_bin, "-NoProfile", "-File", str(HOOKS / "session-start.ps1")]
        env = {**os.environ, "NEXUS_HOME": home.as_posix(), "NEXUS_SESSION_DIGEST": "off"}
        env.pop("NEXUS_DISABLED_HOOKS", None)
        env.pop("NEXUS_HOOK_PROFILE", None)
        result = subprocess.run(argv, cwd=cwd or work, env=env, capture_output=True, text=True, timeout=120,
                                check=False)
        return [line.rstrip("\r") for line in result.stdout.splitlines()], result.returncode

    _run.home = home
    _run.impl = request.param
    return _run


def _index(home: Path) -> str:
    return f"full skill index: {home.as_posix()}/data/SKILL_INDEX.md"


def test_valid_version_and_index_path_come_from_the_same_home(start) -> None:
    lines, code = start(b"9.9.9\n")
    assert code == 0
    assert lines[0] == f"Nexus-Hub v9.9.9 active; {_index(start.home)}"


def test_prerelease_and_crlf_versions_are_accepted(start) -> None:
    assert start(b"4.13.3-rc.1\r\n")[0][0].startswith("Nexus-Hub v4.13.3-rc.1 active; ")


@pytest.mark.parametrize(
    "payload",
    [None, b"", b"9.9.9\nrm -rf /\n", b"1.2.3-" + b"a" * 40, b"not-a-version", b"9.9\n"],
    ids=["missing", "empty", "multi-line", "over-long", "not-semver", "two-part"],
)
def test_invalid_version_is_dropped_and_never_echoed(start, payload: bytes | None) -> None:
    if payload is None and (start.home / "VERSION").exists():
        (start.home / "VERSION").unlink()
    lines, code = start(payload)
    assert code == 0
    assert lines[0] == f"Nexus-Hub active; {_index(start.home)}"
    assert "rm -rf" not in "\n".join(lines)


def test_no_counts_or_removed_commands(start) -> None:
    lines, _ = start(b"9.9.9\n")
    text = "\n".join(lines)
    for removed in REMOVED:
        assert removed not in text, f"{start.impl} still prints {removed!r}"


def test_git_is_one_line_outside_a_repository(start) -> None:
    lines, _ = start(b"9.9.9\n")
    assert lines[1] == "Git: unavailable"
    assert len([line for line in lines if line.strip()]) == 2


def test_git_is_one_line_inside_a_repository(start, tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init", "-q", "-b", "main"], cwd=repo, check=True)
    (repo / "a.txt").write_text("a\n", encoding="utf-8")
    lines, _ = start(b"9.9.9\n", cwd=repo)
    assert lines[1] == "Git: main, 1 changed file(s)"
    assert not any("Recent commits" in line or line.startswith("  Branch:") for line in lines)
