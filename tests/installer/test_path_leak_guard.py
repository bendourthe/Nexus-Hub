"""The installers must not persist a PATH entry for a sandboxed or test home.

The Windows user PATH (HKCU\\Environment\\Path) is shared by the whole account,
but the install root follows USERPROFILE. Test runs that redirected USERPROFILE
therefore wrote their temporary `.nexus-hub\\bin` into the real user PATH (81
entries, past the cmd.exe 8,191-character limit). These tests run the real
launcher function with the PATH writer replaced by a recorder, so nothing here
touches the registry or a real shell profile.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parents[2] / "scripts"
INSTALL_PS1 = SCRIPTS / "installer.ps1"
INSTALL_SH = SCRIPTS / "installer.sh"

_NO_WINDOW = {
    "creationflags": getattr(subprocess, "CREATE_NO_WINDOW", 0),
    "stdin": subprocess.DEVNULL,
}
_RUN_KW = dict(capture_output=True, text=True, encoding="utf-8", errors="replace")

_PS_HARNESS = r"""
$ErrorActionPreference = 'Stop'
$installer = $args[0]; $log = $args[1]; $nexusHomeRoot = $args[2]
$ast = [System.Management.Automation.Language.Parser]::ParseFile($installer, [ref]$null, [ref]$null)
$fn = $ast.Find({ param($n) $n -is [System.Management.Automation.Language.FunctionDefinitionAst] -and $n.Name -eq 'Install-CliLauncher' }, $true)
$text = $fn.Extent.Text
$anchor = 'Join-Path $env:USERPROFILE ".nexus-hub"'
if (([regex]::Matches($text, [regex]::Escape($anchor))).Count -ne 1) { throw 'anchor missing' }
$text = $text.Replace($anchor, 'Join-Path $nexusHomeRoot ".nexus-hub"')
function Write-CenteredBanner { param($Text) }
function Write-Item { param($Message, $Color) }
function Safe-Copy { param($Source, $Destination, $Confirm, $CustomMessage) }
function Add-NexusBinToUserPath { param($BinDir) Add-Content -LiteralPath $log -Value 'called'; return 'added' }
$script:NexusHubVersion = '0.0.0'
$NoModifyPath = $false
Invoke-Expression $text
Install-CliLauncher -RepoRoot $nexusHomeRoot
"""


def _powershell() -> str | None:
    return shutil.which("powershell") or shutil.which("pwsh")


def _run_ps(tmp_path: Path, env_overrides: dict[str, str | None]) -> bool:
    """Run Install-CliLauncher; return True when the PATH writer was called."""
    harness = tmp_path / "harness.ps1"
    harness.write_text(_PS_HARNESS, encoding="utf-8")
    log = tmp_path / "calls.log"
    home_root = tmp_path / "home"
    home_root.mkdir()
    env = {k: v for k, v in os.environ.items() if k != "NEXUS_HUB_NO_MODIFY_PATH"}
    for key, value in env_overrides.items():
        if value is None:
            env.pop(key, None)
        else:
            env[key] = value
    result = subprocess.run(
        [
            _powershell(),
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(harness),
            str(INSTALL_PS1),
            str(log),
            str(home_root),
        ],
        env=env,
        check=False,
        **_RUN_KW,
        **_NO_WINDOW,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    return log.exists()


needs_ps = pytest.mark.skipif(
    sys.platform != "win32" or _powershell() is None, reason="needs Windows PowerShell"
)


@needs_ps
def test_powershell_skips_path_write_for_a_sandboxed_profile(tmp_path: Path) -> None:
    sandbox = tmp_path / "sandbox profile"
    sandbox.mkdir()
    assert not _run_ps(tmp_path, {"USERPROFILE": str(sandbox)})


@needs_ps
def test_powershell_skips_path_write_when_the_env_opt_out_is_set(
    tmp_path: Path,
) -> None:
    assert not _run_ps(tmp_path, {"NEXUS_HUB_NO_MODIFY_PATH": "1"})


@needs_ps
def test_powershell_still_writes_path_for_the_real_profile(tmp_path: Path) -> None:
    # Positive control: with the real profile and no opt-out the writer runs, so
    # the two tests above cannot pass by never reaching the PATH logic.
    assert _run_ps(tmp_path, {})


_BASH_HARNESS = r"""
set -euo pipefail
installer="$1"; log="$2"
extract() { sed -n "/^$1() {/,/^}/p" "$installer"; }
eval "$(extract nexus_path_profile)"
eval "$(extract install_cli_launcher)"
write_section_banner() { :; }
write_item() { :; }
safe_copy() { :; }
add_nexus_bin_to_profile() { echo called >> "$log"; printf 'added\n'; }
NEXUS_HUB_VERSION=0.0.0
GREEN=; YELLOW=; CYAN=; GRAY=; RESET=
install_cli_launcher "$PWD"
"""


def _bash() -> str | None:
    found = shutil.which("bash")
    return found if found and "system32" not in found.lower() else None


def _run_bash(tmp_path: Path, opt_out: bool) -> bool:
    home = tmp_path / "home"
    (home / ".nexus-hub").mkdir(parents=True)
    log = tmp_path / "calls.log"
    env = {k: v for k, v in os.environ.items() if k != "NEXUS_HUB_NO_MODIFY_PATH"}
    env["HOME"] = home.as_posix()
    env["SHELL"] = "/bin/bash"
    if opt_out:
        env["NEXUS_HUB_NO_MODIFY_PATH"] = "1"
    result = subprocess.run(
        [
            _bash(),
            "-c",
            _BASH_HARNESS,
            "harness",
            INSTALL_SH.as_posix(),
            log.as_posix(),
        ],
        env=env,
        check=False,
        **_RUN_KW,
        **_NO_WINDOW,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    return log.exists()


needs_bash = pytest.mark.skipif(_bash() is None, reason="needs a real bash")


@needs_bash
def test_bash_skips_profile_edit_when_the_env_opt_out_is_set(tmp_path: Path) -> None:
    assert not _run_bash(tmp_path, opt_out=True)


@needs_bash
def test_bash_still_edits_the_profile_without_the_opt_out(tmp_path: Path) -> None:
    assert _run_bash(tmp_path, opt_out=False)


def test_test_roots_export_the_opt_out_and_guard_the_user_path() -> None:
    root = Path(__file__).resolve().parents[2]
    for rel in ("tests/conftest.py", "catalog/hooks/tests/conftest.py"):
        text = (root / rel).read_text(encoding="utf-8")
        assert 'os.environ["NEXUS_HUB_NO_MODIFY_PATH"] = "1"' in text, rel
        assert "_check_user_path(session)" in text, rel
