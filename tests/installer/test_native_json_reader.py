"""Native JSON readers preserve opaque strings and root shape before settings writes."""
from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parents[2]
_INSTALLER = _ROOT / "scripts/installer.ps1"
_POWERSHELL = shutil.which(os.environ.get("NEXUS_TEST_POWERSHELL", "pwsh")) or shutil.which("powershell")
pytestmark = pytest.mark.skipif(not _POWERSHELL, reason="no PowerShell interpreter")
_HARNESS = r"""param($Installer,$InputFile,$OutputFile,$Legacy)
$ErrorActionPreference = 'Stop'
$ast = [Management.Automation.Language.Parser]::ParseFile($Installer,[ref]$null,[ref]$null)
foreach($name in @('Read-JsonDocument','Write-JsonFile')) {
 $fn = $ast.FindAll({$args[0] -is [Management.Automation.Language.FunctionDefinitionAst] -and $args[0].Name -eq $name},$true) | Select-Object -First 1
 if(-not $fn) { throw "Missing helper $name" }
 Invoke-Expression $fn.Extent.Text
}
if($Legacy -eq 'yes') {
 if($PSVersionTable.PSVersion.Major -lt 6) { Write-Output 'LEGACY_NOT_APPLICABLE'; exit 0 }
 function Get-Command { param($Name) [pscustomobject]@{Parameters=@{}} }
}
function Assert-OpaqueValue($Value) {
 if($Value -is [DateTime] -or $Value -is [DateTimeOffset]) { throw 'JSON string was coerced into a native date' }
 if($Value -is [Collections.IDictionary]) { foreach($item in $Value.GetEnumerator()) { Assert-OpaqueValue $item.Value } }
 elseif($Value -is [array]) { foreach($item in $Value) { Assert-OpaqueValue $item } }
}
$value = Read-JsonDocument $InputFile
Assert-OpaqueValue $value
$wrapped = [Collections.Specialized.OrderedDictionary]::new([StringComparer]::Ordinal)
$wrapped['value'] = $value
Write-JsonFile -Path $OutputFile -Object $wrapped
"""

CASES = [
    r'{"offset":"2030-01-02T03:04:05+05:30","fraction":"2030-01-02T03:04:05.120Z"}',
    r'{"value":"/Date(0+0530)/"}',
    r'{"value":"\/Date(0+0530)\/"}',
    r'{"slash":"\\/Date(0)/","nested":{"Key":"upper","key":"lower"}}',
    r'[{"value":"2030-01-02T03:04:05+05:30"}]',
    '[null]',
    '[]',
    'null',
    '"2030-01-02T03:04:05+05:30"',
    r'{"2030-01-02T03:04:05+05:30":"key","integer":9007199254740993,"arrays":[[],[null],{},true,false]}',
]


@pytest.mark.parametrize("raw", CASES)
@pytest.mark.parametrize("legacy", [False, True])
def test_native_json_reader_preserves_values_types_and_root_shape(tmp_path: Path, raw: str, legacy: bool) -> None:
    source = tmp_path / "input.json"
    output = tmp_path / "output.json"
    source.write_text(raw, encoding="utf-8")
    harness = tmp_path / "read-json.ps1"
    harness.write_text(_HARNESS, encoding="utf-8-sig")
    result = subprocess.run([_POWERSHELL, "-NoProfile", "-NonInteractive", "-File", str(harness), str(_INSTALLER), str(source), str(output), "yes" if legacy else "no"], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=60, check=False)
    assert result.returncode == 0, result.stdout + result.stderr
    if "LEGACY_NOT_APPLICABLE" in result.stdout:
        pytest.skip("older-Core capability fallback needs a Core shell")
    assert json.loads(output.read_text(encoding="utf-8-sig"))["value"] == json.loads(raw)

def test_native_json_reader_handles_long_backslash_runs_without_rescanning(tmp_path):
    value = {"slashes": "\\" * 65536, "date": "/Date(0+0530)/"}
    source = tmp_path / "long.json"
    output = tmp_path / "output.json"
    source.write_text(json.dumps(value), encoding="utf-8")
    harness = tmp_path / "read-json.ps1"
    harness.write_text(_HARNESS, encoding="utf-8-sig")
    result = subprocess.run([_POWERSHELL, "-NoProfile", "-NonInteractive", "-File", str(harness), str(_INSTALLER), str(source), str(output), "no"], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=20, check=False)
    assert result.returncode == 0, result.stdout + result.stderr
    assert json.loads(output.read_text(encoding="utf-8-sig"))["value"] == value
