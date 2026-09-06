#!/usr/bin/env python3
"""Assert release notes teach every opt-in surface they ship.

Mechanical companion to the capability usage gate (governance step 6 in
`catalog/commands/update.md`, added v3.16.2 Phase 2). For each opt-in surface a
release introduces or materially changes, the notes must carry five elements:

    1. Activation        the exact opt-in mechanism, copy-pasteable
    2. Validation        a runnable command that reads back whether it took effect
    3. Rollback          the exact disable / uninstall / revert path
    4. Authority         what activation does NOT grant
    5. Docs              a canonical documentation link

Element 4 is the one most often skipped and the only one that fails silently, by
letting a user over-trust a surface they enabled. The other four fail loudly the
first time someone tries to use them.

ADVISORY BY DESIGN (for now). `/update release` surfaces this output and a
maintainer decides; it is promoted to a hard gate only after it has caught a
real omission. Pass --strict to make it exit non-zero, which is what a future
promotion flips on. This mirrors the deliberate advisory/blocking split already
documented for the model-prompting freshness check versus the platform
read-contract check.

Detection is marker-based, not prose-inferring. A checker that guessed at
free-text would produce confident false passes, which is worse than no checker:
the gate exists to stop a surface shipping untaught, and a false CLEAR is
exactly that failure wearing a green tick. Each surface therefore declares its
five elements with labelled lines:

    ### NEXUS_HUB_COPILOT_SKILLS
    - Activation: set `NEXUS_HUB_COPILOT_SKILLS=1` before running the installer
    - Validation: `ls .github/skills` lists one directory per bundled skill
    - Rollback: unset the variable and delete `.github/skills/`
    - Authority: does NOT grant Copilot any permission it lacked; the files are
      commit-visible, so treat them as published
    - Docs: https://example.invalid/docs/v3.16.2/copilot-skills

Repo-internal guard, standard library only, no outbound call. NOT a distributed
artifact, so it needs no installer copy step and belongs in DEV_ONLY_SCRIPTS.

Usage:
    python scripts/check_release_capability_docs.py NOTES.md --surface NAME [--surface NAME ...]
    python scripts/check_release_capability_docs.py NOTES.md --expect-no-optional-capability-changes

Exit codes:
    0  every named surface documents all five elements (or advisory mode)
    1  at least one element missing AND --strict was passed
    2  usage error, or the notes file could not be read
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

# Element label -> the accepted synonyms a release author might reasonably use.
# Kept small on purpose: a wide synonym list re-introduces the guessing this
# checker exists to avoid.
ELEMENTS: dict[str, tuple[str, ...]] = {
    "Activation": ("activation", "activate", "opt-in", "enable"),
    "Validation": ("validation", "validate", "verify", "readback"),
    "Rollback": ("rollback", "disable", "uninstall", "revert", "turn off"),
    "Authority": (
        "authority",
        "boundary",
        "authority boundary",
        "privacy boundary",
        "does not grant",
    ),
    "Docs": ("docs", "documentation", "reference", "guide"),
}

# The explicit statement a release with no applicable surface must carry. The
# declaration is REQUIRED rather than optional because "checked and none
# applied" and "never checked" are indistinguishable from silence.
NO_CHANGE_PATTERNS = (
    r"no\s+opt-in\s+(capability|surface)",
    r"changes?\s+no\s+opt-in",
    r"no\s+applicable\s+opt-in",
    r"no\s+optional\s+capability\s+changes?",
)

# Two accepted marker forms, both EXPLICIT. A labelled line ("- Activation: ...")
# and a Markdown table row ("| **Activation** | ... |"). The table form was added
# after this checker failed on the very release notes that introduced it: a table
# is a perfectly reasonable way to present five parallel elements, and rejecting
# it would have pushed the author toward the looser prose the checker cannot
# verify. Both forms are markers, so neither reintroduces prose inference.
LABEL_RE = re.compile(r"^\s*[-*]?\s*\**\s*([A-Za-z][A-Za-z /-]*?)\**\s*:", re.MULTILINE)
TABLE_LABEL_RE = re.compile(r"^\s*\|\s*\**\s*([A-Za-z][A-Za-z /-]*?)\s*\**\s*\|", re.MULTILINE)


def surface_block(text: str, surface: str) -> str | None:
    """Return the text belonging to `surface`.

    The block runs from the first line naming the surface to the next heading at
    the same-or-higher level, or to the next surface mention, whichever is first.
    Returns None when the surface is never mentioned at all.
    """
    lines = text.splitlines()
    start = None
    for i, line in enumerate(lines):
        if surface in line:
            start = i
            break
    if start is None:
        return None

    # Determine the heading level of the line that introduces the surface, so
    # the block ends at the next heading of that level or shallower.
    heading = re.match(r"^(#{1,6})\s", lines[start])
    level = len(heading.group(1)) if heading else None

    body = [lines[start]]
    for line in lines[start + 1 :]:
        h = re.match(r"^(#{1,6})\s", line)
        if h and (level is None or len(h.group(1)) <= level):
            break
        body.append(line)
    return "\n".join(body)


def missing_elements(block: str) -> list[str]:
    """Return the required element names absent from `block`."""
    labels = {m.group(1).strip().lower() for m in LABEL_RE.finditer(block)}
    labels |= {m.group(1).strip().lower() for m in TABLE_LABEL_RE.finditer(block)}
    missing = []
    for element, synonyms in ELEMENTS.items():
        if not any(label in synonyms for label in labels):
            missing.append(element)
    return missing


def check_no_change_declaration(text: str) -> bool:
    lowered = text.lower()
    return any(re.search(p, lowered) for p in NO_CHANGE_PATTERNS)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("notes", help="path to the release-notes file")
    parser.add_argument(
        "--surface",
        action="append",
        default=[],
        metavar="NAME",
        help="an opt-in surface this release introduces or materially changes; repeatable",
    )
    parser.add_argument(
        "--expect-no-optional-capability-changes",
        action="store_true",
        help="assert the notes carry an explicit no-change declaration instead",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="exit non-zero on a missing element (default is advisory, exit 0)",
    )
    args = parser.parse_args()

    if args.surface and args.expect_no_optional_capability_changes:
        print(
            "error: --surface and --expect-no-optional-capability-changes are "
            "mutually exclusive",
            file=sys.stderr,
        )
        return 2
    if not args.surface and not args.expect_no_optional_capability_changes:
        print(
            "error: name at least one --surface, or pass "
            "--expect-no-optional-capability-changes for a release with none",
            file=sys.stderr,
        )
        return 2

    notes_path = Path(args.notes)
    try:
        text = notes_path.read_text(encoding="utf-8")
    except OSError as exc:
        print(f"error: cannot read {notes_path}: {exc}", file=sys.stderr)
        return 2

    failed = False

    if args.expect_no_optional_capability_changes:
        if check_no_change_declaration(text):
            print(f"  OK {notes_path}: explicit no-change declaration present")
            return 0
        print(
            f"FAIL {notes_path}: no explicit no-change declaration found.\n"
            "  A release with no opt-in surface change must SAY so. An implicit\n"
            "  pass cannot be told apart from never having checked.",
            file=sys.stderr,
        )
        failed = True
    else:
        for surface in args.surface:
            block = surface_block(text, surface)
            if block is None:
                print(
                    f"FAIL {surface}: never mentioned in {notes_path}",
                    file=sys.stderr,
                )
                failed = True
                continue
            missing = missing_elements(block)
            if missing:
                print(f"FAIL {surface}: missing {', '.join(missing)}", file=sys.stderr)
                if "Authority" in missing:
                    print(
                        "       (Authority is the element that fails SILENTLY -- "
                        "state what activation does NOT grant)",
                        file=sys.stderr,
                    )
                failed = True
            else:
                print(f"  OK {surface}: all five elements present")

    if failed:
        if args.strict:
            return 1
        print(
            "\nadvisory: not failing the run. Pass --strict to gate on this.",
            file=sys.stderr,
        )
        return 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
