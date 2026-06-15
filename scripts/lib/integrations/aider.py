"""Aider integration.

Aider reads a project-root ``CONVENTIONS.md`` behavioral-guidance file when the
user references it from ``.aider.conf.yml`` (``read: CONVENTIONS.md``). This is a
behavioral-guardrails surface, not a slash-command surface: the catalog's skills
are made discoverable through the embedded ``{{SKILL_INDEX}}`` block rather than
a mirrored file tree.

Workspace scope writes ``<project>/CONVENTIONS.md`` (shared marker-merged so user
edits survive a re-install). Global scope is a no-op: Aider has no standard
global Markdown instruction file (its global surface is the YAML
``~/.aider.conf.yml``, which Nexus-Hub does not generate or modify).
"""

from __future__ import annotations

from .base import InstallContext, MarkdownIntegration
from .result import WriteResult


class AiderIntegration(MarkdownIntegration):
    key = "aider"
    display_name = "Aider"
    instruction_mode = "shared"
    config = {
        "global_dir": None,
        # CONVENTIONS.md lands at the project root (where Aider reads it), so the
        # instruction dir is the workspace root itself.
        "instruction_workspace_dir": "",
        "instruction_file": "CONVENTIONS.md",
        "instruction_template": "templates/ai-instructions/base-aider.md",
        "hooks_supported": False,
    }

    def install_global(self, ctx: InstallContext) -> WriteResult:
        """No-op with an explanatory note.

        Aider has no standard global Markdown instruction file; its global
        surface is the YAML ``~/.aider.conf.yml``, which Nexus-Hub does not
        touch. The project-root ``CONVENTIONS.md`` (workspace scope) is the only
        surface this integration writes.
        """
        result = WriteResult()
        ctx.manifest.log(self.key, "no global instruction surface; project-root CONVENTIONS.md only")
        result.note("Aider has no global instruction surface; install at workspace scope for project-root CONVENTIONS.md")
        return result
