"""Nexus-AI integration -- the local-first desktop AI Studio consumer of Nexus-Hub.

Nexus-AI lives in a separate repository (https://github.com/bendourthe/Nexus-AI).
It is the primary downstream consumer of Nexus-Hub's catalog.

The catalog is installed into an ISOLATED subtree, ``~/.nexus-ai/catalog/`` (and
``<project>/.nexus-ai/catalog/`` at workspace scope), never at the ``~/.nexus-ai/``
root. The root is the Nexus-AI app's own home (settings, MCP config, model
weights, session artifacts, credentials vault); the ``catalog/`` subtree is the
Nexus-Hub catalog the app pulls. Keeping the two apart is a deliberate safety
boundary: Nexus-AI's syncer (and this installer) may wholesale wipe-and-refresh
``catalog/`` without any chance of touching irreplaceable app data. Both
populators -- this integration and Nexus-AI's own syncer -- write ONLY under
``catalog/``.

Layout of ``~/.nexus-ai/catalog/``:

  - skills/                 mirror of catalog/skills/
  - commands/               mirror of catalog/commands/
  - agents/                 mirror of catalog/agents/
  - rules/                  mirror of catalog/rules/
  - hooks/                  mirror of catalog/hooks/
  - mcp-configs/            mirror of catalog/mcp-configs/  (global scope only)
  - templates/              mirror of templates/           (global scope only)
  - NEXUS_AI.md             instruction file (rendered from base-claude.md)
  - nexus-hub-version.json  installed-version manifest (see below)

Version manifest
----------------
``nexus-hub-version.json`` lives at the catalog root and records the installed
Nexus-Hub catalog version and the public release endpoints. The Nexus-AI desktop
app reads ``version`` to show which catalog version is installed, and polls
``latest_release_api`` to detect when a newer release is published upstream so it
can prompt the user to update from inside the app. It also carries a ``layout``
map -- paths relative to the manifest's own directory (the catalog root) -- so
the app can locate each surface without hardcoding the folder names.

The manifest is deterministic -- no timestamps, no absolute paths -- so a
re-install is a byte-identical no-op (the contract suite's idempotency
invariant), and it is manifest-tracked so uninstall removes it. The version is
read from the single canonical source, ``.claude-plugin/plugin.json``, the same
source ``scripts/check_version_sync.py`` enforces across every other surface.
"""

from __future__ import annotations

import json
from pathlib import Path

from .base import InstallContext, MarkdownIntegration, SkillsIntegration
from .result import FileAction, WriteResult

# Public, canonical Nexus-Hub coordinates baked into the version manifest so the
# Nexus-AI app can check for updates without having to hardcode them itself.
_SOURCE_REPO = "bendourthe/Nexus-Hub"
_RELEASES_URL = "https://github.com/bendourthe/Nexus-Hub/releases"
_LATEST_RELEASE_API = "https://api.github.com/repos/bendourthe/Nexus-Hub/releases/latest"
_VERSION_FILE = "nexus-hub-version.json"


class NexusAiIntegration(MarkdownIntegration, SkillsIntegration):
    key = "nexus-ai"
    display_name = "Nexus-AI (Local Desktop Studio)"
    instruction_mode = "dedicated"
    config = {
        # The catalog is isolated under a `catalog/` subtree so the app's own
        # data (at the `~/.nexus-ai/` root) is never in the refresh blast zone.
        "global_dir": "~/.nexus-ai/catalog",
        "workspace_dir": ".nexus-ai/catalog",
        "instruction_file": "NEXUS_AI.md",
        "instruction_template": "templates/ai-instructions/base-claude.md",
        # Nexus-AI follows the SKILL.md open standard (one level deep); flatten the
        # <category>/ layer and add command-skills (v3.12.0 Phase 4).
        "skills_subdir": "skills",
        "flatten_skills_layout": True,
        "commands_subdir": "commands",
        "agents_subdir": "agents",
        "rules_subdir": "rules",
        "hooks_subdir": "hooks",
        "hooks_supported": True,
    }

    def _read_catalog_version(self, ctx: InstallContext) -> str:
        """Return the canonical catalog version from ``.claude-plugin/plugin.json``.

        This is the single source of truth enforced by
        ``scripts/check_version_sync.py``. Falls back to ``"0.0.0"`` (logged to
        the manifest) if the canonical file is missing or unparseable, so an
        install never hard-fails on a partial tree.
        """
        canonical = ctx.repo_root / ".claude-plugin" / "plugin.json"
        try:
            data = json.loads(canonical.read_text(encoding="utf-8"))
            version = data.get("version")
            if isinstance(version, str) and version:
                return version
        except (OSError, ValueError) as exc:
            ctx.manifest.log(self.key, f"version-source-unreadable: {canonical} ({exc})")
        return "0.0.0"

    def _version_manifest_text(self, ctx: InstallContext) -> str:
        """Build the deterministic ``nexus-hub-version.json`` payload.

        Location-independent and timestamp-free so a re-install is a
        byte-identical no-op. ``layout`` paths are relative to this manifest's
        own directory (the catalog root) so the app resolves every surface from
        one place.
        """
        payload = {
            "product": "Nexus-Hub",
            "version": self._read_catalog_version(ctx),
            "source_repo": _SOURCE_REPO,
            "releases_url": _RELEASES_URL,
            "latest_release_api": _LATEST_RELEASE_API,
            "layout": {
                "skills": self.config["skills_subdir"],
                "commands": self.config["commands_subdir"],
                "agents": self.config["agents_subdir"],
                "rules": self.config["rules_subdir"],
                "hooks": self.config["hooks_subdir"],
                "mcp_configs": "mcp-configs",
                "templates": "templates",
                "instructions": self.config["instruction_file"],
            },
        }
        return json.dumps(payload, indent=2) + "\n"

    def _write_version_file(self, target: Path, ctx: InstallContext) -> FileAction:
        """Write ``nexus-hub-version.json`` into the catalog root ``target``."""
        return self._write_generated(
            target / _VERSION_FILE, self._version_manifest_text(ctx), ctx, self.key
        )

    def install_global(self, ctx: InstallContext) -> WriteResult:
        result = super().install_global(ctx)
        target = (Path.home() / ".nexus-ai" / "catalog").resolve()
        mcp_src = ctx.repo_root / "catalog" / "mcp-configs"
        mcp_dst = target / "mcp-configs"
        result.files.append(self._copy_tree(mcp_src, mcp_dst, ctx, self.key))
        tpl_src = ctx.repo_root / "templates"
        tpl_dst = target / "templates"
        result.files.append(self._copy_tree(tpl_src, tpl_dst, ctx, self.key))
        result.files.append(self._write_version_file(target, ctx))
        return result

    def install_workspace(self, ctx: InstallContext) -> WriteResult:
        result = super().install_workspace(ctx)
        target = (ctx.target_root / ".nexus-ai" / "catalog").resolve()
        result.files.append(self._write_version_file(target, ctx))
        return result
