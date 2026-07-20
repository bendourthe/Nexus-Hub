"""GitHub Copilot integration.

Copilot (in VS Code) reads .github/copilot-instructions.md at repo root for
custom instructions, and respects the
`github.copilot.chat.codeGeneration.useInstructionFiles` VS Code setting.

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
"""

from __future__ import annotations

import json
import os
import platform
from pathlib import Path
from typing import Optional

from .base import InstallContext, MarkdownIntegration
from .result import FileAction, WriteResult
from ._command_surface import mirror_command_surface
from scripts.lib.installer.instruction_merge import merge_marker_section

# v3.11.0 Phase 5 (S3): opt-in project-scoped skills surface.
# .github/skills/ is commit-visible in the user's repo, so seeding is OFF by
# default and activates only when this env var is truthy (mirrors the Phase 7.3
# NEXUS_HUB_NO_AUTOSEED opt-out pattern; no installer.sh/ps1 edit required).
_COPILOT_SKILLS_ENV = "NEXUS_HUB_COPILOT_SKILLS"
_COPILOT_CURATED_BUNDLE = "core-developer"


def _is_truthy(val: Optional[str]) -> bool:
    return (val or "").strip().lower() in {"1", "true", "yes", "on"}


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
        "hooks_supported": False,
    }

    def install_global(self, ctx: InstallContext) -> WriteResult:
        """Mirror catalog commands into VS Code's user-profile ``prompts/`` dir.

        Each ``<name>.prompt.md`` becomes ``/<name>`` in Copilot Chat from any
        repo. Skipped with a note when no VS Code user dir is found.
        """
        result = WriteResult()
        user_dir = _vscode_user_dir()
        if user_dir is None:
            ctx.manifest.log(self.key, "VS Code user dir not found; skipping global prompt-file install")
            result.mark_not_detected("VS Code user dir not found; global Copilot prompt files skipped")
            return result
        result.detected = True
        prompts_dir = (user_dir / "prompts").resolve()
        self._ensure_dir(prompts_dir, ctx)
        result.files.extend(
            mirror_command_surface(ctx, self.key, prompts_dir, suffix=".prompt.md")
        )
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
        return result

    def wire_project_surfaces(self, ctx: InstallContext) -> Optional[WriteResult]:
        """Opt-in: seed a curated skill set as ``.github/skills/<name>/SKILL.md``.

        GitHub Copilot reads project Agent Skills from
        ``.github/skills/<name>/SKILL.md`` (the frontmatter ``name`` must match the
        directory; only ``name`` / ``description`` / ``license`` are recognized).
        This is OFF by default because ``.github/skills/`` is commit-visible; it
        activates only when ``NEXUS_HUB_COPILOT_SKILLS`` is truthy. It seeds thin
        WRAPPER files (Copilot-safe ``name`` + ``description`` frontmatter plus a
        pointer to the installed ``~/.nexus-hub/`` content) for the
        ``core-developer`` bundle, ASCII-sanitized, never overwriting an existing
        file. See docs/v3/v3.11/development/copilot-skills-design.md.
        """
        result = WriteResult()
        if not _is_truthy(os.environ.get(_COPILOT_SKILLS_ENV)):
            ctx.manifest.log(
                self.key,
                f"{_COPILOT_SKILLS_ENV} not set; skipping .github/skills seeding",
            )
            result.note(
                f"Copilot project skills opt-in ({_COPILOT_SKILLS_ENV}=1) not set; "
                ".github/skills/ not seeded"
            )
            return result
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

    @staticmethod
    def _curated_skill_names(ctx: InstallContext) -> list[str]:
        """Return the curated bundle's skill names from data/bundles.json."""
        try:
            data = json.loads((ctx.repo_root / "data" / "bundles.json").read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return []
        bundles = data.get("bundles", []) if isinstance(data, dict) else data
        for b in bundles if isinstance(bundles, list) else []:
            if (b.get("id") or b.get("name")) == _COPILOT_CURATED_BUNDLE:
                return [str(s) for s in b.get("skills", [])]
        return []

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
