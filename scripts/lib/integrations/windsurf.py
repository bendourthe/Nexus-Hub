"""Windsurf integration.

Windsurf reads a project-root ``.windsurfrules`` behavioral-guidance file for
project rules, and a global ``global_rules.md`` under
``~/.codeium/windsurf/memories/``. Both are behavioral-guardrails surfaces, not
slash-command surfaces: the catalog's skills are made discoverable through the
embedded ``{{SKILL_INDEX}}`` block rather than a mirrored file tree.

Workspace scope writes ``<project>/.windsurfrules``. Global scope writes
``~/.codeium/windsurf/memories/global_rules.md`` when the Windsurf config root
(``~/.codeium``) is present, and skips with a note otherwise (mirroring the
Copilot VS-Code-dir detection). Both writes are shared (marker-merged) so user
edits survive a re-install.
"""

from __future__ import annotations

from pathlib import Path

from .base import InstallContext, MarkdownIntegration
from .result import FileAction, WriteResult
from scripts.lib.installer.instruction_merge import merge_marker_section


class WindsurfIntegration(MarkdownIntegration):
    key = "windsurf"
    display_name = "Windsurf"
    instruction_mode = "shared"
    config = {
        # Global rules live at the bespoke ~/.codeium/windsurf/memories/ path,
        # handled by install_global below (not a simple home-relative dir).
        "global_dir": None,
        # .windsurfrules lands at the project root (where Windsurf reads it), so
        # the instruction dir is the workspace root itself.
        "instruction_workspace_dir": "",
        "instruction_file": ".windsurfrules",
        "instruction_template": "templates/ai-instructions/base-windsurf.md",
        "hooks_supported": False,
    }

    def install_global(self, ctx: InstallContext) -> WriteResult:
        """Write ``~/.codeium/windsurf/memories/global_rules.md`` when Windsurf
        is detected, else skip with a note.

        Detection: the Windsurf / Codeium config root ``~/.codeium`` must exist.
        When it does not, Windsurf is not installed for this user and the global
        rules write is skipped (the workspace-scope ``.windsurfrules`` is the
        primary surface and is unaffected).
        """
        result = WriteResult()
        codeium_root = (Path.home() / ".codeium").resolve()
        if not codeium_root.exists():
            ctx.manifest.log(self.key, "~/.codeium not found; skipping global Windsurf rules")
            result.note("Windsurf (~/.codeium) not found; global rules skipped")
            return result

        template = ctx.repo_root / self.config["instruction_template"]
        if not template.exists():
            ctx.manifest.log(self.key, f"missing-template: {template}")
            result.files.append(FileAction(path=str(template), action="not-found"))
            return result

        memories_dir = (codeium_root / "windsurf" / "memories").resolve()
        self._ensure_dir(memories_dir, ctx)
        dst = memories_dir / "global_rules.md"
        rendered = self._render(template, ctx)
        action = merge_marker_section(
            dst,
            rendered,
            legacy_header="## Nexus-Hub",
            dry_run=ctx.dry_run,
        )
        ctx.manifest.track_shared(self.key, str(dst))
        result.files.append(action)
        return result
