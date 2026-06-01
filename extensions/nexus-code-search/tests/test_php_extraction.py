"""PhpExtractor coverage (v2.4.0 / DF-v23-4)."""

from __future__ import annotations

from pathlib import Path

from nexus_code_search.extraction.languages.php import PhpExtractor
from nexus_code_search.types import EdgeKind, NodeKind

_SRC = b"""<?php

namespace App;

use App\\Models\\User;

const MAX = 10;

interface Speaker {
    public function speak(): string;
}

class Greeter implements Speaker {
    private $name;

    public function __construct($name) {
        $this->name = $name;
    }

    public function speak(): string {
        return greet($this->name);
    }
}

function greet($n) {
    return $n;
}
"""


def _extract():
    return PhpExtractor().extract(Path("app.php"), _SRC)


def test_php_emits_class_interface_function_method_const() -> None:
    nodes, _ = _extract()
    by_kind: dict[NodeKind, set[str]] = {}
    for n in nodes:
        by_kind.setdefault(n.kind, set()).add(n.name)
    assert "Greeter" in by_kind.get(NodeKind.CLASS, set())
    assert "Speaker" in by_kind.get(NodeKind.INTERFACE, set())
    assert "greet" in by_kind.get(NodeKind.FUNCTION, set())
    assert {"__construct", "speak"} <= by_kind.get(NodeKind.METHOD, set())
    assert "MAX" in by_kind.get(NodeKind.CONSTANT, set())
    assert "name" in by_kind.get(NodeKind.PROPERTY, set())


def test_php_implements_emits_edge() -> None:
    nodes, edges = _extract()
    greeter_idx = next(
        i for i, n in enumerate(nodes)
        if n.name == "Greeter" and n.kind == NodeKind.CLASS
    )
    speaker_idx = next(
        i for i, n in enumerate(nodes)
        if n.name == "Speaker" and n.kind == NodeKind.INTERFACE
    )
    assert any(
        e.kind == EdgeKind.IMPLEMENTS
        and e.source_id == greeter_idx
        and e.target_id == speaker_idx
        for e in edges
    )


def test_php_use_emits_import() -> None:
    nodes, edges = _extract()
    imports = {n.name for n in nodes if n.kind == NodeKind.IMPORT}
    assert "User" in imports
    assert any(e.kind == EdgeKind.IMPORTS for e in edges)


def test_php_in_file_call() -> None:
    nodes, edges = _extract()
    # `speak` is declared on both the interface and the class, so the call
    # edge may attach to either name-collision node; assert across both.
    speak_indices = {
        i for i, n in enumerate(nodes)
        if n.name == "speak" and n.kind == NodeKind.METHOD
    }
    called = {
        nodes[e.target_id].name
        for e in edges
        if e.kind == EdgeKind.CALLS and e.source_id in speak_indices
    }
    assert "greet" in called
