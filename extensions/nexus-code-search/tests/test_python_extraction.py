"""PythonExtractor tests (T025)."""

from __future__ import annotations

from pathlib import Path

from nexus_code_search.extraction.languages.python import PythonExtractor
from nexus_code_search.types import EdgeKind, NodeKind


def _kinds(nodes) -> set[str]:
    return {n.kind.value for n in nodes}


def _names(nodes, kind: NodeKind) -> set[str]:
    return {n.name for n in nodes if n.kind == kind}


def test_python_extractor_emits_function_and_class_nodes(tmp_path: Path) -> None:
    src = (
        "def helper(x, y):\n"
        "    return x + y\n"
        "\n"
        "class Service:\n"
        "    def run(self):\n"
        "        return helper(1, 2)\n"
    )
    nodes, edges = PythonExtractor().extract(tmp_path / "app.py", src.encode("utf-8"))
    assert "function" in _kinds(nodes)
    assert "class" in _kinds(nodes)
    assert "method" in _kinds(nodes)
    assert _names(nodes, NodeKind.FUNCTION) == {"helper"}
    assert _names(nodes, NodeKind.CLASS) == {"Service"}
    assert _names(nodes, NodeKind.METHOD) == {"run"}


def test_python_extractor_emits_parameters(tmp_path: Path) -> None:
    src = "def add(a, b, c=3):\n    return a + b + c\n"
    nodes, _ = PythonExtractor().extract(tmp_path / "a.py", src.encode("utf-8"))
    params = {n.name for n in nodes if n.kind == NodeKind.PARAMETER}
    assert params == {"a", "b", "c"}


def test_python_extractor_emits_calls_edge_in_file(tmp_path: Path) -> None:
    src = "def helper():\n    return 1\n\ndef main():\n    return helper()\n"
    nodes, edges = PythonExtractor().extract(tmp_path / "a.py", src.encode("utf-8"))
    # Find indices.
    helper_idx = next(i for i, n in enumerate(nodes) if n.name == "helper")
    main_idx = next(i for i, n in enumerate(nodes) if n.name == "main")
    calls = [
        e
        for e in edges
        if e.kind == EdgeKind.CALLS
        and e.source_id == main_idx
        and e.target_id == helper_idx
    ]
    assert len(calls) == 1


def test_python_extractor_emits_extends_edge(tmp_path: Path) -> None:
    src = "class Base:\n    pass\n\nclass Child(Base):\n    pass\n"
    nodes, edges = PythonExtractor().extract(tmp_path / "a.py", src.encode("utf-8"))
    base_idx = next(i for i, n in enumerate(nodes) if n.name == "Base")
    child_idx = next(i for i, n in enumerate(nodes) if n.name == "Child")
    extends = [
        e
        for e in edges
        if e.kind == EdgeKind.EXTENDS
        and e.source_id == child_idx
        and e.target_id == base_idx
    ]
    assert len(extends) == 1


def test_python_extractor_emits_import_edges(tmp_path: Path) -> None:
    src = "import os\nfrom pathlib import Path\n"
    nodes, edges = PythonExtractor().extract(tmp_path / "a.py", src.encode("utf-8"))
    imports = {n.name for n in nodes if n.kind == NodeKind.IMPORT}
    assert "os" in imports
    # The `Path` import is captured as `pathlib.Path` or `Path` depending on
    # which tree-sitter Python grammar version names the symbol. Both are
    # acceptable.
    assert any("Path" in name for name in imports)
    # At least one IMPORTS edge from the module to an import node.
    module_imports = [e for e in edges if e.kind == EdgeKind.IMPORTS]
    assert module_imports


def test_python_extractor_captures_docstring(tmp_path: Path) -> None:
    src = (
        "def greet(name):\n"
        '    """Say hello to someone."""\n'
        '    return f"Hello, {name}"\n'
    )
    nodes, _ = PythonExtractor().extract(tmp_path / "a.py", src.encode("utf-8"))
    greet = next(n for n in nodes if n.name == "greet")
    assert "Say hello" in greet.docstring


def test_python_extractor_handles_empty_source(tmp_path: Path) -> None:
    nodes, edges = PythonExtractor().extract(tmp_path / "a.py", b"")
    # One module node is still emitted.
    assert len(nodes) >= 1
    assert all(n.id == -1 for n in nodes)
