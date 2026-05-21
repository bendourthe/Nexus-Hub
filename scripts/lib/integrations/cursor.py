"""Cursor integration.

Cursor uses .cursor/rules/<name>.mdc files (Markdown + YAML frontmatter) for
project rules, plus AGENTS.md at repo root as the canonical instruction file.
Cursor does not have a slash-command surface; commands surface as rule files
or are invoked manually.
"""

from __future__ import annotations

from pathlib import Path

from .base import InstallContext, MarkdownIntegration, YamlIntegration


class CursorIntegration(MarkdownIntegration, YamlIntegration):
    key = "cursor"
    display_name = "Cursor"
    config = {
        "global_dir": None,
        "workspace_dir": ".cursor",
        "instruction_file": "AGENTS.md",
        "instruction_template": "templates/ai-instructions/base-cursor.md",
        "rules_subdir": "rules",
        "hooks_supported": False,
    }

    def install_workspace(self, ctx: InstallContext) -> None:
        target_root = ctx.target_root.resolve()
        if not ctx.dry_run:
            target_root.mkdir(parents=True, exist_ok=True)
        instr_dst = target_root / self.config["instruction_file"]
        if instr_dst.exists() and not ctx.overwrite:
            ctx.manifest.log(self.key, f"skip-existing: {instr_dst}")
        else:
            template = ctx.repo_root / self.config["instruction_template"]
            if template.exists():
                rendered = self._render(template, ctx)
                if not ctx.dry_run:
                    instr_dst.write_text(rendered, encoding="utf-8")
                ctx.manifest.track(self.key, str(instr_dst))

        cursor_root = (target_root / self.config["workspace_dir"]).resolve()
        rules_dst = cursor_root / self.config["rules_subdir"]
        if not ctx.dry_run:
            rules_dst.mkdir(parents=True, exist_ok=True)

        rules_src_root = ctx.repo_root / "catalog" / "rules"
        if rules_src_root.exists():
            for md in sorted(rules_src_root.rglob("*.md")):
                rel = md.relative_to(rules_src_root)
                flat_name = "-".join(rel.with_suffix("").parts) + ".mdc"
                dst = rules_dst / flat_name
                if dst.exists() and not ctx.overwrite:
                    ctx.manifest.log(self.key, f"skip-existing: {dst}")
                    continue
                content = self._md_to_mdc(md, scope="auto")
                if not ctx.dry_run:
                    dst.write_text(content, encoding="utf-8")
                ctx.manifest.track(self.key, str(dst))
