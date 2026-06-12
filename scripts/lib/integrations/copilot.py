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

import os
import platform
from pathlib import Path
from typing import Optional

from .base import InstallContext, MarkdownIntegration
from .result import FileAction, WriteResult
from ._command_surface import mirror_command_surface
from scripts.lib.installer.instruction_merge import merge_marker_section


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
        "permissions_file": "configs/permissions/copilot-permissions.json",
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
            result.note("VS Code user dir not found; global Copilot prompt files skipped")
            return result
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
