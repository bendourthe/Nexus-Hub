"""KotlinExtractor coverage (v3.0.0 / DF-v24-7)."""

from __future__ import annotations

from pathlib import Path

from nexus_code_search.extraction.languages.kotlin import KotlinExtractor
from nexus_code_search.types import EdgeKind, NodeKind

_SRC = b"""
package com.example

import kotlin.collections.List

interface Greeter {
    fun describe(): String
}

open class Base

class Animal(val name: String) : Base(), Greeter {
    override fun describe(): String {
        return name
    }

    fun greet(): String {
        return hello(name)
    }
}

object Singleton {
    fun ping(): Int {
        return 1
    }
}

enum class Color {
    RED,
    GREEN
}

fun hello(text: String): String {
    return text
}
"""


def _extract():
    return KotlinExtractor().extract(Path("app.kt"), _SRC)


def test_kotlin_emits_interface_class_enum() -> None:
    nodes, _ = _extract()
    by_kind: dict[NodeKind, set[str]] = {}
    for n in nodes:
        by_kind.setdefault(n.kind, set()).add(n.name)
    assert "Greeter" in by_kind.get(NodeKind.INTERFACE, set())
    # `object Singleton` is emitted as a class alongside the regular classes.
    assert {"Base", "Animal", "Singleton"} <= by_kind.get(NodeKind.CLASS, set())
    assert "Color" in by_kind.get(NodeKind.ENUM, set())
    assert {"RED", "GREEN"} <= by_kind.get(NodeKind.ENUM_MEMBER, set())


def test_kotlin_emits_method_and_function() -> None:
    nodes, _ = _extract()
    by_kind: dict[NodeKind, set[str]] = {}
    for n in nodes:
        by_kind.setdefault(n.kind, set()).add(n.name)
    assert {"greet", "ping", "describe"} <= by_kind.get(NodeKind.METHOD, set())
    assert "hello" in by_kind.get(NodeKind.FUNCTION, set())


def test_kotlin_superclass_emits_extends_and_implements() -> None:
    nodes, edges = _extract()
    animal_idx = next(
        i for i, n in enumerate(nodes)
        if n.name == "Animal" and n.kind == NodeKind.CLASS
    )
    base_idx = next(
        i for i, n in enumerate(nodes)
        if n.name == "Base" and n.kind == NodeKind.CLASS
    )
    greeter_idx = next(
        i for i, n in enumerate(nodes)
        if n.name == "Greeter" and n.kind == NodeKind.INTERFACE
    )
    assert any(
        e.kind == EdgeKind.EXTENDS
        and e.source_id == animal_idx
        and e.target_id == base_idx
        for e in edges
    )
    assert any(
        e.kind == EdgeKind.IMPLEMENTS
        and e.source_id == animal_idx
        and e.target_id == greeter_idx
        for e in edges
    )


def test_kotlin_import_emits_import() -> None:
    nodes, edges = _extract()
    imports = {n.name for n in nodes if n.kind == NodeKind.IMPORT}
    assert "List" in imports
    assert any(e.kind == EdgeKind.IMPORTS for e in edges)


def test_kotlin_in_file_call() -> None:
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


def test_kotlin_package_and_properties() -> None:
    # Package -> namespace; a top-level `val` -> constant; a class `val` ->
    # property.
    src = b"""
package com.example.app

const val MAX_RETRIES = 3

class Config {
    val timeout: Int = 30
}
"""
    nodes, _ = KotlinExtractor().extract(Path("config.kt"), src)
    by_kind: dict[NodeKind, set[str]] = {}
    for n in nodes:
        by_kind.setdefault(n.kind, set()).add(n.name)
    assert "app" in by_kind.get(NodeKind.NAMESPACE, set())
    assert "MAX_RETRIES" in by_kind.get(NodeKind.CONSTANT, set())
    assert "timeout" in by_kind.get(NodeKind.PROPERTY, set())
