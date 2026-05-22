"""TypeScriptExtractor tests (T025)."""

from __future__ import annotations

from pathlib import Path

from nexus_code_search.extraction.languages.typescript import TypeScriptExtractor
from nexus_code_search.types import EdgeKind, NodeKind


def test_ts_extractor_emits_class_and_interface(tmp_path: Path) -> None:
    src = (
        "interface Greeter {\n"
        "  greet(name: string): string;\n"
        "}\n"
        "\n"
        "export class HelloService implements Greeter {\n"
        "  greet(name: string) {\n"
        "    return `Hello, ${name}`;\n"
        "  }\n"
        "}\n"
    )
    nodes, edges = TypeScriptExtractor().extract(tmp_path / "a.ts", src.encode("utf-8"))
    kinds = {n.kind.value for n in nodes}
    assert "class" in kinds
    assert "interface" in kinds
    assert "method" in kinds
    impls = [e for e in edges if e.kind == EdgeKind.IMPLEMENTS]
    assert impls  # class implements interface


def test_ts_extractor_emits_function_and_export(tmp_path: Path) -> None:
    src = "export function add(a: number, b: number) {\n  return a + b;\n}\n"
    nodes, _ = TypeScriptExtractor().extract(tmp_path / "a.ts", src.encode("utf-8"))
    names = {n.name for n in nodes if n.kind == NodeKind.FUNCTION}
    assert "add" in names


def test_ts_extractor_emits_calls_in_file(tmp_path: Path) -> None:
    src = "function helper() { return 1; }\nfunction main() { return helper(); }\n"
    nodes, edges = TypeScriptExtractor().extract(tmp_path / "a.ts", src.encode("utf-8"))
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


def test_ts_extractor_emits_type_alias(tmp_path: Path) -> None:
    src = "type UserId = number;\n"
    nodes, _ = TypeScriptExtractor().extract(tmp_path / "a.ts", src.encode("utf-8"))
    assert any(n.kind == NodeKind.TYPE_ALIAS and n.name == "UserId" for n in nodes)


def test_ts_extractor_emits_extends_for_class(tmp_path: Path) -> None:
    src = (
        "class Animal { run() { return 'fast'; } }\n"
        "class Dog extends Animal { bark() { return 'woof'; } }\n"
    )
    nodes, edges = TypeScriptExtractor().extract(tmp_path / "a.ts", src.encode("utf-8"))
    dog_idx = next(i for i, n in enumerate(nodes) if n.name == "Dog")
    animal_idx = next(i for i, n in enumerate(nodes) if n.name == "Animal")
    extends = [
        e
        for e in edges
        if e.kind == EdgeKind.EXTENDS
        and e.source_id == dog_idx
        and e.target_id == animal_idx
    ]
    assert len(extends) == 1


def test_tsx_extractor_parses_jsx(tmp_path: Path) -> None:
    src = "export function Hello() {\n  return <div>hi</div>;\n}\n"
    nodes, _ = TypeScriptExtractor().extract(
        tmp_path / "Hello.tsx", src.encode("utf-8")
    )
    assert any(n.name == "Hello" and n.kind == NodeKind.FUNCTION for n in nodes)
