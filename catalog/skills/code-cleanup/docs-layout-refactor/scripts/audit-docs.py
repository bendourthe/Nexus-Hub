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
    lifespan-contradictions
                Report frozen-bucket files committed after release close.

Usage:
    python audit-docs.py inventory --root ./docs
    python audit-docs.py refgraph  --root ./docs --repo-root .
    python audit-docs.py lifespan-contradictions --root ./docs --repo-root .

Output formats are documented in catalog/skills/code-cleanup/docs-layout-refactor/SKILL.md
under "Step 2 - Tree fingerprinting" and "Step 3 - Reference graph".
"""
from __future__ import annotations

import argparse
import fnmatch
import hashlib
import json
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Iterator, List, Optional


# ── Constants ──────────────────────────────────────────────────────────────

VERSION_DIR_RE = re.compile(r"^v\d+(?:\.\d+){0,2}(?:[-_].+)?$")
# Legacy v-bucket migration source: docs/v<MAJOR>/v<MAJOR>.<MINOR>/<topic>/...
MAJOR_BUCKET_RE = re.compile(r"^v\d+$")
MINOR_DIR_RE = re.compile(r"^v\d+\.\d+$")
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

LIFESPAN_DISPOSITIONS = {
    "never": "living",
    "supersession": "append-only",
    "release-close": "frozen-at-close",
    "controlled-record": "controlled record",
    "already-frozen": "already-frozen",
    "generated": "generated",
}

LIFESPAN_FAST_PATH = {
    "adr": "append-only",
    "adrs": "append-only",
    "decisions": "append-only",
    "rfc": "append-only",
    "rfcs": "append-only",
    "handbooks": "living",
    "architecture": "living",
    "design": "living",
    "tutorials": "living",
    "how-to": "living",
    "reference": "living",
    "runbooks": "living",
    "policy": "living",
    "security": "living",
    "compliance": "controlled record",
    "validation": "controlled record",
}

FROZEN_BUCKET_RE = re.compile(
    r"^docs/(?:releases/)?v(?P<major>\d+)/v(?P=major)\.(?P<minor>\d+)(?:/|$)"
)


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


def _resolve_version_topic(
    abs_path: Path, docs_root: Path
) -> "tuple[Optional[str], Optional[str], Optional[str]]":
    """Resolve version, topic, and layout for a docs path.

    Four active-tree layouts are recognized:

    - ``releases``: ``docs/releases/v<MAJOR>/v<MAJOR>.<MINOR>/``.
    - ``v-bucket``: legacy ``docs/v<MAJOR>/v<MAJOR>.<MINOR>/``.
    - ``flat``: legacy ``docs/<vSEMVER>/``.
    - ``versions``: legacy ``docs/versions/v<MAJOR>/<vSEMVER>/``.

    The corresponding ``archives`` and legacy ``archive`` containers reuse the
    same layout labels. Returns ``(None, None, None)`` outside a version tree.
    """
    try:
        sub = abs_path.relative_to(docs_root)
    except ValueError:
        return None, None, None
    parts = list(sub.parts)
    archive_container: Optional[str] = None
    if parts and parts[0] in {"archive", "archives"}:
        archive_container = parts[0]
        parts = parts[1:]
    if not parts:
        return None, None, None
    layout: Optional[str] = None
    if parts[0] == "releases":
        layout = "releases"
        parts = parts[1:]
    elif parts[0] == "versions":
        layout = "versions"
        parts = parts[1:]
    elif archive_container == "archives":
        layout = "releases"
    if not parts:
        return None, None, None
    first = parts[0]
    if not VERSION_DIR_RE.match(first):
        return None, None, None
    if layout == "versions" and len(parts) >= 2 and MAJOR_BUCKET_RE.match(first) and VERSION_DIR_RE.match(parts[1]):
        version = parts[1]
        topic = parts[2] if len(parts) >= 4 else None
        return version, topic, layout
    if len(parts) >= 2 and MAJOR_BUCKET_RE.match(first) and MINOR_DIR_RE.match(parts[1]):
        version = parts[1]
        topic = parts[2] if len(parts) >= 4 else None
        return version, topic, layout or "v-bucket"
    topic = parts[1] if len(parts) >= 3 else None
    return first, topic, layout or "flat"


def _version_dir(abs_path: Path, docs_root: Path) -> Optional[str]:
    """Return the version-directory segment for a docs path, or None.

    Backward-compatible wrapper around :func:`_resolve_version_topic`.
    """
    return _resolve_version_topic(abs_path, docs_root)[0]


def _topic_dir(
    abs_path: Path, docs_root: Path, version_dir: Optional[str] = None
) -> Optional[str]:
    """Return the topic subdirectory for a docs path, or None.

    The ``version_dir`` argument is retained for call-site compatibility but is
    no longer consulted; the resolver derives both values together.
    """
    return _resolve_version_topic(abs_path, docs_root)[1]


def _canonical_destination(docs_root: Path, source: Path, layout: str) -> Optional[Path]:
    relative = source.relative_to(docs_root)
    if layout == "v-bucket":
        major, minor = relative.parts[-2:]
    elif layout == "versions":
        major, version = relative.parts[-2:]
        match = re.fullmatch(r"v(\d+)\.(\d+)(?:\.\d+)?", version)
        if not match:
            return None
        minor = f"v{match.group(1)}.{match.group(2)}"
    else:
        version = relative.parts[-1]
        match = re.fullmatch(r"v(\d+)\.(\d+)(?:\.\d+)?", version)
        if not match:
            return None
        major = f"v{match.group(1)}"
        minor = f"v{match.group(1)}.{match.group(2)}"
    return docs_root / "releases" / major / minor


def _legacy_archive_container(docs_root: Path) -> Optional[tuple[Path, Path, str]]:
    """Return the singular-to-plural archive container rename, or None.

    The frozen tree is prescribed as ``docs/archives/``; the legacy pre-rename
    migration-source container is the singular ``docs/archive/``. Bucketing below
    the container is identical on both sides, so this is a container rename
    rather than a per-version migration. Returns None when that legacy container
    is absent or the canonical one already exists.
    """
    legacy = docs_root / "archive"
    if not legacy.is_dir():
        return None
    return legacy, docs_root / "archives", "archive-container"


def _legacy_version_directories(docs_root: Path) -> list[tuple[Path, Path, str]]:
    migrations: list[tuple[Path, Path, str]] = []
    for major in sorted(docs_root.glob("v[0-9]*")):
        if not major.is_dir() or not MAJOR_BUCKET_RE.fullmatch(major.name):
            continue
        for minor in sorted(major.iterdir()):
            if minor.is_dir() and MINOR_DIR_RE.fullmatch(minor.name):
                destination = _canonical_destination(docs_root, minor, "v-bucket")
                if destination:
                    migrations.append((minor, destination, "v-bucket"))
    versions = docs_root / "versions"
    if versions.is_dir():
        for major in sorted(versions.glob("v[0-9]*")):
            if not major.is_dir() or not MAJOR_BUCKET_RE.fullmatch(major.name):
                continue
            for version in sorted(major.iterdir()):
                if version.is_dir() and VERSION_DIR_RE.fullmatch(version.name):
                    destination = _canonical_destination(docs_root, version, "versions")
                    if destination:
                        migrations.append((version, destination, "versions"))
    for version in sorted(docs_root.glob("v*.*")):
        if version.is_dir() and VERSION_DIR_RE.fullmatch(version.name):
            destination = _canonical_destination(docs_root, version, "flat")
            if destination:
                migrations.append((version, destination, "flat"))
    return migrations


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


def classify_lifespan(answer: str) -> str:
    """Return the disposition for one explicit admission-test answer."""
    key = answer.strip().lower().replace("_", "-")
    if key not in LIFESPAN_DISPOSITIONS:
        raise ValueError(f"indeterminate lifespan answer: {answer}")
    return LIFESPAN_DISPOSITIONS[key]


def lifespan_fast_path(relative_path: str) -> Optional[str]:
    """Return a recognized-root shortcut, or None so the admission test decides."""
    parts = Path(relative_path.replace("\\", "/")).parts
    if parts and parts[0].lower() == "docs":
        parts = parts[1:]
    if not parts:
        return None
    return LIFESPAN_FAST_PATH.get(parts[0].lower())


def _git(repo_root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    """Run one fixed-argv git query without invoking a shell."""
    return subprocess.run(
        ["git", "-C", str(repo_root), *args],
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )


def _parse_iso(value: str) -> datetime:
    return datetime.fromisoformat(value.strip().replace("Z", "+00:00"))


def _release_close_dates(repo_root: Path) -> dict[tuple[int, int], tuple[str, str]]:
    result = _git(
        repo_root,
        "for-each-ref",
        "--format=%(refname:short)%09%(creatordate:iso-strict)",
        "refs/tags",
    )
    if result.returncode != 0:
        return {}
    candidates: dict[tuple[int, int], list[tuple[datetime, str, str]]] = {}
    for line in result.stdout.splitlines():
        if "\t" not in line:
            continue
        tag, created = line.split("\t", 1)
        match = re.fullmatch(r"v(\d+)\.(\d+)(?:\.(\d+))?", tag)
        if not match:
            continue
        key = (int(match.group(1)), int(match.group(2)))
        candidates.setdefault(key, []).append((_parse_iso(created), tag, created))
    closes: dict[tuple[int, int], tuple[str, str]] = {}
    for key, values in candidates.items():
        _, tag, created = min(values, key=lambda item: item[0])
        closes[key] = (tag, created)
    return closes


def find_lifespan_contradictions(repo_root: Path, docs_root: Path) -> list[dict[str, str]]:
    """Find tracked frozen-bucket documents edited after their release closed."""
    try:
        docs_rel = _to_posix(docs_root.resolve().relative_to(repo_root.resolve()))
    except ValueError:
        return []
    tracked = _git(repo_root, "ls-files", "-z", "--", docs_rel)
    if tracked.returncode != 0:
        return []
    closes = _release_close_dates(repo_root)
    findings: list[dict[str, str]] = []
    for path in sorted(item for item in tracked.stdout.split("\0") if item):
        match = FROZEN_BUCKET_RE.match(path)
        if not match:
            continue
        key = (int(match.group("major")), int(match.group("minor")))
        close = closes.get(key)
        if close is None:
            continue
        newest = _git(repo_root, "log", "-1", "--format=%cI", "--", path)
        commit_date = newest.stdout.strip()
        if newest.returncode != 0 or not commit_date:
            continue
        release_tag, release_date = close
        if _parse_iso(commit_date) <= _parse_iso(release_date):
            continue
        findings.append(
            {
                "file": path,
                "bucket": f"v{key[0]}.{key[1]}",
                "release_tag": release_tag,
                "release_close_date": release_date,
                "offending_commit_date": commit_date,
            }
        )
    return findings


# ── Subcommand: inventory ──────────────────────────────────────────────────


def cmd_inventory(args: argparse.Namespace) -> int:
    docs_root = Path(args.root).resolve()
    if not docs_root.exists() or not docs_root.is_dir():
        print(f"Error: docs root not found at {docs_root}", file=sys.stderr)
        return 1

    repo_root = Path(args.repo_root).resolve() if args.repo_root else docs_root.parent
    excludes = set(DEFAULT_EXCLUDES)
    if not args.include_archive:
        excludes.update({"archive", "archives"})
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
        version_dir, topic_dir, layout = _resolve_version_topic(path.resolve(), docs_root)
        record = {
            "path": rel_str,
            "size": stat.st_size,
            "mtime": mtime_dt.isoformat(),
            "mtime_age_days": age_days,
            "sha256_prefix": _sha256_prefix(path, args.max_bytes),
            "version_dir": version_dir,
            "topic_dir": topic_dir,
            "layout": layout,
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
        excludes.update({"archive", "archives"})
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


def cmd_lifespan_contradictions(args: argparse.Namespace) -> int:
    repo_root = Path(args.repo_root).resolve()
    docs_root = Path(args.root).resolve()
    if not repo_root.is_dir() or not docs_root.is_dir():
        print(f"Error: paths missing. docs={docs_root} repo={repo_root}", file=sys.stderr)
        return 2
    findings = find_lifespan_contradictions(repo_root, docs_root)
    json.dump(findings, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")
    return 1 if findings else 0


def cmd_canonicalize_layout(args: argparse.Namespace) -> int:
    docs_root = Path(args.root).resolve()
    if not docs_root.is_dir():
        print(f"Error: docs root not found at {docs_root}", file=sys.stderr)
        return 2
    migrations = _legacy_version_directories(docs_root)
    archive_migration = _legacy_archive_container(docs_root)
    if archive_migration:
        migrations.append(archive_migration)
    collisions = [str(destination) for _, destination, _ in migrations if destination.exists()]
    if collisions:
        print(json.dumps({"error": "destination exists", "paths": collisions}, indent=2), file=sys.stderr)
        return 2
    records: list[dict[str, str]] = []
    for source, destination, layout in migrations:
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(source), str(destination))
        records.append(
            {
                "source": _to_posix(source.relative_to(docs_root.parent)),
                "destination": _to_posix(destination.relative_to(docs_root.parent)),
                "layout": layout,
            }
        )
    json.dump(records, sys.stdout, ensure_ascii=False, indent=2)
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
    inv.add_argument("--include-archive", action="store_true", help="Include docs/archives/ and legacy docs/archive/ in the scan.")
    inv.add_argument("--max-bytes", type=int, default=MAX_FILE_BYTES_DEFAULT,
                     help="Cap on bytes read for hashing and binary detection.")
    inv.set_defaults(func=cmd_inventory)

    ref = sub.add_parser("refgraph", help="Emit JSON map of inbound references to each docs/ file.")
    ref.add_argument("--root", default="./docs", help="Path to the docs root.")
    ref.add_argument("--repo-root", default=".", help="Repo root (defaults to current directory).")
    ref.add_argument("--include-archive", action="store_true", help="Include docs/archives/ and legacy docs/archive/ in the scan targets.")
    ref.set_defaults(func=cmd_refgraph)

    contradictions = sub.add_parser(
        "lifespan-contradictions",
        help="Report frozen-bucket documents committed after the matching release tag.",
    )
    contradictions.add_argument("--root", default="./docs", help="Path to the docs root.")
    contradictions.add_argument("--repo-root", default=".", help="Repository root.")
    contradictions.set_defaults(func=cmd_lifespan_contradictions)

    canonicalize = sub.add_parser(
        "canonicalize-layout",
        help="Move legacy active version directories into docs/releases/ and the legacy docs/archive/ container to docs/archives/.",
    )
    canonicalize.add_argument("--root", default="./docs", help="Path to the docs root.")
    canonicalize.set_defaults(func=cmd_canonicalize_layout)

    return parser


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
