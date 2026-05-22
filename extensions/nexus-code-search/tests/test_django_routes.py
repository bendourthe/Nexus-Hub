"""DjangoFrameworkResolver tests (T029)."""

from __future__ import annotations

from pathlib import Path

from nexus_code_search.extraction.languages.python import PythonExtractor
from nexus_code_search.frameworks.django import DjangoFrameworkResolver
from nexus_code_search.types import EdgeKind, NodeKind

FIXTURES = Path(__file__).parent / "fixtures" / "frameworks" / "django"


def _route_names(nodes) -> set[str]:
    return {n.name for n in nodes if n.kind == NodeKind.ROUTE}


def test_django_resolver_only_applies_to_urls_py(tmp_path: Path) -> None:
    resolver = DjangoFrameworkResolver()
    assert resolver.applies_to(tmp_path / "urls.py") is True
    assert resolver.applies_to(tmp_path / "views.py") is False
    assert resolver.applies_to(tmp_path / "models.py") is False


def test_django_resolver_emits_routes_for_path_calls() -> None:
    fixture = FIXTURES / "simple_urls.py"
    src = fixture.read_bytes()
    ast_nodes, _ = PythonExtractor().extract(fixture, src)
    nodes, edges = DjangoFrameworkResolver().resolve(fixture, src, ast_nodes)
    names = _route_names(nodes)
    assert names == {"", "users/<int:user_id>/", "about/"}


def test_django_resolver_emits_references_edge_to_handler() -> None:
    fixture = FIXTURES / "simple_urls.py"
    src = fixture.read_bytes()
    ast_nodes, _ = PythonExtractor().extract(fixture, src)
    nodes, edges = DjangoFrameworkResolver().resolve(fixture, src, ast_nodes)
    # Find the route node for "users/<int:user_id>/" and confirm it has a
    # references edge to the `user_detail` AST node.
    user_route_local = next(
        i + len(ast_nodes)
        for i, n in enumerate(nodes)
        if n.name == "users/<int:user_id>/"
    )
    user_handler_idx = next(
        i for i, n in enumerate(ast_nodes) if n.name == "user_detail"
    )
    refs = [
        e
        for e in edges
        if e.kind == EdgeKind.REFERENCES
        and e.source_id == user_route_local
        and e.target_id == user_handler_idx
    ]
    assert len(refs) == 1


def test_django_resolver_handles_re_path_and_as_view() -> None:
    fixture = FIXTURES / "regex_urls.py"
    src = fixture.read_bytes()
    ast_nodes, _ = PythonExtractor().extract(fixture, src)
    nodes, edges = DjangoFrameworkResolver().resolve(fixture, src, ast_nodes)
    names = _route_names(nodes)
    assert r"^articles/(?P<year>[0-9]{4})/$" in names
    # The class-based view should resolve to the YearArchiveView class node.
    cbv_route_local = next(
        i + len(ast_nodes)
        for i, n in enumerate(nodes)
        if n.name == r"^articles/(?P<year>[0-9]{4})/$"
    )
    cbv_idx = next(
        i for i, n in enumerate(ast_nodes) if n.name == "YearArchiveView"
    )
    refs = [
        e
        for e in edges
        if e.kind == EdgeKind.REFERENCES
        and e.source_id == cbv_route_local
        and e.target_id == cbv_idx
    ]
    assert len(refs) == 1


def test_django_resolver_emits_include_routes() -> None:
    fixture = FIXTURES / "nested_urls.py"
    src = fixture.read_bytes()
    ast_nodes, _ = PythonExtractor().extract(fixture, src)
    nodes, _ = DjangoFrameworkResolver().resolve(fixture, src, ast_nodes)
    names = _route_names(nodes)
    assert "health/" in names
    assert "include:myproject.api.urls" in names
    assert "include:django.contrib.admin.urls" in names
