"""Gemini CLI integration.

Gemini CLI consumes:
  - ~/.gemini/GEMINI.md as the global instruction file (shared with Gemini IDE)
  - ~/.gemini/commands/<name>.toml as custom slash-command definitions
  - ~/.gemini/extensions/ for extensions
  - ~/.gemini/settings.json (and project .gemini/settings.json) for native hooks
    under a `hooks` key (v3.15.8)
  - Project .gemini/ for project-scoped overrides

This subclass mirrors catalog/commands/*.md to ~/.gemini/commands/*.toml via the
TomlIntegration helper, while still rendering GEMINI.md from the base template.

Hooks arrive through the shared ``SettingsHooksMixin``, because Qwen Code (a
Gemini CLI fork) reads the same nested shape from its own settings.json. The
per-platform differences -- Gemini CLI renamed every lifecycle event, so
``PreToolUse`` is ``BeforeTool`` and ``Stop`` is ``AfterAgent`` -- live in
``GEMINI_CLI_SPEC``.
"""

from __future__ import annotations

from pathlib import Path

from ._owned import remove_dir_if_empty
from ._settings_hooks import GEMINI_CLI_SPEC
from ._settings_hooks_mixin import HOOKS_SUBDIR, SettingsHooksMixin
from .base import (
    InstallContext,
    MarkdownIntegration,
    SkillsIntegration,
    TomlIntegration,
)
from .result import WriteResult


class GeminiCliIntegration(
    MarkdownIntegration, SkillsIntegration, TomlIntegration, SettingsHooksMixin
):
    key = "gemini-cli"
    display_name = "Gemini CLI (Google, ENTERPRISE-ONLY post-2026-06-18)"
    instruction_mode = "shared"
    hook_spec = GEMINI_CLI_SPEC
    config = {
        "global_dir": "~/.gemini",
        "workspace_dir": ".gemini",
        "instruction_file": "GEMINI.md",
        "instruction_template": "templates/ai-instructions/base-gemini-cli.md",
        # Gemini CLI discovers skills one level deep at ~/.gemini/skills/<name>/
        # (or the ~/.agents/skills alias); flatten + add command-skills (Phase 4).
        "skills_subdir": "skills",
        "flatten_skills_layout": True,
        "agents_subdir": "agents",
        "rules_subdir": "rules",
        # Hooks land in settings.json via the mixin rather than as a tree copy,
        # so hooks_subdir is not set on the base class.
        "hooks_supported": True,
    }

    def install_global(self, ctx: InstallContext) -> WriteResult:
        result = super().install_global(ctx)
        root = (Path.home() / ".gemini").resolve()
        result.files.extend(self._write_toml_commands(root / "commands", ctx))
        if not ctx.instruction_only:
            result.extend(self._install_settings_hooks(root, ctx, scope="global"))
        return result

    def install_workspace(self, ctx: InstallContext) -> WriteResult:
        result = super().install_workspace(ctx)
        root = (ctx.target_root / ".gemini").resolve()
        result.files.extend(self._write_toml_commands(root / "commands", ctx))
        if not ctx.instruction_only:
            result.extend(self._install_settings_hooks(root, ctx, scope="workspace"))
        return result

    def teardown(self, ctx: InstallContext) -> WriteResult:
        """Prune our hook entries from settings.json, then run the normal sweep."""
        roots = self._gemini_roots(ctx)
        result = self._teardown_settings_hooks(roots, ctx)
        result.extend(super().teardown(ctx))
        for root in roots:
            remove_dir_if_empty(root / HOOKS_SUBDIR, ctx, result)
        return result

    @staticmethod
    def _gemini_roots(ctx: InstallContext) -> list[Path]:
        if ctx.scope == "global":
            return [(Path.home() / ".gemini").resolve()]
        return [(ctx.target_root / ".gemini").resolve()]
