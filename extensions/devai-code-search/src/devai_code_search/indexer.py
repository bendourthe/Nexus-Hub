"""Walk a repository, chunk files, and maintain a content-hash manifest
for incremental re-indexing.

Respects `.gitignore` and an optional `.devaiignore` at the repo root plus
a hardcoded default-exclude list (node_modules, .venv, dist, etc.).

Content-hash incremental: on re-index, unchanged files (matching SHA-256)
are skipped; modified files are re-chunked; deleted files are dropped.
"""
from __future__ import annotations

import datetime as _dt
import hashlib
import logging
from pathlib import Path
from typing import Iterable, Iterator

import pathspec

from devai_code_search.chunker import chunk_text
from devai_code_search.config import CodeSearchConfig
from devai_code_search.store import load_index, save_index
from devai_code_search.types import Chunk, IndexManifest

logger = logging.getLogger("devai-code-search")


def walk_files(root: Path, config: CodeSearchConfig) -> Iterator[Path]:
    """Yield files under `root` that pass the exclude filter and ignore files."""
    root = root.resolve()
    ignore_spec = _load_ignore_spec(root)

    for path in _iter_files(root, config):
        rel = _rel_posix(path, root)
        if ignore_spec.match_file(rel) or ignore_spec.match_file(rel + "/"):
            continue
        try:
            size = path.stat().st_size
        except OSError:
            continue
        if size > config.max_file_bytes:
            continue
        yield path


def _iter_files(root: Path, config: CodeSearchConfig) -> Iterator[Path]:
    """Walk the tree skipping excluded directory names.

    Symlinks are skipped entirely (both directory and file symlinks) to
    prevent information disclosure when indexing untrusted repositories.
    A malicious repo containing `secrets -> /etc/passwd` or similar would
    otherwise have its target read, hashed, and persisted to the index.
    See the v1.0.0 penetration test (docs/security/penetration-test-
    2026-04-27.md) for the threat model.

    If symlink-following is required for a specific use case (e.g., vendored
    submodules), expose it as an explicit `follow_symlinks` opt-in on
    CodeSearchConfig in a future release.
    """
    stack = [root]
    while stack:
        current = stack.pop()
        try:
            entries = list(current.iterdir())
        except OSError:
            continue
        for entry in entries:
            if entry.is_symlink():
                # Symlinks can point outside the indexed root; skip to
                # prevent unintended file disclosure.
                continue
            if entry.is_dir():
                if entry.name in config.exclude_dirs:
                    continue
                stack.append(entry)
            elif entry.is_file():
                if _matches_exclude_patterns(entry.name, config.exclude_patterns):
                    continue
                yield entry


def _matches_exclude_patterns(name: str, patterns: Iterable[str]) -> bool:
    import fnmatch

    return any(fnmatch.fnmatch(name, pat) for pat in patterns)


def _load_ignore_spec(root: Path) -> pathspec.PathSpec:
    """Combine `.gitignore` + `.devaiignore` into a single PathSpec."""
    lines: list[str] = []
    for name in (".gitignore", ".devaiignore"):
        p = root / name
        if p.exists():
            try:
                lines.extend(p.read_text(encoding="utf-8", errors="ignore").splitlines())
            except OSError:
                pass
    return pathspec.PathSpec.from_lines("gitwildmatch", lines)


def _rel_posix(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def hash_file(path: Path) -> str:
    """Return SHA-256 hex digest of the file contents."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(65536), b""):
            h.update(block)
    return h.hexdigest()


def read_text_safely(path: Path) -> str | None:
    """Read a file as UTF-8 text. Returns None if decode fails (binary)."""
    try:
        with open(path, "rb") as f:
            raw = f.read()
    except OSError:
        return None
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError:
        return None


def index_codebase(
    root: Path,
    config: CodeSearchConfig,
    index_dir: Path,
    force: bool = False,
    progress_cb=None,
) -> tuple[list[Chunk], IndexManifest]:
    """Build or refresh the index for `root`.

    If `force` is True, re-chunk every file regardless of prior hashes.
    Otherwise, skip unchanged files (hash match) and re-chunk modified ones.
    Returns the (complete) list of chunks and the fresh manifest.

    progress_cb, if provided, is called as progress_cb(files_processed, total_files).
    """
    root = root.resolve()
    index_dir.mkdir(parents=True, exist_ok=True)

    prior_chunks, prior_manifest = (
        (load_index(index_dir) if not force else ([], None))
    )
    prior_hashes: dict[str, str] = (
        prior_manifest.file_hashes if prior_manifest else {}
    )
    prior_chunks_by_file: dict[str, list[Chunk]] = {}
    for chunk in prior_chunks:
        prior_chunks_by_file.setdefault(chunk.file_path, []).append(chunk)

    files = list(walk_files(root, config))
    total_files = len(files)

    new_chunks: list[Chunk] = []
    new_hashes: dict[str, str] = {}
    new_chunk_counts: dict[str, int] = {}

    for idx, path in enumerate(files, start=1):
        rel = _rel_posix(path, root)
        try:
            file_hash = hash_file(path)
        except OSError:
            continue

        reuse = (
            not force
            and rel in prior_hashes
            and prior_hashes[rel] == file_hash
            and rel in prior_chunks_by_file
        )

        if reuse:
            file_chunks = prior_chunks_by_file[rel]
        else:
            text = read_text_safely(path)
            if text is None:
                continue
            file_chunks = chunk_text(
                text,
                rel,
                target_size=config.chunk_target_size,
                overlap=config.chunk_overlap,
            )

        new_hashes[rel] = file_hash
        new_chunk_counts[rel] = len(file_chunks)
        new_chunks.extend(file_chunks)

        if progress_cb is not None:
            try:
                progress_cb(idx, total_files)
            except Exception:  # noqa: BLE001
                logger.debug("progress_cb raised; continuing", exc_info=True)

    manifest = IndexManifest(
        root=str(root),
        indexed_at=_dt.datetime.now(_dt.timezone.utc).replace(tzinfo=None).isoformat() + "Z",
        total_chunks=len(new_chunks),
        file_hashes=new_hashes,
        chunk_counts=new_chunk_counts,
    )
    save_index(index_dir, new_chunks, manifest)
    return new_chunks, manifest
