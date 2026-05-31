"""Tests for the --branch / -Branch installer flag (v2.4.0).

The flag installs the catalog from a pushed branch by shallow-cloning it into a
deterministic cache dir (~/.nexus-hub/branches/<sanitized>/) and re-running the
install from that checkout, leaving the user's working copy untouched.

These tests cover:
  * the static surface (both installers declare the flag, the sanitizer, the
    re-entry guard, and document the flag in --help / -Help);
  * the clone-free probe (--branch <name> --check / -Branch <name> -Check prints
    the resolved cache path and exits 0 without cloning);
  * branch-name sanitization (a path-traversal branch name yields no `..`);
  * the empty-value error path.
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
INSTALLER_SH = REPO_ROOT / "scripts" / "installer.sh"
INSTALLER_PS1 = REPO_ROOT / "scripts" / "installer.ps1"

BASH = shutil.which("bash")
PWSH = shutil.which("pwsh") or shutil.which("powershell")


# --- Static surface ---------------------------------------------------------

def test_installer_sh_declares_branch_flag() -> None:
    body = INSTALLER_SH.read_text(encoding="utf-8")
    assert "--branch" in body, "installer.sh must accept --branch"
    assert "sanitize_branch_name" in body, "installer.sh must define the sanitizer"
    assert "BRANCH_NAME" in body
    assert "NEXUS_HUB_BRANCH_RESOLVED" in body, "installer.sh must guard re-entry"
    assert "--branch <name>" in body, "installer.sh --help must document --branch"


def test_installer_ps1_declares_branch_param() -> None:
    body = INSTALLER_PS1.read_text(encoding="utf-8")
    assert "[string]$Branch" in body, "installer.ps1 must declare [string]$Branch"
    assert "Get-SanitizedBranchName" in body, "installer.ps1 must define the sanitizer"
    assert "-Branch" in body
    assert "NEXUS_HUB_BRANCH_RESOLVED" in body, "installer.ps1 must guard re-entry"
    assert "-Branch <name>" in body, "installer.ps1 -Help must document -Branch"


# --- bash probe -------------------------------------------------------------

@pytest.mark.skipif(not BASH, reason="bash not available")
def test_bash_branch_check_probe_resolves_cache_path() -> None:
    proc = subprocess.run(
        [BASH, str(INSTALLER_SH), "--branch", "feature/login", "--check"],
        capture_output=True, text=True, cwd=str(REPO_ROOT),
    )
    assert proc.returncode == 0, proc.stderr
    out = proc.stdout
    assert "branches/feature-login" in out, out
    assert "feature/login" in out  # original branch echoed back


@pytest.mark.skipif(not BASH, reason="bash not available")
def test_bash_branch_check_neutralizes_traversal() -> None:
    proc = subprocess.run(
        [BASH, str(INSTALLER_SH), "--branch", "../../etc", "--check"],
        capture_output=True, text=True, cwd=str(REPO_ROOT),
    )
    assert proc.returncode == 0, proc.stderr
    line = next((ln for ln in proc.stdout.splitlines() if "sanitized:" in ln), "")
    assert "sanitized:" in line, proc.stdout
    assert ".." not in line, f"traversal not neutralized: {line!r}"


@pytest.mark.skipif(not BASH, reason="bash not available")
def test_bash_branch_requires_value() -> None:
    proc = subprocess.run(
        [BASH, str(INSTALLER_SH), "--branch"],
        capture_output=True, text=True, cwd=str(REPO_ROOT),
    )
    assert proc.returncode == 2
    assert "branch name" in (proc.stdout + proc.stderr).lower()


# --- PowerShell probe (skipped where no PowerShell is present) --------------

@pytest.mark.skipif(not PWSH, reason="PowerShell not available")
def test_ps_branch_check_probe_resolves_cache_path() -> None:
    proc = subprocess.run(
        [PWSH, "-NoProfile", "-ExecutionPolicy", "Bypass", "-File",
         str(INSTALLER_PS1), "-Branch", "feature/login", "-Check"],
        capture_output=True, text=True, cwd=str(REPO_ROOT),
    )
    assert proc.returncode == 0, proc.stderr
    assert "feature-login" in proc.stdout, proc.stdout


@pytest.mark.skipif(not PWSH, reason="PowerShell not available")
def test_ps_branch_check_neutralizes_traversal() -> None:
    proc = subprocess.run(
        [PWSH, "-NoProfile", "-ExecutionPolicy", "Bypass", "-File",
         str(INSTALLER_PS1), "-Branch", "../../etc", "-Check"],
        capture_output=True, text=True, cwd=str(REPO_ROOT),
    )
    assert proc.returncode == 0, proc.stderr
    line = next((ln for ln in proc.stdout.splitlines() if "sanitized:" in ln), "")
    assert "sanitized:" in line, proc.stdout
    assert ".." not in line, f"traversal not neutralized: {line!r}"
