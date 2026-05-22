"""Extra TypeScriptExtractor coverage (T025 / T028)."""

from __future__ import annotations

from pathlib import Path

from nexus_code_search.extraction.languages.typescript import TypeScriptExtractor
from nexus_code_search.types import EdgeKind, NodeKind


def test_ts_import_named_specifiers(tmp_path: Path) -> None:
    src = "import { foo, bar as baz } from './helpers';\n"
    nodes, edges = TypeScriptExtractor().extract(
        tmp_path / "a.ts", src.encode("utf-8")
    )
    import_names = {n.name for n in nodes if n.kind == NodeKind.IMPORT}
    # The named imports `foo` and `bar` are both captured.
    assert "foo" in import_names
    assert "bar" in import_names
    # IMPORTS edge from module to each import node.
    imports = [e for e in edges if e.kind == EdgeKind.IMPORTS]
    assert len(imports) >= 2


def test_ts_import_default_and_namespace(tmp_path: Path) -> None:
    src = "import * as utils from './u';\nimport defaultFn from './d';\n"
    nodes, _ = TypeScriptExtractor().extract(
        tmp_path / "a.ts", src.encode("utf-8")
    )
    import_names = {n.name for n in nodes if n.kind == NodeKind.IMPORT}
    assert {"utils", "defaultFn"} <= import_names


def test_ts_export_clause_emits_export_node(tmp_path: Path) -> None:
    src = "const helper = 1;\nexport { helper };\n"
    nodes, edges = TypeScriptExtractor().extract(
        tmp_path / "a.ts", src.encode("utf-8")
    )
    exports = [n for n in nodes if n.kind == NodeKind.EXPORT]
    assert any(e.name == "helper" for e in exports)
    export_edges = [e for e in edges if e.kind == EdgeKind.EXPORTS]
    assert export_edges


def test_ts_const_is_constant_kind(tmp_path: Path) -> None:
    src = "const MAX = 100;\nlet counter = 0;\n"
    nodes, _ = TypeScriptExtractor().extract(
        tmp_path / "a.ts", src.encode("utf-8")
    )
    constants = {n.name for n in nodes if n.kind == NodeKind.CONSTANT}
    variables = {n.name for n in nodes if n.kind == NodeKind.VARIABLE}
    assert "MAX" in constants
    assert "counter" in variables


def test_ts_class_property(tmp_path: Path) -> None:
    src = "class Box { public width: number = 0; height: number = 0; }\n"
    nodes, _ = TypeScriptExtractor().extract(
        tmp_path / "a.ts", src.encode("utf-8")
    )
    props = {n.name for n in nodes if n.kind == NodeKind.PROPERTY}
    assert "width" in props
    assert "height" in props


def test_ts_method_call_through_member_expression(tmp_path: Path) -> None:
    src = (
        "class Logger { log(msg: string) { return msg; } }\n"
        "function go(l: Logger) { return l.log('hi'); }\n"
    )
    nodes, edges = TypeScriptExtractor().extract(
        tmp_path / "a.ts", src.encode("utf-8")
    )
    go_idx = next(i for i, n in enumerate(nodes) if n.name == "go")
    log_idx = next(i for i, n in enumerate(nodes) if n.name == "log")
    calls = [
        e
        for e in edges
        if e.kind == EdgeKind.CALLS
        and e.source_id == go_idx
        and e.target_id == log_idx
    ]
    assert calls
