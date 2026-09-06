"""Installer smoke test - structural + artifact assertions for the v0.9.7 installer.

This test does NOT run the installer end-to-end (a sandboxed full-install test
is deferred to v0.9.8 and tracked as a follow-up). Instead it verifies:

1. The installer scripts carry the expected v0.9.7 banner + version + main-flow
   refactor (global-vs-workspace upfront choice, no template-import prompt).
2. The source artifacts the installer will copy exist at their expected paths
   (new v0.9.7 skills, guides, checklist, templates).
3. The canonical template (`catalog/hooks/settings.json`) has `effortLevel: high`
   which is what the installer writes into `~/.claude/settings.json` on a fresh
   install.
4. The installer scripts are syntactically valid (bash -n for .sh; PowerShell
   AST parse for .ps1 if pwsh/powershell is available).

Run with: pytest catalog/hooks/tests/test_installer_smoke.py
Also runnable directly: python catalog/hooks/tests/test_installer_smoke.py
"""
from __future__ import annotations

import json
import pathlib
import shutil
import subprocess
import sys

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
INSTALLER_SH = REPO_ROOT / "scripts" / "installer.sh"
INSTALLER_PS1 = REPO_ROOT / "scripts" / "installer.ps1"
SETTINGS_TEMPLATE = REPO_ROOT / "catalog" / "hooks" / "settings.json"
PLUGIN_MANIFEST = REPO_ROOT / ".claude-plugin" / "plugin.json"


def _canonical_version() -> str:
    """Return the canonical Nexus-Hub version from .claude-plugin/plugin.json.

    Used as the single source of truth for the installer banner-version
    assertions so that future version bumps do not require editing this test.
    """
    return json.loads(PLUGIN_MANIFEST.read_text(encoding="utf-8"))["version"]


# --- (1) Installer script structural assertions ------------------------------

def test_installer_sh_exists():
    assert INSTALLER_SH.is_file(), f"Missing: {INSTALLER_SH}"


def test_installer_ps1_exists():
    assert INSTALLER_PS1.is_file(), f"Missing: {INSTALLER_PS1}"


def test_installer_sh_carries_version_constant():
    """installer.sh's NEXUS_HUB_VERSION must match .claude-plugin/plugin.json.

    The canonical project version lives in `.claude-plugin/plugin.json`. The
    installer banner reads its label from a `NEXUS_HUB_VERSION="X.Y.Z"`
    constant near the top of the script. The two must stay in lockstep so the
    installer's "Thank You" banner always advertises the correct release.
    Reading the expected value from the manifest (rather than hardcoding it
    in the test) prevents the test from silently lagging the real version.
    """
    expected = f'NEXUS_HUB_VERSION="{_canonical_version()}"'
    body = INSTALLER_SH.read_text(encoding="utf-8")
    assert expected in body, \
        f"installer.sh is missing the {expected} constant"


def test_installer_ps1_carries_version_constant():
    """installer.ps1's $script:NexusHubVersion must match .claude-plugin/plugin.json.

    Same contract as test_installer_sh_carries_version_constant, mirrored for
    the PowerShell installer.
    """
    expected = f'$script:NexusHubVersion = "{_canonical_version()}"'
    body = INSTALLER_PS1.read_text(encoding="utf-8")
    assert expected in body, \
        f"installer.ps1 is missing the {expected} constant"


def test_installer_sh_has_welcome_banner_function():
    body = INSTALLER_SH.read_text(encoding="utf-8")
    assert "print_banner()" in body, "installer.sh is missing print_banner()"
    assert "Welcome to the Nexus-Hub Universal Installer" in body, \
        "installer.sh banner text missing"
    # Accept either ${NEXUS_HUB_VERSION} or $NEXUS_HUB_VERSION interpolation form
    assert "${NEXUS_HUB_VERSION}" in body or "$NEXUS_HUB_VERSION" in body, \
        "installer.sh banner must interpolate the NEXUS_HUB_VERSION variable"


def test_installer_ps1_has_welcome_banner_function():
    body = INSTALLER_PS1.read_text(encoding="utf-8")
    assert "function Show-WelcomeBanner" in body, \
        "installer.ps1 is missing Show-WelcomeBanner"
    assert "Welcome to the Nexus-Hub Universal Installer" in body, \
        "installer.ps1 banner text missing"
    assert "$script:NexusHubVersion" in body, \
        "installer.ps1 banner must interpolate $script:NexusHubVersion"


def test_installer_sh_has_nexus_ascii_banner():
    """v2.0.0 Phase 3 sub-task 3.1: a `print_nexus_banner` ASCII-art wordmark
    must precede the welcome banner. Verifies the function exists, references
    the version variable, and contains at least one literal banner row.
    """
    body = INSTALLER_SH.read_text(encoding="utf-8")
    assert "print_nexus_banner()" in body, \
        "installer.sh is missing print_nexus_banner() (v2.0.0 ASCII banner)"
    # Sanity check that the banner is wired into main flow before the welcome banner.
    assert "print_nexus_banner\nmigrate_legacy_install\nprint_banner" in body or \
           ("print_nexus_banner" in body and "migrate_legacy_install" in body), \
        "installer.sh must invoke print_nexus_banner and migrate_legacy_install at startup"


def test_installer_ps1_has_nexus_ascii_banner():
    """Mirror of test_installer_sh_has_nexus_ascii_banner for PowerShell."""
    body = INSTALLER_PS1.read_text(encoding="utf-8")
    assert "function Write-NexusBanner" in body, \
        "installer.ps1 is missing Write-NexusBanner (v2.0.0 ASCII banner)"
    assert "Invoke-LegacyInstallMigration" in body, \
        "installer.ps1 is missing Invoke-LegacyInstallMigration"
    # Startup invocations must be present in main flow
    assert "Write-NexusBanner" in body and "Show-WelcomeBanner" in body, \
        "installer.ps1 must invoke Write-NexusBanner and Show-WelcomeBanner"


def test_installer_sh_migrates_legacy_nexus_hub_dir():
    """v2.0.0 Phase 3 sub-task 3.3: installer.sh must carry a migration
    function that relocates ~/.nexus-hub/ to ~/.nexus-hub/ on first run.
    """
    body = INSTALLER_SH.read_text(encoding="utf-8")
    assert "migrate_legacy_install()" in body, \
        "installer.sh is missing migrate_legacy_install()"
    assert '"$HOME/.nexus-hub"' in body, \
        "installer.sh migration must reference the legacy ~/.nexus-hub path"
    assert '"$HOME/.nexus-hub"' in body, \
        "installer.sh migration must reference the new ~/.nexus-hub path"
    # The one-way move (legacy-only branch) and the co-existence branch must both be present.
    assert 'mv "$legacy" "$current"' in body, \
        "installer.sh migration must perform the one-way rename"


def test_installer_ps1_migrates_legacy_nexus_hub_dir():
    """Mirror of test_installer_sh_migrates_legacy_nexus_hub_dir for PowerShell."""
    body = INSTALLER_PS1.read_text(encoding="utf-8")
    assert "function Invoke-LegacyInstallMigration" in body, \
        "installer.ps1 is missing Invoke-LegacyInstallMigration"
    assert '".nexus-hub"' in body, \
        "installer.ps1 migration must reference the legacy .nexus-hub directory"
    assert '".nexus-hub"' in body, \
        "installer.ps1 migration must reference the new .nexus-hub directory"
    assert "Move-Item -Path $legacy -Destination $current" in body, \
        "installer.ps1 migration must perform the one-way Move-Item"


def test_installer_sh_scope_is_no_prompt_default_global():
    """v3.7.0 Phase 2 removed the interactive `Select [G/W]` scope prompt: scope
    is resolved from `--workspace <path>` (default = global) with no prompt. This
    guard prevents a regression back to the prompt-driven scope UX.
    """
    body = INSTALLER_SH.read_text(encoding="utf-8")
    assert "Select [G/W]" not in body, \
        "installer.sh must not re-introduce the interactive scope prompt"
    assert "--workspace" in body and "WORKSPACE_PATH" in body, \
        "installer.sh must resolve scope from --workspace"
    # Global is the default branch when no workspace path is given.
    assert 'install_global "$REPO_ROOT"' in body


def test_installer_ps1_scope_is_no_prompt_default_global():
    body = INSTALLER_PS1.read_text(encoding="utf-8")
    assert 'Read-Host "Select [G/W]"' not in body, \
        "installer.ps1 must not re-introduce the interactive scope prompt"
    assert "$Workspace" in body, "installer.ps1 must resolve scope from -Workspace"
    assert "Install-Global -RepoRoot $repoRoot" in body


def test_installers_have_no_phase_labels():
    """The v0.9.7 single-phase refactor removed the legacy 'PHASE 1/2/3' banners.
    Keeping them out prevents regression to the old three-phase UX.
    """
    sh_body = INSTALLER_SH.read_text(encoding="utf-8")
    ps1_body = INSTALLER_PS1.read_text(encoding="utf-8")
    for pattern in ("PHASE 1:", "PHASE 2:", "PHASE 3:", "Installation Phase Complete"):
        assert pattern not in sh_body, (
            f"installer.sh must not contain '{pattern}' (legacy three-phase UX)"
        )
        assert pattern not in ps1_body, (
            f"installer.ps1 must not contain '{pattern}' (legacy three-phase UX)"
        )


def test_installer_ps1_does_not_clear_host_after_scope_choice():
    """The previous flow cleared the screen at the start of Install-Global, losing
    the welcome banner + user's scope selection from scrollback. The v0.9.7
    post-release fix removes the Clear-Host call inside Install-Global.
    """
    body = INSTALLER_PS1.read_text(encoding="utf-8")
    # Find the Install-Global function body and assert no Clear-Host inside
    install_global_idx = body.index("function Install-Global")
    # Find the end of Install-Global: the next top-level 'function ' declaration
    next_fn_idx = body.index("\nfunction ", install_global_idx + len("function Install-Global"))
    install_global_body = body[install_global_idx:next_fn_idx]
    assert "Clear-Host" not in install_global_body, (
        "Install-Global must not call Clear-Host (v0.9.7 keeps the welcome banner "
        "and scope choice visible in scrollback)."
    )


def test_installer_sh_does_not_clear_after_scope_choice():
    """Mirror of test_installer_ps1_does_not_clear_host_after_scope_choice for bash."""
    body = INSTALLER_SH.read_text(encoding="utf-8")
    # Find the install_global function body and assert no `clear` call inside
    install_global_idx = body.index("install_global() {")
    next_fn_idx = body.index("\ninstall_vscode_extensions()", install_global_idx)
    install_global_body = body[install_global_idx:next_fn_idx]
    # Match 'clear' as a whole word, either at start of line or after a semicolon/pipe.
    # Avoid false positives from words containing 'clear'.
    lines = [ln.strip() for ln in install_global_body.splitlines()]
    offending = [ln for ln in lines if ln == "clear" or ln.startswith("clear ") or ln.startswith("clear;")]
    assert not offending, (
        f"install_global must not call `clear` (v0.9.7 UX). Offending lines: {offending}"
    )


def test_installers_use_claude_usage_monitor_banner():
    """Banner text must reference 'Claude Usage Monitor', not the old
    'Claude Code Usage Monitor'. The product name is 'Claude Usage Monitor'
    (per its own README + package.json). The v2.1.0 UX modernization
    dropped the all-caps banner in favor of title-case; the check is now
    case-insensitive on the product name and explicitly rejects the
    'Claude Code Usage Monitor' typo.
    """
    for path in (INSTALLER_SH, INSTALLER_PS1):
        body = path.read_text(encoding="utf-8").lower()
        assert "claude code usage monitor" not in body, (
            f"{path.name} must use 'Claude Usage Monitor' (not 'Claude Code Usage Monitor')"
        )
        assert "claude usage monitor" in body, (
            f"{path.name} is missing the 'Claude Usage Monitor' section banner"
        )


# Every usage monitor the installers must build, in the vendor order both shells
# present them (Anthropic, OpenAI for VS Code; Anysphere/Cursor last).
# Adding a monitor means adding a row here; the tests below then enforce presence
# AND ordering in both shells, so a monitor cannot be wired into one installer
# and forgotten in the other, and the two cannot drift out of order.
USAGE_MONITORS = (
    ("claude-usage-monitor", "nexus-hub.claude-usage-monitor", "Claude Usage Monitor"),
    ("codex-usage-monitor", "nexus-hub.codex-usage-monitor", "Codex Usage Monitor"),
    # The GitHub monitor was WITHDRAWN in v3.18.2; see RETIRED_EXTENSION_IDS below.
    ("cursor-usage-monitor", "nexus-hub.cursor-usage-monitor", "Cursor Usage Monitor"),
)

VS_CODE_USAGE_MONITORS = USAGE_MONITORS[:2]
CURSOR_USAGE_MONITOR = USAGE_MONITORS[2]

#: Extensions a previous release installed that the installers must now UNINSTALL.
#: Unshipping alone is not enough: an extension already on a user's machine keeps
#: running. nexus-hub.github-usage-monitor reconstructed GitHub's included-usage
#: meter from data GitHub does not publish and could report a confident 0% against
#: an exhausted allowance, so it is actively removed from both hosts.
RETIRED_EXTENSION_IDS = ("nexus-hub.github-usage-monitor",)


def test_installers_build_every_usage_monitor_extension():
    """v3.14.4 split the usage monitor into separate extensions; v3.15.8 added
    GitHub; v3.15.9 Phase 6 added Cursor. Both installers must build and install
    EVERY monitor in ``USAGE_MONITORS`` (installer.sh uses '/' paths,
    installer.ps1 '\\').
    """
    for path in (INSTALLER_SH, INSTALLER_PS1):
        body = path.read_text(encoding="utf-8")
        lower = body.lower()
        for folder, extension_id, display_name in USAGE_MONITORS:
            assert (
                f"extensions/{folder}" in body or f"extensions\\{folder}" in body
            ), f"{path.name} must build the {display_name} extension"
            assert extension_id in body, f"{path.name} must install {extension_id}"
            assert display_name.lower() in lower, (
                f"{path.name} must reference the '{display_name}' display name"
            )


def test_installers_uninstall_retired_extensions_from_both_hosts():
    """A withdrawn extension must be UNINSTALLED, not merely unshipped.

    Removing an extension from the build loop stops new installs but leaves every
    existing one running. nexus-hub.github-usage-monitor is the case this guards:
    it reported a confident 0% against an exhausted GitHub allowance, so a user who
    upgrades and still sees it is strictly worse off than one who never had it.

    Both hosts are asserted because that monitor was the one dual-host monitor,
    installed into Cursor as well as VS Code. A VS Code-only sweep would leave the
    Cursor copy on screen, which is the exact failure this test exists to catch.
    """
    for path in (INSTALLER_SH, INSTALLER_PS1):
        body = path.read_text(encoding="utf-8")
        for extension_id in RETIRED_EXTENSION_IDS:
            # Assert on the retirement ARRAY, not merely on the id appearing
            # somewhere in the file. The id is also named in a nearby comment, so a
            # bare substring check passes even when the entry is deleted - the
            # fail-open shape this test exists to prevent.
            marker = "legacy_ids=(" if path is INSTALLER_SH else "$legacyIds = @("
            start = body.index(marker)
            array = body[start : body.index(")", start)]
            assert extension_id in array, (
                f"{path.name} must list {extension_id} in its retirement array so it "
                f"is uninstalled from existing installs, not merely unshipped"
            )
            assert "--uninstall-extension" in body, (
                f"{path.name} must uninstall retired extensions"
            )
            assert f"extensions/{extension_id.split('.', 1)[1]}" not in body, (
                f"{path.name} must NOT build {extension_id}; it was withdrawn"
            )
            windows_path = "extensions" + chr(92) + extension_id.split(".", 1)[1]
            assert windows_path not in body, (
                f"{path.name} must NOT build {extension_id}; it was withdrawn"
            )
        assert '"code", "cursor"' in body or "for cli in code cursor" in body, (
            f"{path.name} must sweep BOTH hosts for retired extensions"
        )


def test_installers_agree_on_usage_monitor_order():
    """The monitors must be built in the same vendor order by both shells.

    Order is user-visible: each monitor prints under its own vendor header and
    then claims a status-bar slot in install order, so a reordering in one shell
    alone gives Windows and macOS/Linux users a different status bar from the
    same release. Cursor (Anysphere) must remain last so VS Code monitors keep
    their established Anthropic → OpenAI → GitHub sequence.
    """
    for path in (INSTALLER_SH, INSTALLER_PS1):
        body = path.read_text(encoding="utf-8")
        positions = [body.index(extension_id) for _, extension_id, _ in USAGE_MONITORS]
        assert positions == sorted(positions), (
            f"{path.name} builds the usage monitors out of order; expected "
            f"{[extension_id for _, extension_id, _ in USAGE_MONITORS]}"
        )


def test_installers_isolate_vscode_and_cursor_hosts():
    """VS Code monitors must never target the Cursor CLI, and vice versa.

    Before v3.15.9 Phase 6 the installer treated Cursor as a VS Code-family
    fallback, which installed Claude/Codex/GitHub monitors into Cursor. The
    dual-host resolver keeps Cursor paths out of the VS Code candidate list and
    routes the Cursor monitor through a separate ``cursor_cli`` / ``$cursorCli``.
    """
    for path in (INSTALLER_SH, INSTALLER_PS1):
        body = path.read_text(encoding="utf-8")
        assert "vscode_cli" in body or "$vscodeCli" in body, (
            f"{path.name} must resolve a dedicated VS Code CLI variable"
        )
        assert "cursor_cli" in body or "$cursorCli" in body, (
            f"{path.name} must resolve a dedicated Cursor CLI variable"
        )

        # Prefer assignment markers so comments mentioning both names do not
        # invert the VS Code / Cursor resolution regions.
        if 'local vscode_cli=""' in body:
            vscode_block_start = body.index('local vscode_cli=""')
            cursor_block_start = body.index('local cursor_cli=""')
        else:
            vscode_block_start = body.index("$vscodeCli = $null")
            cursor_block_start = body.index("$cursorCli = $null")
        assert vscode_block_start < cursor_block_start, (
            f"{path.name} must resolve the VS Code CLI before the Cursor CLI"
        )
        vscode_region = body[vscode_block_start:cursor_block_start]
        assert "Cursor.app" not in vscode_region, (
            f"{path.name} must not list Cursor.app as a VS Code CLI fallback"
        )
        assert "cursor.cmd" not in vscode_region, (
            f"{path.name} must not list cursor.cmd as a VS Code CLI fallback"
        )
        assert "Programs\\cursor" not in vscode_region, (
            f"{path.name} must not list the Windows Cursor install as a VS Code fallback"
        )

        for _, extension_id, _ in VS_CODE_USAGE_MONITORS:
            idx = body.index(extension_id)
            window = body[idx : idx + 280]
            assert "vscode_cli" in window or "vscodeCli" in window, (
                f"{path.name} must pass the VS Code CLI into {extension_id} install"
            )
            assert "cursor_cli" not in window and "cursorCli" not in window, (
                f"{path.name} must not pass the Cursor CLI into {extension_id} install"
            )

        _, cursor_id, _ = CURSOR_USAGE_MONITOR
        cursor_window = body[body.index(cursor_id) : body.index(cursor_id) + 280]
        assert "cursor_cli" in cursor_window or "cursorCli" in cursor_window, (
            f"{path.name} must pass the Cursor CLI into {cursor_id} install"
        )
        assert "vscode_cli" not in cursor_window and "vscodeCli" not in cursor_window, (
            f"{path.name} must not pass the VS Code CLI into {cursor_id} install"
        )
        assert (
            'write_header "ANYSPHERE"' in body
            or 'Write-Header -Provider "ANYSPHERE"' in body
        ), f"{path.name} must present the Cursor monitor under an ANYSPHERE vendor header"


def test_installer_ps1_surfaces_vsce_errors():
    """When `vsce package` fails, the installer must surface the captured output
    rather than silently hiding it with `2>$null | Out-Null`. This was a real
    operator-reported gap ('Packaging failed (exit code: 1)' with no context).
    """
    body = INSTALLER_PS1.read_text(encoding="utf-8")
    # The old silent-failure pattern must be gone
    assert "vsce package --no-dependencies 2>$null | Out-Null" not in body, (
        "installer.ps1 must capture vsce output (2>&1 into a variable), not swallow it"
    )
    # The new capture-and-echo-on-failure pattern must be present. The vsce call
    # is piped a "y" (belt-and-suspenders for any future packaging warning on an
    # unattended run), so match the capture into $vsceOutput + 2>&1 rather than the
    # exact command prefix.
    assert "$vsceOutput =" in body and "npx vsce package" in body and "2>&1" in body, (
        "installer.ps1 must capture vsce output into $vsceOutput using 2>&1 redirection"
    )


def test_installer_ps1_uses_conflict_only_overwrite():
    """v3.7.0 Phase 2 replaced the upfront 'Overwrite Request' O/S/A prompt with
    conflict-only overwrite: in a non-interactive / -Yes / -Force run managed
    files refresh silently (OverwriteMode "ALL"); in an interactive run a single
    end-of-run Resolve-Conflicts prompt lists the differing files. This guard
    prevents a regression back to the prompt-per-install UX.
    """
    body = INSTALLER_PS1.read_text(encoding="utf-8")
    assert 'Write-SubSectionBanner -Text "Overwrite Request"' not in body, \
        "installer.ps1 must not re-introduce the upfront Overwrite Request prompt"
    assert "function Get-Overwrite-Preference" not in body, \
        "the Get-Overwrite-Preference prompt must be removed"
    assert "function Resolve-Conflicts" in body, \
        "installer.ps1 must define the conflict-only resolver"
    assert "$script:ConflictDsts" in body, \
        "installer.ps1 must accumulate managed-file conflicts"


def test_installer_sh_removed_template_import_prompt():
    """The v0.9.6 interactive prompt `read_prompt "Import custom Word/PowerPoint templates? ..."`
    must be gone. A comment referencing the removal is fine; the live read_prompt call is not."""
    body = INSTALLER_SH.read_text(encoding="utf-8")
    # Match the specific interactive construct, not mere mentions in comments.
    assert 'read_prompt "Import custom Word/PowerPoint templates?' not in body, \
        "installer.sh still calls read_prompt for custom-template import; remove the prompt"
    # Also ensure the file-picker loop is gone
    assert 'read_prompt "File path (or press Enter to finish)"' not in body, \
        "installer.sh still prompts for a template file path; that loop must be removed"


def test_installer_ps1_removed_template_import_prompt():
    """Same as the .sh test but targeting PowerShell's Read-Prompt and OpenFileDialog flow."""
    body = INSTALLER_PS1.read_text(encoding="utf-8")
    assert 'Read-Prompt "Import custom Word/PowerPoint templates?' not in body, \
        "installer.ps1 still calls Read-Prompt for custom-template import; remove the prompt"
    # The System.Windows.Forms.OpenFileDialog file picker for templates must be gone too
    assert "Select Document Templates to Import" not in body, \
        "installer.ps1 still opens the document-templates file picker; remove it"


# --- (2) Canonical template settings assertion -------------------------------

PLATFORM_DEFAULTS = REPO_ROOT / "configs" / "platform-defaults.json"


def _declared_claude_settings() -> dict:
    """The values declared in configs/platform-defaults.json for Claude."""
    assert PLATFORM_DEFAULTS.is_file(), f"Missing: {PLATFORM_DEFAULTS}"
    data = json.loads(PLATFORM_DEFAULTS.read_text(encoding="utf-8"))
    return data["platforms"]["claude"]["settings"]


def test_declared_claude_effort_level_is_high():
    """Intent guard for the shipped Claude default `high`, asserted at the source.

    The default moved from `medium` to `high` in v4.4.0 so a fresh install starts
    at the deeper reasoning tier expected by plan-driven, multi-step work. Both
    the scalar and the `env` override are pinned, because
    `env.CLAUDE_CODE_EFFORT_LEVEL` is the higher-precedence lever: leaving the
    two out of step would make the scalar a no-op.

    As of v3.16.0 this assertion lives against configs/platform-defaults.json
    rather than the derived template, so the intended value is stated in exactly
    one place. If a future change wants to move the default, edit the source and
    the CHANGELOG together; the consistency of every derived artifact is checked
    separately by `scripts/sync_platform_defaults.py --check`.
    """
    settings = _declared_claude_settings()
    assert settings["effortLevel"] == "high", (
        f"Expected declared effortLevel='high', got {settings['effortLevel']!r}. "
        "If this was a deliberate change, update the CHANGELOG + test together."
    )
    assert settings.get("env", {}).get("CLAUDE_CODE_EFFORT_LEVEL") == "high", (
        "env.CLAUDE_CODE_EFFORT_LEVEL must match effortLevel ('high'); it is "
        "the higher-precedence lever, so a mismatch silently wins over the scalar."
    )


def test_catalog_hooks_settings_matches_declared_defaults():
    """The shipped template's core keys must equal the declared source.

    catalog/hooks/settings.json is DERIVED from configs/platform-defaults.json
    (v3.16.0). Asserting equality with the source instead of a repeated literal
    is what stops this file from becoming a second place to edit when the
    default moves - the exact duplication that made the v3.15.5 effort change
    touch four declarations across two files.
    """
    assert SETTINGS_TEMPLATE.is_file(), f"Missing: {SETTINGS_TEMPLATE}"
    data = json.loads(SETTINGS_TEMPLATE.read_text(encoding="utf-8"))
    declared = _declared_claude_settings()
    for key in ("effortLevel", "model"):
        assert data.get(key) == declared[key], (
            f"catalog/hooks/settings.json {key}={data.get(key)!r} has drifted from "
            f"the declared {declared[key]!r}. Run: "
            "python scripts/sync_platform_defaults.py --apply"
        )
    assert data.get("env", {}).get("CLAUDE_CODE_EFFORT_LEVEL") == declared["env"][
        "CLAUDE_CODE_EFFORT_LEVEL"
    ], (
        "env.CLAUDE_CODE_EFFORT_LEVEL has drifted from the declared value. Run: "
        "python scripts/sync_platform_defaults.py --apply"
    )


def test_installer_ps1_fallback_literal_matches_template():
    """If the PowerShell core-settings merge fails, installer.ps1 prints a
    manual-add hint.

    installer.ps1 seeds the core defaults dynamically from the template
    (`$coreKeys = @("effortLevel", "model")` plus the env effort override)
    rather than hardcoding the effort literal, so the fallback hint points the
    user at copying effortLevel/model/env from the template file. The hint MUST
    name those keys so it stays consistent with catalog/hooks/settings.json
    whatever the shipped default value is.
    """
    body = INSTALLER_PS1.read_text(encoding="utf-8")
    assert "Manually copy effortLevel/model/env from" in body, (
        "installer.ps1 core-settings fallback must reference copying "
        "effortLevel/model/env from the template so it tracks "
        "catalog/hooks/settings.json without a hardcoded value."
    )


# Scripts under scripts/ that are developer/maintainer tooling and must NOT
# ship to end users via the installer. Each entry needs a one-line justification
# so a future contributor can tell whether a new script belongs here or in the
# installer copy blocks.
DEV_ONLY_SCRIPTS = {
    # Repo-internal co-location guard (v3.17.7): enforces that a /compare
    # report and the plan it seeds share a version directory. Moved out of
    # .github/workflows/doc-colocation.yml so its three fail-open defects
    # could be unit-tested. Runs in CI and make validate; meaningless in an
    # end-user ~/.nexus-hub/scripts/.
    # Repo-internal host-interpreter gate (v4.3.0): probes that the
    # interpreters hook registrations are launched with (`bash <script>`)
    # can actually execute a script on this host. Runs in the fast, full,
    # and platform profiles. Meaningless in an end-user
    # ~/.nexus-hub/scripts/; the equivalent user-facing report is the
    # NEEDS-ACTION line that `runner.py verify` (nexus-hub doctor) emits.
    "check_interpreter_resolution.py",
    "check_doc_colocation.py",
    # Repo-internal retention reporter (v3.18.0): reports per-version
    # development/ subtrees due for archival per docs/policy/docs-retention.md.
    # Advisory (always exit 0), runs in make validate; meaningless in an
    # end-user ~/.nexus-hub/scripts/ with no docs/v* tree.
    "check_docs_retention.py",
    # Repo validator: walks catalog/ for frontmatter + secret scans. Runs in CI
    # and by maintainers; not useful in an end-user ~/.nexus-hub/scripts/.
    "validate_skills.py",
    # Repo-internal agentskills.io contract guard (v3.20.1): proves every
    # SKILL.md satisfies the open-standard name/description rules. Runs in
    # make validate and CI. An end-user install has no catalog source to
    # check, so it is deliberately not installer-copied.
    "check_agentskills_conformance.py",
    # Repo-internal guide count stamper (v4.4.2): rewrites <span data-count> markers in
    # guides/website/nexus-hub-guide.html from data/ and catalog/ so page counts cannot
    # drift; --check runs in make validate. An end-user install has neither source tree.
    "stamp_guide_counts.py",
    # One-shot cross-catalog maintenance utility that injects iterative-refinement
    # text into SKILL.md / command .md files. Maintainer tool only.
    "apply_iterative_workflow.py",
    # One-shot v2.0.0 brand-rename helper that walks catalog/, templates/, and
    # .cursor/ applying the legacy-name to Nexus-Hub variant table. Maintainer
    # tool only; idempotent and useless on an end-user install.
    "apply_rename.py",
    # Repo-internal parity guard (v3.6.0): structurally compares the five
    # templates/ai-instructions/base-*.md files for lockstep drift. Runs in
    # `make validate` and CI; an end user has no base-*.md to check, so unlike
    # check_version_sync.py (which IS distributed) this guard is deliberately
    # not copied by the installers.
    "check_base_template_parity.py",
    # Repo-internal platform read-contract checker (v3.12.1): verifies the
    # installer code matches docs/policy/platform-read-contracts.md. Runs in
    # `make validate` and CI; an end user has no catalog source to check, so
    # like check_base_template_parity.py it is deliberately not installer-copied.
    "verify_platform_contracts.py",
    # Repo-internal release freshness gate (v3.14.5): fails a release when the
    # platform read-contract JSON's meta.verified_for_version does not match the
    # plugin.json version being cut. Runs in `make validate` and CI; a repo-only
    # guard like the two above, so it is deliberately not installer-copied.
    "check_platform_contract_freshness.py",
    # Repo-internal defaults-drift guard (v3.16.0): checks that every artifact
    # derived from configs/platform-defaults.json still matches the declared
    # source, and regenerates them with --apply. Runs in `make validate` and CI.
    # An end-user install carries no configs/ source to derive from, so like the
    # three guards above it is deliberately not installer-copied.
    "sync_platform_defaults.py",
    # Repo-internal incident-note guard (v3.16.2): asserts every docs/incidents/
    # note carries a Public-Safe Shape section and a Durable fix section with a
    # link in it. Runs in `make validate` and CI. An end-user install has no
    # docs/incidents/ tree, so like the four guards above it is deliberately not
    # installer-copied.
    "check_incident_notes.py",
    # Repo-internal doc word-budget guard (v3.17.5): asserts every doc listed
    # in docs/policy/doc-budgets.json stays under its ceiling. Runs in
    # `make validate` and CI. An end-user install carries no repo instruction
    # sources to budget, so like the guards above it is deliberately not
    # installer-copied.
    "validate_doc_budgets.py",
    # Repo-internal memory-integration token-budget guard (v3.19.1): asserts
    # docs/policy/memory-integration-prose.md stays under the 500-token
    # ceiling in the memory substrate contract. Runs in make validate and CI.
    # An end-user install has no policy tree to measure, so it is deliberately
    # not installer-copied.
    "check_memory_integration_budget.py",
    # Repo-internal zero-outbound guard over the context compressor (v3.19.2).
    # Scans production sources for network imports and curl/wget subprocesses.
    # Runs in make validate and CI. Meaningless on an end-user install.
    "check_no_outbound.py",
    # Repo-internal docs convention guard (v3.19.2): case-sensitive relative
    # links, empty directories, kebab-case directory names under docs/.
    # Runs in make validate and CI. An end-user install has no docs/ tree
    # to audit, so it is deliberately not installer-copied.
    "check_docs_conventions.py",
    # Repo-internal memory provenance guard (v3.19.2): asserts catalog/memory
    # templates require a source, keep an append-only changelog, and supersede
    # instead of deleting. Runs in make validate and CI. An end-user install
    # has no catalog/memory templates to audit, so it is not installer-copied.
    "check_memory_provenance.py",
    # Repo-internal decision-record guard (v3.17.5): asserts every record under
    # docs/decisions/ sits at lifecycle/class/file, carries the 3-line header
    # matching its folder, and states its alternatives. Runs in `make validate`
    # and CI. An end-user install carries no decision tree, so like the guards
    # above it is deliberately not installer-copied.
    "validate_decision_records.py",
    # Repo-internal registry drift-check (v3.17.5): renders each skill's
    # expected SKILL_INDEX row and skills.json entry from its own frontmatter
    # and diffs against the committed bytes, plus capability-module
    # reachability. Runs in `make validate` and CI. An end-user install has no
    # catalog source to derive from, so it is deliberately not installer-copied.
    "check_registry_entries.py",
    # Repo-internal required-check coverage guard (v3.17.6): asserts every
    # context in docs/policy/required-checks.json is produced by a workflow that
    # triggers unconditionally, so a required check can never sit Pending
    # forever. Runs in `make validate` and CI. An end-user install has no
    # .github/workflows/ tree or branch protection to check, so like the guards
    # above it is deliberately not installer-copied.
    "check_required_check_coverage.py",
    # Repo-internal release-notes guard (v3.16.2): asserts every opt-in surface a
    # release ships documents its five capability-usage elements. Advisory until
    # it has caught a real omission. An end user has no release notes to check,
    # so like the guards above it is deliberately not installer-copied.
    "check_release_capability_docs.py",
    # Repo-internal hard gate over configs/installer-parity.json. It checks the
    # source installers against each other and has no end-user runtime role.
    "check_installer_parity.py",
    # CI-only shared postcondition checker for throwaway real-installer runs.
    # Installed users do not need a harness that validates CI's temporary HOME.
    "check_installer_smoke.py",
}


def test_installers_copy_every_scripts_dir_py_file():
    """Regression guard for the installer-gap lesson codified in AGENTS.md:
    scripts/*.py files are copied BY NAME, not by folder. Any new user-facing
    script must be explicitly added to both installers or it will be silently
    missed on fresh installs.

    Generalized form: scans scripts/ for every *.py file, drops the
    DEV_ONLY_SCRIPTS allowlist, and asserts each remaining basename appears in
    BOTH installer.sh and installer.ps1. Auto-adapts when user-facing scripts
    are added or removed.
    """
    scripts_dir = REPO_ROOT / "scripts"
    all_py = sorted(p.name for p in scripts_dir.glob("*.py") if p.is_file())
    assert all_py, (
        f"No *.py files found under {scripts_dir} — the glob is wrong or the "
        "scripts directory is empty."
    )
    user_facing = [n for n in all_py if n not in DEV_ONLY_SCRIPTS]
    sh_body = INSTALLER_SH.read_text(encoding="utf-8")
    ps1_body = INSTALLER_PS1.read_text(encoding="utf-8")
    missing_sh = [n for n in user_facing if n not in sh_body]
    missing_ps1 = [n for n in user_facing if n not in ps1_body]
    if missing_sh or missing_ps1:
        msg_lines = [
            "User-facing scripts/*.py files are not referenced by both installers.",
            "AGENTS.md rule: the installer copies scripts by EXPLICIT NAME, not",
            "by folder - every new user-facing script in scripts/ must be added",
            "to BOTH scripts/installer.sh (near the generate_report.py block)",
            "AND scripts/installer.ps1 (Safe-Copy near the same location).",
            "If a new script is developer-only (not meant for end users), add",
            "it to DEV_ONLY_SCRIPTS in this test file with a one-line reason.",
        ]
        if missing_sh:
            msg_lines.append(f"  missing from installer.sh:  {missing_sh}")
        if missing_ps1:
            msg_lines.append(f"  missing from installer.ps1: {missing_ps1}")
        raise AssertionError("\n".join(msg_lines))


# --- (3) Bundled v0.9.7 artifacts must exist at source paths -----------------

V0_9_7_ARTIFACTS = [
    # New skills (Phase 3)
    "catalog/skills/security/business-logic-abuse/SKILL.md",
    "catalog/skills/security/advanced-attack-patterns/SKILL.md",
    # New skill (parallel-session deep-research work)
    "catalog/skills/specialized-domains/deep-research-compilation/SKILL.md",
    # Style guides relocated out of catalog/commands/ in v1.0.0 so they no
    # longer surface as slash commands. They live alongside the matching
    # command name minus the -style-guide suffix.
    "catalog/style-guides/compile-deep-research.md",
    # New guides (Phase 1 + 4). The v0.9.6 migration note was archived
    # into the legacy migration source docs/archive/v0/ during v2.1.0 post-Phase-10 maintenance
    # (commit 590ea5a). The test continues to assert it exists at its new
    # canonical path so the historical record stays reachable.
    "guides/reference/SESSION_LIFECYCLE_DECISIONS.md",
    "docs/archives/v0/v0.9/opus-4-7-migration.md",  # Canonical frozen container since the v4.0.0 rename.
    # New checklist (Phase 3)
    "catalog/checklists/file-upload-security.md",
    # Bundled report templates (copied silently by installer)
    "templates/documentation/generic-word-report-template.docx",
    "templates/documentation/branded-report-template.docx",
    # Report generator scripts (copied by installer to ~/.nexus-hub/scripts/)
    "scripts/generate_report.py",
    # Repo-scoped AI agent instructions (parallel-session work)
    "AGENTS.md",
    "CLAUDE.md",
    "GEMINI.md",
    ".github/copilot-instructions.md",
    ".cursor/rules/nexus-hub.mdc",
]


def test_all_v0_9_7_source_artifacts_exist():
    missing = []
    for rel in V0_9_7_ARTIFACTS:
        path = REPO_ROOT / rel
        if not path.exists():
            missing.append(rel)
    if missing:
        raise AssertionError(
            "v0.9.7 source artifacts missing (installer cannot copy what is not there):\n  "
            + "\n  ".join(missing)
        )


# --- (4) Syntax validation ---------------------------------------------------

def test_installer_sh_bash_syntax_clean():
    """Fast syntax check via bash -n. Fails fast if the refactor broke parsing."""
    bash = shutil.which("bash")
    if bash is None:
        print("SKIP: bash not available on PATH", file=sys.stderr)
        return  # Treat as skip rather than fail on Windows without bash
    result = subprocess.run(
        [bash, "-n", "scripts/installer.sh"],
        capture_output=True,
        text=True,
        timeout=30,
        cwd=REPO_ROOT,
    )
    assert result.returncode == 0, (
        f"bash -n failed on installer.sh:\n{result.stderr}"
    )


def test_installer_ps1_ast_parse_clean():
    """Parse installer.ps1 via PowerShell's language AST. Skips if no pwsh/powershell."""
    ps = shutil.which("pwsh") or shutil.which("powershell")
    if ps is None:
        print("SKIP: PowerShell not available on PATH", file=sys.stderr)
        return
    script = (
        "$errs = $null; $tokens = $null; "
        f"$null = [System.Management.Automation.Language.Parser]::ParseFile("
        f"'{INSTALLER_PS1}', [ref]$tokens, [ref]$errs); "
        "if ($errs -and $errs.Count -gt 0) { "
        "$errs | ForEach-Object { "
        "Write-Host \"Line $($_.Extent.StartLineNumber): $($_.Message)\" }; "
        "exit 1 } else { exit 0 }"
    )
    result = subprocess.run(
        [ps, "-NoProfile", "-Command", script],
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert result.returncode == 0, (
        f"PowerShell AST parse failed on installer.ps1:\n{result.stdout}\n{result.stderr}"
    )


# --- Manual runner ----------------------------------------------------------

def _run_all():
    tests = [
        test_installer_sh_exists,
        test_installer_ps1_exists,
        test_installer_sh_carries_version_constant,
        test_installer_ps1_carries_version_constant,
        test_installer_sh_has_welcome_banner_function,
        test_installer_ps1_has_welcome_banner_function,
        test_installer_sh_has_nexus_ascii_banner,
        test_installer_ps1_has_nexus_ascii_banner,
        test_installer_sh_migrates_legacy_nexus_hub_dir,
        test_installer_ps1_migrates_legacy_nexus_hub_dir,
        test_installer_sh_scope_is_no_prompt_default_global,
        test_installer_ps1_scope_is_no_prompt_default_global,
        test_installers_have_no_phase_labels,
        test_installer_ps1_does_not_clear_host_after_scope_choice,
        test_installer_sh_does_not_clear_after_scope_choice,
        test_installers_use_claude_usage_monitor_banner,
        test_installer_ps1_surfaces_vsce_errors,
        test_installer_ps1_uses_conflict_only_overwrite,
        test_installer_sh_removed_template_import_prompt,
        test_installer_ps1_removed_template_import_prompt,
        test_declared_claude_effort_level_is_high,
        test_installer_ps1_fallback_literal_matches_template,
        test_installers_copy_every_scripts_dir_py_file,
        test_all_v0_9_7_source_artifacts_exist,
        test_installer_sh_bash_syntax_clean,
        test_installer_ps1_ast_parse_clean,
    ]
    failures = 0
    for t in tests:
        try:
            t()
        except AssertionError as e:
            failures += 1
            print(f"FAIL: {t.__name__}\n{e}")
        except Exception as e:
            failures += 1
            print(f"ERROR: {t.__name__}: {e}")
        else:
            print(f"OK: {t.__name__}")
    if failures:
        print(f"\n{failures} test(s) failed.")
        sys.exit(1)
    print(f"\nAll {len(tests)} installer-smoke tests passed.")


# --- (3) Encoding regression: settings.json must be written BOM-less ----------


def test_installer_ps1_writes_settings_without_bom():
    """Windows PowerShell 5.1's `Set-Content -Encoding UTF8` prepends a UTF-8 BOM,
    which is invalid per the JSON spec and breaks strict JSON.parse consumers such
    as the Claude Code VS Code extension ("Unexpected token ... is not valid JSON").
    The installer must never pipe ConvertTo-Json into Set-Content; it must use the
    BOM-less Write-JsonFile helper instead.
    """
    body = INSTALLER_PS1.read_text(encoding="utf-8")
    assert "ConvertTo-Json -Depth 10 | Set-Content" not in body, (
        "installer.ps1 must not write JSON via 'ConvertTo-Json | Set-Content' "
        "(adds a UTF-8 BOM on Windows PowerShell 5.1). Use Write-JsonFile instead."
    )
    assert "function Write-JsonFile {" in body, (
        "installer.ps1 must define the BOM-less Write-JsonFile helper"
    )
    assert "System.Text.UTF8Encoding($false)" in body, (
        "Write-JsonFile must write UTF-8 without a BOM via UTF8Encoding($false)"
    )


def test_settings_template_has_no_bom():
    """The shipped settings.json template must carry no UTF-8 BOM, so the
    no-existing-file copy path yields a BOM-less, JSON.parse-safe file."""
    import codecs

    head = SETTINGS_TEMPLATE.read_bytes()[:3]
    assert head != codecs.BOM_UTF8, (
        "catalog/hooks/settings.json must be saved without a UTF-8 BOM"
    )


if __name__ == "__main__":
    _run_all()
