"""Ruby AST extractor backed by tree-sitter.

Emits node kinds: `module` (file), `namespace` (Ruby `module`), `class`,
`method` (def inside a class/module), `function` (top-level def), `constant`
(top-level constant assignment), `import` (`require` / `require_relative`).
Emits edges: `contains`, `calls`, `extends`, `imports`.

Ruby resolves methods dynamically, so only in-file name matches produce a
`calls` edge (a call whose method name matches an in-file def). A `class C <
Base` whose `Base` is defined in the same file emits `extends`. Parameter
nodes are intentionally not emitted (they inflate the FTS surface without
being useful search targets), matching the Go extractor.
"""

from __future__ import annotations

import logging
from pathlib import Path

from tree_sitter import Language, Node as TSNode, Parser
import tree_sitter_ruby

from nexus_code_search.extraction.languages.base import Extractor
from nexus_code_search.types import Edge, EdgeKind, Node, NodeKind

logger = logging.getLogger("nexus-code-search")

_RUBY_LANGUAGE = Language(tree_sitter_ruby.language())
_RUBY_PARSER = Parser(_RUBY_LANGUAGE)

_REQUIRE_METHODS = {"require", "require_relative", "load", "autoload"}


def _node_text(source: bytes, node: TSNode) -> str:
    return source[node.start_byte : node.end_byte].decode("utf-8", errors="replace")


def _start_line(node: TSNode) -> int:
    return node.start_point[0] + 1


def _end_line(node: TSNode) -> int:
    return node.end_point[0] + 1


def _first_line(source: bytes, node: TSNode) -> str:
    raw = _node_text(source, node).splitlines()
    return raw[0].strip() if raw else ""


class RubyExtractor(Extractor):
    language = "ruby"

    def extract(self, file_path: Path, source: bytes) -> tuple[list[Node], list[Edge]]:
        tree = _RUBY_PARSER.parse(source)
        root = tree.root_node
        module_qual = file_path.stem

        nodes: list[Node] = []
        edges: list[Edge] = []
        index_by_qname: dict[str, int] = {}
        index_by_name: dict[str, int] = {}

        def add_node(node: Node) -> int:
            local_id = len(nodes)
            nodes.append(node)
            index_by_qname[node.qualified_name] = local_id
            index_by_name.setdefault(node.name, local_id)
            return local_id

        module_idx = add_node(
            Node(
                name=module_qual,
                kind=NodeKind.MODULE,
                qualified_name=module_qual,
                file_path=str(file_path),
                start_line=1,
                end_line=max(1, _end_line(root)),
            )
        )

        self._walk(root, source, file_path, module_qual, module_idx, edges, add_node)
        self._collect_calls(
            root, source, module_qual, nodes, edges, index_by_qname, index_by_name
        )
        return nodes, edges

    def _name_of(self, node: TSNode, source: bytes) -> str | None:
        name_node = node.child_by_field_name("name")
        if name_node is not None:
            return _node_text(source, name_node)
        for child in node.named_children:
            if child.type in ("constant", "identifier"):
                return _node_text(source, child)
        return None

    def _walk(
        self, scope, source, file_path, container_qual, container_idx, edges, add_node
    ) -> None:
        """Recurse the body of `scope`, emitting declarations under container."""
        for child in scope.named_children:
            t = child.type
            if t == "call":
                self._handle_require(
                    child, source, file_path, container_qual, container_idx,
                    edges, add_node,
                )
            elif t in ("module", "class"):
                name = self._name_of(child, source)
                if name is None:
                    continue
                kind = NodeKind.NAMESPACE if t == "module" else NodeKind.CLASS
                qname = f"{container_qual}.{name}"
                idx = add_node(
                    Node(
                        name=name,
                        kind=kind,
                        qualified_name=qname,
                        file_path=str(file_path),
                        start_line=_start_line(child),
                        end_line=_end_line(child),
                        signature=_first_line(source, child),
                    )
                )
                edges.append(
                    Edge(source_id=container_idx, target_id=idx, kind=EdgeKind.CONTAINS)
                )
                body = child.child_by_field_name("body") or child
                self._walk(body, source, file_path, qname, idx, edges, add_node)
            elif t in ("method", "singleton_method"):
                name = self._name_of(child, source)
                if name is None:
                    continue
                # A def directly under the file root is a function; under a
                # class/module it is a method.
                is_top = container_qual == file_path.stem
                kind = NodeKind.FUNCTION if is_top else NodeKind.METHOD
                qname = f"{container_qual}.{name}"
                idx = add_node(
                    Node(
                        name=name,
                        kind=kind,
                        qualified_name=qname,
                        file_path=str(file_path),
                        start_line=_start_line(child),
                        end_line=_end_line(child),
                        signature=_first_line(source, child),
                    )
                )
                edges.append(
                    Edge(source_id=container_idx, target_id=idx, kind=EdgeKind.CONTAINS)
                )
            elif t == "assignment":
                self._handle_constant(
                    child, source, file_path, container_qual, container_idx,
                    edges, add_node,
                )
            elif t in ("body_statement", "begin", "then"):
                self._walk(
                    child, source, file_path, container_qual, container_idx,
                    edges, add_node,
                )

    def _handle_require(
        self, node, source, file_path, container_qual, container_idx, edges, add_node
    ) -> None:
        method = node.child_by_field_name("method")
        if method is None or _node_text(source, method) not in _REQUIRE_METHODS:
            return
        args = node.child_by_field_name("arguments")
        if args is None:
            return
        for arg in args.named_children:
            if arg.type != "string":
                continue
            raw = _node_text(source, arg).strip().strip("'\"")
            if not raw:
                continue
            name = raw.rsplit("/", 1)[-1]
            qname = f"{container_qual}.require:{raw}"
            idx = add_node(
                Node(
                    name=name,
                    kind=NodeKind.IMPORT,
                    qualified_name=qname,
                    file_path=str(file_path),
                    start_line=_start_line(node),
                    end_line=_end_line(node),
                    signature=_first_line(source, node),
                )
            )
            edges.append(
                Edge(source_id=container_idx, target_id=idx, kind=EdgeKind.IMPORTS)
            )

    def _handle_constant(
        self, node, source, file_path, container_qual, container_idx, edges, add_node
    ) -> None:
        lhs = node.child_by_field_name("left")
        if lhs is None or lhs.type != "constant":
            return
        name = _node_text(source, lhs)
        idx = add_node(
            Node(
                name=name,
                kind=NodeKind.CONSTANT,
                qualified_name=f"{container_qual}.{name}",
                file_path=str(file_path),
                start_line=_start_line(node),
                end_line=_end_line(node),
                signature=_first_line(source, node),
            )
        )
        edges.append(
            Edge(source_id=container_idx, target_id=idx, kind=EdgeKind.CONTAINS)
        )

    def _collect_calls(
        self, root, source, module_qual, nodes, edges, index_by_qname, index_by_name
    ) -> None:
        stack: list[tuple[TSNode, str | None]] = [(root, None)]
        while stack:
            node, fn_q = stack.pop()
            new_fn = fn_q
            if node.type in ("method", "singleton_method"):
                nn = node.child_by_field_name("name")
                if nn is not None:
                    # Best-effort qualified name by plain name lookup.
                    name = _node_text(source, nn)
                    new_fn = self._owner_qname(name, index_by_name, nodes) or name
            elif node.type == "class":
                sc = node.child_by_field_name("superclass")
                if sc is not None:
                    self._emit_extends(node, sc, source, nodes, edges, index_by_name)
            elif node.type == "call" and fn_q:
                self._emit_call(
                    node, source, fn_q, nodes, edges, index_by_qname, index_by_name
                )
            for c in reversed(node.named_children):
                stack.append((c, new_fn))

    def _owner_qname(self, name, index_by_name, nodes) -> str | None:
        idx = index_by_name.get(name)
        if idx is None:
            return None
        return nodes[idx].qualified_name

    def _emit_extends(self, class_node, sc_node, source, nodes, edges, index_by_name):
        # superclass child holds a constant naming the parent.
        parent = None
        for c in sc_node.named_children:
            if c.type in ("constant", "scope_resolution"):
                parent = _node_text(source, c).split("::")[-1]
                break
        if parent is None:
            return
        name = self._name_of(class_node, source)
        if name is None:
            return
        src_idx = index_by_name.get(name)
        tgt_idx = index_by_name.get(parent)
        if src_idx is None or tgt_idx is None or src_idx == tgt_idx:
            return
        edges.append(
            Edge(source_id=src_idx, target_id=tgt_idx, kind=EdgeKind.EXTENDS)
        )

    def _emit_call(
        self, node, source, fn_q, nodes, edges, index_by_qname, index_by_name
    ) -> None:
        caller_idx = index_by_qname.get(fn_q)
        if caller_idx is None:
            return
        method = node.child_by_field_name("method")
        if method is None:
            return
        called = _node_text(source, method)
        if called in _REQUIRE_METHODS:
            return
        tgt = index_by_name.get(called)
        if tgt is None or tgt == caller_idx:
            return
        if nodes[tgt].kind not in (NodeKind.FUNCTION, NodeKind.METHOD):
            return
        edges.append(
            Edge(
                source_id=caller_idx,
                target_id=tgt,
                kind=EdgeKind.CALLS,
                call_site_line=_start_line(node),
            )
        )
