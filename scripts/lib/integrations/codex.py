"""OpenAI Codex / new ChatGPT desktop app integration.

Codex (the CLI, the IDE extension, and the Codex mode of the new ChatGPT desktop
app that merges Chat + Work + Codex) reads:

  - the AGENTS.md open-standard instruction file (``~/.codex/AGENTS.md`` global +
    the repo-root ``AGENTS.md`` in a project), which carries the ``{{SKILL_INDEX}}``
    block;
  - skills as folder-per-skill ``SKILL.md``, discovered ONE LEVEL DEEP under the
    cross-tool open-standard ``~/.agents/skills/<name>/`` -- invoked as ``$name``;
  - custom prompts (DEPRECATED, but still read) as top-level ``.md`` files under
    ``~/.codex/prompts/``, invoked ``/prompts:name``;
  - custom agents as standalone TOML files under ``~/.codex/agents/`` and
    ``<project>/.codex/agents/`` (v3.15.8);
  - hooks registered in ``hooks.json`` beside an active config layer. Current
    Codex releases load hooks without a mandatory ``[features].hooks`` switch.

Nexus-Hub's catalog is two levels deep (``catalog/skills/<category>/<name>/``), so
a verbatim copy buries every ``SKILL.md`` under a category folder Codex reads as a
skill-less skill and nothing registers. This integration therefore uses the shared
adapters (``scripts/lib/integrations/_catalog_adapters.py``) to (a) FLATTEN skills
into the shared skill root, (b) additionally emit every catalog COMMAND as a skill so
``$presentify`` / ``$implement`` / etc. work in the new desktop app, and (c) keep
the legacy prompts surface so ``/prompts:name`` still works in the CLI. The full
read-contract is documented in ``docs/policy/platform-read-contracts.md``.
"""

from __future__ import annotations

import json
from pathlib import Path

from ._catalog_adapters import (
    catalog_skill_names,
    codex_invocation_policy,
    commands_to_skills,
    commands_to_slash,
    flatten_skills,
)
from ._codex_native import (
    agents_to_codex_toml,
    build_hook_entries,
    merge_hooks_json,
    prune_hooks_json,
)
from ._owned import remove_dir_if_empty
from .base import InstallContext, MarkdownIntegration, SkillsIntegration
from .result import FileAction, WriteResult


class CodexIntegration(MarkdownIntegration, SkillsIntegration):
    key = "codex"
    display_name = "Codex (OpenAI)"
    instruction_mode = "shared"
    config = {
        "global_dir": "~/.codex",
        "workspace_dir": ".codex",
        # Workspace AGENTS.md lands at the project root (the open-standard location
        # Codex / Cursor / OpenCode read); skills/ and prompts/ mirror under .codex/
        # and the cross-tool .agents/. Matches the legacy bash installer (DF-001).
        "instruction_workspace_dir": "",
        "instruction_file": "AGENTS.md",
        "instruction_template": "templates/ai-instructions/base-codex.md",
        # Skills are flattened one level into the documented shared
        # ~/.agents/skills root (see docs/policy/platform-read-contracts.md).
        # Commands surface as skills ($name) there and as legacy top-level
        # prompts (/prompts:name).
        # Codex has no rules/ discovery, so that tree is intentionally NOT created
        # (no dead dirs). Agents and hooks landed in v3.15.8 and are materialized by
        # _codex_native rather than the base copy helpers: agents need a Markdown ->
        # TOML transform, and hooks.json is a shared file that needs a structured
        # merge, so neither is a verbatim tree copy that agents_subdir/hooks_subdir
        # would drive on the base class.
        "skills_subdir": "skills",
        "commands_subdir": "prompts",
        "agents_subdir": "agents",
        "hooks_subdir": "hooks",
        "hooks_supported": True,
    }

    # ----- install entry points -------------------------------------------

    def install_global(self, ctx: InstallContext) -> WriteResult:
        result = WriteResult()
        codex_root = (Path.home() / ".codex").resolve()
        self._ensure_dir(codex_root, ctx)
        action = self._write_instruction(codex_root, ctx)  # ~/.codex/AGENTS.md
        if action is not None:
            result.files.append(action)
        if not ctx.instruction_only:
            agents_root = (Path.home() / ".agents").resolve()
            result.files.extend(self._mirror_codex(codex_root, agents_root, ctx))
            result.files.extend(self._install_native(codex_root, ctx, scope="global"))
            result.notes.extend(self._trust_notes())
        return result

    def install_workspace(self, ctx: InstallContext) -> WriteResult:
        result = WriteResult()
        # Instruction file at the project root (instruction_workspace_dir="").
        root = ctx.target_root.resolve()
        self._ensure_dir(root, ctx)
        action = self._write_instruction(root, ctx)  # <project>/AGENTS.md
        if action is not None:
            result.files.append(action)
        if not ctx.instruction_only:
            codex_root = (ctx.target_root / ".codex").resolve()
            agents_root = (ctx.target_root / ".agents").resolve()
            self._ensure_dir(codex_root, ctx)
            result.files.extend(self._mirror_codex(codex_root, agents_root, ctx))
            result.files.extend(self._install_native(codex_root, ctx, scope="workspace"))
            result.notes.extend(self._trust_notes())
        return result

    # ----- mirror helper ---------------------------------------------------

    def _mirror_codex(
        self, codex_root: Path, agents_root: Path, ctx: InstallContext
    ) -> list:
        """Lay the catalog into Codex's read-shape: flattened skills + command
        skills in the shared skill root, plus the legacy top-level prompts.
        """
        src_skills = ctx.repo_root / "catalog" / "skills"
        src_commands = ctx.repo_root / "catalog" / "commands"
        existing = catalog_skill_names(src_skills)
        actions: list = []
        # The historical ~/.codex/skills duplicate is intentionally absent: the
        # current official contract documents the shared ~/.agents/skills root.
        skills_dst = agents_root / "skills"
        actions.extend(flatten_skills(ctx, self.key, src_skills, skills_dst))
        actions.extend(
            commands_to_skills(ctx, self.key, src_commands, skills_dst, existing)
        )
        # Codex's invocation lever lives in a sidecar, not in SKILL.md, and
        # its polarity is inverted. Must run AFTER command-skill synthesis so
        # generated `disable-model-invocation: true` files get a sidecar.
        actions.extend(codex_invocation_policy(ctx, self.key, skills_dst))
        # Legacy prompts (top-level .md) into ~/.codex/prompts for /prompts:name.
        actions.extend(
            commands_to_slash(
                ctx, self.key, src_commands, codex_root / "prompts", style="codex_prompts"
            )
        )
        return actions

    # ----- native agent + hook surfaces (v3.15.8) --------------------------

    @staticmethod
    def _trust_notes() -> list[str]:
        """Report what the user still has to do for hooks to run.

        Codex requires every non-managed hook to be reviewed and trusted before
        it executes, and records that trust against the hook's hash. Installing a
        hook therefore does not arm it, so the summary says so rather than
        claiming a guardrail the user does not yet have.
        """
        return [
            (
                "Codex hooks are installed but inert until reviewed: run /hooks in "
                "Codex to inspect and trust them."
            ),
        ]

    def _hooks_command_base(self, codex_root: Path, scope: str) -> str:
        """Return the path prefix Codex hook commands resolve against."""
        hooks_subdir = self.config["hooks_subdir"]
        if scope == "workspace":
            return f"{self.config['workspace_dir']}/{hooks_subdir}"
        return (codex_root / hooks_subdir).as_posix()

    def _install_native(
        self, codex_root: Path, ctx: InstallContext, scope: str
    ) -> list[FileAction]:
        """Write the Codex-native agent TOML files and hook registration."""
        actions: list[FileAction] = []
        actions.extend(
            agents_to_codex_toml(
                ctx,
                self.key,
                ctx.repo_root / "catalog" / "agents",
                codex_root / self.config["agents_subdir"],
            )
        )
        actions.extend(self._install_hooks(codex_root, ctx, scope))
        return actions

    def _install_hooks(
        self, codex_root: Path, ctx: InstallContext, scope: str
    ) -> list[FileAction]:
        """Copy the hook scripts Codex can reach and merge them into hooks.json.

        Only the hooks whose event AND matcher have a Codex equivalent are
        registered; the rest are logged as skipped rather than approximated onto
        a matcher Codex would never fire.
        """
        src_hooks = ctx.repo_root / "catalog" / "hooks"
        settings_file = src_hooks / "settings.json"
        if not settings_file.exists():
            ctx.manifest.log(self.key, f"missing-file: {settings_file}")
            return [FileAction(path=str(settings_file), action="not-found")]

        command_base = self._hooks_command_base(codex_root, scope)
        events, scripts, skipped = build_hook_entries(
            json.loads(settings_file.read_text(encoding="utf-8")), src_hooks, command_base
        )
        for reason in skipped:
            ctx.manifest.log(self.key, f"skip-hook {reason}")

        hooks_dst = codex_root / self.config["hooks_subdir"]
        self._ensure_dir(hooks_dst, ctx)
        actions: list[FileAction] = [
            self._copy_file(src_hooks / script, hooks_dst / script, ctx, self.key)
            for script in sorted(scripts)
        ]
        actions.append(
            merge_hooks_json(
                ctx, self.key, codex_root / "hooks.json", events, command_base
            )
        )
        return actions

    # ----- teardown --------------------------------------------------------

    def teardown(self, ctx: InstallContext) -> WriteResult:
        """Remove Nexus-Hub content, leaving shared Codex config intact.

        ``hooks.json`` is a shared file that may hold the user's own hooks, so it
        is pruned of Nexus-Hub handlers instead of deleted, and untracked before
        the manifest teardown runs (which would otherwise remove the whole file).
        No global feature switch is modified; current Codex versions discover
        hooks from the registered hook file directly.
        """
        result = WriteResult()
        roots = self._codex_roots(ctx)
        for codex_root in roots:
            hooks_json = codex_root / "hooks.json"
            owned_base = self._hooks_command_base(codex_root, ctx.scope)
            if str(hooks_json) in set(ctx.manifest.files_for(self.key)):
                result.files.append(
                    prune_hooks_json(hooks_json, owned_base, ctx.dry_run)
                )
                ctx.manifest.untrack(self.key, str(hooks_json))
        result.extend(super().teardown(ctx))
        # Agents and hook scripts are tracked per file, so removing them leaves the
        # parent directory behind. Codex treats an empty agents/ as a no-op, but a
        # dead directory still reads as an install that did not fully uninstall.
        for codex_root in roots:
            for subdir in (self.config["agents_subdir"], self.config["hooks_subdir"]):
                remove_dir_if_empty(codex_root / subdir, ctx, result)
        return result

    def _codex_roots(self, ctx: InstallContext) -> list[Path]:
        if ctx.scope == "global":
            return [(Path.home() / ".codex").resolve()]
        return [(ctx.target_root / ".codex").resolve()]
