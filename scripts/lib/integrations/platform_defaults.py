"""Seed per-platform install-time behavioral defaults into a platform's own config.

The values are DECLARED in ``configs/platform-defaults.json`` (see
``configs/README.md``) and consumed here at install time. This module is the
Phase 3 counterpart to Phase 1's ``scripts/sync_platform_defaults.py``: that
script derives repo artifacts from the source, this one seeds a user's platform
config from the same source.

Three rules govern every write, and each exists because the alternative is
hostile:

1. **Seed-if-absent, never overwrite.** A key the user has already set is left
   exactly as they set it. A reinstall must never quietly reset someone's
   effort level back to the shipped default.
2. **Never destroy what we did not write.** A user's config carries their own
   keys, comments, and formatting. TOML is edited through ``tomlkit``, which
   round-trips comments and layout. YAML is only ever *appended* to, because a
   plain PyYAML round-trip silently strips every comment in the file.
3. **Degrade, never fail.** A missing source file, a missing optional
   dependency, or an unreadable target config results in a skipped seed and a
   one-line note. An install must not break because a default could not be
   written.

Only platforms whose ``install_target.mode`` is ``"write"`` are seeded.
``"already-delivered"`` means an existing installer path already carries the
values (Claude, whose ``~/.claude/settings.json`` is copied from the derived
template). ``"not-writable"`` means the lever is declared for the record but
deliberately not written, with the reason recorded in the source.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple

from .result import FileAction

# Same candidate resolution as scripts/lib/integrations/claude.py: the repo
# checkout first, then a bootstrap-materialized source tree. The installers do
# not copy configs/ into ~/.nexus-hub, so an installed tree finds the source
# only when the one-line bootstrap put a checkout at ~/.nexus-hub/src.
_DEFAULTS_CANDIDATES: Tuple[Path, ...] = (
    Path(__file__).resolve().parents[3] / "configs" / "platform-defaults.json",
    Path.home() / ".nexus-hub" / "src" / "configs" / "platform-defaults.json",
)

SUPPORTED_FORMATS = ("json", "toml", "yaml")

# Written above a seeded block so a user can tell where the values came from.
_BANNER = "Seeded by Nexus-Hub from configs/platform-defaults.json (edit freely)."


def _note(message: str) -> None:
    """One-line diagnostic. Never raises, never blocks an install."""
    print(f"note: platform-defaults: {message}", file=sys.stderr)


# --------------------------------------------------------------------------
# Source loading
# --------------------------------------------------------------------------


def load_source(candidates: Tuple[Path, ...] = _DEFAULTS_CANDIDATES) -> Dict[str, Any]:
    """Return the declared source, or an empty dict when it is unreachable.

    Absence is the normal case on an installed tree that carries no checkout,
    so it degrades silently. A file that exists but cannot be parsed is a real
    defect and gets one line on stderr.
    """
    for path in candidates:
        if not path.is_file():
            continue
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            _note(f"{path} is unreadable ({exc}); no defaults seeded.")
            return {}
    return {}


def declared_for(key: str, source: Dict[str, Any] | None = None) -> Dict[str, Any]:
    """Return the platform's entry, or an empty dict when it declares nothing."""
    data = load_source() if source is None else source
    entry = data.get("platforms", {}).get(key)
    return entry if isinstance(entry, dict) else {}


# --------------------------------------------------------------------------
# Seed-if-absent merge
# --------------------------------------------------------------------------


def merge_missing(target: Dict[str, Any], declared: Dict[str, Any]) -> List[str]:
    """Set every declared leaf that is absent from ``target``, in place.

    Returns the dotted paths actually added. A key the user already set is left
    untouched, including the case where they set a scalar where the declaration
    expects a table: clobbering that would destroy a deliberate choice.
    """
    added: List[str] = []
    for key, value in declared.items():
        if isinstance(value, dict):
            existing = target.get(key)
            if existing is None and key not in target:
                target[key] = {}
                existing = target[key]
            elif not isinstance(existing, dict):
                continue  # user put something else here; leave it alone
            added.extend(f"{key}.{path}" for path in merge_missing(existing, value))
        elif key not in target:
            target[key] = value
            added.append(key)
    return added


def _expand(path_str: str) -> Path:
    """Expand ~ and environment variables in a declared target path.

    ``~`` is resolved through ``Path.home()`` rather than
    ``os.path.expanduser``, matching how ``base.py`` resolves every other
    global target. This is not a style preference: the test suite isolates
    installs by patching ``Path.home``, so an ``expanduser`` call silently
    escapes the fake home and writes into the real one.
    """
    expanded = os.path.expandvars(path_str)
    if expanded == "~":
        return Path.home()
    if expanded.startswith("~/") or expanded.startswith("~\\"):
        return Path.home() / expanded[2:]
    return Path(expanded)


# --------------------------------------------------------------------------
# Per-format writers
# --------------------------------------------------------------------------


def _seed_json(path: Path, declared: Dict[str, Any], dry_run: bool) -> Tuple[str, List[str]]:
    if path.is_file():
        try:
            data = json.loads(path.read_text(encoding="utf-8") or "{}")
        except ValueError as exc:
            _note(f"{path} is not valid JSON ({exc}); left untouched.")
            return "kept", []
        if not isinstance(data, dict):
            _note(f"{path} is not a JSON object; left untouched.")
            return "kept", []
        added = merge_missing(data, declared)
        if not added:
            return "kept", []
        if not dry_run:
            path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        return "updated", added

    data = json.loads(json.dumps(declared))  # deep copy
    added = _leaf_paths(declared)
    if not dry_run:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return "created", added


def _seed_toml(path: Path, declared: Dict[str, Any], dry_run: bool) -> Tuple[str, List[str]]:
    """Edit TOML through tomlkit so comments and layout survive."""
    try:
        import tomlkit
    except ImportError:
        _note(
            f"tomlkit is not installed, so {path} was not seeded. "
            "Install it with: pip install tomlkit"
        )
        return "kept", []

    if path.is_file():
        try:
            doc = tomlkit.parse(path.read_text(encoding="utf-8"))
        except Exception as exc:  # tomlkit raises its own parse errors
            _note(f"{path} is not valid TOML ({exc}); left untouched.")
            return "kept", []
        added = merge_missing(doc, declared)
        if not added:
            return "kept", []
        if not dry_run:
            path.write_text(tomlkit.dumps(doc), encoding="utf-8")
        return "updated", added

    doc = tomlkit.document()
    doc.add(tomlkit.comment(_BANNER))
    merge_missing(doc, declared)
    if not dry_run:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(tomlkit.dumps(doc), encoding="utf-8")
    return "created", _leaf_paths(declared)


def _seed_yaml(path: Path, declared: Dict[str, Any], dry_run: bool) -> Tuple[str, List[str]]:
    """Create a YAML config, or APPEND wholly-absent top-level keys to one.

    PyYAML cannot round-trip comments: loading and re-dumping a user's config
    would silently delete every comment in it. So an existing file is only ever
    appended to, and only with top-level keys that are entirely absent. A
    declared key whose top-level parent already exists is skipped rather than
    merged, because appending a second mapping for an existing key would create
    a duplicate that silently wins or errors depending on the reader.
    """
    try:
        import yaml
    except ImportError:
        _note(
            f"PyYAML is not installed, so {path} was not seeded. "
            "Install it with: pip install PyYAML"
        )
        return "kept", []

    if path.is_file():
        text = path.read_text(encoding="utf-8")
        try:
            existing = yaml.safe_load(text) or {}
        except yaml.YAMLError as exc:
            _note(f"{path} is not valid YAML ({exc}); left untouched.")
            return "kept", []
        if not isinstance(existing, dict):
            _note(f"{path} is not a YAML mapping; left untouched.")
            return "kept", []
        to_add = {k: v for k, v in declared.items() if k not in existing}
        if not to_add:
            return "kept", []
        block = yaml.safe_dump(to_add, default_flow_style=False, sort_keys=True)
        suffix = "" if text.endswith("\n") else "\n"
        if not dry_run:
            path.write_text(f"{text}{suffix}\n# {_BANNER}\n{block}", encoding="utf-8")
        return "updated", _leaf_paths(to_add)

    body = yaml.safe_dump(declared, default_flow_style=False, sort_keys=True)
    if not dry_run:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(f"# {_BANNER}\n{body}", encoding="utf-8")
    return "created", _leaf_paths(declared)


_WRITERS = {"json": _seed_json, "toml": _seed_toml, "yaml": _seed_yaml}


def _leaf_paths(declared: Dict[str, Any], prefix: str = "") -> List[str]:
    paths: List[str] = []
    for key, value in declared.items():
        dotted = f"{prefix}{key}"
        if isinstance(value, dict):
            paths.extend(_leaf_paths(value, prefix=f"{dotted}."))
        else:
            paths.append(dotted)
    return paths


# --------------------------------------------------------------------------
# Entry point
# --------------------------------------------------------------------------


def seed_platform_defaults(key: str, ctx: Any, source: Dict[str, Any] | None = None) -> List[FileAction]:
    """Seed the platform's declared defaults into its own config file.

    Returns the FileActions performed (empty when the platform declares
    nothing, is not writable, or the scope is not global). Never raises.
    """
    if getattr(ctx, "scope", None) != "global":
        return []
    entry = declared_for(key, source)
    if not entry:
        return []
    target = entry.get("install_target") or {}
    if target.get("mode") != "write":
        return []
    declared = entry.get("settings") or {}
    if not declared:
        return []

    fmt = target.get("format")
    writer = _WRITERS.get(fmt)
    if writer is None:
        _note(f"{key}: unsupported target format {fmt!r}; nothing seeded.")
        return []

    path_str = target.get("path")
    if not path_str:
        _note(f"{key}: install_target declares no path; nothing seeded.")
        return []
    path = _expand(path_str)

    try:
        action, added = writer(path, declared, bool(getattr(ctx, "dry_run", False)))
    except OSError as exc:
        _note(f"{key}: could not write {path} ({exc}); nothing seeded.")
        return []

    if action == "kept" and not added:
        return [FileAction(path=str(path), action="kept")]
    manifest = getattr(ctx, "manifest", None)
    if manifest is not None and not getattr(ctx, "dry_run", False):
        try:
            manifest.track(key, str(path))
        except Exception:  # manifest tracking must never break an install
            pass
    return [FileAction(path=str(path), action=action)]
