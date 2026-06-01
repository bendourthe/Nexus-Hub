"""CExtractor coverage (v2.4.0 / DF-v23-4)."""

from __future__ import annotations

from pathlib import Path

from nexus_code_search.extraction.languages.c import CExtractor
from nexus_code_search.types import EdgeKind, NodeKind

_SRC = b"""
#include <stdio.h>

struct Point {
    int x;
    int y;
};

enum Color { RED, GREEN };

int add(int a, int b) {
    return a + b;
}

int compute(int x) {
    return add(x, 1);
}

int main(void) {
    return compute(2);
}
"""


def _extract():
    return CExtractor().extract(Path("app.c"), _SRC)


def test_c_emits_function_struct_enum() -> None:
    nodes, _ = _extract()
    by_kind: dict[NodeKind, set[str]] = {}
    for n in nodes:
        by_kind.setdefault(n.kind, set()).add(n.name)
    assert {"add", "compute", "main"} <= by_kind.get(NodeKind.FUNCTION, set())
    assert "Point" in by_kind.get(NodeKind.STRUCT, set())
    assert "Color" in by_kind.get(NodeKind.ENUM, set())


def test_c_struct_fields_and_enum_members() -> None:
    nodes, _ = _extract()
    fields = {n.name for n in nodes if n.kind == NodeKind.FIELD}
    members = {n.name for n in nodes if n.kind == NodeKind.ENUM_MEMBER}
    assert {"x", "y"} <= fields
    assert {"RED", "GREEN"} <= members


def test_c_include_emits_import() -> None:
    nodes, edges = _extract()
    imports = {n.name for n in nodes if n.kind == NodeKind.IMPORT}
    assert "stdio.h" in imports
    assert any(e.kind == EdgeKind.IMPORTS for e in edges)


def test_c_in_file_calls() -> None:
    nodes, edges = _extract()
    compute_idx = next(
        i for i, n in enumerate(nodes)
        if n.name == "compute" and n.kind == NodeKind.FUNCTION
    )
    called = {
        nodes[e.target_id].name
        for e in edges
        if e.kind == EdgeKind.CALLS and e.source_id == compute_idx
    }
    assert "add" in called
