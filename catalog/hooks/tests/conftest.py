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
"""
from __future__ import annotations

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
    for name in ("pwsh", "powershell"):
        found = shutil.which(name)
        if found:
            return found
    return None


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
