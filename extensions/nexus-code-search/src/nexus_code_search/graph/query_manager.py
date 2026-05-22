"""Higher-level convenience wrappers over GraphTraverser.

These methods accept symbol names (vs. database ids) and disambiguate
multi-match results consistently.
"""

from __future__ import annotations

import sqlite3

from nexus_code_search.graph.traverser import GraphTraverser, _node_to_dict
from nexus_code_search.types import Node, NodeKind


class GraphQueryManager:
    """Name-keyed wrappers for the most common traversal queries."""

    def __init__(self, conn: sqlite3.Connection) -> None:
        self.conn = conn
        self.traverser = GraphTraverser(conn)

    def search(self, query: str, limit: int = 20) -> list[dict]:
        results = self.traverser.search_fts(query, limit=limit)
        return [_node_to_dict(n) for n in results]

    def callers_of(self, symbol: str, kind: NodeKind | None = None) -> dict:
        nodes = self._resolve_symbol(symbol, kind)
        out: list[dict] = []
        for n in nodes:
            for caller in self.traverser.callers(n.id):
                out.append(
                    {"target": _node_to_dict(n), "caller": _node_to_dict(caller)}
                )
        return {"symbol": symbol, "matches": len(nodes), "results": out}

    def callees_of(self, symbol: str, kind: NodeKind | None = None) -> dict:
        nodes = self._resolve_symbol(symbol, kind)
        out: list[dict] = []
        for n in nodes:
            for callee in self.traverser.callees(n.id):
                out.append(
                    {"caller": _node_to_dict(n), "callee": _node_to_dict(callee)}
                )
        return {"symbol": symbol, "matches": len(nodes), "results": out}

    def impact_of(
        self, symbol: str, depth: int = 2, kind: NodeKind | None = None
    ) -> dict:
        nodes = self._resolve_symbol(symbol, kind)
        results: list[dict] = []
        for n in nodes:
            radius = self.traverser.impact_radius(n.id, depth=depth)
            results.append(
                {"node": _node_to_dict(n), "impact": [_node_to_dict(m) for m in radius]}
            )
        return {
            "symbol": symbol,
            "depth": depth,
            "matches": len(nodes),
            "results": results,
        }

    def context_for(self, symbol: str, kind: NodeKind | None = None) -> dict:
        nodes = self._resolve_symbol(symbol, kind)
        results = [self.traverser.context_for(n.id) for n in nodes]
        return {"symbol": symbol, "matches": len(nodes), "results": results}

    def explore(self, symbol: str, depth: int = 2) -> dict:
        """Combine search, callers/callees, and impact into one payload."""
        matches = self.traverser.find_by_name(symbol)
        if not matches:
            matches = self.traverser.search_fts(symbol, limit=10)
        results = []
        for n in matches:
            results.append(
                {
                    "node": _node_to_dict(n),
                    "callers": [_node_to_dict(m) for m in self.traverser.callers(n.id)],
                    "callees": [_node_to_dict(m) for m in self.traverser.callees(n.id)],
                    "impact": [
                        _node_to_dict(m)
                        for m in self.traverser.impact_radius(n.id, depth=depth)
                    ],
                }
            )
        return {
            "symbol": symbol,
            "depth": depth,
            "matches": len(matches),
            "results": results,
        }

    def _resolve_symbol(self, symbol: str, kind: NodeKind | None) -> list[Node]:
        # Try exact qualified-name first, then plain name.
        node = self.traverser.find_by_qualified_name(symbol)
        if node is not None and (kind is None or node.kind == kind):
            return [node]
        return self.traverser.find_by_name(symbol, kind=kind)
