"""OpenAI Codex / new ChatGPT desktop app integration.

Codex (the CLI, the IDE extension, and the Codex mode of the new ChatGPT desktop
app that merges Chat + Work + Codex) reads:

  - the AGENTS.md open-standard instruction file (``~/.codex/AGENTS.md`` global +
    the repo-root ``AGENTS.md`` in a project), which carries the ``{{SKILL_INDEX}}``
    block;
  - skills as folder-per-skill ``SKILL.md``, discovered ONE LEVEL DEEP under a
    skills directory -- both ``~/.codex/skills/<name>/`` and the cross-tool
    open-standard ``~/.agents/skills/<name>/`` -- invoked as ``$name``;
  - custom prompts (DEPRECATED, but still read) as top-level ``.md`` files under
    ``~/.codex/prompts/``, invoked ``/prompts:name``.

Nexus-Hub's catalog is two levels deep (``catalog/skills/<category>/<name>/``), so
a verbatim copy buries every ``SKILL.md`` under a category folder Codex reads as a
skill-less skill and nothing registers. This integration therefore uses the shared
adapters (``scripts/lib/integrations/_catalog_adapters.py``) to (a) FLATTEN skills
into both skill roots, (b) additionally emit every catalog COMMAND as a skill so
``$presentify`` / ``$implement`` / etc. work in the new desktop app, and (c) keep
the legacy prompts surface so ``/prompts:name`` still works in the CLI. The full
read-contract is documented in ``docs/policy/platform-read-contracts.md``.
"""

from __future__ import annotations

from pathlib import Path

from ._catalog_adapters import commands_to_skills, commands_to_slash, flatten_skills
from .base import InstallContext, MarkdownIntegration, SkillsIntegration
from .result import WriteResult


class CodexIntegration(MarkdownIntegration, SkillsIntegration):
    key = "codex"
    display_name = "Codex (OpenAI)"
    instruction_mode = "shared"
    config = {
        "global_dir": "~/.codex",
        "workspace_dir": ".codex",
        # Workspace AGENTS.md lands at the project root (the open-standard location
        # Codex / Cursor / OpenCode read); skills/ and prompts/ mirror under .codex/
        # and the cross-tool .agents/. Matches the legacy bash installer (DF-001).
        "instruction_workspace_dir": "",
        "instruction_file": "AGENTS.md",
        "instruction_template": "templates/ai-instructions/base-codex.md",
        # Skills are flattened one level into BOTH ~/.codex/skills and ~/.agents/skills
        # (see docs/policy/platform-read-contracts.md). Commands surface as skills
        # ($name) in the same roots and as legacy top-level prompts (/prompts:name).
        # Codex has no agents/ or rules/ discovery, so those trees are intentionally
        # NOT created (no dead dirs).
        "skills_subdir": "skills",
        "commands_subdir": "prompts",
        "hooks_supported": False,
        "permissions_file": "configs/permissions/codex-permissions.json",
    }

    # ----- install entry points -------------------------------------------

    def install_global(self, ctx: InstallContext) -> WriteResult:
        result = WriteResult()
        codex_root = (Path.home() / ".codex").resolve()
        self._ensure_dir(codex_root, ctx)
        action = self._write_instruction(codex_root, ctx)  # ~/.codex/AGENTS.md
        if action is not None:
            result.files.append(action)
        if not ctx.instruction_only:
            agents_root = (Path.home() / ".agents").resolve()
            result.files.extend(self._mirror_codex(codex_root, agents_root, ctx))
        return result

    def install_workspace(self, ctx: InstallContext) -> WriteResult:
        result = WriteResult()
        # Instruction file at the project root (instruction_workspace_dir="").
        root = ctx.target_root.resolve()
        self._ensure_dir(root, ctx)
        action = self._write_instruction(root, ctx)  # <project>/AGENTS.md
        if action is not None:
            result.files.append(action)
        if not ctx.instruction_only:
            codex_root = (ctx.target_root / ".codex").resolve()
            agents_root = (ctx.target_root / ".agents").resolve()
            self._ensure_dir(codex_root, ctx)
            result.files.extend(self._mirror_codex(codex_root, agents_root, ctx))
        return result

    # ----- mirror helper ---------------------------------------------------

    def _mirror_codex(
        self, codex_root: Path, agents_root: Path, ctx: InstallContext
    ) -> list:
        """Lay the catalog into Codex's read-shape: flattened skills + command
        skills in both skill roots, plus the legacy top-level prompts.
        """
        src_skills = ctx.repo_root / "catalog" / "skills"
        src_commands = ctx.repo_root / "catalog" / "commands"
        existing = self._catalog_skill_names(src_skills)
        actions: list = []
        # Flattened skills + commands-as-skills into BOTH skill roots.
        for skills_dst in (codex_root / "skills", agents_root / "skills"):
            actions.extend(flatten_skills(ctx, self.key, src_skills, skills_dst))
            actions.extend(
                commands_to_skills(ctx, self.key, src_commands, skills_dst, existing)
            )
        # Legacy prompts (top-level .md) into ~/.codex/prompts for /prompts:name.
        actions.extend(
            commands_to_slash(
                ctx, self.key, src_commands, codex_root / "prompts", style="codex_prompts"
            )
        )
        return actions

    @staticmethod
    def _catalog_skill_names(src_skills: Path) -> set:
        """Return the set of skill folder names under catalog/skills/<category>/."""
        names: set = set()
        if src_skills.exists():
            for category in src_skills.iterdir():
                if category.is_dir():
                    for skill in category.iterdir():
                        if skill.is_dir():
                            names.add(skill.name)
        return names
