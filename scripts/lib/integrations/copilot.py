"""GitHub Copilot integration.

Copilot reads repository instructions from ``.github/copilot-instructions.md``
and personal instructions from ``~/.copilot/copilot-instructions.md``. Native
custom agents live under ``.github/agents`` and ``~/.copilot/agents``; native
version-1 hook files live under ``.github/hooks/*.json`` and
``~/.copilot/hooks/*.json``.

Copilot DOES expose a user-global slash-command surface via VS Code *prompt
files*: ``<vscode-user>/prompts/<name>.prompt.md`` is offered as ``/<name>`` in
Copilot Chat from any repo (requires the ``chat.promptFiles`` setting, on by
default in current VS Code). A global install therefore mirrors the catalog's
commands into the user-profile prompts dir so they are available everywhere with
no per-project install (confirmed empirically against a repo with no local
install). The per-repo ``.github/copilot-instructions.md`` behavioral layer
still installs per-workspace.

GitHub CLI's `gh copilot` extension is also implicitly supported because it
reads the same .github/copilot-instructions.md and the user's gh-installed
extensions independently.

Copilot accepts PascalCase Claude-compatible hook events, snake_case payloads,
and Claude matcher semantics. Nexus-Hub therefore transforms the catalog hook
registration into a dedicated native ``nexus-hub.json`` file while reusing the
catalog scripts and PowerShell siblings. The dedicated file is ownership-aware;
an unrelated user file is never overwritten.
"""

from __future__ import annotations

import json
import os
import platform
from pathlib import Path
from typing import Optional

from scripts.lib.installer.instruction_merge import merge_marker_section

from ._catalog_adapters import _split_frontmatter
from ._command_surface import mirror_command_surface
from ._copilot_native import build_copilot_hooks
from ._owned import remove_dir_if_empty, write_owned_file
from .base import InstallContext, MarkdownIntegration
from .result import FileAction, WriteResult

# Copilot's documented user-profile custom-agent directory. Agent files use the
# `.agent.md` extension, and the name minus that suffix is the dedup key across
# levels, so a project `.claude/agents/planner.md` still wins over the global copy.
_COPILOT_HOME = ".copilot"
_COPILOT_AGENTS_SUBDIR = "agents"
_AGENT_SUFFIX = ".agent.md"

# Copilot caps an agent prompt at 30,000 characters. A longer body is skipped
# rather than shipped truncated or rejected at load time.
_MAX_AGENT_PROMPT_CHARS = 30_000

# v3.11.0 Phase 5 (S3): opt-in project-scoped skills surface, WIDENED to a
# selector in v3.15.0 Phase 5.
#
# GitHub Copilot now reads project Agent Skills natively and default-on
# (`.github/skills/` is canonical, verified 2026-07-20, v3.15.0 Phase 1.2 / DF-5).
# The Nexus-Hub opt-in is therefore NOT a Copilot technical requirement anymore --
# it is a COMMIT-VISIBILITY policy: `.github/skills/` lives in the user's repo and
# is committed, so Nexus-Hub never seeds it unless the user asks. The env var is
# now a SELECTOR, not just a toggle:
#   unset / "" / 0 / false / no / off  -> OFF (nothing seeded)
#   1 / true / yes / on                -> the default bundle (core-developer)
#   <bundle-id>                        -> that skill bundle (see data/bundles.json)
#   all                                -> the full catalog (heavy: every skill is a
#                                         committed .github/skills/<name>/ wrapper)
_COPILOT_SKILLS_ENV = "NEXUS_HUB_COPILOT_SKILLS"
_COPILOT_CURATED_BUNDLE = "core-developer"
_COPILOT_OFF_VALUES = {"", "0", "false", "no", "off"}
_COPILOT_BARE_TRUTHY = {"1", "true", "yes", "on"}


def _copilot_skills_enabled(val: Optional[str]) -> bool:
    """Copilot project-skill seeding is ON for any non-empty, non-falsy value."""
    return (val or "").strip().lower() not in _COPILOT_OFF_VALUES


def _copilot_skill_selection(val: Optional[str]) -> str:
    """Resolve NEXUS_HUB_COPILOT_SKILLS to ``all`` or a bundle id.

    Bare-truthy (or any off value) maps to the default bundle; ``all`` selects the
    full catalog; anything else is treated as a bundle id.
    """
    v = (val or "").strip().lower()
    if v in _COPILOT_BARE_TRUTHY or v in _COPILOT_OFF_VALUES:
        return _COPILOT_CURATED_BUNDLE
    return v


def _copilot_home() -> Path:
    """Return Copilot's user-profile root (``~/.copilot``).

    A module-level accessor rather than an inline ``Path.home()`` so tests can
    redirect it, matching the ``_vscode_user_dir`` pattern next to it. Both
    surfaces this integration writes globally are reachable only through one of
    these two functions, which is what keeps a test run out of the developer's
    real home directory.
    """
    return (Path.home() / _COPILOT_HOME).resolve()


def _vscode_user_dir() -> Optional[Path]:
    """Return the VS Code (or Insiders) user-data dir, or None if not present.

    Windows: %APPDATA%/Code/User ; macOS: ~/Library/Application Support/Code/User ;
    Linux: ~/.config/Code/User. Falls back to the Insiders variant if stable is
    absent. Returns None when neither exists (VS Code not installed).
    """
    home = Path.home()
    system = platform.system()
    if system == "Windows":
        base = Path(os.environ.get("APPDATA") or (home / "AppData" / "Roaming"))
    elif system == "Darwin":
        base = home / "Library" / "Application Support"
    else:
        base = home / ".config"
    for variant in ("Code", "Code - Insiders"):
        candidate = base / variant / "User"
        if candidate.exists():
            return candidate
    return None


class CopilotIntegration(MarkdownIntegration):
    key = "copilot"
    display_name = "GitHub Copilot (Microsoft)"
    # v2.3.0 / Phase 7 / MT-1 -- Copilot now uses the canonical
    # `merge_marker_section` primitive (like Cursor), migrating the v2.1
    # `## Nexus-Hub Harness` legacy header inline into the marker block so user
    # content above and below the block is preserved across re-installs.
    instruction_mode = "shared"
    config = {
        "global_dir": None,
        "workspace_dir": ".github",
        "instruction_file": "copilot-instructions.md",
        "instruction_template": "templates/ai-instructions/base-codex.md",
        "agents_subdir": "agents",
        "hooks_subdir": "hooks",
        "hooks_supported": True,
    }

    def install_global(self, ctx: InstallContext) -> WriteResult:
        """Write personal instructions, prompts, agents, and native hooks.

        Commands become ``<name>.prompt.md`` under VS Code's user-profile
        ``prompts/`` dir, offered as ``/<name>`` in Copilot Chat from any repo.
        Catalog agents become ``<name>.agent.md`` under ``~/.copilot/agents``,
        Copilot's documented user-profile agent location (v3.15.8 Phase 8).

        Detection accepts either signal, because the two surfaces live in
        different places: a VS Code user-data dir covers the prompt files, and an
        existing ``~/.copilot`` covers a Copilot CLI user with no VS Code install.
        When neither is present, Copilot is not installed for this user and the
        whole global write is skipped.
        """
        result = WriteResult()
        user_dir = _vscode_user_dir()
        copilot_home = _copilot_home()
        if user_dir is None and not copilot_home.exists():
            ctx.manifest.log(
                self.key,
                "no VS Code user dir and no ~/.copilot; skipping global install",
            )
            result.mark_not_detected(
                "Copilot not detected (no VS Code user dir, no ~/.copilot); "
                "global prompt files + agents skipped"
            )
            return result
        result.detected = True
        if user_dir is not None:
            prompts_dir = (user_dir / "prompts").resolve()
            self._ensure_dir(prompts_dir, ctx)
            result.files.extend(
                mirror_command_surface(ctx, self.key, prompts_dir, suffix=".prompt.md")
            )
        if not ctx.instruction_only:
            self._ensure_dir(copilot_home, ctx)
            result.files.append(self._write_personal_instruction(copilot_home, ctx))
            result.files.extend(self._install_global_agents(copilot_home, ctx))
            result.files.extend(
                self._install_native_hooks(copilot_home, ctx, scope="global")
            )
        return result

    # ----- global custom agents (v3.15.8 Phase 8) --------------------------

    @staticmethod
    def agent_skip_reason(markdown: str) -> Optional[str]:
        """Return why Copilot would reject this agent file, or None if it is fine.

        Copilot requires only ``description``; ``name`` is an optional display
        name, unrecognized frontmatter is ignored, and Claude's tool names are
        mapped to VS Code tools. The one hard limit is the 30,000-character
        prompt cap, which a catalog agent could plausibly reach.
        """
        meta, body = _split_frontmatter(markdown)
        if not meta.get("description", "").strip():
            return "no description field (required by Copilot)"
        if not body.strip():
            return "no body to use as the agent prompt"
        if len(body) > _MAX_AGENT_PROMPT_CHARS:
            return f"prompt is {len(body)} chars, over Copilot's {_MAX_AGENT_PROMPT_CHARS} cap"
        return None

    def _install_global_agents(
        self, copilot_home: Path, ctx: InstallContext
    ) -> list[FileAction]:
        """Copy catalog agents to ``~/.copilot/agents/<name>.agent.md``, verbatim.

        Copilot accepts the catalog's Claude-style frontmatter as-is, so this is a
        validated copy rather than a transform -- the same conclusion Phase 7
        reached for Kimi. Writes go through ``write_owned_file`` so a user-authored
        agent at the same path is preserved and a drifted owned one is repaired.
        """
        return self._install_agents(copilot_home / _COPILOT_AGENTS_SUBDIR, ctx)

    def _install_agents(
        self, dst_dir: Path, ctx: InstallContext
    ) -> list[FileAction]:
        """Copy catalog agents into one Copilot-native agent directory."""
        src_dir = ctx.repo_root / "catalog" / "agents"
        if not src_dir.exists():
            ctx.manifest.log(self.key, f"missing-tree: {src_dir}")
            return [FileAction(path=str(src_dir), action="not-found")]
        self._ensure_dir(dst_dir, ctx)
        actions: list[FileAction] = []
        for md in sorted(src_dir.glob("*.md")):
            content = md.read_bytes()
            reason = self.agent_skip_reason(content.decode("utf-8"))
            if reason is not None:
                ctx.manifest.log(self.key, f"skip agent ({reason}): {md.name}")
                continue
            dst = dst_dir / f"{md.stem}{_AGENT_SUFFIX}"
            actions.append(write_owned_file(ctx, self.key, dst, content))
        return actions

    def _write_personal_instruction(
        self, copilot_home: Path, ctx: InstallContext
    ) -> FileAction:
        """Marker-merge Nexus-Hub into Copilot's personal instruction file."""
        template = ctx.repo_root / self.config["instruction_template"]
        if not template.exists():
            return FileAction(path=str(template), action="not-found")
        dst = copilot_home / "copilot-instructions.md"
        action = merge_marker_section(
            dst,
            self._render(template, ctx),
            legacy_header="## Nexus-Hub",
            dry_run=ctx.dry_run,
        )
        ctx.manifest.track_shared(self.key, str(dst))
        return action

    def _hooks_command_base(
        self, copilot_home_or_github: Path, scope: str
    ) -> str:
        scripts_subdir = "nexus-hub-scripts"
        if scope == "workspace":
            return f".github/{self.config['hooks_subdir']}/{scripts_subdir}"
        return (
            copilot_home_or_github / self.config["hooks_subdir"] / scripts_subdir
        ).as_posix()

    def _install_native_hooks(
        self,
        copilot_home_or_github: Path,
        ctx: InstallContext,
        *,
        scope: str,
    ) -> list[FileAction]:
        """Write one Copilot-native hook file and its referenced scripts."""
        src_hooks = ctx.repo_root / "catalog" / "hooks"
        settings_file = src_hooks / "settings.json"
        if not settings_file.exists():
            return [FileAction(path=str(settings_file), action="not-found")]
        command_base = self._hooks_command_base(copilot_home_or_github, scope)
        try:
            settings = json.loads(settings_file.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return [FileAction(path=str(settings_file), action="kept")]
        payload, scripts, skipped = build_copilot_hooks(
            settings, src_hooks, command_base
        )
        for reason in skipped:
            ctx.manifest.log(self.key, f"skip-hook {reason}")
        hooks_root = copilot_home_or_github / self.config["hooks_subdir"]
        scripts_root = hooks_root / "nexus-hub-scripts"
        actions = [
            write_owned_file(
                ctx,
                self.key,
                scripts_root / script,
                (src_hooks / script).read_bytes(),
            )
            for script in sorted(scripts)
        ]
        compat_source = (
            ctx.repo_root
            / "scripts"
            / "lib"
            / "integrations"
            / "_cascade_hook_compat.py"
        )
        actions.append(
            write_owned_file(
                ctx,
                self.key,
                scripts_root / "copilot-hook-compat.py",
                compat_source.read_bytes(),
            )
        )
        actions.append(
            write_owned_file(
                ctx,
                self.key,
                hooks_root / "nexus-hub.json",
                (json.dumps(payload, indent=2) + "\n").encode("utf-8"),
            )
        )
        return actions

    def teardown(self, ctx: InstallContext) -> WriteResult:
        """Run the manifest sweep, then drop native directories if they emptied."""
        result = super().teardown(ctx)
        if ctx.scope == "global":
            root = _copilot_home()
        else:
            root = (ctx.target_root / ".github").resolve()
        remove_dir_if_empty(root / _COPILOT_AGENTS_SUBDIR, ctx, result)
        remove_dir_if_empty(
            root / self.config["hooks_subdir"] / "nexus-hub-scripts", ctx, result
        )
        remove_dir_if_empty(root / self.config["hooks_subdir"], ctx, result)
        return result

    def install_workspace(self, ctx: InstallContext) -> WriteResult:
        result = WriteResult()
        rel = self.config["workspace_dir"]
        target = (ctx.target_root / rel).resolve()
        self._ensure_dir(target, ctx)
        dst = target / self.config["instruction_file"]
        template = ctx.repo_root / self.config["instruction_template"]
        if not template.exists():
            ctx.manifest.log(self.key, f"missing-template: {template}")
            result.files.append(FileAction(path=str(template), action="not-found"))
            return result
        rendered = self._render(template, ctx)
        action = merge_marker_section(
            dst,
            rendered,
            legacy_header="## Nexus-Hub Harness",
            dry_run=ctx.dry_run,
        )
        ctx.manifest.track_shared(self.key, str(dst))
        result.files.append(action)
        if not ctx.instruction_only:
            result.files.extend(
                self._install_agents(target / self.config["agents_subdir"], ctx)
            )
            result.files.extend(
                self._install_native_hooks(target, ctx, scope="workspace")
            )
        return result

    def wire_project_surfaces(self, ctx: InstallContext) -> Optional[WriteResult]:
        """Opt-in: seed a selectable skill set as ``.github/skills/<name>/SKILL.md``.

        GitHub Copilot reads project Agent Skills natively from
        ``.github/skills/<name>/SKILL.md`` (the frontmatter ``name`` must match the
        directory; only ``name`` / ``description`` / ``license`` are recognized).
        Copilot reads this default-on (it no longer requires an opt-in), but
        ``.github/skills/`` is COMMIT-VISIBLE in the user's repo, so Nexus-Hub keeps
        seeding OFF by default and gated on ``NEXUS_HUB_COPILOT_SKILLS`` as a policy
        choice. The env var is a SELECTOR (v3.15.0 Phase 5): bare-truthy seeds the
        ``core-developer`` bundle (default), a bundle id from ``data/bundles.json``
        seeds that bundle, and ``all`` seeds the full catalog (heavy). It seeds thin
        WRAPPER files (Copilot-safe ``name`` + ``description`` frontmatter plus a
        pointer to the installed ``~/.nexus-hub/`` content), ASCII-sanitized, never
        overwriting an existing file. See docs/releases/v3/v3.11/development/copilot-skills-design.md.
        """
        result = WriteResult()
        if not _copilot_skills_enabled(os.environ.get(_COPILOT_SKILLS_ENV)):
            ctx.manifest.log(
                self.key,
                f"{_COPILOT_SKILLS_ENV} not set; skipping .github/skills seeding",
            )
            result.note(
                f"Copilot project skills opt-in ({_COPILOT_SKILLS_ENV}=1, "
                "a bundle id, or 'all') not set; .github/skills/ not seeded"
            )
            return result
        # Project agents and native hooks are seeded only once the opt-in is set.
        # They land under the same COMMIT-VISIBLE .github/ tree the opt-in exists to
        # protect, so gating skills while writing these unconditionally would put 82
        # uninvited files into every consuming repository (v4.3.0 Phase 5 regression).
        github_root = (ctx.target_root / ".github").resolve()
        if not ctx.instruction_only:
            result.files.extend(
                self._install_agents(github_root / self.config["agents_subdir"], ctx)
            )
            result.files.extend(
                self._install_native_hooks(github_root, ctx, scope="workspace")
            )
        skills_root = (ctx.target_root / ".github" / "skills").resolve()
        for name in self._curated_skill_names(ctx):
            src_md = self._find_skill_md(ctx.repo_root, name)
            if src_md is None:
                ctx.manifest.log(self.key, f"curated skill not in catalog, skipping: {name}")
                result.files.append(FileAction(path=name, action="not-found"))
                continue
            dst = skills_root / name / "SKILL.md"
            if dst.exists():
                # Never overwrite a user's committed .github/skills file.
                ctx.manifest.log(self.key, f"skip-existing (never overwrite): {dst}")
                result.files.append(FileAction(path=str(dst), action="kept"))
                continue
            result.files.append(
                self._write_generated(dst, self._wrapper_skill_md(name, src_md), ctx, self.key)
            )
        return result

    @classmethod
    def _curated_skill_names(cls, ctx: InstallContext) -> list[str]:
        """Resolve ``NEXUS_HUB_COPILOT_SKILLS`` to the skill names to seed.

        ``all`` -> every catalog skill; a bundle id -> that bundle; bare-truthy or
        an unset value -> the default ``core-developer`` bundle. An unknown bundle
        id falls back to the default (with a logged note) so an opted-in user still
        gets a sensible set rather than nothing.
        """
        sel = _copilot_skill_selection(os.environ.get(_COPILOT_SKILLS_ENV))
        if sel == "all":
            return cls._all_catalog_skill_names(ctx)
        names = cls._bundle_skill_names(ctx, sel)
        if names:
            return names
        if sel != _COPILOT_CURATED_BUNDLE:
            ctx.manifest.log(
                cls.key,
                f"unknown Copilot skill bundle {sel!r}; using {_COPILOT_CURATED_BUNDLE!r}",
            )
        return cls._bundle_skill_names(ctx, _COPILOT_CURATED_BUNDLE)

    @staticmethod
    def _bundle_skill_names(ctx: InstallContext, bundle_id: str) -> list[str]:
        """Return the skill names for a bundle id from data/bundles.json (or [])."""
        try:
            data = json.loads((ctx.repo_root / "data" / "bundles.json").read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return []
        bundles = data.get("bundles", []) if isinstance(data, dict) else data
        for b in bundles if isinstance(bundles, list) else []:
            if (b.get("id") or b.get("name")) == bundle_id:
                return [str(s) for s in b.get("skills", [])]
        return []

    @staticmethod
    def _all_catalog_skill_names(ctx: InstallContext) -> list[str]:
        """Return every catalog skill's directory name (``catalog/skills/<cat>/<name>``)."""
        root = ctx.repo_root / "catalog" / "skills"
        return sorted({p.parent.name for p in root.glob("*/*/SKILL.md")})

    @staticmethod
    def _find_skill_md(repo_root: Path, name: str) -> Optional[Path]:
        matches = sorted((repo_root / "catalog" / "skills").glob(f"*/{name}/SKILL.md"))
        return matches[0] if matches else None

    @staticmethod
    def _ascii(text: str) -> str:
        return text.encode("ascii", "ignore").decode("ascii").strip()

    @classmethod
    def _wrapper_description(cls, src_md: Path) -> str:
        """Prefer the skill's summary_l0; fall back to the description's lead."""
        try:
            text = src_md.read_text(encoding="utf-8")
        except OSError:
            return "Nexus-Hub skill."
        summary = ""
        for line in text.splitlines():
            if line.startswith("summary_l0:"):
                summary = line.split(":", 1)[1].strip().strip('"').strip()
                break
        if not summary:
            for line in text.splitlines():
                if line.startswith("description:"):
                    summary = line.split(":", 1)[1].strip().strip('"').split(". ")[0]
                    break
        return (cls._ascii(summary) or "Nexus-Hub skill.")[:200]

    @classmethod
    def _wrapper_skill_md(cls, name: str, src_md: Path) -> str:
        desc = cls._wrapper_description(src_md).replace('"', "'")
        return (
            "---\n"
            f"name: {name}\n"
            f'description: "{desc}"\n'
            "---\n\n"
            f"# {name}\n\n"
            "Nexus-Hub skill wrapper. The full instructions for this skill ship with "
            f"the Nexus-Hub catalog under `~/.nexus-hub/skills/**/{name}/SKILL.md`. "
            "Read that file for the complete procedure, verification checklist, and "
            "related skills.\n"
        )
