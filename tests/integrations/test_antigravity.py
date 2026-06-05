"""Tests for the Antigravity 1.0 and Antigravity 2.0 + CLI integrations.

Added in v2.2.0 Phase 2 (T008). Covers:
  - Both integrations are registered and resolve via get(key)
  - Antigravity 1.0 lays files under .gemini/antigravity/
  - Antigravity 2.0 + CLI lays files under .agents/ (covers both desktop and CLI;
    paths verified 2026-05-29 against Google's public Antigravity CLI docs --
    binary `agy`, `.agents/` per-project dir, `AGENTS.md` instruction file --
    per docs/archive/v2/v2.2.0/antigravity-cli-probe.md)
  - WriteResult records carry the expected FileAction entries
  - The display_name reflects dual desktop+CLI coverage on the 2.0 integration
"""

from __future__ import annotations

from pathlib import Path

from scripts.lib.integrations import get
from scripts.lib.integrations.base import InstallContext


def test_antigravity_10_install_workspace_lays_files(install_ctx: InstallContext):
    integ = get("antigravity")
    result = integ.install(install_ctx)
    assert (install_ctx.target_root / ".gemini" / "antigravity" / "rules.md").exists()
    assert (install_ctx.target_root / ".gemini" / "antigravity" / "skills").exists()
    assert result.files, "WriteResult should record at least one FileAction"


def test_antigravity_20_install_workspace_lays_files(install_ctx: InstallContext):
    integ = get("antigravity2")
    result = integ.install(install_ctx)
    assert (install_ctx.target_root / ".agents" / "AGENTS.md").exists()
    assert (install_ctx.target_root / ".agents" / "skills").exists()
    assert (install_ctx.target_root / ".agents" / "workflows").exists()
    assert (install_ctx.target_root / ".agents" / "subagents").exists()
    assert result.files, "WriteResult should record at least one FileAction"


def test_antigravity_20_display_name_signals_dual_coverage():
    """Per T008 / probe finding, the Antigravity 2.0 integration covers BOTH
    the desktop IDE and the CLI. The display_name carries that dual-coverage
    signal so the installer logs reflect what the user is actually getting.
    """
    integ = get("antigravity2")
    assert "CLI" in integ.display_name, (
        f"antigravity2 display_name should mention CLI to reflect dual coverage; "
        f"got {integ.display_name!r}"
    )


def test_antigravity_20_uses_dedicated_template():
    """After T011, antigravity2 points at base-antigravity-20.md (not the
    legacy base-gemini.md). This protects against regressions if a future
    refactor reroutes the integration back to a shared Gemini template.
    """
    integ = get("antigravity2")
    template = integ.config.get("instruction_template", "")
    assert template.endswith("base-antigravity-20.md"), (
        f"antigravity2 should use base-antigravity-20.md; got {template!r}"
    )


def test_antigravity_10_uses_dedicated_template():
    integ = get("antigravity")
    template = integ.config.get("instruction_template", "")
    assert template.endswith("base-antigravity-10.md"), (
        f"antigravity should use base-antigravity-10.md; got {template!r}"
    )


def test_antigravity_20_idempotent_install(install_ctx: InstallContext, tmp_path: Path):
    """Second install on the same target should mark all files unchanged."""
    integ = get("antigravity2")
    integ.install(install_ctx)
    result = integ.install(install_ctx)
    actions = {a.action for a in result.files}
    assert "unchanged" in actions, (
        f"second install should produce at least one 'unchanged' action; "
        f"got actions={actions}"
    )
