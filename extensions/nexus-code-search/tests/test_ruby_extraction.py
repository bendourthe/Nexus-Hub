"""RubyExtractor coverage (v2.4.0 / DF-v23-4)."""

from __future__ import annotations

from pathlib import Path

from nexus_code_search.extraction.languages.ruby import RubyExtractor
from nexus_code_search.types import EdgeKind, NodeKind

_SRC = b"""
require 'set'

module Animals
  class Base
  end

  class Greeter < Base
    def initialize(name)
      @name = name
    end

    def greet
      hello(@name)
    end
  end
end

def hello(text)
  text
end
"""


def _extract():
    return RubyExtractor().extract(Path("app.rb"), _SRC)


def test_ruby_emits_module_class_method_function() -> None:
    nodes, _ = _extract()
    by_kind: dict[NodeKind, set[str]] = {}
    for n in nodes:
        by_kind.setdefault(n.kind, set()).add(n.name)
    assert "Animals" in by_kind.get(NodeKind.NAMESPACE, set())
    assert {"Base", "Greeter"} <= by_kind.get(NodeKind.CLASS, set())
    assert {"initialize", "greet"} <= by_kind.get(NodeKind.METHOD, set())
    assert "hello" in by_kind.get(NodeKind.FUNCTION, set())


def test_ruby_superclass_emits_extends() -> None:
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


def test_ruby_require_emits_import() -> None:
    nodes, edges = _extract()
    imports = {n.name for n in nodes if n.kind == NodeKind.IMPORT}
    assert "set" in imports
    assert any(e.kind == EdgeKind.IMPORTS for e in edges)


def test_ruby_in_file_call() -> None:
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
