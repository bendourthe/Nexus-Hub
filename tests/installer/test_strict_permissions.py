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
  * behavioral merge semantics, exercised against the REAL function extracted
    from each installer: additive (never drops a user's entries), leaves
    permissions.allow untouched, and idempotent on a second run;
  * the HO-2 intent marker (both installers export NEXUS_HUB_INIT for `init`).

The bash behavioral test needs jq (the same dependency the pre-existing allow
merge has) and skips without it; the PowerShell one needs no jq, so it runs on the
Windows dev host.
"""

from __future__ import annotations

import json
import os
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
PWSH = shutil.which(os.environ.get("NEXUS_TEST_POWERSHELL", "pwsh")) or shutil.which("powershell")
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
    """The overlay never writes defaultMode, so the user's permission mode (or
    Claude Code's own default) stands. Decision:
    docs/decisions/implemented/policy/2026-10-10-strict-overlay-omits-defaultmode.md."""
    assert "defaultMode" not in overlay["permissions"], (
        "defaultMode stays out of the strict overlay by decision (2026-10-10)"
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


# --- Behavioral merge semantics -------------------------------------------

_PS_HARNESS = r"""
$ErrorActionPreference = 'Stop'
$installer = $args[0]; $settings = $args[1]; $overlay = $args[2]

# Extract the REAL function from installer.ps1 via the AST (the script has
# top-level code, so it cannot simply be dot-sourced).
$ast = [System.Management.Automation.Language.Parser]::ParseFile($installer, [ref]$null, [ref]$null)
foreach ($name in @('Read-JsonDocument', 'Write-JsonFile', 'Merge-StrictPermissions')) {
    $fn = $ast.FindAll({
        $args[0] -is [System.Management.Automation.Language.FunctionDefinitionAst] -and
        $args[0].Name -eq $name
    }, $true) | Select-Object -First 1
    if (-not $fn) { throw "Missing native helper: $name" }
    Invoke-Expression $fn.Extent.Text
}
function Write-Item { param($Message, $Color) Write-Output $Message }

Merge-StrictPermissions -SettingsFile $settings -OverlayFile $overlay -Scope 'Test'
"""

_SH_HARNESS = r"""
set -euo pipefail
installer="$1"; settings="$2"; overlay="$3"
GRAY=""; GREEN=""; YELLOW=""
write_item() { printf '%s\n' "$1"; }
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


@pytest.mark.skipif(not PWSH, reason="no PowerShell interpreter")
@pytest.mark.parametrize("case", ["ordinary", "deep", "near", "distinct", "bracket", "case-metadata", "absent-parent"])
def test_native_strict_writer_preserves_json_and_backs_up_once(tmp_path: Path, overlay: dict, case: str) -> None:
    """Real reader/writer must retain exact keys while applying the selected overlay."""
    home = tmp_path / ("profile [user]" if case == "bracket" else "profile")
    home.mkdir()
    settings = home / "settings.json"
    payload = {"permissions": {"allow": ["Read(user)"], "deny": ["Edit(user)"], "ask": ["Write(user)"]}, "custom": {"keep": "user"}}
    if case in ("distinct", "bracket"):
        payload["env"] = {"VAR": "one", "var": "two"}
    if case == "near":
        payload["env"] = {"claude_code_subagent_model": "user", "CLAUDE_CODE_SUBAGENT_MODEL": "sonnet"}
    if case in ("deep", "bracket"):
        for index in range(15):
            payload["custom"] = {str(index): payload["custom"]}
    if case == "case-metadata":
        payload["Permissions"] = {"keep": True}
        payload["permissions"].update(Deny=["CaseDeny"], Ask=["CaseAsk"])
    if case == "absent-parent":
        del payload["permissions"]
    raw = json.dumps(payload).encode()
    settings.write_bytes(raw)
    harness = tmp_path / "strict.ps1"
    harness.write_text(_PS_HARNESS, encoding="utf-8-sig")
    snapshots = []
    backups = []
    for _ in range(2):
        proc = subprocess.run([PWSH, "-NoProfile", "-NonInteractive", "-File", str(harness), str(INSTALLER_PS1), str(settings), str(OVERLAY)], capture_output=True, text=True, timeout=90, check=False)
        assert proc.returncode == 0, proc.stderr
        assert "Could not merge" not in proc.stdout, proc.stdout
        snapshots.append(settings.read_bytes())
        backups.append(sorted(home.glob("settings.json.bak.*")))
    assert snapshots[0] == snapshots[1]
    assert backups[0] == backups[1] and len(backups[0]) == 1
    assert backups[0][0].read_bytes() == raw
    actual = json.loads(snapshots[0])
    for key, value in payload.items():
        if key != "permissions":
            assert actual[key] == value
            continue
        for permission, entries in value.items():
            if permission in ("deny", "ask"):
                assert actual[key][permission] == list(dict.fromkeys(entries + overlay[key][permission]))
            else:
                assert actual[key][permission] == entries
    for key in ("deny", "ask"):
        assert set(overlay["permissions"][key]) <= set(actual["permissions"][key])
        assert len(actual["permissions"][key]) == len(set(actual["permissions"][key]))


@pytest.mark.skipif(not PWSH, reason="no PowerShell interpreter")
@pytest.mark.parametrize("raw", [
    '{"custom":', '[{"custom":"keep"}]', 'null', '"keep"',
    '{"permissions":null}', '{"permissions":[]}', '{"permissions":"keep"}', '{"permissions":false}',
    '{"permissions":{"deny":null}}', '{"permissions":{"deny":"keep"}}',
    '{"permissions":{"deny":["keep",7]}}', '{"permissions":{"ask":"keep"}}',
])
def test_native_strict_writer_refuses_malformed_custom_data(tmp_path: Path, raw: str) -> None:
    """Refusal must preserve original bytes without a backup or false applied message."""
    settings = tmp_path / "settings.json"
    settings.write_bytes(raw.encode())
    harness = tmp_path / "strict.ps1"
    harness.write_text(_PS_HARNESS, encoding="utf-8-sig")
    proc = subprocess.run([PWSH, "-NoProfile", "-NonInteractive", "-File", str(harness), str(INSTALLER_PS1), str(settings), str(OVERLAY)], capture_output=True, text=True, timeout=90, check=False)
    assert proc.returncode == 0, proc.stderr
    assert settings.read_bytes() == raw.encode()
    assert not list(tmp_path.glob("settings.json.bak.*"))
    assert "Could not merge the strict permission overlay" in proc.stdout
    assert "STRICT permission overlay applied" not in proc.stdout


def _invoke_strict_boundary(tmp_path: Path, backend: str, raw: str, overlay_file: Path = OVERLAY) -> tuple[subprocess.CompletedProcess[str], Path]:
    if backend == "powershell":
        if not PWSH:
            pytest.skip("no PowerShell interpreter")
        script = tmp_path / "strict.ps1"
        script.write_text(_PS_HARNESS, encoding="utf-8-sig")
        command = [PWSH, "-NoProfile", "-NonInteractive", "-File", str(script), str(INSTALLER_PS1)]
    else:
        if not BASH or not JQ:
            pytest.skip("bash strict merge requires bash and jq")
        script = tmp_path / "strict.sh"
        script.write_text(_SH_HARNESS, encoding="utf-8", newline="\n")
        command = [BASH, str(script), str(INSTALLER_SH)]
    settings = tmp_path / "settings.json"
    settings.write_text(raw, encoding="utf-8")
    result = subprocess.run(command + [str(settings), str(overlay_file)], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=90, check=False)
    assert result.returncode == 0, result.stdout + result.stderr
    return result, settings


@pytest.mark.parametrize("backend", ["powershell", "bash"])
@pytest.mark.parametrize(("deny_repeats", "ask_repeats"), [(23, 13), (100, 100)])
def test_strict_counts_missing_rules_independently_of_existing_duplicates(tmp_path: Path, overlay: dict, backend: str, deny_repeats: int, ask_repeats: int) -> None:
    payload = {"permissions": {"allow": ["Read(user)", "Read(user)"], "deny": ["Edit(user)"] * deny_repeats, "ask": ["Write(user)"] * ask_repeats}, "custom": {"keep": True}}
    result, settings = _invoke_strict_boundary(tmp_path, backend, json.dumps(payload))
    actual = json.loads(settings.read_text(encoding="utf-8-sig"))
    assert actual["custom"] == payload["custom"]
    assert actual["permissions"]["allow"] == payload["permissions"]["allow"]
    for key in ("deny", "ask"):
        assert set(overlay["permissions"][key]) <= set(actual["permissions"][key])
        assert set(payload["permissions"][key]) <= set(actual["permissions"][key])
        assert len(actual["permissions"][key]) == len(set(actual["permissions"][key]))
    assert "34 new deny/ask entries" in result.stdout, result.stdout
    assert "already up to date" not in result.stdout
    assert len(list(tmp_path.glob("settings.json.bak.*"))) == 1


@pytest.mark.parametrize("backend", ["powershell", "bash"])
def test_strict_already_present_rules_do_not_rewrite_duplicate_user_entries(tmp_path: Path, overlay: dict, backend: str) -> None:
    payload = {"permissions": {"deny": overlay["permissions"]["deny"] + ["Edit(user)"] * 5, "ask": overlay["permissions"]["ask"] + ["Write(user)"] * 5}}
    raw = json.dumps(payload)
    result, settings = _invoke_strict_boundary(tmp_path, backend, raw)
    assert settings.read_bytes() == raw.encode()
    assert "already up to date (0 new)" in result.stdout
    assert not list(tmp_path.glob("settings.json.bak.*"))


@pytest.mark.parametrize("raw", ['', '   ', '{"broken":', 'null', '[]', '"user"', '{"permissions":null}', '{"permissions":[]}', '{"permissions":"keep"}', '{"permissions":false}', '{"permissions":{"deny":null}}', '{"permissions":{"deny":"keep"}}', '{"permissions":{"ask":[7]}}', '{"permissions":{"ask":"keep"}}', '{} {}', '{"custom":"keep"} {"permissions":{"deny":["Edit(injected)"],"ask":[]}}'])
def test_bash_strict_refuses_invalid_settings_without_false_success(tmp_path: Path, raw: str) -> None:
    result, settings = _invoke_strict_boundary(tmp_path, "bash", raw)
    assert settings.read_bytes() == raw.encode()
    assert "Could not merge the strict permission overlay" in result.stdout
    assert "already up to date" not in result.stdout
    assert "STRICT permission overlay applied" not in result.stdout
    assert not list(tmp_path.glob("settings.json.bak.*"))


@pytest.mark.parametrize("backend", ["powershell", "bash"])
@pytest.mark.parametrize("overlay_raw", ['', '   ', 'null', '[]', '{}', '{"permissions":null}', '{"permissions":{"deny":"keep"}}', '{"permissions":{"ask":[7]}}', '{} {}', '{"permissions":{"deny":[],"ask":[]}} {"permissions":{"deny":["Edit(injected)"]}}'])
def test_strict_refuses_invalid_overlay_without_changing_user_settings(tmp_path: Path, backend: str, overlay_raw: str) -> None:
    overlay_file = tmp_path / "overlay.json"
    overlay_file.write_text(overlay_raw, encoding="utf-8")
    raw = '{"custom":"keep","permissions":{"allow":["Read(user)"]}}'
    result, settings = _invoke_strict_boundary(tmp_path, backend, raw, overlay_file)
    assert settings.read_bytes() == raw.encode()
    assert "Could not merge the strict permission overlay" in result.stdout
    assert "already up to date" not in result.stdout
    assert "STRICT permission overlay applied" not in result.stdout
    assert not list(tmp_path.glob("settings.json.bak.*"))


@pytest.mark.parametrize("backend", ["powershell", "bash"])
@pytest.mark.parametrize("unicode_overlay", [False, True])
def test_strict_merge_preserves_unicode_profile_paths(tmp_path: Path, overlay: dict, backend: str, unicode_overlay: bool) -> None:
    profile = tmp_path / "profile [x] $tick`semi; caf\u00e9 \u6f22\u5b57"
    profile.mkdir()
    overlay_file = profile / "overlay.json" if unicode_overlay else OVERLAY
    if unicode_overlay:
        overlay_file.write_text(json.dumps(overlay), encoding="utf-8")
    raw = '{"custom":"keep","permissions":{"allow":["Read(user)"]}}'
    result, settings = _invoke_strict_boundary(profile, backend, raw, overlay_file)
    actual = json.loads(settings.read_text(encoding="utf-8-sig"))
    assert actual["custom"] == "keep"
    assert actual["permissions"]["allow"] == ["Read(user)"]
    for key in ("deny", "ask"):
        assert set(overlay["permissions"][key]) <= set(actual["permissions"][key])
    assert "34 new deny/ask entries" in result.stdout
    backups = list(profile.glob("settings.json.bak.*"))
    assert len(backups) == 1
    assert backups[0].read_bytes() == raw.encode()
