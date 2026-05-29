"""GoExtractor coverage (T030 / DF-002)."""

from __future__ import annotations

from pathlib import Path

from nexus_code_search.extraction.languages.go import GoExtractor
from nexus_code_search.types import EdgeKind, NodeKind

_SRC = b"""
package main

import "fmt"

type Greeter struct {
\tname string
}

type Speaker interface {
\tSpeak() string
}

func (g Greeter) Speak() string {
\treturn g.name
}

func NewGreeter(n string) Greeter {
\treturn Greeter{name: n}
}

func main() {
\tg := NewGreeter("hi")
\tfmt.Println(g.Speak())
}
"""


def _extract():
    return GoExtractor().extract(Path("app.go"), _SRC)


def test_go_emits_struct_interface_function_method() -> None:
    nodes, _ = _extract()
    by_kind = {}
    for n in nodes:
        by_kind.setdefault(n.kind, set()).add(n.name)
    assert "Greeter" in by_kind.get(NodeKind.STRUCT, set())
    assert "Speaker" in by_kind.get(NodeKind.INTERFACE, set())
    assert "NewGreeter" in by_kind.get(NodeKind.FUNCTION, set())
    assert "Speak" in by_kind.get(NodeKind.METHOD, set())


def test_go_method_qualified_by_receiver_type() -> None:
    nodes, _ = _extract()
    speak = next(n for n in nodes if n.name == "Speak")
    assert speak.qualified_name.endswith("Greeter.Speak")


def test_go_struct_field_emitted() -> None:
    nodes, _ = _extract()
    fields = {n.name for n in nodes if n.kind == NodeKind.FIELD}
    assert "name" in fields


def test_go_import_emitted() -> None:
    nodes, edges = _extract()
    imports = {n.name for n in nodes if n.kind == NodeKind.IMPORT}
    assert "fmt" in imports
    assert any(e.kind == EdgeKind.IMPORTS for e in edges)


def test_go_composite_literal_emits_instantiates() -> None:
    nodes, edges = _extract()
    new_idx = next(i for i, n in enumerate(nodes) if n.name == "NewGreeter")
    greeter_idx = next(
        i for i, n in enumerate(nodes)
        if n.name == "Greeter" and n.kind == NodeKind.STRUCT
    )
    inst = [
        e
        for e in edges
        if e.kind == EdgeKind.INSTANTIATES
        and e.source_id == new_idx
        and e.target_id == greeter_idx
    ]
    assert inst


def test_go_in_file_calls() -> None:
    nodes, edges = _extract()
    main_idx = next(i for i, n in enumerate(nodes) if n.name == "main")
    called = {
        nodes[e.target_id].name
        for e in edges
        if e.kind == EdgeKind.CALLS and e.source_id == main_idx
    }
    assert {"NewGreeter", "Speak"} <= called
