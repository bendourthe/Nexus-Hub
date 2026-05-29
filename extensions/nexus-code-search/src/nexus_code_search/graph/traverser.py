"""Read-only BFS traversal over the v2.0 nodes / edges schema.

Every public method on `GraphTraverser` is side-effect free: the constructor
takes an open `sqlite3.Connection` and the methods issue SELECT queries only.
The connection is owned by the caller.
"""

from __future__ import annotations

import sqlite3
from collections import deque

from nexus_code_search.types import EdgeKind, Node, NodeKind

# Edges followed by `impact_radius` - the set the caller of a function might
# care about when assessing change blast radius. `instantiates` is included so
# that re-typing a constructor call from `calls` (pre-v2.3.0) to `instantiates`
# does not silently drop the relationship from a node's impact radius.
_IMPACT_KINDS: tuple[str, ...] = (
    EdgeKind.CALLS.value,
    EdgeKind.INSTANTIATES.value,
    EdgeKind.REFERENCES.value,
    EdgeKind.EXTENDS.value,
    EdgeKind.IMPLEMENTS.value,
    EdgeKind.OVERRIDES.value,
)


def _scope_to_name(query: str) -> str:
    """Wrap a bare FTS5 query so it matches only the `name` column.

    Returns the query unchanged when it is empty or already uses FTS5
    column-filter syntax (contains a ':'), so advanced/explicit queries keep
    working. Otherwise wraps it as ``name : (<query>)`` so the match is
    restricted to the symbol-name column.
    """
    q = query.strip()
    if not q or ":" in q:
        return q
    return f"name : ({q})"


def _row_to_node(row: tuple) -> Node:
    return Node(
        id=row[0],
        name=row[1],
        kind=NodeKind(row[2]),
        qualified_name=row[3],
        file_path=row[4],
        start_line=row[5],
        end_line=row[6],
        signature=row[7],
        docstring=row[8],
    )


_NODE_SELECT = (
    "SELECT n.id, n.name, n.kind, n.qualified_name, f.path, n.start_line, n.end_line, n.signature, n.docstring "
    "FROM nodes n JOIN files f ON n.file_id = f.id"
)


class GraphTraverser:
    """Read-only graph traversal interface."""

    def __init__(self, conn: sqlite3.Connection) -> None:
        self.conn = conn

    def get_node(self, node_id: int) -> Node | None:
        row = self.conn.execute(f"{_NODE_SELECT} WHERE n.id = ?", (node_id,)).fetchone()
        return _row_to_node(row) if row else None

    def find_by_name(self, name: str, kind: NodeKind | None = None) -> list[Node]:
        if kind is None:
            rows = self.conn.execute(
                f"{_NODE_SELECT} WHERE n.name = ?", (name,)
            ).fetchall()
        else:
            rows = self.conn.execute(
                f"{_NODE_SELECT} WHERE n.name = ? AND n.kind = ?", (name, kind.value)
            ).fetchall()
        return [_row_to_node(r) for r in rows]

    def find_by_qualified_name(self, qualified_name: str) -> Node | None:
        row = self.conn.execute(
            f"{_NODE_SELECT} WHERE n.qualified_name = ?", (qualified_name,)
        ).fetchone()
        return _row_to_node(row) if row else None

    def search_fts(
        self, query: str, limit: int = 20, *, all_columns: bool = False
    ) -> list[Node]:
        """Full-text search over graph node names.

        By default the match is scoped to the `name` column. A symbol search
        should surface symbols *named* like the query, not every node whose
        `qualified_name` happens to contain the query as an ancestor segment
        (a function's parameters and methods all carry the function name in
        their qualified_name) nor docstring prose. Scoping to `name` removes
        that false-positive class without dropping recall on real symbol
        queries.

        Pass `all_columns=True` to match name + qualified_name + docstring
        (the pre-v2.3.0 behavior), e.g. for docstring or path-segment search.
        """
        match_query = query if all_columns else _scope_to_name(query)
        rows = self.conn.execute(
            f"{_NODE_SELECT} JOIN nodes_fts ON nodes_fts.rowid = n.id "
            f"WHERE nodes_fts MATCH ? ORDER BY rank LIMIT ?",
            (match_query, limit),
        ).fetchall()
        return [_row_to_node(r) for r in rows]

    def callers(self, node_id: int) -> list[Node]:
        """Return every node with a `calls` edge whose target is `node_id`."""
        rows = self.conn.execute(
            f"{_NODE_SELECT} JOIN edges e ON e.source_id = n.id "
            f"WHERE e.target_id = ? AND e.kind = ?",
            (node_id, EdgeKind.CALLS.value),
        ).fetchall()
        return [_row_to_node(r) for r in rows]

    def callees(self, node_id: int) -> list[Node]:
        """Return every node `node_id` has a `calls` edge to."""
        rows = self.conn.execute(
            f"{_NODE_SELECT} JOIN edges e ON e.target_id = n.id "
            f"WHERE e.source_id = ? AND e.kind = ?",
            (node_id, EdgeKind.CALLS.value),
        ).fetchall()
        return [_row_to_node(r) for r in rows]

    def impact_radius(self, node_id: int, depth: int = 2) -> list[Node]:
        """Return every node reachable from `node_id` along impact-bearing
        edges up to `depth` hops, walking both directions.

        The traversal follows reverse-`calls` (who-calls-me, transitively),
        `references`, and structural relations (`extends`, `implements`,
        `overrides`). Order is BFS; the result list omits the seed node.
        """
        if depth < 1:
            return []

        visited: set[int] = {node_id}
        queue: deque[tuple[int, int]] = deque([(node_id, 0)])
        results: list[int] = []
        placeholders = ",".join("?" for _ in _IMPACT_KINDS)
        while queue:
            cur_id, cur_depth = queue.popleft()
            if cur_depth >= depth:
                continue
            # Walk both directions: callers (reverse calls) + extenders.
            rows = self.conn.execute(
                f"SELECT source_id FROM edges WHERE target_id = ? AND kind IN ({placeholders})",
                (cur_id, *_IMPACT_KINDS),
            ).fetchall()
            rows.extend(
                self.conn.execute(
                    f"SELECT target_id FROM edges WHERE source_id = ? AND kind IN ({placeholders})",
                    (cur_id, *_IMPACT_KINDS),
                ).fetchall()
            )
            for (neighbor_id,) in rows:
                if neighbor_id in visited:
                    continue
                visited.add(neighbor_id)
                results.append(neighbor_id)
                queue.append((neighbor_id, cur_depth + 1))

        if not results:
            return []
        placeholders_ids = ",".join("?" for _ in results)
        rows = self.conn.execute(
            f"{_NODE_SELECT} WHERE n.id IN ({placeholders_ids})", tuple(results)
        ).fetchall()
        return [_row_to_node(r) for r in rows]

    def find_path(
        self, source_id: int, target_id: int, max_depth: int = 6
    ) -> list[Node]:
        """Shortest path from source to target along outgoing edges. Empty
        list when no path within `max_depth`."""
        if source_id == target_id:
            node = self.get_node(source_id)
            return [node] if node else []
        # BFS over outgoing edges; remember predecessor for reconstruction.
        visited: dict[int, int | None] = {source_id: None}
        queue: deque[tuple[int, int]] = deque([(source_id, 0)])
        while queue:
            cur, depth = queue.popleft()
            if depth >= max_depth:
                continue
            rows = self.conn.execute(
                "SELECT target_id FROM edges WHERE source_id = ?", (cur,)
            ).fetchall()
            for (nxt,) in rows:
                if nxt in visited:
                    continue
                visited[nxt] = cur
                if nxt == target_id:
                    return self._reconstruct_path(visited, target_id)
                queue.append((nxt, depth + 1))
        return []

    def context_for(self, node_id: int) -> dict:
        """Return a context-window summary for a node: itself + callers (1
        hop), callees (1 hop), and the file's other top-level nodes."""
        node = self.get_node(node_id)
        if node is None:
            return {}
        callers = self.callers(node_id)
        callees = self.callees(node_id)
        siblings = self._siblings(node)
        return {
            "node": _node_to_dict(node),
            "callers": [_node_to_dict(n) for n in callers],
            "callees": [_node_to_dict(n) for n in callees],
            "siblings": [_node_to_dict(n) for n in siblings],
        }

    def _siblings(self, node: Node) -> list[Node]:
        # Top-level siblings = nodes contained by the same module as `node`.
        rows = self.conn.execute(
            f"{_NODE_SELECT} JOIN edges e ON e.target_id = n.id "
            f"WHERE e.kind = ? AND e.source_id IN ("
            f"  SELECT source_id FROM edges WHERE target_id = ? AND kind = ?"
            f") AND n.id != ?",
            (EdgeKind.CONTAINS.value, node.id, EdgeKind.CONTAINS.value, node.id),
        ).fetchall()
        return [_row_to_node(r) for r in rows]

    def _reconstruct_path(
        self, visited: dict[int, int | None], target_id: int
    ) -> list[Node]:
        # Walk predecessor links back to source, then reverse.
        ids: list[int] = []
        cur: int | None = target_id
        while cur is not None:
            ids.append(cur)
            cur = visited.get(cur)
        ids.reverse()
        if not ids:
            return []
        placeholders = ",".join("?" for _ in ids)
        rows = self.conn.execute(
            f"{_NODE_SELECT} WHERE n.id IN ({placeholders})", tuple(ids)
        ).fetchall()
        by_id = {r[0]: _row_to_node(r) for r in rows}
        return [by_id[i] for i in ids if i in by_id]


def _node_to_dict(node: Node) -> dict:
    return {
        "id": node.id,
        "name": node.name,
        "kind": node.kind.value,
        "qualified_name": node.qualified_name,
        "file_path": node.file_path,
        "start_line": node.start_line,
        "end_line": node.end_line,
        "signature": node.signature,
        "docstring": node.docstring,
    }
