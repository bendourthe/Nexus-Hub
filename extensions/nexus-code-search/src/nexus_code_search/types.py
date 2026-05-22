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


class NodeKind(str, Enum):
    """Symbol kinds emitted by the AST extractors.

    Mirrors the cloned-codegraph reference (src/types.ts) so future cross-graph
    diffs against that project's evaluation corpora stay one-to-one. The set is
    fixed in v2.0 - adding a kind requires a schema migration since `kind` is
    stored as a TEXT column.
    """

    FILE = "file"
    MODULE = "module"
    CLASS = "class"
    STRUCT = "struct"
    INTERFACE = "interface"
    TRAIT = "trait"
    PROTOCOL = "protocol"
    FUNCTION = "function"
    METHOD = "method"
    PROPERTY = "property"
    FIELD = "field"
    VARIABLE = "variable"
    CONSTANT = "constant"
    ENUM = "enum"
    ENUM_MEMBER = "enum_member"
    TYPE_ALIAS = "type_alias"
    NAMESPACE = "namespace"
    PARAMETER = "parameter"
    IMPORT = "import"
    EXPORT = "export"
    ROUTE = "route"
    COMPONENT = "component"


class EdgeKind(str, Enum):
    """Edge kinds emitted by the AST extractors + graph traverser.

    `calls` and `imports` carry most of the call-graph weight. The full set
    follows codegraph's taxonomy so framework resolvers (Django / FastAPI /
    Express in Phase 5) can reuse the same edges without bespoke kinds.
    """

    CONTAINS = "contains"
    CALLS = "calls"
    IMPORTS = "imports"
    EXPORTS = "exports"
    EXTENDS = "extends"
    IMPLEMENTS = "implements"
    REFERENCES = "references"
    TYPE_OF = "type_of"
    RETURNS = "returns"
    INSTANTIATES = "instantiates"
    OVERRIDES = "overrides"
    DECORATES = "decorates"


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


@dataclass(frozen=True)
class Node:
    """An AST graph node persisted to SQLite.

    `id` is the database primary key (-1 for in-memory nodes not yet flushed).
    `qualified_name` is the dotted path the symbol is reachable by from the
    file root (e.g. `pkg.module.Class.method`). It is the join key when one
    extractor needs to reference a symbol another extractor produced.
    """

    name: str
    kind: NodeKind
    qualified_name: str
    file_path: str
    start_line: int
    end_line: int
    signature: str = ""
    docstring: str = ""
    id: int = -1


@dataclass(frozen=True)
class Edge:
    """An AST graph edge persisted to SQLite.

    `source_id` and `target_id` are Node ids. `call_site_line` is the 1-indexed
    line where the call / reference appears (0 if the edge has no line origin -
    e.g. a structural `contains` edge from a file to a top-level symbol).
    """

    source_id: int
    target_id: int
    kind: EdgeKind
    call_site_line: int = 0
    id: int = -1
