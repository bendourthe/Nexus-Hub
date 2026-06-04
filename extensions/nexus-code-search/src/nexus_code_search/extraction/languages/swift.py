"""Swift AST extractor backed by tree-sitter.

Emits node kinds: `module` (file), `protocol`, `class`, `struct`, `enum`,
`function` (top-level func), `method` (func / init inside a type body),
`property` (stored property), `enum_member` (case), `import`. Emits edges:
`contains`, `calls`, `extends`, `implements`, `imports`.

The Swift grammar collapses `class` / `struct` / `enum` / `actor` /
`extension` into a single `class_declaration` node, discriminated by the
leading keyword token; protocols are their own `protocol_declaration`.
Swift resolves calls dynamically, so only in-file name matches produce a
`calls` edge (a call whose callee name matches an in-file def). A type whose
inheritance specifier names an in-file type emits `extends` (to a class) or
`implements` (to a protocol). Parameter nodes are intentionally not emitted,
matching the Go / Ruby extractors.
"""

from __future__ import annotations

import logging
from pathlib import Path

from tree_sitter import Language, Node as TSNode, Parser
import tree_sitter_swift

from nexus_code_search.extraction.languages.base import Extractor
from nexus_code_search.types import Edge, EdgeKind, Node, NodeKind

logger = logging.getLogger("nexus-code-search")

_SWIFT_LANGUAGE = Language(tree_sitter_swift.language())
_SWIFT_PARSER = Parser(_SWIFT_LANGUAGE)

# Leading keyword token on a `class_declaration` -> node kind. `actor` and
# `extension` are reference types without a dedicated NodeKind, so they map to
# CLASS.
_CLASS_KEYWORDS: dict[str, NodeKind] = {
    "class": NodeKind.CLASS,
    "struct": NodeKind.STRUCT,
    "enum": NodeKind.ENUM,
    "actor": NodeKind.CLASS,
    "extension": NodeKind.CLASS,
}

_TYPE_BODIES = {"class_body", "enum_class_body"}
_METHOD_DECLS = {"function_declaration", "protocol_function_declaration"}


def _node_text(source: bytes, node: TSNode) -> str:
    return source[node.start_byte : node.end_byte].decode("utf-8", errors="replace")


def _start_line(node: TSNode) -> int:
    return node.start_point[0] + 1


def _end_line(node: TSNode) -> int:
    return node.end_point[0] + 1


def _first_line(source: bytes, node: TSNode) -> str:
    raw = _node_text(source, node).splitlines()
    return raw[0].strip() if raw else ""


def _name_field(source: bytes, node: TSNode) -> str | None:
    name_node = node.child_by_field_name("name")
    return _node_text(source, name_node) if name_node is not None else None


class SwiftExtractor(Extractor):
    language = "swift"

    def extract(self, file_path: Path, source: bytes) -> tuple[list[Node], list[Edge]]:
        tree = _SWIFT_PARSER.parse(source)
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
        self._resolve_inheritance(root, source, module_qual, nodes, edges, index_by_name)
        self._collect_calls(root, source, module_qual, nodes, edges, index_by_qname)
        return nodes, edges

    def _class_kind(self, node: TSNode) -> tuple[NodeKind, str]:
        for child in node.children:
            if child.type in _CLASS_KEYWORDS:
                return _CLASS_KEYWORDS[child.type], child.type
        return NodeKind.CLASS, "class"

    def _type_body(self, node: TSNode) -> TSNode | None:
        for child in node.named_children:
            if child.type in _TYPE_BODIES:
                return child
        return None

    def _walk(
        self, scope, source, file_path, container_qual, container_idx, edges, add_node
    ) -> None:
        """Emit declarations under `scope`, recursing into type bodies."""
        for child in scope.named_children:
            t = child.type
            if t == "import_declaration":
                self._handle_import(
                    child, source, file_path, container_qual, container_idx,
                    edges, add_node,
                )
            elif t == "protocol_declaration":
                self._handle_type(
                    child, source, file_path, container_qual, container_idx,
                    NodeKind.PROTOCOL, edges, add_node,
                )
            elif t == "class_declaration":
                kind, _ = self._class_kind(child)
                self._handle_type(
                    child, source, file_path, container_qual, container_idx,
                    kind, edges, add_node,
                )
            elif t in _METHOD_DECLS:
                self._handle_callable(
                    child, source, file_path, container_qual, container_idx,
                    edges, add_node, name=_name_field(source, child),
                )

    def _handle_type(
        self, node, source, file_path, container_qual, container_idx, kind,
        edges, add_node,
    ) -> None:
        body = self._type_body(node) or node.child_by_field_name("body")
        name = _name_field(source, node)
        if name is None:
            return
        qname = f"{container_qual}.{name}"
        type_idx = add_node(
            Node(
                name=name,
                kind=kind,
                qualified_name=qname,
                file_path=str(file_path),
                start_line=_start_line(node),
                end_line=_end_line(node),
                signature=_first_line(source, node),
            )
        )
        edges.append(
            Edge(source_id=container_idx, target_id=type_idx, kind=EdgeKind.CONTAINS)
        )
        if body is None:
            return
        for member in body.named_children:
            mt = member.type
            if mt in _METHOD_DECLS:
                self._handle_callable(
                    member, source, file_path, qname, type_idx, edges, add_node,
                    name=_name_field(source, member),
                )
            elif mt == "init_declaration":
                self._handle_callable(
                    member, source, file_path, qname, type_idx, edges, add_node,
                    name="init",
                )
            elif mt == "property_declaration":
                self._handle_named_member(
                    member, source, file_path, qname, type_idx, NodeKind.PROPERTY,
                    edges, add_node,
                )
            elif mt == "enum_entry":
                self._handle_enum_entry(
                    member, source, file_path, qname, type_idx, edges, add_node
                )
            elif mt in ("class_declaration", "protocol_declaration"):
                nested_kind = (
                    NodeKind.PROTOCOL
                    if mt == "protocol_declaration"
                    else self._class_kind(member)[0]
                )
                self._handle_type(
                    member, source, file_path, qname, type_idx, nested_kind,
                    edges, add_node,
                )

    def _handle_callable(
        self, node, source, file_path, container_qual, container_idx, edges,
        add_node, name,
    ) -> None:
        if name is None:
            return
        # A def directly under the file root is a function; under a type it is
        # a method.
        is_top = container_qual == file_path.stem
        kind = NodeKind.FUNCTION if is_top else NodeKind.METHOD
        idx = add_node(
            Node(
                name=name,
                kind=kind,
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

    def _handle_named_member(
        self, node, source, file_path, container_qual, container_idx, kind,
        edges, add_node,
    ) -> None:
        name = _name_field(source, node)
        if name is None:
            return
        idx = add_node(
            Node(
                name=name,
                kind=kind,
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

    def _handle_enum_entry(
        self, node, source, file_path, container_qual, container_idx, edges, add_node
    ) -> None:
        name = _name_field(source, node)
        if name is None:
            return
        idx = add_node(
            Node(
                name=name,
                kind=NodeKind.ENUM_MEMBER,
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

    def _handle_import(
        self, node, source, file_path, container_qual, container_idx, edges, add_node
    ) -> None:
        # The module path is a chain of `simple_identifier` leaves
        # (`import os.log` -> ["os", "log"]). The top module is the first.
        ids = [
            _node_text(source, c)
            for c in self._descendants(node)
            if c.type == "simple_identifier"
        ]
        if not ids:
            return
        dotted = ".".join(ids)
        name = ids[0]
        idx = add_node(
            Node(
                name=name,
                kind=NodeKind.IMPORT,
                qualified_name=f"{container_qual}.import:{dotted}",
                file_path=str(file_path),
                start_line=_start_line(node),
                end_line=_end_line(node),
                signature=_first_line(source, node),
            )
        )
        edges.append(
            Edge(source_id=container_idx, target_id=idx, kind=EdgeKind.IMPORTS)
        )

    def _resolve_inheritance(
        self, root, source, module_qual, nodes, edges, index_by_name
    ) -> None:
        stack: list[TSNode] = [root]
        while stack:
            node = stack.pop()
            if node.type in ("class_declaration", "protocol_declaration"):
                self._emit_inheritance(node, source, nodes, edges, index_by_name)
            stack.extend(node.named_children)

    def _emit_inheritance(self, node, source, nodes, edges, index_by_name) -> None:
        name = _name_field(source, node)
        if name is None:
            return
        src_idx = index_by_name.get(name)
        if src_idx is None:
            return
        for spec in node.named_children:
            if spec.type != "inheritance_specifier":
                continue
            base = self._base_name(spec, source)
            if base is None:
                continue
            tgt_idx = index_by_name.get(base)
            if tgt_idx is None or tgt_idx == src_idx:
                continue
            kind = (
                EdgeKind.IMPLEMENTS
                if nodes[tgt_idx].kind == NodeKind.PROTOCOL
                else EdgeKind.EXTENDS
            )
            edges.append(Edge(source_id=src_idx, target_id=tgt_idx, kind=kind))

    def _base_name(self, spec: TSNode, source: bytes) -> str | None:
        for child in self._descendants(spec):
            if child.type == "type_identifier":
                return _node_text(source, child)
        return None

    def _collect_calls(
        self, root, source, module_qual, nodes, edges, index_by_qname
    ) -> None:
        index_by_name: dict[str, int] = {}
        for idx, n in enumerate(nodes):
            index_by_name.setdefault(n.name, idx)
        stack: list[tuple[TSNode, str | None]] = [(root, None)]
        while stack:
            node, fn_q = stack.pop()
            new_fn = fn_q
            if node.type in _METHOD_DECLS or node.type == "init_declaration":
                name = (
                    "init"
                    if node.type == "init_declaration"
                    else _name_field(source, node)
                )
                if name is not None:
                    idx = index_by_name.get(name)
                    new_fn = nodes[idx].qualified_name if idx is not None else name
            elif node.type == "call_expression" and fn_q:
                self._emit_call(
                    node, source, fn_q, nodes, edges, index_by_qname, index_by_name
                )
            for c in reversed(node.named_children):
                stack.append((c, new_fn))

    def _emit_call(
        self, node, source, fn_q, nodes, edges, index_by_qname, index_by_name
    ) -> None:
        caller_idx = index_by_qname.get(fn_q)
        if caller_idx is None:
            return
        callee = node.named_children[0] if node.named_children else None
        if callee is None or callee.type != "simple_identifier":
            return
        called = _node_text(source, callee)
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

    def _descendants(self, node: TSNode):
        # Pre-order, preserving sibling document order (push children reversed
        # so the first child is popped first). Order matters for dotted import
        # paths like `import os.log` -> top module `os`.
        stack = [node]
        while stack:
            cur = stack.pop()
            yield cur
            stack.extend(reversed(cur.named_children))
