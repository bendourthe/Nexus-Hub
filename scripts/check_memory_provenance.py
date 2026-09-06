#!/usr/bin/env python3
"""Fail the build when memory templates drop the provenance contract.

Repo-internal guard (no installer copy, no .ps1 sibling). Checks:

- catalog/memory/record.md teaches source, tier, derived_from, supersedes,
  an append-only changelog, and the legacy-import migration token
- catalog/memory/decisions.md requires a Source field and a Changelog, and
  tells authors to supersede instead of delete
- optional --fixture FILE.md fixtures that must parse as valid or invalid
  per --expect fail|pass

Usage:

    python scripts/check_memory_provenance.py
    python scripts/check_memory_provenance.py --root DIR
    python scripts/check_memory_provenance.py --fixture FILE --expect fail

Exit codes:
    0 - templates (and any fixtures) satisfy the contract
    1 - one or more violations
    2 - usage / IO error
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

RECORD_NEEDLES = (
    "source:",
    "tier:",
    "derived_from:",
    "supersedes:",
    "## Changelog",
    "legacy-import",
)

DECISION_NEEDLES = (
    "**Source**",
    "## Changelog",
    "supersede",
)


def _missing(text: str, needles: tuple[str, ...]) -> list[str]:
    lowered = text.lower()
    return [item for item in needles if item.lower() not in lowered]


def check_templates(root: Path) -> list[str]:
    """Return human-readable violations for the catalog memory templates."""
    errors: list[str] = []
    record = root / "catalog" / "memory" / "record.md"
    decisions = root / "catalog" / "memory" / "decisions.md"
    if not record.is_file():
        errors.append(f"missing {record.as_posix()}")
    else:
        text = record.read_text(encoding="utf-8")
        for item in _missing(text, RECORD_NEEDLES):
            errors.append(f"{record.as_posix()}: missing {item!r}")
    if not decisions.is_file():
        errors.append(f"missing {decisions.as_posix()}")
    else:
        text = decisions.read_text(encoding="utf-8")
        for item in _missing(text, DECISION_NEEDLES):
            errors.append(f"{decisions.as_posix()}: missing {item!r}")
    return errors


def check_fixture(path: Path, expect: str) -> list[str]:
    """Validate one markdown fixture against the envelope parser."""
    src = Path(__file__).resolve().parents[1] / "extensions" / "nexus-memory" / "src"
    if str(src) not in sys.path:
        sys.path.insert(0, str(src))
    from nexus_memory.record import MissingSourceError, parse_record

    text = path.read_text(encoding="utf-8")
    try:
        parsed = parse_record(text, strict=True)
        ok = bool(parsed.source.strip())
        err = "" if ok else "empty source"
    except (MissingSourceError, ValueError) as exc:
        ok = False
        err = str(exc)
    if expect == "pass" and not ok:
        return [f"{path.as_posix()}: expected a valid record ({err})"]
    if expect == "fail" and ok:
        return [f"{path.as_posix()}: expected rejection, parsed source={parsed.source!r}"]
    return []


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--root", type=Path, default=None)
    parser.add_argument("--fixture", type=Path, default=None)
    parser.add_argument("--expect", choices=("pass", "fail"), default="pass")
    args = parser.parse_args(argv)
    root = (args.root or Path(__file__).resolve().parents[1]).resolve()
    try:
        errors = check_templates(root)
        if args.fixture is not None:
            errors.extend(check_fixture(args.fixture, args.expect))
    except OSError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    if errors:
        print(f"FAIL: {len(errors)} memory-provenance violation(s)", file=sys.stderr)
        for item in errors:
            print(f"  {item}", file=sys.stderr)
        return 1
    print(f"OK: memory provenance contract holds under {root / 'catalog' / 'memory'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
