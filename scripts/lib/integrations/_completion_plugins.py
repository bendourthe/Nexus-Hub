"""Install the v4.13.2 completion-gate plugin on plugin-only platforms.

OpenCode, OpenClaw, Pi, and Hermes expose their turn-end lever only through typed
plugins, so each receives one thin plugin from ``catalog/plugins/completion-gate/``
that calls the installed gate core (``~/.nexus-hub/scripts/completion_gate.py``).
Decision record: ``docs/decisions/implemented/architecture/2026-09-25-install-completion-plugins-by-default.md``.

Rules:
  - user-global only; callers pass a destination under the user's home,
  - default-on when the platform is detected; ``NEXUS_HUB_COMPLETION_PLUGINS=0``
    opts out before anything is written,
  - every copied file is manifest-owned, so uninstall and repair remove exactly
    what was installed,
  - platforms whose plugins load only after an enablement step get a NEEDS SETUP
    note naming the platform's own documented command; the installer never edits
    a platform config file whose location is not verified.
"""

from __future__ import annotations

import os
from pathlib import Path

PLUGIN_ID = "nexus-completion-gate"
OPT_OUT = "NEXUS_HUB_COMPLETION_PLUGINS"

# platform -> (source files under catalog/plugins/completion-gate/<platform>/,
#              destination names relative to the destination directory,
#              NEEDS SETUP note or None)
SPECS: dict[str, tuple[tuple[str, ...], tuple[str, ...], str | None]] = {
    "opencode": (("nexus-completion-gate.ts",), ("nexus-completion-gate.ts",), None),
    "pi": (("nexus-completion-gate.ts",), ("nexus-completion-gate.ts",), None),
    "openclaw": (
        ("package.json", "openclaw.plugin.json", "index.ts"),
        ("package.json", "openclaw.plugin.json", "index.ts"),
        (
            "NEEDS SETUP: enable the completion plugin with `openclaw plugins enable nexus-completion-gate` "
            "and allow its conversation hook (plugins.entries.nexus-completion-gate.hooks.allowConversationAccess: true)."
        ),
    ),
    "hermes": (
        ("plugin.yaml", "__init__.py"),
        ("plugin.yaml", "__init__.py"),
        "NEEDS SETUP: Hermes loads plugins only when enabled; run `hermes plugins enable nexus-completion-gate`.",
    ),
}


def opted_out() -> bool:
    return os.environ.get(OPT_OUT, "").strip() == "0"


def install_completion_plugin(integration, ctx, platform: str, dest_dir: Path, result) -> None:
    """Copy the platform's completion plugin into ``dest_dir`` (manifest-owned)."""
    if opted_out():
        ctx.manifest.log(integration.key, f"{OPT_OUT}=0: completion plugin skipped")
        return
    sources, destinations, note = SPECS[platform]
    src_dir = ctx.repo_root / "catalog" / "plugins" / "completion-gate" / platform
    if not src_dir.is_dir():
        ctx.manifest.log(integration.key, f"missing-tree: {src_dir}")
        return
    integration._ensure_dir(dest_dir, ctx)
    for source, destination in zip(sources, destinations):
        result.files.append(
            integration._copy_file(src_dir / source, dest_dir / destination, ctx, integration.key)
        )
    if note:
        result.note(note)


__all__ = ["OPT_OUT", "PLUGIN_ID", "SPECS", "install_completion_plugin", "opted_out"]
