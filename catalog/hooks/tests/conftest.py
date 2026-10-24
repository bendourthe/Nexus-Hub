"""Shared fixtures for the hook test suite.

Provides portable shell-hook interpreters and private Git configuration for each test.

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


import runpy as _process_runpy
from pathlib import Path as _ProcessPath

# CREATE_NO_WINDOW is installed by the shared policy below.
_PROCESS_POLICY = _process_runpy.run_path(str(_ProcessPath(__file__).resolve().parents[3] / "scripts" / "nexus_process.py"))
CHILD_CONSOLES_HIDDEN = _PROCESS_POLICY["install_no_window_default"]()


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


# --------------------------------------------------------------------------- #
# Real-home write guard (v4.13.11, BG-2-v4131). Keep in step with the copy in
# tests/conftest.py.
#
# Twice a full-profile run rewrote files in the real user's ~/.nexus-hub because
# a test ran an installer with the inherited home. This guard snapshots the
# install targets a test must never touch, at session start and finish, and
# fails the session when any changed. It records (size, mtime) rather than a
# content hash on purpose: the observed leaks rewrote files with IDENTICAL bytes,
# which a hash comparison cannot see. Scope is limited to installer-owned paths,
# because live agent hooks legitimately write other parts of ~/.nexus-hub (for
# example state/usage-guard and cache/) while the suite runs. The home is read
# from the environment at import time, before any test redirects it.
# NEXUS_REAL_HOME_GUARD=0 disables it (for a run alongside a deliberate real
# install in another terminal).
# --------------------------------------------------------------------------- #

_GUARDED_NEXUS_PATHS = (
    "VERSION", "MANIFEST.sha256", "install-manifest.json", "permissions-manifest.json",
    "bin", "scripts", "hooks", "git-hooks", "style-guides", "templates",
    "state/backups", "state/locks", "state/legacy-candidates",
)
_GUARDED_HOME_FILES = (
    ".claude/CLAUDE.md", ".codex/AGENTS.md", ".gemini/GEMINI.md",
    ".config/opencode/AGENTS.md", ".qwen/QWEN.md", ".kimi-code/AGENTS.md",
)


def _real_home_targets() -> list[Path]:
    homes = {Path(v) for v in (os.environ.get("USERPROFILE"), os.environ.get("HOME")) if v}
    nexus_homes = {h / ".nexus-hub" for h in homes}
    if os.environ.get("NEXUS_HUB_HOME"):
        nexus_homes.add(Path(os.environ["NEXUS_HUB_HOME"]).expanduser())
    targets = [n / p for n in nexus_homes for p in _GUARDED_NEXUS_PATHS]
    targets += [h / f for h in homes for f in _GUARDED_HOME_FILES]
    return targets


_REAL_HOME_TARGETS = _real_home_targets()


def _snapshot_real_home() -> dict[str, tuple[int, int]]:
    snap: dict[str, tuple[int, int]] = {}
    for target in _REAL_HOME_TARGETS:
        paths = [target] if target.is_file() else (p for p in target.rglob("*") if p.is_file())
        for path in paths:
            try:
                st = path.stat()
            except OSError:
                continue
            snap[str(path)] = (st.st_size, st.st_mtime_ns)
    return snap


def _real_home_guard_enabled() -> bool:
    return os.environ.get("NEXUS_REAL_HOME_GUARD", "1") != "0"


def pytest_sessionstart(session):
    if _real_home_guard_enabled():
        session.config._nexus_real_home = _snapshot_real_home()


@pytest.hookimpl(tryfirst=True)
def pytest_sessionfinish(session, exitstatus):
    before = getattr(session.config, "_nexus_real_home", None)
    if before is None:
        return
    after = _snapshot_real_home()
    changed = sorted(k for k in before.keys() | after.keys() if before.get(k) != after.get(k))
    if not changed:
        return
    lines = [f"REAL HOME MODIFIED: {len(changed)} install-target file(s) changed during this run "
             "(a test wrote outside its temporary home; isolate HOME, USERPROFILE, APPDATA, "
             "LOCALAPPDATA and NEXUS_HUB_HOME):"]
    lines += [f"  {path}" for path in changed[:20]]
    reporter = session.config.pluginmanager.get_plugin("terminalreporter")
    for line in lines:
        if reporter is not None:
            reporter.write_line(line, red=True)
        else:
            print(line)
    session.exitstatus = pytest.ExitCode.TESTS_FAILED


@pytest.fixture(autouse=True)
def isolated_git_configuration(
    monkeypatch: pytest.MonkeyPatch, tmp_path_factory: pytest.TempPathFactory
) -> None:
    """Keep synthetic repositories independent of machine Git configuration."""
    config = tmp_path_factory.mktemp("git-config") / "config"
    config.write_text(
        "[user]\n    name = Test User\n    email = test@example.invalid\n"
        "[init]\n    defaultBranch = main\n",
        encoding="utf-8",
    )
    for key in tuple(os.environ):
        if key == "GIT_CONFIG" or key.startswith("GIT_CONFIG_"):
            monkeypatch.delenv(key, raising=False)
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", str(config))
    monkeypatch.setenv("GIT_CONFIG_NOSYSTEM", "1")
