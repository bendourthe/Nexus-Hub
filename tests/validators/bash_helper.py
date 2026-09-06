"""Locate a bash that actually works, for suites that execute shell scripts.

Kept out of conftest.py deliberately: `from conftest import ...` resolves to
tests/conftest.py, which shadows this directory's own conftest, so a module-level
constant has to live somewhere unambiguous.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path


def resolve_bash() -> str | None:
    """Return a bash that actually runs a script, or None.

    On Windows, the System32 bash.exe is the WSL launcher stub. It
    precedes Git Bash on PATH, so a bare `shutil.which("bash")` finds it first,
    and with no WSL distribution installed it prints a UTF-16
    "no installed distributions ... to install" message and exits 1. A test that
    assumes `which("bash")` is a POSIX shell therefore fails on a GitHub Windows
    runner while passing locally and on ubuntu.

    This is the same PATH shadowing v3.15.6 Phase 4 identified for the installer
    (see the `bootstrap` job comment in .github/workflows/ci.yml); it is a
    property of the host, not of the script under test.

    Candidates are probed EMPIRICALLY -- each is asked to echo a token -- rather
    than filtered by path, so a stub is excluded because it does not work rather
    than because its location was guessed.
    """
    candidates: list[str] = []
    found = shutil.which("bash")
    if found:
        candidates.append(found)
    if sys.platform == "win32":
        git = shutil.which("git")
        if git:
            candidates.append(
                str(Path(git).resolve().parent.parent / "bin" / "bash.exe")
            )
        candidates += [
            r"C:\Program Files\Git\bin\bash.exe",
            r"C:\Program Files (x86)\Git\bin\bash.exe",
        ]
    for candidate in candidates:
        if not candidate or not Path(candidate).exists():
            continue
        try:
            proc = subprocess.run(
                [candidate, "-c", "printf ok"],
                capture_output=True,
                text=True,
                check=False,
                timeout=30,
            )
        except (OSError, subprocess.SubprocessError):
            continue
        if proc.returncode == 0 and proc.stdout.strip() == "ok":
            return candidate
    return None


BASH = resolve_bash()
