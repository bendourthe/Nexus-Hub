"""FastAPIFrameworkResolver tests (T030)."""

from __future__ import annotations

from pathlib import Path

from nexus_code_search.extraction.languages.python import PythonExtractor
from nexus_code_search.frameworks.fastapi import FastAPIFrameworkResolver
from nexus_code_search.types import EdgeKind, NodeKind

FIXTURES = Path(__file__).parent / "fixtures" / "frameworks" / "fastapi"


def _route_names(nodes) -> set[str]:
    return {n.name for n in nodes if n.kind == NodeKind.ROUTE}


def test_fastapi_resolver_applies_to_python_files(tmp_path: Path) -> None:
    resolver = FastAPIFrameworkResolver()
    assert resolver.applies_to(tmp_path / "main.py") is True
    assert resolver.applies_to(tmp_path / "app.pyi") is True
    assert resolver.applies_to(tmp_path / "main.ts") is False


def test_fastapi_resolver_emits_routes_for_app_decorators() -> None:
    fixture = FIXTURES / "basic_app.py"
    src = fixture.read_bytes()
    ast_nodes, _ = PythonExtractor().extract(fixture, src)
    nodes, edges = FastAPIFrameworkResolver().resolve(fixture, src, ast_nodes)
    names = _route_names(nodes)
    assert names == {"GET /", "GET /items/{item_id}", "POST /items"}


def test_fastapi_resolver_decorates_edge_targets_handler() -> None:
    fixture = FIXTURES / "basic_app.py"
    src = fixture.read_bytes()
    ast_nodes, _ = PythonExtractor().extract(fixture, src)
    nodes, edges = FastAPIFrameworkResolver().resolve(fixture, src, ast_nodes)
    read_item_idx = next(
        i for i, n in enumerate(ast_nodes) if n.name == "read_item"
    )
    route_local = next(
        i + len(ast_nodes)
        for i, n in enumerate(nodes)
        if n.name == "GET /items/{item_id}"
    )
    decorates = [
        e
        for e in edges
        if e.kind == EdgeKind.DECORATES
        and e.source_id == route_local
        and e.target_id == read_item_idx
    ]
    assert len(decorates) == 1


def test_fastapi_resolver_handles_router_prefix() -> None:
    fixture = FIXTURES / "router_app.py"
    src = fixture.read_bytes()
    ast_nodes, _ = PythonExtractor().extract(fixture, src)
    nodes, _ = FastAPIFrameworkResolver().resolve(fixture, src, ast_nodes)
    names = _route_names(nodes)
    # The resolver records the raw path arg; APIRouter prefix join is a
    # framework concern not detectable from the call site alone.
    assert names == {"GET /", "DELETE /{user_id}", "PATCH /{user_id}"}


def test_fastapi_resolver_handles_flask_style_handlers() -> None:
    fixture = FIXTURES / "flask_app.py"
    src = fixture.read_bytes()
    ast_nodes, _ = PythonExtractor().extract(fixture, src)
    nodes, _ = FastAPIFrameworkResolver().resolve(fixture, src, ast_nodes)
    names = _route_names(nodes)
    assert "ROUTE /" in names
    assert "GET /health" in names
    assert "PUT /items/<int:item_id>" in names


def test_fastapi_resolver_ignores_unrelated_decorators(tmp_path: Path) -> None:
    src = (
        b"from functools import lru_cache\n"
        b"\n"
        b"@lru_cache\n"
        b"def cached():\n"
        b"    return 1\n"
    )
    fixture = tmp_path / "main.py"
    fixture.write_bytes(src)
    ast_nodes, _ = PythonExtractor().extract(fixture, src)
    nodes, _ = FastAPIFrameworkResolver().resolve(fixture, src, ast_nodes)
    assert nodes == []
