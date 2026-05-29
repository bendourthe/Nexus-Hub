"""Rust AST extractor backed by tree-sitter.

Emits node kinds: `module` (file + `mod`), `function`, `method` (functions
inside an `impl` or a `trait`), `struct`, `enum`, `trait`, `import`,
`constant`. Emits edges: `contains`, `calls`, `instantiates`, `implements`,
`imports`.

Methods are functions inside an `impl` block; their qualified name is keyed by
the impl target type (`module.Type.method`). An `impl Trait for Type` block
emits an `implements` edge from the type to the trait (both in-file). A
`Type { .. }` struct literal whose name matches an in-file struct emits
`instantiates`. In-file resolution only.

Parameter nodes are intentionally not emitted.
"""

from __future__ import annotations

import logging
from pathlib import Path

from tree_sitter import Language, Node as TSNode, Parser
import tree_sitter_rust

from nexus_code_search.extraction.languages.base import Extractor
from nexus_code_search.types import Edge, EdgeKind, Node, NodeKind

logger = logging.getLogger("nexus-code-search")

_RS_LANGUAGE = Language(tree_sitter_rust.language())
_RS_PARSER = Parser(_RS_LANGUAGE)


def _node_text(source: bytes, node: TSNode) -> str:
    return source[node.start_byte : node.end_byte].decode("utf-8", errors="replace")


def _start_line(node: TSNode) -> int:
    return node.start_point[0] + 1


def _end_line(node: TSNode) -> int:
    return node.end_point[0] + 1


def _first_line(source: bytes, node: TSNode) -> str:
    raw = _node_text(source, node).splitlines()
    return raw[0].strip() if raw else ""


def _module_name(file_path: Path) -> str:
    return file_path.stem


class RustExtractor(Extractor):
    language = "rust"

    def extract(self, file_path: Path, source: bytes) -> tuple[list[Node], list[Edge]]:
        tree = _RS_PARSER.parse(source)
        root = tree.root_node
        module_qual = _module_name(file_path)

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
            self._handle_item(
                child, source, file_path, module_qual, module_idx, edges,
                index_by_name, add_node,
            )

        self._collect_calls(
            root, source, module_qual, nodes, edges, index_by_qname, index_by_name
        )
        return nodes, edges

    def _handle_item(
        self, node, source, file_path, module_qual, module_idx, edges,
        index_by_name, add_node,
    ) -> None:
        t = node.type
        if t == "use_declaration":
            self._handle_use(
                node, source, file_path, module_qual, module_idx, edges, add_node
            )
        elif t == "function_item":
            self._handle_function(
                node, source, file_path, module_qual, module_idx, None, edges, add_node
            )
        elif t == "struct_item":
            self._handle_named_type(
                node, source, file_path, module_qual, module_idx, NodeKind.STRUCT,
                edges, add_node,
            )
        elif t == "enum_item":
            self._handle_named_type(
                node, source, file_path, module_qual, module_idx, NodeKind.ENUM,
                edges, add_node,
            )
        elif t == "trait_item":
            self._handle_trait(
                node, source, file_path, module_qual, module_idx, edges, add_node
            )
        elif t == "impl_item":
            self._handle_impl(
                node, source, file_path, module_qual, module_idx, edges,
                index_by_name, add_node,
            )
        elif t == "mod_item":
            name_node = node.child_by_field_name("name")
            if name_node is not None:
                name = _node_text(source, name_node)
                idx = add_node(
                    Node(
                        name=name,
                        kind=NodeKind.NAMESPACE,
                        qualified_name=f"{module_qual}.{name}",
                        file_path=str(file_path),
                        start_line=_start_line(node),
                        end_line=_end_line(node),
                        signature=_first_line(source, node),
                    )
                )
                edges.append(
                    Edge(source_id=module_idx, target_id=idx, kind=EdgeKind.CONTAINS)
                )
        elif t in ("const_item", "static_item"):
            name_node = node.child_by_field_name("name")
            if name_node is not None:
                name = _node_text(source, name_node)
                idx = add_node(
                    Node(
                        name=name,
                        kind=NodeKind.CONSTANT,
                        qualified_name=f"{module_qual}.{name}",
                        file_path=str(file_path),
                        start_line=_start_line(node),
                        end_line=_end_line(node),
                        signature=_first_line(source, node),
                    )
                )
                edges.append(
                    Edge(source_id=module_idx, target_id=idx, kind=EdgeKind.CONTAINS)
                )

    def _handle_use(
        self, node, source, file_path, module_qual, module_idx, edges, add_node
    ) -> None:
        # Emit one import node named after the final path segment.
        text = _node_text(source, node).rstrip(";").replace("use", "", 1).strip()
        if not text:
            return
        # Take the last identifier-like segment, ignoring braces/aliases.
        tail = text.split("::")[-1].split(" as ")[0].strip().strip("{}").strip()
        if not tail or tail == "*":
            tail = text.split("::")[-1].strip()
        name = tail.split(",")[0].strip() or text
        idx = add_node(
            Node(
                name=name,
                kind=NodeKind.IMPORT,
                qualified_name=f"{module_qual}.import:{text}",
                file_path=str(file_path),
                start_line=_start_line(node),
                end_line=_end_line(node),
                signature=_first_line(source, node),
            )
        )
        edges.append(Edge(source_id=module_idx, target_id=idx, kind=EdgeKind.IMPORTS))

    def _handle_function(
        self, node, source, file_path, module_qual, parent_idx, impl_type, edges, add_node
    ) -> int | None:
        name_node = node.child_by_field_name("name")
        if name_node is None:
            return None
        name = _node_text(source, name_node)
        kind = NodeKind.METHOD if impl_type else NodeKind.FUNCTION
        qprefix = f"{module_qual}.{impl_type}" if impl_type else module_qual
        qname = f"{qprefix}.{name}"
        idx = add_node(
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
        edges.append(Edge(source_id=parent_idx, target_id=idx, kind=EdgeKind.CONTAINS))
        return idx

    def _handle_named_type(
        self, node, source, file_path, module_qual, module_idx, kind, edges, add_node
    ) -> int | None:
        name_node = node.child_by_field_name("name")
        if name_node is None:
            return None
        name = _node_text(source, name_node)
        idx = add_node(
            Node(
                name=name,
                kind=kind,
                qualified_name=f"{module_qual}.{name}",
                file_path=str(file_path),
                start_line=_start_line(node),
                end_line=_end_line(node),
                signature=_first_line(source, node),
            )
        )
        edges.append(Edge(source_id=module_idx, target_id=idx, kind=EdgeKind.CONTAINS))
        return idx

    def _handle_trait(
        self, node, source, file_path, module_qual, module_idx, edges, add_node
    ) -> None:
        name_node = node.child_by_field_name("name")
        if name_node is None:
            return
        name = _node_text(source, name_node)
        qname = f"{module_qual}.{name}"
        trait_idx = add_node(
            Node(
                name=name,
                kind=NodeKind.TRAIT,
                qualified_name=qname,
                file_path=str(file_path),
                start_line=_start_line(node),
                end_line=_end_line(node),
                signature=_first_line(source, node),
            )
        )
        edges.append(
            Edge(source_id=module_idx, target_id=trait_idx, kind=EdgeKind.CONTAINS)
        )
        body = node.child_by_field_name("body")
        for member in body.named_children if body else ():
            if member.type in ("function_signature_item", "function_item"):
                m_name_node = member.child_by_field_name("name")
                if m_name_node is None:
                    continue
                m_name = _node_text(source, m_name_node)
                m_idx = add_node(
                    Node(
                        name=m_name,
                        kind=NodeKind.METHOD,
                        qualified_name=f"{qname}.{m_name}",
                        file_path=str(file_path),
                        start_line=_start_line(member),
                        end_line=_end_line(member),
                        signature=_first_line(source, member),
                    )
                )
                edges.append(
                    Edge(source_id=trait_idx, target_id=m_idx, kind=EdgeKind.CONTAINS)
                )

    def _handle_impl(
        self, node, source, file_path, module_qual, module_idx, edges,
        index_by_name, add_node,
    ) -> None:
        type_node = node.child_by_field_name("type")
        if type_node is None:
            return
        impl_type = _node_text(source, type_node).split("<")[0].strip().split("::")[-1]
        impl_type_idx = index_by_name.get(impl_type)
        # `impl Trait for Type` -> implements edge (type -> trait), in-file only.
        trait_node = node.child_by_field_name("trait")
        if trait_node is not None and impl_type_idx is not None:
            trait_name = _node_text(source, trait_node).split("<")[0].strip().split("::")[-1]
            trait_idx = index_by_name.get(trait_name)
            if trait_idx is not None and trait_idx != impl_type_idx:
                edges.append(
                    Edge(
                        source_id=impl_type_idx,
                        target_id=trait_idx,
                        kind=EdgeKind.IMPLEMENTS,
                    )
                )
        body = node.child_by_field_name("body")
        parent_idx = impl_type_idx if impl_type_idx is not None else module_idx
        for member in body.named_children if body else ():
            if member.type == "function_item":
                self._handle_function(
                    member, source, file_path, module_qual, parent_idx, impl_type,
                    edges, add_node,
                )

    def _collect_calls(
        self, root, source, module_qual, nodes, edges, index_by_qname, index_by_name
    ) -> None:
        stack: list[tuple[TSNode, str | None, str | None]] = [(root, None, None)]
        while stack:
            node, fn_q, impl_type = stack.pop()
            new_fn = fn_q
            new_impl = impl_type
            if node.type == "impl_item":
                tn = node.child_by_field_name("type")
                new_impl = (
                    _node_text(source, tn).split("<")[0].strip().split("::")[-1]
                    if tn
                    else impl_type
                )
            elif node.type == "function_item":
                nn = node.child_by_field_name("name")
                if nn is not None:
                    prefix = f"{module_qual}.{impl_type}" if impl_type else module_qual
                    new_fn = f"{prefix}.{_node_text(source, nn)}"
            elif node.type == "call_expression" and fn_q:
                self._emit_call(
                    node, source, module_qual, fn_q, nodes, edges,
                    index_by_qname, index_by_name,
                )
            elif node.type == "struct_expression" and fn_q:
                self._emit_struct_literal(
                    node, source, fn_q, nodes, edges, index_by_qname, index_by_name
                )
            for c in reversed(node.named_children):
                stack.append((c, new_fn, new_impl))

    def _emit_call(
        self, node, source, module_qual, fn_q, nodes, edges, index_by_qname, index_by_name
    ) -> None:
        caller_idx = index_by_qname.get(fn_q)
        if caller_idx is None:
            return
        ff = node.child_by_field_name("function")
        called = self._resolve_called_name(ff, source) if ff else ""
        if not called:
            return
        tgt = index_by_qname.get(f"{module_qual}.{called}") or index_by_name.get(
            called.split(".")[-1]
        )
        if tgt is None or tgt == caller_idx:
            return
        kind = (
            EdgeKind.INSTANTIATES
            if nodes[tgt].kind in (NodeKind.STRUCT, NodeKind.ENUM)
            else EdgeKind.CALLS
        )
        edges.append(
            Edge(
                source_id=caller_idx,
                target_id=tgt,
                kind=kind,
                call_site_line=_start_line(node),
            )
        )

    def _emit_struct_literal(
        self, node, source, fn_q, nodes, edges, index_by_qname, index_by_name
    ) -> None:
        caller_idx = index_by_qname.get(fn_q)
        if caller_idx is None:
            return
        name_node = node.child_by_field_name("name")
        if name_node is None:
            return
        tname = _node_text(source, name_node).split("::")[-1].strip()
        tgt = index_by_name.get(tname)
        if tgt is None or tgt == caller_idx:
            return
        if nodes[tgt].kind not in (NodeKind.STRUCT, NodeKind.ENUM):
            return
        edges.append(
            Edge(
                source_id=caller_idx,
                target_id=tgt,
                kind=EdgeKind.INSTANTIATES,
                call_site_line=_start_line(node),
            )
        )

    def _resolve_called_name(self, fn_field: TSNode, source: bytes) -> str:
        if fn_field.type == "identifier":
            return _node_text(source, fn_field)
        if fn_field.type == "scoped_identifier":
            name = fn_field.child_by_field_name("name")
            return _node_text(source, name) if name else ""
        if fn_field.type == "field_expression":
            field = fn_field.child_by_field_name("field")
            return _node_text(source, field) if field else ""
        return ""
