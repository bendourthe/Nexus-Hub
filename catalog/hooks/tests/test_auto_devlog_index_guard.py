"""Tests for the index-format guard in catalog/hooks/auto-devlog.{sh,ps1} (v3.18.0 Phase 2).

`docs/DEVLOG.md` became a bounded per-release INDEX in v3.18.0: a header plus one
table row per release. This hook predates that and prepends a narrative entry above
the first `## [` heading. Against an index that write is silent corruption, so the
hook now detects the index table header and stands down.

The load-bearing assertion is the NEGATIVE one: against an index-format DEVLOG the
file must come back byte-identical. The positive case is equally necessary, because
a guard that fires on everything would quietly disable the hook for the consuming
projects that still keep a narrative DEVLOG, and that failure looks identical to
"the hook worked".

Every test runs against BOTH implementations via the `run` fixture, so the suite is
also the .sh/.ps1 parity check for this behavior.

Run from the repo root:
    python -m pytest catalog/hooks/tests/test_auto_devlog_index_guard.py -v
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

import pytest

_HOOKS_DIR = Path(__file__).resolve().parent.parent
_HOOK_SH = _HOOKS_DIR / "auto-devlog.sh"
_HOOK_PS1 = _HOOKS_DIR / "auto-devlog.ps1"

# The hook skips when DEVLOG.md was modified in the last 300 seconds (double-run
# guard). A file created by the test is modified *now*, so without backdating it
# every test would exit 0 for the wrong reason and assert nothing.
_DOUBLE_RUN_WINDOW = 300
_BACKDATE = _DOUBLE_RUN_WINDOW * 2

_INDEX_DEVLOG = """# Development Log

This is an **index**, not a log. One line per release, newest first.

| Date | Version | Summary | Plan | History | Gaps |
|---|---|---|---|---|---|
| 2026-08-20 | v3.17.6 | CI gate hygiene | - | - | - |
"""

_NARRATIVE_DEVLOG = """# Development Log

## [2020-01-01] - an old narrative entry

### What Changed

Something, a long time ago.
"""


def _git(repo: Path, *args: str) -> None:
    subprocess.run(
        ["git", *args],
        cwd=str(repo),
        check=True,
        capture_output=True,
        text=True,
        timeout=120,
    )


@pytest.fixture
def repo(tmp_path: Path):
    """A git repo with a docs/ directory and enough commits to trip the hook."""
    root = tmp_path / "proj"
    (root / "docs").mkdir(parents=True)
    _git(root.parent, "init", "-q", str(root))
    _git(root, "config", "user.email", "test@example.invalid")
    _git(root, "config", "user.name", "Test")
    # The hook needs at least AUTO_DEVLOG_MIN_COMMITS commits to consider writing.
    for i in range(3):
        marker = root / f"file{i}.txt"
        marker.write_text(f"content {i}\n", encoding="utf-8")
        _git(root, "add", "-A")
        _git(root, "commit", "-q", "-m", f"commit {i}")
    return root


def _write_devlog(repo: Path, body: str) -> Path:
    devlog = repo / "docs" / "DEVLOG.md"
    devlog.write_text(body, encoding="utf-8", newline="\n")
    stale = os.path.getmtime(devlog) - _BACKDATE
    os.utime(devlog, (stale, stale))
    return devlog


@pytest.fixture(params=["sh", "ps1"])
def run(request):
    """Invoke either implementation against a given repo."""
    if request.param == "sh":
        prefix = [request.getfixturevalue("bash_bin"), str(_HOOK_SH)]
    else:
        prefix = [
            request.getfixturevalue("powershell_bin"),
            "-NoProfile",
            "-File",
            str(_HOOK_PS1),
        ]

    def _run(repo: Path, opt_in: bool = True) -> subprocess.CompletedProcess:
        env = {**os.environ}
        if opt_in:
            env["AUTO_DEVLOG"] = "1"
        else:
            env.pop("AUTO_DEVLOG", None)
        # Never let the optional AI path run: it costs tokens and needs a CLI.
        env.pop("AUTO_DEVLOG_AI", None)
        for key in ("NEXUS_DISABLED_HOOKS", "NEXUS_HOOK_PROFILE"):
            env.pop(key, None)
        return subprocess.run(
            prefix,
            input="{}",
            text=True,
            capture_output=True,
            env=env,
            cwd=str(repo),
            timeout=180,
        )

    return _run


def test_index_format_devlog_is_left_untouched(run, repo: Path) -> None:
    """The guard's whole purpose: an index must come back byte-identical."""
    devlog = _write_devlog(repo, _INDEX_DEVLOG)
    before = devlog.read_bytes()

    proc = run(repo)

    assert proc.returncode == 0, (proc.stdout, proc.stderr)
    assert devlog.read_bytes() == before, "the hook wrote into a per-release index"


def test_index_format_devlog_explains_the_skip(run, repo: Path) -> None:
    """A silent skip is indistinguishable from a broken hook, so it must say why."""
    _write_devlog(repo, _INDEX_DEVLOG)

    proc = run(repo)

    combined = (proc.stdout + proc.stderr).lower()
    assert "index" in combined, combined
    assert "history" in combined, "the notice must point at where narrative belongs"


def test_narrative_devlog_still_receives_an_entry(run, repo: Path) -> None:
    """The guard must not fire on the legacy format it was not written for."""
    devlog = _write_devlog(repo, _NARRATIVE_DEVLOG)
    before = devlog.read_bytes()

    proc = run(repo)

    assert proc.returncode == 0, (proc.stdout, proc.stderr)
    assert devlog.read_bytes() != before, (
        "a narrative DEVLOG must still be appended to; a guard that fires on "
        "everything disables the hook while looking like it worked"
    )


def test_no_devlog_at_all_is_silent(run, repo: Path) -> None:
    """A project without a DEVLOG is not an error condition."""
    proc = run(repo)

    assert proc.returncode == 0, (proc.stdout, proc.stderr)
    assert not (repo / "docs" / "DEVLOG.md").exists(), "the hook must not create one"


def test_opt_in_gate_still_governs(run, repo: Path) -> None:
    """Without AUTO_DEVLOG=1 the hook does nothing, narrative or not.

    Guards the guard: if the opt-in check had regressed, the narrative test above
    would still pass and this hook would have become opt-out for every user.
    """
    devlog = _write_devlog(repo, _NARRATIVE_DEVLOG)
    before = devlog.read_bytes()

    proc = run(repo, opt_in=False)

    assert proc.returncode == 0, (proc.stdout, proc.stderr)
    assert devlog.read_bytes() == before, "the hook ran without being opted in"
