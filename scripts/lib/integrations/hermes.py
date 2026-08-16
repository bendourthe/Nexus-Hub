"""Hermes integration.

Hermes is a skills-native 2026 agent that discovers folder-per-skill ``SKILL.md``
directly (the open standard shared by Claude Code, Codex, Gemini CLI, OpenCode, and
Antigravity), so it needs no rendered instruction file. It reads skills from:

  - its NATIVE root ``~/.hermes/skills/<name>/`` (global) and ``.hermes/skills/``
    (project), and
  - the cross-tool open-standard alias ``~/.agents/skills/<name>/`` (global) and the
    project ``.agents/skills/`` -- the same shared surfaces Codex and Antigravity 2.0
    already populate.

This integration therefore writes ONLY Hermes's native ``~/.hermes/skills`` (global,
detection-gated) and ``.hermes/skills`` (project). It deliberately does NOT write the
shared ``~/.agents/skills`` (owned by the ``codex`` integration) or the project
``.agents/skills`` (seeded by ``antigravity2``'s ``wire_project_surfaces`` on
``nexus-hub init``) -- writing them here would create an ``uninstall --platforms
hermes`` teardown conflict with the integration that owns each shared path, the same
conflict the Kimi integration is designed around. Hermes reads those shared paths;
it does not own them.

Skills-only surface: Hermes has no instruction-file surface (no ``base-hermes.md``),
so this is a ``SkillsIntegration`` (not ``MarkdownIntegration``). Skills are flattened
one level (``skills/<name>/SKILL.md``) and each catalog command additionally surfaces
as a skill, matching the SKILL.md open-standard shape the other flattened platforms
use. Global scope is detection-gated on ``~/.hermes``, consistent with the other
extended-platform subclasses (Kimi, Qwen, OpenClaw, Windsurf).

The full read-contract is documented in ``docs/policy/platform-read-contracts.md``.
"""

from __future__ import annotations

from pathlib import Path

from .base import InstallContext, SkillsIntegration
from .result import WriteResult


class HermesIntegration(SkillsIntegration):
    key = "hermes"
    display_name = "Hermes"
    config = {
        # Global skills live under ~/.hermes, written by install_global below
        # (detection-gated), so there is no simple home-relative global_dir.
        "global_dir": None,
        # Project skills mirror under .hermes/ at workspace scope.
        "workspace_dir": ".hermes",
        # Skills flattened one level; each catalog command surfaces as a skill too,
        # matching the SKILL.md open standard Hermes reads.
        "skills_subdir": "skills",
        "flatten_skills_layout": True,
        "hooks_supported": False,
    }

    def install_global(self, ctx: InstallContext) -> WriteResult:
        """Write ``~/.hermes/skills`` when Hermes is detected, else skip with a note.

        Detection: the Hermes config root ``~/.hermes`` must exist. When it does not,
        Hermes is not installed for this user and the global write is skipped (the
        workspace-scope ``.hermes/`` surfaces are unaffected). The shared
        ``~/.agents/skills`` alias Hermes also reads is populated by the ``codex``
        integration, not here.
        """
        result = WriteResult()
        hermes_root = (Path.home() / ".hermes").resolve()
        if not hermes_root.exists():
            ctx.manifest.log(self.key, "~/.hermes not found; skipping global Hermes surfaces")
            result.mark_not_detected("Hermes (~/.hermes) not found; global skills skipped")
            return result
        result.detected = True
        self._ensure_dir(hermes_root, ctx)
        if not ctx.instruction_only:
            result.files.extend(self._mirror_catalog(hermes_root, ctx))
        return result
