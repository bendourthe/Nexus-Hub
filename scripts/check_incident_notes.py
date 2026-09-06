#!/usr/bin/env python3
"""Assert that every incident note in docs/incidents/ is publishable.

An incident note is closed by a change, not by an explanation. This guard makes
that rule mechanical instead of aspirational: it fails when a note is missing
the Public-Safe Shape section, missing the Durable fix section, or carrying a
Durable fix section with no link in it. A note whose "fix" is a paragraph rather
than a pointer to a concrete change is exactly the entry that turns an incident
archive into a graveyard, so it fails here rather than being merged.

Repo-internal guard, standard library only, no outbound call. It is NOT a
distributed artifact and therefore needs no installer copy step; it belongs in
DEV_ONLY_SCRIPTS alongside the other repo-only guards.

Usage:
    python scripts/check_incident_notes.py [--incidents-dir docs/incidents]

Exit codes:
    0  every note passes (or the directory does not exist yet)
    1  at least one note failed
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

# Files in docs/incidents/ that are not incident notes. Everything else must
# follow the <slug>-YYYYMMDD.md convention and carry the required sections.
NON_NOTE_FILENAMES = {"README.md", "TEMPLATE.md", "shapes.md"}

NOTE_NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*-\d{8}\.md$")

REQUIRED_SECTIONS = ("## Public-Safe Shape", "## Durable fix")

# A Markdown inline link: [text](target). Enough to distinguish "named and
# linked" from a prose paragraph; deliberately not a link *resolver*, because
# a note may legitimately link a commit or an anchor this script cannot open.
LINK_RE = re.compile(r"\[[^\]]+\]\([^)]+\)")


def section_body(text: str, heading: str) -> str | None:
    """Return the body under `heading`, or None when the heading is absent."""
    lines = text.splitlines()
    start = None
    for i, line in enumerate(lines):
        if line.strip() == heading:
            start = i + 1
            break
    if start is None:
        return None
    body: list[str] = []
    for line in lines[start:]:
        if line.startswith("## "):
            break
        body.append(line)
    return "\n".join(body)


def check_note(path: Path) -> list[str]:
    """Return a list of failure messages for one note (empty when it passes)."""
    failures: list[str] = []

    if not NOTE_NAME_RE.match(path.name):
        failures.append(
            f"filename does not follow the <slug>-YYYYMMDD.md convention "
            f"(got {path.name!r}); rename it, or add it to NON_NOTE_FILENAMES "
            f"if it is not an incident note"
        )

    text = path.read_text(encoding="utf-8")

    for heading in REQUIRED_SECTIONS:
        if section_body(text, heading) is None:
            failures.append(f"missing required section {heading!r}")

    fix_body = section_body(text, "## Durable fix")
    if fix_body is not None and not LINK_RE.search(fix_body):
        failures.append(
            "the 'Durable fix' section contains no link. An incident is closed "
            "by a change, not by an explanation: name AND link the concrete "
            "change (a commit, test, CI gate, hook, validator, or skill edit). "
            "If no fix exists yet, link the tracked gap-log item instead."
        )

    return failures


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--incidents-dir",
        default="docs/incidents",
        help="directory holding incident notes (default: docs/incidents)",
    )
    args = parser.parse_args()

    incidents_dir = Path(args.incidents_dir)
    if not incidents_dir.is_dir():
        print(f"  no {incidents_dir} directory -- nothing to check")
        return 0

    notes = sorted(
        p
        for p in incidents_dir.glob("*.md")
        if p.name not in NON_NOTE_FILENAMES
    )

    if not notes:
        print(f"  {incidents_dir} holds no incident notes yet")
        return 0

    failed = False
    for note in notes:
        failures = check_note(note)
        if failures:
            failed = True
            print(f"FAIL {note}", file=sys.stderr)
            for failure in failures:
                print(f"  - {failure}", file=sys.stderr)
        else:
            print(f"  OK {note.name}")

    if failed:
        print(
            "\nIncident notes must carry a Public-Safe Shape section and a "
            "Durable fix section naming and linking a concrete change.",
            file=sys.stderr,
        )
        return 1

    print(f"  {len(notes)} incident note(s) OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
