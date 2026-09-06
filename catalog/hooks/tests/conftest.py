"""Shared fixtures for the hook test suite.

Provides interpreter resolution for the shell hooks so the suite runs on Windows
as well as POSIX hosts.

Why this exists (v3.15.6 Phase 2): on Windows, `shutil.which("bash")` commonly
resolves to `C:\\Windows\\System32\\bash.exe`, the WSL launcher stub. That stub
receives a Windows-style script path (`C:\\repo\\catalog\\hooks\\x.sh`), cannot
resolve it, and exits 127 before running a single line. Every bash-invoking hook
test then fails for an environmental reason that looks like a real failure, which
is what the long-standing WN-v36-1 note recorded as "bash cannot be exercised on
the Windows dev host". The cause is PATH shadowing, not host incapability: Git
Bash resolves the same path correctly.

These fixtures probe each candidate interpreter by actually running a hook with
empty stdin (every hook in this catalog exits 0 on empty input) and return the
first one that works, so the suite is correct on any host and skips cleanly when
no usable interpreter exists.

Two layers, deliberately (v3.15.6 Phase 4 / DF-2):

  1. The `bash_bin` / `powershell_bin` fixtures, for tests that want the
     interpreter path explicitly.
  2. A module-level PATH repair, so the ~11 pre-existing test files that call
     `shutil.which("bash")` or `subprocess.run(["bash", ...])` directly are fixed
     WITHOUT being edited. pytest imports `conftest.py` before it imports any test
     module, so repairing `os.environ["PATH"]` here lands before those modules run
     their module-level `shutil.which("bash")`. This closes the whole class rather
     than converting each file, and it keeps working for test files added later.
     It is a no-op on POSIX hosts, where the bash already on PATH works.
"""
from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

import pytest

_HOOKS_DIR = Path(__file__).resolve().parent.parent

# A hook that exits 0 on empty stdin, used purely as an interpreter probe.
_PROBE_HOOK = _HOOKS_DIR / "escalation-trigger.sh"

# Windows Git Bash install locations, checked after whatever is on PATH.
_GIT_BASH_CANDIDATES = (
    r"C:\Program Files\Git\bin\bash.exe",
    r"C:\Program Files (x86)\Git\bin\bash.exe",
    r"C:\Program Files\Git\usr\bin\bash.exe",
)


def _can_run_script(interpreter: str, script: Path) -> bool:
    """True when `interpreter script` executes rather than failing to resolve it.

    A WSL stub handed a Windows path exits 127 ("No such file or directory")
    without executing the script, which this distinguishes from a real run.
    """
    try:
        proc = subprocess.run(
            [interpreter, str(script)],
            input="",
            text=True,
            capture_output=True,
            timeout=60,
        )
    except (OSError, subprocess.SubprocessError):
        return False
    return proc.returncode == 0


def _resolve_bash() -> str | None:
    candidates: list[str] = []
    on_path = shutil.which("bash")
    if on_path:
        candidates.append(on_path)
    candidates.extend(p for p in _GIT_BASH_CANDIDATES if Path(p).is_file())

    for candidate in candidates:
        if _can_run_script(candidate, _PROBE_HOOK):
            return candidate
    return None


def _resolve_powershell() -> str | None:
    """Resolve a PowerShell interpreter, honoring an explicit pin.

    NEXUS_TEST_POWERSHELL pins which interpreter the suite exercises. This matters
    because the two editions differ in ways that bite: the v3.15.6 Phase 3 ledger
    BOM defect (`Add-Content -Encoding utf8` emitting a UTF-8 BOM) reproduces on
    Windows PowerShell 5.1 and NOT on pwsh 7, so a suite that silently prefers 7
    passes while shipping a file that is broken for 5.1 users.

    CI uses the pin to cover both editions across two legs: the ubuntu leg takes
    the default (pwsh 7), and the windows leg pins `powershell` (5.1).
    """
    pinned = os.environ.get("NEXUS_TEST_POWERSHELL")
    if pinned:
        found = shutil.which(pinned)
        if found:
            return found
        # An explicit pin that cannot be resolved is a configuration error worth
        # surfacing, not something to silently paper over with the other edition.
        return None

    for name in ("pwsh", "powershell"):
        found = shutil.which(name)
        if found:
            return found
    return None


def _repair_bash_on_path() -> str | None:
    """Prepend a working bash to PATH when the one already there cannot run a script.

    Runs at import time (see the module docstring) so it precedes every test
    module's own `shutil.which("bash")`. Returns the directory prepended, or None
    when nothing needed changing.

    No-op when the bash on PATH already works, which is every POSIX host and any
    Windows host whose PATH puts Git Bash ahead of the WSL launcher stub.
    """
    on_path = shutil.which("bash")
    if on_path and _can_run_script(on_path, _PROBE_HOOK):
        return None

    for candidate in _GIT_BASH_CANDIDATES:
        path = Path(candidate)
        if not path.is_file():
            continue
        if not _can_run_script(candidate, _PROBE_HOOK):
            continue
        bin_dir = str(path.parent)
        os.environ["PATH"] = bin_dir + os.pathsep + os.environ.get("PATH", "")
        return bin_dir
    return None


# Executed at collection time, before any test module is imported.
BASH_PATH_REPAIRED_WITH = _repair_bash_on_path()


@pytest.fixture(scope="session")
def bash_bin() -> str:
    """Path to a bash that can execute a hook script, or skip the test."""
    resolved = _resolve_bash()
    if resolved is None:
        pytest.skip(
            "no bash able to execute a hook script "
            "(on Windows, install Git Bash or put it ahead of the WSL stub on PATH)"
        )
    return resolved


@pytest.fixture(scope="session")
def powershell_bin() -> str:
    """Path to a PowerShell interpreter, or skip the test."""
    resolved = _resolve_powershell()
    if resolved is None:
        pytest.skip("no PowerShell interpreter (pwsh/powershell) on PATH")
    return resolved
