"""Hermes integration.

Hermes is a skills-native 2026 agent that discovers folder-per-skill ``SKILL.md``
directly from its native ``~/.hermes/skills/<name>/`` (global) and
``.hermes/skills/<name>/`` (project) roots, so it needs no rendered instruction
file. Additional roots such as ``~/.agents/skills`` are read only when the user
adds them to Hermes's ``skills.external_dirs`` setting; Nexus-Hub does not alter
that user-owned setting and therefore does not claim automatic shared-root reach.

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
        workspace-scope ``.hermes/`` surfaces are unaffected). Nexus-Hub does not
        add ``~/.agents/skills`` to the user-owned ``skills.external_dirs`` list.
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
