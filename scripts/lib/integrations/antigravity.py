"""Google Antigravity integrations (1.0 IDE and 2.0 desktop + CLI).

Antigravity 1.0 (the original IDE released ahead of I/O 2026): customizations
live under the IDE's Customizations menu and on disk under
`~/.gemini/antigravity/`. Rules + Workflows.

Antigravity 2.0 + CLI (announced at Google I/O 2026; CLI transition announced
2026-05-21): standalone agent-first platform that ships a desktop IDE, a CLI
(`agy`), and an SDK against a shared backend. Project instructions live in the
project-root `AGENTS.md`; project customization surfaces live below `.agents/`.

On-disk conventions (verified 2026-06-10 against Google's public Antigravity
docs + codelabs, superseding the 2026-05-29 static probe in
docs/archive/v2/v2.2/antigravity-cli-probe.md):

  - **Skills are a FLAT folder-per-skill**: `skills/<skill-name>/SKILL.md`
    (frontmatter `description` mandatory, `name` optional -> defaults to the
    folder name). Antigravity scans ONE level under `skills/`, so the catalog's
    `<category>/<skill-name>/SKILL.md` layout MUST be flattened on install --
    a verbatim copy buries every SKILL.md under a category folder Antigravity
    reads as a (skill-less) skill and nothing registers. This is the bug this
    integration fixes (skills + commands were invisible in the 2.0 IDE).
  - **Workflows are the slash-command surface**: `workflows/<name>.md`, invoked
    as `/<name>`. The catalog's `commands/*.md` are already flat, so they mirror
    verbatim (byte-identical, no TOML wrapping -- that is the Gemini CLI schema).
  - **Global scope splits by surface**: the desktop **IDE** reads global content
    from `~/.gemini/config/`; the **`agy` CLI** reads settings from
    `~/.gemini/antigravity-cli/` while sharing `~/.gemini/GEMINI.md` and the
    documented Gemini agent/skill roots. CLI-specific loose workflow and hook
    directories remain unverified and are therefore not emitted automatically.

Residual CLI workflow and hook paths remain unverified. The adapter does not
guess those destinations; a future official contract can enable them.
"""

from __future__ import annotations

import json
from pathlib import Path

from ._catalog_adapters import (
    catalog_skill_names,
    commands_to_skills,
    commands_to_slash,
    flatten_skills,
)
from ._hooks_common import command_for, is_windows_host, sourced_modules
from .base import InstallContext, MarkdownIntegration, SkillsIntegration
from .result import FileAction, WriteResult


class Antigravity10Integration(MarkdownIntegration, SkillsIntegration):
    """Antigravity 1.0 (the original pre-2.0 IDE). DEPRECATED and NOT installer-wired.

    v3.11.0 read-contract audit (C3): the ``antigravity`` key is retained in the
    registry for reference and back-compat, but no installer block invokes it and it
    is not in the installers' ``--platforms`` vocabulary. Antigravity 2.0 + CLI
    (``Antigravity20Integration`` below) supersedes it and covers current users.
    Outright removal is deferred to avoid churning the registry-key set that tests
    assert on; this note resolves the "registered but unreachable" confusion.
    """

    key = "antigravity"
    display_name = "Antigravity 1.0 (Google)"
    instruction_mode = "shared"
    config = {
        "global_dir": "~/.gemini/antigravity",
        "workspace_dir": ".gemini/antigravity",
        "instruction_file": "rules.md",
        "instruction_template": "templates/ai-instructions/base-antigravity-10.md",
        "skills_subdir": "skills",
        "commands_subdir": "global_workflows",
        "rules_subdir": "rules_library",
        "hooks_supported": False,
    }


class Antigravity20Integration(MarkdownIntegration, SkillsIntegration):
    """Covers both the Antigravity 2.0 desktop IDE and the Antigravity CLI (`agy`).

    Global read-paths (verified 2026-07-13 against the current Antigravity docs;
    see docs/policy/platform-read-contracts.md and the codelabs cited there):

      - IDE global skills:    ``~/.gemini/config/skills/<name>/`` (flattened, one level)
      - IDE global slash cmds: ``~/.gemini/config/global_workflows/<name>.md``
      - IDE global rules:     ``~/.gemini/GEMINI.md`` (shared with the ``gemini``
        integration; marker-merge keeps both coexisting -- one Nexus-Hub block)
      - CLI global skills:    ``~/.gemini/antigravity-cli/skills/<name>/`` (flattened)
      - project (all):        ``<project>/.agents/{skills,workflows,rules,hooks}``

    The prior version wrote global content under ``~/.gemini/antigravity/`` (which
    the IDE does not read) and did not expose commands as skills. This integration
    now (a) flattens skills into each surface's skills dir, (b) emits every command
    BOTH as a slash workflow AND as a skill (so both ``/name`` and skill-invocation
    work), and (c) installs the hook scripts plus an Antigravity-schema
        ``hooks.json`` for the verified IDE/workspace surface. Workspace
        instructions now use the documented project-root ``AGENTS.md``.
    """

    key = "antigravity2"
    display_name = "Antigravity 2.0 + CLI (Google)"
    instruction_mode = "shared"
    config = {
        # IDE catalog root (skills, global_workflows) is ~/.gemini/config; IDE rules
        # live at the sibling ~/.gemini/GEMINI.md. The `agy` CLI reads its catalog
        # from ~/.gemini/antigravity-cli. Project scope is .agents/. install_global /
        # install_workspace below use these explicitly (no generic root loop).
        "global_dir": "~/.gemini/config",
        "cli_global_dir": "~/.gemini/antigravity-cli",
        "ide_rules_file": "~/.gemini/GEMINI.md",
        "workspace_dir": ".agents",
        # Antigravity reads the WORKSPACE-ROOT AGENTS.md, not .agents/AGENTS.md.
        # install_workspace writes it to the root; declaring the empty instruction
        # dir keeps this config the single source of truth for that placement.
        "instruction_workspace_dir": "",
        "instruction_file": "AGENTS.md",
        "instruction_template": "templates/ai-instructions/base-antigravity-20.md",
        "skills_subdir": "skills",
        "commands_subdir": "workflows",
        "ide_commands_subdir": "global_workflows",
        "agents_subdir": "agents",
        "rules_subdir": "rules",
        "hooks_subdir": "hooks",
        "hooks_supported": True,
    }

    # Curated, platform-agnostic hooks ported to Antigravity. Excludes the
    # Claude-CLI-specific hooks (approval-dialog formatters, usage display, etc.)
    # that have no meaning outside Claude Code. `matcher` uses the documented
    # Antigravity tool names so unrelated tool calls never enter file guards.
    def _hook_registration(self, wrapped_command_for) -> dict:
        return {
            "nexus-hub-guardrails": {
                "enabled": True,
                "PreToolUse": [
                    {
                        "matcher": (
                            "write_to_file|replace_file_content|"
                            "multi_replace_file_content"
                        ),
                        "hooks": [
                            {"command": wrapped_command_for("secret-scan.sh")},
                            {"command": wrapped_command_for("large-file-guard.sh")},
                        ],
                    },
                    {
                        "matcher": "run_command",
                        "hooks": [
                            {"command": wrapped_command_for("git-guardrails.sh")},
                        ],
                    },
                ],
            },
        }

    _CURATED_HOOK_SCRIPTS = (
        "secret-scan.sh",
        "large-file-guard.sh",
        "git-guardrails.sh",
    )

    # ----- install entry points -------------------------------------------

    def install_global(self, ctx: InstallContext) -> WriteResult:
        result = WriteResult()
        gemini_home = (Path.home() / ".gemini").resolve()

        # IDE surface: catalog under ~/.gemini/config, rules at ~/.gemini/GEMINI.md.
        config_root = gemini_home / "config"
        self._ensure_dir(config_root, ctx)
        result.files.append(self._write_instruction_file(gemini_home / "GEMINI.md", ctx))
        if not ctx.instruction_only:
            result.files.extend(
                self._mirror_surface(
                    config_root, ctx, scope="global",
                    commands_subdir=self.config["ide_commands_subdir"],
                )
            )

        # CLI surface: keep the verified skill root. Global instructions are the
        # shared ~/.gemini/GEMINI.md written above; CLI-only workflow, agent,
        # rule, and hook destinations are not documented, so do not invent them.
        cli_root = gemini_home / "antigravity-cli"
        self._ensure_dir(cli_root, ctx)
        if not ctx.instruction_only:
            result.files.extend(
                self._mirror_surface(
                    cli_root, ctx, scope="global",
                    commands_subdir=self.config["commands_subdir"],
                    include_slash_commands=False,
                    include_agents=False,
                    include_rules=False,
                    include_hooks=False,
                )
            )
        return result

    def install_workspace(self, ctx: InstallContext) -> WriteResult:
        result = WriteResult()
        root = ctx.target_root.resolve()
        parent = (root / self.config["workspace_dir"]).resolve()
        self._ensure_dir(parent, ctx)
        result.files.append(
            self._write_instruction_file(root / self.config["instruction_file"], ctx)
        )
        if not ctx.instruction_only:
            result.files.extend(
                self._mirror_surface(
                    parent, ctx, scope="workspace",
                    commands_subdir=self.config["commands_subdir"],
                )
            )
        return result

    def wire_project_surfaces(self, ctx: InstallContext) -> WriteResult:
        """Seed the current repo's ``.agents/`` surfaces for ``nexus-hub init``.

        Beyond the corrected global read-paths, the Antigravity 2.0 IDE also reads
        slash commands, skills, and rules from the OPEN project's ``.agents/``.
        ``nexus-hub init`` writes that tree into the current repo so the catalog is
        available project-scoped too. Mirrors the workspace ``.agents/`` content but
        leaves the shared ``AGENTS.md`` instruction file to the install flow.
        """
        result = WriteResult()
        parent = (ctx.target_root / self.config["workspace_dir"]).resolve()
        self._ensure_dir(parent, ctx)
        result.files.extend(
            self._mirror_surface(
                parent, ctx, scope="workspace",
                commands_subdir=self.config["commands_subdir"],
            )
        )
        return result

    # ----- mirror helpers --------------------------------------------------

    def _write_instruction_file(self, dst_path: Path, ctx: InstallContext) -> FileAction:
        """Render base-antigravity-20.md and marker-merge it into an explicit path.

        Mirrors ``MarkdownIntegration._write_instruction`` shared-mode behavior but
        to a caller-chosen path (the IDE rules file is ``~/.gemini/GEMINI.md``,
        while the CLI and workspace use ``AGENTS.md``). Tracked as a shared file so
        only the Nexus-Hub marker block is removed on teardown -- important because
        ``~/.gemini/GEMINI.md`` is shared with the ``gemini`` integration.
        """
        from scripts.lib.installer.instruction_merge import merge_marker_section

        template_path = ctx.repo_root / self.config["instruction_template"]
        if not template_path.exists():
            ctx.manifest.log(self.key, f"missing-template: {template_path}")
            return FileAction(path=str(template_path), action="not-found")
        rendered = self._render(template_path, ctx)
        if not ctx.dry_run:
            dst_path.parent.mkdir(parents=True, exist_ok=True)
        action = merge_marker_section(
            dst_path, rendered, legacy_header="## Nexus-Hub", dry_run=ctx.dry_run
        )
        ctx.manifest.track_shared(self.key, str(dst_path))
        return action

    def _mirror_surface(
        self,
        root: Path,
        ctx: InstallContext,
        scope: str,
        commands_subdir: str,
        *,
        include_slash_commands: bool = True,
        include_agents: bool = True,
        include_rules: bool = True,
        include_hooks: bool = True,
    ) -> list[FileAction]:
        """Lay the catalog into one Antigravity surface in the shape it reads.

        Skills are flattened one level (``skills/<name>/``) and every command is
        emitted BOTH as a slash workflow (``<commands_subdir>/<name>.md``) and as a
        skill (``skills/<name>/SKILL.md``) so both ``/name`` and skill-invocation
        work. Agents/rules trees are additive (Antigravity ignores what it does not
        consume); hooks + hooks.json are installed per the schema.
        """
        src_skills = ctx.repo_root / "catalog" / "skills"
        src_commands = ctx.repo_root / "catalog" / "commands"
        skills_dst = root / self.config["skills_subdir"]
        existing = catalog_skill_names(src_skills)

        actions: list[FileAction] = []
        actions.extend(flatten_skills(ctx, self.key, src_skills, skills_dst))
        actions.extend(commands_to_skills(ctx, self.key, src_commands, skills_dst, existing))
        if include_slash_commands:
            actions.extend(
                commands_to_slash(
                    ctx,
                    self.key,
                    src_commands,
                    root / commands_subdir,
                    style="verbatim",
                )
            )
        catalog_trees = []
        if include_agents:
            catalog_trees.append(("agents_subdir", "catalog/agents"))
        if include_rules:
            catalog_trees.append(("rules_subdir", "catalog/rules"))
        for cfg_key, src_rel in catalog_trees:
            subdir = self.config.get(cfg_key)
            if subdir:
                actions.append(
                    self._copy_tree(ctx.repo_root / src_rel, root / subdir, ctx, self.key)
                )
        # Gate the bespoke hooks.json + script install on the declared
        # capability (`hooks_supported`), mirroring the base-class gate so a
        # platform's hook support is declared in exactly one place. Antigravity
        # 2.0 sets `hooks_supported: True`, so this is byte-identical today.
        if include_hooks and self.config.get("hooks_supported"):
            actions.extend(self._install_hooks(root, ctx, scope))
        return actions

    def _install_hooks(
        self, parent: Path, ctx: InstallContext, scope: str
    ) -> list[FileAction]:
        """Copy the curated hook scripts and write the Antigravity hooks.json."""
        src_hooks = ctx.repo_root / "catalog" / "hooks"
        if not src_hooks.exists():
            ctx.manifest.log(self.key, f"missing-tree: {src_hooks}")
            return [FileAction(path=str(src_hooks), action="not-found")]
        hooks_dst = parent / self.config["hooks_subdir"]
        self._ensure_dir(hooks_dst, ctx)
        actions: list[FileAction] = []
        scripts = set(self._CURATED_HOOK_SCRIPTS)
        scripts |= {f"{Path(script).stem}.ps1" for script in self._CURATED_HOOK_SCRIPTS}
        scripts |= sourced_modules(scripts, src_hooks)
        for script in sorted(scripts):
            actions.append(
                self._copy_file(src_hooks / script, hooks_dst / script, ctx, self.key)
            )
        actions.append(
            self._copy_file(
                ctx.repo_root
                / "scripts"
                / "lib"
                / "integrations"
                / "_cascade_hook_compat.py",
                hooks_dst / "antigravity-hook-compat.py",
                ctx,
                self.key,
            )
        )
        actions.append(self._write_hooks_json(parent, hooks_dst, ctx, scope))
        return actions

    def _write_hooks_json(
        self, parent: Path, hooks_dst: Path, ctx: InstallContext, scope: str
    ) -> FileAction:
        """Render and write <parent>/hooks.json in Antigravity's schema.

        Workspace hooks reference scripts by a project-root-relative path
        (`.agents/hooks/<script>`); global hooks reference the resolved absolute
        path. `.sh` scripts run under `bash`, `.py` under `python3`, matching the
        Claude settings.json convention. On Windows the `.sh` hooks need a Unix
        shell (git-bash), exactly as the existing Claude/rtk hooks document.
        """
        if scope == "workspace":
            base = f"{self.config['workspace_dir']}/{self.config['hooks_subdir']}"
        else:
            base = hooks_dst.as_posix()

        windows = is_windows_host()

        def wrapped_command_for(script: str) -> str:
            host_script = f"{Path(script).stem}.ps1" if windows else script
            compat_runner = "python" if windows else "python3"
            compat = f'{compat_runner} "{base}/antigravity-hook-compat.py"'
            child = command_for(host_script, base, windows)
            return f"{compat} antigravity PreToolUse -- {child}"

        content = json.dumps(self._hook_registration(wrapped_command_for), indent=2) + "\n"
        content_bytes = content.encode("utf-8")
        dst = parent / "hooks.json"
        if dst.exists():
            if dst.read_bytes() == content_bytes:
                ctx.manifest.track(self.key, str(dst))
                return FileAction(path=str(dst), action="unchanged")
            if not ctx.overwrite:
                # Preserve user edits to an existing hooks.json.
                ctx.manifest.log(self.key, f"skip-existing: {dst}")
                return FileAction(path=str(dst), action="kept")
        existed = dst.exists()
        if not ctx.dry_run:
            dst.parent.mkdir(parents=True, exist_ok=True)
            dst.write_bytes(content_bytes)
        ctx.manifest.track(self.key, str(dst))
        return FileAction(path=str(dst), action="updated" if existed else "created")
