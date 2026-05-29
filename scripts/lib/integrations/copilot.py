"""GitHub Copilot integration.

Copilot (in VS Code) reads .github/copilot-instructions.md at repo root for
custom instructions, and respects the
`github.copilot.chat.codeGeneration.useInstructionFiles` VS Code setting.

Copilot does not have a slash-command surface nor a skills folder; the
catalog/skills/ index is appended to the instruction file as a Skill Index
reference block so the assistant can search by name.

GitHub CLI's `gh copilot` extension is also implicitly supported because it
reads the same .github/copilot-instructions.md and the user's gh-installed
extensions independently.
"""

from __future__ import annotations

from .base import InstallContext, MarkdownIntegration
from .result import FileAction, WriteResult
from scripts.lib.installer.instruction_merge import merge_marker_section


class CopilotIntegration(MarkdownIntegration):
    key = "copilot"
    display_name = "GitHub Copilot (Microsoft)"
    # v2.3.0 / Phase 7 / MT-1 -- Copilot now uses the canonical
    # `merge_marker_section` primitive (like Cursor), migrating the v2.1
    # `## Nexus-Hub Harness` legacy header inline into the marker block so user
    # content above and below the block is preserved across re-installs.
    instruction_mode = "shared"
    config = {
        "global_dir": None,
        "workspace_dir": ".github",
        "instruction_file": "copilot-instructions.md",
        "instruction_template": "templates/ai-instructions/base-codex.md",
        "hooks_supported": False,
        "permissions_file": "configs/permissions/copilot-permissions.json",
    }

    def install_global(self, ctx: InstallContext) -> WriteResult:
        result = WriteResult()
        ctx.manifest.log(self.key, "Copilot has no global instruction-file location on Windows")
        result.note("Copilot has no global instruction-file location")
        return result

    def install_workspace(self, ctx: InstallContext) -> WriteResult:
        result = WriteResult()
        rel = self.config["workspace_dir"]
        target = (ctx.target_root / rel).resolve()
        self._ensure_dir(target, ctx)
        dst = target / self.config["instruction_file"]
        template = ctx.repo_root / self.config["instruction_template"]
        if not template.exists():
            ctx.manifest.log(self.key, f"missing-template: {template}")
            result.files.append(FileAction(path=str(template), action="not-found"))
            return result
        rendered = self._render(template, ctx)
        action = merge_marker_section(
            dst,
            rendered,
            legacy_header="## Nexus-Hub Harness",
            dry_run=ctx.dry_run,
        )
        ctx.manifest.track_shared(self.key, str(dst))
        result.files.append(action)
        return result
