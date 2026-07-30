"""Tests for the no-prompt all-platform install + conflict-only overwrite
(v3.7.0 Phase 2).

Phase 2 removed the interactive scope (`Select [G/W]`) and the per-file
`Overwrite? [Y/N/A]` prompts. The installer now:

  * defaults to a global install across ALL platforms with no prompts;
  * gates each per-provider block on a `--platforms` / `-Platforms` subset
    (absent platforms skip-with-note);
  * accepts `--workspace` / `-Workspace`, `--platforms` / `-Platforms`,
    `--yes` / `-Yes`, and `--force` / `-Force`;
  * keeps marker-merge for instruction files, and for plain managed files uses
    conflict-only overwrite: in a non-interactive / --yes / --force run they are
    refreshed to the latest version silently; in an interactive run a managed
    file that differs on disk is collected and a SINGLE end-of-run prompt lists
    the files and asks once whether to overwrite.

Coverage:
  * Static surface (both installers): the scope/overwrite prompts are gone, the
    new flags are parsed, the conflict accumulators + resolver exist, and the
    per-provider blocks are platform-gated.
  * bash functional: the conflict + platform-filter helpers are extracted from
    `scripts/installer.sh` and driven in isolation -- the no-conflict (silent)
    path, the refresh path, the interactive conflict path (keep vs overwrite),
    the folder merge-vs-full-sync modes, and the should_install gating.
  * bash functional (early-exit): an unknown `--platforms` key and a missing
    `--workspace` path both exit non-zero with a clear message.

The bash functional tests skip cleanly when bash is absent or on Windows; CI
(ubuntu) is authoritative for the bash path. The static tests run everywhere.

Note on WN-v36-1, which this file used to cite as "bash cannot always be fully run
on the Windows dev host": that framing was DISPROVEN in v3.15.6 Phase 4. The cause
was PATH shadowing (the WSL launcher stub preceding Git Bash), not host
incapability. The Windows skip here is retained on the narrower ground that these
tests drive the full installer, a path this suite has never verified on Windows.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
INSTALLER_SH = REPO_ROOT / "scripts" / "installer.sh"
INSTALLER_PS1 = REPO_ROOT / "scripts" / "installer.ps1"

BASH = shutil.which("bash")
WINDOWS = sys.platform == "win32"

bash_functional = pytest.mark.skipif(
    not BASH or WINDOWS,
    reason="full bash installer verified on CI/macOS; unverified on Windows",
)

_RUN_KW = dict(capture_output=True, text=True, encoding="utf-8", errors="replace")

# The integration-key vocabulary --platforms / -Platforms must accept.
PLATFORM_KEYS = [
    "claude", "codex", "gemini", "antigravity2", "gemini-cli", "copilot",
    "cursor", "opencode", "nexus-ai", "aider", "windsurf", "kimi", "qwen",
    "openclaw",
]


# --- helpers ----------------------------------------------------------------

def _extract_bash_function(body: str, name: str) -> str:
    """Return the source of the top-level bash function `name` from `body`.

    Relies on the installer convention that every function opens with
    `<name>() {` and closes with a `}` alone at column 0 (nested blocks use
    if/fi, case/esac, for/done -- never a bare `}` at column 0).
    """
    lines = body.splitlines()
    start = None
    opener = f"{name}() {{"
    for i, line in enumerate(lines):
        if line.strip() == opener or line.startswith(opener):
            start = i
            break
    assert start is not None, f"function {name}() not found in installer.sh"
    for j in range(start + 1, len(lines)):
        if lines[j] == "}":
            return "\n".join(lines[start : j + 1])
    raise AssertionError(f"no column-0 closing brace for {name}()")


_HARNESS_PREAMBLE = r"""
set -e
RESET=""; RED=""; GREEN=""; YELLOW=""; GRAY=""; DARK_YELLOW=""; CYAN=""
OVERWRITE_ALL=${OVERWRITE_ALL:-false}
PLATFORMS_FILTER=${PLATFORMS_FILTER:-}
CONFLICT_SRCS=()
CONFLICT_DSTS=()
TEMP_FILES=()
write_item() { echo "ITEM: $1"; }
write_subsection_banner() { echo "BANNER: $1"; }
# read_prompt is stubbed to return a scripted response instead of reading stdin.
read_prompt() { echo "${HARNESS_RESP:-}"; }
"""


def _run_harness(driver: str, env: dict | None = None) -> subprocess.CompletedProcess:
    """Compose stubs + the Phase 2 helpers extracted from installer.sh + a
    per-test driver into one bash program and run it."""
    body = INSTALLER_SH.read_text(encoding="utf-8")
    funcs = "\n\n".join(
        _extract_bash_function(body, name)
        for name in ("safe_copy", "safe_folder_copy", "resolve_conflicts", "should_install")
    )
    program = _HARNESS_PREAMBLE + "\n" + funcs + "\n\n" + driver
    run_env = {**os.environ, **(env or {})}
    return subprocess.run([BASH, "-c", program], **_RUN_KW, env=run_env)


# --- static surface: bash ---------------------------------------------------

def test_bash_scope_and_overwrite_prompts_removed() -> None:
    body = INSTALLER_SH.read_text(encoding="utf-8")
    assert "Select [G/W]" not in body, "the interactive scope prompt must be gone"
    assert "Overwrite? [Y]es / [N]o / [A]ll" not in body, "per-file overwrite prompt must be gone"
    assert "Full sync? [Y]es" not in body, "per-folder full-sync prompt must be gone"


def test_bash_new_flags_parsed() -> None:
    body = INSTALLER_SH.read_text(encoding="utf-8")
    for flag in ("--workspace", "--platforms", "--yes", "--force"):
        assert flag in body, f"installer.sh must parse {flag}"
    assert "WORKSPACE_PATH" in body and "PLATFORMS_ARG" in body


def test_bash_conflict_machinery_present() -> None:
    body = INSTALLER_SH.read_text(encoding="utf-8")
    assert "CONFLICT_SRCS" in body and "CONFLICT_DSTS" in body, "conflict accumulators must exist"
    assert "resolve_conflicts()" in body, "resolve_conflicts must exist"
    assert "should_install()" in body, "should_install platform gate must exist"
    # Every provider block must be gated on the platform subset.
    for key in ("claude", "codex", "copilot", "cursor", "opencode", "nexus-ai"):
        assert f"should_install {key}" in body, f"provider block for {key} must be platform-gated"


def test_bash_non_interactive_resolves_to_refresh() -> None:
    body = INSTALLER_SH.read_text(encoding="utf-8")
    # The resolution block keys assume-yes on --yes / --force / a non-TTY stdin.
    assert "! -t 0" in body, "a non-TTY stdin must imply assume-yes"
    assert 'ASSUME_YES=true' in body and 'OVERWRITE_ALL=true' in body


# --- static surface: PowerShell ---------------------------------------------

def test_ps_scope_and_overwrite_prompts_removed() -> None:
    body = INSTALLER_PS1.read_text(encoding="utf-8")
    assert 'Read-Host "Select [G/W]"' not in body, "the PS scope prompt must be gone"
    assert "function Get-Overwrite-Preference" not in body, "the PS overwrite prompt must be gone"
    assert "function Select-Platforms" not in body, "the PS platform menu must be gone"


def test_ps_new_params_present() -> None:
    body = INSTALLER_PS1.read_text(encoding="utf-8")
    for param in ("$Workspace", "$Platforms", "$Yes", "$Force"):
        assert f"[string]{param}" in body or f"[switch]{param}" in body, f"PS must declare {param}"


def test_ps_conflict_machinery_present() -> None:
    body = INSTALLER_PS1.read_text(encoding="utf-8")
    assert "function Resolve-Conflicts" in body
    assert "function Resolve-Platforms" in body
    assert "$script:ConflictSrcs" in body and "$script:ConflictDsts" in body
    # Refresh-on-yes: the resolved decision maps to OverwriteMode "ALL".
    assert "IsInputRedirected" in body, "a redirected stdin must imply assume-yes"
    assert '$script:OverwriteMode = "ALL"' in body


def test_ps_platform_key_map_complete() -> None:
    body = INSTALLER_PS1.read_text(encoding="utf-8")
    # Resolve-Platforms must map every integration key to an internal platform.
    for key in PLATFORM_KEYS:
        assert f'"{key}"' in body, f"PS Resolve-Platforms must map the '{key}' key"


# --- bash functional: conflict + platform helpers ---------------------------

@bash_functional
def test_helper_fresh_copy_creates_no_conflict(tmp_path: Path) -> None:
    src = tmp_path / "src.txt"; src.write_text("v1\n")
    dst = tmp_path / "out" / "dst.txt"
    driver = f'''
safe_copy "{src}" "{dst}" true "OK installed"
echo "CONFLICTS=${{#CONFLICT_DSTS[@]}}"
'''
    proc = _run_harness(driver, env={"OVERWRITE_ALL": "false"})
    assert proc.returncode == 0, proc.stderr
    assert dst.read_text() == "v1\n", "fresh destination must be created"
    assert "CONFLICTS=0" in proc.stdout, "a fresh copy is not a conflict"


@bash_functional
def test_helper_identical_copy_is_silent_no_conflict(tmp_path: Path) -> None:
    src = tmp_path / "src.txt"; src.write_text("same\n")
    dst = tmp_path / "dst.txt"; dst.write_text("same\n")
    driver = f'''
safe_copy "{src}" "{dst}" true "OK"
echo "CONFLICTS=${{#CONFLICT_DSTS[@]}}"
'''
    proc = _run_harness(driver, env={"OVERWRITE_ALL": "false"})
    assert proc.returncode == 0, proc.stderr
    assert "CONFLICTS=0" in proc.stdout, "an identical file is not a conflict"


@bash_functional
def test_helper_interactive_conflict_collected_and_kept(tmp_path: Path) -> None:
    src = tmp_path / "src.txt"; src.write_text("NEW\n")
    dst = tmp_path / "dst.txt"; dst.write_text("USER EDIT\n")
    driver = f'''
safe_copy "{src}" "{dst}" true "OK"
echo "CONFLICTS=${{#CONFLICT_DSTS[@]}}"
echo "FIRST=${{CONFLICT_DSTS[0]}}"
'''
    proc = _run_harness(driver, env={"OVERWRITE_ALL": "false"})
    assert proc.returncode == 0, proc.stderr
    assert "CONFLICTS=1" in proc.stdout, "a differing file must be recorded as exactly one conflict"
    assert str(dst) in proc.stdout, "the conflict prompt must name the file"
    assert dst.read_text() == "USER EDIT\n", "the user's file must be kept pending confirmation"


@bash_functional
def test_helper_resolve_conflicts_overwrite_on_yes(tmp_path: Path) -> None:
    src = tmp_path / "src.txt"; src.write_text("NEW\n")
    dst = tmp_path / "dst.txt"; dst.write_text("OLD\n")
    driver = f'''
safe_copy "{src}" "{dst}" true "OK"
resolve_conflicts
'''
    proc = _run_harness(driver, env={"OVERWRITE_ALL": "false", "HARNESS_RESP": "y"})
    assert proc.returncode == 0, proc.stderr
    assert dst.read_text() == "NEW\n", "confirming overwrite must refresh the file"


@bash_functional
def test_helper_resolve_conflicts_keep_on_no(tmp_path: Path) -> None:
    src = tmp_path / "src.txt"; src.write_text("NEW\n")
    dst = tmp_path / "dst.txt"; dst.write_text("OLD\n")
    driver = f'''
safe_copy "{src}" "{dst}" true "OK"
resolve_conflicts
'''
    proc = _run_harness(driver, env={"OVERWRITE_ALL": "false", "HARNESS_RESP": "n"})
    assert proc.returncode == 0, proc.stderr
    assert dst.read_text() == "OLD\n", "declining must keep the user's file"
    assert "Kept your" in proc.stdout


@bash_functional
def test_helper_refresh_mode_overwrites_without_conflict(tmp_path: Path) -> None:
    src = tmp_path / "src.txt"; src.write_text("NEW\n")
    dst = tmp_path / "dst.txt"; dst.write_text("OLD\n")
    driver = f'''
safe_copy "{src}" "{dst}" true "OK"
echo "CONFLICTS=${{#CONFLICT_DSTS[@]}}"
'''
    proc = _run_harness(driver, env={"OVERWRITE_ALL": "true"})
    assert proc.returncode == 0, proc.stderr
    assert dst.read_text() == "NEW\n", "refresh mode must overwrite immediately"
    assert "CONFLICTS=0" in proc.stdout, "refresh mode records no conflict (no prompt)"


@bash_functional
def test_helper_folder_full_sync_removes_stale(tmp_path: Path) -> None:
    src = tmp_path / "src"; src.mkdir(); (src / "a.txt").write_text("a")
    dst = tmp_path / "dst"; dst.mkdir()
    (dst / "a.txt").write_text("a"); (dst / "stale.txt").write_text("stale")
    driver = f'safe_folder_copy "{src}" "{dst}" "OK"\n'
    proc = _run_harness(driver, env={"OVERWRITE_ALL": "true"})
    assert proc.returncode == 0, proc.stderr
    assert not (dst / "stale.txt").exists(), "full sync (refresh) must remove stale files"


@bash_functional
def test_helper_folder_merge_keeps_extras(tmp_path: Path) -> None:
    src = tmp_path / "src"; src.mkdir(); (src / "a.txt").write_text("a")
    dst = tmp_path / "dst"; dst.mkdir()
    (dst / "extra.txt").write_text("user added")
    driver = f'safe_folder_copy "{src}" "{dst}" "OK"\n'
    proc = _run_harness(driver, env={"OVERWRITE_ALL": "false"})
    assert proc.returncode == 0, proc.stderr
    assert (dst / "a.txt").read_text() == "a", "merge must add/update catalog files"
    assert (dst / "extra.txt").exists(), "merge (interactive) must keep user-added extras"


@bash_functional
def test_helper_should_install_gating() -> None:
    driver = '''
PLATFORMS_FILTER=""
should_install claude && echo "EMPTY_ALLOWS_claude"
PLATFORMS_FILTER="claude codex"
should_install claude && echo "FILTER_ALLOWS_claude"
should_install gemini || echo "FILTER_SKIPS_gemini"
'''
    proc = _run_harness(driver)
    assert proc.returncode == 0, proc.stderr
    assert "EMPTY_ALLOWS_claude" in proc.stdout, "no filter => install all"
    assert "FILTER_ALLOWS_claude" in proc.stdout
    assert "FILTER_SKIPS_gemini" in proc.stdout, "a key outside the filter must be skipped"


# --- bash functional: early-exit flag validation ----------------------------

@bash_functional
def test_invalid_platform_key_exits_nonzero() -> None:
    proc = subprocess.run(
        [BASH, "scripts/installer.sh", "--platforms", "bogus"],
        cwd=str(REPO_ROOT), stdin=subprocess.DEVNULL, **_RUN_KW,
    )
    assert proc.returncode == 2, (proc.stdout, proc.stderr)
    combined = proc.stdout + proc.stderr
    assert "Unknown platform key" in combined
    assert "Valid keys" in combined


@bash_functional
def test_missing_workspace_path_exits_nonzero() -> None:
    proc = subprocess.run(
        [BASH, "scripts/installer.sh", "--workspace", str(REPO_ROOT / "does-not-exist-xyz")],
        cwd=str(REPO_ROOT), stdin=subprocess.DEVNULL, **_RUN_KW,
    )
    assert proc.returncode == 2, (proc.stdout, proc.stderr)
    assert "Workspace path not found" in (proc.stdout + proc.stderr)
