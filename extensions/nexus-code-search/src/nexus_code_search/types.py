"""Data types for the code-search server. Pure data-plumbing; no logic."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class IndexState(str, Enum):
    """Current state of the indexer for a given root."""

    IDLE = "idle"
    RUNNING = "running"
    ERROR = "error"


@dataclass(frozen=True)
class Chunk:
    """A single chunk of source code with provenance."""

    file_path: str
    start_line: int
    end_line: int
    text: str


@dataclass
class IndexManifest:
    """Manifest written alongside the pickled index.

    `file_hashes` maps relative file paths (POSIX-style, forward slashes) to SHA-256 hex digests.
    `chunk_counts` maps relative file paths to the number of chunks the file produced.
    """

    root: str
    indexed_at: str
    total_chunks: int
    file_hashes: dict[str, str] = field(default_factory=dict)
    chunk_counts: dict[str, int] = field(default_factory=dict)
    version: str = "1.0.0"

    def to_dict(self) -> dict:
        return {
            "root": self.root,
            "indexed_at": self.indexed_at,
            "total_chunks": self.total_chunks,
            "file_hashes": self.file_hashes,
            "chunk_counts": self.chunk_counts,
            "version": self.version,
        }

    @classmethod
    def from_dict(cls, data: dict) -> IndexManifest:
        return cls(
            root=data["root"],
            indexed_at=data["indexed_at"],
            total_chunks=data["total_chunks"],
            file_hashes=dict(data.get("file_hashes", {})),
            chunk_counts=dict(data.get("chunk_counts", {})),
            version=data.get("version", "1.0.0"),
        )


@dataclass(frozen=True)
class SearchResult:
    """A single search result ranked by score."""

    chunk: Chunk
    score: float
    rank: int


@dataclass
class IndexStatus:
    """Pollable status of an indexing operation."""

    root: str
    state: IndexState
    files_processed: int = 0
    total_files: int = 0
    last_updated: Optional[str] = None
    error: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "root": self.root,
            "state": self.state.value,
            "files_processed": self.files_processed,
            "total_files": self.total_files,
            "last_updated": self.last_updated,
            "error": self.error,
        }
