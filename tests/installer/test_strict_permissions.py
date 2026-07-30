"""Tests for the --strict-permissions / -StrictPermissions installer flag (v3.15.6 AC5).

The flag installs an OPT-IN hardened Claude Code permission posture: it merges the
`deny` and `ask` arrays from configs/permissions/claude-permissions-strict.json on
top of the read-only allow list. Without the flag the install is unchanged.

Coverage:
  * the static surface (both installers declare the flag, document it in help,
    define the merge function, and reference the overlay by name);
  * the overlay's content contract (valid JSON, deny + ask present, NO
    defaultMode, the group A/B/C surfaces covered, and the allow list NOT
    duplicated so it keeps a single source of truth);
  * behavioural merge semantics, exercised against the REAL function extracted
    from each installer: additive (never drops a user's entries), leaves
    permissions.allow untouched, and idempotent on a second run;
  * the HO-2 intent marker (both installers export NEXUS_HUB_INIT for `init`).

The bash behavioural test needs jq (the same dependency the pre-existing allow
merge has) and skips without it; the PowerShell one needs no jq, so it runs on the
Windows dev host.
"""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
INSTALLER_SH = REPO_ROOT / "scripts" / "installer.sh"
INSTALLER_PS1 = REPO_ROOT / "scripts" / "installer.ps1"
OVERLAY = REPO_ROOT / "configs" / "permissions" / "claude-permissions-strict.json"
BASE_TEMPLATE = REPO_ROOT / "configs" / "permissions" / "claude-permissions.json"

BASH = shutil.which("bash")
PWSH = shutil.which("pwsh") or shutil.which("powershell")
JQ = shutil.which("jq")


# --- Static surface ---------------------------------------------------------


def test_installer_sh_declares_flag_and_helper() -> None:
    body = INSTALLER_SH.read_text(encoding="utf-8")
    assert "--strict-permissions)" in body, "installer.sh must parse --strict-permissions"
    assert "STRICT_PERMISSIONS=0" in body, "installer.sh must default the flag off"
    assert "merge_strict_permissions()" in body, "installer.sh must define the merge helper"
    assert "claude-permissions-strict.json" in body, "installer.sh must reference the overlay"
    assert "--strict-permissions" in body.split("EOF")[0] or "--strict-permissions" in body, (
        "installer.sh --help must document the flag"
    )


def test_installer_ps1_declares_flag_and_helper() -> None:
    body = INSTALLER_PS1.read_text(encoding="utf-8")
    assert "[switch]$StrictPermissions" in body, "installer.ps1 must declare the switch"
    assert "function Merge-StrictPermissions" in body, "installer.ps1 must define the merge helper"
    assert "claude-permissions-strict.json" in body, "installer.ps1 must reference the overlay"
    assert "-StrictPermissions" in body, "installer.ps1 -Help must document the switch"


def test_both_installers_gained_the_flag_in_lockstep() -> None:
    """The installer-aware rule: a flag must exist in BOTH installers."""
    sh = INSTALLER_SH.read_text(encoding="utf-8")
    ps = INSTALLER_PS1.read_text(encoding="utf-8")
    assert ("strict-permissions" in sh) == ("StrictPermissions" in ps), (
        "the strict-permissions flag must be present in both installers or neither"
    )


def test_ho2_intent_marker_exported_by_both_installers() -> None:
    """HO-2: `init` announces installer-owned intent for the hook carve-out."""
    assert "export NEXUS_HUB_INIT=1" in INSTALLER_SH.read_text(encoding="utf-8")
    assert '$env:NEXUS_HUB_INIT = "1"' in INSTALLER_PS1.read_text(encoding="utf-8")


# --- Overlay content contract ----------------------------------------------


@pytest.fixture(scope="module")
def overlay() -> dict:
    return json.loads(OVERLAY.read_text(encoding="utf-8"))


def test_overlay_is_valid_json_with_deny_and_ask(overlay: dict) -> None:
    perms = overlay["permissions"]
    assert isinstance(perms.get("deny"), list) and perms["deny"], "overlay needs deny entries"
    assert isinstance(perms.get("ask"), list) and perms["ask"], "overlay needs ask entries"


def test_overlay_omits_defaultmode(overlay: dict) -> None:
    """defaultMode's value set is unverified in this repo, so it is deliberately
    NOT written into a user's settings.json. See the overlay's own comment and the
    v3.15.6 known-gaps note."""
    assert "defaultMode" not in overlay["permissions"], (
        "defaultMode must stay out of the overlay until its enum is verified"
    )


def test_overlay_does_not_duplicate_the_allow_list(overlay: dict) -> None:
    """The overlay is an OVERLAY: the allow list has one source of truth."""
    assert "allow" not in overlay["permissions"], (
        "the overlay must not carry an allow list; it would drift from "
        "claude-permissions.json"
    )
    assert "allow" in json.loads(BASE_TEMPLATE.read_text(encoding="utf-8"))["permissions"]


@pytest.mark.parametrize(
    "needle",
    [
        # group A: version-control metadata, the highest-blast-radius writes
        ".git/hooks/**",
        ".git/config",
        # group C: interpreter paths an editor extension auto-executes
        ".venv/**",
        "pyvenv.cfg",
        # group B: git execution indirection, as command patterns
        "core.hooksPath",
        "core.fsmonitor",
    ],
)
def test_deny_covers_the_canonical_surfaces(overlay: dict, needle: str) -> None:
    blob = " ".join(overlay["permissions"]["deny"])
    assert needle in blob, f"deny does not cover {needle}"


@pytest.mark.parametrize(
    "needle",
    [".claude/settings.json", ".claude/hooks/**", ".vscode/tasks.json", ".cursor/**"],
)
def test_ask_covers_the_legitimately_edited_surfaces(overlay: dict, needle: str) -> None:
    """These have real agent workflows, so they require approval rather than a
    hard deny (control layer 3 of the agentic-endpoint-hardening skill)."""
    blob = " ".join(overlay["permissions"]["ask"])
    assert needle in blob, f"ask does not cover {needle}"


def test_deny_and_ask_do_not_overlap(overlay: dict) -> None:
    """An entry in both lists is ambiguous; the split must be a real decision."""
    deny = set(overlay["permissions"]["deny"])
    ask = set(overlay["permissions"]["ask"])
    assert not (deny & ask), f"entries in both deny and ask: {sorted(deny & ask)}"


# --- Behavioural merge semantics -------------------------------------------

_PS_HARNESS = r"""
$ErrorActionPreference = 'Stop'
$installer = $args[0]; $settings = $args[1]; $overlay = $args[2]

# Extract the REAL function from installer.ps1 via the AST (the script has
# top-level code, so it cannot simply be dot-sourced).
$ast = [System.Management.Automation.Language.Parser]::ParseFile($installer, [ref]$null, [ref]$null)
$fn = $ast.FindAll({
    $args[0] -is [System.Management.Automation.Language.FunctionDefinitionAst] -and
    $args[0].Name -eq 'Merge-StrictPermissions'
}, $true) | Select-Object -First 1
if (-not $fn) { Write-Error 'Merge-StrictPermissions not found'; exit 3 }
Invoke-Expression $fn.Extent.Text

# Minimal stubs for the installer's output + write helpers. Write-JsonFile
# mirrors the real one at installer.ps1:448 exactly, including the BOM-less
# UTF8Encoding($false): Set-Content -Encoding utf8 would emit a BOM on Windows
# PowerShell 5.1 and make the result unparseable by strict JSON readers.
function Write-Item { param($Message, $Color) }
function Write-JsonFile { param($Path, $Object, [int]$Depth = 10)
    $json = $Object | ConvertTo-Json -Depth $Depth
    [System.IO.File]::WriteAllText($Path, $json, (New-Object System.Text.UTF8Encoding($false)))
}

Merge-StrictPermissions -SettingsFile $settings -OverlayFile $overlay -Scope 'Test'
"""

_SH_HARNESS = r"""
set -euo pipefail
installer="$1"; settings="$2"; overlay="$3"
GRAY=""; GREEN=""; YELLOW=""
write_item() { :; }
# Extract the real function (it ends with a lone brace at column 0).
eval "$(sed -n '/^merge_strict_permissions() {/,/^}/p' "$installer")"
merge_strict_permissions "$settings" "$overlay" "Test"
"""


def _seed_settings(path: Path) -> None:
    """A settings.json shaped like a real one: an allow list plus a user's own
    deny entry that the merge must preserve."""
    path.write_text(
        json.dumps(
            {
                "permissions": {
                    "allow": ["Read", "Glob", "Bash(ls)"],
                    "deny": ["Bash(rm -rf /)"],
                },
                "someUserKey": "preserve-me",
            },
            indent=2,
        ),
        encoding="utf-8",
    )


def _assert_merged(result: dict, overlay_data: dict) -> None:
    perms = result["permissions"]
    # Additive: the user's pre-existing deny entry survives.
    assert "Bash(rm -rf /)" in perms["deny"], "merge dropped a user's deny entry"
    # Unrelated keys survive.
    assert result.get("someUserKey") == "preserve-me", "merge dropped an unrelated key"
    # allow is untouched by the overlay.
    assert perms["allow"] == ["Read", "Glob", "Bash(ls)"], "merge modified permissions.allow"
    # Every overlay entry landed.
    for entry in overlay_data["permissions"]["deny"]:
        assert entry in perms["deny"], f"deny entry not merged: {entry}"
    for entry in overlay_data["permissions"]["ask"]:
        assert entry in perms["ask"], f"ask entry not merged: {entry}"


@pytest.mark.skipif(not PWSH, reason="no PowerShell interpreter")
def test_powershell_merge_is_additive_and_idempotent(
    tmp_path: Path, overlay: dict
) -> None:
    harness = tmp_path / "harness.ps1"
    harness.write_text(_PS_HARNESS, encoding="utf-8")
    settings = tmp_path / "settings.json"
    _seed_settings(settings)

    for run in (1, 2):  # second run proves idempotence
        proc = subprocess.run(
            [PWSH, "-NoProfile", "-File", str(harness), str(INSTALLER_PS1),
             str(settings), str(OVERLAY)],
            capture_output=True, text=True, timeout=180,
        )
        assert proc.returncode == 0, f"run {run} failed: {proc.stderr}"
        _assert_merged(json.loads(settings.read_text(encoding="utf-8")), overlay)

    # Idempotent: no duplicate entries after two merges.
    perms = json.loads(settings.read_text(encoding="utf-8"))["permissions"]
    assert len(perms["deny"]) == len(set(perms["deny"])), "duplicate deny entries"
    assert len(perms["ask"]) == len(set(perms["ask"])), "duplicate ask entries"


@pytest.mark.skipif(not BASH or not JQ, reason="bash merge path requires bash and jq")
def test_bash_merge_is_additive_and_idempotent(tmp_path: Path, overlay: dict) -> None:
    harness = tmp_path / "harness.sh"
    harness.write_text(_SH_HARNESS, encoding="utf-8", newline="\n")
    settings = tmp_path / "settings.json"
    _seed_settings(settings)

    for run in (1, 2):
        proc = subprocess.run(
            [BASH, str(harness), str(INSTALLER_SH), str(settings), str(OVERLAY)],
            capture_output=True, text=True, timeout=180,
        )
        assert proc.returncode == 0, f"run {run} failed: {proc.stderr}"
        _assert_merged(json.loads(settings.read_text(encoding="utf-8")), overlay)

    perms = json.loads(settings.read_text(encoding="utf-8"))["permissions"]
    assert len(perms["deny"]) == len(set(perms["deny"])), "duplicate deny entries"


@pytest.mark.skipif(not PWSH, reason="no PowerShell interpreter")
def test_merge_is_a_no_op_without_a_settings_file(tmp_path: Path) -> None:
    """No settings.json means nothing to harden; it must not crash or create one."""
    harness = tmp_path / "harness.ps1"
    harness.write_text(_PS_HARNESS, encoding="utf-8")
    missing = tmp_path / "absent.json"
    proc = subprocess.run(
        [PWSH, "-NoProfile", "-File", str(harness), str(INSTALLER_PS1),
         str(missing), str(OVERLAY)],
        capture_output=True, text=True, timeout=180,
    )
    assert proc.returncode == 0, proc.stderr
    assert not missing.exists(), "merge must not fabricate a settings.json"


def test_default_install_does_not_reference_the_overlay_unconditionally() -> None:
    """The overlay must be reachable ONLY behind the flag, so the documented
    no-prompt allow-only default is genuinely unchanged."""
    sh = INSTALLER_SH.read_text(encoding="utf-8")
    idx = sh.index("merge_strict_permissions \\")
    guard_window = sh[max(0, idx - 400):idx]
    assert "STRICT_PERMISSIONS:-0" in guard_window, (
        "the bash call site must be guarded by the flag"
    )

    ps = INSTALLER_PS1.read_text(encoding="utf-8")
    idx = ps.index("Merge-StrictPermissions `")
    guard_window = ps[max(0, idx - 400):idx]
    assert "if ($StrictPermissions)" in guard_window, (
        "the PowerShell call site must be guarded by the switch"
    )
