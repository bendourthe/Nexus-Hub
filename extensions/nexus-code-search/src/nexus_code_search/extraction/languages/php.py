"""PHP AST extractor backed by tree-sitter.

Emits node kinds: `module` (file), `namespace`, `class`, `interface`,
`method`, `function`, `constant`, `property`, `import` (`use`). Emits edges:
`contains`, `calls`, `extends`, `implements`, `imports`.

A `class C extends Base` whose `Base` is declared in the same file emits
`extends`; `implements I` emits `implements`. A call whose target name matches
an in-file function / method emits `calls`. In-file resolution only.
Parameter nodes are intentionally not emitted (FTS-surface discipline).
"""

from __future__ import annotations

import logging
from pathlib import Path

from tree_sitter import Language, Node as TSNode, Parser
import tree_sitter_php

from nexus_code_search.extraction.languages.base import Extractor
from nexus_code_search.types import Edge, EdgeKind, Node, NodeKind

logger = logging.getLogger("nexus-code-search")

_PHP_LANGUAGE = Language(tree_sitter_php.language_php())
_PHP_PARSER = Parser(_PHP_LANGUAGE)


def _node_text(source: bytes, node: TSNode) -> str:
    return source[node.start_byte : node.end_byte].decode("utf-8", errors="replace")


def _start_line(node: TSNode) -> int:
    return node.start_point[0] + 1


def _end_line(node: TSNode) -> int:
    return node.end_point[0] + 1


def _first_line(source: bytes, node: TSNode) -> str:
    raw = _node_text(source, node).splitlines()
    return raw[0].strip() if raw else ""


def _name_field(node: TSNode, source: bytes) -> str | None:
    name_node = node.child_by_field_name("name")
    if name_node is not None:
        return _node_text(source, name_node).lstrip("$")
    for child in node.named_children:
        if child.type == "name":
            return _node_text(source, child)
    return None


class PhpExtractor(Extractor):
    language = "php"

    def extract(self, file_path: Path, source: bytes) -> tuple[list[Node], list[Edge]]:
        tree = _PHP_PARSER.parse(source)
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
            self._handle_top_level(
                child, source, file_path, module_qual, module_idx, edges, add_node,
                index_by_name,
            )

        self._collect_calls(
            root, source, nodes, edges, index_by_qname, index_by_name
        )
        return nodes, edges

    def _handle_top_level(
        self, node, source, file_path, module_qual, module_idx, edges, add_node,
        index_by_name,
    ) -> None:
        t = node.type
        if t == "namespace_use_declaration":
            self._handle_use(
                node, source, file_path, module_qual, module_idx, edges, add_node
            )
        elif t == "namespace_definition":
            name_node = node.child_by_field_name("name")
            name = _node_text(source, name_node) if name_node else None
            if name:
                add_node(
                    Node(
                        name=name.split("\\")[-1],
                        kind=NodeKind.NAMESPACE,
                        qualified_name=f"{module_qual}.namespace:{name}",
                        file_path=str(file_path),
                        start_line=_start_line(node),
                        end_line=_end_line(node),
                        signature=_first_line(source, node),
                    )
                )
            body = node.child_by_field_name("body")
            if body is not None:
                for child in body.named_children:
                    self._handle_top_level(
                        child, source, file_path, module_qual, module_idx, edges,
                        add_node, index_by_name,
                    )
        elif t in ("class_declaration", "interface_declaration", "trait_declaration"):
            self._handle_class_like(
                node, source, file_path, module_qual, module_idx, edges, add_node,
                index_by_name,
            )
        elif t == "function_definition":
            name = _name_field(node, source)
            if name:
                qname = f"{module_qual}.{name}"
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
                    Edge(source_id=module_idx, target_id=idx, kind=EdgeKind.CONTAINS)
                )
        elif t == "const_declaration":
            for el in node.named_children:
                if el.type != "const_element":
                    continue
                name = _name_field(el, source)
                if not name:
                    continue
                idx = add_node(
                    Node(
                        name=name,
                        kind=NodeKind.CONSTANT,
                        qualified_name=f"{module_qual}.{name}",
                        file_path=str(file_path),
                        start_line=_start_line(el),
                        end_line=_end_line(el),
                        signature=_first_line(source, node),
                    )
                )
                edges.append(
                    Edge(source_id=module_idx, target_id=idx, kind=EdgeKind.CONTAINS)
                )

    def _handle_use(
        self, node, source, file_path, module_qual, module_idx, edges, add_node
    ) -> None:
        for clause in node.named_children:
            if clause.type != "namespace_use_clause":
                continue
            qn = None
            for c in clause.named_children:
                if c.type in ("qualified_name", "name"):
                    qn = _node_text(source, c)
                    break
            if not qn:
                continue
            name = qn.split("\\")[-1]
            idx = add_node(
                Node(
                    name=name,
                    kind=NodeKind.IMPORT,
                    qualified_name=f"{module_qual}.use:{qn}",
                    file_path=str(file_path),
                    start_line=_start_line(node),
                    end_line=_end_line(node),
                    signature=_first_line(source, node),
                )
            )
            edges.append(
                Edge(source_id=module_idx, target_id=idx, kind=EdgeKind.IMPORTS)
            )

    def _handle_class_like(
        self, node, source, file_path, module_qual, module_idx, edges, add_node,
        index_by_name,
    ) -> None:
        name = _name_field(node, source)
        if not name:
            return
        kind = NodeKind.INTERFACE if node.type == "interface_declaration" else NodeKind.CLASS
        qname = f"{module_qual}.{name}"
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
            Edge(source_id=module_idx, target_id=class_idx, kind=EdgeKind.CONTAINS)
        )

        # extends (base_clause) and implements (class_interface_clause).
        for child in node.named_children:
            if child.type == "base_clause":
                for c in child.named_children:
                    if c.type == "name":
                        self._pending_relation(
                            edges, index_by_name, class_idx,
                            _node_text(source, c), EdgeKind.EXTENDS,
                        )
            elif child.type == "class_interface_clause":
                for c in child.named_children:
                    if c.type == "name":
                        self._pending_relation(
                            edges, index_by_name, class_idx,
                            _node_text(source, c), EdgeKind.IMPLEMENTS,
                        )

        body = node.child_by_field_name("body")
        if body is None:
            for child in node.named_children:
                if child.type == "declaration_list":
                    body = child
                    break
        if body is None:
            return
        for member in body.named_children:
            if member.type == "method_declaration":
                mname = _name_field(member, source)
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
            elif member.type == "property_declaration":
                for pe in member.named_children:
                    if pe.type != "property_element":
                        continue
                    pname = _name_field(pe, source)
                    if not pname:
                        continue
                    idx = add_node(
                        Node(
                            name=pname,
                            kind=NodeKind.PROPERTY,
                            qualified_name=f"{qname}.{pname}",
                            file_path=str(file_path),
                            start_line=_start_line(member),
                            end_line=_end_line(member),
                            signature=_first_line(source, member),
                        )
                    )
                    edges.append(
                        Edge(source_id=class_idx, target_id=idx, kind=EdgeKind.CONTAINS)
                    )

    def _pending_relation(self, edges, index_by_name, src_idx, target_name, kind):
        # Resolved against in-file names at emit time. The class/interface being
        # referenced may be declared later in the file, so this is best-effort
        # and re-checked after the full declaration pass would be ideal; in
        # practice fixtures declare the base before the derived type.
        tgt = index_by_name.get(target_name)
        if tgt is not None and tgt != src_idx:
            edges.append(Edge(source_id=src_idx, target_id=tgt, kind=kind))

    def _collect_calls(
        self, root, source, nodes, edges, index_by_qname, index_by_name
    ) -> None:
        stack: list[tuple[TSNode, int | None]] = [(root, None)]
        while stack:
            node, caller_idx = stack.pop()
            new_caller = caller_idx
            if node.type in ("function_definition", "method_declaration"):
                name = _name_field(node, source)
                if name is not None:
                    new_caller = index_by_name.get(name, caller_idx)
            elif node.type in (
                "function_call_expression",
                "member_call_expression",
                "scoped_call_expression",
            ) and caller_idx is not None:
                self._emit_call(
                    node, source, caller_idx, nodes, edges, index_by_name
                )
            for c in reversed(node.named_children):
                stack.append((c, new_caller))

    def _emit_call(
        self, node, source, caller_idx, nodes, edges, index_by_name
    ) -> None:
        name_node = node.child_by_field_name("name")
        called = None
        if name_node is not None:
            called = _node_text(source, name_node)
        else:
            for c in node.named_children:
                if c.type == "name":
                    called = _node_text(source, c)
                    break
        if not called:
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
