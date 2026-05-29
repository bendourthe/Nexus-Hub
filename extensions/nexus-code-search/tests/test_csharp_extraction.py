"""CSharpExtractor coverage (T030 / DF-002)."""

from __future__ import annotations

from pathlib import Path

from nexus_code_search.extraction.languages.csharp import CSharpExtractor
from nexus_code_search.types import EdgeKind, NodeKind

_SRC = b"""
namespace Zoo;

using System;

class Animal
{
    public virtual string Describe()
    {
        return "animal";
    }
}

interface IMover
{
    void Move();
}

class Lion : Animal, IMover
{
    private int age;

    public override string Describe()
    {
        return "lion";
    }

    public void Move()
    {
    }

    public Animal Spawn()
    {
        var cub = new Lion();
        cub.Describe();
        return cub;
    }
}
"""


def _extract():
    return CSharpExtractor().extract(Path("Zoo.cs"), _SRC)


def test_csharp_emits_class_interface_method_field() -> None:
    nodes, _ = _extract()
    by_kind = {}
    for n in nodes:
        by_kind.setdefault(n.kind, set()).add(n.name)
    assert "Animal" in by_kind.get(NodeKind.CLASS, set())
    assert "IMover" in by_kind.get(NodeKind.INTERFACE, set())
    assert "Spawn" in by_kind.get(NodeKind.METHOD, set())
    assert "age" in by_kind.get(NodeKind.FIELD, set())


def test_csharp_namespace_and_import() -> None:
    nodes, _ = _extract()
    namespaces = {n.name for n in nodes if n.kind == NodeKind.NAMESPACE}
    imports = {n.name for n in nodes if n.kind == NodeKind.IMPORT}
    assert "Zoo" in namespaces
    assert "System" in imports


def test_csharp_base_list_resolves_extends_and_implements() -> None:
    nodes, edges = _extract()
    lion = next(
        i for i, n in enumerate(nodes)
        if n.name == "Lion" and n.kind == NodeKind.CLASS
    )
    animal = next(
        i for i, n in enumerate(nodes)
        if n.name == "Animal" and n.kind == NodeKind.CLASS
    )
    imover = next(
        i for i, n in enumerate(nodes)
        if n.name == "IMover" and n.kind == NodeKind.INTERFACE
    )
    # Base class -> extends; interface -> implements (refined from the base list).
    assert any(
        e.kind == EdgeKind.EXTENDS and e.source_id == lion and e.target_id == animal
        for e in edges
    )
    assert any(
        e.kind == EdgeKind.IMPLEMENTS and e.source_id == lion and e.target_id == imover
        for e in edges
    )


def test_csharp_override_edge() -> None:
    nodes, edges = _extract()
    lion_describe = next(
        i for i, n in enumerate(nodes) if n.qualified_name.endswith("Lion.Describe")
    )
    animal_describe = next(
        i for i, n in enumerate(nodes) if n.qualified_name.endswith("Animal.Describe")
    )
    assert any(
        e.kind == EdgeKind.OVERRIDES
        and e.source_id == lion_describe
        and e.target_id == animal_describe
        for e in edges
    )


def test_csharp_object_creation_emits_instantiates() -> None:
    nodes, edges = _extract()
    spawn_idx = next(i for i, n in enumerate(nodes) if n.name == "Spawn")
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


def test_csharp_invocation_emits_calls() -> None:
    nodes, edges = _extract()
    spawn_idx = next(i for i, n in enumerate(nodes) if n.name == "Spawn")
    called = {
        nodes[e.target_id].name
        for e in edges
        if e.kind == EdgeKind.CALLS and e.source_id == spawn_idx
    }
    assert "Describe" in called
