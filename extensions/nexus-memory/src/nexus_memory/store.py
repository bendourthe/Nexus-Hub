"""Append-only fixed-width entry log.

Every record is padded to ``record_width`` bytes so record N lives at
offset N times the width. Lookup is one seek. There is no index file.
The on-disk cost is roughly 2x versus a packed log; constant-time access
and crash-safe repair are the reason.

Records are binary. The reader and writer force UTF-8 for the payload
regardless of the process locale. An entry longer than ``max_entry_length``
is rejected, never silently truncated. Existing records are never rewritten.
"""

from __future__ import annotations

import struct
from pathlib import Path

from .config import (
    StoreConfig,
    assert_root_allowed,
    default_store_root,
    load_config,
    restrict_private,
    save_config,
    write_marker,
)
from .lock import FileLock

LOG_NAME = "entries.log"
LOCK_NAME = "entries.lock"
_LENGTH = struct.Struct("<I")


class EntryTooLongError(ValueError):
    """The entry exceeds ``max_entry_length`` and was not written."""


class BlankRecordError(ValueError):
    """A complete record is empty or malformed; repair rather than guess."""


class CorruptTailError(ValueError):
    """The log length is not a multiple of the record width."""


class WidthMismatchError(ValueError):
    """The on-disk log does not match the configured record width."""


class MemoryStore:
    """One append-only log under a store root."""

    def __init__(
        self,
        root: Path | None = None,
        config: StoreConfig | None = None,
    ) -> None:
        self.root = Path(root) if root is not None else default_store_root()
        existing = self.root / "config.json"
        creating = not existing.is_file()
        if creating:
            assert_root_allowed(self.root)
        self.root.mkdir(parents=True, exist_ok=True)
        restrict_private(self.root)
        write_marker(self.root)
        self.config = config if config is not None else load_config(self.root)
        self.config.validate()
        if creating:
            save_config(self.root, self.config)
        self.log_path = self.root / LOG_NAME
        self.lock_path = self.root / LOCK_NAME

    @property
    def width(self) -> int:
        return self.config.record_width

    def count(self) -> int:
        """Return the number of complete records. A leftover tail is not counted."""
        if not self.log_path.is_file():
            return 0
        size = self.log_path.stat().st_size
        return size // self.width

    def append(self, text: str) -> int:
        """Append *text* and return its 0-based index."""
        payload = text.encode("utf-8")
        if len(payload) > self.config.max_entry_length:
            raise EntryTooLongError(
                f"entry is {len(payload)} bytes; max_entry_length is "
                f"{self.config.max_entry_length}"
            )
        record = self._pack(payload)
        assert_root_allowed(self.root)
        with FileLock(self.lock_path):
            self._assert_width_or_empty()
            with open(self.log_path, "ab") as fh:
                fh.write(record)
                fh.flush()
                os_fsync(fh.fileno())
            restrict_private(self.log_path)
            restrict_private(self.lock_path)
            return self.count() - 1

    def get(self, index: int) -> str:
        """Return the entry at *index*. Raises on a blank or short record."""
        if index < 0:
            raise IndexError(f"index must be >= 0, got {index}")
        n = self.count()
        if index >= n:
            raise IndexError(f"index {index} is past the last record ({n})")
        with open(self.log_path, "rb") as fh:
            fh.seek(index * self.width)
            raw = fh.read(self.width)
        if len(raw) != self.width:
            raise BlankRecordError(self._recovery("a short record was read"))
        return self._unpack(raw, index)

    def slice(self, lo: int, hi: int) -> list[str]:
        """Return entries ``[lo, hi)``."""
        if lo < 0 or hi < lo:
            raise IndexError(f"invalid slice [{lo}, {hi})")
        return [self.get(i) for i in range(lo, min(hi, self.count()))]

    def repair(self) -> int:
        """Truncate a non-integral tail. Never touch a complete prior record.

        Returns the number of bytes removed. A clean log returns 0.
        """
        if not self.log_path.is_file():
            return 0
        with FileLock(self.lock_path):
            size = self.log_path.stat().st_size
            remainder = size % self.width
            if remainder == 0:
                return 0
            keep = size - remainder
            with open(self.log_path, "r+b") as fh:
                fh.truncate(keep)
                fh.flush()
                os_fsync(fh.fileno())
            return remainder

    def _pack(self, payload: bytes) -> bytes:
        record = _LENGTH.pack(len(payload)) + payload
        if len(record) > self.width:
            raise EntryTooLongError(
                f"packed record is {len(record)} bytes; record_width is {self.width}"
            )
        return record + (b"\x00" * (self.width - len(record)))

    def _unpack(self, raw: bytes, index: int) -> str:
        (length,) = _LENGTH.unpack(raw[:4])
        if length > self.width - 4:
            raise BlankRecordError(
                self._recovery(f"record {index} has an impossible length {length}")
            )
        payload = raw[4 : 4 + length]
        if len(payload) != length:
            raise BlankRecordError(
                self._recovery(f"record {index} is truncated inside its payload")
            )
        try:
            return payload.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise BlankRecordError(
                self._recovery(f"record {index} is not valid UTF-8")
            ) from exc

    def _assert_width_or_empty(self) -> None:
        if not self.log_path.is_file():
            return
        size = self.log_path.stat().st_size
        if size == 0:
            return
        if size % self.width != 0:
            raise CorruptTailError(
                self._recovery(
                    f"log length {size} is not a multiple of record_width "
                    f"{self.width}"
                )
            )

    def _recovery(self, reason: str) -> str:
        return (
            f"{reason}. Recover with: python -m nexus_memory repair --root "
            f"{self.root}"
        )


def os_fsync(fd: int) -> None:
    """fsync *fd*; imported locally so the module stays stdlib-only."""
    import os

    os.fsync(fd)
