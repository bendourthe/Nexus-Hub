"""Route extraction over the AST graph.

Reads the `route` nodes the framework resolvers (FastAPI / Flask / Django /
Express) already emit at index time, and enriches each into a structured
:class:`RouteInfo`: framework, HTTP method, path, URL parameters, the resolved
handler, and coarse behavior tags inferred from the handler's source.

This is a read-only post-graph pass - it adds no new resolver and reimplements
nothing framework-specific beyond parsing the already-emitted route labels, so
it inherits whatever framework coverage the extraction layer provides.
"""

from __future__ import annotations

import re
import sqlite3
from pathlib import Path

from nexus_code_search.contextmap.behavior import infer_behavior_tags
from nexus_code_search.contextmap.model import RouteInfo

# Handler-linking edges emitted by the resolvers: FastAPI uses `decorates`,
# Express / Django use `references`.
_HANDLER_EDGE_KINDS = ("decorates", "references")

# URL-parameter syntaxes across the supported frameworks, unioned:
#   {name} / {name:conv}   FastAPI, Flask (curly)
#   <name> / <conv:name>   Django, Flask (angle)
#   :name                  Express
#   (?P<name>...)          Django regex named groups
_PARAM_PATTERNS = (
    re.compile(r"\{([a-zA-Z_]\w*)"),
    re.compile(r"\(\?P<([a-zA-Z_]\w*)>"),
    re.compile(r"<(?:[a-zA-Z_]\w*:)?([a-zA-Z_]\w*)>"),
    re.compile(r":([a-zA-Z_]\w*)"),
)


def extract_routes(conn: sqlite3.Connection, root: Path) -> list[RouteInfo]:
    """Return every route in the graph as an enriched :class:`RouteInfo`."""
    cur = conn.cursor()
    files_by_id: dict[int, str] = {
        fid: path for fid, path in cur.execute("SELECT id, path FROM files")
    }
    route_rows = cur.execute(
        "SELECT id, name, qualified_name, file_id, start_line, end_line "
        "FROM nodes WHERE kind = 'route'"
    ).fetchall()

    source_cache: dict[str, list[str]] = {}
    routes: list[RouteInfo] = []
    for route_id, name, qualified_name, file_id, start_line, end_line in route_rows:
        framework = qualified_name.split(":", 1)[0] if ":" in qualified_name else ""
        method, path = _split_method_path(framework, name)
        route_file = files_by_id.get(file_id, "")
        handler, handler_file, tags = _resolve_handler(
            cur,
            route_id,
            files_by_id,
            root,
            source_cache,
            route_file=route_file,
            route_start=start_line,
            route_end=end_line,
        )
        routes.append(
            RouteInfo(
                framework=framework,
                method=method,
                path=path,
                params=tuple(_extract_params(path)),
                handler=handler,
                handler_file=handler_file,
                behavior_tags=tags,
                source_file=files_by_id.get(file_id, ""),
            )
        )

    routes.sort(key=lambda r: (r.source_file, r.method, r.path))
    return routes


def _split_method_path(framework: str, label: str) -> tuple[str, str]:
    """Split a route node label into (method, path).

    FastAPI / Express labels are `<METHOD> <path>`. Django labels are the raw
    URL pattern (no method); `include:` labels name a nested URL conf.
    """
    if framework == "django":
        if label.startswith("include:"):
            return "INCLUDE", label[len("include:") :]
        return "ANY", label
    if " " in label:
        method, path = label.split(" ", 1)
        return method.upper(), path
    return "ANY", label


def _extract_params(path: str) -> list[str]:
    """Return the ordered, de-duplicated URL parameters in ``path``."""
    seen: list[str] = []
    for pattern in _PARAM_PATTERNS:
        for match in pattern.finditer(path):
            name = match.group(1)
            if name not in seen:
                seen.append(name)
    return seen


def _resolve_handler(
    cur: sqlite3.Cursor,
    route_id: int,
    files_by_id: dict[int, str],
    root: Path,
    source_cache: dict[str, list[str]],
    *,
    route_file: str,
    route_start: int,
    route_end: int,
) -> tuple[str, str, tuple[str, ...]]:
    """Resolve a route's handler and infer its behavior tags.

    The handler is the LAST edge target (Express emits a `references` edge per
    positional arg - middleware first, the handler last; FastAPI / Django emit a
    single edge). Behavior tags are inferred from the UNION of the resolved
    handler's source and the route node's own span, so inline handlers (an
    Express arrow whose body lives inside the route call, with no separate
    node) are still tagged. Returns handler="" when no named handler resolves.
    """
    placeholders = ", ".join("?" for _ in _HANDLER_EDGE_KINDS)
    rows = cur.execute(
        f"SELECT target_id FROM edges WHERE source_id = ? AND kind IN ({placeholders}) "
        "ORDER BY id",
        (route_id, *_HANDLER_EDGE_KINDS),
    ).fetchall()

    # Always available: the route node's own source span (covers an inline
    # Express handler body).
    route_span = _source_slice(root, route_file, route_start, route_end, source_cache)

    handler = ""
    handler_file = route_file
    handler_slice = ""
    if rows:
        node = cur.execute(
            "SELECT name, qualified_name, file_id, start_line, end_line FROM nodes "
            "WHERE id = ?",
            (rows[-1][0],),
        ).fetchone()
        if node is not None:
            name, qualified_name, file_id, start_line, end_line = node
            handler = qualified_name or name
            handler_file = files_by_id.get(file_id, route_file)
            handler_slice = _source_slice(
                root, handler_file, start_line, end_line, source_cache
            )

    tags = infer_behavior_tags(f"{handler_slice}\n{route_span}")
    return handler, handler_file, tags


def _source_slice(
    root: Path,
    rel_path: str,
    start_line: int,
    end_line: int,
    source_cache: dict[str, list[str]],
) -> str:
    if not rel_path:
        return ""
    lines = source_cache.get(rel_path)
    if lines is None:
        try:
            lines = (
                (root / rel_path)
                .read_text(encoding="utf-8", errors="replace")
                .splitlines()
            )
        except OSError:
            lines = []
        source_cache[rel_path] = lines
    start = max(start_line, 1)
    return "\n".join(lines[start - 1 : end_line])
