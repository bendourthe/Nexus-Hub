"""Cross-installer permission parity: merge path, Git-Bash Copilot, workspace scope.

v3.17.0 Phase 1.2 closed three defects that all shared one shape -- a capability that
existed on one operating system and silently did nothing on another:

1. **Merge parity.** `installer.ps1` performed its own native union merge, so removal
   propagation (retiring an entry a prior version shipped and this one dropped) worked
   on macOS and Linux and did nothing on Windows. Both now call
   `scripts/merge_permissions.py`.
2. **Copilot on Git-Bash.** The bash `case "$(uname -s)"` handled only `Darwin*` and
   `Linux*`, so a Windows Git-Bash invocation skipped Copilot entirely.
3. **Workspace scope.** `install_permissions` took a `scope` parameter that every call
   site passed as `"Global"`, and `install_workspace` never called it, so `--workspace`
   installed no baseline on any OS.

The behavioral tests here extract the REAL functions from each installer (bash via
`sed`, PowerShell via the AST) following the harness pattern in
`tests/installer/test_strict_permissions.py`, because a text assertion cannot tell the
difference between a function that is present and a function that works.

Note deliberately NOT tested here: "both installers reference every new script by
name". `catalog/hooks/tests/test_installer_smoke.py` already asserts that for every
`scripts/*.py` via a glob, so a per-script copy here would be a near-duplicate of an
aggregate test (AGENTS.md test-retention policy).
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

BASH = shutil.which("bash")


def _resolve_powershell() -> str | None:
    """Resolve a PowerShell interpreter, honoring the NEXUS_TEST_POWERSHELL pin.

    Mirrors catalog/hooks/tests/conftest.py. The pin is load-bearing in CI: the Windows
    leg sets it to `powershell` (5.1) precisely because the editions differ in ways that
    bite, and a suite that silently prefers pwsh 7 passes while leaving 5.1 uncovered.
    An unresolvable pin returns None rather than falling back to the other edition,
    because silently testing the wrong edition is the failure mode being avoided.
    """
    import os

    pinned = os.environ.get("NEXUS_TEST_POWERSHELL")
    if pinned:
        return shutil.which(pinned)
    for name in ("pwsh", "powershell"):
        found = shutil.which(name)
        if found:
            return found
    return None


PWSH = _resolve_powershell()

COPILOT_KEY = "github.copilot.chat.codeGeneration.useInstructionFiles"


# --- Static surface: one merge implementation, no stale sentinels -------------


def test_both_installers_delegate_to_the_shared_merge_helper() -> None:
    sh = INSTALLER_SH.read_text(encoding="utf-8")
    ps = INSTALLER_PS1.read_text(encoding="utf-8")
    assert "merge_permissions_via_helper()" in sh
    assert "function Merge-PermissionsViaHelper" in ps
    for body, label in ((sh, "installer.sh"), (ps, "installer.ps1")):
        assert "merge_permissions.py" in body, f"{label} must call the shared helper"


def test_powershell_no_longer_carries_a_native_permission_union() -> None:
    """The ported-away native merge was the parity debt itself: a pure union cannot
    retire an entry, so Windows users kept every mutation-capable entry on upgrade."""
    ps = INSTALLER_PS1.read_text(encoding="utf-8")
    assert "$existingJson.permissions.allow = $merged" not in ps, (
        "installer.ps1 still performs its own permissions.allow union merge"
    )
    assert "$existingJson.tools.allowed = @($existingTools" not in ps, (
        "installer.ps1 still performs its own tools.allowed union merge"
    )


def _code_lines(path: Path) -> str:
    """The file with whole-line comments stripped.

    Both installers now carry comments that quote the removed sentinels to explain the
    defect, so a raw substring search would fire on the documentation of the fix. What
    matters is that no sentinel appears in executable code.
    """
    return "\n".join(
        line for line in path.read_text(encoding="utf-8").splitlines()
        if not line.lstrip().startswith("#")
    )


@pytest.mark.parametrize(
    ("installer", "sentinel"),
    [
        (INSTALLER_SH, "run_shell_command(docker ps)"),
        (INSTALLER_PS1, '"ReadFileTool"'),
    ],
)
def test_stale_gemini_sentinels_are_gone(installer: Path, sentinel: str) -> None:
    """A3 bug 1, both shells. A fixed marker present in every existing user's config
    made the branch return early forever, so those users never received newly-shipped
    entries -- including the Phase 1.1 hardening."""
    assert sentinel not in _code_lines(installer), (
        f"{installer.name} still gates the Gemini branch on the stale sentinel {sentinel}"
    )


def test_bash_copilot_branch_handles_git_bash_unames() -> None:
    sh = INSTALLER_SH.read_text(encoding="utf-8")
    assert "MINGW*|MSYS*|CYGWIN*)" in sh, (
        "the Copilot branch must map Git-Bash unames instead of falling through to skip"
    )


def test_copilot_path_matches_between_installers() -> None:
    """The bash arm must mirror installer.ps1's path, not guess one."""
    sh = INSTALLER_SH.read_text(encoding="utf-8")
    ps = INSTALLER_PS1.read_text(encoding="utf-8")
    assert 'Join-Path $env:APPDATA "Code\\User\\settings.json"' in ps
    assert '"$appdata/Code/User/settings.json"' in sh


def test_both_installers_wire_workspace_scope() -> None:
    sh = INSTALLER_SH.read_text(encoding="utf-8")
    ps = INSTALLER_PS1.read_text(encoding="utf-8")
    assert 'install_permissions "$repo_root" "CLAUDE" "Workspace" "$target_path"' in sh, (
        "install_workspace must call install_permissions, or the scope parameter is decorative"
    )
    assert '-Platform "CLAUDE" -Scope "Workspace" -TargetPath $targetPath' in ps


def test_workspace_target_is_the_local_settings_file_in_both_installers() -> None:
    """`.claude/settings.json` is commit-visible; a permission grant written there would
    enter the user's repository history."""
    for installer in (INSTALLER_SH, INSTALLER_PS1):
        body = installer.read_text(encoding="utf-8")
        assert "settings.local.json" in body, (
            f"{installer.name} must target settings.local.json at workspace scope"
        )


# --- Behavioral harnesses ----------------------------------------------------

_SH_HARNESS = r"""
set -euo pipefail
installer="$1"; repo_root="$2"; platform="$3"; scope="$4"; target="${5:-}"
GRAY=""; GREEN=""; YELLOW=""; DARK_YELLOW=""; RED=""
write_item() { printf '%s\n' "$1"; }
ensure_codex_cli() { :; }
# Force the Git-Bash branch of the Copilot OS switch. A shell function shadows the
# external command, so this exercises the real `case "$(uname -s)"` logic.
if [ "${FAKE_MINGW:-0}" = "1" ]; then
    uname() { echo "MINGW64_NT-10.0-22631"; }
fi
extract() { sed -n "/^$1() {/,/^}/p" "$installer"; }
eval "$(extract resolve_python_executable)"
eval "$(extract resolve_permissions_helper)"
eval "$(extract report_permissions_helper_output)"
eval "$(extract merge_permissions_via_helper)"
eval "$(extract set_permission_flag_via_helper)"
eval "$(extract install_permissions)"
install_permissions "$repo_root" "$platform" "$scope" "$target"
"""

_PS_HARNESS = r"""
$ErrorActionPreference = 'Stop'
$installer = $args[0]; $repoRoot = $args[1]; $platform = $args[2]
$scope = $args[3]; $target = if ($args.Count -gt 4) { $args[4] } else { "" }

# Extract the REAL functions via the AST; installer.ps1 has top-level code so it
# cannot simply be dot-sourced.
$ast = [System.Management.Automation.Language.Parser]::ParseFile($installer, [ref]$null, [ref]$null)
foreach ($name in @('Resolve-PythonExecutable', 'Merge-PermissionsViaHelper', 'Install-Permissions')) {
    $fn = $ast.FindAll({
        $args[0] -is [System.Management.Automation.Language.FunctionDefinitionAst] -and
        $args[0].Name -eq $name
    }, $true) | Select-Object -First 1
    if (-not $fn) { Write-Error "$name not found"; exit 3 }
    Invoke-Expression $fn.Extent.Text
}

# Write-HOST, not Write-Output, mirroring installer.ps1:317 exactly. Write-Output would
# put these strings into the pipeline, where `if (Merge-PermissionsViaHelper ...)` would
# swallow them as part of the boolean evaluation -- so the stub would silently hide the
# very removal reports this suite asserts on.
function Write-Item { param($Message, $Color) Write-Host $Message }
function Write-JsonFile { param($Path, $Object, [int]$Depth = 10)
    [System.IO.File]::WriteAllText($Path, ($Object | ConvertTo-Json -Depth $Depth), (New-Object System.Text.UTF8Encoding($false)))
}
function Ensure-CodexCli { }

Install-Permissions -RepoRoot $repoRoot -Platform $platform -Scope $scope -TargetPath $target
"""


def _run_sh(tmp_path: Path, platform: str, scope: str, target: str = "",
            home: Path | None = None, fake_mingw: bool = False,
            appdata: Path | None = None) -> subprocess.CompletedProcess[str]:
    import os

    tmp_path.mkdir(parents=True, exist_ok=True)
    harness = tmp_path / "harness.sh"
    harness.write_text(_SH_HARNESS, encoding="utf-8", newline="\n")
    # Inherit the real environment and override only what the test controls. A minimal
    # env (PATH + HOME) is tempting but wrong on Windows: with SystemDrive unset, a
    # child process expands "%SystemDrive%" literally and creates a directory by that
    # name in the CWD -- which is the repository root.
    env = dict(os.environ)
    env["HOME"] = str(home or tmp_path / "home")
    if fake_mingw:
        env["FAKE_MINGW"] = "1"
    if appdata is not None:
        env["APPDATA"] = str(appdata)
    else:
        env.pop("APPDATA", None)  # the unset-APPDATA skip path must really be unset
    return subprocess.run(
        [BASH, str(harness), str(INSTALLER_SH), str(REPO_ROOT), platform, scope, target],
        capture_output=True, text=True, timeout=300, env=env, cwd=str(tmp_path),
    )


def _run_ps(tmp_path: Path, platform: str, scope: str, target: str = "",
            userprofile: Path | None = None,
            appdata: Path | None = None) -> subprocess.CompletedProcess[str]:
    import os

    tmp_path.mkdir(parents=True, exist_ok=True)
    harness = tmp_path / "harness.ps1"
    harness.write_text(_PS_HARNESS, encoding="utf-8")
    env = dict(os.environ)
    env["USERPROFILE"] = str(userprofile or tmp_path / "profile")
    if appdata is not None:
        env["APPDATA"] = str(appdata)
    return subprocess.run(
        [PWSH, "-NoProfile", "-File", str(harness), str(INSTALLER_PS1), str(REPO_ROOT),
         platform, scope, target],
        capture_output=True, text=True, timeout=300, env=env, cwd=str(tmp_path),
    )


# --- Copilot on Git-Bash ------------------------------------------------------


@pytest.mark.skipif(not BASH, reason="no bash interpreter")
def test_copilot_resolves_a_path_on_a_simulated_mingw_uname(tmp_path: Path) -> None:
    """Before the fix this printed 'not supported on this OS via bash' and returned."""
    appdata = tmp_path / "AppData" / "Roaming"
    settings = appdata / "Code" / "User" / "settings.json"
    settings.parent.mkdir(parents=True)
    settings.write_text(json.dumps({"editor.fontSize": 12}), encoding="utf-8")

    proc = _run_sh(tmp_path, "COPILOT", "Global", fake_mingw=True, appdata=appdata)

    assert proc.returncode == 0, proc.stderr
    assert "not supported on this OS" not in proc.stdout, (
        f"Git-Bash still skips Copilot configuration:\n{proc.stdout}"
    )
    doc = json.loads(settings.read_text(encoding="utf-8"))
    assert doc.get(COPILOT_KEY) is True, (
        "the Copilot key was not written, so the branch resolved a path but did nothing "
        f"(this is the jq dependency the fix removed):\n{proc.stdout}"
    )
    assert doc["editor.fontSize"] == 12, "the user's own VS Code settings must survive"


@pytest.mark.skipif(not BASH, reason="no bash interpreter")
def test_copilot_skips_cleanly_when_appdata_is_unset(tmp_path: Path) -> None:
    proc = _run_sh(tmp_path, "COPILOT", "Global", fake_mingw=True)
    assert proc.returncode == 0, proc.stderr
    assert "APPDATA" in proc.stdout, "an unresolvable path must say why it skipped"


# --- Workspace scope ---------------------------------------------------------


@pytest.mark.skipif(not BASH, reason="no bash interpreter")
def test_bash_workspace_install_writes_the_local_settings_file(tmp_path: Path) -> None:
    target = tmp_path / "project"
    target.mkdir()

    proc = _run_sh(tmp_path, "CLAUDE", "Workspace", str(target))

    assert proc.returncode == 0, proc.stderr
    local = target / ".claude" / "settings.local.json"
    assert local.exists(), f"workspace install wrote nothing:\n{proc.stdout}"
    assert (target / ".claude" / "settings.json").exists() is False, (
        "workspace scope must never write the commit-visible settings.json"
    )
    entries = json.loads(local.read_text(encoding="utf-8"))["permissions"]["allow"]
    assert entries, "the workspace baseline is empty"


@pytest.mark.skipif(not BASH, reason="no bash interpreter")
@pytest.mark.parametrize("platform", ["GEMINI", "CODEX", "COPILOT"])
def test_unwired_platforms_skip_with_a_note_at_workspace_scope(
    tmp_path: Path, platform: str
) -> None:
    """Skip-with-note, not a guess: a fabricated project path looks configured and is
    not, which is worse than an explicit skip."""
    target = tmp_path / "project"
    target.mkdir()

    proc = _run_sh(tmp_path, platform, "Workspace", str(target))

    assert proc.returncode == 0, proc.stderr
    assert "Skip:" in proc.stdout, f"{platform} must state why it skipped:\n{proc.stdout}"
    assert list(target.iterdir()) == [], (
        f"{platform} wrote into the project at workspace scope: {list(target.iterdir())}"
    )


@pytest.mark.skipif(not BASH, reason="no bash interpreter")
def test_no_workspace_write_targets_a_commit_visible_file(tmp_path: Path) -> None:
    """The blanket assertion: after a workspace install of all four platforms, none of
    the commit-visible permission surfaces exists."""
    target = tmp_path / "project"
    target.mkdir()
    for platform in ("CLAUDE", "GEMINI", "CODEX", "COPILOT"):
        proc = _run_sh(tmp_path, platform, "Workspace", str(target))
        assert proc.returncode == 0, proc.stderr

    for commit_visible in (".claude/settings.json", ".vscode/settings.json",
                           ".gemini/settings.json", ".codex/config.toml"):
        assert not (target / commit_visible).exists(), (
            f"workspace install wrote the commit-visible {commit_visible}"
        )


@pytest.mark.skipif(not BASH, reason="no bash interpreter")
def test_workspace_install_rejects_a_missing_target(tmp_path: Path) -> None:
    proc = _run_sh(tmp_path, "CLAUDE", "Workspace", str(tmp_path / "absent"))
    assert proc.returncode == 0, proc.stderr
    assert "Skip:" in proc.stdout


@pytest.mark.skipif(not PWSH, reason="no PowerShell interpreter")
def test_powershell_workspace_install_writes_the_local_settings_file(tmp_path: Path) -> None:
    target = tmp_path / "project"
    target.mkdir()

    proc = _run_ps(tmp_path, "CLAUDE", "Workspace", str(target))

    assert proc.returncode == 0, proc.stderr
    local = target / ".claude" / "settings.local.json"
    assert local.exists(), f"workspace install wrote nothing:\n{proc.stdout}"
    assert not (target / ".claude" / "settings.json").exists()


# --- The parity assertion the debt was about --------------------------------


@pytest.mark.skipif(not BASH or not PWSH, reason="needs both interpreters")
def test_both_installers_produce_an_identical_merged_config(tmp_path: Path) -> None:
    """The end-to-end parity check: same input, same output, both shells.

    Each side gets its own home seeded identically -- an existing config carrying an
    entry a prior version shipped and this one no longer does (`Bash(gh api *)`), plus
    an entry the user added themselves -- and a manifest recording the former as
    Nexus-Hub-shipped. Both installers must retire the first, keep the second, and
    preserve an unrelated sibling key.
    """
    seeded = {
        "permissions": {"allow": ["Read", "Bash(gh api *)", "Bash(my-own-tool *)"]},
        "someUserKey": "preserve-me",
    }
    manifest = {"shipped": {"CLAUDE": ["Bash(gh api *)"]}}

    homes = {}
    for label in ("sh", "ps"):
        home = tmp_path / label
        (home / ".claude").mkdir(parents=True)
        (home / ".claude" / "settings.json").write_text(json.dumps(seeded, indent=2),
                                                        encoding="utf-8")
        (home / ".nexus-hub").mkdir(parents=True)
        (home / ".nexus-hub" / "permissions-manifest.json").write_text(
            json.dumps(manifest), encoding="utf-8")
        homes[label] = home

    sh_proc = _run_sh(tmp_path / "sh-run", "CLAUDE", "Global", home=homes["sh"])
    assert sh_proc.returncode == 0, sh_proc.stderr
    ps_proc = _run_ps(tmp_path / "ps-run", "CLAUDE", "Global", userprofile=homes["ps"])
    assert ps_proc.returncode == 0, ps_proc.stderr

    results = {}
    for label, home in homes.items():
        results[label] = (home / ".claude" / "settings.json").read_text(encoding="utf-8")

    assert results["sh"] == results["ps"], (
        "the bash and PowerShell paths produced different merged configs, which is the "
        "drift this phase exists to eliminate"
    )

    doc = json.loads(results["sh"])
    allow = doc["permissions"]["allow"]
    assert "Bash(gh api *)" not in allow, "removal propagation did not run"
    assert "Bash(my-own-tool *)" in allow, "a user-added entry was removed"
    assert doc["someUserKey"] == "preserve-me", "an unrelated key was dropped"
    assert not any(k.startswith("_") for k in doc), "template metadata leaked"


@pytest.mark.skipif(not BASH or not PWSH, reason="needs both interpreters")
def test_both_installers_report_the_retired_entry(tmp_path: Path) -> None:
    """Removals are reported, never silent: the target file is one the user may have
    hand-edited."""
    outputs = {}
    for label, runner, kwargs in (
        ("sh", _run_sh, "home"),
        ("ps", _run_ps, "userprofile"),
    ):
        home = tmp_path / label
        (home / ".claude").mkdir(parents=True)
        (home / ".claude" / "settings.json").write_text(
            json.dumps({"permissions": {"allow": ["Bash(gh api *)"]}}), encoding="utf-8")
        (home / ".nexus-hub").mkdir(parents=True)
        (home / ".nexus-hub" / "permissions-manifest.json").write_text(
            json.dumps({"shipped": {"CLAUDE": ["Bash(gh api *)"]}}), encoding="utf-8")
        outputs[label] = runner(tmp_path / f"{label}-run", "CLAUDE", "Global",
                                **{kwargs: home})

    for label, proc in outputs.items():
        assert proc.returncode == 0, proc.stderr
        assert "removed: Bash(gh api *)" in proc.stdout, (
            f"{label} did not report the retired entry:\n{proc.stdout}"
        )
