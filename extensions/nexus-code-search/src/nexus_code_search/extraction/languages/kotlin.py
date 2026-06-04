"""Kotlin AST extractor backed by tree-sitter.

Emits node kinds: `module` (file), `namespace` (package), `interface`,
`class`, `enum`, `function` (top-level fun), `method` (fun inside a type
body), `enum_member` (enum entry), `import`. Kotlin `object` singletons are
emitted as `class`. Emits edges: `contains`, `calls`, `extends`,
`implements`, `imports`.

The Kotlin grammar uses a single `class_declaration` for `class`,
`interface`, and `enum class`, discriminated by the leading keyword token and
the presence of an `enum_class_body`; `object` is its own
`object_declaration`. Kotlin resolves calls dynamically, so only in-file name
matches produce a `calls` edge (a call whose callee name matches an in-file
def). A `delegation_specifier` naming an in-file type emits `extends` (to a
class) or `implements` (to an interface). Parameter nodes are intentionally
not emitted, matching the Go / Ruby extractors.
"""

from __future__ import annotations

import logging
from pathlib import Path

from tree_sitter import Language, Node as TSNode, Parser
import tree_sitter_kotlin

from nexus_code_search.extraction.languages.base import Extractor
from nexus_code_search.types import Edge, EdgeKind, Node, NodeKind

logger = logging.getLogger("nexus-code-search")

_KOTLIN_LANGUAGE = Language(tree_sitter_kotlin.language())
_KOTLIN_PARSER = Parser(_KOTLIN_LANGUAGE)

_TYPE_BODIES = {"class_body", "enum_class_body"}


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


class KotlinExtractor(Extractor):
    language = "kotlin"

    def extract(self, file_path: Path, source: bytes) -> tuple[list[Node], list[Edge]]:
        tree = _KOTLIN_PARSER.parse(source)
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
        self._resolve_inheritance(root, source, nodes, edges, index_by_name)
        self._collect_calls(root, source, nodes, edges, index_by_qname)
        return nodes, edges

    def _class_kind(self, node: TSNode) -> NodeKind:
        anon = {c.type for c in node.children if not c.is_named}
        if "interface" in anon:
            return NodeKind.INTERFACE
        if any(c.type == "enum_class_body" for c in node.children):
            return NodeKind.ENUM
        return NodeKind.CLASS

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
            if t == "package_header":
                self._handle_package(
                    child, source, file_path, container_qual, container_idx,
                    edges, add_node,
                )
            elif t == "import":
                self._handle_import(
                    child, source, file_path, container_qual, container_idx,
                    edges, add_node,
                )
            elif t == "class_declaration":
                self._handle_type(
                    child, source, file_path, container_qual, container_idx,
                    self._class_kind(child), edges, add_node,
                )
            elif t == "object_declaration":
                self._handle_type(
                    child, source, file_path, container_qual, container_idx,
                    NodeKind.CLASS, edges, add_node,
                )
            elif t == "function_declaration":
                self._handle_function(
                    child, source, file_path, container_qual, container_idx,
                    edges, add_node,
                )
            elif t == "property_declaration":
                self._handle_property(
                    child, source, file_path, container_qual, container_idx,
                    edges, add_node,
                )

    def _handle_type(
        self, node, source, file_path, container_qual, container_idx, kind,
        edges, add_node,
    ) -> None:
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
        body = self._type_body(node)
        if body is None:
            return
        for member in body.named_children:
            mt = member.type
            if mt == "function_declaration":
                self._handle_function(
                    member, source, file_path, qname, type_idx, edges, add_node
                )
            elif mt == "property_declaration":
                self._handle_property(
                    member, source, file_path, qname, type_idx, edges, add_node
                )
            elif mt == "enum_entry":
                self._handle_enum_entry(
                    member, source, file_path, qname, type_idx, edges, add_node
                )
            elif mt in ("class_declaration", "object_declaration"):
                nested_kind = (
                    NodeKind.CLASS
                    if mt == "object_declaration"
                    else self._class_kind(member)
                )
                self._handle_type(
                    member, source, file_path, qname, type_idx, nested_kind,
                    edges, add_node,
                )

    def _handle_function(
        self, node, source, file_path, container_qual, container_idx, edges, add_node
    ) -> None:
        name = _name_field(source, node)
        if name is None:
            return
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

    def _handle_property(
        self, node, source, file_path, container_qual, container_idx, edges, add_node
    ) -> None:
        name = _name_field(source, node)
        if name is None:
            # `val x = ...` exposes the binding via a variable_declaration child.
            for child in node.named_children:
                if child.type == "variable_declaration":
                    name = _name_field(source, child)
                    if name is None:
                        for leaf in child.named_children:
                            if leaf.type in ("identifier", "simple_identifier"):
                                name = _node_text(source, leaf)
                                break
                    break
        if name is None:
            return
        is_top = container_qual == file_path.stem
        kind = NodeKind.CONSTANT if is_top else NodeKind.PROPERTY
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
        # `enum_entry` has no `name` field; the leading `identifier` child is
        # the member name.
        name = _name_field(source, node)
        if name is None:
            for child in node.named_children:
                if child.type == "identifier":
                    name = _node_text(source, child)
                    break
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

    def _handle_package(
        self, node, source, file_path, container_qual, container_idx, edges, add_node
    ) -> None:
        text = _node_text(source, node).replace("package", "", 1).strip().rstrip(";")
        if not text:
            return
        name = text.split(".")[-1]
        idx = add_node(
            Node(
                name=name,
                kind=NodeKind.NAMESPACE,
                qualified_name=f"{container_qual}.package:{text}",
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
        text = _node_text(source, node).replace("import", "", 1).strip().rstrip(";")
        if not text:
            return
        # `import a.b.C` -> name `C`; `import a.b.*` -> name `b`.
        name = text.replace(".*", "").split(".")[-1]
        idx = add_node(
            Node(
                name=name,
                kind=NodeKind.IMPORT,
                qualified_name=f"{container_qual}.import:{text}",
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
        self, root, source, nodes, edges, index_by_name
    ) -> None:
        stack: list[TSNode] = [root]
        while stack:
            node = stack.pop()
            if node.type in ("class_declaration", "object_declaration"):
                self._emit_inheritance(node, source, nodes, edges, index_by_name)
            stack.extend(node.named_children)

    def _emit_inheritance(self, node, source, nodes, edges, index_by_name) -> None:
        name = _name_field(source, node)
        if name is None:
            return
        src_idx = index_by_name.get(name)
        if src_idx is None:
            return
        for child in node.named_children:
            if child.type != "delegation_specifiers":
                continue
            for spec in child.named_children:
                if spec.type != "delegation_specifier":
                    continue
                base = self._base_name(spec, source)
                if base is None:
                    continue
                tgt_idx = index_by_name.get(base)
                if tgt_idx is None or tgt_idx == src_idx:
                    continue
                kind = (
                    EdgeKind.IMPLEMENTS
                    if nodes[tgt_idx].kind == NodeKind.INTERFACE
                    else EdgeKind.EXTENDS
                )
                edges.append(Edge(source_id=src_idx, target_id=tgt_idx, kind=kind))

    def _base_name(self, spec: TSNode, source: bytes) -> str | None:
        # `Base()` (constructor invocation) or `Greeter` (bare type) - the bare
        # type name is the first `type_identifier` / `identifier` leaf.
        stack: list[TSNode] = [spec]
        while stack:
            cur = stack.pop()
            if cur.type in ("type_identifier", "identifier"):
                return _node_text(source, cur).split(".")[-1]
            stack.extend(reversed(cur.named_children))
        return None

    def _collect_calls(self, root, source, nodes, edges, index_by_qname) -> None:
        index_by_name: dict[str, int] = {}
        for idx, n in enumerate(nodes):
            index_by_name.setdefault(n.name, idx)
        stack: list[tuple[TSNode, str | None]] = [(root, None)]
        while stack:
            node, fn_q = stack.pop()
            new_fn = fn_q
            if node.type == "function_declaration":
                name = _name_field(source, node)
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
        if callee is None or callee.type != "identifier":
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
