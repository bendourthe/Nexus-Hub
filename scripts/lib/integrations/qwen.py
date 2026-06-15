"""Qwen integration.

Qwen Code reads a Markdown instruction file: a project-root ``QWEN.md`` for
project guidance and ``~/.qwen/QWEN.md`` for global guidance. This is a
behavioral-guardrails surface, not a slash-command surface: the catalog's
skills are made discoverable through the embedded ``{{SKILL_INDEX}}`` block
rather than a mirrored file tree.

Workspace scope writes ``<project>/QWEN.md`` (shared marker-merged so user edits
survive a re-install). Global scope writes ``~/.qwen/QWEN.md`` when the Qwen
config root (``~/.qwen``) is present, and skips with a note otherwise (mirroring
the Windsurf detection model).
"""

from __future__ import annotations

from pathlib import Path

from .base import InstallContext, MarkdownIntegration
from .result import FileAction, WriteResult


class QwenIntegration(MarkdownIntegration):
    key = "qwen"
    display_name = "Qwen Code"
    instruction_mode = "shared"
    config = {
        # Global rules live under ~/.qwen, handled by install_global below
        # (gated on detection), so no simple home-relative global_dir.
        "global_dir": None,
        # QWEN.md lands at the project root (where Qwen reads it), so the
        # instruction dir is the workspace root itself.
        "instruction_workspace_dir": "",
        "instruction_file": "QWEN.md",
        "instruction_template": "templates/ai-instructions/base-qwen.md",
        "hooks_supported": False,
    }

    def install_global(self, ctx: InstallContext) -> WriteResult:
        """Write ``~/.qwen/QWEN.md`` when Qwen is detected, else skip with a note.

        Detection: the Qwen config root ``~/.qwen`` must exist. When it does not,
        Qwen is not installed for this user and the global write is skipped (the
        workspace-scope project-root ``QWEN.md`` is the primary surface and is
        unaffected).
        """
        result = WriteResult()
        qwen_root = (Path.home() / ".qwen").resolve()
        if not qwen_root.exists():
            ctx.manifest.log(self.key, "~/.qwen not found; skipping global QWEN.md")
            result.note("Qwen (~/.qwen) not found; global QWEN.md skipped")
            return result
        self._ensure_dir(qwen_root, ctx)
        action = self._write_instruction(qwen_root, ctx)
        if action is not None:
            result.files.append(action)
        return result
