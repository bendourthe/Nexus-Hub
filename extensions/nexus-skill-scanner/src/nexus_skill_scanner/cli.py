"""Command-line interface for the skill-security scanner.

    nexus-skill-scanner <target> [<target> ...] [options]

Options mirror the established skill-scanner CLI shape:
    --format {terminal,json,markdown,sarif}   output format (default terminal)
    --output PATH                             write to a file instead of stdout
    --fail-on {none,low,medium,high,critical} exit 1 if any finding meets/exceeds
                                              this severity (default none; the CI
                                              catalog gate uses --fail-on high)
    --no-llm                                  documented default: the engine is
                                              always deterministic; the semantic
                                              pass is the skill-security-scan skill
    --osv                                     (Phase 7) opt-in OSV.dev dep lookup;
                                              not yet available -- reported as skipped
    --repo-root PATH                          Nexus-Hub checkout root (auto-detected)
    -V / --version                            print the scanner version

Exit codes: 0 = clean / below threshold, 1 = findings at/above --fail-on,
2 = usage or IO error.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import __version__
from .analyzers.subsumed import find_repo_root
from .emitters import render
from .scanner import Scanner
from .types import Severity


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="nexus-skill-scanner",
        description="Local-only static skill-security scanner (16 vulnerability classes).",
    )
    parser.add_argument("targets", nargs="*", help="files or directories to scan")
    parser.add_argument(
        "--format", "-f", default="terminal",
        choices=["terminal", "json", "markdown", "sarif"],
        help="output format (default: terminal)",
    )
    parser.add_argument("--output", "-o", type=Path, default=None, help="write output to this file")
    parser.add_argument(
        "--fail-on", default="none",
        choices=["none", "low", "medium", "high", "critical"],
        help="exit 1 if any finding meets/exceeds this severity (default: none)",
    )
    parser.add_argument(
        "--no-llm", action="store_true",
        help="no-op: the engine is always deterministic; the semantic pass is a skill",
    )
    parser.add_argument(
        "--osv", action="store_true",
        help="(Phase 7) opt-in OSV.dev dependency lookup; not yet available",
    )
    parser.add_argument("--repo-root", type=Path, default=None, help="Nexus-Hub checkout root")
    parser.add_argument("-V", "--version", action="version", version=f"nexus-skill-scanner {__version__}")
    return parser


def run(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if not args.targets:
        parser.error("at least one target is required")

    targets = [Path(t) for t in args.targets]
    missing = [t for t in targets if not t.exists()]
    if missing:
        print(
            "ERROR: target(s) not found: " + ", ".join(str(m) for m in missing),
            file=sys.stderr,
        )
        return 2

    repo_root = args.repo_root or find_repo_root(targets[0])
    scanner = Scanner(repo_root=repo_root)
    result = scanner.scan(targets)

    # Optional modules that are not part of the deterministic Phase 6 core.
    if args.osv:
        result.skipped_modules.append("osv (Phase 7, not yet available)")

    output = render(result, args.format)
    if args.output:
        try:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(output + "\n", encoding="utf-8")
        except OSError as exc:
            print(f"ERROR: could not write {args.output}: {exc}", file=sys.stderr)
            return 2
        print(f"Wrote {args.format} report to {args.output}", file=sys.stderr)
    else:
        print(output)

    if args.fail_on != "none":
        threshold = Severity.from_label(args.fail_on)
        if any(f.severity >= threshold for f in result.findings):
            n = sum(1 for f in result.findings if f.severity >= threshold)
            print(
                f"\nGATE FAILED: {n} finding(s) at or above {args.fail_on.upper()}.",
                file=sys.stderr,
            )
            return 1
    return 0


def main(argv: list[str] | None = None) -> int:
    try:
        return run(argv)
    except KeyboardInterrupt:  # pragma: no cover
        return 130
