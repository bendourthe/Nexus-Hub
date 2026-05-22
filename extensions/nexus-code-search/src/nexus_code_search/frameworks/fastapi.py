"""FastAPI / Flask-style decorator-based route resolver.

Recognizes decorator forms common in FastAPI and Flask:

    @app.get('/items/{item_id}')
    @router.post('/users', response_model=User)
    @api.delete('/v1/{thing_id}')

For each decorated function definition, emits one `route` node with
name = `<METHOD> <path>` and a `decorates` edge from the route node back to
the handler function the decorator annotated.
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

_HTTP_METHODS: frozenset[str] = frozenset(
    {"get", "post", "put", "patch", "delete", "options", "head", "route"}
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
    if len(text) >= 2 and text[0] == text[-1] and text[0] in ("'", '"'):
        return text[1:-1]
    return text


def _decorator_call(decorator_node: TSNode) -> TSNode | None:
    """Return the underlying `call` node when the decorator is `@x.method(...)`."""
    for child in decorator_node.named_children:
        if child.type == "call":
            return child
    return None


def _attribute_parts(attr_node: TSNode, source: bytes) -> tuple[str, str]:
    """Split `app.get` into (`app`, `get`); return ("", short) on plain identifiers."""
    if attr_node.type == "identifier":
        return ("", _node_text(source, attr_node))
    if attr_node.type == "attribute":
        obj = attr_node.child_by_field_name("object")
        attr = attr_node.child_by_field_name("attribute")
        obj_text = _node_text(source, obj) if obj else ""
        attr_text = _node_text(source, attr) if attr else ""
        return (obj_text, attr_text)
    return ("", "")


class FastAPIFrameworkResolver(FrameworkResolver):
    name = "fastapi"

    def applies_to(self, file_path: Path) -> bool:
        # FastAPI/Flask handlers live in any .py file; the resolver inspects
        # decorator targets to decide.
        return file_path.suffix.lower() in (".py", ".pyi")

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
            logger.debug("FastAPI parse failed for %s", file_path, exc_info=True)
            return [], []

        nodes: list[Node] = []
        edges: list[Edge] = []
        ast_count = len(ast_nodes)
        name_to_ast = {n.name: idx for idx, n in enumerate(ast_nodes)}

        # Walk decorated_definition nodes only - FastAPI/Flask handlers are
        # decorator-driven.
        for decorated in _iter_decorated(tree.root_node):
            definition = decorated.child_by_field_name("definition")
            if definition is None or definition.type != "function_definition":
                continue
            handler_name_node = definition.child_by_field_name("name")
            if handler_name_node is None:
                continue
            handler_name = _node_text(source, handler_name_node)
            handler_ast_id = name_to_ast.get(handler_name)

            for child in decorated.named_children:
                if child.type != "decorator":
                    continue
                call_node = _decorator_call(child)
                if call_node is None:
                    continue
                fn_field = call_node.child_by_field_name("function")
                if fn_field is None:
                    continue
                obj_text, attr_text = _attribute_parts(fn_field, source)
                method = attr_text.lower()
                if method not in _HTTP_METHODS:
                    continue
                # First positional arg is the path string.
                args_node = call_node.child_by_field_name("arguments")
                if args_node is None:
                    continue
                positional = [
                    c
                    for c in args_node.named_children
                    if c.type != "keyword_argument"
                ]
                if not positional:
                    continue
                path_str = _strip_quotes(_node_text(source, positional[0]))
                if not path_str:
                    continue
                method_upper = method.upper()
                route_label = f"{method_upper} {path_str}"
                local_id = ast_count + len(nodes)
                nodes.append(
                    Node(
                        name=route_label,
                        kind=NodeKind.ROUTE,
                        qualified_name=f"fastapi:{route_label}",
                        file_path=str(file_path),
                        start_line=_start_line(call_node),
                        end_line=_end_line(call_node),
                        signature=_node_text(source, child).strip(),
                    )
                )
                if handler_ast_id is not None:
                    edges.append(
                        Edge(
                            source_id=local_id,
                            target_id=handler_ast_id,
                            kind=EdgeKind.DECORATES,
                            call_site_line=_start_line(child),
                        )
                    )

        return nodes, edges


def _iter_decorated(root: TSNode):
    """Yield every `decorated_definition` descendant of `root`."""
    stack: list[TSNode] = [root]
    while stack:
        node = stack.pop()
        if node.type == "decorated_definition":
            yield node
        stack.extend(reversed(node.named_children))
