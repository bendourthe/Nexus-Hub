"""Optional MCP setup failures must leave the native core installer usable."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
pytestmark = pytest.mark.skipif(os.name != "nt", reason="Windows PowerShell 5.1 installer boundary")

HARNESS = r"""param($Installer, $Repo, $FixtureHome, $Backend, $Failure)
$ErrorActionPreference = 'Stop'
$env:USERPROFILE = $FixtureHome
$script:Calls = [System.Collections.Generic.List[string]]::new()
$script:Messages = [System.Collections.Generic.List[string]]::new()
function Write-Item { param($Message,$Color) $script:Messages.Add([string]$Message) }
function global:python {
    if ($args[0] -eq '--version') { $global:LASTEXITCODE = 0; return 'Python 3.11.15' }
    $script:Calls.Add('python ' + ($args -join ' '))
    if ($Failure -eq 'venv') { $global:LASTEXITCODE = 17; return }
    $scriptsDir = Join-Path $args[2] 'Scripts'
    New-Item -ItemType Directory -Force -Path $scriptsDir | Out-Null
    if ($Failure -eq 'pip-fail') {
        Copy-Item -LiteralPath (Join-Path $env:SystemRoot 'System32/where.exe') -Destination (Join-Path $scriptsDir 'pip.exe')
    }
    $global:LASTEXITCODE = 0
}
if ($Backend -eq 'uv') {
    function global:uv {
        $script:Calls.Add('uv ' + ($args -join ' '))
        if ($Failure -eq 'invoke-error') { throw 'Controlled optional tool invocation error' }
        if (($args[0] -eq 'venv' -and $Failure -eq 'venv') -or ($args[0] -eq 'pip' -and $Failure -eq 'pip-fail')) {
            $global:LASTEXITCODE = 19; return
        }
        $global:LASTEXITCODE = 0
    }
}
$tokens = $null; $parseErrors = $null
$ast = [System.Management.Automation.Language.Parser]::ParseFile($Installer, [ref]$tokens, [ref]$parseErrors)
if ($parseErrors.Count) { throw 'Installer parse failure' }
foreach ($functionName in @('Read-JsonDocument', 'Write-JsonFile', 'Install-SkillDiscovery')) {
    $functionAst = $ast.Find({param($node) $node -is [System.Management.Automation.Language.FunctionDefinitionAst] -and $node.Name -eq $functionName}, $true)
    if (-not $functionAst) { throw "Missing native helper: $functionName" }
    Invoke-Expression $functionAst.Extent.Text
}
$settings = Join-Path $FixtureHome '.claude/settings.json'
$before = [System.IO.File]::ReadAllBytes($settings)
Install-SkillDiscovery -RepoRoot $Repo
$after = [System.IO.File]::ReadAllBytes($settings)
$unchanged = [Convert]::ToBase64String($before) -eq [Convert]::ToBase64String($after)
try { $payload = Read-JsonDocument $settings } catch { $payload = $null }
$servers = $payload -is [Collections.IDictionary] -and $payload['mcpServers'] -is [Collections.IDictionary] -and @($payload['mcpServers'].GetEnumerator() | Where-Object { $_.Key -ceq 'nexus-skill-server' }).Count -gt 0
$result = @{ continued = $true; unchanged = $unchanged; servers = $servers; messages = @($script:Messages); calls = @($script:Calls) }
Write-Output ('PROBE_JSON=' + ($result | ConvertTo-Json -Depth 8 -Compress))
"""


def _exercise_setup(
    tmp_path: Path, backend: str, failure: str, raw: str
) -> tuple[dict[str, object], Path]:
    """Exercise actual native setup, parsing and writing inside a disposable profile."""
    home = tmp_path / "home"
    settings = home / ".claude/settings.json"
    settings.parent.mkdir(parents=True)
    settings.write_text(raw, encoding="utf-8")
    repo = tmp_path / "source"
    package = repo / "extensions/nexus-skill-server"
    package.mkdir(parents=True)
    (package / "pyproject.toml").write_text('[project]\nname="fixture"\n', encoding="utf-8")
    script = tmp_path / "probe.ps1"
    script.write_text(HARNESS, encoding="utf-8-sig")
    powershell = Path(shutil.which(os.environ.get("NEXUS_TEST_POWERSHELL", "powershell")) or (Path(os.environ["SYSTEMROOT"]) / "System32/WindowsPowerShell/v1.0/powershell.exe"))
    env = dict(os.environ)
    env["PATH"] = str(powershell.parent) + os.pathsep + str(Path(os.environ["SYSTEMROOT"]) / "System32")
    result = subprocess.run(
        [str(powershell), "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass",
         "-File", str(script), str(ROOT / "scripts/installer.ps1"), str(repo), str(home), backend, failure],
        env=env, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=60, check=False,
    )
    assert result.returncode == 0, result.stderr
    lines = [line.removeprefix("PROBE_JSON=") for line in result.stdout.splitlines() if line.startswith("PROBE_JSON=")]
    assert len(lines) == 1, result.stdout
    observed = json.loads(lines[0])
    assert observed["continued"]
    return observed, settings


@pytest.mark.parametrize(
    ("backend", "failure"),
    [("uv", "venv"), ("uv", "pip-fail"), ("python", "venv"),
     ("python", "pip-missing"), ("python", "pip-fail"), ("uv", "invoke-error"), ("uv", "success")],
)
def test_optional_mcp_setup_failure_is_nonfatal(
    tmp_path: Path, backend: str, failure: str
) -> None:
    """Dependency failures preserve all settings and never register dead servers."""
    observed, _ = _exercise_setup(tmp_path, backend, failure, '{"custom":{"keep":"user"}}')
    if failure == "success":
        assert observed["servers"]
        assert not observed["unchanged"]
    else:
        assert observed["unchanged"], observed
        assert not observed["servers"]
        assert any("skipping the local MCP servers" in message for message in observed["messages"])
        if failure == "venv" and backend == "uv":
            assert not any(call.startswith("uv pip") for call in observed["calls"])


@pytest.mark.parametrize(
    ("raw", "registered"),
    [
        ('{"env":{"VAR":"one","var":"two"},"custom":{"keep":true}}', True),
        ('{"env":{"claude_code_subagent_model":"user","CLAUDE_CODE_SUBAGENT_MODEL":"sonnet"}}', True),
        ('{"mcpServers":{"user-server":{"command":"keep"}}}', True),
        ('{"custom":{"offset":"2030-01-02T03:04:05+05:30","fraction":"2030-01-02T03:04:05.120Z"}}', True),
        ('{"mcpServers":{"user-server":{"command":"keep","args":["2030-01-02T03:04:05+05:30"],"env":{"STAMP":"2030-01-02T03:04:05.120Z"}}}}', True),
        ('[{"custom":{"keep":true}}]', False),
        ('{"broken":', False),
        ('{"mcpServers":null,"custom":"keep"}', False),
        ('{"mcpServers":[],"custom":"keep"}', False),
        ('{"mcpServers":"user","custom":"keep"}', False),
    ],
)
def test_mcp_registration_preserves_user_json_or_refuses_the_write(
    tmp_path: Path, raw: str, registered: bool
) -> None:
    """Successful dependency setup must not turn a parse failure into data loss."""
    observed, settings = _exercise_setup(tmp_path, "uv", "success", raw)
    assert observed["servers"] is registered
    if not registered:
        assert observed["unchanged"]
        assert any("preserving" in message for message in observed["messages"])
        assert not any("MCP servers registered" in message for message in observed["messages"])
        return
    before = json.loads(raw)
    after = json.loads(settings.read_text(encoding="utf-8-sig"))
    for key, value in before.items():
        if key == "mcpServers":
            for server, entry in value.items():
                assert after[key][server] == entry
        else:
            assert after[key] == value
    assert len(after["mcpServers"]) >= 4
