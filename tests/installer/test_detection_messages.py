"""Both installers print the same NOT DETECTED evidence and remedy (v4.14.7 Phase 4).

The runner's install summary carries, for a platform `detect_platform` did not
find, an `evidence` string and a one-line `remedy`. The bash installer reads it
in `render_platform_from_summary`; the PowerShell installer in
`Resolve-UndetectedReason`. Each harness extracts only those functions and the
undetected-group helpers from the real installer, feeds them one shared summary,
and the printed group must match line for line. A second case pins that
`--forced <key>` is passed to the runner only when `--platforms` was explicit.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
INSTALLER_SH = REPO_ROOT / "scripts" / "installer.sh"
INSTALLER_PS1 = REPO_ROOT / "scripts" / "installer.ps1"
BASH = shutil.which("bash")


def _resolve_powershell() -> str | None:
    pinned = os.environ.get("NEXUS_TEST_POWERSHELL")
    if pinned:
        return shutil.which(pinned)
    for name in ("pwsh", "powershell"):
        found = shutil.which(name)
        if found:
            return found
    return None


PWSH = _resolve_powershell()
_DECODE = {"encoding": "utf-8", "errors": "replace"}
_NO_WINDOW = {"creationflags": getattr(subprocess, "CREATE_NO_WINDOW", 0), "stdin": subprocess.DEVNULL}

SUMMARY = {
    "scope": "global",
    "platforms": [
        {
            "platform": "qwen",
            "display_name": "Qwen Code",
            "detected": False,
            "evidence": "qwen not on PATH; ~/.qwen holds only Nexus-Hub files",
            "remedy": "Install Qwen Code, then run `nexus-hub upgrade`, or name it with --platforms qwen.",
            "surfaces": {},
            "notes": ["Qwen Code not detected (...); global QWEN.md + skills skipped"],
        },
        {
            "platform": "windsurf",
            "display_name": "Devin Desktop",
            "detected": False,
            "surfaces": {},
            "notes": ["Devin Desktop (~/.codeium) not found"],
        },
    ],
}

_SH_HARNESS = r"""
set -euo pipefail
installer="$1"; summary="$2"; py="$3"
GRAY=""; GREEN=""; YELLOW=""; RESET=""
write_item() { printf '%s\n' "$1"; }
extract() { sed -n "/^$1() {/,/^}/p" "$installer"; }
UNDETECTED_PLATFORMS=(); UNDETECTED_REMEDIES=()
for fn in reset_undetected_platforms add_undetected_platform write_undetected_group render_platform_from_summary; do
    eval "$(extract "$fn")"
done
reset_undetected_platforms
render_platform_from_summary "$summary" qwen QWEN "Qwen Code" "$py"
render_platform_from_summary "$summary" windsurf WINDSURF "Devin Desktop" "$py"
write_undetected_group
"""

_PS_HARNESS = r"""
$ErrorActionPreference = 'Stop'
$installer = $args[0]; $summaryPath = $args[1]
$ast = [System.Management.Automation.Language.Parser]::ParseFile($installer, [ref]$null, [ref]$null)
foreach ($name in @('Reset-UndetectedPlatforms', 'Add-UndetectedPlatform', 'Write-UndetectedGroup', 'Resolve-UndetectedReason')) {
    $fn = $ast.Find({ param($n) $n -is [System.Management.Automation.Language.FunctionDefinitionAst] -and $n.Name -eq $name }, $true)
    if (-not $fn) { Write-Error "$name not found"; exit 3 }
    Invoke-Expression $fn.Extent.Text
}
$script:UndetectedPlatforms = @()
$summary = Get-Content $summaryPath -Raw | ConvertFrom-Json
foreach ($pair in @(@('qwen', 'Qwen Code'), @('windsurf', 'Devin Desktop'))) {
    $plat = $summary.platforms | Where-Object { $_.platform -eq $pair[0] } | Select-Object -First 1
    $u = Resolve-UndetectedReason -PlatformSummary $plat
    Add-UndetectedPlatform -Name $pair[1] -Reason $u.Reason -Remedy $u.Remedy
}
Write-UndetectedGroup
"""

EXPECTED = [
    "> NOT DETECTED (skipped)",
    "- Qwen Code (not detected: qwen not on PATH; ~/.qwen holds only Nexus-Hub files)",
    "Install Qwen Code, then run `nexus-hub upgrade`, or name it with --platforms qwen.",
    "- Devin Desktop (not detected)",
]


def _lines(output: str) -> list[str]:
    return [line.strip() for line in output.splitlines() if line.strip()]


@pytest.fixture
def summary_file(tmp_path: Path) -> Path:
    path = tmp_path / "summary.json"
    path.write_text(json.dumps(SUMMARY), encoding="utf-8")
    return path


@pytest.mark.skipif(not BASH, reason="needs bash")
def test_bash_installer_prints_evidence_and_remedy(tmp_path: Path, summary_file: Path) -> None:
    harness = tmp_path / "harness.sh"
    harness.write_text(_SH_HARNESS, encoding="utf-8", newline="\n")
    proc = subprocess.run(
        [BASH, str(harness), INSTALLER_SH.as_posix(), summary_file.as_posix(), Path(sys.executable).as_posix()],
        cwd=tmp_path, capture_output=True, text=True, timeout=120, check=False, **_DECODE, **_NO_WINDOW,
    )
    assert proc.returncode == 0, proc.stderr
    assert _lines(proc.stdout) == EXPECTED


@pytest.mark.skipif(not PWSH, reason="needs PowerShell")
def test_powershell_installer_prints_evidence_and_remedy(tmp_path: Path, summary_file: Path) -> None:
    harness = tmp_path / "harness.ps1"
    harness.write_text(_PS_HARNESS, encoding="utf-8")
    proc = subprocess.run(
        [PWSH, "-NoProfile", "-File", str(harness), str(INSTALLER_PS1), str(summary_file)],
        cwd=tmp_path, capture_output=True, text=True, timeout=120, check=False, **_DECODE, **_NO_WINDOW,
    )
    assert proc.returncode == 0, proc.stderr
    assert _lines(proc.stdout) == EXPECTED


def test_forced_is_passed_only_for_an_explicit_platform_list() -> None:
    """Both installers add `--forced <key>` on global runner calls, and only
    when the user gave --platforms / -Platforms."""
    bash = INSTALLER_SH.read_text(encoding="utf-8")
    assert re.search(
        r'if \[ "\$scope" = "global" \] && \[ -n "\$PLATFORMS_ARG" \]; then\s+args\+=\("--forced" "\$key"\)',
        bash,
    )
    ps = INSTALLER_PS1.read_text(encoding="utf-8")
    assert "$script:PlatformsExplicit = -not [string]::IsNullOrWhiteSpace($Platforms)" in ps
    assert re.search(
        r'if \(\$Scope -eq "global" -and \$script:PlatformsExplicit\) \{ \$argsList \+= @\("--forced", \$IntegrationKey\) \}',
        ps,
    )
