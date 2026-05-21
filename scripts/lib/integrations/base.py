"""Base classes for Nexus-Hub integrations.

The class hierarchy is:

    IntegrationBase
      |-- MarkdownIntegration       (renders a base-<platform>.md to an instruction file)
      |-- TomlIntegration           (writes TOML command files; used by Gemini CLI)
      |-- YamlIntegration           (writes YAML frontmatter content; used by Cursor .mdc rules)
      |-- SkillsIntegration         (copies catalog/skills/ to a per-platform skills folder)

A concrete platform subclass typically inherits from MarkdownIntegration AND
SkillsIntegration (multiple inheritance) and declares its config in a class-level
dict.

The base classes are intentionally pure-Python and stdlib-only. They never call
out to shell tools; all file operations use pathlib and shutil.
"""

from __future__ import annotations

import json
import os
import re
import shutil
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from .manifest import InstallManifest


def _safe_resolve(root: Path, candidate: str) -> Path:
    """Resolve `candidate` against `root`, rejecting any path that escapes root.

    Defense against the path-traversal vector covered by
    tests/installer/test_registrar_path_traversal.py.
    """
    if "\x00" in candidate:
        raise ValueError(f"Null byte in path: {candidate!r}")
    if candidate.startswith(("/", "\\")) or (len(candidate) > 1 and candidate[1] == ":"):
        raise ValueError(f"Absolute path not allowed: {candidate!r}")
    if candidate.startswith("\\\\"):
        raise ValueError(f"UNC path not allowed: {candidate!r}")
    resolved = (root / candidate).resolve()
    root_resolved = root.resolve()
    try:
        resolved.relative_to(root_resolved)
    except ValueError as exc:
        raise ValueError(f"Path escapes root: {candidate!r} -> {resolved}") from exc
    return resolved


@dataclass
class InstallContext:
    """Per-invocation state passed to every integration."""

    repo_root: Path
    target_root: Path
    scope: str = "workspace"
    overwrite: bool = False
    dry_run: bool = False
    manifest: InstallManifest = field(default_factory=InstallManifest)
    template_vars: Dict[str, str] = field(default_factory=dict)


class IntegrationBase:
    """Abstract integration. Subclasses MUST set `key` and `config` and SHOULD
    override `install_global` / `install_workspace` / `teardown` as needed.
    """

    key: str = ""
    display_name: str = ""
    config: Dict[str, Any] = {}

    def __init__(self) -> None:
        if not self.key:
            raise NotImplementedError(f"{type(self).__name__} must set .key")
        if not self.display_name:
            self.display_name = self.key.capitalize()

    def install(self, ctx: InstallContext) -> None:
        """Dispatch to install_global or install_workspace based on ctx.scope."""
        if ctx.scope == "global":
            self.install_global(ctx)
        elif ctx.scope == "workspace":
            self.install_workspace(ctx)
        else:
            raise ValueError(f"Unknown scope: {ctx.scope!r}")

    def install_global(self, ctx: InstallContext) -> None:
        """Cooperative-super root. Subclasses extend via super().install_global(ctx)."""
        return

    def install_workspace(self, ctx: InstallContext) -> None:
        """Cooperative-super root. Subclasses extend via super().install_workspace(ctx)."""
        return

    def teardown(self, ctx: InstallContext) -> None:
        """Remove every file/directory previously logged in the manifest for
        this integration. Safe to call multiple times.
        """
        for path_str in list(ctx.manifest.files_for(self.key)):
            path = Path(path_str)
            if path.is_file():
                if not ctx.dry_run:
                    path.unlink(missing_ok=True)
            elif path.is_dir():
                if not ctx.dry_run:
                    shutil.rmtree(path, ignore_errors=True)
            ctx.manifest.untrack(self.key, path_str)

    def describe(self) -> Dict[str, Any]:
        """Return a JSON-serializable description for `runner.py list`."""
        return {
            "key": self.key,
            "display_name": self.display_name,
            "class": type(self).__name__,
            "config": self.config,
        }

    @staticmethod
    def _ensure_dir(path: Path, ctx: InstallContext) -> Path:
        if not ctx.dry_run:
            path.mkdir(parents=True, exist_ok=True)
        return path

    @staticmethod
    def _copy_file(src: Path, dst: Path, ctx: InstallContext, integration_key: str) -> None:
        if not src.exists():
            ctx.manifest.log(integration_key, f"skip-missing: {src}")
            return
        if dst.exists() and not ctx.overwrite:
            ctx.manifest.log(integration_key, f"skip-existing: {dst}")
            return
        if not ctx.dry_run:
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
        ctx.manifest.track(integration_key, str(dst))

    @staticmethod
    def _copy_tree(src: Path, dst: Path, ctx: InstallContext, integration_key: str) -> None:
        if not src.exists():
            ctx.manifest.log(integration_key, f"skip-missing-tree: {src}")
            return
        if not ctx.dry_run:
            if dst.exists() and ctx.overwrite:
                shutil.rmtree(dst, ignore_errors=True)
            shutil.copytree(src, dst, dirs_exist_ok=True)
        ctx.manifest.track(integration_key, str(dst))


class MarkdownIntegration(IntegrationBase):
    """Integration that renders a Markdown instruction file by substituting
    `{{TOKEN}}` placeholders from ctx.template_vars.

    Subclass requirements:
      - config["global_dir"]        : path relative to user home for global scope
      - config["workspace_dir"]     : path relative to target root for workspace scope
      - config["instruction_file"]  : filename written under the dir (e.g., "CLAUDE.md")
      - config["instruction_template"] : path under repo_root (e.g., "templates/ai-instructions/base-claude.md")
    """

    _TOKEN_RE = re.compile(r"\{\{([A-Z0-9_]+)\}\}")

    def _render(self, template_path: Path, ctx: InstallContext) -> str:
        text = template_path.read_text(encoding="utf-8")

        def repl(match: re.Match[str]) -> str:
            key = match.group(1)
            return str(ctx.template_vars.get(key, match.group(0)))

        return self._TOKEN_RE.sub(repl, text)

    def _write_instruction(self, dst_dir: Path, ctx: InstallContext) -> None:
        template_rel = self.config.get("instruction_template")
        instruction_file = self.config.get("instruction_file")
        if not template_rel or not instruction_file:
            ctx.manifest.log(self.key, "no instruction_template/instruction_file configured")
            return
        template_path = ctx.repo_root / template_rel
        if not template_path.exists():
            ctx.manifest.log(self.key, f"missing-template: {template_path}")
            return
        rendered = self._render(template_path, ctx)
        dst = dst_dir / instruction_file
        if dst.exists() and not ctx.overwrite:
            ctx.manifest.log(self.key, f"skip-existing: {dst}")
            return
        if not ctx.dry_run:
            dst.parent.mkdir(parents=True, exist_ok=True)
            dst.write_text(rendered, encoding="utf-8")
        ctx.manifest.track(self.key, str(dst))

    def install_global(self, ctx: InstallContext) -> None:
        rel = self.config.get("global_dir")
        if rel is not None:
            rel = rel.lstrip("~/")
            target = (Path.home() / rel).resolve()
            self._ensure_dir(target, ctx)
            self._write_instruction(target, ctx)
        super().install_global(ctx)

    def install_workspace(self, ctx: InstallContext) -> None:
        rel = self.config.get("workspace_dir")
        if rel is not None:
            target = (ctx.target_root / rel).resolve()
            self._ensure_dir(target, ctx)
            self._write_instruction(target, ctx)
        super().install_workspace(ctx)


class TomlIntegration(IntegrationBase):
    """Integration that writes TOML command files (used by Gemini CLI's
    `~/.gemini/commands/<name>.toml` convention).

    The Markdown command body under catalog/commands/<name>.md is converted
    to a TOML file with `prompt` and `description` fields.
    """

    def _md_to_toml(self, md_path: Path) -> str:
        body = md_path.read_text(encoding="utf-8")
        first_line = body.strip().splitlines()[0] if body.strip() else ""
        description = re.sub(r"^#+\s*", "", first_line).strip() or md_path.stem
        escaped = body.replace("\\", "\\\\").replace('"""', '\\"\\"\\"')
        return f'description = "{description}"\nprompt = """\n{escaped}\n"""\n'

    def _write_toml_commands(self, dst_dir: Path, ctx: InstallContext) -> None:
        src_dir = ctx.repo_root / "catalog" / "commands"
        if not src_dir.exists():
            ctx.manifest.log(self.key, f"missing: {src_dir}")
            return
        for md in sorted(src_dir.glob("*.md")):
            toml_dst = dst_dir / f"{md.stem}.toml"
            if toml_dst.exists() and not ctx.overwrite:
                ctx.manifest.log(self.key, f"skip-existing: {toml_dst}")
                continue
            if not ctx.dry_run:
                dst_dir.mkdir(parents=True, exist_ok=True)
                toml_dst.write_text(self._md_to_toml(md), encoding="utf-8")
            ctx.manifest.track(self.key, str(toml_dst))


class YamlIntegration(IntegrationBase):
    """Integration that writes .mdc files (Markdown + YAML frontmatter) used by
    Cursor's .cursor/rules/ directory convention.
    """

    def _md_to_mdc(self, md_path: Path, scope: str = "auto") -> str:
        body = md_path.read_text(encoding="utf-8")
        frontmatter = f"---\nname: {md_path.stem}\nscope: {scope}\n---\n\n"
        return frontmatter + body


class SkillsIntegration(IntegrationBase):
    """Integration that mirrors catalog/skills/, catalog/commands/,
    catalog/agents/, catalog/rules/, and catalog/hooks/ into per-platform
    subdirectories per the integration's config.
    """

    def _mirror_catalog(self, parent_dir: Path, ctx: InstallContext) -> None:
        mappings = {
            "skills_subdir": "catalog/skills",
            "commands_subdir": "catalog/commands",
            "agents_subdir": "catalog/agents",
            "rules_subdir": "catalog/rules",
            "hooks_subdir": "catalog/hooks",
        }
        for cfg_key, src_rel in mappings.items():
            subdir = self.config.get(cfg_key)
            if not subdir:
                continue
            src = ctx.repo_root / src_rel
            dst = parent_dir / subdir
            self._copy_tree(src, dst, ctx, self.key)

    def install_global(self, ctx: InstallContext) -> None:
        super().install_global(ctx)
        rel = self.config.get("global_dir")
        if rel is None:
            return
        rel = rel.lstrip("~/")
        parent = (Path.home() / rel).resolve()
        self._ensure_dir(parent, ctx)
        self._mirror_catalog(parent, ctx)

    def install_workspace(self, ctx: InstallContext) -> None:
        super().install_workspace(ctx)
        rel = self.config.get("workspace_dir")
        if rel is None:
            return
        parent = (ctx.target_root / rel).resolve()
        self._ensure_dir(parent, ctx)
        self._mirror_catalog(parent, ctx)
