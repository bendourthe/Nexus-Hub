"""Abstract base class for per-language AST extractors."""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from nexus_code_search.types import Edge, Node


class Extractor(ABC):
    """Abstract base every language extractor implements."""

    language: str = ""

    @abstractmethod
    def extract(self, file_path: Path, source: bytes) -> tuple[list[Node], list[Edge]]:
        """Parse `source` and return graph (nodes, edges) for this file.

        Implementations MUST return id=-1 for every Node and Edge (the
        orchestrator assigns ids when rows are flushed to SQLite). Edges that
        reference a node by name (cross-file `calls`, `imports` targets) MUST
        be resolved by the orchestrator post-parse - the extractor only emits
        local-resolution edges (e.g., a `calls` edge between two functions in
        the same file). When local resolution is impossible, omit the edge.
        """
        raise NotImplementedError
