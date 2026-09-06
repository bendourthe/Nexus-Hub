"""Behavioral parity for Claude core-setting seed-if-absent installs."""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
from collections.abc import Callable
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
INSTALLER_SH = REPO_ROOT / "scripts" / "installer.sh"
INSTALLER_PS1 = REPO_ROOT / "scripts" / "installer.ps1"

BASH = shutil.which("bash")
JQ = shutil.which("jq")


def _resolve_powershell() -> str | None:
    """Resolve the pinned PowerShell edition when CI names one."""
    pinned = os.environ.get("NEXUS_TEST_POWERSHELL")
    if pinned:
        return shutil.which(pinned)
    for name in ("pwsh", "powershell"):
        found = shutil.which(name)
        if found:
            return found
    return None


PWSH = _resolve_powershell()

_SH_HARNESS = r"""
set -euo pipefail
installer="$1"; repo_root="$2"; target="$3"
GRAY=""; GREEN=""; YELLOW=""
write_item() { printf '%s\n' "$1"; }
extract() { sed -n "/^$1() {/,/^}/p" "$installer"; }
eval "$(extract install_core_settings)"
install_core_settings "$repo_root" "$target" "Test"
"""

_PS_HARNESS = r"""
$ErrorActionPreference = 'Stop'
$installer = $args[0]; $repoRoot = $args[1]; $target = $args[2]
$ast = [System.Management.Automation.Language.Parser]::ParseFile($installer, [ref]$null, [ref]$null)
$fn = $ast.FindAll({
    $args[0] -is [System.Management.Automation.Language.FunctionDefinitionAst] -and
    $args[0].Name -eq 'Install-CoreSettings'
}, $true) | Select-Object -First 1
if (-not $fn) { Write-Error 'Install-CoreSettings not found'; exit 3 }
Invoke-Expression $fn.Extent.Text
function Write-Item { param($Message, $Color) Write-Host $Message }
function Write-JsonFile { param($Path, $Object, [int]$Depth = 100)
    [System.IO.File]::WriteAllText(
        $Path,
        ($Object | ConvertTo-Json -Depth $Depth),
        (New-Object System.Text.UTF8Encoding($false))
    )
}
Install-CoreSettings -RepoRoot $repoRoot -TargetClaudeDir $target -Scope 'Test'
"""


def _seed(tmp_path: Path, value: dict[str, object]) -> tuple[Path, bytes]:
    target = tmp_path / "claude"
    target.mkdir(parents=True)
    settings = target / "settings.json"
    settings.write_text(json.dumps(value, indent=2), encoding="utf-8")
    return settings, settings.read_bytes()


def _run_bash(tmp_path: Path, target: Path) -> subprocess.CompletedProcess[str]:
    harness = tmp_path / "core-settings-harness.sh"
    harness.write_text(_SH_HARNESS, encoding="utf-8", newline="\n")
    return subprocess.run(
        [BASH, str(harness), str(INSTALLER_SH), str(REPO_ROOT), str(target)],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )


def _run_powershell(tmp_path: Path, target: Path) -> subprocess.CompletedProcess[str]:
    harness = tmp_path / "core-settings-harness.ps1"
    harness.write_text(_PS_HARNESS, encoding="utf-8")
    return subprocess.run(
        [
            PWSH,
            "-NoProfile",
            "-File",
            str(harness),
            str(INSTALLER_PS1),
            str(REPO_ROOT),
            str(target),
        ],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )


Runner = Callable[[Path, Path], subprocess.CompletedProcess[str]]
RUNNERS: list[object] = [
    pytest.param(
        "bash",
        _run_bash,
        marks=pytest.mark.skipif(not BASH or not JQ, reason="needs working bash and jq"),
    ),
    pytest.param(
        "powershell",
        _run_powershell,
        marks=pytest.mark.skipif(not PWSH, reason="needs PowerShell"),
    ),
]


def test_core_settings_seeding_is_global_only_and_runs_after_settings_owner() -> None:
    bash = INSTALLER_SH.read_text(encoding="utf-8")
    powershell = INSTALLER_PS1.read_text(encoding="utf-8")

    bash_calls = list(re.finditer(r"(?m)^\s*install_core_settings\s+", bash))
    powershell_calls = list(
        re.finditer(r"(?m)^\s*Install-CoreSettings\s+-", powershell)
    )
    bash_call = re.search(
        r'(?m)^\s*install_core_settings\s+"\$repo_root"\s+'
        r'"\$global_claude"\s+"Global"\s+>/dev/null\s*$',
        bash,
    )
    powershell_call = re.search(
        r'(?m)^\s*Install-CoreSettings\s+-RepoRoot\s+\$RepoRoot\s+'
        r'-TargetClaudeDir\s+\$globalClaude\s+-Scope\s+"Global"\s+6>\$null\s*$',
        powershell,
    )
    bash_guardrail = re.search(
        r'(?m)^\s*install_git_guardrails\s+"\$repo_root"\s+"\$global_claude"\s+"Global"',
        bash,
    )
    powershell_guardrail = re.search(
        r'(?m)^\s*Install-GitGuardrails\s+-RepoRoot\s+\$RepoRoot\s+'
        r'-TargetClaudeDir\s+\$globalClaude\s+-Scope\s+"Global"',
        powershell,
    )
    assert len(bash_calls) == 1 and bash_call
    assert len(powershell_calls) == 1 and powershell_call
    assert bash_guardrail and bash_guardrail.start() < bash_call.start()
    assert powershell_guardrail and powershell_guardrail.start() < powershell_call.start()


def test_global_call_surfaces_warnings_and_reports_preservation_honestly() -> None:
    bash = INSTALLER_SH.read_text(encoding="utf-8")
    powershell = INSTALLER_PS1.read_text(encoding="utf-8")

    assert (
        'write_item "Warning: existing env is not an object; preserving it and '
        'skipping env.CLAUDE_CODE_EFFORT_LEVEL" "$YELLOW" >&2'
    ) in bash
    assert (
        'Write-Warning "existing env is not an object; preserving it and '
        'skipping env.CLAUDE_CODE_EFFORT_LEVEL"'
    ) in powershell
    detail = "settings.json retained; existing values preserved (see warnings above)"
    assert f'write_checklist_row "Core Settings" "ok" "{detail}"' in bash
    assert (
        f'Write-ChecklistRow -Label "Core Settings" -State "ok" -Detail "{detail}"'
        in powershell
    )
    assert "effortLevel, model, env (settings.json)" not in bash
    assert "effortLevel, model, env (settings.json)" not in powershell


@pytest.mark.parametrize(("label", "runner"), RUNNERS)
def test_existing_core_values_survive_core_settings_merge_byte_for_byte(
    tmp_path: Path, label: str, runner: Runner
) -> None:
    initial = {
        "effortLevel": "low",
        "model": "sonnet",
        "env": {"CLAUDE_CODE_EFFORT_LEVEL": "xhigh", "KEEP_ME": "yes"},
        "customUserSetting": {"preserve": True},
    }
    settings, before = _seed(tmp_path / label, initial)

    proc = runner(tmp_path / label, settings.parent)

    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert settings.read_bytes() == before
    assert "already present" in proc.stdout or "existing values preserved" in proc.stdout


@pytest.mark.parametrize(("label", "runner"), RUNNERS)
def test_absent_core_values_seed_from_the_high_default(
    tmp_path: Path, label: str, runner: Runner
) -> None:
    settings, _ = _seed(
        tmp_path / label,
        {"env": {"KEEP_ME": "yes"}, "customUserSetting": {"preserve": True}},
    )

    proc = runner(tmp_path / label, settings.parent)

    assert proc.returncode == 0, proc.stdout + proc.stderr
    installed = json.loads(settings.read_text(encoding="utf-8"))
    assert installed["effortLevel"] == "high"
    assert installed["model"] == "opus"
    assert installed["env"] == {
        "KEEP_ME": "yes",
        "CLAUDE_CODE_EFFORT_LEVEL": "high",
    }
    assert installed["customUserSetting"] == {"preserve": True}
    assert "seeded absent core settings" in proc.stdout

    seeded_bytes = settings.read_bytes()
    second = runner(tmp_path / label, settings.parent)
    assert second.returncode == 0, second.stdout + second.stderr
    assert settings.read_bytes() == seeded_bytes


@pytest.mark.parametrize(("label", "runner"), RUNNERS)
def test_missing_env_object_is_created(
    tmp_path: Path, label: str, runner: Runner
) -> None:
    settings, _ = _seed(
        tmp_path / label,
        {"customUserSetting": {"preserve": True}},
    )

    proc = runner(tmp_path / label, settings.parent)

    assert proc.returncode == 0, proc.stdout + proc.stderr
    installed = json.loads(settings.read_text(encoding="utf-8"))
    assert installed["effortLevel"] == "high"
    assert installed["model"] == "opus"
    assert installed["env"] == {"CLAUDE_CODE_EFFORT_LEVEL": "high"}
    assert installed["customUserSetting"] == {"preserve": True}


@pytest.mark.parametrize(("label", "runner"), RUNNERS)
def test_partial_config_seeds_only_missing_keys(
    tmp_path: Path, label: str, runner: Runner
) -> None:
    settings, _ = _seed(
        tmp_path / label,
        {
            "effortLevel": "medium",
            "env": {"CLAUDE_CODE_EFFORT_LEVEL": "xhigh", "KEEP_ME": "yes"},
        },
    )

    proc = runner(tmp_path / label, settings.parent)

    assert proc.returncode == 0, proc.stdout + proc.stderr
    installed = json.loads(settings.read_text(encoding="utf-8"))
    assert installed["effortLevel"] == "medium"
    assert installed["model"] == "opus"
    assert installed["env"] == {
        "CLAUDE_CODE_EFFORT_LEVEL": "xhigh",
        "KEEP_ME": "yes",
    }


@pytest.mark.parametrize(("label", "runner"), RUNNERS)
@pytest.mark.parametrize(
    ("initial", "expected_scalar", "expected_env_effort"),
    [
        ({"effortLevel": "low", "env": {"KEEP_ME": "yes"}}, "low", None),
        (
            {"env": {"CLAUDE_CODE_EFFORT_LEVEL": "xhigh", "KEEP_ME": "yes"}},
            None,
            "xhigh",
        ),
    ],
)
def test_single_effort_key_preserves_pair_shape_without_pinning_partner(
    tmp_path: Path,
    label: str,
    runner: Runner,
    initial: dict[str, object],
    expected_scalar: str | None,
    expected_env_effort: str | None,
) -> None:
    settings, _ = _seed(tmp_path / label, initial)

    proc = runner(tmp_path / label, settings.parent)

    assert proc.returncode == 0, proc.stdout + proc.stderr
    installed = json.loads(settings.read_text(encoding="utf-8"))
    if expected_scalar is None:
        assert "effortLevel" not in installed
    else:
        assert installed["effortLevel"] == expected_scalar
    if expected_env_effort is None:
        assert "CLAUDE_CODE_EFFORT_LEVEL" not in installed["env"]
    else:
        assert installed["env"]["CLAUDE_CODE_EFFORT_LEVEL"] == expected_env_effort
    assert installed["env"]["KEEP_ME"] == "yes"
    assert installed["model"] == "opus"

    first_bytes = settings.read_bytes()
    second = runner(tmp_path / label, settings.parent)

    assert second.returncode == 0, second.stdout + second.stderr
    assert settings.read_bytes() == first_bytes


@pytest.mark.parametrize(("label", "runner"), RUNNERS)
@pytest.mark.parametrize(
    "invalid_env",
    [
        pytest.param("user-owned-invalid-shape", id="string"),
        pytest.param(None, id="null"),
    ],
)
def test_non_object_env_is_warned_and_preserved(
    tmp_path: Path, label: str, runner: Runner, invalid_env: object
) -> None:
    settings, _ = _seed(
        tmp_path / label,
        {"env": invalid_env, "customUserSetting": "keep"},
    )

    proc = runner(tmp_path / label, settings.parent)

    assert proc.returncode == 0, proc.stdout + proc.stderr
    installed = json.loads(settings.read_text(encoding="utf-8"))
    assert installed["effortLevel"] == "high"
    assert installed["model"] == "opus"
    assert installed["env"] == invalid_env
    assert installed["customUserSetting"] == "keep"
    assert "existing env is not an object" in proc.stdout + proc.stderr


@pytest.mark.parametrize(("label", "runner"), RUNNERS)
@pytest.mark.parametrize(
    "invalid_env",
    [
        pytest.param("user-owned-invalid-shape", id="string"),
        pytest.param(None, id="null"),
    ],
)
def test_existing_scalar_with_non_object_env_preserves_pair_shape(
    tmp_path: Path, label: str, runner: Runner, invalid_env: object
) -> None:
    settings, _ = _seed(
        tmp_path / label,
        {"effortLevel": "medium", "env": invalid_env, "customUserSetting": "keep"},
    )

    proc = runner(tmp_path / label, settings.parent)

    assert proc.returncode == 0, proc.stdout + proc.stderr
    installed = json.loads(settings.read_text(encoding="utf-8"))
    assert installed["effortLevel"] == "medium"
    assert installed["model"] == "opus"
    assert installed["env"] == invalid_env
    assert installed["customUserSetting"] == "keep"
    assert "existing env is not an object" not in proc.stdout + proc.stderr
