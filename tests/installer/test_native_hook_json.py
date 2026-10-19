"""Native Windows hook upgrades preserve unrelated exact-case JSON and custom hooks."""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parents[2]
_INSTALLER = _ROOT / "scripts/installer.ps1"
_POWERSHELL = shutil.which(os.environ.get("NEXUS_TEST_POWERSHELL", "pwsh")) or shutil.which("powershell")
pytestmark = pytest.mark.skipif(not _POWERSHELL, reason="no PowerShell interpreter")
_HARNESS = r"""param($Installer,$Repo,$Target,$Python,$Writer)
$ErrorActionPreference = 'Stop'
$script:ProbePython = $Python
$ast = [Management.Automation.Language.Parser]::ParseFile($Installer,[ref]$null,[ref]$null)
foreach($name in @('Read-JsonDocument','Write-JsonFile','Get-ManagedHookStem','Merge-ManagedClaudeHooks','Convert-ClaudeHookCommandsForWindows','Install-ClaudeHookFiles','Install-GitGuardrails','Install-UsageDisplay','Install-RequireDescription','Install-CoreSettings')) {
 $fn = $ast.FindAll({$args[0] -is [Management.Automation.Language.FunctionDefinitionAst] -and $args[0].Name -eq $name},$true) | Select-Object -First 1
 if(-not $fn) { throw "Missing native helper $name" }
 Invoke-Expression $fn.Extent.Text
}
function Safe-Copy { param($Source,$Destination,$Confirm,$CustomMessage) }
function Write-Item { param($Message,$Color) Write-Output $Message }
function Resolve-PythonExecutable { return $script:ProbePython }
if($Writer -eq 'upgrade') {
 Install-GitGuardrails -RepoRoot $Repo -TargetClaudeDir $Target -Scope Global
 Install-UsageDisplay -RepoRoot $Repo -TargetClaudeDir $Target -Scope Global
 Install-RequireDescription -RepoRoot $Repo -TargetClaudeDir $Target -Scope Global
 Install-CoreSettings -RepoRoot $Repo -TargetClaudeDir $Target -Scope Global
} else { & $Writer -RepoRoot $Repo -TargetClaudeDir $Target -Scope Global }
"""


def _invoke(script: Path, target: Path, writer: str) -> subprocess.CompletedProcess[str]:
    env = dict(os.environ, HOME=str(target.parent), USERPROFILE=str(target.parent), PYTHONDONTWRITEBYTECODE="1")
    result = subprocess.run([_POWERSHELL, "-NoProfile", "-NonInteractive", "-File", str(script), str(_INSTALLER), str(_ROOT), str(target), sys.executable, writer], env=env, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=90, check=False)
    assert result.returncode == 0, result.stdout + result.stderr
    return result


@pytest.mark.parametrize("writer", ["Install-GitGuardrails", "Install-UsageDisplay", "Install-RequireDescription", "upgrade"])
@pytest.mark.parametrize("case", ["distinct", "near", "metadata", "deep-bracket", "timestamps", "nested-metadata", "date-keys", "null-hooks"])
def test_hook_writers_preserve_user_document_and_install_native_commands(tmp_path: Path, writer: str, case: str) -> None:
    target = tmp_path / ("home [user]" if case == "deep-bracket" else "home") / ".claude"
    target.mkdir(parents=True)
    settings = target / "settings.json"
    user_hook = {"matcher": "Custom", "hooks": [{"type": "command", "command": "echo keep-user-hook"}]}
    payload = {"env": {"VAR": "one", "var": "two"}, "hooks": {"PreToolUse": [user_hook]}, "custom": {"keep": True}}
    if case == "near":
        payload["env"] = {"claude_code_subagent_model": "user"}
    if case == "metadata":
        payload["Hooks"] = {"user": "case-preserved"}
    if case == "deep-bracket":
        for index in range(15):
            payload["custom"] = {str(index): payload["custom"]}
    if case == "timestamps":
        payload["custom"] = {"offset": "2030-01-02T03:04:05+05:30", "fraction": "2030-01-02T03:04:05.120Z", "ms": "/Date(0+0530)/", "literal": r"\/Date(0)/"}
        payload["env"]["OPAQUE_OFFSET"] = payload["custom"]["offset"]
    if case == "nested-metadata":
        user_hook["meta"] = {"Model": "upper", "model": "lower", "offset": "2030-01-02T03:04:05+05:30"}
        user_hook["hooks"][0]["meta"] = {"Key": "upper", "key": "lower"}
    if case == "date-keys":
        payload["custom"] = {"2030-01-02T03:04:05+05:30": "key-preserved", "/Date(0)/": "also-a-key"}
    if case == "null-hooks":
        payload["hooks"] = None
    raw = json.dumps(payload)
    if case == "timestamps":
        raw = raw.replace("/", "\\/")
    settings.write_text(raw, encoding="utf-8")
    script = tmp_path / "hook-probe.ps1"
    script.write_text(_HARNESS, encoding="utf-8-sig")
    contents = []
    for _ in range(2):
        result = _invoke(script, target, writer)
        assert "Could not merge" not in result.stdout, result.stdout
        contents.append(settings.read_bytes())
        actual = json.loads(contents[-1])
        for key, value in payload.items():
            if key != "hooks":
                if writer == "upgrade" and key == "env":
                    assert all(actual[key][name] == entry for name, entry in value.items())
                else:
                    assert actual[key] == value
        if case != "null-hooks":
            assert user_hook in actual["hooks"]["PreToolUse"]
        commands = [hook["command"] for entries in actual["hooks"].values() for entry in entries for hook in entry["hooks"]]
        stems = ["git-guardrails.ps1", "usage-display.ps1", "require-description.ps1", "require-powershell-description.ps1", "format-powershell-description.py"] if writer in ("Install-GitGuardrails", "upgrade") else (["usage-display.ps1"] if writer == "Install-UsageDisplay" else ["require-description.ps1", "require-powershell-description.ps1", "format-powershell-description.py"])
        for stem in stems:
            matching = [command for command in commands if stem in command]
            assert len(matching) == 1, (stem, commands)
            assert "cursor-hook-compat.py" in matching[0], matching[0]
            assert str((target / "hooks").resolve()).replace("\\", "/") in matching[0], matching[0]
        if writer == "upgrade":
            assert actual["env"]["CLAUDE_CODE_SUBAGENT_MODEL"] == "sonnet"
    if writer == "upgrade":
        # First seed ends in the PowerShell core writer; a no-change upgrade
        # ends in the existing Python hook converter. Their whitespace differs.
        assert json.loads(contents[0]) == json.loads(contents[1])
        result = _invoke(script, target, writer)
        assert "Could not merge" not in result.stdout, result.stdout
        assert settings.read_bytes() == contents[1]
    else:
        assert contents[0] == contents[1], "repeat hook write changed settings bytes"


@pytest.mark.parametrize("writer", ["Install-GitGuardrails", "Install-UsageDisplay", "Install-RequireDescription"])
@pytest.mark.parametrize("raw", ['[{"keep":true}]', 'null', '{"broken":', '{"hooks":[],"keep":true}', '{"hooks":"keep","keep":true}', '{"hooks":false,"keep":true}'])
def test_hook_writers_refuse_nonobject_documents_or_hooks(tmp_path: Path, writer: str, raw: str) -> None:
    target = tmp_path / "home/.claude"
    target.mkdir(parents=True)
    settings = target / "settings.json"
    settings.write_text(raw, encoding="utf-8")
    script = tmp_path / "hook-probe.ps1"
    script.write_text(_HARNESS, encoding="utf-8-sig")
    result = _invoke(script, target, writer)
    assert settings.read_text(encoding="utf-8") == raw
    assert "Could not merge" in result.stdout
