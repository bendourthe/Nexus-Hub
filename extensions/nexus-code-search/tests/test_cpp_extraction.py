"""CppExtractor coverage (v2.4.0 / DF-v23-4)."""

from __future__ import annotations

from pathlib import Path

from nexus_code_search.extraction.languages.cpp import CppExtractor
from nexus_code_search.types import EdgeKind, NodeKind

_SRC = b"""
#include <string>

namespace zoo {

class Base {
public:
    virtual void run() {}
};

class Greeter : public Base {
public:
    Greeter(std::string title) : title_(title) {}

    std::string greet() {
        return hello(title_);
    }

    std::string banner;

private:
    std::string title_;
};

std::string hello(std::string n) {
    return n;
}

}  // namespace zoo
"""


def _extract():
    return CppExtractor().extract(Path("app.cpp"), _SRC)


def test_cpp_emits_namespace_class_method_function() -> None:
    nodes, _ = _extract()
    by_kind: dict[NodeKind, set[str]] = {}
    for n in nodes:
        by_kind.setdefault(n.kind, set()).add(n.name)
    assert "zoo" in by_kind.get(NodeKind.NAMESPACE, set())
    assert {"Base", "Greeter"} <= by_kind.get(NodeKind.CLASS, set())
    assert "greet" in by_kind.get(NodeKind.METHOD, set())
    assert "hello" in by_kind.get(NodeKind.FUNCTION, set())


def test_cpp_field_emitted() -> None:
    nodes, _ = _extract()
    fields = {n.name for n in nodes if n.kind == NodeKind.FIELD}
    assert {"banner", "title_"} <= fields


def test_cpp_base_class_emits_extends() -> None:
    nodes, edges = _extract()
    greeter_idx = next(
        i for i, n in enumerate(nodes)
        if n.name == "Greeter" and n.kind == NodeKind.CLASS
    )
    base_idx = next(
        i for i, n in enumerate(nodes)
        if n.name == "Base" and n.kind == NodeKind.CLASS
    )
    assert any(
        e.kind == EdgeKind.EXTENDS
        and e.source_id == greeter_idx
        and e.target_id == base_idx
        for e in edges
    )


def test_cpp_include_emits_import() -> None:
    nodes, edges = _extract()
    imports = {n.name for n in nodes if n.kind == NodeKind.IMPORT}
    assert "string" in imports
    assert any(e.kind == EdgeKind.IMPORTS for e in edges)


def test_cpp_in_file_call() -> None:
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
