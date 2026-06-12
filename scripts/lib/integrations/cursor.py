"""Cursor integration.

Cursor uses .cursor/rules/<name>.mdc files (Markdown + YAML frontmatter) for
project rules, plus AGENTS.md at repo root as the canonical instruction file.

Cursor DOES expose a user-global slash-command surface: it scans
``~/.cursor/commands/<name>.md`` (alongside project ``.cursor/commands/``) and
offers each as ``/<name>`` in any repo. A global install therefore mirrors the
catalog's commands there so they are available from every project with no
per-project install (confirmed empirically against a repo with no local
install). Project rules still install per-workspace.
"""

from __future__ import annotations

from pathlib import Path

from .base import InstallContext, MarkdownIntegration, YamlIntegration
from .result import FileAction, WriteResult
from ._command_surface import mirror_command_surface
from scripts.lib.installer.instruction_merge import merge_marker_section


class CursorIntegration(MarkdownIntegration, YamlIntegration):
    key = "cursor"
    display_name = "Cursor"
    instruction_mode = "shared"
    config = {
        "global_dir": None,
        "workspace_dir": ".cursor",
        "instruction_file": "AGENTS.md",
        "instruction_template": "templates/ai-instructions/base-cursor.md",
        "rules_subdir": "rules",
        "hooks_supported": False,
    }

    def install_global(self, ctx: InstallContext) -> WriteResult:
        """Mirror catalog commands into ``~/.cursor/commands/`` (global surface).

        Cursor offers every ``~/.cursor/commands/<name>.md`` as ``/<name>`` in
        any repo, so this makes the Nexus-Hub commands available globally with
        no per-project install. Stale commands from a prior install are pruned.
        """
        result = super().install_global(ctx)
        commands_dir = (Path.home() / ".cursor" / "commands").resolve()
        self._ensure_dir(commands_dir, ctx)
        result.files.extend(
            mirror_command_surface(ctx, self.key, commands_dir, suffix=".md")
        )
        return result

    def install_workspace(self, ctx: InstallContext) -> WriteResult:
        result = WriteResult()
        target_root = ctx.target_root.resolve()
        if not ctx.dry_run:
            target_root.mkdir(parents=True, exist_ok=True)
        instr_dst = target_root / self.config["instruction_file"]
        template = ctx.repo_root / self.config["instruction_template"]
        if not template.exists():
            result.files.append(FileAction(path=str(template), action="not-found"))
        else:
            rendered = self._render(template, ctx)
            action = merge_marker_section(
                instr_dst,
                rendered,
                legacy_header="## Nexus-Hub",
                dry_run=ctx.dry_run,
            )
            ctx.manifest.track_shared(self.key, str(instr_dst))
            result.files.append(action)

        cursor_root = (target_root / self.config["workspace_dir"]).resolve()
        rules_dst = cursor_root / self.config["rules_subdir"]
        if not ctx.dry_run:
            rules_dst.mkdir(parents=True, exist_ok=True)

        rules_src_root = ctx.repo_root / "catalog" / "rules"
        if not rules_src_root.exists():
            result.files.append(FileAction(path=str(rules_src_root), action="not-found"))
            return result

        for md in sorted(rules_src_root.rglob("*.md")):
            rel = md.relative_to(rules_src_root)
            flat_name = "-".join(rel.with_suffix("").parts) + ".mdc"
            dst = rules_dst / flat_name
            content = self._md_to_mdc(md, scope="auto")
            content_bytes = content.encode("utf-8")
            if dst.exists() and not ctx.overwrite:
                if dst.read_bytes() == content_bytes:
                    ctx.manifest.track(self.key, str(dst))
                    result.files.append(FileAction(path=str(dst), action="unchanged"))
                else:
                    ctx.manifest.log(self.key, f"skip-existing: {dst}")
                    result.files.append(FileAction(path=str(dst), action="kept"))
                continue
            existed = dst.exists()
            if not ctx.dry_run:
                dst.write_bytes(content_bytes)
            ctx.manifest.track(self.key, str(dst))
            result.files.append(
                FileAction(path=str(dst), action="updated" if existed else "created")
            )
        return result

    def wire_project_surfaces(self, ctx: InstallContext) -> WriteResult:
        """Write a single `.cursor/rules/nexus-hub.mdc` to the project root.

        Distilled from the workspace install: a global Cursor user keeps the
        catalog at `~/.cursor/` but each project still needs the rules file
        Cursor scans. This hook lets `nexus-hub init` drop only that file
        without rendering AGENTS.md or re-mirroring every catalog rule.
        """
        result = WriteResult()
        rules_dst = (ctx.target_root / self.config["workspace_dir"] / self.config["rules_subdir"]).resolve()
        if not ctx.dry_run:
            rules_dst.mkdir(parents=True, exist_ok=True)
        dst = rules_dst / "nexus-hub.mdc"
        body = (
            "---\n"
            "name: nexus-hub\n"
            "scope: auto\n"
            "---\n\n"
            "# Nexus-Hub project rules\n\n"
            "This project participates in the Nexus-Hub catalog. The agent\n"
            "should defer to the skills, commands, and rules installed under\n"
            "`~/.cursor/` for catalog-level guidance.\n"
        )
        body_bytes = body.encode("utf-8")
        if dst.exists():
            if dst.read_bytes() == body_bytes:
                ctx.manifest.track(self.key, str(dst))
                result.files.append(FileAction(path=str(dst), action="unchanged"))
                return result
            if not ctx.dry_run:
                dst.write_bytes(body_bytes)
            ctx.manifest.track(self.key, str(dst))
            result.files.append(FileAction(path=str(dst), action="updated"))
            return result
        if not ctx.dry_run:
            dst.write_bytes(body_bytes)
        ctx.manifest.track(self.key, str(dst))
        result.files.append(FileAction(path=str(dst), action="created"))
        return result
