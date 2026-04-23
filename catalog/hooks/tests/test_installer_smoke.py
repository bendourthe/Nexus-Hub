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


# --- (1) Installer script structural assertions ------------------------------

def test_installer_sh_exists():
    assert INSTALLER_SH.is_file(), f"Missing: {INSTALLER_SH}"


def test_installer_ps1_exists():
    assert INSTALLER_PS1.is_file(), f"Missing: {INSTALLER_PS1}"


def test_installer_sh_carries_version_constant():
    body = INSTALLER_SH.read_text(encoding="utf-8")
    assert 'DEVAI_HUB_VERSION="0.9.7"' in body, \
        "installer.sh is missing the DEVAI_HUB_VERSION='0.9.7' constant"


def test_installer_ps1_carries_version_constant():
    body = INSTALLER_PS1.read_text(encoding="utf-8")
    assert '$script:DevAIHubVersion = "0.9.7"' in body, \
        "installer.ps1 is missing the $script:DevAIHubVersion = '0.9.7' constant"


def test_installer_sh_has_welcome_banner_function():
    body = INSTALLER_SH.read_text(encoding="utf-8")
    assert "print_banner()" in body, "installer.sh is missing print_banner()"
    assert "Welcome to the DevAI-Hub Universal Installer" in body, \
        "installer.sh banner text missing"
    # Accept either ${DEVAI_HUB_VERSION} or $DEVAI_HUB_VERSION interpolation form
    assert "${DEVAI_HUB_VERSION}" in body or "$DEVAI_HUB_VERSION" in body, \
        "installer.sh banner must interpolate the DEVAI_HUB_VERSION variable"


def test_installer_ps1_has_welcome_banner_function():
    body = INSTALLER_PS1.read_text(encoding="utf-8")
    assert "function Show-WelcomeBanner" in body, \
        "installer.ps1 is missing Show-WelcomeBanner"
    assert "Welcome to the DevAI-Hub Universal Installer" in body, \
        "installer.ps1 banner text missing"
    assert "$script:DevAIHubVersion" in body, \
        "installer.ps1 banner must interpolate $script:DevAIHubVersion"


def test_installer_sh_asks_global_vs_workspace_first():
    body = INSTALLER_SH.read_text(encoding="utf-8")
    # The upfront scope choice prompt (v0.9.7 refactor, terse form in post-release fix)
    assert "Select [G/W]" in body, \
        "installer.sh is missing the upfront global-vs-workspace choice"
    # Global must be the default (recommended) branch
    assert "Global (recommended)" in body, \
        "installer.sh should present Global as the recommended option"


def test_installer_ps1_asks_global_vs_workspace_first():
    body = INSTALLER_PS1.read_text(encoding="utf-8")
    assert "Select [G/W]" in body, \
        "installer.ps1 is missing the upfront global-vs-workspace choice"
    assert "Global (recommended)" in body, \
        "installer.ps1 should present Global as the recommended option"


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
    """Banner text must read 'CLAUDE USAGE MONITOR', not the old 'CLAUDE CODE USAGE MONITOR'.
    The product name is 'Claude Usage Monitor' (per its own README + package.json).
    """
    for path in (INSTALLER_SH, INSTALLER_PS1):
        body = path.read_text(encoding="utf-8")
        assert "CLAUDE CODE USAGE MONITOR" not in body, (
            f"{path.name} must use 'CLAUDE USAGE MONITOR' as the section banner text"
        )
        assert "CLAUDE USAGE MONITOR" in body, (
            f"{path.name} is missing the 'CLAUDE USAGE MONITOR' section banner"
        )


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
    # The new capture-and-echo-on-failure pattern must be present
    assert "$vsceOutput = & npx vsce package" in body and "2>&1" in body, (
        "installer.ps1 must capture vsce output into $vsceOutput using 2>&1 redirection"
    )


def test_installer_ps1_has_overwrite_request_subsection():
    """Both Install-Global and Install-Workspace must render an 'Overwrite Request'
    subsection banner before calling Get-Overwrite-Preference, so the preamble
    prompt is framed consistently with the other subsections.
    """
    body = INSTALLER_PS1.read_text(encoding="utf-8")
    # Must appear at least twice (Install-Global + Install-Workspace)
    count = body.count('Write-SubSectionBanner -Text "Overwrite Request"')
    assert count >= 2, (
        f"installer.ps1 must render an 'Overwrite Request' subsection in both "
        f"Install-Global and Install-Workspace (found {count} occurrences)"
    )


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

def test_catalog_hooks_settings_effort_level_is_xhigh():
    """Regression guard for the shipped v0.9.7 default `xhigh`.

    A mid-release interlude briefly reduced this to `high`; the reduction
    was reverted before tag. If a future change wants to reduce the default
    again, update the CHANGELOG + this test together so the intent is explicit.
    """
    assert SETTINGS_TEMPLATE.is_file(), f"Missing: {SETTINGS_TEMPLATE}"
    data = json.loads(SETTINGS_TEMPLATE.read_text(encoding="utf-8"))
    assert "effortLevel" in data, "catalog/hooks/settings.json is missing 'effortLevel'"
    assert data["effortLevel"] == "xhigh", (
        f"Expected effortLevel='xhigh' (v0.9.7 shipped default), got {data['effortLevel']!r}. "
        "If this was a deliberate change, update the CHANGELOG + test and remove "
        "this assertion's tag."
    )


def test_installer_ps1_fallback_literal_matches_template():
    """If jq/PowerShell merge fails, installer.ps1 prints a manual-add hint.

    That hint MUST reference the same value as catalog/hooks/settings.json.
    """
    body = INSTALLER_PS1.read_text(encoding="utf-8")
    assert '"effortLevel`": `"xhigh`"' in body, (
        "installer.ps1 manual-add fallback must reference \"xhigh\" to match "
        "catalog/hooks/settings.json. Update both together if the default changes."
    )


# Scripts under scripts/ that are developer/maintainer tooling and must NOT
# ship to end users via the installer. Each entry needs a one-line justification
# so a future contributor can tell whether a new script belongs here or in the
# installer copy blocks.
DEV_ONLY_SCRIPTS = {
    # Repo validator: walks catalog/ for frontmatter + secret scans. Runs in CI
    # and by maintainers; not useful in an end-user ~/.devai-hub/scripts/.
    "validate_skills.py",
    # One-shot cross-catalog maintenance utility that injects iterative-refinement
    # text into SKILL.md / command .md files. Maintainer tool only.
    "apply_iterative_workflow.py",
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
            "by folder — every new user-facing script in scripts/ must be added",
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
    # New commands (parallel-session deep-research work)
    "catalog/commands/compile-deep-research.md",
    "catalog/commands/compile-deep-research-style-guide.md",
    # New guides (Phase 1 + 4)
    "guides/SESSION_LIFECYCLE_DECISIONS.md",
    "docs/v0.9.6/opus-4-7-migration.md",
    # New checklist (Phase 3)
    "catalog/checklists/file-upload-security.md",
    # Bundled report templates (copied silently by installer)
    "templates/documentation/generic-word-report-template.docx",
    "templates/documentation/branded-report-template.docx",
    # Report generator scripts (copied by installer to ~/.devai-hub/scripts/)
    "scripts/generate_report.py",
    # Repo-scoped AI agent instructions (parallel-session work)
    "AGENTS.md",
    "CLAUDE.md",
    "GEMINI.md",
    ".github/copilot-instructions.md",
    ".cursor/rules/devai-hub.mdc",
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
        [bash, "-n", str(INSTALLER_SH)],
        capture_output=True,
        text=True,
        timeout=30,
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
        test_installer_sh_asks_global_vs_workspace_first,
        test_installer_ps1_asks_global_vs_workspace_first,
        test_installers_have_no_phase_labels,
        test_installer_ps1_does_not_clear_host_after_scope_choice,
        test_installer_sh_does_not_clear_after_scope_choice,
        test_installers_use_claude_usage_monitor_banner,
        test_installer_ps1_surfaces_vsce_errors,
        test_installer_ps1_has_overwrite_request_subsection,
        test_installer_sh_removed_template_import_prompt,
        test_installer_ps1_removed_template_import_prompt,
        test_catalog_hooks_settings_effort_level_is_xhigh,
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


if __name__ == "__main__":
    _run_all()
