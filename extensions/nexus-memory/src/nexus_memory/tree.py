"""Summary-tree cache over the entry log.

One file per level (ranges of size 2, 4, 8, ...). Each file is a dense
prefix of fixed-width summary records, so a level's byte length tells
you exactly how far compression has progressed at that level. The whole
structure is a cache: deleting it loses no entries.

Pending work is the next unbuilt range at each level, listed
smallest-first, using one length check per level and never a scan.
Pending count is the same total without materializing the list, and
each level clamps at zero because entries keep arriving while an agent
reads.
"""

from __future__ import annotations

import struct
from pathlib import Path

from .config import restrict_private
from .lock import FileLock
from .store import os_fsync

TREE_DIR = "tree"
_LENGTH = struct.Struct("<I")


class MissingChildError(ValueError):
    """A merge was requested whose child summary is missing or blank."""


class TreeStore:
    """On-disk cache of range summaries."""

    def __init__(self, root: Path, *, record_width: int, log_count: int) -> None:
        if record_width < 32:
            raise ValueError("record_width must be >= 32")
        self.root = Path(root)
        self.tree_dir = self.root / TREE_DIR
        self.width = record_width
        self.log_count = log_count
        self.tree_dir.mkdir(parents=True, exist_ok=True)
        restrict_private(self.tree_dir)
        self._lock = FileLock(self.tree_dir / "tree.lock")

    def put(self, lo: int, hi: int, text: str) -> None:
        """Write the summary for an aligned power-of-two range ``[lo, hi)``."""
        size = _validate_range(lo, hi)
        payload = text.encode("utf-8")
        if 4 + len(payload) > self.width:
            raise ValueError(
                f"summary is {len(payload)} bytes; record_width is {self.width}"
            )
        record = _LENGTH.pack(len(payload)) + payload
        record += b"\x00" * (self.width - len(record))
        path = self._level_path(size)
        index = lo // size
        with self._lock:
            built = self._built(path)
            if index > built:
                raise ValueError(
                    f"range [{lo}, {hi}) is past the dense prefix "
                    f"(next index is {built})"
                )
            if index < built:
                raise ValueError(
                    f"range [{lo}, {hi}) is already written; drop it first"
                )
            with open(path, "ab") as fh:
                fh.write(record)
                fh.flush()
                os_fsync(fh.fileno())
            restrict_private(path)

    def get(self, lo: int, hi: int) -> str | None:
        """Return the summary for ``[lo, hi)``, or None if it is not built."""
        size = _validate_range(lo, hi)
        path = self._level_path(size)
        index = lo // size
        with self._lock:
            built = self._built(path)
            if index >= built:
                return None
            with open(path, "rb") as fh:
                fh.seek(index * self.width)
                raw = fh.read(self.width)
        if len(raw) != self.width:
            return None
        (length,) = _LENGTH.unpack(raw[:4])
        if length == 0 or length > self.width - 4:
            return None
        payload = raw[4 : 4 + length]
        if len(payload) != length:
            return None
        text = payload.decode("utf-8")
        if not text.strip():
            return None
        return text

    def drop(self, lo: int, hi: int) -> None:
        """Discard ``[lo, hi)`` and every later record at that level.

        Dense-prefix storage cannot punch a hole, so dropping a range
        also drops the suffix after it. Those ranges become pending again
        and rebuild from the log.
        """
        size = _validate_range(lo, hi)
        path = self._level_path(size)
        index = lo // size
        with self._lock:
            built = self._built(path)
            if index >= built:
                return
            keep = index * self.width
            with open(path, "r+b") as fh:
                fh.truncate(keep)
                fh.flush()
                os_fsync(fh.fileno())

    def pending(self) -> list[tuple[int, int]]:
        """Buildable-but-unbuilt ranges, smallest-first."""
        out: list[tuple[int, int]] = []
        for size in _level_sizes(self.log_count):
            item = self._next_pending(size)
            if item is not None:
                out.append(item)
        return out

    def pending_count(self) -> int:
        """Same total as ``len(pending())`` without materializing the list."""
        total = 0
        for size in _level_sizes(self.log_count):
            if self._next_pending(size) is not None:
                total += 1
        return max(total, 0)

    def children_ready(self, lo: int, hi: int) -> bool:
        """True when both children exist so this range may be merged."""
        size = hi - lo
        if size == 2:
            return self.log_count >= hi
        mid = lo + size // 2
        left = self.get(lo, mid)
        right = self.get(mid, hi)
        return bool(left) and bool(right)

    def child_contents(self, lo: int, hi: int) -> tuple[str, str]:
        """Return the two child texts, or raise ``MissingChildError``."""
        size = hi - lo
        mid = lo + size // 2
        if size == 2:
            raise MissingChildError(
                "size-2 merges read entries from the log, not the tree"
            )
        left = self.get(lo, mid)
        right = self.get(mid, hi)
        if not left or not right:
            raise MissingChildError(
                f"child summary missing for [{lo}, {hi}). Recover with: "
                f"python -m nexus_memory drop --lo {lo} --hi {hi}"
            )
        return left, right

    def _next_pending(self, size: int) -> tuple[int, int] | None:
        path = self._level_path(size)
        built = self._built(path)
        possible = self.log_count // size
        remaining = possible - built
        if remaining <= 0:
            return None
        lo = built * size
        hi = lo + size
        if not self.children_ready(lo, hi):
            return None
        return (lo, hi)

    def _built(self, path: Path) -> int:
        if not path.is_file():
            return 0
        return path.stat().st_size // self.width

    def _level_path(self, size: int) -> Path:
        return self.tree_dir / f"level_{size}"


def _validate_range(lo: int, hi: int) -> int:
    if lo < 0 or hi <= lo:
        raise ValueError(f"invalid range [{lo}, {hi})")
    size = hi - lo
    if size & (size - 1):
        raise ValueError(f"range size {size} is not a power of two")
    if lo % size != 0:
        raise ValueError(f"range [{lo}, {hi}) is not aligned")
    return size


def _level_sizes(n: int) -> list[int]:
    """Level sizes from 2 up to the largest power of two that can cover n."""
    sizes: list[int] = []
    size = 2
    while size <= n:
        sizes.append(size)
        size *= 2
    return sizes
