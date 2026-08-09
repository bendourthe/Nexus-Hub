"""Cross-implementation parity for install selection (v3.16.1 Phase 6.5).

Phase 5 froze the contract and tested the Python resolver against fixtures. This
module guards the part Phase 6 added: that the Bash and PowerShell installers
expose the same selector surface, fail the same way, and filter the same
surfaces.

One thing changed between the plan and the implementation, and it changes what
these tests need to prove. The plan called for each installer to implement the
contract NATIVELY. That was reversed after the jq implementation proved
untestable on the development host (no jq installed), so both installers now
delegate resolution to `scripts/lib/installer/selection.py`. Resolution parity is
therefore structural rather than something to test - there is one resolver.

What still needs proving, and what these tests cover:

* Both installers expose the same three selectors, in each shell's idiom.
* Both fail closed on a bad selector, before writing anything.
* Both require Python only when a selector was supplied, so a full install still
  works with neither Python nor jq - the constraint the original "native"
  wording existed to protect.
* Both filter exactly the three selectable surfaces and leave policy
  infrastructure alone.
* The end-to-end file sets agree (the slow test at the bottom).
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parents[2]
_SH = _ROOT / "scripts" / "installer.sh"
_PS1 = _ROOT / "scripts" / "installer.ps1"
_RESOLVER = _ROOT / "scripts" / "lib" / "installer" / "selection.py"

if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))


@pytest.fixture(scope="module")
def sh() -> str:
    return _SH.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def ps1() -> str:
    return _PS1.read_text(encoding="utf-8")


# --------------------------------------------------------------------------- #
# Selector surface parity
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize("selector", ["profile", "modules", "bundles"])
def test_bash_declares_each_selector(sh: str, selector: str) -> None:
    assert f"--{selector})" in sh, f"installer.sh must accept --{selector}"
    assert f"--{selector}=*)" in sh, (
        f"installer.sh must accept --{selector}=VALUE too; every other flag in "
        "this installer supports both forms and a selector that did not would "
        "be an inconsistency users hit by habit."
    )


@pytest.mark.parametrize("selector", ["Modules", "Bundles"])
def test_powershell_declares_each_selector(ps1: str, selector: str) -> None:
    assert f"[string]${selector}" in ps1, (
        f"installer.ps1 must declare -{selector} in its param block."
    )


def test_powershell_profile_is_an_alias_not_a_parameter_name(ps1: str) -> None:
    """-Profile must bind, but must NOT be the variable name.

    `$Profile` is a PowerShell automatic variable (the path to the user's
    profile script), and a parameter of that name shadows it inside the script.
    The alias keeps the user-facing spelling identical to the Bash `--profile`
    without the shadowing, which is what PSScriptAnalyzer's
    PSAvoidAssignmentToAutomaticVariable flags.
    """
    assert '[Alias("Profile")]' in ps1, (
        "installer.ps1 must expose -Profile via an alias so the spelling stays "
        "in lockstep with Bash's --profile."
    )
    assert "[string]$InstallProfile" in ps1, (
        "the backing parameter must be $InstallProfile, not $Profile."
    )
    assert "[string]$Profile," not in ps1, (
        "a parameter literally named $Profile shadows a PowerShell automatic "
        "variable; use the alias arrangement instead."
    )


def test_both_installers_forward_selectors_to_the_registry(sh: str, ps1: str) -> None:
    """The legacy script and the registry must resolve the same plan.

    If only one of them applied the selection, a platform installed by the
    registry would get a different set than one installed by the legacy copy
    block, in the same run.
    """
    for name, body, flag in (("installer.sh", sh, '"--profile"'), ("installer.ps1", ps1, '"--profile"')):
        assert flag in body, f"{name} must forward --profile to runner.py"
        assert '"--modules"' in body and '"--bundles"' in body, (
            f"{name} must forward --modules and --bundles to runner.py"
        )


def test_neither_installer_interpolates_selectors_into_a_command_string(sh: str, ps1: str) -> None:
    """Selectors must be passed as discrete arguments, never spliced into a string.

    The bash form appends to an args array and PowerShell to $argsList; both are
    invoked as arrays, so a selector value cannot inject an extra argument.
    """
    assert 'args+=("--profile" "$SELECT_PROFILE")' in sh, (
        "installer.sh must append --profile as two array elements."
    )
    assert '$argsList += @("--profile", $InstallProfile)' in ps1, (
        "installer.ps1 must append the profile as discrete array elements "
        "(from $InstallProfile, the alias-backed parameter)."
    )


# --------------------------------------------------------------------------- #
# Fail-closed behavior
# --------------------------------------------------------------------------- #

def test_both_installers_resolve_before_writing(sh: str, ps1: str) -> None:
    """Resolution must sit beside the --platforms validation, before any copy.

    Position matters: an invalid selector discovered halfway through an install
    has already written files, which is exactly what the contract's
    fail-before-write rule forbids.
    """
    sh_resolve = sh.index("resolve_selection \"$REPO_ROOT\"")
    sh_overwrite = sh.index("Resolve the assume-yes / overwrite decision")
    assert sh_resolve < sh_overwrite, (
        "installer.sh must resolve the selection before the install flow begins."
    )
    ps_resolve = ps1.index("Resolve-Selection -RepoRoot $repoRoot")
    ps_overwrite = ps1.index("Resolve the assume-yes / overwrite decision")
    assert ps_resolve < ps_overwrite, (
        "installer.ps1 must resolve the selection before the install flow begins."
    )


def test_both_installers_require_python_only_for_selectors(sh: str, ps1: str) -> None:
    """A no-selector full install must still work with no Python and no jq.

    This is the constraint the plan's 'native implementation' wording existed to
    protect, and it survives the delegation decision because the Python path is
    only reached once a selector has been supplied.
    """
    assert "selection_requested || return 0" in sh, (
        "installer.sh must return before touching Python when no selector was given."
    )
    assert "if (-not (Test-SelectionRequested)) { return }" in ps1, (
        "installer.ps1 must return before touching Python when no selector was given."
    )
    for name, body in (("installer.sh", sh), ("installer.ps1", ps1)):
        assert "need Python to resolve" in body, (
            f"{name} must explain that selectors specifically need Python, and "
            "that a full install does not."
        )


def test_bash_error_path_captures_status_under_set_e(sh: str) -> None:
    """Regression guard for a bug this phase actually hit.

    `set -e` is active, so a bare `out=$(...)` aborts the script at the
    assignment when the resolver exits non-zero, and the handler that prints
    WHICH selector was wrong never runs. The user gets exit 2 and silence.
    """
    assert 'out=$("$py" "${args[@]}" 2>&1) || rc=$?' in sh, (
        "installer.sh must capture the resolver status in a `|| rc=$?` branch, "
        "or `set -e` swallows the error message."
    )


def test_powershell_does_not_redirect_native_stderr(ps1: str) -> None:
    """Regression guard for the PS 5.1 NativeCommandError trap.

    Redirecting a native command's stderr with 2>&1 wraps each line in an
    ErrorRecord and sets $? false even on a clean exit, turning a good run into a
    visible error.
    """
    assert "$output = & $py @resolverArgs\n" in ps1, (
        "installer.ps1 must invoke the resolver without 2>&1."
    )
    assert "$output = & $py @resolverArgs 2>&1" not in ps1, (
        "2>&1 on a native command produces NativeCommandError noise on PS 5.1."
    )


def test_bash_strips_carriage_returns_from_resolver_output(sh: str) -> None:
    """Regression guard for a Windows/Git Bash bug this phase actually hit.

    A Windows Python invoked from Git Bash writes CRLF. Without stripping, every
    value carries a trailing \\r, `find -name` matches nothing, and the install
    silently stages an empty selection - which looks like a working install that
    shipped no skills.
    """
    assert "value=\"${value%$'\\r'}\"" in sh, (
        "installer.sh must strip a trailing CR from each resolver record."
    )


# --------------------------------------------------------------------------- #
# What is filtered, and what is never filtered
# --------------------------------------------------------------------------- #

def test_both_installers_filter_exactly_the_selectable_surfaces(sh: str, ps1: str) -> None:
    for surface in ("skills", "commands", "agents"):
        assert f'catalog_src "$repo_root" {surface}' in sh, (
            f"installer.sh must route the {surface} copy through catalog_src."
        )
        assert f'-Surface "{surface}"' in ps1, (
            f"installer.ps1 must route the {surface} copy through Get-CatalogSource."
        )


@pytest.mark.parametrize("surface", ["hooks", "rules", "context", "memory", "style-guides", "mcp-configs"])
def test_policy_surfaces_are_never_routed_through_the_filter(sh: str, surface: str) -> None:
    """A narrower capability set must never mean weaker guardrails.

    Filtering the secret-scan hook out of a focused install would make the
    focused path less safe than the default one, which inverts the purpose.
    """
    assert f'catalog_src "$repo_root" {surface}' not in sh, (
        f"{surface} is policy infrastructure and must not be filtered."
    )


def test_stage_only_holds_the_three_selectable_surfaces(sh: str, ps1: str) -> None:
    assert '"$SELECTION_STAGE/skills" "$SELECTION_STAGE/commands" "$SELECTION_STAGE/agents"' in sh
    assert '@("skills", "commands", "agents")' in ps1


# --------------------------------------------------------------------------- #
# The resolver CLI both installers depend on
# --------------------------------------------------------------------------- #

def test_resolver_cli_emits_the_documented_line_format() -> None:
    out = subprocess.run(
        [sys.executable, str(_RESOLVER), "--repo-root", str(_ROOT),
         "--modules", "ai-engineering", "--emit", "lines"],
        check=True, **_CAPTURE,
    ).stdout
    lines = [ln for ln in out.splitlines() if ln.strip()]
    kinds = {ln.split("\t")[0] for ln in lines}
    assert kinds <= {"HASH", "SKILL", "COMMAND", "AGENT", "WARN"}, f"unexpected record kinds: {kinds}"
    assert lines[0].startswith("HASH\tsha256:"), "the first record must be the plan hash"
    assert any(ln == "SKILL\teval-pipeline-audit" for ln in lines), (
        "the ai-engineering module must resolve eval-pipeline-audit (added Phase 2)"
    )
    for ln in lines:
        assert "\t" in ln, f"every record must be tab-separated: {ln!r}"


@pytest.mark.parametrize(
    "args,expected_code",
    [
        (["--profile", "does-not-exist"], 2),
        (["--profile", "full", "--modules", "ai-engineering"], 2),
        (["--modules", "ai-engineering,,testing"], 2),
    ],
)
def test_resolver_cli_exit_codes(args: list, expected_code: int) -> None:
    proc = subprocess.run(
        [sys.executable, str(_RESOLVER), "--repo-root", str(_ROOT), "--emit", "lines"] + args,
        **_CAPTURE,
    )
    assert proc.returncode == expected_code, (
        f"expected exit {expected_code}, got {proc.returncode}. stderr: {proc.stderr}"
    )
    assert proc.stdout.strip() == "", "a failing resolution must emit no plan"


def test_resolver_cli_writes_nothing(tmp_path: Path) -> None:
    """The installers rely on this: resolution happens before any install write."""
    before = os.getcwd()
    os.chdir(tmp_path)
    try:
        subprocess.run(
            [sys.executable, str(_RESOLVER), "--repo-root", str(_ROOT),
             "--modules", "ai-engineering", "--emit", "lines"],
            check=True, **_CAPTURE,
        )
        assert list(tmp_path.iterdir()) == []
    finally:
        os.chdir(before)


# --------------------------------------------------------------------------- #
# End-to-end parity (slow; both installers actually run)
# --------------------------------------------------------------------------- #

def _bash() -> str | None:
    return shutil.which("bash")


def _powershell() -> str | None:
    """A PowerShell that can actually run scripts/installer.ps1.

    Gated on Windows deliberately. GitHub's ubuntu-latest image ships `pwsh`, so
    a bare `which` check does NOT skip on Linux - it finds pwsh, runs the Windows
    installer against a POSIX host, and fails with a bare `rc=1`. installer.ps1
    is a Windows installer (registry-adjacent paths, %TEMP%, Windows PowerShell
    5.1 idioms); running it on Linux is not a supported scenario, so the correct
    behavior is to skip rather than to report a failure.
    """
    if sys.platform != "win32":
        return None
    return shutil.which("powershell") or shutil.which("pwsh")


# Every subprocess that captures installer output MUST pass these.
#
# The installers print UTF-8 (check marks, box drawing). On Windows, Python's
# subprocess reader thread defaults to the ANSI code page, dies with
# UnicodeDecodeError mid-read, and leaves `proc.stdout` as None. The test then
# fails while BUILDING its own assertion message - "TypeError: 'NoneType' object
# is not subscriptable" - which hides whatever actually happened. Decoding
# explicitly with a replacement policy keeps the real result visible.
_CAPTURE = {"capture_output": True, "text": True, "encoding": "utf-8", "errors": "replace"}


def _install_failure(proc) -> str:
    """Readable diagnostic for a failed installer run.

    stderr comes FIRST because that is where both shells write the actual
    error; stdout is a long progress log whose tail is usually the last
    successful step, not the failure. An earlier version printed only the
    stdout tail, which sent a CI investigation to the wrong part of the script.
    """
    return (
        f"install failed (rc={proc.returncode})\n"
        f"--- stderr ---\n{(proc.stderr or '')[-4000:]}\n"
        f"--- stdout tail ---\n{(proc.stdout or '')[-1500:]}"
    )


@pytest.mark.slow
@pytest.mark.skipif(_bash() is None, reason="bash not available")
def test_bash_filtered_install_matches_the_resolver(tmp_path: Path) -> None:
    target = tmp_path / "ws"
    target.mkdir()
    proc = subprocess.run(
        [_bash(), str(_SH), "--workspace", str(target), "--platforms", "claude",
         "--modules", "ai-engineering", "--yes"],
        cwd=str(_ROOT), timeout=900, **_CAPTURE,
    )
    assert proc.returncode == 0, _install_failure(proc)
    expected = json.loads(subprocess.run(
        [sys.executable, str(_RESOLVER), "--repo-root", str(_ROOT), "--modules", "ai-engineering"],
        check=True, **_CAPTURE,
    ).stdout)["resolved"]["skills"]

    skills_dir = target / ".claude" / "skills"
    installed = {p.name for p in skills_dir.iterdir() if p.is_dir()}
    missing = [s for s in expected if s not in installed]
    assert not missing, f"resolved skills missing from the install: {missing}"
    # Policy infrastructure must survive a focused install.
    assert (target / ".claude" / "rules").is_dir(), "rules must install under any selection"


@pytest.mark.slow
@pytest.mark.skipif(_powershell() is None, reason="powershell not available")
def test_powershell_filtered_install_matches_bash(tmp_path: Path) -> None:
    """Both installers must produce the same skill set for the same selector."""
    target = tmp_path / "ps"
    target.mkdir()
    proc = subprocess.run(
        [_powershell(), "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(_PS1),
         "-Workspace", str(target), "-Platforms", "claude", "-Modules", "ai-engineering", "-Yes"],
        cwd=str(_ROOT), timeout=900, **_CAPTURE,
    )
    assert proc.returncode == 0, _install_failure(proc)
    expected = json.loads(subprocess.run(
        [sys.executable, str(_RESOLVER), "--repo-root", str(_ROOT), "--modules", "ai-engineering"],
        check=True, **_CAPTURE,
    ).stdout)["resolved"]["skills"]
    installed = {p.name for p in (target / ".claude" / "skills").iterdir() if p.is_dir()}
    missing = [s for s in expected if s not in installed]
    assert not missing, f"resolved skills missing from the PowerShell install: {missing}"
    assert (target / ".claude" / "rules").is_dir()
