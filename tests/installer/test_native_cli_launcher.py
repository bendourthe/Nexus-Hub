"""Exercise the real PowerShell launcher writer with literal profile paths."""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
POWERSHELL = shutil.which(os.environ.get("NEXUS_TEST_POWERSHELL", "powershell"))
pytestmark = pytest.mark.skipif(os.name != "nt" or not POWERSHELL, reason="native Windows launcher requires PowerShell and cmd")
HARNESS = r"""
param($Installer, $Repo)
$ErrorActionPreference = 'Stop'
$script:NexusHubVersion = '0.0.0'
$script:OverwriteMode = 'ALL'
function Write-CenteredBanner { param($Text) }
function Write-Item { param($Message, $Color, $Indent) Write-Output $Message }
$ast = [System.Management.Automation.Language.Parser]::ParseFile($Installer, [ref]$null, [ref]$null)
foreach ($name in @('Get-FileSha256', 'Safe-Copy', 'Install-CliLauncher')) {
    $definition = $ast.FindAll({ param($node) $node -is [System.Management.Automation.Language.FunctionDefinitionAst] -and $node.Name -eq $name }, $false) | Select-Object -First 1
    if (-not $definition) { throw "Missing function: $name" }
    Invoke-Expression $definition.Extent.Text
}
Install-CliLauncher -RepoRoot $Repo
Install-CliLauncher -RepoRoot $Repo
"""


@pytest.mark.parametrize("profile_name", ["ordinary", "home [user]", "home [user] $tick`semi; caf\u00e9 \u6f22\u5b57"])
def test_native_launcher_installs_and_runs_from_literal_profile_path(tmp_path: Path, profile_name: str) -> None:
    home = tmp_path / profile_name
    home.mkdir()
    nexus = home / ".nexus-hub"
    scripts = nexus / "scripts"
    scripts.mkdir(parents=True)
    shutil.copy2(ROOT / "scripts/nexus_hub_cli.py", scripts / "nexus_hub_cli.py")
    harness = tmp_path / "launcher.ps1"
    harness.write_text(HARNESS, encoding="utf-8-sig")
    env = dict(os.environ, HOME=str(home), USERPROFILE=str(home), NEXUS_HUB_HOME=str(nexus))
    env["PATH"] = os.pathsep.join([str(Path(sys.executable).parent), str(Path(env["SYSTEMROOT"]) / "System32")])
    result = subprocess.run([str(POWERSHELL), "-NoProfile", "-NonInteractive", "-File", str(harness), str(ROOT / "scripts/installer.ps1"), str(ROOT)], env=env, cwd=tmp_path, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=60, check=False)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "ERROR:" not in result.stdout
    assert (nexus / "VERSION").read_bytes() == b"0.0.0"
    launcher = nexus / "bin/nexus-hub.cmd"
    assert launcher.read_bytes() == (ROOT / "scripts/nexus-hub.cmd").read_bytes()
    version = subprocess.run(["cmd", "/d", "/c", str(launcher), "--version"], env=env, cwd=tmp_path, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=30, check=False)
    assert version.returncode == 0, version.stdout + version.stderr
    assert "nexus-hub 0.0.0" in version.stdout
