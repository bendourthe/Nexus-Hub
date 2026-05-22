"""TypeScript / TSX AST extractor backed by tree-sitter.

Emits the following node kinds: `class`, `interface`, `function`, `method`,
`type_alias`, `import`, `export`, `property`, `variable`, `constant`. Emits
edges: `contains`, `calls`, `extends`, `implements`, `imports`, `exports`.

Same in-file resolution scope as the Python extractor: cross-file references
are left to the orchestrator.
"""

from __future__ import annotations

import logging
from pathlib import Path

from tree_sitter import Language, Node as TSNode, Parser
import tree_sitter_typescript

from nexus_code_search.extraction.languages.base import Extractor
from nexus_code_search.types import Edge, EdgeKind, Node, NodeKind

logger = logging.getLogger("nexus-code-search")

_TS_LANGUAGE = Language(tree_sitter_typescript.language_typescript())
_TSX_LANGUAGE = Language(tree_sitter_typescript.language_tsx())
_TS_PARSER = Parser(_TS_LANGUAGE)
_TSX_PARSER = Parser(_TSX_LANGUAGE)


def _node_text(source: bytes, node: TSNode) -> str:
    return source[node.start_byte : node.end_byte].decode("utf-8", errors="replace")


def _start_line(node: TSNode) -> int:
    return node.start_point[0] + 1


def _end_line(node: TSNode) -> int:
    return node.end_point[0] + 1


def _signature_first_line(source: bytes, node: TSNode) -> str:
    raw = _node_text(source, node).splitlines()
    return raw[0].strip() if raw else ""


def _module_name(file_path: Path) -> str:
    return file_path.stem


class TypeScriptExtractor(Extractor):
    language = "typescript"

    def extract(self, file_path: Path, source: bytes) -> tuple[list[Node], list[Edge]]:
        parser = _TSX_PARSER if file_path.suffix.lower() == ".tsx" else _TS_PARSER
        tree = parser.parse(source)
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
                child,
                source,
                file_path,
                module_qual,
                module_idx,
                nodes,
                edges,
                index_by_qname,
                index_by_name,
                add_node,
            )

        # Second pass for call edges.
        self._collect_calls(
            root,
            source,
            module_qual,
            edges,
            index_by_qname,
            index_by_name,
        )

        return nodes, edges

    def _handle_top_level(
        self,
        node: TSNode,
        source: bytes,
        file_path: Path,
        module_qual: str,
        module_idx: int,
        nodes: list[Node],
        edges: list[Edge],
        index_by_qname: dict[str, int],
        index_by_name: dict[str, int],
        add_node,
    ) -> None:
        t = node.type
        if t in ("import_statement",):
            self._handle_import(
                node, source, file_path, module_qual, module_idx, edges, add_node
            )
        elif t == "export_statement":
            # Unwrap one level: an export_statement wraps a class/function/var.
            declaration = node.child_by_field_name("declaration")
            if declaration is not None:
                self._handle_top_level(
                    declaration,
                    source,
                    file_path,
                    module_qual,
                    module_idx,
                    nodes,
                    edges,
                    index_by_qname,
                    index_by_name,
                    add_node,
                )
            self._handle_export(
                node, source, file_path, module_qual, module_idx, edges, add_node
            )
        elif t == "class_declaration":
            self._handle_class(
                node,
                source,
                file_path,
                module_qual,
                module_idx,
                nodes,
                edges,
                index_by_qname,
                index_by_name,
                add_node,
                kind=NodeKind.CLASS,
            )
        elif t == "interface_declaration":
            self._handle_class(
                node,
                source,
                file_path,
                module_qual,
                module_idx,
                nodes,
                edges,
                index_by_qname,
                index_by_name,
                add_node,
                kind=NodeKind.INTERFACE,
            )
        elif t == "function_declaration":
            self._handle_function(
                node,
                source,
                file_path,
                module_qual,
                module_idx,
                parent_class=None,
                nodes=nodes,
                edges=edges,
                index_by_qname=index_by_qname,
                index_by_name=index_by_name,
                add_node=add_node,
            )
        elif t == "type_alias_declaration":
            self._handle_type_alias(
                node, source, file_path, module_qual, module_idx, edges, add_node
            )
        elif t in ("variable_statement", "lexical_declaration"):
            self._handle_variable(
                node, source, file_path, module_qual, module_idx, edges, add_node
            )

    def _handle_import(
        self,
        node: TSNode,
        source: bytes,
        file_path: Path,
        module_qual: str,
        module_idx: int,
        edges: list[Edge],
        add_node,
    ) -> None:
        # `from "<module>"` is the source; the imported names are the targets.
        source_node = node.child_by_field_name("source")
        source_text = (
            _node_text(source, source_node).strip().strip("'\"") if source_node else ""
        )
        names: list[str] = []
        clause = None
        for child in node.named_children:
            if child.type == "import_clause":
                clause = child
                break
        if clause is not None:
            for sub in clause.named_children:
                if sub.type == "identifier":
                    names.append(_node_text(source, sub))
                elif sub.type == "named_imports":
                    for spec in sub.named_children:
                        if spec.type == "import_specifier":
                            n_node = spec.child_by_field_name("name")
                            if n_node is not None:
                                names.append(_node_text(source, n_node))
                elif sub.type == "namespace_import":
                    for spec in sub.named_children:
                        if spec.type == "identifier":
                            names.append(_node_text(source, spec))
        if not names:
            names = [source_text]
        for name in names:
            qname = (
                f"{module_qual}.import:{source_text}:{name}"
                if source_text
                else f"{module_qual}.import:{name}"
            )
            idx = add_node(
                Node(
                    name=name,
                    kind=NodeKind.IMPORT,
                    qualified_name=qname,
                    file_path=str(file_path),
                    start_line=_start_line(node),
                    end_line=_end_line(node),
                    signature=_signature_first_line(source, node),
                )
            )
            edges.append(
                Edge(source_id=module_idx, target_id=idx, kind=EdgeKind.IMPORTS)
            )

    def _handle_export(
        self,
        node: TSNode,
        source: bytes,
        file_path: Path,
        module_qual: str,
        module_idx: int,
        edges: list[Edge],
        add_node,
    ) -> None:
        # Track explicit `export { foo }` clauses. Inline `export function ...`
        # is already handled by the unwrap in _handle_top_level.
        for child in node.named_children:
            if child.type != "export_clause":
                continue
            for spec in child.named_children:
                if spec.type == "export_specifier":
                    n_node = spec.child_by_field_name("name")
                    if n_node is None:
                        continue
                    name = _node_text(source, n_node)
                    qname = f"{module_qual}.export:{name}"
                    idx = add_node(
                        Node(
                            name=name,
                            kind=NodeKind.EXPORT,
                            qualified_name=qname,
                            file_path=str(file_path),
                            start_line=_start_line(spec),
                            end_line=_end_line(spec),
                        )
                    )
                    edges.append(
                        Edge(source_id=module_idx, target_id=idx, kind=EdgeKind.EXPORTS)
                    )

    def _handle_class(
        self,
        node: TSNode,
        source: bytes,
        file_path: Path,
        module_qual: str,
        module_idx: int,
        nodes: list[Node],
        edges: list[Edge],
        index_by_qname: dict[str, int],
        index_by_name: dict[str, int],
        add_node,
        kind: NodeKind,
    ) -> None:
        name_node = node.child_by_field_name("name")
        if name_node is None:
            return
        name = _node_text(source, name_node)
        qname = f"{module_qual}.{name}"
        class_idx = add_node(
            Node(
                name=name,
                kind=kind,
                qualified_name=qname,
                file_path=str(file_path),
                start_line=_start_line(node),
                end_line=_end_line(node),
                signature=_signature_first_line(source, node),
            )
        )
        edges.append(
            Edge(source_id=module_idx, target_id=class_idx, kind=EdgeKind.CONTAINS)
        )

        # `extends` and `implements` clauses live under `class_heritage`. The
        # heritage child is not exposed under a field name in this grammar
        # version, so walk named children to find it.
        heritage = None
        for child in node.named_children:
            if child.type == "class_heritage":
                heritage = child
                break
        for hc in heritage.named_children if heritage else ():
            base_kind = (
                EdgeKind.EXTENDS
                if hc.type == "extends_clause"
                else (EdgeKind.IMPLEMENTS if hc.type == "implements_clause" else None)
            )
            if base_kind is None:
                continue
            # The clause's named children are identifier / type_identifier
            # nodes - one per base type.
            for base in hc.named_children:
                base_text = _node_text(source, base).split("<")[0].strip()
                simple = base_text.split(".")[-1].strip()
                if not simple:
                    continue
                target = index_by_name.get(simple)
                if target is not None and target != class_idx:
                    edges.append(
                        Edge(source_id=class_idx, target_id=target, kind=base_kind)
                    )

        body = node.child_by_field_name("body")
        if body is None:
            return
        for member in body.named_children:
            if member.type == "method_definition":
                self._handle_function(
                    member,
                    source,
                    file_path,
                    module_qual,
                    class_idx,
                    parent_class=name,
                    nodes=nodes,
                    edges=edges,
                    index_by_qname=index_by_qname,
                    index_by_name=index_by_name,
                    add_node=add_node,
                )
            elif member.type in ("public_field_definition", "property_signature"):
                prop_name_node = member.child_by_field_name("name")
                if prop_name_node is None:
                    continue
                prop_name = _node_text(source, prop_name_node)
                pqname = f"{qname}.{prop_name}"
                pidx = add_node(
                    Node(
                        name=prop_name,
                        kind=NodeKind.PROPERTY,
                        qualified_name=pqname,
                        file_path=str(file_path),
                        start_line=_start_line(member),
                        end_line=_end_line(member),
                        signature=_signature_first_line(source, member),
                    )
                )
                edges.append(
                    Edge(source_id=class_idx, target_id=pidx, kind=EdgeKind.CONTAINS)
                )

    def _handle_function(
        self,
        node: TSNode,
        source: bytes,
        file_path: Path,
        module_qual: str,
        parent_idx: int,
        parent_class: str | None,
        nodes: list[Node],
        edges: list[Edge],
        index_by_qname: dict[str, int],
        index_by_name: dict[str, int],
        add_node,
    ) -> None:
        name_node = node.child_by_field_name("name")
        if name_node is None:
            return
        name = _node_text(source, name_node)
        kind = NodeKind.METHOD if parent_class is not None else NodeKind.FUNCTION
        qprefix = f"{module_qual}.{parent_class}" if parent_class else module_qual
        qname = f"{qprefix}.{name}"
        fn_idx = add_node(
            Node(
                name=name,
                kind=kind,
                qualified_name=qname,
                file_path=str(file_path),
                start_line=_start_line(node),
                end_line=_end_line(node),
                signature=_signature_first_line(source, node),
            )
        )
        edges.append(
            Edge(source_id=parent_idx, target_id=fn_idx, kind=EdgeKind.CONTAINS)
        )

        params = node.child_by_field_name("parameters")
        if params is not None:
            for child in params.named_children:
                # required_parameter / optional_parameter wrap an identifier or
                # pattern.
                pname = self._param_name(child, source)
                if not pname:
                    continue
                pqname = f"{qname}.{pname}"
                pidx = add_node(
                    Node(
                        name=pname,
                        kind=NodeKind.PARAMETER,
                        qualified_name=pqname,
                        file_path=str(file_path),
                        start_line=_start_line(child),
                        end_line=_end_line(child),
                        signature=_node_text(source, child),
                    )
                )
                edges.append(
                    Edge(source_id=fn_idx, target_id=pidx, kind=EdgeKind.CONTAINS)
                )

    def _param_name(self, node: TSNode, source: bytes) -> str:
        pat = node.child_by_field_name("pattern")
        if pat is not None and pat.type == "identifier":
            return _node_text(source, pat)
        if node.type == "identifier":
            return _node_text(source, node)
        for child in node.named_children:
            if child.type == "identifier":
                return _node_text(source, child)
        return ""

    def _handle_type_alias(
        self,
        node: TSNode,
        source: bytes,
        file_path: Path,
        module_qual: str,
        module_idx: int,
        edges: list[Edge],
        add_node,
    ) -> None:
        name_node = node.child_by_field_name("name")
        if name_node is None:
            return
        name = _node_text(source, name_node)
        qname = f"{module_qual}.{name}"
        idx = add_node(
            Node(
                name=name,
                kind=NodeKind.TYPE_ALIAS,
                qualified_name=qname,
                file_path=str(file_path),
                start_line=_start_line(node),
                end_line=_end_line(node),
                signature=_signature_first_line(source, node),
            )
        )
        edges.append(Edge(source_id=module_idx, target_id=idx, kind=EdgeKind.CONTAINS))

    def _handle_variable(
        self,
        node: TSNode,
        source: bytes,
        file_path: Path,
        module_qual: str,
        module_idx: int,
        edges: list[Edge],
        add_node,
    ) -> None:
        # variable_statement -> variable_declaration_list; lexical_declaration
        # ('const' / 'let') has direct variable_declarators.
        declarators: list[TSNode] = []
        for child in node.named_children:
            if child.type == "variable_declarator":
                declarators.append(child)
            elif child.type == "variable_declaration":
                declarators.extend(
                    c for c in child.named_children if c.type == "variable_declarator"
                )
        is_const = _node_text(source, node).lstrip().startswith("const")
        for d in declarators:
            name_node = d.child_by_field_name("name")
            if name_node is None or name_node.type != "identifier":
                continue
            name = _node_text(source, name_node)
            kind = NodeKind.CONSTANT if is_const else NodeKind.VARIABLE
            qname = f"{module_qual}.{name}"
            idx = add_node(
                Node(
                    name=name,
                    kind=kind,
                    qualified_name=qname,
                    file_path=str(file_path),
                    start_line=_start_line(d),
                    end_line=_end_line(d),
                    signature=_node_text(source, d).splitlines()[0],
                )
            )
            edges.append(
                Edge(source_id=module_idx, target_id=idx, kind=EdgeKind.CONTAINS)
            )

    def _collect_calls(
        self,
        root: TSNode,
        source: bytes,
        module_qual: str,
        edges: list[Edge],
        index_by_qname: dict[str, int],
        index_by_name: dict[str, int],
    ) -> None:
        stack: list[tuple[TSNode, str | None, str | None]] = [(root, None, None)]
        while stack:
            node, fn_q, cls_n = stack.pop()
            new_fn = fn_q
            new_cls = cls_n
            if node.type in ("class_declaration", "interface_declaration"):
                cls_name_node = node.child_by_field_name("name")
                new_cls = _node_text(source, cls_name_node) if cls_name_node else cls_n
            elif node.type in ("function_declaration", "method_definition"):
                name_node = node.child_by_field_name("name")
                if name_node is not None:
                    fname = _node_text(source, name_node)
                    qprefix = f"{module_qual}.{cls_n}" if cls_n else module_qual
                    new_fn = f"{qprefix}.{fname}"
            elif node.type == "call_expression":
                caller_idx = index_by_qname.get(fn_q) if fn_q else None
                if caller_idx is not None:
                    fn_field = node.child_by_field_name("function")
                    if fn_field is not None:
                        called = self._resolve_called_name(fn_field, source)
                        if called:
                            target_idx = index_by_qname.get(
                                f"{module_qual}.{called}"
                            ) or index_by_name.get(called.split(".")[-1])
                            if target_idx is not None and target_idx != caller_idx:
                                edges.append(
                                    Edge(
                                        source_id=caller_idx,
                                        target_id=target_idx,
                                        kind=EdgeKind.CALLS,
                                        call_site_line=_start_line(node),
                                    )
                                )
            for c in reversed(node.named_children):
                stack.append((c, new_fn, new_cls))

    def _resolve_called_name(self, fn_field: TSNode, source: bytes) -> str:
        if fn_field.type == "identifier":
            return _node_text(source, fn_field)
        if fn_field.type == "member_expression":
            obj = fn_field.child_by_field_name("object")
            prop = fn_field.child_by_field_name("property")
            obj_text = _node_text(source, obj) if obj else ""
            prop_text = _node_text(source, prop) if prop else ""
            if obj_text and prop_text:
                return f"{obj_text}.{prop_text}"
            return prop_text
        return ""
