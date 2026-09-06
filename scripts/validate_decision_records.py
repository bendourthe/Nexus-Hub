#!/usr/bin/env python3
"""Assert that every decision record is structurally findable and complete.

A decision record answers why a design won and what it beat. The second half is
what stops re-litigation, so `## Alternatives considered` is mandatory in every
lifecycle and this guard treats its absence as an error rather than a style
nit: a record without alternatives is an implementation note wearing a decision
record's filename.

The other rules exist to keep the tree greppable. Records live at exactly
lifecycle/class/file so `rejected/` can be scanned before proposing something
that was already declined, and a record filed at the wrong depth or under an
invented class is invisible to that scan while still looking filed.

Repo-internal guard, standard library only, no outbound call. It is NOT a
distributed artifact and therefore needs no installer copy step; it belongs in
DEV_ONLY_SCRIPTS alongside the other repo-only guards.

Usage:
    python scripts/validate_decision_records.py [--root .] [--decisions-dir docs/decisions]

Exit codes:
    0  every record passes (or the tree does not exist yet)
    1  at least one record failed
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

LIFECYCLES = ("proposed", "implemented", "rejected")
CLASSES = ("architecture", "policy", "process", "tooling")

# No `feature` class on purpose: feature intent lives in plans, not here.
FILENAME_RE = re.compile(r"^\d{4}-\d{2}-\d{2}-[a-z0-9-]+\.md$")
TITLE_RE = re.compile(r"^# Decision: \S.*$")
STATUS_RE = re.compile(r"^Status: (proposed|implemented|rejected) - \S.*$")

ALTERNATIVES = "## Alternatives considered"
CONSEQUENCES = "## Consequences"

# Headings that describe something that has not happened yet. Legal in a
# proposal, and legal frozen inside a rejected record, but in an implemented
# record they mean the proposal shipped and was never rewritten.
PROPOSAL_ERA_HEADINGS = ("## Proposal", "## Acceptance criteria")

REQUIRED_SECTIONS = {
    "proposed": ("## Problem", "## Proposal", ALTERNATIVES, "## Acceptance criteria", "## Risks"),
    "implemented": ("## Problem", "## Decision", ALTERNATIVES, CONSEQUENCES),
    "rejected": (ALTERNATIVES,),
}

# Places a decision record must not be written. A record here is invisible to
# anyone grepping the tree, so it fails loudly with a relocation hint rather
# than being silently skipped.
LEGACY_LOCATIONS = (
    "docs/rfc",
    "docs/adr",
    "docs/architecture-decisions",
    ".claude/memory/decisions.md",
)

NON_RECORD_FILENAMES = {"README.md"}


def headings(text: str) -> set[str]:
    """Return the exact `## ` heading lines in a record."""
    return {line.rstrip() for line in text.splitlines() if line.startswith("## ")}


def check_header(lines: list[str], lifecycle: str) -> list[str]:
    """Validate the fixed three-line header and its agreement with the folder."""
    failures: list[str] = []

    if len(lines) < 3:
        return ["file is shorter than the required 3-line header"]

    if not TITLE_RE.match(lines[0]):
        failures.append(
            f"line 1 must be '# Decision: <title>', got {lines[0]!r}"
        )
    if lines[1].strip():
        failures.append(f"line 2 must be blank, got {lines[1]!r}")
    if not STATUS_RE.match(lines[2]):
        failures.append(
            f"line 3 must be 'Status: <lifecycle> - <one line>', got {lines[2]!r}"
        )
    else:
        declared = lines[2].split()[1]
        if declared != lifecycle:
            failures.append(
                f"Status says {declared!r} but the file sits in {lifecycle!r}/. "
                f"A record moves by being rewritten and moved, so update both."
            )

    return failures


def check_record(path: Path, lifecycle: str) -> list[str]:
    """Return every failure for one record (empty when it passes)."""
    try:
        text = path.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError) as exc:
        # One unreadable file must not mask the rest of the tree.
        return [f"could not be read ({exc.__class__.__name__}: {exc})"]

    failures = check_header(text.splitlines(), lifecycle)
    present = headings(text)

    for required in REQUIRED_SECTIONS[lifecycle]:
        if required not in present:
            failures.append(
                f"missing required section {required!r} for a {lifecycle} record"
            )

    if lifecycle == "implemented":
        for heading in PROPOSAL_ERA_HEADINGS:
            if heading in present:
                failures.append(
                    f"{heading!r} describes work that has not happened yet and "
                    f"must not survive into an implemented record. Rewrite: "
                    f"'## Proposal' becomes '## Decision' in the present tense, "
                    f"'## Acceptance criteria' becomes '## Consequences'."
                )

    return failures


def check_legacy_locations(root: Path) -> list[str]:
    """Fail when decision records reappear outside the canonical tree."""
    failures: list[str] = []
    for legacy in LEGACY_LOCATIONS:
        target = root / legacy
        if target.is_dir() and any(target.glob("*.md")):
            failures.append(
                f"{legacy}/ holds Markdown files. Decision records live under "
                f"docs/decisions/<lifecycle>/<class>/; relocate them."
            )
        elif target.is_file() and target.suffix == ".md":
            body = target.read_text(encoding="utf-8", errors="replace")
            if "# Decision:" in body:
                failures.append(
                    f"{legacy} contains a decision record. Records live under "
                    f"docs/decisions/<lifecycle>/<class>/; relocate it and "
                    f"leave a pointer."
                )
    return failures


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root",
        default=".",
        help="repo root (default: .)",
    )
    parser.add_argument(
        "--decisions-dir",
        default=None,
        help="decision tree (default: <root>/docs/decisions)",
    )
    args = parser.parse_args()

    root = Path(args.root)
    decisions = Path(args.decisions_dir) if args.decisions_dir else root / "docs" / "decisions"

    failures: list[str] = check_legacy_locations(root)

    if not decisions.is_dir():
        if failures:
            print("FAIL decision records", file=sys.stderr)
            for failure in failures:
                print(f"  - {failure}", file=sys.stderr)
            return 1
        print(f"  no {decisions} tree -- nothing to check")
        return 0

    records = 0
    for path in sorted(decisions.rglob("*.md")):
        if path.name in NON_RECORD_FILENAMES and path.parent == decisions:
            continue

        rel = path.relative_to(decisions)
        parts = rel.parts

        if len(parts) != 3:
            failures.append(
                f"{rel.as_posix()}: expected exactly "
                f"<lifecycle>/<class>/<file>.md, found {len(parts)} path "
                f"segment(s)"
            )
            continue

        lifecycle, cls, filename = parts

        if lifecycle not in LIFECYCLES:
            failures.append(
                f"{rel.as_posix()}: unknown lifecycle {lifecycle!r}; "
                f"expected one of {', '.join(LIFECYCLES)}"
            )
            continue
        if cls not in CLASSES:
            failures.append(
                f"{rel.as_posix()}: unknown class {cls!r}; expected one of "
                f"{', '.join(CLASSES)} (there is deliberately no 'feature' "
                f"class: feature intent lives in plans)"
            )
            continue
        if not FILENAME_RE.match(filename):
            failures.append(
                f"{rel.as_posix()}: filename must match "
                f"YYYY-MM-DD-<kebab-slug>.md"
            )
            continue

        records += 1
        for failure in check_record(path, lifecycle):
            failures.append(f"{rel.as_posix()}: {failure}")

    if failures:
        print("FAIL decision records", file=sys.stderr)
        for failure in failures:
            print(f"  - {failure}", file=sys.stderr)
        print(
            "\nA decision recorded without what it beat invites re-litigation. "
            "Format and lifecycle rules: docs/decisions/README.md",
            file=sys.stderr,
        )
        return 1

    print(f"  {records} decision record(s) OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
