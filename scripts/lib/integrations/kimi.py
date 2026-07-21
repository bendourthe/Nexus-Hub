"""Kimi integration (Kimi Code CLI).

Kimi Code CLI (``MoonshotAI/kimi-code``, data root ``~/.kimi-code/``) reads a full
skills surface plus the merged ``AGENTS.md`` project context (verified 2026-07-21
against https://www.kimi.com/code/docs/):

  - **Instruction**: global ``~/.kimi-code/AGENTS.md``; project ``.kimi-code/AGENTS.md``
    (marker-merged; the ``{{SKILL_INDEX}}`` block is embedded there too).
  - **Skills**: folder-per-skill ``SKILL.md`` one level deep at ``~/.kimi-code/skills/``
    (global) and ``.kimi-code/skills/`` (project). Each skill auto-registers as a
    ``/skill:<name>`` slash command -- skills ARE the command mechanism, there is NO
    separate command file format, so the catalog's commands are surfaced as skills
    too (flattened command-skills). Kimi also honors the cross-tool
    ``~/.agents/skills`` alias, but this integration writes only Kimi's NATIVE
    ``~/.kimi-code/skills`` to avoid an ``uninstall --platforms kimi`` teardown
    conflict with the codex integration that owns the shared path.
  - **Agents**: none -- Kimi Code CLI has only fixed built-in subagents, no
    user-definable agent files.
  - **Hooks**: none -- Kimi's hooks are a ``[[hooks]]`` TOML array in
    ``~/.kimi-code/config.toml`` (a config-merge mechanism, not a folder copy), so
    they are out of scope (``hooks_supported: False``).

MIGRATION (v3.15.0 Phase 4): reclassified from the instruction-file-only surface
that targeted the OLDER, separate "Kimi CLI" product (``~/.kimi/``,
moonshotai.github.io/kimi-cli) to the current "Kimi Code CLI" product
(``~/.kimi-code/``, kimi.com/code/docs). Per the maintainer decision this is a FULL
migration: the ``~/.kimi/`` writes and the Nexus-Hub-invented ``.kimi/agent.yaml``
companion are dropped (neither is read by the current product). A user still on the
old ``~/.kimi/`` Kimi CLI therefore no longer receives a surface; existing
``~/.kimi/`` files from prior installs are left in place (removed only by an
explicit ``uninstall``). Global scope is detection-gated on ``~/.kimi-code``.
"""

from __future__ import annotations

from pathlib import Path

from .base import InstallContext, MarkdownIntegration, SkillsIntegration
from .result import WriteResult


class KimiIntegration(MarkdownIntegration, SkillsIntegration):
    key = "kimi"
    display_name = "Kimi Code CLI"
    instruction_mode = "shared"
    config = {
        # Global surfaces live under ~/.kimi-code, written by install_global below
        # (detection-gated), so there is no simple home-relative global_dir.
        "global_dir": None,
        # AGENTS.md + skills both mirror under .kimi-code/ at workspace scope.
        "workspace_dir": ".kimi-code",
        "instruction_workspace_dir": ".kimi-code",
        "instruction_file": "AGENTS.md",
        "instruction_template": "templates/ai-instructions/base-kimi.md",
        # Skills flattened one level; each catalog command surfaces as a skill too,
        # which is how commands reach Kimi (as /skill:<name>).
        "skills_subdir": "skills",
        "flatten_skills_layout": True,
        "hooks_supported": False,
    }

    def install_global(self, ctx: InstallContext) -> WriteResult:
        """Write the ``~/.kimi-code`` surfaces when Kimi Code CLI is detected, else skip.

        Detection: the Kimi Code CLI data root ``~/.kimi-code`` must exist. When it
        does not, Kimi Code CLI is not installed for this user and the global write
        is skipped (the workspace-scope ``.kimi-code/`` surfaces are unaffected).
        """
        result = WriteResult()
        kimi_root = (Path.home() / ".kimi-code").resolve()
        if not kimi_root.exists():
            ctx.manifest.log(self.key, "~/.kimi-code not found; skipping global Kimi surfaces")
            result.mark_not_detected(
                "Kimi Code CLI (~/.kimi-code) not found; global AGENTS.md + skills skipped"
            )
            return result
        result.detected = True
        self._ensure_dir(kimi_root, ctx)
        action = self._write_instruction(kimi_root, ctx)
        if action is not None:
            result.files.append(action)
        if not ctx.instruction_only:
            result.files.extend(self._mirror_catalog(kimi_root, ctx))
        return result
