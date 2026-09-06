#!/usr/bin/env python3
"""Report per-version documentation that is due for archival. Advisory only.

`docs/policy/docs-retention.md` says a minor version's `development/history/`
subtree moves to `docs/archive/v<MAJOR>/v<MAJOR>.<MINOR>/development/history/`
once that minor is two or more minors behind the current one. This reports drift
against that rule and names the destination.

Only `history/` ages out. See the AGING_SUBDIR comment below for why the rest of
`development/` does not.

It NEVER moves or deletes anything, and it ALWAYS exits 0. Archiving repairs
references across the repo, so it belongs in a reviewed `docs-layout-refactor`
pass with a confirmation gate, not in a validator that runs on every commit. A
hard gate here would also block an unrelated release the moment a minor version
aged out, which is a real cost to prevent no harm.

Repo-internal maintainer tooling: no `.ps1` sibling, no installer copy step. It
is listed in `DEV_ONLY_SCRIPTS` in `catalog/hooks/tests/test_installer_smoke.py`.

Usage:
    python scripts/check_docs_retention.py [--root PATH] [--quiet]

Exit codes:
    0 - always, including when violations are reported or the tree is absent
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from io import StringIO
from pathlib import Path

_LIB = Path(__file__).resolve().parent / "lib"
if str(_LIB) not in sys.path:
    sys.path.insert(0, str(_LIB))

from output_paging import OversizedLineError, emit_paged  # noqa: E402

# docs/policy/docs-retention.md: two or more minors behind current.
ARCHIVE_AFTER_MINORS = 2

# Only `development/history/` ages out, NOT `development/` wholesale. The v3.18.0
# Phase 5 archive pass found that `development/` also holds live content: CI
# fixtures under `fixtures/` and `worked-example/` that .github/workflows execute
# directly, and contract documents under v3.15 that shipped hooks and tests cite
# by path. Archiving those would break CI and orphan a shipped code citation.
# plans/ and comparisons/ are linked from the DEVLOG index and known-gaps.md is
# read forward by the next plan, so none of the three ages out.
AGING_SUBDIR = "development/history"

_VERSION_DIR = re.compile(r"^v(?P<major>\d+)\.(?P<minor>\d+)$")


def read_canonical_version(root: Path) -> tuple[int, int] | None:
    """Return (major, minor) from the canonical plugin version, or None.

    Same source `check_version_sync.py` treats as canonical, so the two cannot
    disagree about what "current" means.
    """
    plugin = root / ".claude-plugin" / "plugin.json"
    try:
        raw = json.loads(plugin.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    version = raw.get("version")
    if not isinstance(version, str):
        return None
    match = re.match(r"^(\d+)\.(\d+)", version)
    if not match:
        return None
    return int(match.group(1)), int(match.group(2))


def find_candidates(root: Path, current: tuple[int, int]) -> list[tuple[Path, str, str]]:
    """Return (source_dir, version_label, archive_destination) for each aged-out tree."""
    current_major, current_minor = current
    out: list[tuple[Path, str, str]] = []

    for major_dir in sorted(root.glob("docs/v*")):
        if not major_dir.is_dir():
            continue
        major_name = major_dir.name
        if not re.match(r"^v\d+$", major_name):
            continue
        major = int(major_name[1:])

        try:
            # Sort numerically, not lexicographically: a plain sort puts v3.10
            # between v3.1 and v3.2, which reads as a mistake in the report.
            minor_dirs = sorted(
                (p for p in major_dir.iterdir() if p.is_dir()),
                key=lambda p: (
                    int(m.group("minor")) if (m := _VERSION_DIR.match(p.name)) else -1
                ),
            )
        except OSError as exc:  # unreadable directory: warn and continue, never fail
            print(f"  WARN: cannot read {major_dir}: {exc}", file=sys.stderr)
            continue

        for minor_dir in minor_dirs:
            match = _VERSION_DIR.match(minor_dir.name)
            if not match or int(match.group("major")) != major:
                continue
            minor = int(match.group("minor"))

            # An older major is entirely archivable; within the current major,
            # apply the two-minor distance.
            if major == current_major:
                if current_minor - minor < ARCHIVE_AFTER_MINORS:
                    continue
            elif major > current_major:
                continue  # a future version directory is planning, not history

            source = minor_dir / "development" / "history"
            if not source.is_dir():
                continue

            destination = f"docs/archive/{major_name}/{minor_dir.name}/{AGING_SUBDIR}/"
            if (root / destination).is_dir():
                continue  # already archived

            out.append((source, minor_dir.name, destination))

    return out


def render_report(root: Path, quiet: bool) -> str:
    """Build the advisory report as a single string (no I/O besides reads)."""
    buf = StringIO()

    if not (root / "docs").is_dir():
        # Not an error: a consuming project may have no docs/ tree at all.
        if not quiet:
            buf.write("  docs/ not present; retention check is a no-op\n")
        return buf.getvalue()

    current = read_canonical_version(root)
    if current is None:
        if not quiet:
            buf.write("  canonical version unreadable; retention check skipped (advisory)\n")
        return buf.getvalue()

    candidates = find_candidates(root, current)

    if not candidates:
        if not quiet:
            buf.write(
                f"  docs retention: nothing due for archival "
                f"(current v{current[0]}.{current[1]}, threshold {ARCHIVE_AFTER_MINORS} minors)\n"
            )
        return buf.getvalue()

    buf.write(
        f"  docs retention: {len(candidates)} version(s) due for archival "
        f"(current v{current[0]}.{current[1]}, threshold {ARCHIVE_AFTER_MINORS} minors). "
        f"Advisory only; see docs/policy/docs-retention.md\n"
    )
    for source, _label, destination in candidates:
        file_count = sum(1 for _ in source.rglob("*") if _.is_file())
        rel = source.relative_to(root).as_posix()
        buf.write(f"  WARN: {rel} ({file_count} file(s)) -> {destination}\n")
    buf.write("  Run the archive pass via /update refactor or the docs-layout-refactor skill.\n")
    return buf.getvalue()


def _replay_args(root_arg: str, quiet: bool) -> list[str]:
    """Arguments needed to reproduce this invocation, excluding --part."""
    extra: list[str] = []
    if root_arg != ".":
        extra.extend(["--root", root_arg])
    if quiet:
        extra.append("--quiet")
    return extra


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--root", default=".", help="Repository root.")
    parser.add_argument("--quiet", action="store_true", help="Print only violations.")
    parser.add_argument(
        "--part",
        type=int,
        default=1,
        help="1-based output page. Transport paging; see scripts/lib/output_paging.py.",
    )
    args = parser.parse_args(argv)

    root = Path(args.root).resolve()
    text = render_report(root, args.quiet)

    extra = _replay_args(args.root, args.quiet)
    try:
        print(
            emit_paged(
                text,
                part=args.part,
                extra_args=extra,
                script_path=Path(__file__),
            ),
            end="",
        )
    except (OversizedLineError, ValueError) as exc:
        # Advisory tool: never fail the validate gate because a page is
        # missing or a line is too long. Fall back to the unpaged report.
        print(f"  WARN: output paging: {exc}", file=sys.stderr)
        print(text, end="")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
