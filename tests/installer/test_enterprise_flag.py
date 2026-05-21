"""Tests for the --enterprise / -Enterprise flag added in v2.2.0 Phase 2 (T013).

The flag gates the standalone Gemini CLI install path. Without the flag, the
installer prints a sunset warning (per the 2026-05-21 Google Developers Blog
announcement) and skips the Gemini CLI registry dispatch. With the flag, the
installer runs the legacy install path.

These tests assert on the *source* of the installer scripts (not on a live
install run) because:
  1. Running the full installer in CI would touch the user's $HOME or $env:USERPROFILE.
  2. The flag's behavior is a textual gate around a specific dispatch line; a
     source-level check is the cheapest way to confirm both files are
     consistent.

If a future refactor moves the dispatch into a function, these tests need to
follow that refactor; see docs/v2.2.0/plans/codegraph-and-antigravity.md
sub-task 2.7 (T013).
"""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
INSTALLER_SH = REPO_ROOT / "scripts" / "installer.sh"
INSTALLER_PS1 = REPO_ROOT / "scripts" / "installer.ps1"


def test_installer_sh_declares_enterprise_flag():
    """installer.sh must accept --enterprise and document it in --help."""
    body = INSTALLER_SH.read_text(encoding="utf-8")
    assert "--enterprise" in body, "installer.sh must accept --enterprise"
    assert "ENTERPRISE=1" in body or "ENTERPRISE=\"1\"" in body, (
        "installer.sh must set ENTERPRISE when --enterprise is passed"
    )
    assert "show_installer_usage" in body, "installer.sh must define a usage function"


def test_installer_sh_gates_gemini_cli_dispatch():
    """Both Gemini CLI registry dispatch lines (global + workspace) must be
    inside an `if ENTERPRISE` block so non-enterprise users skip the install.
    """
    body = INSTALLER_SH.read_text(encoding="utf-8")
    # Both dispatches should still exist...
    assert body.count("gemini-cli") >= 2, (
        "installer.sh should still reference gemini-cli at least twice (global + workspace)"
    )
    # ...but each must be inside a conditional block.
    # Heuristic: find each gemini-cli line and check the immediately preceding
    # ~10 lines for an ENTERPRISE check.
    lines = body.splitlines()
    cli_line_indices = [i for i, line in enumerate(lines) if "gemini-cli" in line and "invoke_registry_platform" in line]
    assert len(cli_line_indices) >= 2, (
        f"expected >=2 invoke_registry_platform gemini-cli dispatch lines; "
        f"got {len(cli_line_indices)}"
    )
    for idx in cli_line_indices:
        window = "\n".join(lines[max(0, idx - 10):idx])
        assert "ENTERPRISE" in window, (
            f"gemini-cli dispatch at line {idx + 1} is not gated by an "
            f"ENTERPRISE check in the preceding 10 lines"
        )


def test_installer_sh_prints_sunset_warning():
    """The non-enterprise path must surface the 2026-06-18 sunset notice."""
    body = INSTALLER_SH.read_text(encoding="utf-8")
    assert "2026-06-18" in body, (
        "installer.sh must reference the 2026-06-18 Gemini CLI sunset date"
    )
    assert "Antigravity CLI" in body, (
        "installer.sh sunset notice must point users at Antigravity CLI as the replacement"
    )


def test_installer_ps1_declares_enterprise_switch():
    """installer.ps1 must accept -Enterprise as a [switch] parameter."""
    body = INSTALLER_PS1.read_text(encoding="utf-8")
    assert "[switch]$Enterprise" in body or "[switch] $Enterprise" in body, (
        "installer.ps1 must declare [switch]$Enterprise in its param block"
    )
    assert "-Enterprise" in body, "installer.ps1 must reference -Enterprise"


def test_installer_ps1_gates_gemini_cli_dispatch():
    body = INSTALLER_PS1.read_text(encoding="utf-8")
    lines = body.splitlines()
    cli_line_indices = [
        i for i, line in enumerate(lines)
        if "gemini-cli" in line and "Invoke-RegistryPlatform" in line
    ]
    assert len(cli_line_indices) >= 2, (
        f"expected >=2 Invoke-RegistryPlatform gemini-cli dispatch lines; "
        f"got {len(cli_line_indices)}"
    )
    for idx in cli_line_indices:
        window = "\n".join(lines[max(0, idx - 10):idx])
        assert "$Enterprise" in window or "Enterprise" in window, (
            f"gemini-cli dispatch at line {idx + 1} is not gated by an "
            f"$Enterprise check in the preceding 10 lines"
        )


def test_installer_ps1_prints_sunset_warning():
    body = INSTALLER_PS1.read_text(encoding="utf-8")
    assert "2026-06-18" in body
    assert "Antigravity CLI" in body


def test_gemini_cli_integration_display_name_signals_enterprise_only():
    """The Gemini CLI integration's display_name must signal ENTERPRISE-ONLY
    so the runner's per-line log reflects the v2.2.0 gating.
    """
    from scripts.lib.integrations import get

    integ = get("gemini-cli")
    assert "ENTERPRISE-ONLY" in integ.display_name, (
        f"gemini-cli display_name should signal ENTERPRISE-ONLY post-2026-06-18; "
        f"got {integ.display_name!r}"
    )
    assert "2026-06-18" in integ.display_name, (
        f"gemini-cli display_name should reference the 2026-06-18 sunset date; "
        f"got {integ.display_name!r}"
    )
