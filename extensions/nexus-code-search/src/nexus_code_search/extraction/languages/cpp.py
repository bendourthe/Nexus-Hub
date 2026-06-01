"""C++ AST extractor backed by tree-sitter.

Emits node kinds: `module` (file), `namespace`, `class`, `struct`, `method`
(function defined inside a class/struct body), `function` (free function),
`field`, `enum`, `enum_member`, `import` (`#include`). Emits edges:
`contains`, `calls`, `extends` (public/private base class), `imports`.

A `class D : public Base` whose `Base` is defined in the same file emits
`extends`. A call whose target identifier matches an in-file function / method
emits `calls`. In-file resolution only. Parameter nodes are intentionally not
emitted (FTS-surface discipline).
"""

from __future__ import annotations

import logging
from pathlib import Path

from tree_sitter import Language, Node as TSNode, Parser
import tree_sitter_cpp

from nexus_code_search.extraction.languages.base import Extractor
from nexus_code_search.types import Edge, EdgeKind, Node, NodeKind

logger = logging.getLogger("nexus-code-search")

_CPP_LANGUAGE = Language(tree_sitter_cpp.language())
_CPP_PARSER = Parser(_CPP_LANGUAGE)


def _node_text(source: bytes, node: TSNode) -> str:
    return source[node.start_byte : node.end_byte].decode("utf-8", errors="replace")


def _start_line(node: TSNode) -> int:
    return node.start_point[0] + 1


def _end_line(node: TSNode) -> int:
    return node.end_point[0] + 1


def _first_line(source: bytes, node: TSNode) -> str:
    raw = _node_text(source, node).splitlines()
    return raw[0].strip() if raw else ""


def _declarator_name(source: bytes, node: TSNode | None) -> str | None:
    """Descend a declarator to the simple identifier naming the symbol."""
    while node is not None:
        if node.type in ("identifier", "field_identifier", "type_identifier"):
            return _node_text(source, node)
        if node.type == "qualified_identifier":
            name_node = node.child_by_field_name("name")
            if name_node is not None:
                return _declarator_name(source, name_node)
        if node.type == "destructor_name" or node.type == "operator_name":
            return _node_text(source, node)
        nxt = node.child_by_field_name("declarator")
        if nxt is None:
            for c in node.named_children:
                if c.type in (
                    "identifier", "field_identifier", "qualified_identifier",
                    "function_declarator", "pointer_declarator",
                    "reference_declarator", "parenthesized_declarator",
                ):
                    nxt = c
                    break
        node = nxt
    return None


class CppExtractor(Extractor):
    language = "cpp"

    def extract(self, file_path: Path, source: bytes) -> tuple[list[Node], list[Edge]]:
        tree = _CPP_PARSER.parse(source)
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

        for child in root.named_children:
            self._handle(
                child, source, file_path, module_qual, module_idx, edges, add_node,
                index_by_name,
            )

        self._collect_calls(root, source, nodes, edges, index_by_name)
        return nodes, edges

    def _handle(
        self, node, source, file_path, container_qual, container_idx, edges, add_node,
        index_by_name,
    ) -> None:
        t = node.type
        if t == "preproc_include":
            self._handle_include(
                node, source, file_path, container_qual, container_idx, edges, add_node
            )
        elif t == "namespace_definition":
            name_node = node.child_by_field_name("name")
            name = _node_text(source, name_node) if name_node else "anonymous"
            qname = f"{container_qual}.{name}"
            idx = add_node(
                Node(
                    name=name,
                    kind=NodeKind.NAMESPACE,
                    qualified_name=qname,
                    file_path=str(file_path),
                    start_line=_start_line(node),
                    end_line=_end_line(node),
                    signature=_first_line(source, node),
                )
            )
            edges.append(
                Edge(source_id=container_idx, target_id=idx, kind=EdgeKind.CONTAINS)
            )
            body = node.child_by_field_name("body")
            if body is not None:
                for child in body.named_children:
                    self._handle(
                        child, source, file_path, qname, idx, edges, add_node,
                        index_by_name,
                    )
        elif t in ("class_specifier", "struct_specifier"):
            self._handle_class(
                node, source, file_path, container_qual, container_idx, edges,
                add_node, index_by_name,
            )
        elif t == "enum_specifier":
            self._handle_enum(
                node, source, file_path, container_qual, container_idx, edges, add_node
            )
        elif t == "function_definition":
            name = _declarator_name(source, node.child_by_field_name("declarator"))
            if name:
                qname = f"{container_qual}.{name}"
                idx = add_node(
                    Node(
                        name=name,
                        kind=NodeKind.FUNCTION,
                        qualified_name=qname,
                        file_path=str(file_path),
                        start_line=_start_line(node),
                        end_line=_end_line(node),
                        signature=_first_line(source, node),
                    )
                )
                edges.append(
                    Edge(source_id=container_idx, target_id=idx, kind=EdgeKind.CONTAINS)
                )
        elif t == "declaration":
            for c in node.named_children:
                if c.type in ("class_specifier", "struct_specifier", "enum_specifier"):
                    self._handle(
                        c, source, file_path, container_qual, container_idx, edges,
                        add_node, index_by_name,
                    )

    def _handle_include(
        self, node, source, file_path, container_qual, container_idx, edges, add_node
    ) -> None:
        path_node = None
        for c in node.named_children:
            if c.type in ("system_lib_string", "string_literal"):
                path_node = c
                break
        if path_node is None:
            return
        raw = _node_text(source, path_node).strip().strip("<>\"")
        if not raw:
            return
        name = raw.rsplit("/", 1)[-1]
        idx = add_node(
            Node(
                name=name,
                kind=NodeKind.IMPORT,
                qualified_name=f"{container_qual}.include:{raw}",
                file_path=str(file_path),
                start_line=_start_line(node),
                end_line=_end_line(node),
                signature=_first_line(source, node),
            )
        )
        edges.append(
            Edge(source_id=container_idx, target_id=idx, kind=EdgeKind.IMPORTS)
        )

    def _handle_class(
        self, node, source, file_path, container_qual, container_idx, edges, add_node,
        index_by_name,
    ) -> None:
        name_node = node.child_by_field_name("name")
        if name_node is None:
            return
        name = _node_text(source, name_node)
        kind = NodeKind.STRUCT if node.type == "struct_specifier" else NodeKind.CLASS
        qname = f"{container_qual}.{name}"
        class_idx = add_node(
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
            Edge(source_id=container_idx, target_id=class_idx, kind=EdgeKind.CONTAINS)
        )

        # base_class_clause -> extends (resolved against in-file types).
        for child in node.named_children:
            if child.type == "base_class_clause":
                for c in child.named_children:
                    if c.type in ("type_identifier", "qualified_identifier"):
                        base = _node_text(source, c).split("::")[-1]
                        tgt = index_by_name.get(base)
                        if tgt is not None and tgt != class_idx:
                            edges.append(
                                Edge(
                                    source_id=class_idx,
                                    target_id=tgt,
                                    kind=EdgeKind.EXTENDS,
                                )
                            )

        body = node.child_by_field_name("body")
        if body is None:
            return
        for member in body.named_children:
            if member.type == "function_definition":
                mname = _declarator_name(source, member.child_by_field_name("declarator"))
                if not mname:
                    continue
                idx = add_node(
                    Node(
                        name=mname,
                        kind=NodeKind.METHOD,
                        qualified_name=f"{qname}.{mname}",
                        file_path=str(file_path),
                        start_line=_start_line(member),
                        end_line=_end_line(member),
                        signature=_first_line(source, member),
                    )
                )
                edges.append(
                    Edge(source_id=class_idx, target_id=idx, kind=EdgeKind.CONTAINS)
                )
            elif member.type == "field_declaration":
                fident = None
                for c in member.named_children:
                    if c.type == "field_identifier":
                        fident = c
                        break
                if fident is None:
                    fname = _declarator_name(source, member.child_by_field_name("declarator"))
                else:
                    fname = _node_text(source, fident)
                if not fname:
                    continue
                idx = add_node(
                    Node(
                        name=fname,
                        kind=NodeKind.FIELD,
                        qualified_name=f"{qname}.{fname}",
                        file_path=str(file_path),
                        start_line=_start_line(member),
                        end_line=_end_line(member),
                        signature=_first_line(source, member),
                    )
                )
                edges.append(
                    Edge(source_id=class_idx, target_id=idx, kind=EdgeKind.CONTAINS)
                )

    def _handle_enum(
        self, node, source, file_path, container_qual, container_idx, edges, add_node
    ) -> None:
        name_node = node.child_by_field_name("name")
        if name_node is None:
            return
        name = _node_text(source, name_node)
        qname = f"{container_qual}.{name}"
        enum_idx = add_node(
            Node(
                name=name,
                kind=NodeKind.ENUM,
                qualified_name=qname,
                file_path=str(file_path),
                start_line=_start_line(node),
                end_line=_end_line(node),
                signature=_first_line(source, node),
            )
        )
        edges.append(
            Edge(source_id=container_idx, target_id=enum_idx, kind=EdgeKind.CONTAINS)
        )
        body = node.child_by_field_name("body")
        if body is None:
            return
        for en in body.named_children:
            if en.type != "enumerator":
                continue
            nn = en.child_by_field_name("name") or (
                en.named_children[0] if en.named_children else None
            )
            if nn is None:
                continue
            mname = _node_text(source, nn)
            idx = add_node(
                Node(
                    name=mname,
                    kind=NodeKind.ENUM_MEMBER,
                    qualified_name=f"{qname}.{mname}",
                    file_path=str(file_path),
                    start_line=_start_line(en),
                    end_line=_end_line(en),
                    signature=_first_line(source, en),
                )
            )
            edges.append(
                Edge(source_id=enum_idx, target_id=idx, kind=EdgeKind.CONTAINS)
            )

    def _collect_calls(self, root, source, nodes, edges, index_by_name) -> None:
        stack: list[tuple[TSNode, int | None]] = [(root, None)]
        while stack:
            node, caller_idx = stack.pop()
            new_caller = caller_idx
            if node.type == "function_definition":
                name = _declarator_name(source, node.child_by_field_name("declarator"))
                if name is not None:
                    new_caller = index_by_name.get(name, caller_idx)
            elif node.type == "call_expression" and caller_idx is not None:
                fn = node.child_by_field_name("function")
                called = None
                if fn is not None:
                    if fn.type == "identifier":
                        called = _node_text(source, fn)
                    elif fn.type == "qualified_identifier":
                        called = _node_text(source, fn).split("::")[-1]
                    elif fn.type == "field_expression":
                        fld = fn.child_by_field_name("field")
                        if fld is not None:
                            called = _node_text(source, fld)
                if called:
                    tgt = index_by_name.get(called)
                    if (
                        tgt is not None
                        and tgt != caller_idx
                        and nodes[tgt].kind in (NodeKind.FUNCTION, NodeKind.METHOD)
                    ):
                        edges.append(
                            Edge(
                                source_id=caller_idx,
                                target_id=tgt,
                                kind=EdgeKind.CALLS,
                                call_site_line=_start_line(node),
                            )
                        )
            for c in reversed(node.named_children):
                stack.append((c, new_caller))
