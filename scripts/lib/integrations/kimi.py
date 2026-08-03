"""Kimi integration (Kimi Code CLI).

Kimi Code CLI (``MoonshotAI/kimi-code``, data root ``~/.kimi-code/``) reads a full
skills surface plus the merged ``AGENTS.md`` project context (verified 2026-07-21
against https://www.kimi.com/code/docs/):

  - **Instruction**: global ``~/.kimi-code/AGENTS.md``; project ``.kimi-code/AGENTS.md``
    (marker-merged; the ``{{SKILL_INDEX}}`` block is embedded there too).
  - **Skills**: folder-per-skill ``SKILL.md`` one level deep at ``~/.kimi-code/skills/``
    (global) and ``.kimi-code/skills/`` (project). Each skill auto-registers as a
    ``/skill:<name>`` slash command -- skills ARE the command mechanism, there is NO
    separate command file format, so the catalog's commands are surfaced as skills
    too (flattened command-skills). Kimi also honors the cross-tool
    ``~/.agents/skills`` alias, but this integration writes only Kimi's NATIVE
    ``~/.kimi-code/skills`` to avoid an ``uninstall --platforms kimi`` teardown
    conflict with the codex integration that owns the shared path.
  - **Agents**: user-definable Markdown agents at ``~/.kimi-code/agents/``
    (global) and ``.kimi-code/agents/`` (project), added v3.15.8. Kimi documents
    the Claude Code frontmatter shape as loadable, so the catalog's agents are
    copied VERBATIM rather than transformed. Kimi also reads the shared
    ``~/.agents/agents/`` and ``.agents/agents/`` directories, which this
    integration deliberately does NOT write, matching the rule it already follows
    for skills. (The pre-v3.15.8 claim that Kimi had only fixed built-in
    subagents was superseded by the 2026-08-02 re-verification.)
  - **Hooks**: a ``[[hooks]]`` TOML array in ``~/.kimi-code/config.toml``, added
    v3.15.8 at GLOBAL SCOPE ONLY. The project config is ``.kimi-code/local.toml``
    and documents only a ``[workspace]`` table, so no project-scoped hook path is
    supported and none is invented. See ``_kimi_native`` for the
    comment-preserving marker-block merge and why Kimi's four-field-only schema
    rules out the handler-``name`` ownership used for Gemini CLI and Qwen.

MIGRATION (v3.15.0 Phase 4): reclassified from the instruction-file-only surface
that targeted the OLDER, separate "Kimi CLI" product (``~/.kimi/``,
moonshotai.github.io/kimi-cli) to the current "Kimi Code CLI" product
(``~/.kimi-code/``, kimi.com/code/docs). Per the maintainer decision this is a FULL
migration: the ``~/.kimi/`` writes and the Nexus-Hub-invented ``.kimi/agent.yaml``
companion are dropped (neither is read by the current product). A user still on the
old ``~/.kimi/`` Kimi CLI therefore no longer receives a surface; existing
``~/.kimi/`` files from prior installs are left in place (removed only by an
explicit ``uninstall``). Global scope is detection-gated on ``~/.kimi-code``.
"""

from __future__ import annotations

import json
from pathlib import Path

from ._hooks_common import is_windows_host
from ._kimi_native import (
    agents_to_kimi,
    build_kimi_hooks,
    merge_config_hooks,
    prune_config_hooks,
    render_hooks_block,
)
from ._owned import remove_dir_if_empty
from .base import InstallContext, MarkdownIntegration, SkillsIntegration
from .result import FileAction, WriteResult

AGENTS_SUBDIR = "agents"
HOOKS_SUBDIR = "hooks"
CONFIG_FILE = "config.toml"


class KimiIntegration(MarkdownIntegration, SkillsIntegration):
    key = "kimi"
    display_name = "Kimi Code CLI"
    instruction_mode = "shared"
    config = {
        # Global surfaces live under ~/.kimi-code, written by install_global below
        # (detection-gated), so there is no simple home-relative global_dir.
        "global_dir": None,
        # AGENTS.md + skills both mirror under .kimi-code/ at workspace scope.
        "workspace_dir": ".kimi-code",
        "instruction_workspace_dir": ".kimi-code",
        "instruction_file": "AGENTS.md",
        "instruction_template": "templates/ai-instructions/base-kimi.md",
        # Skills flattened one level; each catalog command surfaces as a skill too,
        # which is how commands reach Kimi (as /skill:<name>).
        "skills_subdir": "skills",
        "flatten_skills_layout": True,
        # `agents_subdir` is deliberately NOT set. Setting it would make the base
        # `_mirror_catalog` copy catalog/agents through `_copy_tree`, which is
        # ownership-blind (it keeps any existing destination and so never repairs
        # a drifted owned file) and applies no validation. This integration writes
        # the same tree itself via `_install_agents`, which does both. Setting the
        # key as well would write every agent twice per install.
        #
        # Hooks are likewise a marker-managed block inside the user's config.toml
        # rather than a tree copy, so hooks_subdir is not set either. Global scope
        # only -- Kimi documents no project-scoped hook path.
        "hooks_supported": True,
    }

    def install_workspace(self, ctx: InstallContext) -> WriteResult:
        """Write the project ``.kimi-code`` surfaces, including custom agents.

        Hooks are deliberately absent here: Kimi's project config is
        ``.kimi-code/local.toml`` and documents only a ``[workspace]`` table, so
        there is no supported project hook path to write.
        """
        result = super().install_workspace(ctx)
        if not ctx.instruction_only:
            kimi_root = (ctx.target_root / self.config["workspace_dir"]).resolve()
            result.files.extend(self._install_agents(kimi_root, ctx))
        return result

    def install_global(self, ctx: InstallContext) -> WriteResult:
        """Write the ``~/.kimi-code`` surfaces when Kimi Code CLI is detected, else skip.

        Detection: the Kimi Code CLI data root ``~/.kimi-code`` must exist. When it
        does not, Kimi Code CLI is not installed for this user and the global write
        is skipped (the workspace-scope ``.kimi-code/`` surfaces are unaffected).
        """
        result = WriteResult()
        kimi_root = (Path.home() / ".kimi-code").resolve()
        if not kimi_root.exists():
            ctx.manifest.log(
                self.key, "~/.kimi-code not found; skipping global Kimi surfaces"
            )
            result.mark_not_detected(
                "Kimi Code CLI (~/.kimi-code) not found; global AGENTS.md + skills skipped"
            )
            return result
        result.detected = True
        self._ensure_dir(kimi_root, ctx)
        action = self._write_instruction(kimi_root, ctx)
        if action is not None:
            result.files.append(action)
        if not ctx.instruction_only:
            result.files.extend(self._mirror_catalog(kimi_root, ctx))
            result.files.extend(self._install_agents(kimi_root, ctx))
            result.extend(self._install_hooks(kimi_root, ctx))
        return result

    # ----- native agent + hook surfaces (v3.15.8) --------------------------

    def _install_agents(self, kimi_root: Path, ctx: InstallContext) -> list[FileAction]:
        """Copy the catalog agents into Kimi's agents directory, unchanged."""
        return agents_to_kimi(
            ctx,
            self.key,
            ctx.repo_root / "catalog" / "agents",
            kimi_root / AGENTS_SUBDIR,
        )

    def _install_hooks(self, kimi_root: Path, ctx: InstallContext) -> WriteResult:
        """Copy the hook scripts Kimi can run and splice them into config.toml.

        Only groups whose event AND matcher have a Kimi equivalent are
        registered; the rest are logged as skipped rather than mapped onto a tool
        name Kimi does not have.
        """
        result = WriteResult()
        src_hooks = ctx.repo_root / "catalog" / "hooks"
        settings_file = src_hooks / "settings.json"
        if not settings_file.exists():
            ctx.manifest.log(self.key, f"missing-file: {settings_file}")
            result.files.append(FileAction(path=str(settings_file), action="not-found"))
            return result

        windows = is_windows_host()
        hooks_dst = kimi_root / HOOKS_SUBDIR
        entries, scripts, skipped = build_kimi_hooks(
            json.loads(settings_file.read_text(encoding="utf-8")),
            src_hooks,
            hooks_dst.as_posix(),
            windows,
        )
        for reason in skipped:
            ctx.manifest.log(self.key, f"skip-hook {reason}")

        self._ensure_dir(hooks_dst, ctx)
        for script in sorted(scripts):
            result.files.append(
                self._copy_file(src_hooks / script, hooks_dst / script, ctx, self.key)
            )
        result.files.append(
            merge_config_hooks(
                ctx, self.key, kimi_root / CONFIG_FILE, render_hooks_block(entries)
            )
        )
        result.notes.append(
            "Kimi hooks are fail-open by design: a hook that errors or times out "
            "allows the action, so treat them as alerts rather than a sole barrier."
        )
        return result

    # ----- teardown --------------------------------------------------------

    def teardown(self, ctx: InstallContext) -> WriteResult:
        """Remove Nexus-Hub content, leaving the user's Kimi config intact.

        ``config.toml`` holds the user's providers, models, and permission rules,
        so the managed hook block is spliced out and the path untracked before the
        manifest sweep, which would otherwise delete the whole file.
        """
        result = WriteResult()
        roots = self._kimi_roots(ctx)
        tracked = set(ctx.manifest.files_for(self.key))
        for kimi_root in roots:
            config_path = kimi_root / CONFIG_FILE
            if str(config_path) in tracked:
                result.files.append(prune_config_hooks(config_path, ctx.dry_run))
                ctx.manifest.untrack(self.key, str(config_path))
        result.extend(super().teardown(ctx))
        # Agents and hook scripts are tracked per file, so removing them leaves
        # the parent directory behind as a dead surface.
        for kimi_root in roots:
            for subdir in (AGENTS_SUBDIR, HOOKS_SUBDIR):
                remove_dir_if_empty(kimi_root / subdir, ctx, result)
        return result

    def _kimi_roots(self, ctx: InstallContext) -> list[Path]:
        if ctx.scope == "global":
            return [(Path.home() / ".kimi-code").resolve()]
        return [(ctx.target_root / self.config["workspace_dir"]).resolve()]
