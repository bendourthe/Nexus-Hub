"""Cursor integration.

Cursor (2.4+) reads a broad surface set (verified 2026-07-20, v3.15.0 Phase 1.2;
see docs/policy/platform-read-contracts.md and the parity_verification_v3_15_0
block in the sibling .json):

  - **Rules**: project ``.cursor/rules/<name>.mdc`` (Markdown + YAML frontmatter)
    plus ``AGENTS.md`` at repo root as the canonical instruction file.
  - **Commands**: global ``~/.cursor/commands/<name>.md`` (offered as ``/<name>``
    in ANY repo) AND project ``<project>/.cursor/commands/<name>.md``.
  - **Skills**: folder-per-skill ``SKILL.md``, discovered one level deep, at
    ``~/.cursor/skills/<name>/`` (global) and ``.cursor/skills/<name>/`` (project).
    Cursor ALSO reads the shared ``~/.agents/skills`` and ``~/.claude/skills``
    aliases, but this integration writes ONLY Cursor's native ``skills`` dir: the
    shared ``~/.agents/skills`` is populated by the codex integration on a full
    install, and writing it here too would let ``uninstall --platforms cursor``
    delete codex's skills (both track the same paths). Native-only avoids that
    shared-path teardown conflict while a Cursor-only install still gets skills.
  - **Subagents**: ``~/.cursor/agents/<name>.md`` (global) and ``.cursor/agents/``
    (project) -- plain ``.md`` with YAML frontmatter, exactly the shape of the
    catalog's ``catalog/agents/*.md`` files (NOT ``.agent.md``).
  - **Hooks**: ``~/.cursor/hooks.json`` (global) and ``<project>/.cursor/hooks.json``
    (project), in Cursor's own schema (``{"version": 1, "hooks": {...}}``), with the
    hook scripts under ``.cursor/hooks/``. Gated on ``hooks_supported``.

Cursor's hook event model differs from Claude's: it has no before-file-write
blocking event (only ``afterFileEdit``), and hooks receive a Cursor-shaped stdin
JSON rather than Claude's. Only ``git-guardrails`` maps onto a clean, blocking
event (``beforeShellExecution``; exit code 2 blocks). The curated script is
shipped there; because it currently parses Claude's stdin shape it degrades to a
fail-open no-op on Cursor (never a wrong block) until a follow-up adapts its stdin
parsing -- tracked in the version's known-gaps.
"""

from __future__ import annotations

import json
from pathlib import Path

from ._catalog_adapters import (
    catalog_skill_names,
    commands_to_skills,
    flatten_skills,
)
from ._command_surface import mirror_command_surface
from .base import InstallContext, MarkdownIntegration, SkillsIntegration, YamlIntegration
from .result import FileAction, WriteResult
from scripts.lib.installer.instruction_merge import merge_marker_section


class CursorIntegration(MarkdownIntegration, YamlIntegration, SkillsIntegration):
    key = "cursor"
    display_name = "Cursor"
    instruction_mode = "shared"
    config = {
        "global_dir": None,
        "workspace_dir": ".cursor",
        "instruction_file": "AGENTS.md",
        "instruction_template": "templates/ai-instructions/base-cursor.md",
        # Skills discovered one level deep (folder-per-skill SKILL.md), so flatten
        # the catalog's <category>/ layer and surface each command as a skill too.
        "skills_subdir": "skills",
        "flatten_skills_layout": True,
        # Subagents: catalog/agents/*.md (plain .md + frontmatter) copied verbatim.
        "agents_subdir": "agents",
        # Project-scoped slash commands (in addition to the global ~/.cursor/commands/).
        "commands_subdir": "commands",
        "rules_subdir": "rules",
        # hooks.json + hooks/ script dir; gated on hooks_supported (v3.15.0).
        "hooks_subdir": "hooks",
        "hooks_supported": True,
    }

    # Only git-guardrails maps onto a clean, blocking Cursor event
    # (beforeShellExecution -> exit 2 blocks a destructive git command). The other
    # Nexus-Hub guardrails (secret-scan, large-file-guard) guard file WRITES, for
    # which Cursor exposes no before-write blocking event, so they are intentionally
    # not shipped here (post-hoc afterFileEdit cannot prevent the write).
    _CURATED_HOOK_SCRIPTS = ("git-guardrails.sh",)

    def _hook_registration(self, command_for) -> dict:
        """Return the Cursor hooks.json body (schema: version 1, hooks object).

        git-guardrails runs on every shell execution and self-filters to
        destructive git commands, so no matcher is needed (beforeShellExecution
        already scopes to shell commands).
        """
        return {
            "version": 1,
            "hooks": {
                "beforeShellExecution": [
                    {"command": command_for("git-guardrails.sh")},
                ],
            },
        }

    # ----- install entry points -------------------------------------------

    def install_global(self, ctx: InstallContext) -> WriteResult:
        """Mirror the global Cursor surfaces from ``~/.cursor/``.

        Cursor offers every ``~/.cursor/commands/<name>.md`` as ``/<name>`` in any
        repo, so the commands mirror makes the catalog available globally with no
        per-project install. Skills, agents, and hooks land in ``~/.cursor/`` too.
        """
        result = super().install_global(ctx)  # instruction no-op (global_dir=None)
        cursor_root = (Path.home() / ".cursor").resolve()
        self._ensure_dir(cursor_root, ctx)
        commands_dir = cursor_root / self.config["commands_subdir"]
        self._ensure_dir(commands_dir, ctx)
        result.files.extend(
            mirror_command_surface(ctx, self.key, commands_dir, suffix=".md")
        )
        if not ctx.instruction_only:
            result.files.extend(self._mirror_catalog_surfaces(cursor_root, ctx, scope="global"))
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
        self._ensure_dir(cursor_root, ctx)
        result.files.extend(self._install_rules(cursor_root, ctx))
        if not ctx.instruction_only:
            # Project-scoped slash commands (in addition to the global surface).
            commands_dir = cursor_root / self.config["commands_subdir"]
            self._ensure_dir(commands_dir, ctx)
            result.files.extend(
                mirror_command_surface(ctx, self.key, commands_dir, suffix=".md")
            )
            result.files.extend(self._mirror_catalog_surfaces(cursor_root, ctx, scope="workspace"))
        return result

    # ----- surface helpers -------------------------------------------------

    def _install_rules(self, cursor_root: Path, ctx: InstallContext) -> list[FileAction]:
        """Flatten catalog/rules/**.md into ``<cursor_root>/rules/<flat>.mdc``."""
        actions: list[FileAction] = []
        rules_dst = cursor_root / self.config["rules_subdir"]
        if not ctx.dry_run:
            rules_dst.mkdir(parents=True, exist_ok=True)
        rules_src_root = ctx.repo_root / "catalog" / "rules"
        if not rules_src_root.exists():
            actions.append(FileAction(path=str(rules_src_root), action="not-found"))
            return actions
        for md in sorted(rules_src_root.rglob("*.md")):
            rel = md.relative_to(rules_src_root)
            flat_name = "-".join(rel.with_suffix("").parts) + ".mdc"
            dst = rules_dst / flat_name
            content = self._md_to_mdc(md, scope="auto")
            content_bytes = content.encode("utf-8")
            if dst.exists() and not ctx.overwrite:
                if dst.read_bytes() == content_bytes:
                    ctx.manifest.track(self.key, str(dst))
                    actions.append(FileAction(path=str(dst), action="unchanged"))
                else:
                    ctx.manifest.log(self.key, f"skip-existing: {dst}")
                    actions.append(FileAction(path=str(dst), action="kept"))
                continue
            existed = dst.exists()
            if not ctx.dry_run:
                dst.write_bytes(content_bytes)
            ctx.manifest.track(self.key, str(dst))
            actions.append(
                FileAction(path=str(dst), action="updated" if existed else "created")
            )
        return actions

    def _mirror_catalog_surfaces(
        self, cursor_root: Path, ctx: InstallContext, scope: str
    ) -> list[FileAction]:
        """Write skills (flattened + command-skills), agents, and hooks to ``cursor_root``.

        Skills go ONLY to Cursor's native ``skills`` dir (see the module docstring
        for why the shared ``~/.agents/skills`` is deliberately not written here).
        """
        actions: list[FileAction] = []
        src_skills = ctx.repo_root / "catalog" / "skills"
        src_commands = ctx.repo_root / "catalog" / "commands"
        skills_dst = cursor_root / self.config["skills_subdir"]
        actions.extend(flatten_skills(ctx, self.key, src_skills, skills_dst))
        actions.extend(
            commands_to_skills(
                ctx, self.key, src_commands, skills_dst, catalog_skill_names(src_skills)
            )
        )
        # Subagents: catalog/agents/*.md copied verbatim (Cursor reads .md + frontmatter).
        agents_subdir = self.config.get("agents_subdir")
        if agents_subdir:
            actions.append(
                self._copy_tree(
                    ctx.repo_root / "catalog" / "agents",
                    cursor_root / agents_subdir,
                    ctx,
                    self.key,
                )
            )
        if self.config.get("hooks_supported"):
            actions.extend(self._install_hooks(cursor_root, ctx, scope))
        return actions

    def _install_hooks(
        self, cursor_root: Path, ctx: InstallContext, scope: str
    ) -> list[FileAction]:
        """Copy the curated hook scripts and write Cursor's hooks.json."""
        src_hooks = ctx.repo_root / "catalog" / "hooks"
        if not src_hooks.exists():
            ctx.manifest.log(self.key, f"missing-tree: {src_hooks}")
            return [FileAction(path=str(src_hooks), action="not-found")]
        hooks_dst = cursor_root / self.config["hooks_subdir"]
        self._ensure_dir(hooks_dst, ctx)
        actions: list[FileAction] = []
        for script in self._CURATED_HOOK_SCRIPTS:
            actions.append(
                self._copy_file(src_hooks / script, hooks_dst / script, ctx, self.key)
            )
        actions.append(self._write_hooks_json(cursor_root, hooks_dst, ctx, scope))
        return actions

    def _write_hooks_json(
        self, cursor_root: Path, hooks_dst: Path, ctx: InstallContext, scope: str
    ) -> FileAction:
        """Render and write ``<cursor_root>/hooks.json`` in Cursor's schema.

        Workspace hooks reference scripts by a project-relative path
        (``.cursor/hooks/<script>``); global hooks reference the resolved absolute
        path. ``.sh`` scripts run under ``bash`` (git-bash on Windows, exactly as
        the Claude hooks document). An existing user-edited hooks.json is preserved
        unless ``--overwrite`` is set.
        """
        if scope == "workspace":
            base = f"{self.config['workspace_dir']}/{self.config['hooks_subdir']}"
        else:
            base = hooks_dst.as_posix()

        def command_for(script: str) -> str:
            runner = "python3" if script.endswith(".py") else "bash"
            return f"{runner} {base}/{script}"

        content = json.dumps(self._hook_registration(command_for), indent=2) + "\n"
        content_bytes = content.encode("utf-8")
        dst = cursor_root / "hooks.json"
        if dst.exists():
            if dst.read_bytes() == content_bytes:
                ctx.manifest.track(self.key, str(dst))
                return FileAction(path=str(dst), action="unchanged")
            if not ctx.overwrite:
                ctx.manifest.log(self.key, f"skip-existing: {dst}")
                return FileAction(path=str(dst), action="kept")
        existed = dst.exists()
        if not ctx.dry_run:
            dst.parent.mkdir(parents=True, exist_ok=True)
            dst.write_bytes(content_bytes)
        ctx.manifest.track(self.key, str(dst))
        return FileAction(path=str(dst), action="updated" if existed else "created")

    def wire_project_surfaces(self, ctx: InstallContext) -> WriteResult:
        """Write a single ``.cursor/rules/nexus-hub.mdc`` to the project root.

        Distilled from the workspace install: a global Cursor user keeps the
        catalog at ``~/.cursor/`` but each project still needs the rules file
        Cursor scans. This hook lets ``nexus-hub init`` drop only that file
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
