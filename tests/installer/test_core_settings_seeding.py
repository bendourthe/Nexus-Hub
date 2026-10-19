"""Behavioral parity for ownership-aware Claude core-setting installs."""

from __future__ import annotations

import inspect
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
foreach ($helperName in @('Read-JsonDocument', 'Write-JsonFile')) {
    $helperAst = $ast.Find({param($node) $node -is [System.Management.Automation.Language.FunctionDefinitionAst] -and $node.Name -eq $helperName}, $true)
    if ($helperAst) { Invoke-Expression $helperAst.Extent.Text }
}
Install-CoreSettings -RepoRoot $repoRoot -TargetClaudeDir $target -Scope 'Test'
"""


def _seed(tmp_path: Path, value: dict[str, object]) -> tuple[Path, bytes]:
    target = tmp_path / "claude"
    target.mkdir(parents=True)
    settings = target / "settings.json"
    settings.write_text(json.dumps(value, indent=2), encoding="utf-8")
    return settings, settings.read_bytes()


# Decode child output permissively. `text=True` alone picks an encoding from the
# environment, and under UTF-8 mode a shell that writes its own console code page
# is undecodable: the reader thread raises UnicodeDecodeError, subprocess leaves
# `stdout` as None, and every assertion over the output dies with
# `TypeError: argument of type 'NoneType' is not iterable` -- which points at the
# assertion rather than at the encoding, and hides that the installer itself
# worked correctly.
#
# This is not hypothetical. `scripts/ci/run.py` exports PYTHONUTF8=1 and
# PYTHONIOENCODING=utf-8 for every step, so on a host whose only PowerShell is
# Windows PowerShell 5.1 (cp1252 output, no pwsh 7) these tests failed inside
# `--profile full` and passed when run directly. CI never saw it because its
# Windows runner has pwsh 7, which emits UTF-8.
#
# `errors="replace"` is the same choice run.py itself makes. Every assertion here
# matches ASCII text, so a replaced byte cannot mask a real failure.
_DECODE = {"encoding": "utf-8", "errors": "replace"}


def _function_source(fn) -> str:
    """Return the source of one function, without `inspect.getsource`.

    `inspect.getsource` resolves source through the module's loader. Under
    pytest's assertion-rewriting importer that lookup fails on some
    interpreter/pytest combinations (observed: Python 3.12 + pytest 7.4.4 on
    Windows), raising `OSError: could not get source code` -- while the same
    call succeeds on the same file outside pytest. That made this test fail for
    a reason unrelated to the behavior it guards.

    Reading the defining file directly and slicing from the function's own
    `co_firstlineno` to the next dedent keeps the property that matters: the
    assertion sees ONE function's body, so it cannot pass vacuously by matching
    this test's own assertion text elsewhere in the file.
    """
    path = Path(inspect.getfile(fn))
    lines = path.read_text(encoding="utf-8").splitlines()
    start = fn.__code__.co_firstlineno - 1
    indent = len(lines[start]) - len(lines[start].lstrip())
    body = [lines[start]]
    for line in lines[start + 1 :]:
        if line.strip() and (len(line) - len(line.lstrip())) <= indent:
            break
        body.append(line)
    return "\n".join(body)


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
        **_DECODE,
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
        **_DECODE,
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
        'skipping template env defaults" "$YELLOW" >&2'
    ) in bash
    assert (
        'Write-Warning "existing env is not an object; preserving it and '
        'skipping template env defaults"'
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
        "env": {
            "CLAUDE_CODE_EFFORT_LEVEL": "xhigh",
            "CLAUDE_CODE_SUBAGENT_MODEL": "inherit",
            "KEEP_ME": "yes",
        },
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
    assert installed["modelSettings"]["claude-opus-5-5"]["effortLevel"] == "high"
    assert installed["env"] == {
        "KEEP_ME": "yes",
        "CLAUDE_CODE_SUBAGENT_MODEL": "sonnet",
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
    assert installed["modelSettings"]["claude-opus-5-5"]["effortLevel"] == "high"
    assert installed["env"] == {
        "CLAUDE_CODE_SUBAGENT_MODEL": "sonnet",
    }
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
        "CLAUDE_CODE_SUBAGENT_MODEL": "sonnet",
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
    assert "existing env is not an object" in proc.stdout + proc.stderr


def test_child_output_is_decoded_permissively() -> None:
    """Regression guard for WN-I.

    Both runners must pass an explicit encoding AND an error policy. Without
    them, `text=True` picks an encoding from the environment, and under the
    UTF-8 mode that `scripts/ci/run.py` exports for every step, a shell writing
    its own console code page becomes undecodable: subprocess leaves `stdout`
    as None and every assertion over the output fails with a TypeError that
    points at the assertion instead of at the encoding.

    Asserted at the source level because the defect is invisible on a host with
    pwsh 7 (UTF-8 native), which is what CI's Windows runner has. A behavioral
    test here would pass on CI while the defect was live for anyone whose only
    PowerShell is Windows PowerShell 5.1.
    """
    assert _DECODE == {"encoding": "utf-8", "errors": "replace"}
    # Inspect the functions rather than the file text: a source-wide string
    # search would also match this test's own assertions and pass vacuously.
    for runner in (_run_bash, _run_powershell):
        body = _function_source(runner)
        assert "**_DECODE," in body, (
            f"{runner.__name__} does not decode through _DECODE, so its output "
            "becomes None under UTF-8 mode when the child writes another code page"
        )


@pytest.mark.parametrize(("label", "runner"), RUNNERS)
def test_upgrade_receives_future_env_defaults_without_pinning_effort_partner(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, label: str, runner: Runner
) -> None:
    """An old install must receive future defaults without creating an effort override."""
    template = json.loads(
        (REPO_ROOT / "catalog/hooks/settings.json").read_text(encoding="utf-8")
    )
    template["env"].update(
        {
            "CLAUDE_CODE_SUBAGENT_MODEL": "sonnet",
            "NEXUS_FUTURE_DEFAULT": "enabled",
        }
    )
    fake_repo = tmp_path / "repo"
    hooks = fake_repo / "catalog/hooks"
    hooks.mkdir(parents=True)
    (hooks / "settings.json").write_text(
        json.dumps(template, indent=2), encoding="utf-8"
    )
    monkeypatch.setitem(globals(), "REPO_ROOT", fake_repo)
    initial = {
        "model": "sonnet",
        "effortLevel": "xhigh",
        "env": {"KEEP_ME": "yes"},
        "customUserSetting": {"keep": True},
    }
    settings, _ = _seed(tmp_path / label, initial)

    proc = runner(tmp_path / label, settings.parent)

    assert proc.returncode == 0, proc.stdout + proc.stderr
    installed = json.loads(settings.read_text(encoding="utf-8"))
    assert installed == {
        **initial,
        "env": {
            "KEEP_ME": "yes",
            "CLAUDE_CODE_SUBAGENT_MODEL": "sonnet",
            "NEXUS_FUTURE_DEFAULT": "enabled",
        },
    }
    first = settings.read_bytes()
    second = runner(tmp_path / label, settings.parent)
    assert second.returncode == 0, second.stdout + second.stderr
    assert settings.read_bytes() == first


@pytest.mark.parametrize(("label", "runner"), RUNNERS)
@pytest.mark.parametrize("owned_value", ["inherit", "haiku", "", None])
def test_existing_subagent_value_is_never_replaced(
    tmp_path: Path, label: str, runner: Runner, owned_value: object
) -> None:
    initial = {
        "model": "sonnet",
        "effortLevel": "medium",
        "env": {"CLAUDE_CODE_SUBAGENT_MODEL": owned_value, "KEEP_ME": "yes"},
    }
    settings, before = _seed(tmp_path / label, initial)

    proc = runner(tmp_path / label, settings.parent)

    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert settings.read_bytes() == before


@pytest.mark.parametrize(("label", "runner"), RUNNERS)
@pytest.mark.parametrize("raw", ["{", "[1, 2]", "null", "[{}]", '[{"model":"opus"}]'])
def test_invalid_settings_root_is_preserved_without_an_exit_mismatch(
    tmp_path: Path, label: str, runner: Runner, raw: str
) -> None:
    settings, _ = _seed(tmp_path / label, {})
    settings.write_text(raw, encoding="utf-8", newline="")
    before = settings.read_bytes()

    proc = runner(tmp_path / label, settings.parent)

    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert settings.read_bytes() == before
    assert "settings.json" in proc.stdout + proc.stderr


@pytest.mark.parametrize(("label", "runner"), RUNNERS)
def test_unicode_user_values_survive_an_upgrade(
    tmp_path: Path, label: str, runner: Runner
) -> None:
    initial = {
        "model": "sonnet",
        "effortLevel": "xhigh",
        "customUserSetting": {"label": "caf\u00e9 \u2603"},
    }
    settings, _ = _seed(tmp_path / label, initial)
    settings.write_text(
        json.dumps(initial, ensure_ascii=False, indent=2), encoding="utf-8", newline=""
    )

    proc = runner(tmp_path / label, settings.parent)

    assert proc.returncode == 0, proc.stdout + proc.stderr
    installed = json.loads(settings.read_text(encoding="utf-8"))
    assert installed["customUserSetting"] == initial["customUserSetting"]
    assert installed["model"] == "sonnet"
    assert installed["effortLevel"] == "xhigh"
    assert installed["env"] == {"CLAUDE_CODE_SUBAGENT_MODEL": "sonnet"}


@pytest.mark.parametrize(("label", "runner"), RUNNERS)
def test_literal_target_path_is_preserved(
    tmp_path: Path, label: str, runner: Runner
) -> None:
    settings, _ = _seed(
        tmp_path / label / "profile [custom]",
        {"model": "sonnet", "effortLevel": "xhigh"},
    )

    proc = runner(tmp_path / label, settings.parent)

    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert json.loads(settings.read_text(encoding="utf-8")) == {
        "model": "sonnet",
        "effortLevel": "xhigh",
        "env": {"CLAUDE_CODE_SUBAGENT_MODEL": "sonnet"},
    }


_SEED_MANIFEST = "core-settings-seeds.json"
_OPUS_EFFORT = "modelSettings.claude-opus-5-5.effortLevel"


def _ownership_file(settings: Path) -> Path:
    return settings.parent.parent / ".nexus-hub" / _SEED_MANIFEST


def _write_ownership(settings: Path, values: dict[str, object]) -> Path:
    record = _ownership_file(settings)
    record.parent.mkdir(parents=True, exist_ok=True)
    record.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "target": settings.parent.name + "/settings.json",
                "values": values,
                "removed": [],
                "keepMetadata": True,
            }
        ),
        encoding="utf-8",
    )
    return record


@pytest.mark.parametrize(("label", "runner"), RUNNERS)
@pytest.mark.parametrize("case", ["owned", "changed", "legacy", "fresh"])
def test_core_seed_ownership_cases(
    tmp_path: Path, label: str, runner: Runner, case: str
) -> None:
    initial = (
        {}
        if case == "fresh"
        else {
            "model": "opus",
            "effortLevel": "high",
            "env": {
                "CLAUDE_CODE_EFFORT_LEVEL": "medium",
                "CLAUDE_CODE_SUBAGENT_MODEL": "inherit",
            },
            "modelSettings": {
                "claude-opus-5-5": {"effortLevel": "medium", "maxEffortLevel": "xhigh"}
            },
            "customUserSetting": {"keep": True},
        }
    )
    settings, before = _seed(tmp_path / label, initial)
    if case in ("owned", "changed"):
        prior = "medium" if case == "owned" else "high"
        _write_ownership(
            settings, {"env.CLAUDE_CODE_EFFORT_LEVEL": prior, _OPUS_EFFORT: prior}
        )
    proc = runner(tmp_path / label, settings.parent)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    installed = json.loads(settings.read_text(encoding="utf-8"))
    if case in ("owned", "fresh"):
        assert "CLAUDE_CODE_EFFORT_LEVEL" not in installed["env"]
        assert installed["modelSettings"]["claude-opus-5-5"]["effortLevel"] == "high"
        record = json.loads(_ownership_file(settings).read_text(encoding="utf-8-sig"))
        assert not _ownership_file(settings).read_bytes().startswith(b"\xef\xbb\xbf")
        assert record["values"][_OPUS_EFFORT] == "high"
        assert "env.CLAUDE_CODE_EFFORT_LEVEL" not in record["values"]
        if case == "owned":
            assert (
                installed["modelSettings"]["claude-opus-5-5"]["maxEffortLevel"]
                == "xhigh"
            )
            assert installed["customUserSetting"] == {"keep": True}
            assert record["keepMetadata"] is True
        else:
            assert record["values"]["model"] == "opus"
            assert record["values"]["effortLevel"] == "high"
            assert record["values"]["env.CLAUDE_CODE_SUBAGENT_MODEL"] == "sonnet"
    else:
        assert settings.read_bytes() == before
        if case == "legacy":
            from scripts.lib.integrations.claude import effort_override_note

            note = effort_override_note(settings)
            assert note and "medium" in note and "/effort" in note
            assert "Remove only env.CLAUDE_CODE_EFFORT_LEVEL" in note
    first = settings.read_bytes()
    second = runner(tmp_path / label, settings.parent)
    assert second.returncode == 0, second.stdout + second.stderr
    assert settings.read_bytes() == first


@pytest.mark.parametrize(("label", "runner"), RUNNERS)
@pytest.mark.parametrize(
    "bad_record",
    [
        "{",
        "null",
        '{"schema_version":1,"target":"another/settings.json","values":{}}',
        '[{"schema_version":1,"target":"claude/settings.json","values":{"env.CLAUDE_CODE_EFFORT_LEVEL":"medium"},"removed":[]}]',
    ],
)
def test_invalid_seed_record_preserves_existing_effort(
    tmp_path: Path, label: str, runner: Runner, bad_record: str
) -> None:
    template = json.loads(
        (REPO_ROOT / "catalog/hooks/settings.json").read_text(encoding="utf-8")
    )
    template.pop("hooks", None)
    template["env"]["CLAUDE_CODE_EFFORT_LEVEL"] = "medium"
    settings, before = _seed(tmp_path / label, template)
    record = _ownership_file(settings)
    record.parent.mkdir(parents=True, exist_ok=True)
    record.write_text(bad_record, encoding="utf-8")
    proc = runner(tmp_path / label, settings.parent)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert settings.read_bytes() == before
    assert record.read_text(encoding="utf-8") == bad_record


@pytest.mark.parametrize(("label", "runner"), RUNNERS)
def test_removed_owned_model_effort_is_not_reseeded(
    tmp_path: Path, label: str, runner: Runner
) -> None:
    settings, _ = _seed(tmp_path / label, {})
    first = runner(tmp_path / label, settings.parent)
    assert first.returncode == 0, first.stdout + first.stderr
    installed = json.loads(settings.read_text(encoding="utf-8"))
    del installed["modelSettings"]["claude-opus-5-5"]["effortLevel"]
    settings.write_text(json.dumps(installed), encoding="utf-8")
    for _ in range(2):
        proc = runner(tmp_path / label, settings.parent)
        assert proc.returncode == 0, proc.stdout + proc.stderr
        assert (
            "effortLevel"
            not in json.loads(settings.read_text())["modelSettings"]["claude-opus-5-5"]
        )
    record = json.loads(_ownership_file(settings).read_text(encoding="utf-8-sig"))
    assert _OPUS_EFFORT in record["removed"]
    assert _OPUS_EFFORT not in record["values"]


def _configure_settings_owner_harness(
    monkeypatch: pytest.MonkeyPatch, label: str
) -> tuple[str, str]:
    """Exercise the real settings writers; hook copying/conversion are separate contracts."""
    if label == "bash":
        name = "_SH_HARNESS"
        extra = """
install_claude_hook_files() { :; }
safe_copy() { :; }
convert_claude_hook_commands_for_posix() { :; }
merge_managed_claude_hooks() { cat "$1"; }
eval "$(extract resolve_settings_write_target)"
eval "$(extract install_git_guardrails)"
eval "$(extract install_usage_display)"
eval "$(extract install_require_description)"
install_git_guardrails "$repo_root" "$target" "Test"
install_usage_display "$repo_root" "$target" "Test"
install_require_description "$repo_root" "$target" "Test"
"""
        marker = 'install_core_settings "$repo_root" "$target" "Test"'
    else:
        name = "_PS_HARNESS"
        extra = """
foreach ($ownerName in @('Install-GitGuardrails','Install-UsageDisplay','Install-RequireDescription')) {
    $owner = $ast.FindAll({
        $args[0] -is [System.Management.Automation.Language.FunctionDefinitionAst] -and
        $args[0].Name -eq $ownerName
    }, $true) | Select-Object -First 1
    Invoke-Expression $owner.Extent.Text
}
function Install-ClaudeHookFiles { }
function Safe-Copy { }
function Convert-ClaudeHookCommandsForWindows { }
function Merge-ManagedClaudeHooks { param($ExistingJson, $TemplateJson) return $ExistingJson }
Install-GitGuardrails -RepoRoot $repoRoot -TargetClaudeDir $target -Scope 'Test'
Install-UsageDisplay -RepoRoot $repoRoot -TargetClaudeDir $target -Scope 'Test'
Install-RequireDescription -RepoRoot $repoRoot -TargetClaudeDir $target -Scope 'Test'
"""
        marker = "Install-CoreSettings -RepoRoot $repoRoot -TargetClaudeDir $target -Scope 'Test'"
    original = globals()[name]
    assert original.count(marker) == 1
    monkeypatch.setitem(globals(), name, original.replace(marker, extra + marker))
    return name, original


@pytest.mark.parametrize(("label", "runner"), RUNNERS)
@pytest.mark.parametrize("removed", [False, True])
def test_fresh_template_copy_handoff_records_actual_core_writes(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    label: str,
    runner: Runner,
    removed: bool,
) -> None:
    target = tmp_path / label / "claude"
    target.mkdir(parents=True)
    settings = target / "settings.json"
    if removed:
        record = _write_ownership(settings, {})
        data = json.loads(record.read_text())
        data["removed"] = [_OPUS_EFFORT]
        record.write_text(json.dumps(data), encoding="utf-8")
    name, original = _configure_settings_owner_harness(monkeypatch, label)
    proc = runner(tmp_path / label, target)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    installed = json.loads(settings.read_text(encoding="utf-8-sig"))
    record = json.loads(_ownership_file(settings).read_text(encoding="utf-8-sig"))
    expected = {"effortLevel", "model", "env.CLAUDE_CODE_SUBAGENT_MODEL"}
    expected |= {
        f"modelSettings.{model}.effortLevel" for model in installed["modelSettings"]
    }
    if removed:
        expected.remove(_OPUS_EFFORT)
        assert "effortLevel" not in installed["modelSettings"]["claude-opus-5-5"]
        assert _OPUS_EFFORT in record["removed"]
    assert set(record["values"]) == expected
    assert "hooks" not in record["values"] and "attribution" not in record["values"]
    assert not _ownership_file(settings).read_bytes().startswith(b"\xef\xbb\xbf")
    settings_before = settings.read_bytes()
    record_before = _ownership_file(settings).read_bytes()
    monkeypatch.setitem(globals(), name, original)
    second = runner(tmp_path / label, target)
    assert second.returncode == 0, second.stdout + second.stderr
    assert settings.read_bytes() == settings_before
    assert _ownership_file(settings).read_bytes() == record_before


@pytest.mark.parametrize(("label", "runner"), RUNNERS)
@pytest.mark.parametrize("profile", ["ordinary", "profile [custom]"])
def test_upgrade_writer_sequence_preserves_literal_paths_and_utf8(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    label: str,
    runner: Runner,
    profile: str,
) -> None:
    target = tmp_path / label / profile / "claude"
    target.mkdir(parents=True)
    settings = target / "settings.json"
    initial = json.loads(
        (REPO_ROOT / "catalog/hooks/settings.json").read_text(encoding="utf-8")
    )
    initial["hooks"] = {"PreToolUse": [], "Stop": []}
    initial["keepUnicode"] = "caf\u00e9 \u2603"
    settings.write_text(json.dumps(initial, ensure_ascii=False), encoding="utf-8")
    _configure_settings_owner_harness(monkeypatch, label)
    proc = runner(tmp_path / label, target)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    installed = json.loads(settings.read_text(encoding="utf-8"))
    assert installed["keepUnicode"] == initial["keepUnicode"]
    assert "reconciled with managed hooks" in proc.stdout
    assert installed["hooks"]["Stop"] and installed["hooks"]["PreToolUse"]
    assert not _ownership_file(settings).exists(), (
        "matching pre-existing values are not installer ownership"
    )


@pytest.mark.parametrize(("label", "runner"), RUNNERS)
@pytest.mark.parametrize("invalid_models", [None, "preserve", []])
def test_nonobject_model_settings_preserved_while_env_defaults_seed(
    tmp_path: Path, label: str, runner: Runner, invalid_models: object
) -> None:
    settings, _ = _seed(
        tmp_path / label,
        {
            "model": "opus",
            "effortLevel": "high",
            "modelSettings": invalid_models,
            "env": {"KEEP": "yes"},
        },
    )
    proc = runner(tmp_path / label, settings.parent)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    installed = json.loads(settings.read_text(encoding="utf-8"))
    assert installed["modelSettings"] == invalid_models
    assert installed["env"] == {"KEEP": "yes", "CLAUDE_CODE_SUBAGENT_MODEL": "sonnet"}


@pytest.mark.parametrize(("label", "runner"), RUNNERS)
def test_removed_legacy_override_is_user_owned_even_if_stale_value_remains(
    tmp_path: Path, label: str, runner: Runner
) -> None:
    template = json.loads(
        (REPO_ROOT / "catalog/hooks/settings.json").read_text(encoding="utf-8")
    )
    template.pop("hooks", None)
    template["env"]["CLAUDE_CODE_EFFORT_LEVEL"] = "medium"
    settings, before = _seed(tmp_path / label, template)
    key = "env.CLAUDE_CODE_EFFORT_LEVEL"
    record = _write_ownership(settings, {key: "medium"})
    ownership = json.loads(record.read_text(encoding="utf-8"))
    ownership["removed"] = [key]
    record.write_text(json.dumps(ownership), encoding="utf-8")
    proc = runner(tmp_path / label, settings.parent)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert settings.read_bytes() == before
    installed_record = json.loads(record.read_text(encoding="utf-8"))
    assert key in installed_record["removed"]
    assert key not in installed_record["values"]


@pytest.mark.parametrize(("label", "runner"), RUNNERS)
@pytest.mark.parametrize(
    "initial",
    [
        {"env": {"claude_code_subagent_model": "user"}, "effortLevel": "high"},
        {"Model": "user-model", "effortLevel": "high"},
        {"ENV": {"user": "keep"}, "effortLevel": "high"},
        {"ModelSettings": {"keep": False}, "effortLevel": "high"},
        {"env": {"VAR": "one", "var": "two"}, "effortLevel": "high"},
        {"custom": {"Value": "one", "value": "two", "array": [{}, [], None, False]}},
        {"modelSettings": {"claude-opus-5-5": {"EffortLevel": "user"}}},
    ],
)
def test_case_distinct_user_keys_survive_core_seeding(
    tmp_path: Path, label: str, runner: Runner, initial: dict[str, object]
) -> None:
    """JSON keys retain exact spelling while the documented default is delivered."""
    settings, _ = _seed(tmp_path / label, initial)
    result = runner(tmp_path / label, settings.parent)
    assert result.returncode == 0, result.stdout + result.stderr
    actual = json.loads(settings.read_text(encoding="utf-8-sig"))
    assert actual.get("env", {}).get("CLAUDE_CODE_SUBAGENT_MODEL") == "sonnet", result.stdout + result.stderr
    for key, value in initial.items():
        if key == "env":
            for name, expected in value.items():
                assert actual[key][name] == expected
        elif key == "modelSettings":
            for model, properties in value.items():
                for name, expected in properties.items():
                    assert actual[key][model][name] == expected
        else:
            assert actual[key] == value
    before_second_run = settings.read_bytes()
    runner(tmp_path / label, settings.parent)
    assert settings.read_bytes() == before_second_run


@pytest.mark.parametrize(("label", "runner"), RUNNERS)
def test_deep_user_object_survives_the_real_settings_writer(
    tmp_path: Path, label: str, runner: Runner
) -> None:
    """The native writer must not replace a deep object with a truncated string."""
    nested = {"keep": "must remain an object"}
    for index in range(15):
        nested = {"level" + str(index): nested}
    settings, _ = _seed(tmp_path / label, {"custom": nested})
    result = runner(tmp_path / label, settings.parent)
    assert result.returncode == 0, result.stdout + result.stderr
    actual = json.loads(settings.read_text(encoding="utf-8-sig"))
    assert actual["env"]["CLAUDE_CODE_SUBAGENT_MODEL"] == "sonnet"
    assert actual["custom"] == nested


@pytest.mark.parametrize(("label", "runner"), RUNNERS)
@pytest.mark.parametrize("raw", ['[{"model":"user","custom":{"keep":true}}]', "[]", "null", '"user"'])
def test_nonobject_settings_keep_their_original_root_shape(
    tmp_path: Path, label: str, runner: Runner, raw: str
) -> None:
    """A one-item root array must never be unwrapped into mutable settings."""
    settings, _ = _seed(tmp_path / label, {})
    settings.write_text(raw, encoding="utf-8")
    before = settings.read_bytes()
    result = runner(tmp_path / label, settings.parent)
    assert result.returncode == 0, result.stdout + result.stderr
    assert settings.read_bytes() == before
    assert "preserv" in (result.stdout + result.stderr).lower()


@pytest.mark.parametrize(("label", "runner"), RUNNERS)
def test_core_writer_preserves_opaque_user_timestamp_strings(tmp_path: Path, label: str, runner: Runner) -> None:
    """Applying defaults must retain JSON strings instead of interpreting dates."""
    payload = {"custom": {"offset": "2030-01-02T03:04:05+05:30", "fraction": "2030-01-02T03:04:05.120Z", "ms": "/Date(0+0530)/"}, "env": {"OPAQUE_STAMP": "2030-01-02T03:04:05+05:30"}}
    settings, _ = _seed(tmp_path / label, payload)
    settings.write_text(json.dumps(payload).replace("/", "\\/"), encoding="utf-8")
    for _ in range(2):
        proc = runner(tmp_path / label, settings.parent)
        assert proc.returncode == 0, proc.stdout + proc.stderr
        actual = json.loads(settings.read_text(encoding="utf-8-sig"))
        assert actual["custom"] == payload["custom"]
        assert actual["env"]["OPAQUE_STAMP"] == payload["env"]["OPAQUE_STAMP"]


@pytest.mark.parametrize(("label", "runner"), RUNNERS)
@pytest.mark.parametrize("invalid_role", ["settings-stream", "template-stream", "template-array"])
def test_core_merge_rejects_non_document_inputs_without_writes(tmp_path, monkeypatch, label, runner, invalid_role):
    settings, _ = _seed(tmp_path / label, {"model": "opus", "effortLevel": "high", "env": {"CLAUDE_CODE_EFFORT_LEVEL": "medium"}})
    record = _write_ownership(settings, {"env.CLAUDE_CODE_EFFORT_LEVEL": "medium"})
    template_dir = tmp_path / "template/catalog/hooks"
    template_dir.mkdir(parents=True)
    raw = (REPO_ROOT / "catalog/hooks/settings.json").read_text(encoding="utf-8")
    template = template_dir / "settings.json"
    template.write_text(raw, encoding="utf-8")
    if invalid_role == "settings-stream":
        with settings.open("a", encoding="utf-8") as output:
            output.write('\n{"env":{"CLAUDE_CODE_SUBAGENT_MODEL":"injected"}}\n')
    else:
        template.write_text(raw + "\n{}" if invalid_role == "template-stream" else "[" + raw + "]", encoding="utf-8")
    before_settings, before_record = settings.read_bytes(), record.read_bytes()
    monkeypatch.setattr(__import__(__name__, fromlist=["REPO_ROOT"]), "REPO_ROOT", tmp_path / "template")
    result = runner(tmp_path / label, settings.parent)
    assert result.returncode == 0, result.stdout + result.stderr
    assert settings.read_bytes() == before_settings
    assert record.read_bytes() == before_record
    assert "warning:" in (result.stdout + result.stderr).lower()
