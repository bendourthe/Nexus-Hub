#!/usr/bin/env python3
"""
audit-docs.py — Inventory and reference-graph helper for the docs-layout-refactor skill.

This script ships as a Tier-3 bundled resource: agents invoke it via the shell
and consume its JSON output without reading the source into context. It is
single-file, stdlib-only, and works on Python 3.8+ across macOS, Linux, and
Windows.

Subcommands:
    inventory   Walk a docs/ tree and emit one NDJSON record per file.
    refgraph    Scan the rest of the repo for inbound references to each docs file.

Usage:
    python audit-docs.py inventory --root ./docs
    python audit-docs.py refgraph  --root ./docs --repo-root .

Output formats are documented in catalog/skills/code-cleanup/docs-layout-refactor/SKILL.md
under "Step 2 - Tree fingerprinting" and "Step 3 - Reference graph".
"""
from __future__ import annotations

import argparse
import fnmatch
import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Iterator, List, Optional


# ── Constants ──────────────────────────────────────────────────────────────

VERSION_DIR_RE = re.compile(r"^v\d+(?:\.\d+){0,2}(?:[-_].+)?$")
BINARY_EXTENSIONS = {
    ".png", ".jpg", ".jpeg", ".gif", ".bmp", ".tiff", ".webp", ".ico", ".svg",
    ".pdf", ".docx", ".xlsx", ".pptx", ".odt", ".ods", ".odp",
    ".zip", ".tar", ".gz", ".bz2", ".7z", ".rar",
    ".mp3", ".mp4", ".wav", ".mov", ".avi", ".mkv",
    ".pkl", ".pickle", ".bin", ".onnx", ".pt", ".pth", ".h5", ".parquet",
    ".so", ".dylib", ".dll", ".exe", ".wasm", ".class", ".jar",
}
REFGRAPH_SCAN_EXTENSIONS = {
    ".md", ".markdown", ".json", ".yaml", ".yml", ".toml", ".cfg", ".ini",
    ".sh", ".bash", ".ps1", ".psm1", ".py", ".js", ".ts", ".tsx", ".jsx",
    ".go", ".rs", ".java", ".kt", ".rb", ".php", ".html", ".xml",
}
DEFAULT_EXCLUDES = {
    ".git", ".github", "node_modules", "vendor", ".venv", "venv", "env",
    "__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache",
    "dist", "build", "target", "out", ".next", ".nuxt", ".turbo",
    "coverage", "htmlcov", ".tox",
}
MAX_FILE_BYTES_DEFAULT = 1_048_576  # 1 MB


# ── Helpers ────────────────────────────────────────────────────────────────


def _to_posix(path: Path) -> str:
    """Return a POSIX-style relative path string (forward slashes)."""
    return str(path).replace("\\", "/")


def _is_binary(path: Path, max_bytes: int) -> bool:
    """Decide if a file is binary based on extension and a content sample."""
    if path.suffix.lower() in BINARY_EXTENSIONS:
        return True
    try:
        with path.open("rb") as fh:
            sample = fh.read(min(8192, max_bytes))
    except OSError:
        return True
    if b"\x00" in sample:
        return True
    return False


def _sha256_prefix(path: Path, max_bytes: int) -> Optional[str]:
    """Hash up to max_bytes of file content and return the first 12 hex chars."""
    h = hashlib.sha256()
    try:
        with path.open("rb") as fh:
            remaining = max_bytes
            while remaining > 0:
                chunk = fh.read(min(65536, remaining))
                if not chunk:
                    break
                h.update(chunk)
                remaining -= len(chunk)
    except OSError:
        return None
    return h.hexdigest()[:12]


def _line_count(path: Path) -> Optional[int]:
    """Count lines in a text file. Returns None on read failure."""
    try:
        with path.open("r", encoding="utf-8", errors="replace") as fh:
            return sum(1 for _ in fh)
    except OSError:
        return None


def _version_dir(rel: Path, docs_root: Path) -> Optional[str]:
    """Return the vX.Y.Z segment if the path is under docs/v*/, else None."""
    try:
        sub = rel.relative_to(docs_root)
    except ValueError:
        return None
    if not sub.parts:
        return None
    first = sub.parts[0]
    if VERSION_DIR_RE.match(first):
        return first
    return None


def _topic_dir(rel: Path, docs_root: Path, version_dir: Optional[str]) -> Optional[str]:
    """Return the topic subdirectory under the version dir, if any."""
    if version_dir is None:
        return None
    try:
        sub = rel.relative_to(docs_root)
    except ValueError:
        return None
    if len(sub.parts) < 3:
        return None
    return sub.parts[1]


def _walk(root: Path, excludes: Iterable[str]) -> Iterator[Path]:
    """Walk `root` and yield every file path, honoring excludes by name."""
    excludes_set = set(excludes)
    stack: List[Path] = [root]
    while stack:
        current = stack.pop()
        try:
            entries = list(current.iterdir())
        except OSError:
            continue
        for entry in entries:
            if entry.name in excludes_set:
                continue
            if entry.is_symlink():
                continue
            if entry.is_dir():
                stack.append(entry)
            elif entry.is_file():
                yield entry


def _match_any(name: str, globs: Iterable[str]) -> bool:
    return any(fnmatch.fnmatch(name, g) for g in globs)


# ── Subcommand: inventory ──────────────────────────────────────────────────


def cmd_inventory(args: argparse.Namespace) -> int:
    docs_root = Path(args.root).resolve()
    if not docs_root.exists() or not docs_root.is_dir():
        print(f"Error: docs root not found at {docs_root}", file=sys.stderr)
        return 1

    repo_root = Path(args.repo_root).resolve() if args.repo_root else docs_root.parent
    excludes = set(DEFAULT_EXCLUDES)
    if not args.include_archive:
        excludes.add("archive")
    extra_excludes = args.exclude or []

    now = datetime.now(timezone.utc)

    for path in _walk(docs_root, excludes):
        rel_repo = path.resolve().relative_to(repo_root)
        rel_str = _to_posix(rel_repo)
        if _match_any(path.name, extra_excludes):
            continue

        try:
            stat = path.stat()
        except OSError:
            continue

        mtime_dt = datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc)
        age_days = (now - mtime_dt).days

        is_binary = _is_binary(path, args.max_bytes)
        record = {
            "path": rel_str,
            "size": stat.st_size,
            "mtime": mtime_dt.isoformat(),
            "mtime_age_days": age_days,
            "sha256_prefix": _sha256_prefix(path, args.max_bytes),
            "version_dir": _version_dir(path.resolve(), docs_root),
            "topic_dir": _topic_dir(path.resolve(), docs_root, _version_dir(path.resolve(), docs_root)),
            "extension": path.suffix.lower(),
            "line_count": None if is_binary else _line_count(path),
            "is_binary": is_binary,
        }
        print(json.dumps(record, ensure_ascii=False))

    return 0


# ── Subcommand: refgraph ───────────────────────────────────────────────────


def _collect_docs_paths(docs_root: Path, repo_root: Path, include_archive: bool) -> List[str]:
    """Return POSIX-style repo-relative paths for every file under docs/."""
    excludes = set(DEFAULT_EXCLUDES)
    if not include_archive:
        excludes.add("archive")
    out: List[str] = []
    for path in _walk(docs_root, excludes):
        try:
            rel = path.resolve().relative_to(repo_root)
        except ValueError:
            continue
        out.append(_to_posix(rel))
    return out


def cmd_refgraph(args: argparse.Namespace) -> int:
    docs_root = Path(args.root).resolve()
    repo_root = Path(args.repo_root).resolve() if args.repo_root else docs_root.parent

    if not docs_root.exists() or not repo_root.exists():
        print(
            f"Error: paths missing. docs={docs_root} repo={repo_root}",
            file=sys.stderr,
        )
        return 1

    docs_paths = _collect_docs_paths(docs_root, repo_root, args.include_archive)
    if not docs_paths:
        print("{}")
        return 0

    # Index by basename to speed up scanning. Multiple paths may share a basename;
    # the scan resolves the full path match at line level.
    basenames: dict[str, List[str]] = {}
    for p in docs_paths:
        basenames.setdefault(Path(p).name, []).append(p)

    graph: dict[str, List[dict]] = {p: [] for p in docs_paths}

    excludes = set(DEFAULT_EXCLUDES)
    excludes.add("docs")  # don't scan docs/ itself

    for src in _walk(repo_root, excludes):
        if src.suffix.lower() not in REFGRAPH_SCAN_EXTENSIONS:
            continue
        try:
            text = src.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        try:
            referrer = _to_posix(src.resolve().relative_to(repo_root))
        except ValueError:
            continue

        # Quick pre-filter: skip files that mention no docs/-style path or basename.
        if "docs/" not in text and "docs\\" not in text:
            if not any(name in text for name in basenames):
                continue

        for lineno, line in enumerate(text.splitlines(), start=1):
            # Two match modes:
            # 1. Full path mention "docs/..." that ends at a non-path char.
            # 2. Basename mention scoped to the file's reference graph.
            for docs_path in docs_paths:
                if docs_path in line:
                    graph[docs_path].append({"referrer": referrer, "line": lineno})
                    continue
            # Basename-only scan (rarer; many false positives, so keep it scoped).
            for bn, owners in basenames.items():
                if len(owners) != 1:
                    continue  # ambiguous basename; only the full-path mode is safe
                docs_path = owners[0]
                if bn in line and docs_path not in line:
                    # Require the basename to appear adjacent to a path separator
                    # to avoid prose mentions like "see CHANGELOG.md".
                    if re.search(rf"[\\/]{re.escape(bn)}\b", line):
                        graph[docs_path].append({"referrer": referrer, "line": lineno})

    # Drop entries with no inbound refs to keep the output compact.
    compact = {k: v for k, v in graph.items() if v}
    json.dump(compact, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")
    return 0


# ── CLI ────────────────────────────────────────────────────────────────────


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="audit-docs",
        description="Inventory and reference-graph helper for docs-layout-refactor.",
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    inv = sub.add_parser("inventory", help="Emit NDJSON inventory of files under docs/.")
    inv.add_argument("--root", default="./docs", help="Path to the docs root.")
    inv.add_argument("--repo-root", default=None, help="Repo root (defaults to parent of --root).")
    inv.add_argument("--exclude", action="append", default=[], help="Glob to skip (repeatable).")
    inv.add_argument("--include-archive", action="store_true", help="Include docs/archive/ in the scan.")
    inv.add_argument("--max-bytes", type=int, default=MAX_FILE_BYTES_DEFAULT,
                     help="Cap on bytes read for hashing and binary detection.")
    inv.set_defaults(func=cmd_inventory)

    ref = sub.add_parser("refgraph", help="Emit JSON map of inbound references to each docs/ file.")
    ref.add_argument("--root", default="./docs", help="Path to the docs root.")
    ref.add_argument("--repo-root", default=".", help="Repo root (defaults to current directory).")
    ref.add_argument("--include-archive", action="store_true", help="Include docs/archive/ in the scan targets.")
    ref.set_defaults(func=cmd_refgraph)

    return parser


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
