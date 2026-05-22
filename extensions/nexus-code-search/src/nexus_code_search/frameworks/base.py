"""Abstract base for framework route resolvers."""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from nexus_code_search.types import Edge, Node


class FrameworkResolver(ABC):
    """Abstract base every framework resolver implements.

    Resolvers are invoked once per source file, AFTER per-language AST
    extraction. They receive the file path, raw source bytes, and the list of
    AST nodes the extractor already produced. They return additional
    `(nodes, edges)` to merge into the per-file output.

    The new nodes use local indices that continue from `len(existing_nodes)`,
    and edges may reference both the new framework nodes (by local index
    relative to the framework output) AND the existing AST nodes (by index
    into `existing_nodes`). The orchestrator threads both index spaces into
    the SQLite flush so the resolver does not need to know about database
    ids.
    """

    name: str = ""

    @abstractmethod
    def applies_to(self, file_path: Path) -> bool:
        """Return True when this resolver should be invoked for `file_path`."""
        raise NotImplementedError

    @abstractmethod
    def resolve(
        self,
        file_path: Path,
        source: bytes,
        ast_nodes: list[Node],
    ) -> tuple[list[Node], list[Edge]]:
        """Emit framework-specific `(nodes, edges)` for this file.

        Edge `source_id` / `target_id` semantics:
          - target_id values in [0, len(ast_nodes)) reference an existing AST
            node (the handler function the route points at).
          - source_id / target_id values in [len(ast_nodes), len(ast_nodes) +
            len(new_nodes)) reference a node emitted by this resolver (the
            route node itself).

        The orchestrator translates both index spaces to SQLite primary keys
        before writing edges.
        """
        raise NotImplementedError
