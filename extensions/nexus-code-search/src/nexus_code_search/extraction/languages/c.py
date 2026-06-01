"""C AST extractor backed by tree-sitter.

Emits node kinds: `module` (file), `function`, `struct`, `field`, `enum`,
`enum_member`, `type_alias` (typedef), `import` (`#include`). Emits edges:
`contains`, `calls`, `imports`.

C has no classes or inheritance, so no `extends` / `implements` edges. A call
whose target identifier matches an in-file function emits `calls`. In-file
resolution only. Parameter nodes are intentionally not emitted (FTS-surface
discipline), matching the Go extractor.
"""

from __future__ import annotations

import logging
from pathlib import Path

from tree_sitter import Language, Node as TSNode, Parser
import tree_sitter_c

from nexus_code_search.extraction.languages.base import Extractor
from nexus_code_search.types import Edge, EdgeKind, Node, NodeKind

logger = logging.getLogger("nexus-code-search")

_C_LANGUAGE = Language(tree_sitter_c.language())
_C_PARSER = Parser(_C_LANGUAGE)


def _node_text(source: bytes, node: TSNode) -> str:
    return source[node.start_byte : node.end_byte].decode("utf-8", errors="replace")


def _start_line(node: TSNode) -> int:
    return node.start_point[0] + 1


def _end_line(node: TSNode) -> int:
    return node.end_point[0] + 1


def _first_line(source: bytes, node: TSNode) -> str:
    raw = _node_text(source, node).splitlines()
    return raw[0].strip() if raw else ""


def _declarator_identifier(node: TSNode | None) -> TSNode | None:
    """Descend a (possibly pointer/array-wrapped) declarator to its identifier."""
    while node is not None:
        if node.type in ("identifier", "field_identifier", "type_identifier"):
            return node
        nxt = node.child_by_field_name("declarator")
        if nxt is None:
            # function_declarator nests the name as its `declarator` too; if the
            # field lookup failed, fall back to the first identifier-ish child.
            for c in node.named_children:
                if c.type in ("identifier", "function_declarator",
                              "pointer_declarator", "array_declarator",
                              "parenthesized_declarator"):
                    nxt = c
                    break
        node = nxt
    return None


class CExtractor(Extractor):
    language = "c"

    def extract(self, file_path: Path, source: bytes) -> tuple[list[Node], list[Edge]]:
        tree = _C_PARSER.parse(source)
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
                child, source, file_path, module_qual, module_idx, edges, add_node
            )

        self._collect_calls(root, source, nodes, edges, index_by_name)
        return nodes, edges

    def _handle_top_level(
        self, node, source, file_path, module_qual, module_idx, edges, add_node
    ) -> None:
        t = node.type
        if t == "preproc_include":
            self._handle_include(
                node, source, file_path, module_qual, module_idx, edges, add_node
            )
        elif t == "function_definition":
            decl = node.child_by_field_name("declarator")
            ident = _declarator_identifier(decl)
            if ident is None:
                return
            name = _node_text(source, ident)
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
        elif t in ("struct_specifier", "union_specifier"):
            self._handle_struct(
                node, source, file_path, module_qual, module_idx, edges, add_node
            )
        elif t == "enum_specifier":
            self._handle_enum(
                node, source, file_path, module_qual, module_idx, edges, add_node
            )
        elif t == "type_definition":
            self._handle_typedef(
                node, source, file_path, module_qual, module_idx, edges, add_node
            )
        elif t == "declaration":
            # A top-level declaration may wrap a struct/enum specifier (e.g.
            # `struct Point { ... } p;`) or be a function prototype / global.
            for c in node.named_children:
                if c.type in ("struct_specifier", "union_specifier", "enum_specifier"):
                    self._handle_top_level(
                        c, source, file_path, module_qual, module_idx, edges, add_node
                    )

    def _handle_include(
        self, node, source, file_path, module_qual, module_idx, edges, add_node
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
                qualified_name=f"{module_qual}.include:{raw}",
                file_path=str(file_path),
                start_line=_start_line(node),
                end_line=_end_line(node),
                signature=_first_line(source, node),
            )
        )
        edges.append(
            Edge(source_id=module_idx, target_id=idx, kind=EdgeKind.IMPORTS)
        )

    def _handle_struct(
        self, node, source, file_path, module_qual, module_idx, edges, add_node
    ) -> None:
        name_node = node.child_by_field_name("name")
        if name_node is None:
            return
        name = _node_text(source, name_node)
        qname = f"{module_qual}.{name}"
        struct_idx = add_node(
            Node(
                name=name,
                kind=NodeKind.STRUCT,
                qualified_name=qname,
                file_path=str(file_path),
                start_line=_start_line(node),
                end_line=_end_line(node),
                signature=_first_line(source, node),
            )
        )
        edges.append(
            Edge(source_id=module_idx, target_id=struct_idx, kind=EdgeKind.CONTAINS)
        )
        body = node.child_by_field_name("body")
        if body is None:
            return
        for fd in body.named_children:
            if fd.type != "field_declaration":
                continue
            fident = _declarator_identifier(fd.child_by_field_name("declarator"))
            if fident is None:
                for c in fd.named_children:
                    if c.type == "field_identifier":
                        fident = c
                        break
            if fident is None:
                continue
            fname = _node_text(source, fident)
            idx = add_node(
                Node(
                    name=fname,
                    kind=NodeKind.FIELD,
                    qualified_name=f"{qname}.{fname}",
                    file_path=str(file_path),
                    start_line=_start_line(fd),
                    end_line=_end_line(fd),
                    signature=_first_line(source, fd),
                )
            )
            edges.append(
                Edge(source_id=struct_idx, target_id=idx, kind=EdgeKind.CONTAINS)
            )

    def _handle_enum(
        self, node, source, file_path, module_qual, module_idx, edges, add_node
    ) -> None:
        name_node = node.child_by_field_name("name")
        if name_node is None:
            return
        name = _node_text(source, name_node)
        qname = f"{module_qual}.{name}"
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
            Edge(source_id=module_idx, target_id=enum_idx, kind=EdgeKind.CONTAINS)
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

    def _handle_typedef(
        self, node, source, file_path, module_qual, module_idx, edges, add_node
    ) -> None:
        decl = node.child_by_field_name("declarator")
        ident = _declarator_identifier(decl)
        if ident is None:
            for c in reversed(node.named_children):
                if c.type == "type_identifier":
                    ident = c
                    break
        if ident is None:
            return
        name = _node_text(source, ident)
        idx = add_node(
            Node(
                name=name,
                kind=NodeKind.TYPE_ALIAS,
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

    def _collect_calls(self, root, source, nodes, edges, index_by_name) -> None:
        stack: list[tuple[TSNode, int | None]] = [(root, None)]
        while stack:
            node, caller_idx = stack.pop()
            new_caller = caller_idx
            if node.type == "function_definition":
                ident = _declarator_identifier(node.child_by_field_name("declarator"))
                if ident is not None:
                    new_caller = index_by_name.get(_node_text(source, ident), caller_idx)
            elif node.type == "call_expression" and caller_idx is not None:
                fn = node.child_by_field_name("function")
                if fn is not None and fn.type == "identifier":
                    called = _node_text(source, fn)
                    tgt = index_by_name.get(called)
                    if (
                        tgt is not None
                        and tgt != caller_idx
                        and nodes[tgt].kind == NodeKind.FUNCTION
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
