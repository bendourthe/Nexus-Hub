"""Python AST extractor backed by tree-sitter.

Emits the following node kinds: `function`, `method`, `class`, `parameter`,
`import`, `variable`, `constant`. Emits edges: `contains`, `calls`,
`instantiates`, `overrides`, `extends`, `imports`, `decorates`.

Edge resolution scope: only in-file edges are emitted. A `calls` edge is
produced when the call target name (or its dotted suffix) matches one of the
function / method nodes also extracted from the same file. When the resolved
target is a `class`, the edge is emitted as `instantiates` rather than `calls`
(a constructor call). An `overrides` edge is emitted when a method's enclosing
class extends (in-file) a parent class that defines a same-named method.
Cross-file resolution is the orchestrator's responsibility (it joins on
qualified_name after every file has been parsed).

By extractor convention, `source_id` and `target_id` on every emitted Edge
hold the LOCAL index into the emitted nodes list (not a database id). The
orchestrator rewrites those indices to real ids when nodes are flushed.
"""

from __future__ import annotations

import logging
from pathlib import Path

from tree_sitter import Language, Node as TSNode, Parser
import tree_sitter_python

from nexus_code_search.extraction.languages.base import Extractor
from nexus_code_search.types import Edge, EdgeKind, Node, NodeKind

logger = logging.getLogger("nexus-code-search")

_PY_LANGUAGE = Language(tree_sitter_python.language())
_PY_PARSER = Parser(_PY_LANGUAGE)


def _decode_range(source: bytes, start: int, end: int) -> str:
    try:
        return source[start:end].decode("utf-8", errors="replace")
    except Exception:  # noqa: BLE001
        return ""


def _node_text(source: bytes, node: TSNode) -> str:
    return _decode_range(source, node.start_byte, node.end_byte)


def _start_line(node: TSNode) -> int:
    return node.start_point[0] + 1


def _end_line(node: TSNode) -> int:
    return node.end_point[0] + 1


def _docstring_for(source: bytes, body: TSNode | None) -> str:
    """Return the docstring for a function / class body, or ''."""
    if body is None:
        return ""
    for child in body.named_children:
        if child.type == "expression_statement":
            inner = child.named_children[0] if child.named_children else None
            if inner is not None and inner.type == "string":
                text = _node_text(source, inner).strip()
                # Strip simple quote variants.
                for prefix in ('"""', "'''", '"', "'"):
                    if (
                        text.startswith(prefix)
                        and text.endswith(prefix)
                        and len(text) >= 2 * len(prefix)
                    ):
                        return text[len(prefix) : -len(prefix)].strip()
                return text
        break
    return ""


def _signature_for(source: bytes, fn: TSNode) -> str:
    """Return the first-line signature of a function / method definition."""
    raw = _node_text(source, fn).splitlines()
    return raw[0].strip() if raw else ""


def _module_name(file_path: Path) -> str:
    # Best-effort qualifier: use the file stem. The orchestrator owns the
    # repo-relative qualifier; per-file qualification is enough for in-file
    # edge resolution.
    return file_path.stem


class PythonExtractor(Extractor):
    language = "python"

    def extract(self, file_path: Path, source: bytes) -> tuple[list[Node], list[Edge]]:
        tree = _PY_PARSER.parse(source)
        root = tree.root_node
        module_qual = _module_name(file_path)

        nodes: list[Node] = []
        edges: list[Edge] = []
        # Map qualified_name -> local index in `nodes` for in-file edge resolution.
        index_by_qname: dict[str, int] = {}
        # Map simple symbol name -> local index (used as a fallback when a call
        # target lacks a dotted prefix that matches a class qualifier).
        index_by_name: dict[str, int] = {}

        def add_node(node: Node) -> int:
            local_id = len(nodes)
            nodes.append(node)
            index_by_qname[node.qualified_name] = local_id
            index_by_name.setdefault(node.name, local_id)
            return local_id

        # Add module node first so file-level imports can attach via `contains`.
        module_node = Node(
            name=module_qual,
            kind=NodeKind.MODULE,
            qualified_name=module_qual,
            file_path=str(file_path),
            start_line=1,
            end_line=max(1, _end_line(root)),
            signature="",
            docstring=_docstring_for(source, root),
        )
        module_idx = add_node(module_node)

        # Walk top-level statements.
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

        # Resolve call edges over already-known symbols. We do a second pass
        # so calls forward-referencing later-defined functions still resolve.
        self._collect_calls(
            root,
            source,
            file_path,
            module_qual,
            nodes,
            edges,
            index_by_qname,
            index_by_name,
        )

        # Resolve method-override edges against in-file parent classes.
        self._resolve_overrides(nodes, edges, index_by_qname)

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
        if node.type in ("import_statement", "import_from_statement"):
            self._handle_import(
                node, source, file_path, module_qual, module_idx, edges, add_node
            )
        elif node.type == "function_definition":
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
        elif node.type == "decorated_definition":
            inner = node.child_by_field_name("definition")
            if inner is not None:
                self._handle_top_level(
                    inner,
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
            self._handle_decorators(node, source, edges, index_by_qname, index_by_name)
        elif node.type == "class_definition":
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
            )
        elif node.type == "expression_statement":
            inner = node.named_children[0] if node.named_children else None
            if inner is not None and inner.type == "assignment":
                self._handle_assignment(
                    inner,
                    source,
                    file_path,
                    module_qual,
                    module_idx,
                    parent_class=None,
                    nodes=nodes,
                    edges=edges,
                    add_node=add_node,
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
        # For both `import foo` and `from bar import baz`, emit one import node
        # per dotted-name target.
        targets: list[str] = []
        if node.type == "import_statement":
            for child in node.named_children:
                if child.type in ("dotted_name", "aliased_import"):
                    targets.append(_node_text(source, child).split(" as ")[0].strip())
        else:  # import_from_statement
            module_name_node = node.child_by_field_name("module_name")
            module_name = (
                _node_text(source, module_name_node) if module_name_node else ""
            )
            for child in node.named_children:
                if child is module_name_node:
                    continue
                if child.type in ("dotted_name", "aliased_import"):
                    name = _node_text(source, child).split(" as ")[0].strip()
                    full = f"{module_name}.{name}" if module_name else name
                    targets.append(full)
        for tgt in targets:
            qname = f"{module_qual}.import:{tgt}"
            import_idx = add_node(
                Node(
                    name=tgt,
                    kind=NodeKind.IMPORT,
                    qualified_name=qname,
                    file_path=str(file_path),
                    start_line=_start_line(node),
                    end_line=_end_line(node),
                    signature=_node_text(source, node).splitlines()[0]
                    if _node_text(source, node)
                    else "",
                )
            )
            edges.append(
                Edge(source_id=module_idx, target_id=import_idx, kind=EdgeKind.IMPORTS)
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
        body_node = node.child_by_field_name("body")
        fn_idx = add_node(
            Node(
                name=name,
                kind=kind,
                qualified_name=qname,
                file_path=str(file_path),
                start_line=_start_line(node),
                end_line=_end_line(node),
                signature=_signature_for(source, node),
                docstring=_docstring_for(source, body_node),
            )
        )
        edges.append(
            Edge(source_id=parent_idx, target_id=fn_idx, kind=EdgeKind.CONTAINS)
        )

        # Parameters.
        params_node = node.child_by_field_name("parameters")
        if params_node is not None:
            for child in params_node.named_children:
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
        if node.type in ("identifier",):
            return _node_text(source, node)
        # typed_parameter / default_parameter / typed_default_parameter / list_splat / dict_splat
        name_child = node.child_by_field_name("name")
        if name_child is not None:
            return _node_text(source, name_child)
        # Fallback: first identifier descendant.
        for child in node.named_children:
            if child.type == "identifier":
                return _node_text(source, child)
        return ""

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
    ) -> None:
        name_node = node.child_by_field_name("name")
        if name_node is None:
            return
        name = _node_text(source, name_node)
        qname = f"{module_qual}.{name}"
        body_node = node.child_by_field_name("body")
        class_idx = add_node(
            Node(
                name=name,
                kind=NodeKind.CLASS,
                qualified_name=qname,
                file_path=str(file_path),
                start_line=_start_line(node),
                end_line=_end_line(node),
                signature=_signature_for(source, node),
                docstring=_docstring_for(source, body_node),
            )
        )
        edges.append(
            Edge(source_id=module_idx, target_id=class_idx, kind=EdgeKind.CONTAINS)
        )

        # Base classes -> extends edges (best-effort name match).
        bases_node = node.child_by_field_name("superclasses")
        if bases_node is not None:
            for base in bases_node.named_children:
                base_name = _node_text(source, base).split("(")[0].strip()
                if not base_name:
                    continue
                # Resolve via index_by_name; if absent, skip (cross-file
                # extension is left for the orchestrator's post-pass).
                target = index_by_name.get(base_name.split(".")[-1])
                if target is not None:
                    edges.append(
                        Edge(
                            source_id=class_idx, target_id=target, kind=EdgeKind.EXTENDS
                        )
                    )

        # Class body: methods + class-level assignments.
        if body_node is not None:
            for child in body_node.named_children:
                if child.type == "function_definition":
                    self._handle_function(
                        child,
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
                elif child.type == "decorated_definition":
                    inner = child.child_by_field_name("definition")
                    if inner is not None and inner.type == "function_definition":
                        self._handle_function(
                            inner,
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
                elif child.type == "expression_statement":
                    expr_inner = (
                        child.named_children[0] if child.named_children else None
                    )
                    if expr_inner is not None and expr_inner.type == "assignment":
                        self._handle_assignment(
                            expr_inner,
                            source,
                            file_path,
                            module_qual,
                            class_idx,
                            parent_class=name,
                            nodes=nodes,
                            edges=edges,
                            add_node=add_node,
                        )

    def _handle_assignment(
        self,
        node: TSNode,
        source: bytes,
        file_path: Path,
        module_qual: str,
        parent_idx: int,
        parent_class: str | None,
        nodes: list[Node],
        edges: list[Edge],
        add_node,
    ) -> None:
        left = node.child_by_field_name("left")
        if left is None or left.type != "identifier":
            return
        name = _node_text(source, left)
        kind = (
            NodeKind.CONSTANT
            if name.isupper()
            else (NodeKind.FIELD if parent_class else NodeKind.VARIABLE)
        )
        qprefix = f"{module_qual}.{parent_class}" if parent_class else module_qual
        qname = f"{qprefix}.{name}"
        idx = add_node(
            Node(
                name=name,
                kind=kind,
                qualified_name=qname,
                file_path=str(file_path),
                start_line=_start_line(node),
                end_line=_end_line(node),
                signature=_node_text(source, node).splitlines()[0],
            )
        )
        edges.append(Edge(source_id=parent_idx, target_id=idx, kind=EdgeKind.CONTAINS))

    def _handle_decorators(
        self,
        node: TSNode,
        source: bytes,
        edges: list[Edge],
        index_by_qname: dict[str, int],
        index_by_name: dict[str, int],
    ) -> None:
        # The decorated function/class is the last child; decorators precede it.
        definition = node.child_by_field_name("definition")
        if definition is None:
            return
        def_name_node = definition.child_by_field_name("name")
        if def_name_node is None:
            return
        def_name = _node_text(source, def_name_node)
        def_idx = index_by_name.get(def_name)
        if def_idx is None:
            return
        for child in node.named_children:
            if child.type != "decorator":
                continue
            target_name = (
                _node_text(source, child)
                .lstrip("@")
                .split("(")[0]
                .strip()
                .split(".")[-1]
            )
            if not target_name:
                continue
            tgt = index_by_name.get(target_name)
            if tgt is not None and tgt != def_idx:
                edges.append(
                    Edge(
                        source_id=tgt,
                        target_id=def_idx,
                        kind=EdgeKind.DECORATES,
                        call_site_line=_start_line(child),
                    )
                )

    def _collect_calls(
        self,
        root: TSNode,
        source: bytes,
        file_path: Path,
        module_qual: str,
        nodes: list[Node],
        edges: list[Edge],
        index_by_qname: dict[str, int],
        index_by_name: dict[str, int],
    ) -> None:
        """Walk `root` to find `call` expressions and emit in-file calls edges."""
        # Walk; whenever we enter a function/method body, push its qname as the
        # active caller; whenever we exit, pop. `_walk_with_function_parent`
        # threads the enclosing function's qname through to each descendant.
        for node, _ in self._walk_with_function_parent(root, module_qual, source):
            if node[0].type != "call":
                continue
            ts_node, caller_qname = node
            if caller_qname is None:
                continue
            caller_idx = index_by_qname.get(caller_qname)
            if caller_idx is None:
                continue
            fn_field = ts_node.child_by_field_name("function")
            if fn_field is None:
                continue
            called_name = self._resolve_called_name(fn_field, source)
            if not called_name:
                continue
            # Try a fully-qualified lookup first (module.Class.method or
            # module.func), then fall back to simple name.
            target_idx = index_by_qname.get(
                f"{module_qual}.{called_name}"
            ) or index_by_name.get(called_name.split(".")[-1])
            if target_idx is None or target_idx == caller_idx:
                continue
            # A call whose target is a class is a constructor invocation: emit
            # `instantiates` rather than `calls` so the graph distinguishes
            # "uses this function" from "creates this type".
            edge_kind = (
                EdgeKind.INSTANTIATES
                if nodes[target_idx].kind == NodeKind.CLASS
                else EdgeKind.CALLS
            )
            edges.append(
                Edge(
                    source_id=caller_idx,
                    target_id=target_idx,
                    kind=edge_kind,
                    call_site_line=_start_line(ts_node),
                )
            )

    def _walk_with_function_parent(
        self,
        root: TSNode,
        module_qual: str,
        source: bytes,
    ):
        """Yield (node, enclosing_function_qname) for every descendant of root."""
        stack: list[tuple[TSNode, str | None, str | None]] = [(root, None, None)]
        # tuple: (node, enclosing_function_qname, enclosing_class_name)
        while stack:
            node, fn_q, cls_n = stack.pop()
            if node.type == "class_definition":
                cls_name_node = node.child_by_field_name("name")
                cls_n_next = (
                    _node_text(source, cls_name_node) if cls_name_node else cls_n
                )
                for c in reversed(node.named_children):
                    stack.append((c, fn_q, cls_n_next))
                continue
            if node.type == "function_definition":
                name_node = node.child_by_field_name("name")
                if name_node is not None:
                    fname = _node_text(source, name_node)
                    qprefix = f"{module_qual}.{cls_n}" if cls_n else module_qual
                    new_fn = f"{qprefix}.{fname}"
                else:
                    new_fn = fn_q
                yield (node, fn_q), fn_q  # yield call info; caller still parent
                for c in reversed(node.named_children):
                    stack.append((c, new_fn, cls_n))
                continue
            # Yield the (node, current_function) pair for traversal logic.
            yield (node, fn_q), fn_q
            for c in reversed(node.named_children):
                stack.append((c, fn_q, cls_n))

    def _resolve_called_name(self, fn_field: TSNode, source: bytes) -> str:
        """Return the dotted name of a call target, or '' if unresolvable."""
        if fn_field.type == "identifier":
            return _node_text(source, fn_field)
        if fn_field.type == "attribute":
            obj = fn_field.child_by_field_name("object")
            attr = fn_field.child_by_field_name("attribute")
            obj_text = _node_text(source, obj) if obj else ""
            attr_text = _node_text(source, attr) if attr else ""
            if obj_text and attr_text:
                return f"{obj_text}.{attr_text}"
            return attr_text
        # Skip more complex call targets (subscripts, lambdas, etc.).
        return ""

    def _resolve_overrides(
        self,
        nodes: list[Node],
        edges: list[Edge],
        index_by_qname: dict[str, int],
    ) -> None:
        """Emit `overrides` edges for methods that shadow a parent's method.

        Uses the in-file `extends` edges already emitted by `_handle_class`:
        a method `Child.foo` overrides `Parent.foo` when `Child` extends
        `Parent` (transitively, within this file) and `Parent` defines a
        method named `foo`. Resolution is in-file only; cross-file inheritance
        is the orchestrator's responsibility.
        """
        # child class qualified_name -> parent class qualified_name (in-file).
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
