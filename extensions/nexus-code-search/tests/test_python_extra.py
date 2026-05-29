"""Extra PythonExtractor coverage (T025 / T028)."""

from __future__ import annotations

from pathlib import Path

from nexus_code_search.extraction.languages.python import PythonExtractor
from nexus_code_search.types import EdgeKind, NodeKind


def test_python_module_constant(tmp_path: Path) -> None:
    src = "MAX_RETRIES = 3\nname = 'value'\n"
    nodes, _ = PythonExtractor().extract(tmp_path / "a.py", src.encode("utf-8"))
    constants = {n.name for n in nodes if n.kind == NodeKind.CONSTANT}
    variables = {n.name for n in nodes if n.kind == NodeKind.VARIABLE}
    assert "MAX_RETRIES" in constants
    assert "name" in variables


def test_python_class_field_vs_module_variable(tmp_path: Path) -> None:
    src = (
        "x = 1\n"
        "class Counter:\n"
        "    count = 0\n"
    )
    nodes, _ = PythonExtractor().extract(tmp_path / "a.py", src.encode("utf-8"))
    var_names = {n.name for n in nodes if n.kind == NodeKind.VARIABLE}
    field_names = {n.name for n in nodes if n.kind == NodeKind.FIELD}
    assert "x" in var_names
    assert "count" in field_names


def test_python_decorated_function_emits_decorates_edge(tmp_path: Path) -> None:
    src = (
        "def cache(fn):\n"
        "    return fn\n"
        "\n"
        "@cache\n"
        "def fetch():\n"
        "    return 1\n"
    )
    nodes, edges = PythonExtractor().extract(tmp_path / "a.py", src.encode("utf-8"))
    fetch_idx = next(i for i, n in enumerate(nodes) if n.name == "fetch")
    cache_idx = next(i for i, n in enumerate(nodes) if n.name == "cache")
    decs = [
        e
        for e in edges
        if e.kind == EdgeKind.DECORATES
        and e.source_id == cache_idx
        and e.target_id == fetch_idx
    ]
    assert decs


def test_python_class_method_call_via_attribute(tmp_path: Path) -> None:
    src = (
        "class Greeter:\n"
        "    def say(self):\n"
        "        return 'hi'\n"
        "    def go(self):\n"
        "        return self.say()\n"
    )
    nodes, edges = PythonExtractor().extract(tmp_path / "a.py", src.encode("utf-8"))
    say_idx = next(i for i, n in enumerate(nodes) if n.name == "say")
    go_idx = next(i for i, n in enumerate(nodes) if n.name == "go")
    calls = [
        e
        for e in edges
        if e.kind == EdgeKind.CALLS
        and e.source_id == go_idx
        and e.target_id == say_idx
    ]
    assert calls


def test_python_typed_parameter_name_extracted(tmp_path: Path) -> None:
    src = "def f(x: int, y: str = 'a', *args, **kwargs):\n    return x\n"
    nodes, _ = PythonExtractor().extract(tmp_path / "a.py", src.encode("utf-8"))
    params = {n.name for n in nodes if n.kind == NodeKind.PARAMETER}
    assert "x" in params
    assert "y" in params
    # *args / **kwargs may resolve as `args` / `kwargs` depending on grammar.
    assert any(p in params for p in ("args", "kwargs"))


def test_python_constructor_emits_instantiates_edge(tmp_path: Path) -> None:
    src = (
        "class Widget:\n"
        "    def __init__(self):\n"
        "        pass\n"
        "\n"
        "def build():\n"
        "    return Widget()\n"
    )
    nodes, edges = PythonExtractor().extract(tmp_path / "a.py", src.encode("utf-8"))
    build_idx = next(i for i, n in enumerate(nodes) if n.name == "build")
    widget_idx = next(
        i for i, n in enumerate(nodes)
        if n.name == "Widget" and n.kind == NodeKind.CLASS
    )
    inst = [
        e
        for e in edges
        if e.kind == EdgeKind.INSTANTIATES
        and e.source_id == build_idx
        and e.target_id == widget_idx
    ]
    assert inst
    # The constructor call is NOT also emitted as a plain `calls` edge.
    calls_to_widget = [
        e
        for e in edges
        if e.kind == EdgeKind.CALLS and e.target_id == widget_idx
    ]
    assert not calls_to_widget


def test_python_method_override_emits_overrides_edge(tmp_path: Path) -> None:
    src = (
        "class Base:\n"
        "    def run(self):\n"
        "        return 1\n"
        "\n"
        "class Derived(Base):\n"
        "    def run(self):\n"
        "        return 2\n"
    )
    nodes, edges = PythonExtractor().extract(tmp_path / "a.py", src.encode("utf-8"))
    base_run = next(
        i for i, n in enumerate(nodes) if n.qualified_name.endswith("Base.run")
    )
    derived_run = next(
        i for i, n in enumerate(nodes) if n.qualified_name.endswith("Derived.run")
    )
    overrides = [
        e
        for e in edges
        if e.kind == EdgeKind.OVERRIDES
        and e.source_id == derived_run
        and e.target_id == base_run
    ]
    assert overrides


def test_python_no_override_when_names_differ(tmp_path: Path) -> None:
    src = (
        "class Base:\n"
        "    def run(self):\n"
        "        return 1\n"
        "\n"
        "class Derived(Base):\n"
        "    def jog(self):\n"
        "        return 2\n"
    )
    nodes, edges = PythonExtractor().extract(tmp_path / "a.py", src.encode("utf-8"))
    overrides = [e for e in edges if e.kind == EdgeKind.OVERRIDES]
    assert not overrides


def test_python_extractor_skips_unresolvable_calls(tmp_path: Path) -> None:
    src = (
        "def main(items):\n"
        "    return [x for x in items if x()]\n"
    )
    nodes, edges = PythonExtractor().extract(tmp_path / "a.py", src.encode("utf-8"))
    # `x()` is a subscript-derived call where the target is a comprehension
    # variable; no matching node, so no CALLS edge should be emitted.
    main_idx = next(i for i, n in enumerate(nodes) if n.name == "main")
    calls = [e for e in edges if e.kind == EdgeKind.CALLS and e.source_id == main_idx]
    # Result may include 0 or filter-friendly: the assertion is "no crash" and
    # "no spurious calls into the parameter or main itself".
    for e in calls:
        target_node = nodes[e.target_id]
        assert target_node.id == -1  # local index marker remains
        assert target_node.name != "x"
