#!/usr/bin/env python3
"""Enumerate the repository's plan queue deterministically.

Maintainer tooling for the plan-queue continuity workflow. Walks every plan
under the release documentation tree and reports, per plan, the inputs a
staleness or ordering decision needs: version, slug, status, open and completed
task counts, and the repository paths its task lines name.

Two failure modes this exists to prevent, both previously observed:

- A directory listing is alphabetical, which orders ``v3.10`` before ``v3.5``.
  Versions are parsed into integers and sorted on those.
- Plans routinely live several minors ahead of the in-flight version, so a scan
  scoped to the current minor cannot see them. The whole tree is scanned.

One finding this exists to surface: an open task count does NOT identify the
queue. Shipped and abandoned plans retain unchecked task lines, several of them
larger than any genuinely queued plan. The declared status is reported
alongside the counts so a caller never treats "has open tasks" as membership.

Exit codes: 0 clean scan, 1 at least one plan could not be parsed (it is still
listed, with the reason), 2 usage or environment error.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections.abc import Iterable, Sequence
from dataclasses import dataclass, field
from pathlib import Path

# A strict task line. The trailing space matters: without it, an exit-checklist
# item beginning "The ..." matches "T" and inflates every count.
TASK_LINE = re.compile(r"^- \[(?P<mark>[ xX])\] (?P<id>T\d{3}) ")

# Repository paths named inside a task line. Two conventions are in use across
# the tree and BOTH must be read: backtick-quoted (`docs/releases/.../x.md`) and
# bare trailing paths. Matching only the quoted form returned zero touched paths
# for three of five live plans, which would report a false "no impact" for every
# pair involving them.
TOUCHED_PATH = re.compile(
    r"`([A-Za-z0-9_][A-Za-z0-9_./-]*(?:\.[A-Za-z0-9]{1,6}|/))`"
    r"|(?<![`\w/])([A-Za-z0-9_][A-Za-z0-9_.-]*(?:/[A-Za-z0-9_.-]+)+(?:\.[A-Za-z0-9]{1,6}|/))"
)

STATUS_LINE = re.compile(r"^\*\*Status\*\*:\s*(?P<status>.+?)\s*$", re.MULTILINE)
VERSION_DIR = re.compile(r"^v(?P<major>\d+)\.(?P<minor>\d+)$")
PLAN_VERSION = re.compile(
    r"^v(?P<major>\d+)\.(?P<minor>\d+)\.(?P<patch>\d+)-(?P<slug>.+)$"
)

UNKNOWN_STATUS = "unknown (no parseable Status line)"


@dataclass
class Plan:
    """One plan file and the decision inputs read from it."""

    path: str
    major: int
    minor: int
    patch: int | None
    slug: str
    status: str
    open_tasks: int
    done_tasks: int
    touched: list[str] = field(default_factory=list)
    error: str | None = None
    note: str | None = None

    @property
    def version(self) -> str:
        if self.patch is None:
            return f"v{self.major}.{self.minor}"
        return f"v{self.major}.{self.minor}.{self.patch}"

    @property
    def sort_key(self) -> tuple[int, int, int, str]:
        # Sort on parsed integers, never lexically. A patchless legacy plan
        # sorts before v<major>.<minor>.0 rather than being dropped.
        return (
            self.major,
            self.minor,
            -1 if self.patch is None else self.patch,
            self.slug,
        )

    def as_dict(self) -> dict[str, object]:
        return {
            "version": self.version,
            "slug": self.slug,
            "path": self.path,
            "status": self.status,
            "open_tasks": self.open_tasks,
            "done_tasks": self.done_tasks,
            "touched": self.touched,
            "error": self.error,
            "note": self.note,
        }


def _parse_version_dir(name: str) -> tuple[int, int] | None:
    match = VERSION_DIR.match(name)
    if match is None:
        return None
    return int(match.group("major")), int(match.group("minor"))


def _parse_plan_name(stem: str, fallback: tuple[int, int]) -> tuple[int | None, str]:
    """Return (patch, slug) for a plan filename, tolerating legacy names."""
    match = PLAN_VERSION.match(stem)
    if match is None:
        # Legacy plans predate the versioned filename convention. They are real
        # plans and must stay in the queue, so they take the directory version
        # with no patch rather than being reported as a parse failure.
        return None, stem
    if (int(match.group("major")), int(match.group("minor"))) != fallback:
        # A filename disagreeing with its directory is a real inconsistency, but
        # the directory is authoritative for placement.
        pass
    return int(match.group("patch")), match.group("slug")


def _read_plan(path: Path, root: Path, version: tuple[int, int]) -> Plan:
    rel = path.relative_to(root).as_posix()
    major, minor = version
    patch, slug = _parse_plan_name(path.stem, version)

    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        # Reported, never omitted: an unreadable plan is invisible in every
        # downstream ranking if it is silently dropped.
        return Plan(
            path=rel,
            major=major,
            minor=minor,
            patch=patch,
            slug=slug,
            status=UNKNOWN_STATUS,
            open_tasks=0,
            done_tasks=0,
            error=f"unreadable: {exc.__class__.__name__}",
        )

    open_tasks = 0
    done_tasks = 0
    touched: list[str] = []
    seen: set[str] = set()
    for line in text.splitlines():
        match = TASK_LINE.match(line)
        if match is None:
            continue
        if match.group("mark") == " ":
            open_tasks += 1
        else:
            done_tasks += 1
        for quoted, bare in TOUCHED_PATH.findall(line):
            candidate = quoted or bare
            if candidate and candidate not in seen:
                seen.add(candidate)
                touched.append(candidate)

    status_match = STATUS_LINE.search(text)
    status = status_match.group("status") if status_match else UNKNOWN_STATUS
    # A missing Status line is common on older plans and is NOT a parse failure.
    # Treating it as one would make every run exit 1 and the exit code useless.
    # It is reported as a note so a caller knows membership is undeclared.
    note = None if status_match else "no Status line; membership is undeclared"

    return Plan(
        path=rel,
        major=major,
        minor=minor,
        patch=patch,
        slug=slug,
        status=status,
        open_tasks=open_tasks,
        done_tasks=done_tasks,
        touched=touched,
        note=note,
    )


def enumerate_plans(root: Path) -> list[Plan]:
    """Scan the whole release tree and return plans in numeric version order."""
    releases = root / "docs" / "releases"
    if not releases.is_dir():
        return []

    plans: list[Plan] = []
    for major_dir in sorted(releases.iterdir()):
        if not major_dir.is_dir():
            continue
        for minor_dir in sorted(major_dir.iterdir()):
            if not minor_dir.is_dir():
                continue
            version = _parse_version_dir(minor_dir.name)
            if version is None:
                continue
            plans_dir = minor_dir / "plans"
            if not plans_dir.is_dir():
                continue
            for plan_path in sorted(plans_dir.glob("*.md")):
                plans.append(_read_plan(plan_path, root, version))

    plans.sort(key=lambda p: p.sort_key)
    return plans


def render_table(plans: Sequence[Plan]) -> str:
    if not plans:
        return "No plans found."
    width = max(len(p.version) for p in plans)
    lines = [f"{'VERSION'.ljust(width)}  OPEN  DONE  SLUG"]
    for plan in plans:
        flag = "  ERROR" if plan.error else ("  ?" if plan.note else "")
        lines.append(
            f"{plan.version.ljust(width)}  {plan.open_tasks:>4}  {plan.done_tasks:>4}  {plan.slug}{flag}"
        )
    errored = [p for p in plans if p.error]
    if errored:
        lines.append("")
        lines.append("Errors (reported, never omitted):")
        for plan in errored:
            lines.append(f"  {plan.version} {plan.slug}: {plan.error}")
    undeclared = [p for p in plans if p.note and not p.error]
    if undeclared:
        lines.append("")
        lines.append(
            f"Undeclared status: {len(undeclared)} plan(s) carry no Status line."
        )
    lines.append("")
    lines.append(
        "An open task count is NOT queue membership: shipped and abandoned plans "
        "retain unchecked task lines. Read the status before ranking."
    )
    return "\n".join(lines)


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--root", default=".", help="repository root (default: .)")
    parser.add_argument(
        "--json", action="store_true", help="emit JSON instead of a table"
    )
    args = parser.parse_args(list(argv) if argv is not None else None)

    root = Path(args.root).resolve()
    if not root.is_dir():
        print(f"error: root is not a directory: {root}", file=sys.stderr)
        return 2

    plans = enumerate_plans(root)

    if args.json:
        print(json.dumps({"plans": [p.as_dict() for p in plans]}, indent=2))
    else:
        print(render_table(plans))

    return 1 if any(p.error for p in plans) else 0


if __name__ == "__main__":
    sys.exit(main())
