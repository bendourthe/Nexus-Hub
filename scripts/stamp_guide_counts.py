#!/usr/bin/env python3
"""Stamp catalog-derived counts into the guide so no number on the page can drift.

Repo-internal maintainer tool (v4.4.2). It is listed in ``DEV_ONLY_SCRIPTS`` in
``catalog/hooks/tests/test_installer_smoke.py`` and is deliberately NOT copied by
either installer: an end-user ``~/.nexus-hub/scripts/`` has no ``data/`` or
``catalog/`` source tree to count.

Markers in ``guides/website/nexus-hub-guide.html`` look like::

    <span data-count="skills">329</span>

Recognised sources:

- ``skills``     - entries in ``data/skills.json``
- ``hooks``      - distinct hook scripts registered in ``catalog/hooks/settings.json``
- ``pretooluse`` - distinct hook scripts registered on the ``PreToolUse`` event
- ``commands``   - ``catalog/commands/*.md`` minus permanent aliases (frontmatter
  ``description`` containing the word ``alias``)

Usage::

    python scripts/stamp_guide_counts.py            # rewrite markers in place
    python scripts/stamp_guide_counts.py --check    # exit 1 on any stale marker
    python scripts/stamp_guide_counts.py --guide PATH [--root PATH]

Exit codes: 0 clean, 1 stale marker(s) under ``--check``, 2 a source or the guide
could not be read (never writes a guide with a missing number).
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

MARKER = re.compile(
    r'(<span\b[^>]*\bdata-count="(?P<name>skills|hooks|pretooluse|commands)"[^>]*>)'
    r"(?P<value>[^<]*)(</span>)"
)
SCRIPT_RE = re.compile(r"([A-Za-z0-9_.-]+)\.(sh|py|ps1)\b")
ALIAS_RE = re.compile(r"^description:.*\balias\b", re.IGNORECASE | re.MULTILINE)


class SourceError(RuntimeError):
    """A catalog source is missing or malformed."""


def _hook_scripts(settings: dict, event: str | None = None) -> set[str]:
    hooks = settings.get("hooks")
    if not isinstance(hooks, dict):
        raise SourceError("catalog/hooks/settings.json has no 'hooks' object")
    names: set[str] = set()
    for ev, entries in hooks.items():
        if event is not None and ev != event:
            continue
        for entry in entries or []:
            for hook in entry.get("hooks", []) or []:
                match = SCRIPT_RE.search(str(hook.get("command", "")))
                if match:
                    names.add(match.group(1))
    return names


def compute_counts(root: Path) -> dict[str, int]:
    """Return every count the guide may reference, read fresh from the catalog."""
    try:
        skills = json.loads((root / "data" / "skills.json").read_text(encoding="utf-8"))["skills"]
        settings = json.loads((root / "catalog" / "hooks" / "settings.json").read_text(encoding="utf-8"))
    except (OSError, ValueError, KeyError, TypeError) as exc:
        raise SourceError(f"cannot read a catalog source: {exc}") from exc
    if not isinstance(skills, list):
        raise SourceError("data/skills.json 'skills' is not a list")
    commands_dir = root / "catalog" / "commands"
    command_files = sorted(commands_dir.glob("*.md"))
    if not command_files:
        raise SourceError(f"no command files under {commands_dir}")
    aliases = [p for p in command_files if ALIAS_RE.search(p.read_text(encoding="utf-8")[:2000])]
    return {
        "skills": len(skills),
        "hooks": len(_hook_scripts(settings)),
        "pretooluse": len(_hook_scripts(settings, "PreToolUse")),
        "commands": len(command_files) - len(aliases),
    }


def stamp(text: str, counts: dict[str, int]) -> tuple[str, list[tuple[str, str, int]]]:
    """Rewrite every marker; return the new text and a list of (name, old, new) changes."""
    changes: list[tuple[str, str, int]] = []

    def repl(match: re.Match) -> str:
        name = match.group("name")
        new = counts[name]
        old = match.group("value").strip()
        if old != str(new):
            changes.append((name, old, new))
        return f"{match.group(1)}{new}{match.group(4)}"

    return MARKER.sub(repl, text), changes


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--check", action="store_true", help="report stale markers and exit 1; write nothing")
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--guide", type=Path, default=None,
                        help="guide file (default: <root>/guides/website/nexus-hub-guide.html)")
    args = parser.parse_args(argv)
    guide = args.guide or (args.root / "guides" / "website" / "nexus-hub-guide.html")

    try:
        counts = compute_counts(args.root)
        text = guide.read_text(encoding="utf-8")
    except (SourceError, OSError) as exc:
        print(f"stamp_guide_counts: ERROR: {exc}", file=sys.stderr)
        return 2

    new_text, changes = stamp(text, counts)
    markers = len(MARKER.findall(text))
    summary = ", ".join(f"{k}={v}" for k, v in counts.items())
    if args.check:
        if changes:
            for name, old, new in changes:
                print(f"stamp_guide_counts: STALE data-count=\"{name}\": page says {old!r}, catalog says {new}")
            return 1
        print(f"stamp_guide_counts: OK -- {markers} marker(s) match the catalog ({summary})")
        return 0
    if changes:
        guide.write_text(new_text, encoding="utf-8", newline="\n")
        for name, old, new in changes:
            print(f"stamp_guide_counts: stamped data-count=\"{name}\": {old!r} -> {new}")
    print(f"stamp_guide_counts: {markers} marker(s); {len(changes)} rewritten ({summary})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
