"""ExpressFrameworkResolver tests (T031)."""

from __future__ import annotations

from pathlib import Path

from nexus_code_search.extraction.languages.typescript import TypeScriptExtractor
from nexus_code_search.frameworks.express import ExpressFrameworkResolver
from nexus_code_search.types import EdgeKind, NodeKind

FIXTURES = Path(__file__).parent / "fixtures" / "frameworks" / "express"


def _route_names(nodes) -> set[str]:
    return {n.name for n in nodes if n.kind == NodeKind.ROUTE}


def test_express_resolver_applies_to_typescript_files(tmp_path: Path) -> None:
    resolver = ExpressFrameworkResolver()
    assert resolver.applies_to(tmp_path / "main.ts") is True
    assert resolver.applies_to(tmp_path / "main.tsx") is True
    assert resolver.applies_to(tmp_path / "main.py") is False


def test_express_resolver_emits_basic_routes() -> None:
    fixture = FIXTURES / "basic_app.ts"
    src = fixture.read_bytes()
    ast_nodes, _ = TypeScriptExtractor().extract(fixture, src)
    nodes, edges = ExpressFrameworkResolver().resolve(fixture, src, ast_nodes)
    names = _route_names(nodes)
    assert names == {"GET /users", "POST /users", "GET /health"}


def test_express_resolver_emits_references_edge_to_handler() -> None:
    fixture = FIXTURES / "basic_app.ts"
    src = fixture.read_bytes()
    ast_nodes, _ = TypeScriptExtractor().extract(fixture, src)
    nodes, edges = ExpressFrameworkResolver().resolve(fixture, src, ast_nodes)
    create_idx = next(
        i for i, n in enumerate(ast_nodes) if n.name == "createUser"
    )
    create_route_local = next(
        i + len(ast_nodes)
        for i, n in enumerate(nodes)
        if n.name == "POST /users"
    )
    refs = [
        e
        for e in edges
        if e.kind == EdgeKind.REFERENCES
        and e.source_id == create_route_local
        and e.target_id == create_idx
    ]
    assert len(refs) == 1


def test_express_resolver_handles_router_methods() -> None:
    fixture = FIXTURES / "router_app.ts"
    src = fixture.read_bytes()
    ast_nodes, _ = TypeScriptExtractor().extract(fixture, src)
    nodes, _ = ExpressFrameworkResolver().resolve(fixture, src, ast_nodes)
    names = _route_names(nodes)
    assert names == {"GET /:id", "DELETE /:id", "PUT /:id"}


def test_express_resolver_emits_edges_for_middleware_chain() -> None:
    fixture = FIXTURES / "middleware_chain.ts"
    src = fixture.read_bytes()
    ast_nodes, _ = TypeScriptExtractor().extract(fixture, src)
    nodes, edges = ExpressFrameworkResolver().resolve(fixture, src, ast_nodes)
    names = _route_names(nodes)
    assert "POST /admin" in names
    assert "ALL /wildcard/*" in names
    # Wildcard route should reference auth, logger, and admin handlers.
    wildcard_local = next(
        i + len(ast_nodes)
        for i, n in enumerate(nodes)
        if n.name == "ALL /wildcard/*"
    )
    handler_names = {"authMiddleware", "loggerMiddleware", "adminHandler"}
    handler_ids = {
        i for i, n in enumerate(ast_nodes) if n.name in handler_names
    }
    refs = {
        e.target_id
        for e in edges
        if e.kind == EdgeKind.REFERENCES and e.source_id == wildcard_local
    }
    assert refs == handler_ids
