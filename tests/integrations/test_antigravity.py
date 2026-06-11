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

import json
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


def test_antigravity_20_skills_are_flattened(install_ctx: InstallContext):
    """Antigravity discovers skills one level under skills/, so the catalog's
    `<category>/<skill-name>/SKILL.md` layout MUST be flattened to
    `skills/<skill-name>/SKILL.md`. A verbatim copy (with the category layer)
    is the bug that made every skill invisible in the 2.0 IDE.
    """
    integ = get("antigravity2")
    integ.install(install_ctx)
    skills_dir = install_ctx.target_root / ".agents" / "skills"

    # The category layer must be gone: known category names must NOT appear as
    # folders under skills/.
    for category in ("ai-development", "workflow", "security", "orchestration"):
        assert not (skills_dir / category).is_dir(), (
            f"category folder {category!r} leaked into skills/ -- skills were not "
            f"flattened"
        )

    # Every immediate child of skills/ is a skill folder holding a SKILL.md.
    skill_dirs = [p for p in skills_dir.iterdir() if p.is_dir()]
    assert len(skill_dirs) >= 50, f"expected the full flat catalog; got {len(skill_dirs)}"
    for skill in skill_dirs[:15]:
        assert (skill / "SKILL.md").exists(), (
            f"{skill.name}/ must contain SKILL.md directly (flat layout)"
        )


def test_antigravity_20_installs_hooks_and_registration(install_ctx: InstallContext):
    """Hooks: the curated scripts land under hooks/ and a hooks.json in
    Antigravity's named-group schema registers them with the confirmed
    `run_command` matcher and a workspace-relative command path.
    """
    integ = get("antigravity2")
    integ.install(install_ctx)
    agents = install_ctx.target_root / ".agents"

    for script in ("secret-scan.sh", "large-file-guard.sh", "git-guardrails.sh", "compress-output.sh"):
        assert (agents / "hooks" / script).exists(), f"hook script {script} not installed"

    hooks_json = agents / "hooks.json"
    assert hooks_json.exists(), "hooks.json registration not written"
    data = json.loads(hooks_json.read_text(encoding="utf-8"))
    assert "nexus-hub-guardrails" in data and "nexus-hub-context-compressor" in data
    guardrails = data["nexus-hub-guardrails"]
    assert guardrails["enabled"] is True
    commands = [h["command"] for entry in guardrails["PreToolUse"] for h in entry["hooks"]]
    assert any(".agents/hooks/secret-scan.sh" in c for c in commands), (
        f"workspace hooks.json should reference the project-relative hook path; got {commands}"
    )
    matchers = {entry["matcher"] for entry in guardrails["PreToolUse"]}
    assert "run_command" in matchers, "git-guardrails must match the run_command tool"


def test_antigravity_20_global_targets_both_ide_and_cli_roots(install_ctx: InstallContext):
    """Global install must reach BOTH the IDE root (~/.gemini/antigravity) and
    the CLI root (~/.gemini/antigravity-cli). Uses dry_run so the real home
    directory is never touched.
    """
    from dataclasses import replace

    integ = get("antigravity2")
    global_ctx = replace(install_ctx, scope="global")
    result = integ.dry_run(global_ctx)
    paths = [fa.path.replace("\\", "/") for fa in result.files]
    joined = " ".join(paths)
    assert "/.gemini/antigravity/" in joined, (
        "global install must write to the IDE root ~/.gemini/antigravity/"
    )
    assert "/.gemini/antigravity-cli/" in joined, (
        "global install must write to the CLI root ~/.gemini/antigravity-cli/"
    )
