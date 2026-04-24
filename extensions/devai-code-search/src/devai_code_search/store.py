"""Persistence layer for the code-search index.

Two artifacts are written to the index directory:

- `chunks.pickle` - the pickled list of Chunk objects (one per file+chunk).
- `manifest.json` - the JSON IndexManifest describing the indexed files.

A lockfile `index.lock` guards concurrent indexers. On Windows `msvcrt.locking`
is used; on POSIX `fcntl.flock`. Both are advisory.
"""
from __future__ import annotations

import json
import logging
import os
import pickle
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from devai_code_search.types import Chunk, IndexManifest

logger = logging.getLogger("devai-code-search")

CHUNKS_FILENAME = "chunks.pickle"
MANIFEST_FILENAME = "manifest.json"
LOCK_FILENAME = "index.lock"


def save_index(index_dir: Path, chunks: list[Chunk], manifest: IndexManifest) -> None:
    """Persist chunks + manifest atomically (relative to index_dir)."""
    index_dir.mkdir(parents=True, exist_ok=True)

    chunks_path = index_dir / CHUNKS_FILENAME
    manifest_path = index_dir / MANIFEST_FILENAME

    chunks_tmp = chunks_path.with_suffix(chunks_path.suffix + ".tmp")
    manifest_tmp = manifest_path.with_suffix(manifest_path.suffix + ".tmp")

    with open(chunks_tmp, "wb") as f:
        pickle.dump(chunks, f, protocol=pickle.HIGHEST_PROTOCOL)

    with open(manifest_tmp, "w", encoding="utf-8") as f:
        json.dump(manifest.to_dict(), f, indent=2)

    os.replace(chunks_tmp, chunks_path)
    os.replace(manifest_tmp, manifest_path)


def load_index(index_dir: Path) -> tuple[list[Chunk], IndexManifest | None]:
    """Load chunks + manifest.

    Returns ([], None) if the index does not exist. On corruption, logs a
    warning and returns ([], None) so the caller can fall back to a full re-index.
    """
    chunks_path = index_dir / CHUNKS_FILENAME
    manifest_path = index_dir / MANIFEST_FILENAME

    if not chunks_path.exists() or not manifest_path.exists():
        return [], None

    try:
        with open(chunks_path, "rb") as f:
            chunks = pickle.load(f)
        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest = IndexManifest.from_dict(json.load(f))
    except (pickle.UnpicklingError, json.JSONDecodeError, KeyError, OSError) as exc:
        logger.warning("Index at %s is corrupt (%s); treating as empty", index_dir, exc)
        return [], None

    return chunks, manifest


def clear_index(index_dir: Path) -> bool:
    """Remove the index directory. Returns True if anything was removed."""
    if not index_dir.exists():
        return False

    for name in (CHUNKS_FILENAME, MANIFEST_FILENAME, LOCK_FILENAME):
        target = index_dir / name
        if target.exists():
            try:
                target.unlink()
            except OSError as exc:
                logger.warning("Could not remove %s: %s", target, exc)

    try:
        index_dir.rmdir()
    except OSError:
        # Directory not empty (e.g. user added extra files); leave it.
        pass

    return True


@contextmanager
def index_lock(index_dir: Path) -> Iterator[None]:
    """Acquire an advisory lock on `<index_dir>/index.lock`.

    Uses fcntl on POSIX and msvcrt on Windows. Raises `BlockingIOError`
    (or equivalent) if the lock is already held. Callers should handle
    that by returning a 'concurrent index running' status.
    """
    index_dir.mkdir(parents=True, exist_ok=True)
    lock_path = index_dir / LOCK_FILENAME
    fh = open(lock_path, "a+b")
    try:
        _lock_file(fh)
        try:
            yield
        finally:
            _unlock_file(fh)
    finally:
        fh.close()


def _lock_file(fh) -> None:
    if os.name == "nt":
        import msvcrt

        # Seek to 0 and lock 1 byte (msvcrt requires a non-zero region).
        fh.seek(0)
        # Ensure the file is at least 1 byte so locking has a region to hold.
        fh.write(b"\x00")
        fh.flush()
        fh.seek(0)
        msvcrt.locking(fh.fileno(), msvcrt.LK_NBLCK, 1)
    else:
        import fcntl

        fcntl.flock(fh.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)


def _unlock_file(fh) -> None:
    if os.name == "nt":
        import msvcrt

        try:
            fh.seek(0)
            msvcrt.locking(fh.fileno(), msvcrt.LK_UNLCK, 1)
        except OSError:
            pass
    else:
        import fcntl

        fcntl.flock(fh.fileno(), fcntl.LOCK_UN)
