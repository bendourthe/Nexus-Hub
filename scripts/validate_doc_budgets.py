#!/usr/bin/env python3
"""Assert that every budgeted standing doc stays under its word ceiling.

Always-loaded instruction docs (AGENTS.md, CLAUDE.md, the lockstep base-*.md
templates) cost tokens in every session, on every platform, forever. Left
ungoverned they only grow, because each individual addition is locally
justified and nobody is measuring the total. This guard makes the budget
mechanical: a doc that outgrows its ceiling fails here instead of quietly
taxing every future session.

The policy is a RATCHET. A ceiling may be lowered freely as content is
relocated or condensed; raising one is an explicit, justified decision made in
a pull request, never the default response to a failure. The failure message
says so, so the cheap fix stays the obvious one.

Repo-internal guard, standard library only, no outbound call. It is NOT a
distributed artifact and therefore needs no installer copy step; it belongs in
DEV_ONLY_SCRIPTS alongside the other repo-only guards.

Usage:
    python scripts/validate_doc_budgets.py [--root .] [--manifest PATH] [--list]

Exit codes:
    0  every budgeted doc is under its ceiling (or --list was requested)
    1  at least one BAD, DUPE, MISS, or OVER failure
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path, PurePosixPath

DEFAULT_MANIFEST = "docs/policy/doc-budgets.json"

# Ceilings are seeded with headroom so a normal edit does not trip the gate.
# Below this the doc is effectively frozen, which is a different (and usually
# unintended) policy than "budgeted", so --list flags it for a human.
LOW_HEADROOM_RATIO = 0.05


def normalize(raw: str) -> str:
    """Normalize a manifest key to a comparable repo-relative POSIX path.

    Accepts Windows separators and a leading './' so a manifest edited on
    either platform compares equal. Two keys that normalize to the same path
    are a DUPE failure rather than a silent last-one-wins overwrite.
    """
    posix = PurePosixPath(raw.replace("\\", "/"))
    parts = [p for p in posix.parts if p not in (".", "")]
    return str(PurePosixPath(*parts)) if parts else ""


def count_words(path: Path) -> int:
    """Count whitespace-delimited words in a file.

    Deliberately counts fenced code blocks and tables too. They are real tokens
    the model loads, and exempting them would make the cheapest way to pass the
    gate "move the prose into a code fence".
    """
    text = path.read_text(encoding="utf-8")
    return len(text.split())


def load_manifest(manifest_path: Path) -> tuple[dict[str, int], list[str]]:
    """Return (entries, failures). Entries map normalized path -> ceiling."""
    if not manifest_path.is_file():
        return {}, [f"BAD  {manifest_path}: manifest not found"]

    duplicates: list[str] = []

    def reject_duplicate_keys(pairs: list[tuple[str, object]]) -> dict[str, object]:
        seen: set[str] = set()
        for key, _ in pairs:
            if key in seen:
                duplicates.append(key)
            seen.add(key)
        return dict(pairs)

    try:
        raw = json.loads(
            manifest_path.read_text(encoding="utf-8"),
            object_pairs_hook=reject_duplicate_keys,
        )
    except json.JSONDecodeError as exc:
        return {}, [f"BAD  {manifest_path}: not valid JSON ({exc})"]

    if not isinstance(raw, dict):
        return {}, [
            f"BAD  {manifest_path}: expected a JSON object mapping paths to "
            f"integer ceilings, got {type(raw).__name__}"
        ]

    failures: list[str] = [
        f"DUPE {key}: listed more than once in the manifest" for key in duplicates
    ]

    entries: dict[str, int] = {}
    origins: dict[str, str] = {}

    for key, ceiling in raw.items():
        if key.startswith("_"):
            # Underscore-prefixed keys are manifest comments, not budgets.
            continue

        path_key = normalize(key)
        if not path_key:
            failures.append(f"BAD  {key!r}: not a usable repo-relative path")
            continue

        if path_key in origins:
            failures.append(
                f"DUPE {path_key}: named by both {origins[path_key]!r} and "
                f"{key!r}; these normalize to the same file"
            )
            continue

        # bool is an int subclass; a `true` ceiling is a mistake, not a budget.
        if isinstance(ceiling, bool) or not isinstance(ceiling, int) or ceiling <= 0:
            failures.append(
                f"BAD  {path_key}: ceiling must be a positive integer, "
                f"got {ceiling!r}"
            )
            continue

        entries[path_key] = ceiling
        origins[path_key] = key

    if not entries and not failures:
        failures.append(f"BAD  {manifest_path}: manifest lists no budgeted docs")

    return entries, failures


def print_table(root: Path, entries: dict[str, int]) -> None:
    """Print the usage table (path, words, ceiling, headroom)."""
    rows: list[tuple[str, str, str, str]] = []
    for path_key in sorted(entries):
        ceiling = entries[path_key]
        target = root / path_key
        if not target.is_file():
            rows.append((path_key, "-", str(ceiling), "MISSING"))
            continue
        words = count_words(target)
        headroom = ceiling - words
        ratio = headroom / ceiling
        flag = "  <- tight" if ratio < LOW_HEADROOM_RATIO else ""
        rows.append(
            (path_key, str(words), str(ceiling), f"{headroom:+d} ({ratio:.0%}){flag}")
        )

    width = max(len(row[0]) for row in rows)
    print(f"{'PATH'.ljust(width)}  {'WORDS':>7}  {'CEILING':>7}  HEADROOM")
    for path_key, words, ceiling, headroom in rows:
        print(f"{path_key.ljust(width)}  {words:>7}  {ceiling:>7}  {headroom}")


def check(root: Path, entries: dict[str, int]) -> list[str]:
    """Return every MISS/OVER failure, collected so one does not mask another."""
    failures: list[str] = []
    for path_key in sorted(entries):
        ceiling = entries[path_key]
        target = root / path_key
        if not target.is_file():
            failures.append(
                f"MISS {path_key}: budgeted file not found. If it moved or was "
                f"deleted, update the manifest in the same change."
            )
            continue
        words = count_words(target)
        if words > ceiling:
            failures.append(
                f"OVER {path_key}: {words} words exceeds the {ceiling} ceiling "
                f"by {words - ceiling}. Relocate or condense; raising a ceiling "
                f"requires justification in the PR."
            )
    return failures


def report(manifest_path: Path, failures: list[str], epilogue: str = "") -> int:
    """Print every collected failure before the single exit."""
    print(f"FAIL {manifest_path}", file=sys.stderr)
    for failure in failures:
        print(f"  - {failure}", file=sys.stderr)
    if epilogue:
        print(f"\n{epilogue}", file=sys.stderr)
    return 1


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root",
        default=".",
        help="repo root that manifest paths are relative to (default: .)",
    )
    parser.add_argument(
        "--manifest",
        default=None,
        help=f"budget manifest (default: <root>/{DEFAULT_MANIFEST})",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="print the usage table (path, words, ceiling, headroom) and exit 0",
    )
    args = parser.parse_args()

    root = Path(args.root)
    manifest_path = Path(args.manifest) if args.manifest else root / DEFAULT_MANIFEST

    entries, failures = load_manifest(manifest_path)
    if failures:
        return report(manifest_path, failures)

    if args.list:
        print_table(root, entries)
        return 0

    failures = check(root, entries)
    if failures:
        return report(
            manifest_path,
            failures,
            "Budgeted docs are always-loaded instruction text: every word is "
            "paid for in every session. Ceilings ratchet DOWN over releases.",
        )

    print(f"  {len(entries)} budgeted doc(s) within ceiling")
    return 0


if __name__ == "__main__":
    sys.exit(main())
