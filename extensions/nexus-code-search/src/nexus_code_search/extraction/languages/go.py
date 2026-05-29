"""Go AST extractor backed by tree-sitter.

Emits node kinds: `module` (package), `function`, `method`, `struct`,
`interface`, `field`, `import`, `constant`, `variable`. Emits edges:
`contains`, `calls`, `instantiates`, `imports`.

Go has no class inheritance and interface satisfaction is structural (not
declared), so no `extends` / `implements` / `overrides` edges are produced. A
`T{...}` composite literal whose type matches an in-file struct emits
`instantiates`; a call whose target matches an in-file function / method emits
`calls`. In-file resolution only - cross-file joins are the orchestrator's
responsibility.

Parameter nodes are intentionally not emitted (they are rarely a search target
and inflate the FTS surface); functions, methods, types, fields, and imports
are the searchable symbols.
"""

from __future__ import annotations

import logging
from pathlib import Path

from tree_sitter import Language, Node as TSNode, Parser
import tree_sitter_go

from nexus_code_search.extraction.languages.base import Extractor
from nexus_code_search.types import Edge, EdgeKind, Node, NodeKind

logger = logging.getLogger("nexus-code-search")

_GO_LANGUAGE = Language(tree_sitter_go.language())
_GO_PARSER = Parser(_GO_LANGUAGE)


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


class GoExtractor(Extractor):
    language = "go"

    def extract(self, file_path: Path, source: bytes) -> tuple[list[Node], list[Edge]]:
        tree = _GO_PARSER.parse(source)
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
            self._handle_top_level(
                child, source, file_path, module_qual, module_idx, edges, add_node
            )

        self._collect_calls(
            root, source, module_qual, nodes, edges, index_by_qname, index_by_name
        )
        return nodes, edges

    def _handle_top_level(
        self,
        node: TSNode,
        source: bytes,
        file_path: Path,
        module_qual: str,
        module_idx: int,
        edges: list[Edge],
        add_node,
    ) -> None:
        t = node.type
        if t == "import_declaration":
            self._handle_import(
                node, source, file_path, module_qual, module_idx, edges, add_node
            )
        elif t == "function_declaration":
            self._handle_function(
                node, source, file_path, module_qual, module_idx, edges, add_node, None
            )
        elif t == "method_declaration":
            self._handle_function(
                node,
                source,
                file_path,
                module_qual,
                module_idx,
                edges,
                add_node,
                self._receiver_type(node, source),
            )
        elif t == "type_declaration":
            self._handle_type(
                node, source, file_path, module_qual, module_idx, edges, add_node
            )
        elif t in ("const_declaration", "var_declaration"):
            self._handle_const_var(
                node, source, file_path, module_qual, module_idx, edges, add_node, t
            )

    def _handle_import(
        self, node, source, file_path, module_qual, module_idx, edges, add_node
    ) -> None:
        specs: list[TSNode] = []
        for child in node.named_children:
            if child.type == "import_spec":
                specs.append(child)
            elif child.type == "import_spec_list":
                specs.extend(c for c in child.named_children if c.type == "import_spec")
        for spec in specs:
            path_node = spec.child_by_field_name("path")
            path = _node_text(source, path_node).strip().strip('"') if path_node else ""
            if not path:
                continue
            name = path.rsplit("/", 1)[-1]
            qname = f"{module_qual}.import:{path}"
            idx = add_node(
                Node(
                    name=name,
                    kind=NodeKind.IMPORT,
                    qualified_name=qname,
                    file_path=str(file_path),
                    start_line=_start_line(spec),
                    end_line=_end_line(spec),
                    signature=_first_line(source, spec),
                )
            )
            edges.append(
                Edge(source_id=module_idx, target_id=idx, kind=EdgeKind.IMPORTS)
            )

    def _receiver_type(self, node: TSNode, source: bytes) -> str | None:
        recv = node.child_by_field_name("receiver")
        if recv is None:
            return None
        for pd in recv.named_children:
            if pd.type == "parameter_declaration":
                t = pd.child_by_field_name("type")
                if t is not None:
                    txt = _node_text(source, t).lstrip("*").strip()
                    return txt.split(".")[-1] or None
        return None

    def _handle_function(
        self,
        node,
        source,
        file_path,
        module_qual,
        module_idx,
        edges,
        add_node,
        receiver_type: str | None,
    ) -> None:
        name_node = node.child_by_field_name("name")
        if name_node is None:
            return
        name = _node_text(source, name_node)
        kind = NodeKind.METHOD if receiver_type else NodeKind.FUNCTION
        qprefix = f"{module_qual}.{receiver_type}" if receiver_type else module_qual
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
        edges.append(Edge(source_id=module_idx, target_id=idx, kind=EdgeKind.CONTAINS))

    def _handle_type(
        self, node, source, file_path, module_qual, module_idx, edges, add_node
    ) -> None:
        for spec in node.named_children:
            if spec.type != "type_spec":
                continue
            name_node = spec.child_by_field_name("name")
            type_node = spec.child_by_field_name("type")
            if name_node is None or type_node is None:
                continue
            name = _node_text(source, name_node)
            if type_node.type == "struct_type":
                kind = NodeKind.STRUCT
            elif type_node.type == "interface_type":
                kind = NodeKind.INTERFACE
            else:
                kind = NodeKind.TYPE_ALIAS
            qname = f"{module_qual}.{name}"
            type_idx = add_node(
                Node(
                    name=name,
                    kind=kind,
                    qualified_name=qname,
                    file_path=str(file_path),
                    start_line=_start_line(spec),
                    end_line=_end_line(spec),
                    signature=_first_line(source, spec),
                )
            )
            edges.append(
                Edge(source_id=module_idx, target_id=type_idx, kind=EdgeKind.CONTAINS)
            )
            if type_node.type == "struct_type":
                self._handle_struct_fields(
                    type_node, source, file_path, qname, type_idx, edges, add_node
                )

    def _handle_struct_fields(
        self, struct_node, source, file_path, struct_qname, struct_idx, edges, add_node
    ) -> None:
        for child in struct_node.named_children:
            if child.type != "field_declaration_list":
                continue
            for fd in child.named_children:
                if fd.type != "field_declaration":
                    continue
                for ident in fd.named_children:
                    if ident.type != "field_identifier":
                        continue
                    fname = _node_text(source, ident)
                    idx = add_node(
                        Node(
                            name=fname,
                            kind=NodeKind.FIELD,
                            qualified_name=f"{struct_qname}.{fname}",
                            file_path=str(file_path),
                            start_line=_start_line(fd),
                            end_line=_end_line(fd),
                            signature=_first_line(source, fd),
                        )
                    )
                    edges.append(
                        Edge(
                            source_id=struct_idx,
                            target_id=idx,
                            kind=EdgeKind.CONTAINS,
                        )
                    )

    def _handle_const_var(
        self, node, source, file_path, module_qual, module_idx, edges, add_node, t
    ) -> None:
        spec_type = "const_spec" if t == "const_declaration" else "var_spec"
        kind = NodeKind.CONSTANT if t == "const_declaration" else NodeKind.VARIABLE
        specs: list[TSNode] = []
        for child in node.named_children:
            if child.type == spec_type:
                specs.append(child)
            elif child.type in ("const_spec_list", "var_spec_list"):
                specs.extend(c for c in child.named_children if c.type == spec_type)
        for spec in specs:
            for ident in spec.named_children:
                if ident.type != "identifier":
                    continue
                name = _node_text(source, ident)
                idx = add_node(
                    Node(
                        name=name,
                        kind=kind,
                        qualified_name=f"{module_qual}.{name}",
                        file_path=str(file_path),
                        start_line=_start_line(spec),
                        end_line=_end_line(spec),
                        signature=_first_line(source, spec),
                    )
                )
                edges.append(
                    Edge(source_id=module_idx, target_id=idx, kind=EdgeKind.CONTAINS)
                )

    def _collect_calls(
        self, root, source, module_qual, nodes, edges, index_by_qname, index_by_name
    ) -> None:
        stack: list[tuple[TSNode, str | None]] = [(root, None)]
        while stack:
            node, fn_q = stack.pop()
            new_fn = fn_q
            if node.type == "function_declaration":
                nn = node.child_by_field_name("name")
                if nn is not None:
                    new_fn = f"{module_qual}.{_node_text(source, nn)}"
            elif node.type == "method_declaration":
                nn = node.child_by_field_name("name")
                if nn is not None:
                    rt = self._receiver_type(node, source)
                    prefix = f"{module_qual}.{rt}" if rt else module_qual
                    new_fn = f"{prefix}.{_node_text(source, nn)}"
            elif node.type == "call_expression" and fn_q:
                self._emit_call(
                    node, source, module_qual, fn_q, nodes, edges,
                    index_by_qname, index_by_name,
                )
            elif node.type == "composite_literal" and fn_q:
                self._emit_composite(
                    node, source, fn_q, nodes, edges, index_by_qname, index_by_name
                )
            for c in reversed(node.named_children):
                stack.append((c, new_fn))

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
            if nodes[tgt].kind == NodeKind.STRUCT
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

    def _emit_composite(
        self, node, source, fn_q, nodes, edges, index_by_qname, index_by_name
    ) -> None:
        caller_idx = index_by_qname.get(fn_q)
        if caller_idx is None:
            return
        tn = node.child_by_field_name("type")
        if tn is None:
            return
        tname = _node_text(source, tn).split(".")[-1].strip()
        tgt = index_by_name.get(tname)
        if tgt is None or tgt == caller_idx or nodes[tgt].kind != NodeKind.STRUCT:
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
        if fn_field.type == "selector_expression":
            field = fn_field.child_by_field_name("field")
            return _node_text(source, field) if field else ""
        return ""
