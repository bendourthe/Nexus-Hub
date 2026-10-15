#!/usr/bin/env python3
"""Fail when an unresolved merge conflict marker is committed to a tracked file.

A rename/modify merge that is committed without resolution leaves `<<<<<<<`,
`=======` and `>>>>>>>` lines in the file. Nothing else in the gate reads the
repository's own documentation, so this survives every rendered-output check:
six files carried markers for days, including the progress dashboard, while the
fast profile reported 13 of 13 green.

Only line-anchored conflict markers count. A skill that documents the markers,
or prose that mentions them inline, is not a conflict.

The marker run is seven characters ONLY in the common case. Git widens it when
the two sides disagree about the path as well as the content, so a rename that
is merged and committed unresolved writes `<<<<<<<< HEAD:old/path`. Anchoring
on exactly seven let eleven such conflicts sit in a release plan while this
check reported clean, which is the same blindness it was written to end.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

# A file whose SUBJECT is merge conflicts legitimately contains the markers.
ALLOWLIST = {
    "catalog/skills/workflow/conflict-analyzer/SKILL.md",
    # The committed Antigravity project-surface copy of the same skill.
    ".agents/skills/conflict-analyzer/SKILL.md",
    "scripts/check_merge_conflict_markers.py",
}

# Seven or more, because a rename conflict widens the run. The trailing group
# keeps a line of seven-plus nested blockquotes, or a rule of equals signs,
# from reading as a conflict: git always writes a label or nothing after it.
MARKER = re.compile(r"^(?:<{7,}|>{7,})(?: .*)?$")

TEXT_SUFFIXES = {
    ".md", ".py", ".js", ".json", ".yml", ".yaml", ".toml", ".sh", ".ps1",
    ".css", ".html", ".txt", ".cfg", ".ini",
}


def tracked_files(root: Path) -> list[Path]:
    """Tracked text files that contain a line starting with a marker run.

    `git grep` prefilters natively in about a second; reading all ~8,000
    tracked files through Python took 100-120 s on Windows and timed out the
    fast profile's 120 s bound. The prefilter is a superset of MARKER, so
    `conflicts_in` still makes the exact decision on each candidate.
    """
    result = subprocess.run(
        ["git", "-C", str(root), "grep", "-l", "-z", "-E", "^(<{7,}|>{7,})"],
        capture_output=True,
    )
    if result.returncode == 1:  # git grep: no line matched anywhere
        return []
    if result.returncode != 0:
        raise subprocess.CalledProcessError(result.returncode, result.args, result.stdout, result.stderr)
    return [
        Path(name)
        for name in result.stdout.decode("utf-8", "replace").split("\0")
        if name and Path(name).suffix.lower() in TEXT_SUFFIXES
    ]


def conflicts_in(path: Path) -> list[tuple[int, str]]:
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return []
    found = []
    for number, line in enumerate(text.splitlines(), start=1):
        # A bare row of equals signs is also a valid Markdown setext rule, so
        # only the start and end markers are scanned; either one alone proves
        # the conflict.
        if MARKER.match(line):
            found.append((number, line[:60]))
    return found


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("."))
    args = parser.parse_args(argv)
    root = args.root.resolve()

    findings: list[str] = []
    for relative in tracked_files(root):
        if relative.as_posix() in ALLOWLIST:
            continue
        for number, snippet in conflicts_in(root / relative):
            findings.append(f"{relative.as_posix()}:{number}: {snippet}")

    for finding in findings:
        print(f"merge conflict marker: {finding}")
    total = len(findings)
    print(
        f"check_merge_conflict_markers: {total} marker(s) in "
        f"{len({f.split(':')[0] for f in findings})} file(s)."
    )
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
