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


class CopilotIntegration(MarkdownIntegration):
    key = "copilot"
    display_name = "GitHub Copilot (Microsoft)"
    # Copilot has a bespoke append-after-existing-header flow predating the
    # marker-merge primitive; the `instruction_mode` attribute is set here for
    # documentation but does not change behavior (this subclass overrides
    # `install_workspace` entirely).
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
        marker = "## Nexus-Hub Harness"
        # Always emit the marker so a subsequent install can detect prior
        # ownership and short-circuit to `kept`. The first install on a fresh
        # workspace writes `<marker>\n\n<rendered>\n`; the same shape is what
        # later installs see and skip.
        managed_block = marker + "\n\n" + rendered.rstrip() + "\n"
        managed_bytes = managed_block.encode("utf-8")
        if dst.exists() and not ctx.overwrite:
            existing = dst.read_text(encoding="utf-8")
            if marker not in existing:
                merged = existing.rstrip() + "\n\n" + managed_block
                merged_bytes = merged.encode("utf-8")
                if existing.encode("utf-8") == merged_bytes:
                    ctx.manifest.track(self.key, str(dst))
                    result.files.append(FileAction(path=str(dst), action="unchanged"))
                else:
                    if not ctx.dry_run:
                        dst.write_bytes(merged_bytes)
                    ctx.manifest.track(self.key, str(dst))
                    result.files.append(FileAction(path=str(dst), action="updated"))
            else:
                ctx.manifest.log(self.key, f"skip-existing-with-marker: {dst}")
                result.files.append(FileAction(path=str(dst), action="kept"))
        else:
            existed = dst.exists()
            if not ctx.dry_run:
                dst.write_bytes(managed_bytes)
            ctx.manifest.track(self.key, str(dst))
            result.files.append(
                FileAction(path=str(dst), action="updated" if existed else "created")
            )
        return result
