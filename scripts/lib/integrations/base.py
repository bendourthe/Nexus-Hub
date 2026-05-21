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

Lifecycle methods (`install_global`, `install_workspace`, `teardown`,
`uninstall_global`, `uninstall_workspace`) all return `WriteResult` since v2.2.0;
helpers (`_copy_file`, `_copy_tree`, `_write_instruction`) return `FileAction`
records so callers can thread them into the running result.

The base classes are intentionally pure-Python and stdlib-only. They never call
out to shell tools; all file operations use pathlib and shutil.
"""

from __future__ import annotations

import re
import shutil
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Optional

from .manifest import InstallManifest
from .result import FileAction, WriteResult


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

    def install(self, ctx: InstallContext) -> WriteResult:
        """Dispatch to install_global or install_workspace based on ctx.scope."""
        if ctx.scope == "global":
            return self.install_global(ctx)
        if ctx.scope == "workspace":
            return self.install_workspace(ctx)
        raise ValueError(f"Unknown scope: {ctx.scope!r}")

    def install_global(self, ctx: InstallContext) -> WriteResult:
        """Cooperative-super root. Subclasses extend via super().install_global(ctx)."""
        return WriteResult()

    def install_workspace(self, ctx: InstallContext) -> WriteResult:
        """Cooperative-super root. Subclasses extend via super().install_workspace(ctx)."""
        return WriteResult()

    def uninstall(self, ctx: InstallContext) -> WriteResult:
        """Dispatch to uninstall_global or uninstall_workspace based on ctx.scope."""
        if ctx.scope == "global":
            return self.uninstall_global(ctx)
        if ctx.scope == "workspace":
            return self.uninstall_workspace(ctx)
        raise ValueError(f"Unknown scope: {ctx.scope!r}")

    def uninstall_global(self, ctx: InstallContext) -> WriteResult:
        """Default uninstall: replay the manifest. Nexus-Hub's manifest is
        scope-agnostic, so both `uninstall_global` and `uninstall_workspace`
        delegate to `teardown`. Subclasses may override either side if a future
        scope-specific cleanup is needed.
        """
        return self.teardown(ctx)

    def uninstall_workspace(self, ctx: InstallContext) -> WriteResult:
        return self.teardown(ctx)

    def teardown(self, ctx: InstallContext) -> WriteResult:
        """Remove every file/directory previously logged in the manifest for
        this integration. Safe to call multiple times.
        """
        result = WriteResult()
        for path_str in list(ctx.manifest.files_for(self.key)):
            path = Path(path_str)
            if path.is_file():
                if not ctx.dry_run:
                    path.unlink(missing_ok=True)
                result.add(path_str, "removed")
            elif path.is_dir():
                if not ctx.dry_run:
                    shutil.rmtree(path, ignore_errors=True)
                result.add(path_str, "removed")
            else:
                result.add(path_str, "not-found")
            ctx.manifest.untrack(self.key, path_str)
        return result

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
    def _copy_file(
        src: Path, dst: Path, ctx: InstallContext, integration_key: str
    ) -> FileAction:
        """Copy `src` to `dst`. Returns a `FileAction` describing the outcome.

        Action mapping:
          - src missing                                 -> "not-found"
          - dst exists, not overwrite, src not asked    -> "kept"
          - dst exists, bytes equal to src              -> "unchanged"
          - dst missing                                 -> "created"
          - dst exists, bytes differ, overwrite=True    -> "updated"
        """
        if not src.exists():
            ctx.manifest.log(integration_key, f"skip-missing: {src}")
            return FileAction(path=str(src), action="not-found")
        if dst.exists() and not ctx.overwrite:
            ctx.manifest.log(integration_key, f"skip-existing: {dst}")
            return FileAction(path=str(dst), action="kept")
        src_bytes = src.read_bytes()
        if dst.exists():
            if dst.read_bytes() == src_bytes:
                ctx.manifest.track(integration_key, str(dst))
                return FileAction(path=str(dst), action="unchanged")
            if not ctx.dry_run:
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dst)
            ctx.manifest.track(integration_key, str(dst))
            return FileAction(path=str(dst), action="updated")
        if not ctx.dry_run:
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
        ctx.manifest.track(integration_key, str(dst))
        return FileAction(path=str(dst), action="created")

    @staticmethod
    def _copy_tree(
        src: Path, dst: Path, ctx: InstallContext, integration_key: str
    ) -> FileAction:
        """Copy a tree from `src` to `dst`. Returns one summary `FileAction`
        whose `path` is the destination directory.

        Action: "not-found" if src missing; "unchanged" if every existing file
        already matches; "created" if dst did not exist before; "updated"
        otherwise.
        """
        if not src.exists():
            ctx.manifest.log(integration_key, f"skip-missing-tree: {src}")
            return FileAction(path=str(src), action="not-found")
        existed_before = dst.exists()
        all_unchanged = existed_before and _tree_matches(src, dst)
        if not ctx.dry_run:
            if existed_before and ctx.overwrite:
                shutil.rmtree(dst, ignore_errors=True)
                existed_before = False
                all_unchanged = False
            shutil.copytree(src, dst, dirs_exist_ok=True)
        ctx.manifest.track(integration_key, str(dst))
        if all_unchanged:
            return FileAction(path=str(dst), action="unchanged")
        if not existed_before:
            return FileAction(path=str(dst), action="created")
        return FileAction(path=str(dst), action="updated")


def _tree_matches(src: Path, dst: Path) -> bool:
    """Return True if every file under `src` exists at the matching `dst` path
    with byte-identical content. False if any file differs, is missing at the
    destination, or if a read fails.
    """
    try:
        for src_file in src.rglob("*"):
            if not src_file.is_file():
                continue
            rel = src_file.relative_to(src)
            dst_file = dst / rel
            if not dst_file.is_file():
                return False
            if src_file.read_bytes() != dst_file.read_bytes():
                return False
        return True
    except OSError:
        return False


class MarkdownIntegration(IntegrationBase):
    """Integration that renders a Markdown instruction file by substituting
    `{{TOKEN}}` placeholders from ctx.template_vars.

    Subclass requirements:
      - config["global_dir"]        : path relative to user home for global scope
      - config["workspace_dir"]     : path relative to target root for workspace scope
      - config["instruction_file"]  : filename written under the dir (e.g., "CLAUDE.md")
      - config["instruction_template"] : path under repo_root (e.g., "templates/ai-instructions/base-claude.md")

    Phase 1 (v2.2.0) added an `instruction_mode` class attribute. Defaults to
    `"shared"`, in which case T004 (sub-task 1.4) will route writes through
    `merge_marker_section` so user edits to CLAUDE.md / AGENTS.md survive a
    re-install. Set `"dedicated"` on subclasses where Nexus-Hub owns the whole
    file.
    """

    _TOKEN_RE = re.compile(r"\{\{([A-Z0-9_]+)\}\}")
    instruction_mode: str = "shared"

    def _render(self, template_path: Path, ctx: InstallContext) -> str:
        text = template_path.read_text(encoding="utf-8")

        def repl(match: re.Match[str]) -> str:
            key = match.group(1)
            return str(ctx.template_vars.get(key, match.group(0)))

        return self._TOKEN_RE.sub(repl, text)

    def _write_instruction(
        self, dst_dir: Path, ctx: InstallContext
    ) -> Optional[FileAction]:
        """Render the configured template and write it to dst_dir.

        Shared-mode subclasses (the default) route writes through
        `merge_marker_section` so user content above and below the
        Nexus-Hub-managed block survives a re-install. Dedicated-mode
        subclasses rewrite the file in full.

        Returns one `FileAction` per call (or None when no template /
        instruction file is configured).
        """
        template_rel = self.config.get("instruction_template")
        instruction_file = self.config.get("instruction_file")
        if not template_rel or not instruction_file:
            ctx.manifest.log(self.key, "no instruction_template/instruction_file configured")
            return None
        template_path = ctx.repo_root / template_rel
        if not template_path.exists():
            ctx.manifest.log(self.key, f"missing-template: {template_path}")
            return FileAction(path=str(template_path), action="not-found")
        rendered = self._render(template_path, ctx)
        dst = dst_dir / instruction_file

        if self.instruction_mode == "shared":
            from scripts.lib.installer.instruction_merge import merge_marker_section

            if not ctx.dry_run:
                dst.parent.mkdir(parents=True, exist_ok=True)
            action = merge_marker_section(
                dst,
                rendered,
                legacy_header="## Nexus-Hub",
                dry_run=ctx.dry_run,
            )
            ctx.manifest.track_shared(self.key, str(dst))
            return action

        # Dedicated mode: Nexus-Hub owns the file end-to-end.
        rendered_bytes = rendered.encode("utf-8")
        if dst.exists() and not ctx.overwrite:
            existing = dst.read_bytes()
            if existing == rendered_bytes:
                ctx.manifest.track(self.key, str(dst))
                return FileAction(path=str(dst), action="unchanged")
            ctx.manifest.log(self.key, f"skip-existing: {dst}")
            return FileAction(path=str(dst), action="kept")
        existed = dst.exists()
        if existed:
            existing = dst.read_bytes()
            if existing == rendered_bytes:
                ctx.manifest.track(self.key, str(dst))
                return FileAction(path=str(dst), action="unchanged")
        if not ctx.dry_run:
            dst.parent.mkdir(parents=True, exist_ok=True)
            dst.write_bytes(rendered_bytes)
        ctx.manifest.track(self.key, str(dst))
        return FileAction(
            path=str(dst), action="updated" if existed else "created"
        )

    def install_global(self, ctx: InstallContext) -> WriteResult:
        result = super().install_global(ctx)
        rel = self.config.get("global_dir")
        if rel is not None:
            rel = rel.lstrip("~/")
            target = (Path.home() / rel).resolve()
            self._ensure_dir(target, ctx)
            action = self._write_instruction(target, ctx)
            if action is not None:
                result.files.append(action)
        return result

    def install_workspace(self, ctx: InstallContext) -> WriteResult:
        result = super().install_workspace(ctx)
        rel = self.config.get("workspace_dir")
        if rel is not None:
            target = (ctx.target_root / rel).resolve()
            self._ensure_dir(target, ctx)
            action = self._write_instruction(target, ctx)
            if action is not None:
                result.files.append(action)
        return result

    def teardown(self, ctx: InstallContext) -> WriteResult:
        """Remove the marker-delimited section from every shared instruction
        file this integration wrote, then run the default manifest-based
        teardown for tracked tree paths.
        """
        result = WriteResult()
        if self.instruction_mode == "shared":
            from scripts.lib.installer.instruction_merge import remove_marker_section

            for shared_path in list(ctx.manifest.shared_for(self.key)):
                action = remove_marker_section(Path(shared_path), dry_run=ctx.dry_run)
                result.files.append(action)
                ctx.manifest.untrack_shared(self.key, shared_path)
        result.extend(super().teardown(ctx))
        return result


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

    def _write_toml_commands(self, dst_dir: Path, ctx: InstallContext) -> list[FileAction]:
        """Render every catalog/commands/*.md into `<dst_dir>/<name>.toml`.

        Returns one `FileAction` per source command (so the runner can render
        per-file detail). When `catalog/commands/` is missing entirely, returns
        a single "not-found" action.
        """
        actions: list[FileAction] = []
        src_dir = ctx.repo_root / "catalog" / "commands"
        if not src_dir.exists():
            ctx.manifest.log(self.key, f"missing: {src_dir}")
            return [FileAction(path=str(src_dir), action="not-found")]
        for md in sorted(src_dir.glob("*.md")):
            toml_dst = dst_dir / f"{md.stem}.toml"
            rendered = self._md_to_toml(md)
            rendered_bytes = rendered.encode("utf-8")
            if toml_dst.exists() and not ctx.overwrite:
                if toml_dst.read_bytes() == rendered_bytes:
                    ctx.manifest.track(self.key, str(toml_dst))
                    actions.append(FileAction(path=str(toml_dst), action="unchanged"))
                else:
                    ctx.manifest.log(self.key, f"skip-existing: {toml_dst}")
                    actions.append(FileAction(path=str(toml_dst), action="kept"))
                continue
            existed = toml_dst.exists()
            if not ctx.dry_run:
                dst_dir.mkdir(parents=True, exist_ok=True)
                toml_dst.write_bytes(rendered_bytes)
            ctx.manifest.track(self.key, str(toml_dst))
            actions.append(
                FileAction(
                    path=str(toml_dst), action="updated" if existed else "created"
                )
            )
        return actions


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

    def _mirror_catalog(self, parent_dir: Path, ctx: InstallContext) -> list[FileAction]:
        mappings = {
            "skills_subdir": "catalog/skills",
            "commands_subdir": "catalog/commands",
            "agents_subdir": "catalog/agents",
            "rules_subdir": "catalog/rules",
            "hooks_subdir": "catalog/hooks",
        }
        actions: list[FileAction] = []
        for cfg_key, src_rel in mappings.items():
            subdir = self.config.get(cfg_key)
            if not subdir:
                continue
            src = ctx.repo_root / src_rel
            dst = parent_dir / subdir
            actions.append(self._copy_tree(src, dst, ctx, self.key))
        return actions

    def install_global(self, ctx: InstallContext) -> WriteResult:
        result = super().install_global(ctx)
        rel = self.config.get("global_dir")
        if rel is None:
            return result
        rel = rel.lstrip("~/")
        parent = (Path.home() / rel).resolve()
        self._ensure_dir(parent, ctx)
        result.files.extend(self._mirror_catalog(parent, ctx))
        return result

    def install_workspace(self, ctx: InstallContext) -> WriteResult:
        result = super().install_workspace(ctx)
        rel = self.config.get("workspace_dir")
        if rel is None:
            return result
        parent = (ctx.target_root / rel).resolve()
        self._ensure_dir(parent, ctx)
        result.files.extend(self._mirror_catalog(parent, ctx))
        return result
