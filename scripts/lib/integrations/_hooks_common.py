"""Hook primitives shared by every native-hook adapter (v3.15.8 Phase 9).

Phases 5 through 8 added four native-hook adapters -- Codex (`hooks.json`),
Gemini CLI and Qwen (`settings.json`), and Kimi (`config.toml`) -- and each one
needed the same three low-level operations:

  - work out which catalog script a ``catalog/hooks/settings.json`` command runs,
  - pick the sibling and interpreter the installing host can execute, and
  - decide whether a handler already in the user's config is one of ours.

Those grew a copy per adapter. This module is the single home for them, so a fix
to the ownership predicate or the Windows command shape lands once rather than
three times. The parts that are genuinely per-platform -- event names, matcher
vocabularies, file formats, merge strategies -- stay in each platform's own
module, because those differences are real and collapsing them would hide the
schema divergence the read contract exists to document.

Before Phase 9 the host helpers lived in ``_settings_hooks`` and Kimi imported
them from there, which read as a Kimi-on-Gemini-CLI dependency that was never
intended. Moving them here repairs that reference.

This module is stdlib-only and makes no outbound calls.
"""

from __future__ import annotations

import os
from pathlib import Path

# Every Nexus-Hub handler that carries a platform-supported ``name`` field uses
# this prefix, which is what makes ownership survive a path change. Codex's
# schema has no ``name`` slot and Kimi's forbids extra fields, so those adapters
# fall back to the command path; the predicate below accepts either signal.
OWNED_NAME_PREFIX = "nexus-hub:"


# ----- host-aware command construction ------------------------------------


def is_windows_host() -> bool:
    """True when the installing host runs Windows.

    Isolated in a function so tests can exercise both branches without touching
    ``os.name``, and so the single place this decision is made is obvious.
    """
    return os.name == "nt"


def host_shell(windows: bool) -> str:
    return "powershell" if windows else "bash"


def script_basename(command: str) -> str | None:
    """Return the script filename a catalog hook command runs.

    Catalog commands are ``<runner> <path>`` (for example
    ``bash .claude/hooks/secret-scan.sh``), so the script is the basename of the
    last token. Returns ``None`` for a command with no argument, which no catalog
    entry has but a hand-edited one might.
    """
    parts = command.split()
    if len(parts) < 2:
        return None
    return os.path.basename(parts[-1])


def script_for_host(script: str, windows: bool) -> str:
    """Return the sibling of ``script`` that the host can execute.

    Relies on the v3.15.6 invariant that every ``catalog/hooks/<name>.sh`` ships
    a behavior-matched ``<name>.ps1``. Python hooks are cross-platform already
    and are returned unchanged.
    """
    if script.endswith(".py"):
        return script
    if windows:
        return f"{Path(script).stem}.ps1"
    return f"{Path(script).stem}.sh"


def command_for(script: str, base: str, windows: bool) -> str:
    """Build the command string that runs ``script`` out of ``base``.

    The path is quoted because a hooks directory under a user profile routinely
    contains a space.
    """
    target = f"{base}/{script}"
    if script.endswith(".py"):
        return f"{'python' if windows else 'python3'} {target}"
    if windows:
        return f'powershell -NoProfile -ExecutionPolicy Bypass -File "{target}"'
    return f'bash "{target}"'


def sibling_scripts(script: str) -> tuple[str, str]:
    """Return both shell siblings of ``script`` (``.sh`` then ``.ps1``).

    Adapters copy both regardless of host, so re-running the installer on the
    other OS only has to re-point the registration.
    """
    stem = Path(script).stem
    return f"{stem}.sh", f"{stem}.ps1"


def sourced_modules(scripts: set[str], src_hooks_dir: Path) -> set[str]:
    """Return underscore-prefixed sibling modules sourced by delivered hooks."""
    found: set[str] = set()
    modules = [p for p in src_hooks_dir.glob("_*") if p.suffix in (".sh", ".ps1")]
    for script in sorted(scripts):
        path = src_hooks_dir / script
        if path.suffix not in (".sh", ".ps1") or not path.exists():
            continue
        try:
            body = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for module in modules:
            if module.name == script or module.name not in body:
                continue
            found.add(module.name)
            sibling = module.with_suffix(".ps1" if module.suffix == ".sh" else ".sh")
            if sibling.exists():
                found.add(sibling.name)
    return found


# ----- ownership of an existing handler ------------------------------------


def handler_is_owned(handler: dict, owned_base: str) -> bool:
    """True when a handler already in the user's config is a Nexus-Hub one.

    Two signals, because the platforms differ in what they allow. A
    ``nexus-hub:``-prefixed ``name`` is the primary identity where the schema has
    that field (Gemini CLI, Qwen). Where it does not (Codex, Kimi), or where the
    user renamed a handler by hand, a command pointing into the installed hooks
    directory is the fallback. ``commandWindows`` is checked because Codex's
    Windows override may be the only field carrying the path.
    """
    name = handler.get("name")
    if isinstance(name, str) and name.startswith(OWNED_NAME_PREFIX):
        return True
    for field in ("command", "commandWindows", "command_windows"):
        value = handler.get(field)
        if isinstance(value, str) and owned_base in value:
            return True
    return False


def strip_owned_handlers(groups: list, owned_base: str) -> list:
    """Drop Nexus-Hub handlers from ``groups``, preserving everything else.

    Filtering happens per handler rather than per group, so a user who added
    their own handler beside ours inside the same matcher group keeps it, and a
    group left with no handlers is dropped rather than emitted empty. Anything
    that is not a recognizable group is passed through untouched.
    """
    kept: list = []
    for group in groups:
        if not isinstance(group, dict) or "hooks" not in group:
            kept.append(group)
            continue
        handlers = [
            handler
            for handler in group.get("hooks", [])
            if not (isinstance(handler, dict) and handler_is_owned(handler, owned_base))
        ]
        if handlers:
            survivor = dict(group)
            survivor["hooks"] = handlers
            kept.append(survivor)
    return kept


__all__ = [
    "OWNED_NAME_PREFIX",
    "command_for",
    "handler_is_owned",
    "host_shell",
    "is_windows_host",
    "script_basename",
    "script_for_host",
    "sibling_scripts",
    "sourced_modules",
    "strip_owned_handlers",
]
