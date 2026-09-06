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
from typing import Any, Dict, List, Optional

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
    # v2.3.0 / Phase 7 / T022 -- the selected language list (e.g. ["Python",
    # "TypeScript"]). MarkdownIntegration appends the matching coding-snippet
    # fragment for each language, mirroring the legacy bash `render_template`
    # snippet-append step. Empty by default (global scope passes no languages).
    languages: List[str] = field(default_factory=list)
    # v2.3.0 / Phase 7 / T022 -- when True, MarkdownIntegration renders only the
    # instruction file and SkillsIntegration skips the catalog tree mirror. The
    # installer uses this when it has already copied catalog/ via its own
    # `safe_folder_copy` block and only needs the registry to render the
    # marker-merged instruction file (the DF-001 legacy-block replacement path).
    instruction_only: bool = False
    # v3.17.4 Phase 3 -- diagnostic detail is opt-in so an absent organization
    # connection remains silent during installer --quiet runs.
    verbose: bool = False
    # v3.16.1 Phase 5.4 -- the resolved install selection, a
    # `scripts.lib.installer.selection.SelectionPlan`, or None.
    #
    # None means NO FILTERING, i.e. the full catalog. That default is what makes
    # this additive: every pre-v3.16.1 caller constructs an InstallContext
    # without this field and keeps its exact current behavior with no edit,
    # matching how `languages` and `instruction_only` were introduced.
    #
    # Typed as Any rather than SelectionPlan on purpose. `base` is the most
    # widely imported module in the package, and importing the installer package
    # here would give every integration a hard dependency on the resolver -
    # including on hosts where the legacy installer path deliberately never
    # touches it. Phase 6 consumes this field where the copying happens.
    selection: Optional[Any] = None

    # ------------------------------------------------------------------
    # v3.16.1 Phase 6.3 -- selection predicates
    #
    # Every caller asks the same question ("may I copy this?") and gets True
    # unconditionally when no selection is present. That is what keeps a full
    # install on its EXACT pre-v3.16.1 code path: `selection is None` short-
    # circuits before any set is built, so the byte-equivalence requirement in
    # the contract is structural rather than something the copy sites have to
    # reproduce carefully.
    # ------------------------------------------------------------------

    def _selected(self, surface: str) -> Optional[frozenset]:
        """Resolved names for one surface, or None when nothing is filtered."""
        if self.selection is None:
            return None
        cache = getattr(self, "_selection_cache", None)
        if cache is None:
            plan = self.selection
            # Accept either a SelectionPlan or the plain dict a manifest holds,
            # so a repair driven from a recorded manifest needs no re-resolution.
            payload = plan.to_dict() if hasattr(plan, "to_dict") else dict(plan)
            resolved = payload.get("resolved", {}) or {}
            cache = {k: frozenset(v or ()) for k, v in resolved.items()}
            self._selection_cache = cache
        return cache.get(surface, frozenset())

    def selects_skill(self, name: str) -> bool:
        chosen = self._selected("skills")
        return True if chosen is None else name in chosen

    def selects_command(self, name: str) -> bool:
        chosen = self._selected("commands")
        return True if chosen is None else name in chosen

    def selects_agent(self, name: str) -> bool:
        chosen = self._selected("agents")
        return True if chosen is None else name in chosen

    @property
    def is_filtered(self) -> bool:
        """True when a selection is active. Copy sites branch on this to keep
        the unfiltered path byte-identical to pre-v3.16.1 behavior."""
        return self.selection is not None


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
        """Dispatch to install_global or install_workspace based on ctx.scope.

        Runs the per-integration legacy-state cleanups from
        ``scripts/lib/integrations/legacy.py`` first so any old artifacts are
        removed before the new content is written. Cleanups that return
        ``None`` (nothing to clean) are silently skipped.
        """
        # Import locally to break the legacy <-> base import cycle.
        from .legacy import run_cleanups

        cleanup_actions = run_cleanups(self.key, ctx)
        if ctx.scope == "global":
            result = self.install_global(ctx)
        elif ctx.scope == "workspace":
            result = self.install_workspace(ctx)
        else:
            raise ValueError(f"Unknown scope: {ctx.scope!r}")
        if cleanup_actions:
            # Cleanups happened before the install, so prepend them so the
            # rendered output reads top-to-bottom in execution order.
            result.files = list(cleanup_actions) + list(result.files)
        if result.detected is not False:
            # v3.16.0 Phase 3: seed the platform's declared install-time
            # behavioral defaults. Deliberately hooked here rather than in
            # install_global, because subclasses override that and a subclass
            # that forgot to call super() would silently skip its defaults.
            # The dispatcher runs for every integration, so this cannot be
            # missed. Import locally to keep the module import graph flat.
            #
            # Gated on `result.detected is not False`, NOT on truthiness:
            # `detected` is Optional[bool] where None means "this platform is
            # not detection-gated at all" (codex, cursor, claude). Only an
            # explicit False means "the tool was not found". Seeding an
            # undetected platform would create a config file for software the
            # user does not have installed, which is worse than shipping no
            # default at all.
            from .org_knowledge import seed_org_knowledge
            from .platform_defaults import seed_platform_defaults

            result.files.extend(seed_platform_defaults(self.key, ctx))
            # Organization knowledge belongs at this same dispatcher seam, not
            # in install_global/install_workspace overrides. Unlike platform
            # defaults, its helper intentionally handles both scopes so
            # workspace-only instruction surfaces such as Cursor and Aider are
            # materialized without inventing global files.
            result.files.extend(seed_org_knowledge(self.key, ctx))
        return result

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
        from .org_knowledge import remove_org_knowledge

        result = WriteResult(files=remove_org_knowledge(self.key, ctx))
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

    def dry_run(self, ctx: InstallContext) -> WriteResult:
        """Return a ``WriteResult`` for what ``install(ctx)`` would do, no writes.

        Default implementation flips ``ctx.dry_run=True`` and re-uses the
        existing install machinery. Helpers in this module (``_copy_file``,
        ``_copy_tree``, ``_write_instruction``, ``merge_marker_section``) all
        honor ``ctx.dry_run``, so the resulting ``WriteResult.files`` array is
        guaranteed to reflect the on-disk delta without touching disk.

        Subclasses with bespoke ``install_workspace`` / ``install_global``
        bodies inherit dry-run support for free as long as they gate every
        ``write_bytes`` / ``write_text`` / ``shutil.copytree`` on
        ``ctx.dry_run``.
        """
        from dataclasses import replace

        forced = replace(ctx, dry_run=True)
        return self.install(forced)

    def print_config(self, ctx: InstallContext) -> str:
        """Return a Markdown readout of what install would write, no writes.

        The output has three sections:

        1. Header with display name, scope, and target root.
        2. A FileActions table summarizing every file the install would touch
           (action + path, sourced from ``dry_run``).
        3. For ``MarkdownIntegration`` subclasses, the rendered body of the
           instruction template so the user can paste the block manually.

        Tree contents (skills/, commands/, etc.) are summarized by directory
        path rather than enumerating thousands of files; the FileActions table
        already names the destination.
        """
        result = self.dry_run(ctx)
        lines: List[str] = []
        lines.append(f"# {self.display_name} ({self.key})")
        lines.append("")
        lines.append(f"- Scope: `{ctx.scope}`")
        lines.append(f"- Target root: `{ctx.target_root}`")
        lines.append("")
        lines.append("## File actions")
        lines.append("")
        if not result.files:
            lines.append("_(no files would be written)_")
        else:
            lines.append("| Action | Path |")
            lines.append("|--------|------|")
            for fa in result.files:
                lines.append(f"| `{fa.action}` | `{fa.path}` |")
        lines.append("")
        template_rel = self.config.get("instruction_template")
        instruction_file = self.config.get("instruction_file")
        if (
            isinstance(self, MarkdownIntegration)
            and template_rel
            and instruction_file
        ):
            tpl_path = ctx.repo_root / template_rel
            if tpl_path.exists():
                rendered = self._render(tpl_path, ctx)
                lines.append(f"## Rendered instruction body ({instruction_file})")
                lines.append("")
                lines.append("```markdown")
                lines.append(rendered.rstrip())
                lines.append("```")
                lines.append("")
        for note in result.notes:
            lines.append(f"> {note}")
        return "\n".join(lines) + "\n"

    def wire_project_surfaces(self, ctx: InstallContext) -> Optional[WriteResult]:
        """Bootstrap project-local surfaces from a *global* install.

        Some platforms (Cursor with ``.cursor/rules/*.mdc``, Claude Code with a
        per-project ``.claude/settings.json``) gain functionality from a
        project-scoped file even when the catalog itself lives at
        ``~/.<platform>/``. ``nexus-hub init`` walks every registered
        integration and calls this hook so users can opt into the project
        surfaces without re-running the full workspace install.

        Returns ``None`` (the default) when the integration has no project-
        local surface. Override on the relevant subclass to return a
        ``WriteResult`` describing the files written.
        """
        return None

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

    @staticmethod
    def _write_generated(
        dst: Path, content: str, ctx: InstallContext, integration_key: str
    ) -> FileAction:
        """Write a deterministic, Nexus-Hub-owned companion file.

        Used by integrations that emit a small generated config/identity file
        alongside a marker-merged instruction file (e.g., Kimi's ``agent.yaml``,
        OpenClaw's ``SOUL.md`` / ``IDENTITY.md``). Mirrors the dedicated-mode
        contract of ``_write_instruction`` so these files share the same
        idempotency, partial-recovery, and dry-run guarantees the contract suite
        asserts:

          - dst missing                              -> write -> "created"
          - dst exists, bytes match                  -> no write -> "unchanged"
          - dst exists, bytes differ, overwrite=True -> write -> "updated"
          - dst exists, bytes differ, no overwrite   -> no write -> "kept"

        The path is tracked in the manifest so the default teardown removes it.
        """
        content_bytes = content.encode("utf-8")
        if dst.exists():
            if dst.read_bytes() == content_bytes:
                ctx.manifest.track(integration_key, str(dst))
                return FileAction(path=str(dst), action="unchanged")
            if not ctx.overwrite:
                ctx.manifest.log(integration_key, f"skip-existing: {dst}")
                return FileAction(path=str(dst), action="kept")
            if not ctx.dry_run:
                dst.parent.mkdir(parents=True, exist_ok=True)
                dst.write_bytes(content_bytes)
            ctx.manifest.track(integration_key, str(dst))
            return FileAction(path=str(dst), action="updated")
        if not ctx.dry_run:
            dst.parent.mkdir(parents=True, exist_ok=True)
            dst.write_bytes(content_bytes)
        ctx.manifest.track(integration_key, str(dst))
        return FileAction(path=str(dst), action="created")


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

    # v2.3.0 / Phase 7 / T022 -- built-in defaults for the instruction-template
    # placeholders. These mirror the constant sed substitutions the legacy bash
    # `render_template` performs (installer.sh ~line 1000) so a render with no
    # caller-supplied vars still produces a complete instruction file (used by
    # `print-config`). Caller-supplied `ctx.template_vars` override these, and
    # the installer threads its detected values (PRIMARY_LANGUAGE, BUILD_CMD,
    # ...) the same way the bash path fills them. `{{SKILL_INDEX}}` is loaded
    # from data/SKILL_INDEX.md on demand (see `_render`). Tokens absent from
    # both this map and `ctx.template_vars` (e.g. `{{AGENT_REGISTRY}}`) are left
    # literal, exactly as the bash `sed` list leaves them.
    _DEFAULT_TEMPLATE_VARS: Dict[str, str] = {
        "PROJECT_DESCRIPTION": "(Add a 2-3 sentence project description here, or run /setup project)",
        "PRIMARY_LANGUAGE": "",
        "LANGUAGE_VERSION": "",
        "PACKAGE_MANAGER": "",
        "BUILD_TOOL": "",
        "TEST_FRAMEWORK": "",
        "LINT_TOOL": "",
        "PROJECT_STRUCTURE_BRIEF": "(Run /setup project to generate project layout)",
        "BUILD_CMD": "# specify build command",
        "TEST_CMD": "# specify test command",
        "LINT_CMD": "# specify lint command",
        "NON_OBVIOUS_TOOLING": "- (configure per project with /setup project)",
        "LANGUAGE_CONVENTIONS": "(See coding-snippets or run /setup project)",
        "OS_CONTEXT": "",
    }

    def _load_skill_index(self, ctx: InstallContext) -> Optional[str]:
        """Return the contents of data/SKILL_INDEX.md, or None if absent.

        Mirrors the bash `render_template` multi-line `{{SKILL_INDEX}}` replace:
        the index is substituted only when the file exists; otherwise the token
        is left literal so the absence is visible rather than silently blanked.
        """
        index_path = ctx.repo_root / "data" / "SKILL_INDEX.md"
        if index_path.exists():
            return index_path.read_text(encoding="utf-8")
        return None

    def _effective_template_vars(self, ctx: InstallContext) -> Dict[str, str]:
        """Merge built-in defaults, the auto-loaded skill index, and the
        caller-supplied vars (the caller wins). The result is the full token map
        used for one render.
        """
        merged: Dict[str, str] = dict(self._DEFAULT_TEMPLATE_VARS)
        skill_index = self._load_skill_index(ctx)
        if skill_index is not None:
            merged["SKILL_INDEX"] = skill_index
        merged.update(ctx.template_vars)
        return merged

    def _render(self, template_path: Path, ctx: InstallContext) -> str:
        text = template_path.read_text(encoding="utf-8")
        merged = self._effective_template_vars(ctx)

        def repl(match: re.Match[str]) -> str:
            key = match.group(1)
            if key in merged:
                return str(merged[key])
            return match.group(0)

        rendered = self._TOKEN_RE.sub(repl, text)
        return self._append_language_snippets(rendered, ctx)

    def _append_language_snippets(self, rendered: str, ctx: InstallContext) -> str:
        """Append each selected language's coding-snippet fragment.

        Reproduces the legacy bash `render_template` snippet-append loop: for
        every language in `ctx.languages`, append
        `templates/ai-instructions/coding-snippets/<lang>.md` (lowercased, with
        `c++`->`cpp` and `c#`->`csharp`) separated by a blank line. Because the
        shared-mode marker block strips surrounding whitespace, each fragment is
        normalized to a single trailing newline so the output is deterministic
        across the bash and PowerShell installers (which historically appended
        slightly different whitespace).
        """
        for lang in ctx.languages:
            lang_key = lang.strip().lower()
            if not lang_key:
                continue
            if lang_key == "c++":
                lang_key = "cpp"
            elif lang_key == "c#":
                lang_key = "csharp"
            snippet = (
                ctx.repo_root
                / "templates"
                / "ai-instructions"
                / "coding-snippets"
                / f"{lang_key}.md"
            )
            if snippet.exists():
                fragment = snippet.read_text(encoding="utf-8").strip()
                rendered = rendered.rstrip("\n") + "\n\n" + fragment + "\n"
        return rendered

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
        # v2.3.0 / Phase 7 / DF-001 -- the instruction file may live in a
        # different directory than the catalog mirror. `instruction_workspace_dir`
        # defaults to `workspace_dir`, but claude/codex set it to "" so the
        # instruction file (CLAUDE.md / AGENTS.md) lands at the project root --
        # the location those tools actually read -- matching the legacy bash
        # installer, while skills/ still mirror under `.claude/` / `.codex/`.
        rel = self.config.get("instruction_workspace_dir", self.config.get("workspace_dir"))
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
        actions: list[FileAction] = []

        # Skills. When the platform declares `flatten_skills_layout: True`, it
        # discovers skills one level deep (skills/<name>/SKILL.md -- the SKILL.md
        # open standard shared by Claude Code, Codex, Gemini CLI, OpenCode, and
        # Antigravity), so the catalog's <category>/ layer must be dropped and each
        # command additionally surfaces as a skill. Otherwise the catalog skills
        # tree is mirrored verbatim (nested) for platforms that read it that way.
        skills_subdir = self.config.get("skills_subdir")
        if skills_subdir:
            skills_dst = parent_dir / skills_subdir
            if self.config.get("flatten_skills_layout"):
                # Local import breaks the base <-> _catalog_adapters import cycle.
                from ._catalog_adapters import (
                    catalog_skill_names,
                    commands_to_skills,
                    flatten_skills,
                )

                src_skills = ctx.repo_root / "catalog" / "skills"
                src_commands = ctx.repo_root / "catalog" / "commands"
                actions.extend(flatten_skills(ctx, self.key, src_skills, skills_dst))
                actions.extend(
                    commands_to_skills(
                        ctx, self.key, src_commands, skills_dst,
                        catalog_skill_names(src_skills),
                    )
                )
            elif ctx.is_filtered:
                # v3.16.1 Phase 6.3 -- nested layout under a selection. Only
                # reached when a selection is active; the unfiltered branch
                # below keeps its single whole-tree copy untouched.
                from ._catalog_adapters import nested_skills_selected

                actions.extend(
                    nested_skills_selected(
                        ctx, self.key, ctx.repo_root / "catalog" / "skills", skills_dst
                    )
                )
            else:
                actions.append(
                    self._copy_tree(ctx.repo_root / "catalog" / "skills", skills_dst, ctx, self.key)
                )

        # Commands, agents, rules, hooks: verbatim tree copy (already flat / tree-shaped).
        for cfg_key, src_rel in (
            ("commands_subdir", "catalog/commands"),
            ("agents_subdir", "catalog/agents"),
            ("rules_subdir", "catalog/rules"),
            ("hooks_subdir", "catalog/hooks"),
        ):
            subdir = self.config.get(cfg_key)
            if not subdir:
                continue
            # Hook installation is gated on the declared capability so a
            # platform's hook support lives in exactly one place
            # (`hooks_supported`). Every integration that declares
            # `hooks_subdir` today also sets `hooks_supported: True`, so this is
            # byte-identical to the prior unconditional copy; the gate prevents a
            # future `hooks_subdir` declaration from silently shipping hooks to a
            # platform that cannot run them.
            if cfg_key == "hooks_subdir" and not self.config.get("hooks_supported"):
                continue
            # v3.16.1 Phase 6.3 -- commands and agents are selectable surfaces;
            # rules and hooks are policy infrastructure and are NEVER filtered.
            # A user narrowing their capability set is not asking for weaker
            # guardrails, so a focused install must not be less safe than the
            # default one.
            surface = {"commands_subdir": "command", "agents_subdir": "agent"}.get(cfg_key)
            if surface and ctx.is_filtered:
                from ._catalog_adapters import flat_md_selected

                actions.extend(
                    flat_md_selected(
                        ctx, self.key, ctx.repo_root / src_rel, parent_dir / subdir, surface
                    )
                )
                continue
            actions.append(
                self._copy_tree(ctx.repo_root / src_rel, parent_dir / subdir, ctx, self.key)
            )
        return actions

    def install_global(self, ctx: InstallContext) -> WriteResult:
        result = super().install_global(ctx)
        # v2.3.0 / Phase 7 / T022 -- skip the catalog mirror when the caller only
        # wants the instruction file rendered (the installer copies catalog/ via
        # its own block and uses --instruction-only for the registry call).
        if ctx.instruction_only:
            return result
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
        if ctx.instruction_only:
            return result
        rel = self.config.get("workspace_dir")
        if rel is None:
            return result
        parent = (ctx.target_root / rel).resolve()
        self._ensure_dir(parent, ctx)
        result.files.extend(self._mirror_catalog(parent, ctx))
        return result
