"""Nexus-Hub persistent agent-memory store.

Append-only fixed-width log, cross-platform write locking, and crash
recovery. Compression is performed by the calling agent, never by this
package. Runtime is the Python standard library only: zero outbound
calls, zero API keys, zero model downloads.
"""

from __future__ import annotations

from .config import (
    InRepoStoreError,
    StoreConfig,
    default_store_root,
    load_config,
    save_config,
)
from .store import (
    BlankRecordError,
    CorruptTailError,
    EntryTooLongError,
    MemoryStore,
    WidthMismatchError,
)
from .tiling import tile
from .tree import MissingChildError, TreeStore

__version__ = "3.19.1"

__all__ = [
    "BlankRecordError",
    "CorruptTailError",
    "EntryTooLongError",
    "InRepoStoreError",
    "MemoryStore",
    "MissingChildError",
    "StoreConfig",
    "TreeStore",
    "WidthMismatchError",
    "default_store_root",
    "load_config",
    "save_config",
    "tile",
]
