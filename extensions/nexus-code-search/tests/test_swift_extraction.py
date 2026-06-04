"""SwiftExtractor coverage (v3.0.0 / DF-v24-7)."""

from __future__ import annotations

from pathlib import Path

from nexus_code_search.extraction.languages.swift import SwiftExtractor
from nexus_code_search.types import EdgeKind, NodeKind

_SRC = b"""
import Foundation

protocol Greeter {
    func describe() -> String
}

class Base {
}

class Animal: Base {
    let name: String

    init(name: String) {
        self.name = name
    }

    func greet() -> String {
        return hello(name)
    }
}

struct Point {
    var x: Int
}

enum Color {
    case red
}

func hello(_ text: String) -> String {
    return text
}
"""


def _extract():
    return SwiftExtractor().extract(Path("app.swift"), _SRC)


def test_swift_emits_protocol_class_struct_enum() -> None:
    nodes, _ = _extract()
    by_kind: dict[NodeKind, set[str]] = {}
    for n in nodes:
        by_kind.setdefault(n.kind, set()).add(n.name)
    assert "Greeter" in by_kind.get(NodeKind.PROTOCOL, set())
    assert {"Base", "Animal"} <= by_kind.get(NodeKind.CLASS, set())
    assert "Point" in by_kind.get(NodeKind.STRUCT, set())
    assert "Color" in by_kind.get(NodeKind.ENUM, set())


def test_swift_emits_method_function_and_init() -> None:
    nodes, _ = _extract()
    by_kind: dict[NodeKind, set[str]] = {}
    for n in nodes:
        by_kind.setdefault(n.kind, set()).add(n.name)
    # `greet` and `init` are methods (inside a type); `hello` is a top-level
    # function; `describe` is a protocol requirement (also a method).
    assert {"greet", "init", "describe"} <= by_kind.get(NodeKind.METHOD, set())
    assert "hello" in by_kind.get(NodeKind.FUNCTION, set())
    assert "red" in by_kind.get(NodeKind.ENUM_MEMBER, set())


def test_swift_superclass_emits_extends() -> None:
    nodes, edges = _extract()
    animal_idx = next(
        i for i, n in enumerate(nodes)
        if n.name == "Animal" and n.kind == NodeKind.CLASS
    )
    base_idx = next(
        i for i, n in enumerate(nodes)
        if n.name == "Base" and n.kind == NodeKind.CLASS
    )
    assert any(
        e.kind == EdgeKind.EXTENDS
        and e.source_id == animal_idx
        and e.target_id == base_idx
        for e in edges
    )


def test_swift_import_emits_import() -> None:
    nodes, edges = _extract()
    imports = {n.name for n in nodes if n.kind == NodeKind.IMPORT}
    assert "Foundation" in imports
    assert any(e.kind == EdgeKind.IMPORTS for e in edges)


def test_swift_in_file_call() -> None:
    nodes, edges = _extract()
    greet_idx = next(
        i for i, n in enumerate(nodes)
        if n.name == "greet" and n.kind == NodeKind.METHOD
    )
    called = {
        nodes[e.target_id].name
        for e in edges
        if e.kind == EdgeKind.CALLS and e.source_id == greet_idx
    }
    assert "hello" in called


def test_swift_submodule_import_uses_top_module_name() -> None:
    # `import os.log` -> the top module `os` is the import node name.
    src = b"import os.log\n"
    nodes, _ = SwiftExtractor().extract(Path("log.swift"), src)
    imports = {n.name for n in nodes if n.kind == NodeKind.IMPORT}
    assert "os" in imports


def test_swift_protocol_conformance_emits_implements() -> None:
    # A class conforming to an in-file protocol emits an `implements` edge.
    src = b"""
protocol Drawable {
    func draw()
}

class Shape: Drawable {
    func draw() {
    }
}
"""
    nodes, edges = SwiftExtractor().extract(Path("shape.swift"), src)
    shape_idx = next(
        i for i, n in enumerate(nodes)
        if n.name == "Shape" and n.kind == NodeKind.CLASS
    )
    drawable_idx = next(
        i for i, n in enumerate(nodes)
        if n.name == "Drawable" and n.kind == NodeKind.PROTOCOL
    )
    assert any(
        e.kind == EdgeKind.IMPLEMENTS
        and e.source_id == shape_idx
        and e.target_id == drawable_idx
        for e in edges
    )
