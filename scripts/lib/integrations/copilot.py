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

from pathlib import Path

from .base import InstallContext, MarkdownIntegration


class CopilotIntegration(MarkdownIntegration):
    key = "copilot"
    display_name = "GitHub Copilot (Microsoft)"
    config = {
        "global_dir": None,
        "workspace_dir": ".github",
        "instruction_file": "copilot-instructions.md",
        "instruction_template": "templates/ai-instructions/base-codex.md",
        "hooks_supported": False,
        "permissions_file": "configs/permissions/copilot-permissions.json",
    }

    def install_global(self, ctx: InstallContext) -> None:
        ctx.manifest.log(self.key, "Copilot has no global instruction-file location on Windows")

    def install_workspace(self, ctx: InstallContext) -> None:
        rel = self.config["workspace_dir"]
        target = (ctx.target_root / rel).resolve()
        self._ensure_dir(target, ctx)
        dst = target / self.config["instruction_file"]
        template = ctx.repo_root / self.config["instruction_template"]
        if not template.exists():
            ctx.manifest.log(self.key, f"missing-template: {template}")
            return
        rendered = self._render(template, ctx)
        if dst.exists() and not ctx.overwrite:
            existing = dst.read_text(encoding="utf-8")
            marker = "## Nexus-Hub Harness"
            if marker not in existing:
                merged = existing.rstrip() + "\n\n" + marker + "\n\n" + rendered
                if not ctx.dry_run:
                    dst.write_text(merged, encoding="utf-8")
                ctx.manifest.track(self.key, str(dst))
            else:
                ctx.manifest.log(self.key, f"skip-existing-with-marker: {dst}")
        else:
            if not ctx.dry_run:
                dst.write_text(rendered, encoding="utf-8")
            ctx.manifest.track(self.key, str(dst))
