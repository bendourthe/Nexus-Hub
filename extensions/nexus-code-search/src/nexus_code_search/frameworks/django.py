"""Django URL-conf framework resolver.

Recognizes the four canonical URL-binding helpers in Django's `urls.py`
files:

    path('users/<int:id>/', views.user_detail, name='user-detail')
    re_path(r'^articles/(?P<year>[0-9]{4})/$', views.year_archive)
    url(r'^foo/$', views.foo)              # Django <2.0 legacy
    include('myapp.urls')                  # nested include

Plus the `MyView.as_view()` pattern that wraps class-based views into
callable handlers.

Emits one `route` node per detected pattern (name = the URL pattern itself,
qualified_name = `<METHOD> <path>` when a method is implied via decorator,
otherwise just the pattern) and a `references` edge from the route to the
handler symbol (when the handler resolves locally in `ast_nodes`).
"""

from __future__ import annotations

import logging
from pathlib import Path

import tree_sitter_python
from tree_sitter import Language, Node as TSNode, Parser

from nexus_code_search.frameworks.base import FrameworkResolver
from nexus_code_search.types import Edge, EdgeKind, Node, NodeKind

logger = logging.getLogger("nexus-code-search")

_PY_LANGUAGE = Language(tree_sitter_python.language())
_PY_PARSER = Parser(_PY_LANGUAGE)

_ROUTE_FUNCS: frozenset[str] = frozenset({"path", "re_path", "url"})


def _node_text(source: bytes, ts_node: TSNode) -> str:
    return source[ts_node.start_byte : ts_node.end_byte].decode(
        "utf-8", errors="replace"
    )


def _start_line(ts_node: TSNode) -> int:
    return ts_node.start_point[0] + 1


def _end_line(ts_node: TSNode) -> int:
    return ts_node.end_point[0] + 1


def _strip_quotes(text: str) -> str:
    text = text.strip()
    if len(text) >= 2 and text[0] == text[-1] and text[0] in ("'", '"'):
        return text[1:-1]
    # r-prefixed raw string literal (e.g. r'^foo$') - strip prefix then quotes.
    if len(text) >= 3 and text[0] in ("r", "R") and text[1] == text[-1] and text[1] in (
        "'",
        '"',
    ):
        return text[2:-1]
    return text


def _call_func_name(call_node: TSNode, source: bytes) -> str:
    """Return the dotted call target (e.g. 'path' or 'views.user_detail')."""
    fn = call_node.child_by_field_name("function")
    if fn is None:
        return ""
    if fn.type == "identifier":
        return _node_text(source, fn)
    if fn.type == "attribute":
        return _node_text(source, fn)
    return ""


def _call_args(call_node: TSNode) -> list[TSNode]:
    args_node = call_node.child_by_field_name("arguments")
    if args_node is None:
        return []
    return [c for c in args_node.named_children if c.type != "keyword_argument"]


class DjangoFrameworkResolver(FrameworkResolver):
    name = "django"

    def applies_to(self, file_path: Path) -> bool:
        # Django convention: URL configuration lives in urls.py (project or app).
        return file_path.name == "urls.py"

    def resolve(
        self,
        file_path: Path,
        source: bytes,
        ast_nodes: list[Node],
    ) -> tuple[list[Node], list[Edge]]:
        if not source:
            return [], []
        try:
            tree = _PY_PARSER.parse(source)
        except Exception:  # noqa: BLE001
            logger.debug("Django parse failed for %s", file_path, exc_info=True)
            return [], []

        nodes: list[Node] = []
        edges: list[Edge] = []
        ast_count = len(ast_nodes)
        name_to_ast = {n.name: idx for idx, n in enumerate(ast_nodes)}
        qual_to_ast = {n.qualified_name: idx for idx, n in enumerate(ast_nodes)}

        def emit_route(pattern: str, ts_node: TSNode) -> int:
            local_id = ast_count + len(nodes)
            nodes.append(
                Node(
                    name=pattern,
                    kind=NodeKind.ROUTE,
                    qualified_name=f"django:{pattern}",
                    file_path=str(file_path),
                    start_line=_start_line(ts_node),
                    end_line=_end_line(ts_node),
                    signature=_node_text(source, ts_node).splitlines()[0].strip()
                    if _node_text(source, ts_node)
                    else "",
                )
            )
            return local_id

        def resolve_handler(expr_text: str) -> int | None:
            """Best-effort: match `views.user_detail`, `user_detail`, or
            `MyView.as_view()` to an AST node in the same file."""
            text = expr_text.strip()
            if not text:
                return None
            # Strip trailing as_view() invocation for class-based views.
            if text.endswith(".as_view()"):
                text = text[: -len(".as_view()")]
            elif text.endswith("()"):
                text = text[:-2]
            # Try qualified_name first, then dotted suffix as plain name.
            if text in qual_to_ast:
                return qual_to_ast[text]
            simple = text.split(".")[-1]
            return name_to_ast.get(simple)

        # Walk every call node in the source. urls.py is small, so the cost is
        # negligible vs. running tree-sitter queries.
        for call in _iter_calls(tree.root_node):
            fname = _call_func_name(call, source)
            if not fname:
                continue
            short = fname.split(".")[-1]
            args = _call_args(call)
            if short in _ROUTE_FUNCS and args:
                # An empty string is a valid Django root URL pattern; only
                # skip when the arg failed to parse (not a string literal).
                first_arg_text = _node_text(source, args[0])
                if args[0].type not in ("string",):
                    continue
                pattern = _strip_quotes(first_arg_text)
                route_id = emit_route(pattern, call)
                # Handler is positional arg 2 if present.
                if len(args) >= 2:
                    handler_text = _node_text(source, args[1])
                    ast_id = resolve_handler(handler_text)
                    if ast_id is not None:
                        edges.append(
                            Edge(
                                source_id=route_id,
                                target_id=ast_id,
                                kind=EdgeKind.REFERENCES,
                                call_site_line=_start_line(call),
                            )
                        )
            elif short == "include" and args:
                # `include('myapp.urls')` is a nested URL conf - emit a route
                # node so the include surface is searchable, but skip the
                # handler edge (the target lives in a different file).
                target = _strip_quotes(_node_text(source, args[0]))
                if target:
                    emit_route(f"include:{target}", call)

        return nodes, edges


def _iter_calls(root: TSNode):
    """Yield every `call` descendant of `root` (DFS, no recursion limit)."""
    stack: list[TSNode] = [root]
    while stack:
        node = stack.pop()
        if node.type == "call":
            yield node
        stack.extend(reversed(node.named_children))
