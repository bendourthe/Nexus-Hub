"""RustExtractor coverage (T030 / DF-002)."""

from __future__ import annotations

from pathlib import Path

from nexus_code_search.extraction.languages.rust import RustExtractor
from nexus_code_search.types import EdgeKind, NodeKind

_SRC = b"""
use std::fmt;

trait Shape {
    fn area(&self) -> f64;
}

struct Circle {
    radius: f64,
}

impl Shape for Circle {
    fn area(&self) -> f64 {
        self.radius
    }
}

impl Circle {
    fn make(r: f64) -> Circle {
        Circle { radius: r }
    }
}

fn run() {
    let c = Circle::make(1.0);
    c.area();
}
"""


def _extract():
    return RustExtractor().extract(Path("lib.rs"), _SRC)


def test_rust_emits_struct_trait_function() -> None:
    nodes, _ = _extract()
    by_kind = {}
    for n in nodes:
        by_kind.setdefault(n.kind, set()).add(n.name)
    assert "Circle" in by_kind.get(NodeKind.STRUCT, set())
    assert "Shape" in by_kind.get(NodeKind.TRAIT, set())
    assert "run" in by_kind.get(NodeKind.FUNCTION, set())


def test_rust_impl_methods_keyed_by_type() -> None:
    nodes, _ = _extract()
    make = next(n for n in nodes if n.name == "make")
    assert make.kind == NodeKind.METHOD
    assert make.qualified_name.endswith("Circle.make")


def test_rust_impl_trait_emits_implements_edge() -> None:
    nodes, edges = _extract()
    circle_idx = next(
        i for i, n in enumerate(nodes)
        if n.name == "Circle" and n.kind == NodeKind.STRUCT
    )
    shape_idx = next(
        i for i, n in enumerate(nodes)
        if n.name == "Shape" and n.kind == NodeKind.TRAIT
    )
    impl = [
        e
        for e in edges
        if e.kind == EdgeKind.IMPLEMENTS
        and e.source_id == circle_idx
        and e.target_id == shape_idx
    ]
    assert impl


def test_rust_struct_literal_emits_instantiates() -> None:
    nodes, edges = _extract()
    make_idx = next(i for i, n in enumerate(nodes) if n.name == "make")
    circle_idx = next(
        i for i, n in enumerate(nodes)
        if n.name == "Circle" and n.kind == NodeKind.STRUCT
    )
    inst = [
        e
        for e in edges
        if e.kind == EdgeKind.INSTANTIATES
        and e.source_id == make_idx
        and e.target_id == circle_idx
    ]
    assert inst


def test_rust_in_file_calls() -> None:
    nodes, edges = _extract()
    run_idx = next(i for i, n in enumerate(nodes) if n.name == "run")
    called = {
        nodes[e.target_id].name
        for e in edges
        if e.kind == EdgeKind.CALLS and e.source_id == run_idx
    }
    assert {"make", "area"} <= called


def test_rust_use_declaration_emits_import() -> None:
    nodes, edges = _extract()
    imports = {n.name for n in nodes if n.kind == NodeKind.IMPORT}
    assert "fmt" in imports
    assert any(e.kind == EdgeKind.IMPORTS for e in edges)
