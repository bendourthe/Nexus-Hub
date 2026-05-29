"""JavaExtractor coverage (T030 / DF-002)."""

from __future__ import annotations

from pathlib import Path

from nexus_code_search.extraction.languages.java import JavaExtractor
from nexus_code_search.types import EdgeKind, NodeKind

_SRC = b"""
package com.zoo;

import java.util.List;

class Animal {
    String describe() {
        return "animal";
    }
}

interface Mover {
    void move();
}

class Lion extends Animal implements Mover {
    private int age;

    String describe() {
        return "lion";
    }

    public void move() {
    }

    Animal spawn() {
        Lion cub = new Lion();
        cub.describe();
        return cub;
    }
}
"""


def _extract():
    return JavaExtractor().extract(Path("Zoo.java"), _SRC)


def test_java_emits_class_interface_method_field() -> None:
    nodes, _ = _extract()
    by_kind = {}
    for n in nodes:
        by_kind.setdefault(n.kind, set()).add(n.name)
    assert "Animal" in by_kind.get(NodeKind.CLASS, set())
    assert "Mover" in by_kind.get(NodeKind.INTERFACE, set())
    assert "spawn" in by_kind.get(NodeKind.METHOD, set())
    assert "age" in by_kind.get(NodeKind.FIELD, set())


def test_java_extends_and_implements_edges() -> None:
    nodes, edges = _extract()
    lion = next(
        i for i, n in enumerate(nodes)
        if n.name == "Lion" and n.kind == NodeKind.CLASS
    )
    animal = next(
        i for i, n in enumerate(nodes)
        if n.name == "Animal" and n.kind == NodeKind.CLASS
    )
    mover = next(
        i for i, n in enumerate(nodes)
        if n.name == "Mover" and n.kind == NodeKind.INTERFACE
    )
    assert any(
        e.kind == EdgeKind.EXTENDS and e.source_id == lion and e.target_id == animal
        for e in edges
    )
    assert any(
        e.kind == EdgeKind.IMPLEMENTS and e.source_id == lion and e.target_id == mover
        for e in edges
    )


def test_java_override_edge() -> None:
    nodes, edges = _extract()
    lion_describe = next(
        i for i, n in enumerate(nodes) if n.qualified_name.endswith("Lion.describe")
    )
    animal_describe = next(
        i for i, n in enumerate(nodes) if n.qualified_name.endswith("Animal.describe")
    )
    assert any(
        e.kind == EdgeKind.OVERRIDES
        and e.source_id == lion_describe
        and e.target_id == animal_describe
        for e in edges
    )


def test_java_new_expression_emits_instantiates() -> None:
    nodes, edges = _extract()
    spawn_idx = next(i for i, n in enumerate(nodes) if n.name == "spawn")
    lion_idx = next(
        i for i, n in enumerate(nodes)
        if n.name == "Lion" and n.kind == NodeKind.CLASS
    )
    assert any(
        e.kind == EdgeKind.INSTANTIATES
        and e.source_id == spawn_idx
        and e.target_id == lion_idx
        for e in edges
    )


def test_java_method_invocation_emits_calls() -> None:
    nodes, edges = _extract()
    spawn_idx = next(i for i, n in enumerate(nodes) if n.name == "spawn")
    called = {
        nodes[e.target_id].name
        for e in edges
        if e.kind == EdgeKind.CALLS and e.source_id == spawn_idx
    }
    assert "describe" in called


def test_java_import_emitted() -> None:
    nodes, _ = _extract()
    imports = {n.name for n in nodes if n.kind == NodeKind.IMPORT}
    assert "List" in imports
