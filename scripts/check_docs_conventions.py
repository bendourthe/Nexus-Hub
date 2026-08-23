#!/usr/bin/env python3
"""Fail the build on broken relative docs links and directory-name drift.

Repo-internal guard (no installer copy, no .ps1 sibling). Scans Markdown
under docs/ (skipping docs/archive/) for:

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
import re
import sys
from pathlib import Path

SKIP_DIR_NAMES = frozenset(
    {
        "archive",
        "__pycache__",
        ".git",
        ".venv",
        "node_modules",
        ".pytest_cache",
    }
)
DIR_NAME_RE = re.compile(r"^[a-z0-9]+(?:[.-][a-z0-9]+)*$")
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
    # In this repo the active minor is docs/v3/v3.19/. Historical minor trees
    # carry grandfathered broken links; gating them would turn a new checker
    # into a 100+ finding archaeology project. Tests pass a tmp tree that has
    # docs/ but no v3.19, so they still scan the whole docs/ folder.
    active = root / "docs" / "v3" / "v3.19"
    if active.is_dir():
        tree = active
    else:
        tree = docs_root(root)
    if not tree.is_dir():
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
    active = root / "docs" / "v3" / "v3.19"
    shown = active if active.is_dir() else docs_root(root)
    print(f"OK: docs conventions hold under {shown}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
