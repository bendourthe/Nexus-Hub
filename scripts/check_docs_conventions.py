#!/usr/bin/env python3
"""Fail the build on broken relative docs links and directory-name drift.

Repo-internal guard (no installer copy, no .ps1 sibling). Scans Markdown
under the canonical ``docs/v<MAJOR>/v<MAJOR>.<MINOR>/`` tree (plugin.json
major.minor, skipping ``docs/archive/``, older minors, and future majors
such as ``docs/v4/`` while the catalog is still 3.x) for:

- relative links and image paths whose target is missing
- relative links whose target exists only with a different case (breaks on
  GitHub/Linux while passing on Windows)
- empty directories
- directory names that are not kebab-case (lowercase, digits, hyphen; dots
  allowed so version dirs like v3.19 stay legal)

Usage:

    python scripts/check_docs_conventions.py
    python scripts/check_docs_conventions.py --root DIR

Exit codes:
    0 - the scanned tree is clean
    1 - one or more violations
    2 - usage / IO error
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

SKIP_DIR_NAMES = frozenset(
    {
        "archive",
        # v4.0.0 renamed the frozen container to the plural form; both are
        # skipped so a legacy consuming tree behaves identically.
        "archives",
        "__pycache__",
        ".git",
        ".venv",
        "node_modules",
        ".pytest_cache",
    }
)
DIR_NAME_RE = re.compile(r"^[a-z0-9]+(?:[.-][a-z0-9]+)*$")
_VERSION_DIR = re.compile(r"^v(?P<major>\d+)\.(?P<minor>\d+)$")
# Markdown inline link or image: ](dest) / ](<dest>). Skip autolinks.
LINK_RE = re.compile(r"!?\[[^\]]*\]\(\s*<?([^)\s>]+)>?\s*\)")
SKIP_SCHEMES = ("http://", "https://", "mailto:", "ftp://")


def rel(path: Path, root: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def docs_root(root: Path) -> Path:
    nested = root / "docs"
    return nested if nested.is_dir() else root


def read_canonical_major_minor(root: Path) -> tuple[int, int] | None:
    """Return (major, minor) from ``.claude-plugin/plugin.json``, or None."""
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


def _newest_minor_under(major_dir: Path, major: int) -> Path | None:
    """Newest ``v<major>.<minor>`` child of ``major_dir``, numeric not lexical."""
    best: tuple[int, Path] | None = None
    try:
        children = list(major_dir.iterdir())
    except OSError:
        return None
    for minor_dir in children:
        if not minor_dir.is_dir():
            continue
        match = _VERSION_DIR.match(minor_dir.name)
        if not match or int(match.group("major")) != major:
            continue
        minor = int(match.group("minor"))
        if best is None or minor > best[0]:
            best = (minor, minor_dir)
    return None if best is None else best[1]


def find_active_minor(root: Path) -> Path | None:
    """Return the docs tree this guard should scan, or None.

    Prefer the canonical plugin version's ``docs/v<MAJOR>/v<MAJOR>.<MINOR>/``.
    That is the live minor; a future major on disk (``docs/v4/`` while the
    catalog is 3.20.x) is planning, not the scan target -- picking it would
    repeat the colocation fail-open. Without plugin.json (tmp fixtures), pick
    the newest version directory on disk. Historical minors stay unscanned:
    they carry grandfathered broken links.
    """
    canonical = read_canonical_major_minor(root)
    if canonical is not None:
        major, minor = canonical
        # Canonical (v4.0.0+) tree first, then the legacy v-bucket. Without the
        # canonical branch this returns None on a migrated repo and
        # resolve_scan_tree falls back to the WHOLE docs tree, re-opening the
        # colocation fail-open this function exists to prevent.
        for base in (root / "docs" / "releases" / f"v{major}", root / "docs" / f"v{major}"):
            exact = base / f"v{major}.{minor}"
            if exact.is_dir():
                return exact
            if base.is_dir():
                newest = _newest_minor_under(base, major)
                if newest is not None:
                    return newest
        return None
    docs = root / "docs"
    if not docs.is_dir():
        return None
    best: tuple[int, int, Path] | None = None
    try:
        major_dirs = list(docs.iterdir())
    except OSError:
        return None
    releases = docs / "releases"
    if releases.is_dir():
        major_dirs = list(releases.iterdir())
    for major_dir in major_dirs:
        if not major_dir.is_dir() or not re.match(r"^v\d+$", major_dir.name):
            continue
        major = int(major_dir.name[1:])
        newest = _newest_minor_under(major_dir, major)
        if newest is None:
            continue
        match = _VERSION_DIR.match(newest.name)
        if not match:
            continue
        minor = int(match.group("minor"))
        if best is None or (major, minor) > (best[0], best[1]):
            best = (major, minor, newest)
    return None if best is None else best[2]


def resolve_scan_tree(root: Path) -> Path | None:
    active = find_active_minor(root)
    if active is not None:
        return active
    tree = docs_root(root)
    return tree if tree.is_dir() else None


def iter_dirs(base: Path) -> list[Path]:
    found: list[Path] = []
    stack = [base]
    while stack:
        current = stack.pop()
        try:
            children = list(current.iterdir())
        except OSError:
            continue
        for child in children:
            if not child.is_dir() or child.name in SKIP_DIR_NAMES:
                continue
            found.append(child)
            stack.append(child)
    return found


def iter_markdown(base: Path) -> list[Path]:
    files: list[Path] = []
    for path in base.rglob("*.md"):
        if any(part in SKIP_DIR_NAMES for part in path.parts):
            continue
        if path.is_file():
            files.append(path)
    return files


def case_walk(start: Path, dest: str) -> str | None:
    """Walk dest relative to start using the names as written.

    Returns 'missing', 'case', or None if every component exists with
    the exact case the link used. Walking listings (not Path.exists)
    is what catches Windows-only case bugs.
    """
    cursor = start
    for part in Path(dest).parts:
        if part == ".":
            continue
        if part == "..":
            cursor = cursor.parent
            continue
        try:
            names = [p.name for p in cursor.iterdir()]
        except OSError:
            return "missing"
        if part in names:
            cursor = cursor / part
            continue
        folded = {name.lower(): name for name in names}
        if part.lower() in folded:
            return "case"
        return "missing"
    return None


def check_links(md_file: Path, tree: Path) -> list[str]:
    findings: list[str] = []
    try:
        text = md_file.read_text(encoding="utf-8")
    except OSError as exc:
        return [f"IO: {rel(md_file, tree)}: {exc}"]
    for match in LINK_RE.finditer(text):
        dest = match.group(1).strip()
        if not dest or dest.startswith(SKIP_SCHEMES) or dest.startswith("#"):
            continue
        dest = dest.split("#", 1)[0].split("?", 1)[0]
        if not dest or dest.startswith("/"):
            continue
        kind = case_walk(md_file.parent, dest)
        loc = rel(md_file, tree)
        if kind == "missing":
            findings.append(f"{loc}: missing relative target {dest}")
        elif kind == "case":
            findings.append(f"{loc}: case-mismatch relative target {dest}")
    return findings


def check_dirs(tree: Path) -> list[str]:
    findings: list[str] = []
    for directory in iter_dirs(tree):
        name = directory.name
        if not DIR_NAME_RE.match(name):
            findings.append(f"{rel(directory, tree)}: directory name is not kebab-case")
        try:
            children = list(directory.iterdir())
        except OSError:
            continue
        if not children:
            findings.append(f"{rel(directory, tree)}: empty directory")
    return findings


def scan(root: Path) -> list[str]:
    tree = resolve_scan_tree(root)
    if tree is None:
        return [f"MISS: docs tree not found under {root}"]
    findings: list[str] = []
    findings.extend(check_dirs(tree))
    for md_file in iter_markdown(tree):
        findings.extend(check_links(md_file, tree))
    return findings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=None, help="repo root or docs tree")
    args = parser.parse_args(argv)
    root = (args.root or Path(__file__).resolve().parents[1]).resolve()
    if args.root is not None and not root.exists():
        print(f"MISS: root {root} does not exist", file=sys.stderr)
        return 1
    try:
        findings = scan(root)
    except OSError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    if findings:
        print(f"FAIL: {len(findings)} docs-convention violation(s)", file=sys.stderr)
        for item in findings:
            print(f"  {item}", file=sys.stderr)
        return 1
    shown = resolve_scan_tree(root) or docs_root(root)
    print(f"OK: docs conventions hold under {shown}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
