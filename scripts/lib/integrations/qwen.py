"""Qwen integration (Qwen Code).

Qwen Code is an open-source Gemini CLI fork (verified 2026-07-21 against
https://qwenlm.github.io/qwen-code-docs/). It reads the full parity surface set,
not just an instruction file:

  - **Instruction**: project-root ``QWEN.md`` and global ``~/.qwen/QWEN.md``
    (marker-merged; the ``{{SKILL_INDEX}}`` block is embedded there too).
  - **Skills**: folder-per-skill ``SKILL.md`` one level deep at ``~/.qwen/skills/``
    (global) and ``.qwen/skills/`` (project). Flattened; each catalog command also
    surfaces as a skill. Qwen does NOT read the shared ``~/.agents/skills`` alias,
    so only the native paths are written.
  - **Commands**: ``~/.qwen/commands/<name>.md`` (global) and ``.qwen/commands/``
    (project). MARKDOWN is Qwen's primary/recommended command format; TOML is
    DEPRECATED and triggers an in-product migration prompt, so the catalog's
    Markdown command bodies are mirrored verbatim (like Cursor), NOT converted to
    TOML.
  - **Agents**: ``~/.qwen/agents/<name>.md`` (global) and ``.qwen/agents/`` (project).
  - **Rules**: none as a folder -- Qwen uses ``QWEN.md`` for guidance.

Reclassified from instruction-file-only to a full skills + commands + agents mirror
in v3.15.0 Phase 4 (acting on the Gemini-CLI-class GO from Phase 1). Global scope is
detection-gated on ``~/.qwen`` (preserving the prior behavior + the Windsurf model).

DF-2 caveat: Qwen open issue #2343 reports project-scoped skills may not auto-load
on some builds until a restart. Skills are delivered to BOTH the reliable global
``~/.qwen/skills/`` and the project ``.qwen/skills/``; Qwen's own docs note skills
load on the next start, so a restart after install picks them up.
"""

from __future__ import annotations

from pathlib import Path

from ._command_surface import mirror_command_surface
from .base import InstallContext, MarkdownIntegration, SkillsIntegration
from .result import WriteResult


class QwenIntegration(MarkdownIntegration, SkillsIntegration):
    key = "qwen"
    display_name = "Qwen Code"
    instruction_mode = "shared"
    config = {
        # Global surfaces live under ~/.qwen, written by install_global below
        # (detection-gated), so there is no simple home-relative global_dir.
        "global_dir": None,
        # Skills/agents mirror under .qwen/; QWEN.md lands at the project root.
        "workspace_dir": ".qwen",
        "instruction_workspace_dir": "",
        "instruction_file": "QWEN.md",
        "instruction_template": "templates/ai-instructions/base-qwen.md",
        "skills_subdir": "skills",
        "flatten_skills_layout": True,
        "agents_subdir": "agents",
        "hooks_supported": False,
    }

    def install_workspace(self, ctx: InstallContext) -> WriteResult:
        # super() (MarkdownIntegration -> SkillsIntegration) writes the project-root
        # QWEN.md (instruction_workspace_dir="") and mirrors skills + agents under
        # .qwen/ (workspace_dir). Add the native Markdown command surface.
        result = super().install_workspace(ctx)
        if not ctx.instruction_only:
            commands_dst = (ctx.target_root / self.config["workspace_dir"] / "commands").resolve()
            self._ensure_dir(commands_dst, ctx)
            result.files.extend(
                mirror_command_surface(ctx, self.key, commands_dst, suffix=".md")
            )
        return result

    def install_global(self, ctx: InstallContext) -> WriteResult:
        """Write the ``~/.qwen`` surfaces when Qwen is detected, else skip with a note.

        Detection: the Qwen config root ``~/.qwen`` must exist. When it does not,
        Qwen is not installed for this user and the global write is skipped (the
        workspace-scope project surfaces are unaffected).
        """
        result = WriteResult()
        qwen_root = (Path.home() / ".qwen").resolve()
        if not qwen_root.exists():
            ctx.manifest.log(self.key, "~/.qwen not found; skipping global Qwen surfaces")
            result.mark_not_detected("Qwen (~/.qwen) not found; global QWEN.md + skills skipped")
            return result
        result.detected = True
        self._ensure_dir(qwen_root, ctx)
        action = self._write_instruction(qwen_root, ctx)
        if action is not None:
            result.files.append(action)
        if not ctx.instruction_only:
            result.files.extend(self._mirror_catalog(qwen_root, ctx))
            commands_dst = qwen_root / "commands"
            self._ensure_dir(commands_dst, ctx)
            result.files.extend(
                mirror_command_surface(ctx, self.key, commands_dst, suffix=".md")
            )
        return result
