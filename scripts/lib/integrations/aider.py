"""Aider integration.

Aider reads a project-root ``CONVENTIONS.md`` behavioral-guidance file when the
user references it from ``.aider.conf.yml`` (``read: CONVENTIONS.md``). This is a
behavioral-guardrails surface, not a slash-command surface: the catalog's skills
are made discoverable through the embedded ``{{SKILL_INDEX}}`` block rather than
a mirrored file tree.

Workspace scope writes ``<project>/CONVENTIONS.md``. Both scopes seed Aider's
documented YAML read list and attribution defaults without replacing user keys.
"""

from __future__ import annotations

from pathlib import Path

from .base import InstallContext, MarkdownIntegration
from .platform_defaults import _seed_yaml, declared_for
from .result import FileAction, WriteResult


class AiderIntegration(MarkdownIntegration):
    key = "aider"
    display_name = "Aider"
    instruction_mode = "shared"
    config = {
        "global_dir": None,
        # CONVENTIONS.md lands at the project root (where Aider reads it), so the
        # instruction dir is the workspace root itself.
        "instruction_workspace_dir": "",
        "instruction_file": "CONVENTIONS.md",
        "instruction_template": "templates/ai-instructions/base-aider.md",
        "hooks_supported": False,
    }

    def install_global(self, ctx: InstallContext) -> WriteResult:
        """Seed global attribution settings and the shared policy read path."""
        result = WriteResult()
        self._attribution_config(ctx.global_root, ctx, result)
        return result

    def install_workspace(self, ctx: InstallContext) -> WriteResult:
        result = super().install_workspace(ctx)
        self._attribution_config(ctx.target_root, ctx, result)
        return result

    def _attribution_config(
        self, root: Path, ctx: InstallContext, result: WriteResult
    ) -> None:
        home = ctx.global_root if ctx.scope == "global" else Path.home()
        guide = (home / ".nexus-hub/style-guides/git-attribution.md").as_posix()
        reads = [guide]
        if ctx.scope == "workspace":
            reads.append((ctx.target_root / "CONVENTIONS.md").resolve().as_posix())
        settings = dict(declared_for(self.key).get("settings", {}))
        if not settings:
            result.note(
                "NEEDS SETUP: Aider attribution defaults unavailable; reinstall from a complete Nexus-Hub source."
            )
            return
        settings["read"] = reads
        path = root / ".aider.conf.yml"
        action, _ = _seed_yaml(path, settings, ctx.dry_run)
        result.files.append(FileAction(path=str(path), action=action))
        # Shared user configuration is retained on uninstall, not owned wholesale.
        if not ctx.dry_run:
            try:
                import yaml
            except ImportError:
                result.note("NEEDS SETUP: PyYAML is required to verify Aider configuration.")
                return
            try:
                current = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
                configured_reads = current.get("read", [])
                if isinstance(configured_reads, str):
                    configured_reads = [configured_reads]
                if any(
                    current.get(k) != v for k, v in settings.items() if k != "read"
                ) or not set(reads).issubset(configured_reads):
                    result.note(
                        "NEEDS SETUP: Existing Aider settings override attribution defaults or omit the policy read path; reconcile .aider.conf.yml with the installed git-attribution guide."
                    )
            except (yaml.YAMLError, OSError, ValueError, AttributeError, TypeError):
                result.note(
                    "NEEDS SETUP: Aider configuration could not be verified; check .aider.conf.yml."
                )
