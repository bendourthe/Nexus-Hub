"""Google Antigravity integrations (1.0 IDE and 2.0 desktop + CLI).

Antigravity 1.0 (the original IDE released ahead of I/O 2026): customizations
live under the IDE's Customizations menu and on disk under
`~/.gemini/antigravity/`. Rules + Workflows.

Antigravity 2.0 + CLI (announced at Google I/O 2026; CLI transition announced
2026-05-21): standalone agent-first platform that ships a desktop IDE, a CLI
(`agy`), and an SDK against a shared backend. The surfaces use a `.agents/`
directory convention -- `.agents/{skills,workflows,rules,hooks}` per-project,
`AGENTS.md` as the project-root instruction file.

On-disk conventions (verified 2026-06-10 against Google's public Antigravity
docs + codelabs, superseding the 2026-05-29 static probe in
docs/archive/v2/v2.2.0/antigravity-cli-probe.md):

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
  - **Hooks** (`hooks.json` + a `hooks/` script dir) are supported and use a
    Claude-compatible event model (PreToolUse/PostToolUse/SessionStart/Stop,
    `matcher` regex, JSON stdin/stdout). The registration file is keyed by named
    hook GROUPS (each with an `enabled` flag), not Claude's flat `hooks` object.
  - **Global scope splits by surface**: the desktop **IDE** reads global content
    from `~/.gemini/antigravity/` (matching the SDK app-data root
    `~/.gemini/antigravity/brain/`); the **`agy` CLI** reads from
    `~/.gemini/antigravity-cli/`. We install to BOTH so a user on either surface
    gets the catalog. Workspace scope is `.agents/` for both.

Residual items still pending a live-VM `agy` smoke (tracked in the current
version's known-gaps): the exact tool-name matchers for file write/edit ops
(`run_command` is confirmed; the file-content guards therefore use a match-all
matcher and self-filter), and whether the hook scripts' stdin field names match
Antigravity's exactly (the scripts are fail-open, so a schema mismatch degrades
to a no-op rather than a false block).
"""

from __future__ import annotations

import json
from pathlib import Path

from .base import InstallContext, MarkdownIntegration, SkillsIntegration
from .result import FileAction, WriteResult


class Antigravity10Integration(MarkdownIntegration, SkillsIntegration):
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

    Unlike the generic ``SkillsIntegration`` verbatim mirror, this integration
    overrides the install path to (a) flatten the skill tree to the flat
    folder-per-skill layout Antigravity discovers, (b) write the catalog to BOTH
    the IDE global root (``~/.gemini/antigravity``) and the CLI global root
    (``~/.gemini/antigravity-cli``), and (c) install the hook scripts plus a
    Antigravity-schema ``hooks.json`` registration. Commands still mirror
    verbatim into ``workflows/`` (the slash-command surface).
    """

    key = "antigravity2"
    display_name = "Antigravity 2.0 + CLI (Google)"
    instruction_mode = "shared"
    config = {
        # The desktop IDE reads global content from ~/.gemini/antigravity/; the
        # `agy` CLI reads from ~/.gemini/antigravity-cli/. Install to both.
        "global_dir": "~/.gemini/antigravity",
        "additional_global_dirs": ["~/.gemini/antigravity-cli"],
        "workspace_dir": ".agents",
        "instruction_file": "AGENTS.md",
        "instruction_template": "templates/ai-instructions/base-antigravity-20.md",
        "skills_subdir": "skills",
        "commands_subdir": "workflows",
        "agents_subdir": "subagents",
        "rules_subdir": "rules",
        "hooks_subdir": "hooks",
        "hooks_supported": True,
        "permissions_file": "configs/permissions/gemini-permissions.json",
    }

    # Curated, platform-agnostic hooks ported to Antigravity. Excludes the
    # Claude-CLI-specific hooks (approval-dialog formatters, usage display, etc.)
    # that have no meaning outside Claude Code. `matcher` uses the confirmed
    # `run_command` tool name for shell hooks; the file-content guards use the
    # match-all matcher ("") because the exact write/edit tool names are not yet
    # live-verified and the scripts self-filter.
    def _hook_registration(self, command_for) -> dict:
        return {
            "nexus-hub-guardrails": {
                "enabled": True,
                "PreToolUse": [
                    {
                        "matcher": "",
                        "hooks": [
                            {"command": command_for("secret-scan.sh")},
                            {"command": command_for("large-file-guard.sh")},
                        ],
                    },
                    {
                        "matcher": "run_command",
                        "hooks": [
                            {"command": command_for("git-guardrails.sh")},
                        ],
                    },
                ],
            },
            "nexus-hub-context-compressor": {
                "enabled": True,
                "PreToolUse": [
                    {
                        "matcher": "run_command",
                        "hooks": [
                            {"command": command_for("compress-output.sh")},
                        ],
                    },
                ],
            },
        }

    _CURATED_HOOK_SCRIPTS = (
        "secret-scan.sh",
        "large-file-guard.sh",
        "git-guardrails.sh",
        "compress-output.sh",
    )

    # ----- install entry points -------------------------------------------

    def install_global(self, ctx: InstallContext) -> WriteResult:
        result = WriteResult()
        targets = [self.config["global_dir"], *self.config.get("additional_global_dirs", [])]
        for rel in targets:
            parent = (Path.home() / rel.lstrip("~/")).resolve()
            self._ensure_dir(parent, ctx)
            action = self._write_instruction(parent, ctx)
            if action is not None:
                result.files.append(action)
            if not ctx.instruction_only:
                result.files.extend(self._mirror_antigravity(parent, ctx, scope="global"))
        return result

    def install_workspace(self, ctx: InstallContext) -> WriteResult:
        result = WriteResult()
        parent = (ctx.target_root / self.config["workspace_dir"]).resolve()
        self._ensure_dir(parent, ctx)
        action = self._write_instruction(parent, ctx)
        if action is not None:
            result.files.append(action)
        if not ctx.instruction_only:
            result.files.extend(self._mirror_antigravity(parent, ctx, scope="workspace"))
        return result

    # ----- mirror helpers --------------------------------------------------

    def _mirror_antigravity(
        self, parent: Path, ctx: InstallContext, scope: str
    ) -> list[FileAction]:
        """Lay the catalog into one Antigravity root in the format it reads."""
        actions: list[FileAction] = []
        actions.extend(self._mirror_flattened_skills(parent, ctx))
        # Commands -> workflows (verbatim, already flat). Agents and rules keep
        # their tree shape (Antigravity ignores any subdir it does not consume).
        for cfg_key, src_rel in (
            ("commands_subdir", "catalog/commands"),
            ("agents_subdir", "catalog/agents"),
            ("rules_subdir", "catalog/rules"),
        ):
            subdir = self.config.get(cfg_key)
            if not subdir:
                continue
            src = ctx.repo_root / src_rel
            actions.append(self._copy_tree(src, parent / subdir, ctx, self.key))
        actions.extend(self._install_hooks(parent, ctx, scope))
        return actions

    def _mirror_flattened_skills(
        self, parent: Path, ctx: InstallContext
    ) -> list[FileAction]:
        """Flatten catalog/skills/<category>/<name>/ -> skills/<name>/.

        Antigravity discovers skills one level under `skills/`, so the catalog's
        category layer must be dropped. Skill folder names are globally unique
        across categories (enforced by the catalog), so flattening cannot
        collide.
        """
        src_skills = ctx.repo_root / "catalog" / "skills"
        skills_dst = parent / self.config["skills_subdir"]
        if not src_skills.exists():
            ctx.manifest.log(self.key, f"missing-tree: {src_skills}")
            return [FileAction(path=str(src_skills), action="not-found")]
        self._ensure_dir(skills_dst, ctx)
        actions: list[FileAction] = []
        for category in sorted(p for p in src_skills.iterdir() if p.is_dir()):
            for skill in sorted(p for p in category.iterdir() if p.is_dir()):
                actions.append(
                    self._copy_tree(skill, skills_dst / skill.name, ctx, self.key)
                )
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
        for script in self._CURATED_HOOK_SCRIPTS:
            actions.append(
                self._copy_file(src_hooks / script, hooks_dst / script, ctx, self.key)
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

        def command_for(script: str) -> str:
            runner = "python3" if script.endswith(".py") else "bash"
            return f"{runner} {base}/{script}"

        content = json.dumps(self._hook_registration(command_for), indent=2) + "\n"
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
