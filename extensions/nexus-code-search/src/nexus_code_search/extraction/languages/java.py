"""Java AST extractor backed by tree-sitter.

Emits node kinds: `module` (file), `namespace` (package), `class`,
`interface`, `method`, `field`, `import`, `constant`. Emits edges:
`contains`, `calls`, `instantiates`, `extends`, `implements`, `overrides`,
`imports`.

Constructors are emitted as methods named after the class. A
`new Foo(...)` expression resolving to an in-file class emits `instantiates`;
a `method_invocation` resolving to an in-file method/constructor emits
`calls`. `extends` / `implements` edges are resolved against in-file
class/interface nodes, and `overrides` is derived from in-file `extends`
chains. In-file resolution only.

Parameter nodes are intentionally not emitted.
"""

from __future__ import annotations

import logging
from pathlib import Path

from tree_sitter import Language, Node as TSNode, Parser
import tree_sitter_java

from nexus_code_search.extraction.languages.base import Extractor
from nexus_code_search.types import Edge, EdgeKind, Node, NodeKind

logger = logging.getLogger("nexus-code-search")

_JAVA_LANGUAGE = Language(tree_sitter_java.language())
_JAVA_PARSER = Parser(_JAVA_LANGUAGE)


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


def _simple_type_name(text: str) -> str:
    """Strip generics / array / package qualifier to the bare type name."""
    return text.split("<")[0].split("[")[0].strip().split(".")[-1].strip()


class JavaExtractor(Extractor):
    language = "java"

    def extract(self, file_path: Path, source: bytes) -> tuple[list[Node], list[Edge]]:
        tree = _JAVA_PARSER.parse(source)
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
                child, source, file_path, module_qual, module_idx, edges,
                index_by_name, add_node,
            )

        self._collect_calls(
            root, source, module_qual, nodes, edges, index_by_qname, index_by_name
        )
        self._resolve_overrides(nodes, edges, index_by_qname)
        return nodes, edges

    def _handle_top_level(
        self, node, source, file_path, module_qual, module_idx, edges,
        index_by_name, add_node,
    ) -> None:
        t = node.type
        if t == "package_declaration":
            text = _node_text(source, node).replace("package", "", 1).strip().rstrip(";")
            name = text.split(".")[-1] if text else text
            idx = add_node(
                Node(
                    name=name,
                    kind=NodeKind.NAMESPACE,
                    qualified_name=f"{module_qual}.package:{text}",
                    file_path=str(file_path),
                    start_line=_start_line(node),
                    end_line=_end_line(node),
                    signature=_first_line(source, node),
                )
            )
            edges.append(
                Edge(source_id=module_idx, target_id=idx, kind=EdgeKind.CONTAINS)
            )
        elif t == "import_declaration":
            text = _node_text(source, node).replace("import", "", 1).replace(
                "static", "", 1
            ).strip().rstrip(";")
            name = text.split(".")[-1] if text else text
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
            edges.append(
                Edge(source_id=module_idx, target_id=idx, kind=EdgeKind.IMPORTS)
            )
        elif t == "class_declaration":
            self._handle_type(
                node, source, file_path, module_qual, module_idx, NodeKind.CLASS,
                edges, index_by_name, add_node,
            )
        elif t == "interface_declaration":
            self._handle_type(
                node, source, file_path, module_qual, module_idx, NodeKind.INTERFACE,
                edges, index_by_name, add_node,
            )

    def _handle_type(
        self, node, source, file_path, module_qual, module_idx, kind, edges,
        index_by_name, add_node,
    ) -> None:
        name_node = node.child_by_field_name("name")
        if name_node is None:
            return
        name = _node_text(source, name_node)
        qname = f"{module_qual}.{name}"
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
            Edge(source_id=module_idx, target_id=type_idx, kind=EdgeKind.CONTAINS)
        )

        # extends (superclass field) -> extends edge.
        superclass = node.child_by_field_name("superclass")
        if superclass is not None:
            for base in superclass.named_children:
                self._link_base(
                    base, source, type_idx, EdgeKind.EXTENDS, edges, index_by_name
                )
        # implements (interfaces field -> super_interfaces -> type_list).
        interfaces = node.child_by_field_name("interfaces")
        if interfaces is not None:
            for tl in interfaces.named_children:
                bases = tl.named_children if tl.type == "type_list" else (tl,)
                for base in bases:
                    self._link_base(
                        base, source, type_idx, EdgeKind.IMPLEMENTS, edges, index_by_name
                    )

        body = node.child_by_field_name("body")
        for member in body.named_children if body else ():
            if member.type in ("method_declaration", "constructor_declaration"):
                self._handle_method(
                    member, source, file_path, qname, type_idx, edges, add_node
                )
            elif member.type == "field_declaration":
                self._handle_field(
                    member, source, file_path, qname, type_idx, edges, add_node
                )

    def _link_base(
        self, base, source, type_idx, kind, edges, index_by_name
    ) -> None:
        base_name = _simple_type_name(_node_text(source, base))
        if not base_name:
            return
        target = index_by_name.get(base_name)
        if target is not None and target != type_idx:
            edges.append(Edge(source_id=type_idx, target_id=target, kind=kind))

    def _handle_method(
        self, node, source, file_path, class_qname, class_idx, edges, add_node
    ) -> None:
        name_node = node.child_by_field_name("name")
        if name_node is None:
            return
        name = _node_text(source, name_node)
        idx = add_node(
            Node(
                name=name,
                kind=NodeKind.METHOD,
                qualified_name=f"{class_qname}.{name}",
                file_path=str(file_path),
                start_line=_start_line(node),
                end_line=_end_line(node),
                signature=_first_line(source, node),
            )
        )
        edges.append(Edge(source_id=class_idx, target_id=idx, kind=EdgeKind.CONTAINS))

    def _handle_field(
        self, node, source, file_path, class_qname, class_idx, edges, add_node
    ) -> None:
        for declarator in node.named_children:
            if declarator.type != "variable_declarator":
                continue
            name_node = declarator.child_by_field_name("name")
            if name_node is None:
                continue
            name = _node_text(source, name_node)
            idx = add_node(
                Node(
                    name=name,
                    kind=NodeKind.FIELD,
                    qualified_name=f"{class_qname}.{name}",
                    file_path=str(file_path),
                    start_line=_start_line(node),
                    end_line=_end_line(node),
                    signature=_first_line(source, node),
                )
            )
            edges.append(
                Edge(source_id=class_idx, target_id=idx, kind=EdgeKind.CONTAINS)
            )

    def _collect_calls(
        self, root, source, module_qual, nodes, edges, index_by_qname, index_by_name
    ) -> None:
        stack: list[tuple[TSNode, str | None, str | None]] = [(root, None, None)]
        while stack:
            node, fn_q, cls_n = stack.pop()
            new_fn = fn_q
            new_cls = cls_n
            if node.type in ("class_declaration", "interface_declaration"):
                nn = node.child_by_field_name("name")
                new_cls = _node_text(source, nn) if nn else cls_n
            elif node.type in ("method_declaration", "constructor_declaration"):
                nn = node.child_by_field_name("name")
                if nn is not None:
                    prefix = f"{module_qual}.{cls_n}" if cls_n else module_qual
                    new_fn = f"{prefix}.{_node_text(source, nn)}"
            elif node.type == "method_invocation" and fn_q:
                nn = node.child_by_field_name("name")
                if nn is not None:
                    self._emit_edge(
                        node, _node_text(source, nn), module_qual, fn_q, nodes, edges,
                        index_by_qname, index_by_name, force_instantiates=False,
                    )
            elif node.type == "object_creation_expression" and fn_q:
                tn = node.child_by_field_name("type")
                if tn is not None:
                    self._emit_edge(
                        node, _simple_type_name(_node_text(source, tn)), module_qual,
                        fn_q, nodes, edges, index_by_qname, index_by_name,
                        force_instantiates=True,
                    )
            for c in reversed(node.named_children):
                stack.append((c, new_fn, new_cls))

    def _emit_edge(
        self, node, called, module_qual, fn_q, nodes, edges, index_by_qname,
        index_by_name, force_instantiates,
    ) -> None:
        caller_idx = index_by_qname.get(fn_q)
        if caller_idx is None or not called:
            return
        tgt = index_by_qname.get(f"{module_qual}.{called}") or index_by_name.get(
            called.split(".")[-1]
        )
        if tgt is None or tgt == caller_idx:
            return
        is_class = nodes[tgt].kind == NodeKind.CLASS
        kind = (
            EdgeKind.INSTANTIATES if force_instantiates or is_class else EdgeKind.CALLS
        )
        edges.append(
            Edge(
                source_id=caller_idx,
                target_id=tgt,
                kind=kind,
                call_site_line=_start_line(node),
            )
        )

    def _resolve_overrides(self, nodes, edges, index_by_qname) -> None:
        parent_of: dict[str, str] = {}
        for e in edges:
            if e.kind != EdgeKind.EXTENDS:
                continue
            child = nodes[e.source_id]
            parent = nodes[e.target_id]
            if child.kind == NodeKind.CLASS and parent.kind == NodeKind.CLASS:
                parent_of[child.qualified_name] = parent.qualified_name
        if not parent_of:
            return
        for idx, node in enumerate(nodes):
            if node.kind != NodeKind.METHOD:
                continue
            class_qname = node.qualified_name.rsplit(".", 1)[0]
            seen: set[str] = set()
            cur = parent_of.get(class_qname)
            while cur is not None and cur not in seen:
                seen.add(cur)
                parent_method_idx = index_by_qname.get(f"{cur}.{node.name}")
                if (
                    parent_method_idx is not None
                    and parent_method_idx != idx
                    and nodes[parent_method_idx].kind == NodeKind.METHOD
                ):
                    edges.append(
                        Edge(
                            source_id=idx,
                            target_id=parent_method_idx,
                            kind=EdgeKind.OVERRIDES,
                        )
                    )
                    break
                cur = parent_of.get(cur)
