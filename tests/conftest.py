"""Repo-level pytest fixtures for the `tests/` tree.

Currently one job: make `bash` resolvable on Windows, for the same reason and by
the same mechanism as `catalog/hooks/tests/conftest.py` (v3.15.6 Phase 4 / DF-2).

Why this is duplicated rather than shared: `catalog/hooks/tests/` and `tests/` are
deliberately SEPARATE pytest roots. `.github/workflows/ci.yml` runs them as
distinct invocations and documents why (a single invocation makes pytest adopt a
nested `pyproject.toml` as rootdir and breaks module discovery). A module importable
from both would have to live outside both roots and be put on `sys.path` by each
conftest anyway, which is more machinery than the ~20 lines it would save. Keep the
two copies in step.

The problem: on Windows, `shutil.which("bash")` commonly resolves to
`C:\\Windows\\System32\\bash.exe`, the WSL launcher stub. Handed a Windows-style
script path it cannot resolve, that stub exits 127 before running a line, so every
bash-invoking test fails for an environmental reason that looks like a real failure.
`tests/validators/test_session_query_extract.py` and
`tests/installer/test_branch_flag.py` are the affected files here.

The fix: prepend a bash that can actually execute a script, at import time, before
pytest imports any test module. No-op on POSIX hosts and on any Windows host whose
PATH already puts Git Bash ahead of the stub.
"""
from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent

# Any hook that exits 0 on empty stdin works as an interpreter probe.
_PROBE_SCRIPT = REPO_ROOT / "catalog" / "hooks" / "escalation-trigger.sh"

_GIT_BASH_CANDIDATES = (
    r"C:\Program Files\Git\bin\bash.exe",
    r"C:\Program Files (x86)\Git\bin\bash.exe",
    r"C:\Program Files\Git\usr\bin\bash.exe",
)


def _can_run_script(interpreter: str, script: Path) -> bool:
    """True when `interpreter script` executes rather than failing to resolve it."""
    if not script.is_file():
        return False
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


def _repair_bash_on_path() -> str | None:
    """Prepend a working bash to PATH when the one already there cannot run a script."""
    on_path = shutil.which("bash")
    if on_path and _can_run_script(on_path, _PROBE_SCRIPT):
        return None

    for candidate in _GIT_BASH_CANDIDATES:
        path = Path(candidate)
        if not path.is_file() or not _can_run_script(candidate, _PROBE_SCRIPT):
            continue
        bin_dir = str(path.parent)
        os.environ["PATH"] = bin_dir + os.pathsep + os.environ.get("PATH", "")
        return bin_dir
    return None


# Executed at collection time, before any test module is imported.
BASH_PATH_REPAIRED_WITH = _repair_bash_on_path()


@pytest.fixture
def render_gate():
    """Turn a browser-dependent test's runtime skip into a FAILURE when the
    environment promised a browser (v3.16.5 Phase 3).

    The problem this solves: three browser-dependent checks in `tests/skills/`
    skipped silently for four minor versions (v3.15 known-gap MT-1), because a
    skip on a missing browser is correct locally and indistinguishable from a
    pass in aggregate output. A job that deliberately INSTALLED a browser and
    then skipped the checks anyway told nobody.

    Local behavior is unchanged - skip-with-note, never a hard fail on a missing
    browser. A caller that guarantees a browser sets `NEXUS_REQUIRE_RENDER=1`
    (the CI render job does), and then the same condition fails loudly instead.

    Usage: take `render_gate` as a parameter and call it in place of
    `pytest.skip(reason)`.
    """
    def gate(reason: str):
        if os.environ.get("NEXUS_REQUIRE_RENDER") == "1":
            pytest.fail(
                f"NEXUS_REQUIRE_RENDER=1 promised a headless browser, but {reason}"
            )
        pytest.skip(reason)

    return gate


def pytest_configure(config):
    """Register the `slow` marker (v3.16.1 Phase 6.5).

    The install-selection parity suite ends with two end-to-end tests that run a
    real installer into a temp dir; each takes minutes. They are marked `slow` so
    a routine `pytest tests/installer` can deselect them with `-m "not slow"`
    while CI still runs the full set. Registered here rather than in a new root
    pytest.ini, because this repo deliberately runs several separate pytest roots
    and a root config would apply to invocations that never asked for it.
    """
    config.addinivalue_line(
        "markers", "slow: end-to-end test that runs a real installer (minutes, not seconds)"
    )
