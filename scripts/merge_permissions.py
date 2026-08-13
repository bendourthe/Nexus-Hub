#!/usr/bin/env python3
"""Merge a Nexus-Hub permission template into a platform settings file without jq.

``scripts/installer.sh`` merged permission templates with ``jq``. macOS does not ship
``jq``, so on a stock Mac the installer printed a warning and installed *no*
auto-approve baseline at all, while ``scripts/installer.ps1`` used native JSON handling
and had no such dependency. That asymmetry is what this helper removes.

This is now the ONLY merge implementation: both installers call it and neither retains
a native path. The ``jq`` fast path the v3.17.0 plan originally asked to keep was
dropped, and ``installer.ps1``'s native JSON merge was ported here in the same phase,
for one reason -- removal propagation lives here. A second implementation would mean a
host with ``jq`` (or a Windows host on the native path) silently keeps retired
mutation-capable entries while another host has them removed, which is the exact
divergence this phase exists to eliminate.

Python is already a documented dependency of this repository and both installers
already check for it, so this adds no new dependency. Standard library only.

Two behaviors matter for parity with the historical ``jq`` path:

* **Union semantics.** ``jq``'s ``unique`` both de-duplicates *and sorts*, so the
  merged array is sorted. This helper sorts identically, which is what lets a test
  assert the two paths produce byte-identical output for the same input.
* **Metadata stripping.** Template files carry documentation keys prefixed with ``_``
  (``_description``, and since v3.17.0 the ``_hardening`` audit block). Those describe
  the template and must never land in a user's live settings file. The ``jq`` creation
  path avoided this by selecting only ``.permissions``; the no-``jq`` path used a plain
  ``cp`` and did copy them, which this helper fixes.

Usage::

    python scripts/merge_permissions.py --template TPL --settings OUT --key permissions.allow
    python scripts/merge_permissions.py --template TPL --settings OUT --set-true some.key

Exit codes: ``0`` merged (or already current), ``1`` merge failed, ``2`` usage error.

Output protocol -- one machine-readable line per fact, all on **stdout**::

    added: <count>
    removed: <entry>        # zero or more
    set: <dotted.key>       # --set-true mode only, omitted when already true

Both installers parse stdout and nothing else. Removals were originally reported on
stderr, which bash reads happily but Windows PowerShell 5.1 does not: redirecting a
native command's stderr there wraps every line in an ``ErrorRecord`` and sets ``$?``
to ``$false`` even on a clean exit, turning a good install into a visible error. One
stdout protocol is what lets both installers share one calling convention.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


def _strip_metadata(node: Any) -> Any:
    """Recursively drop ``_``-prefixed documentation keys from a template."""
    if isinstance(node, dict):
        return {
            key: _strip_metadata(value)
            for key, value in node.items()
            if not (isinstance(key, str) and key.startswith("_"))
        }
    if isinstance(node, list):
        return [_strip_metadata(item) for item in node]
    return node


def _get_path(doc: Any, dotted: str) -> Any:
    """Read a dotted key path, returning None when any segment is missing."""
    node = doc
    for segment in dotted.split("."):
        if not isinstance(node, dict) or segment not in node:
            return None
        node = node[segment]
    return node


def _set_path(doc: dict, dotted: str, value: Any) -> None:
    """Write a dotted key path, creating intermediate dicts as needed."""
    segments = dotted.split(".")
    node = doc
    for segment in segments[:-1]:
        existing = node.get(segment)
        if not isinstance(existing, dict):
            existing = {}
            node[segment] = existing
        node = existing
    node[segments[-1]] = value


def _dump(doc: Any) -> str:
    """Serialize matching jq's default output: 2-space indent, raw UTF-8, trailing newline."""
    return json.dumps(doc, indent=2, ensure_ascii=False) + "\n"


def _load_manifest(manifest_path: Path) -> dict[str, list[str]]:
    """Read the shipped-entry manifest, tolerating absence and corruption.

    A missing or unreadable manifest is not an error: it simply means no removal can
    be proven safe this run, so the merge degrades to pure-union behavior. Failing
    the install over a damaged bookkeeping file would be worse than skipping removals.
    """
    if not manifest_path.exists():
        return {}
    try:
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    if not isinstance(data, dict):
        return {}
    shipped = data.get("shipped")
    if not isinstance(shipped, dict):
        return {}
    return {k: v for k, v in shipped.items() if isinstance(v, list)}


def _write_manifest(manifest_path: Path, manifest: dict[str, list[str]]) -> None:
    """Record what this version shipped, so the NEXT upgrade can retire it safely."""
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "_description": (
            "Records the permission entries each Nexus-Hub version shipped, per platform. "
            "Used to retire an entry that Nexus-Hub previously shipped and no longer does, "
            "WITHOUT touching an entry the user added themselves. Deleting this file is "
            "safe: it only disables removal propagation until the next install."
        ),
        "shipped": {k: sorted(v) for k, v in manifest.items()},
    }
    tmp_path = manifest_path.with_suffix(manifest_path.suffix + ".tmp")
    tmp_path.write_text(_dump(payload), encoding="utf-8")
    tmp_path.replace(manifest_path)


def _backup(settings_path: Path) -> Path:
    """Copy *settings_path* aside under the installers' ``.bak.YYYYMMDD-HHMMSS`` convention."""
    from datetime import datetime

    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup_path = settings_path.with_name(settings_path.name + f".bak.{stamp}")
    backup_path.write_text(settings_path.read_text(encoding="utf-8"), encoding="utf-8")
    return backup_path


def _atomic_write(settings_path: Path, doc: Any) -> None:
    """Write *doc* via temp-file-plus-rename.

    A truncated settings.json breaks the user's agent entirely, and an interrupted
    installer is a realistic way to produce one.
    """
    settings_path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = settings_path.with_suffix(settings_path.suffix + ".tmp")
    tmp_path.write_text(_dump(doc), encoding="utf-8")
    tmp_path.replace(settings_path)


def set_true(settings_path: Path, key: str, backup: bool = True) -> bool:
    """Set the dotted boolean *key* to ``True``. Returns True when a write happened.

    Copilot is the one platform whose permission surface is a scalar rather than an
    array: a single ``github.copilot.chat.codeGeneration.useInstructionFiles`` key in
    VS Code's settings.json. It lives here rather than in either installer because the
    bash side previously did it with ``jq`` and skipped entirely without it, which made
    the Git-Bash path unreachable in practice (Git-Bash ships no ``jq``), while the
    PowerShell side did it natively. Same defect class as the array merge, same fix.

    Two deliberate asymmetries with ``merge()``:

    * *key* is a LITERAL key, not a dotted path. VS Code's settings.json is flat and
      its keys contain dots (``"github.copilot.chat.codeGeneration.useInstructionFiles"``
      is one key, not five levels), so traversing it as a path would write a nested
      object VS Code never reads -- and the setting would silently stay off.
    * No manifest and no removal propagation. Nexus-Hub sets this key; it has never
      shipped a *set* of them, so there is nothing a later version could safely retire.
    """
    if settings_path.exists():
        doc = json.loads(settings_path.read_text(encoding="utf-8"))
        if not isinstance(doc, dict):
            raise ValueError(f"{settings_path} does not contain a JSON object")
    else:
        doc = {}

    if doc.get(key) is True:
        return False

    if backup and settings_path.exists():
        _backup(settings_path)
    doc[key] = True
    _atomic_write(settings_path, doc)
    return True


def merge(
    template_path: Path,
    settings_path: Path,
    key: str,
    manifest_path: Path | None = None,
    platform: str | None = None,
    backup: bool = True,
) -> tuple[int, list[str]]:
    """Sync the template's array at *key* into *settings_path*.

    Returns ``(entries_added, entries_removed)``.

    Additions are a union, matching the historical ``jq`` behavior. Removals are
    strictly opt-in and provably safe: an entry is retired only when the manifest
    records that a previous Nexus-Hub install shipped it AND the current template no
    longer does. An entry the user added by hand is never in the manifest, so it can
    never be removed. Without a manifest, no removal happens at all.
    """
    template = _strip_metadata(json.loads(template_path.read_text(encoding="utf-8")))
    template_entries = _get_path(template, key) or []
    if not isinstance(template_entries, list):
        raise ValueError(f"template key {key!r} is not an array")

    if settings_path.exists():
        existing_doc = json.loads(settings_path.read_text(encoding="utf-8"))
        if not isinstance(existing_doc, dict):
            raise ValueError(f"{settings_path} does not contain a JSON object")
        existing_entries = _get_path(existing_doc, key) or []
        if not isinstance(existing_entries, list):
            raise ValueError(f"settings key {key!r} is not an array")
    else:
        # Creation path: emit only the template's own structure, metadata already
        # stripped above, so documentation keys never reach a live config.
        existing_doc = {}
        existing_entries = []

    existing_set = set(existing_entries)
    template_set = set(template_entries)

    manifest: dict[str, list[str]] = {}
    retired: set[str] = set()
    if manifest_path is not None and platform is not None:
        manifest = _load_manifest(manifest_path)
        previously_shipped = set(manifest.get(platform, []))
        # The whole safety argument in one line: retire only what WE shipped and have
        # since dropped, intersected with what is actually present.
        retired = (previously_shipped - template_set) & existing_set

    merged_set = (existing_set | template_set) - retired
    # jq's `unique` de-duplicates AND sorts; match that exactly for byte parity.
    merged_entries = sorted(merged_set)
    added = len(template_set - existing_set)
    removed = sorted(retired)

    manifest_stale = (
        manifest_path is not None
        and platform is not None
        and set(manifest.get(platform, [])) != template_set
    )

    if added == 0 and not removed and settings_path.exists() and not manifest_stale:
        return 0, []

    if backup and settings_path.exists() and (added or removed):
        _backup(settings_path)

    _set_path(existing_doc, key, merged_entries)
    _atomic_write(settings_path, existing_doc)

    if manifest_path is not None and platform is not None:
        manifest[platform] = sorted(template_set)
        _write_manifest(manifest_path, manifest)

    return added, removed


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Merge a permission template into a settings file without jq.",
    )
    parser.add_argument("--template", type=Path, default=None,
                        help="Nexus-Hub permission template to merge FROM. Required for "
                             "an array merge; unused by --set-true, which writes a key "
                             "rather than copying entries from a template.")
    parser.add_argument("--settings", required=True, type=Path,
                        help="Platform settings file to merge INTO (created if absent).")
    parser.add_argument("--key", default="permissions.allow",
                        help="Dotted path to the allowlist array. Default: permissions.allow "
                             "(Gemini uses tools.allowed).")
    parser.add_argument("--count-only", action="store_true",
                        help="Report how many entries WOULD be added; write nothing.")
    parser.add_argument("--manifest", type=Path, default=None,
                        help="Shipped-entry manifest enabling removal propagation. Without "
                             "it the merge is add-only, matching pre-v3.17.0 behavior.")
    parser.add_argument("--platform", default=None,
                        help="Platform key within the manifest (CLAUDE, GEMINI, ...). "
                             "Required alongside --manifest.")
    parser.add_argument("--set-true", metavar="KEY", default=None,
                        help="Set a single LITERAL boolean key to true instead of merging "
                             "an array (VS Code settings.json is flat, so its dotted keys "
                             "are literal). Used for Copilot's useInstructionFiles key.")
    parser.add_argument("--no-backup", action="store_true",
                        help="Skip the timestamped backup. Intended for tests only.")
    args = parser.parse_args(argv)

    if args.set_true:
        try:
            wrote = set_true(args.settings, args.set_true, backup=not args.no_backup)
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            return 1
        if wrote:
            print(f"set: {args.set_true}")
        return 0

    if bool(args.manifest) != bool(args.platform):
        print("ERROR: --manifest and --platform must be given together", file=sys.stderr)
        return 2

    if args.template is None:
        print("ERROR: --template is required unless --set-true is given", file=sys.stderr)
        return 2

    if not args.template.exists():
        print(f"ERROR: template not found: {args.template}", file=sys.stderr)
        return 2

    try:
        if args.count_only:
            template = _strip_metadata(json.loads(args.template.read_text(encoding="utf-8")))
            template_entries = set(_get_path(template, args.key) or [])
            if args.settings.exists():
                existing = set(
                    _get_path(json.loads(args.settings.read_text(encoding="utf-8")), args.key)
                    or []
                )
            else:
                existing = set()
            print(len(template_entries - existing))
            return 0
        added, removed = merge(
            args.template, args.settings, args.key,
            manifest_path=args.manifest, platform=args.platform,
            backup=not args.no_backup,
        )
        print(f"added: {added}")
        for entry in removed:
            print(f"removed: {entry}")
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
