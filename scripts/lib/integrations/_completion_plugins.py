"""Opt-in completion-gate plugin for the plugin-only platforms (v4.13.2, opt-in since 2026-10-28).

OpenCode, OpenClaw, Pi, and Hermes expose their turn-end lever only through typed
plugins, so each can receive one thin plugin from ``catalog/plugins/completion-gate/``
that calls the installed gate core (``~/.nexus-hub/scripts/completion_gate.py``).
Decision record: ``docs/decisions/implemented/tooling/2026-10-28-remove-completion-gate-stop-default.md``
(supersedes the install-by-default decision of 2026-09-25).

The plugin re-prompts at the end of every agent turn during a full ``/implement``
run, including turns that end because the next step needs the user, CI, or an
approval. It is therefore NOT part of a default install.

Rules:
  - user-global only; callers pass a destination under the user's home,
  - off by default; ``NEXUS_HUB_COMPLETION_PLUGINS=1`` opts in when the platform
    is detected,
  - when it is off, a plugin an earlier install wrote is retired: only files the
    install manifest records as Nexus-Hub-owned are removed, so a plugin the user
    placed there by hand survives,
  - every copied file is manifest-owned, so uninstall and repair remove exactly
    what was installed,
  - platforms whose plugins load only after an enablement step get a NEEDS SETUP
    note naming the platform's own documented command; the installer never edits
    a platform config file whose location is not verified.
"""

from __future__ import annotations

import os
from pathlib import Path

from ._owned import is_owned, remove_dir_if_empty
from .base import long_path
from .result import FileAction

PLUGIN_ID = "nexus-completion-gate"
OPT_IN = "NEXUS_HUB_COMPLETION_PLUGINS"

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

# Platforms whose enablement lives in the platform's own config, which this
# installer never edits. The retirement note tells the user to undo it.
_ENABLEMENT_PLATFORMS = ("openclaw", "hermes")


def opted_in() -> bool:
    return os.environ.get(OPT_IN, "").strip() == "1"


def _retire_plugin(integration, ctx, platform: str, dest_dir: Path, result) -> None:
    """Remove the plugin files an earlier install wrote, never a file we do not own."""
    _, destinations, _ = SPECS[platform]
    removed = False
    for name in destinations:
        path = dest_dir / name
        if not long_path(path).exists() or not is_owned(ctx, integration.key, path):
            continue
        if not ctx.dry_run:
            long_path(path).unlink()
        ctx.manifest.untrack(integration.key, str(path))
        result.files.append(FileAction(path=str(path), action="removed"))
        removed = True
    if not removed:
        return
    if dest_dir.name == PLUGIN_ID:
        remove_dir_if_empty(dest_dir, ctx, result)
    ctx.manifest.log(integration.key, f"completion plugin retired (default-off): {dest_dir}")
    if platform in _ENABLEMENT_PLATFORMS:
        result.note(
            f"NOTE: the retired {PLUGIN_ID} plugin was enabled in the {integration.display_name} "
            "configuration by an earlier setup step; remove that enablement entry so the platform "
            "stops looking for it."
        )


def install_completion_plugin(integration, ctx, platform: str, dest_dir: Path, result) -> None:
    """Copy the platform's completion plugin into ``dest_dir`` only when opted in.

    Off by default: a default install writes nothing and retires an earlier copy.
    """
    if not opted_in():
        _retire_plugin(integration, ctx, platform, dest_dir, result)
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


__all__ = ["OPT_IN", "PLUGIN_ID", "SPECS", "install_completion_plugin", "opted_in"]
