"""Express.js framework route resolver.

Recognizes the call forms used by Express applications and routers:

    app.get('/users', handler)
    router.post('/users/:id', middleware, handler)
    app.use('/admin', adminRouter)
    app.all('/*', catchAllHandler)

For each detected call, emits one `route` node (name = `<METHOD> <path>`)
and a `references` edge from the route to the final handler function (the
last positional argument after the path string).
"""

from __future__ import annotations

import logging
from pathlib import Path

import tree_sitter_typescript
from tree_sitter import Language, Node as TSNode, Parser

from nexus_code_search.frameworks.base import FrameworkResolver
from nexus_code_search.types import Edge, EdgeKind, Node, NodeKind

logger = logging.getLogger("nexus-code-search")

_TS_LANGUAGE = Language(tree_sitter_typescript.language_typescript())
_TSX_LANGUAGE = Language(tree_sitter_typescript.language_tsx())
_TS_PARSER = Parser(_TS_LANGUAGE)
_TSX_PARSER = Parser(_TSX_LANGUAGE)

_HTTP_METHODS: frozenset[str] = frozenset(
    {"get", "post", "put", "patch", "delete", "options", "head", "all", "use"}
)


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
    if len(text) >= 2 and text[0] == text[-1] and text[0] in ("'", '"', "`"):
        return text[1:-1]
    return text


def _parser_for(file_path: Path) -> Parser:
    return _TSX_PARSER if file_path.suffix.lower() == ".tsx" else _TS_PARSER


class ExpressFrameworkResolver(FrameworkResolver):
    name = "express"

    def applies_to(self, file_path: Path) -> bool:
        return file_path.suffix.lower() in (".ts", ".tsx", ".mts", ".cts")

    def resolve(
        self,
        file_path: Path,
        source: bytes,
        ast_nodes: list[Node],
    ) -> tuple[list[Node], list[Edge]]:
        if not source:
            return [], []
        try:
            tree = _parser_for(file_path).parse(source)
        except Exception:  # noqa: BLE001
            logger.debug("Express parse failed for %s", file_path, exc_info=True)
            return [], []

        nodes: list[Node] = []
        edges: list[Edge] = []
        ast_count = len(ast_nodes)
        name_to_ast = {n.name: idx for idx, n in enumerate(ast_nodes)}

        for call in _iter_calls(tree.root_node):
            fn = call.child_by_field_name("function")
            if fn is None or fn.type != "member_expression":
                continue
            obj = fn.child_by_field_name("object")
            prop = fn.child_by_field_name("property")
            if obj is None or prop is None:
                continue
            method = _node_text(source, prop).lower()
            if method not in _HTTP_METHODS:
                continue
            args_node = call.child_by_field_name("arguments")
            if args_node is None:
                continue
            positional = [
                c
                for c in args_node.named_children
                if c.type != "comment"
            ]
            if len(positional) < 2:
                continue
            path_arg = positional[0]
            if path_arg.type not in ("string", "template_string"):
                # Filter: Express paths are string literals. `app.use(router)`
                # without a path string is technically valid but emits no
                # useful route; skip those.
                if method == "use":
                    continue
                # For non-string first args, skip (likely not a route call).
                continue
            path_str = _strip_quotes(_node_text(source, path_arg))
            if not path_str:
                continue
            method_upper = method.upper()
            route_label = f"{method_upper} {path_str}"
            local_id = ast_count + len(nodes)
            nodes.append(
                Node(
                    name=route_label,
                    kind=NodeKind.ROUTE,
                    qualified_name=f"express:{route_label}",
                    file_path=str(file_path),
                    start_line=_start_line(call),
                    end_line=_end_line(call),
                    signature=_node_text(source, call).splitlines()[0].strip()
                    if _node_text(source, call)
                    else "",
                )
            )
            # Every positional arg after the path is a middleware / handler;
            # emit a `references` edge for each one that resolves to an AST
            # node in the same file.
            for handler_arg in positional[1:]:
                handler_name = _identifier_text(handler_arg, source)
                if not handler_name:
                    continue
                ast_id = name_to_ast.get(handler_name)
                if ast_id is None:
                    continue
                edges.append(
                    Edge(
                        source_id=local_id,
                        target_id=ast_id,
                        kind=EdgeKind.REFERENCES,
                        call_site_line=_start_line(call),
                    )
                )

        return nodes, edges


def _identifier_text(arg_node: TSNode, source: bytes) -> str:
    """Return the simple identifier name for a handler argument, or ''."""
    if arg_node.type == "identifier":
        return _node_text(source, arg_node)
    if arg_node.type == "member_expression":
        # `module.handler` - take the property.
        prop = arg_node.child_by_field_name("property")
        return _node_text(source, prop) if prop else ""
    return ""


def _iter_calls(root: TSNode):
    """Yield every `call_expression` descendant of `root`."""
    stack: list[TSNode] = [root]
    while stack:
        node = stack.pop()
        if node.type == "call_expression":
            yield node
        stack.extend(reversed(node.named_children))
