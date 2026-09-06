#!/usr/bin/env python3
"""Validate that no personal user paths leak into distributed content.

Scans the documentation, catalog, and template trees for absolute paths that
embed a real user's home directory (POSIX `/Users/<name>`, `/home/<name>`, or
Windows `C:\\Users\\<name>`). Placeholder usernames (`example`, `you`,
`username`, etc.) and well-known service accounts (`runner`, `Administrator`)
are allowed; everything else fails the build.

Exit codes:
    0 - no findings
    1 - one or more leaked paths detected
    2 - usage / IO error

Usage:
    python scripts/validate_no_personal_paths.py
    python scripts/validate_no_personal_paths.py --path catalog/
    python scripts/validate_no_personal_paths.py --verbose
"""

from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path

ALLOWED_USERNAMES: frozenset[str] = frozenset({
    "example",
    "user",
    "users",
    "you",
    "yourname",
    "username",
    "me",
    "name",
    "someone",
    "developer",
    "dev",
    "test",
    "tester",
    "runner",
    "administrator",
    "public",
    "root",
    "claude",
    "agent",
    "ci",
    "build",
    "testuser",
    "fakeuser",
    "dummyuser",
    "alice",
    "bob",
    "carol",
    "demo",
    "service",
    "appuser",
})

PLACEHOLDER_PREFIXES: tuple[str, ...] = ("<", "${", "{{", "%(", "$")

DEFAULT_TARGETS: tuple[str, ...] = (
    "README.md",
    "catalog",
    "docs",
    "templates",
)

EXEMPT_DIR_PARTS: frozenset[str] = frozenset({
    "archive",
    # v4.0.0 renamed the frozen container to the plural form. Both are listed so
    # a consuming repo still on the legacy singular tree stays exempt too.
    "archives",
    "forensics",
    "smoke-reports",
    "installer-smoke",
})

TEXT_EXTENSIONS: frozenset[str] = frozenset({
    ".md", ".txt", ".json", ".yaml", ".yml", ".toml", ".cfg", ".ini",
    ".py", ".sh", ".ps1", ".js", ".ts", ".tsx", ".jsx", ".html",
    ".css", ".scss", ".rst", ".bash", ".zsh", ".fish", ".env",
})

POSIX_PATH_RE = re.compile(
    r"(?P<full>/(?:Users|home)/(?P<user>[A-Za-z0-9_.\-]+))(?![A-Za-z0-9_.\-])"
)
WINDOWS_PATH_RE = re.compile(
    r"(?P<full>[A-Za-z]:[\\/]+Users[\\/]+(?P<user>[A-Za-z0-9_.\-]+))"
    r"(?![A-Za-z0-9_.\-])"
)


def is_text_file(path: Path) -> bool:
    if path.suffix.lower() in TEXT_EXTENSIONS:
        return True
    if path.suffix == "" and path.name.isupper():
        return True
    return False


def in_exempt_dir(path: Path) -> bool:
    return any(part in EXEMPT_DIR_PARTS for part in path.parts)


def username_is_placeholder(user: str) -> bool:
    lower = user.lower()
    if lower in ALLOWED_USERNAMES:
        return True
    if any(user.startswith(p) for p in PLACEHOLDER_PREFIXES):
        return True
    return False


def scan_file(path: Path) -> list[tuple[int, int, str, str]]:
    """Return [(line_no, col, matched_path, username), ...]."""
    findings: list[tuple[int, int, str, str]] = []
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return findings

    for line_no, line in enumerate(text.splitlines(), start=1):
        for regex in (POSIX_PATH_RE, WINDOWS_PATH_RE):
            for match in regex.finditer(line):
                user = match.group("user")
                if username_is_placeholder(user):
                    continue
                findings.append((line_no, match.start() + 1, match.group("full"), user))
    return findings


def path_is_excluded(path: Path, root: Path, excludes: tuple[Path, ...]) -> bool:
    try:
        rel = path.resolve().relative_to(root)
    except ValueError:
        return False
    for ex in excludes:
        try:
            rel.relative_to(ex)
            return True
        except ValueError:
            continue
    return False


def iter_target_files(
    root: Path,
    targets: tuple[str, ...],
    excludes: tuple[Path, ...] = (),
) -> list[Path]:
    files: list[Path] = []
    for target in targets:
        full = root / target
        if not full.exists():
            continue
        if full.is_file():
            if (
                is_text_file(full)
                and not in_exempt_dir(full)
                and not path_is_excluded(full, root, excludes)
            ):
                files.append(full)
            continue
        for dirpath, dirnames, filenames in os.walk(full):
            dirnames[:] = [d for d in dirnames if d not in EXEMPT_DIR_PARTS]
            current = Path(dirpath)
            dirnames[:] = [
                d for d in dirnames
                if not path_is_excluded(current / d, root, excludes)
            ]
            for name in filenames:
                candidate = current / name
                if not is_text_file(candidate):
                    continue
                if in_exempt_dir(candidate):
                    continue
                if path_is_excluded(candidate, root, excludes):
                    continue
                files.append(candidate)
    return files


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parent.parent,
        help="Repository root (default: detected from script location).",
    )
    parser.add_argument(
        "--path",
        action="append",
        default=None,
        help="Override scan targets; repeat for multiple paths.",
    )
    parser.add_argument(
        "--exclude",
        action="append",
        default=None,
        help="Exclude a path (relative to --root) from scanning; repeatable.",
    )
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    root: Path = args.root.resolve()
    if not root.is_dir():
        print(f"ERROR: root not found: {root}", file=sys.stderr)
        return 2

    targets = tuple(args.path) if args.path else DEFAULT_TARGETS
    excludes: tuple[Path, ...] = tuple(
        Path(e).as_posix().lstrip("./") for e in (args.exclude or ())
    )
    excludes = tuple(Path(e) for e in excludes)
    files = iter_target_files(root, targets, excludes)

    if args.verbose:
        print(f"Scanning {len(files)} text file(s) under {root}...")

    total_findings = 0
    for path in files:
        findings = scan_file(path)
        if not findings:
            continue
        rel = path.relative_to(root)
        for line_no, col, matched, user in findings:
            print(
                f"{rel}:{line_no}:{col}: personal path leak: "
                f"{matched!r} (username={user!r})",
                file=sys.stderr,
            )
            total_findings += 1

    if total_findings:
        print(
            f"\nvalidate_no_personal_paths: {total_findings} finding(s) "
            f"in {len(files)} scanned file(s).",
            file=sys.stderr,
        )
        return 1

    if args.verbose:
        print(
            f"validate_no_personal_paths: clean "
            f"({len(files)} file(s) scanned, 0 findings)."
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
