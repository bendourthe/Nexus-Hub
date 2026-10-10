"""An aborted focused install must not leak its selection stage (AR-10).

A focused install (`-Modules` / `--modules`) builds a filtered copy of the
catalog in a temporary "selection stage" directory. Before v4.13.11 the
PowerShell installer removed that stage only on the normal completion path, so
any `exit` taken after `Resolve-Selection` (the "Workspace path not found"
check, observed during v3.16.1 testing) left a full copy of the selected skills
under %TEMP%. The fix wraps the post-selection flow in one try/finally.

These tests run the REAL installers with a selector and a missing workspace
path, which exits early after the stage exists, inside a fully isolated
environment: HOME, USERPROFILE, APPDATA, LOCALAPPDATA, NEXUS_HUB_HOME, the Git
global config, and the temporary directory all point into pytest's tmp_path,
so the run cannot touch the real user's home and the stage count is measured
in a directory nothing else writes to.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parents[2]
_SH = _ROOT / "scripts" / "installer.sh"
_PS1 = _ROOT / "scripts" / "installer.ps1"
_STAGE_PREFIXES = ("nexus-selection-", "tmp.")
_CAPTURE = {"capture_output": True, "text": True, "encoding": "utf-8", "errors": "replace"}


def _windows_powershell() -> str | None:
    """Windows PowerShell 5.1 specifically, the shell the AR-10 leak was seen on."""
    if sys.platform != "win32":
        return None
    return shutil.which("powershell")


@pytest.fixture
def short_temp():
    """A fresh, empty temporary directory with a SHORT path.

    The stage holds a full skill tree; under pytest's deep tmp_path a stage
    path can pass the Windows 260-character limit and fail for an unrelated
    reason. A fresh mkdtemp directory under the system temp root is just as
    isolated (nothing else writes to it) and keeps the paths short.
    """
    path = Path(tempfile.mkdtemp(prefix="nxs"))
    try:
        yield path
    finally:
        shutil.rmtree(path, ignore_errors=True)


def _isolated_env(tmp_path: Path, temp: Path) -> tuple[dict[str, str], Path]:
    profile = tmp_path / "profile"
    for d in (profile, tmp_path / "appdata", tmp_path / "localappdata"):
        d.mkdir()
    env = {
        **os.environ,
        "HOME": str(profile),
        "USERPROFILE": str(profile),
        "APPDATA": str(tmp_path / "appdata"),
        "LOCALAPPDATA": str(tmp_path / "localappdata"),
        "NEXUS_HUB_HOME": str(profile / ".nexus-hub"),
        "GIT_CONFIG_GLOBAL": str(profile / ".gitconfig"),
        "TEMP": str(temp),
        "TMP": str(temp),
        "TMPDIR": temp.as_posix(),
    }
    return env, temp


def _stages(temp: Path) -> list[str]:
    return sorted(p.name for p in temp.iterdir() if p.is_dir() and p.name.startswith(_STAGE_PREFIXES))


@pytest.mark.slow
@pytest.mark.skipif(_windows_powershell() is None, reason="Windows PowerShell 5.1 not available")
def test_powershell_early_exit_after_selection_removes_the_stage(tmp_path: Path, short_temp: Path) -> None:
    env, temp = _isolated_env(tmp_path, short_temp)
    before = _stages(temp)
    missing = tmp_path / "does-not-exist"

    proc = subprocess.run(
        [_windows_powershell(), "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(_PS1),
         "-Workspace", str(missing), "-Platforms", "claude", "-Modules", "ai-engineering", "-Yes"],
        cwd=str(_ROOT), env=env, timeout=600, **_CAPTURE,
    )

    output = (proc.stdout or "") + (proc.stderr or "")
    # Non-vacuity: the selection really was staged before the early exit.
    assert "Selection:" in output, f"the selector was not resolved, so no stage was built:\n{output[-3000:]}"
    assert "Workspace path not found" in output, f"expected the workspace early exit:\n{output[-3000:]}"
    assert proc.returncode == 2, f"expected exit 2, got {proc.returncode}"
    assert _stages(temp) == before, (
        f"the early exit leaked a selection stage into the isolated TEMP: {_stages(temp)}"
    )


@pytest.mark.slow
@pytest.mark.skipif(shutil.which("bash") is None, reason="bash not available")
def test_bash_early_exit_after_selection_removes_the_stage(tmp_path: Path, short_temp: Path) -> None:
    """Lockstep guard: Bash already cleans up through its EXIT trap."""
    env, temp = _isolated_env(tmp_path, short_temp)
    before = _stages(temp)
    missing = tmp_path / "does-not-exist"

    proc = subprocess.run(
        [shutil.which("bash"), str(_SH), "--workspace", missing.as_posix(),
         "--platforms", "claude", "--modules", "ai-engineering", "--yes"],
        cwd=str(_ROOT), env=env, timeout=600, **_CAPTURE,
    )

    output = (proc.stdout or "") + (proc.stderr or "")
    assert "Selection:" in output, f"the selector was not resolved, so no stage was built:\n{output[-3000:]}"
    assert "Workspace path not found" in output, f"expected the workspace early exit:\n{output[-3000:]}"
    assert proc.returncode == 2, f"expected exit 2, got {proc.returncode}"
    assert _stages(temp) == before, (
        f"the early exit leaked a selection stage into the isolated TMPDIR: {_stages(temp)}"
    )
