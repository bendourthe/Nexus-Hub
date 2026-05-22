"""GraphTraverser / GraphQueryManager tests (T026)."""

from __future__ import annotations

from pathlib import Path

import pytest

from nexus_code_search.config import CodeSearchConfig
from nexus_code_search.extraction import ExtractionOrchestrator
from nexus_code_search.graph import GraphQueryManager, GraphTraverser
from nexus_code_search.types import NodeKind


@pytest.fixture
def indexed_repo(tmp_path: Path) -> tuple[Path, Path]:
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "calc.py").write_text(
        "def add(a, b):\n    return a + b\n"
        "\n"
        "def mul(a, b):\n    return a * b\n"
        "\n"
        "def compute(x, y):\n    return add(mul(x, y), 1)\n",
        encoding="utf-8",
    )
    idx_dir = tmp_path / ".nexus" / "code-index"
    with ExtractionOrchestrator(
        tmp_path, CodeSearchConfig(hub_root=None), idx_dir
    ) as orch:
        orch.run()
    return tmp_path, idx_dir


def test_traverser_finds_callers(indexed_repo) -> None:
    _, idx_dir = indexed_repo
    from nexus_code_search.db import open_database

    conn = open_database(idx_dir)
    try:
        trav = GraphTraverser(conn)
        add_nodes = trav.find_by_name("add", kind=NodeKind.FUNCTION)
        assert add_nodes
        callers = trav.callers(add_nodes[0].id)
        assert any(c.name == "compute" for c in callers)
    finally:
        conn.close()


def test_traverser_finds_callees(indexed_repo) -> None:
    _, idx_dir = indexed_repo
    from nexus_code_search.db import open_database

    conn = open_database(idx_dir)
    try:
        trav = GraphTraverser(conn)
        compute_nodes = trav.find_by_name("compute", kind=NodeKind.FUNCTION)
        callees = trav.callees(compute_nodes[0].id)
        callee_names = {c.name for c in callees}
        # `compute` calls add and mul.
        assert {"add", "mul"} <= callee_names
    finally:
        conn.close()


def test_traverser_impact_radius_finds_transitive_callers(indexed_repo) -> None:
    _, idx_dir = indexed_repo
    from nexus_code_search.db import open_database

    conn = open_database(idx_dir)
    try:
        trav = GraphTraverser(conn)
        add_nodes = trav.find_by_name("add", kind=NodeKind.FUNCTION)
        # depth=2 should reach `compute` (1 hop, reverse calls).
        impact = trav.impact_radius(add_nodes[0].id, depth=2)
        assert any(n.name == "compute" for n in impact)
    finally:
        conn.close()


def test_traverser_find_path(indexed_repo) -> None:
    _, idx_dir = indexed_repo
    from nexus_code_search.db import open_database

    conn = open_database(idx_dir)
    try:
        trav = GraphTraverser(conn)
        compute = trav.find_by_name("compute", kind=NodeKind.FUNCTION)[0]
        add = trav.find_by_name("add", kind=NodeKind.FUNCTION)[0]
        path = trav.find_path(compute.id, add.id, max_depth=4)
        assert path
        assert path[0].id == compute.id
        assert path[-1].id == add.id
    finally:
        conn.close()


def test_query_manager_resolves_by_qualified_name(indexed_repo) -> None:
    _, idx_dir = indexed_repo
    from nexus_code_search.db import open_database

    conn = open_database(idx_dir)
    try:
        qm = GraphQueryManager(conn)
        result = qm.callers_of("calc.add")
        assert result["matches"] == 1
        assert any(r["caller"]["name"] == "compute" for r in result["results"])
    finally:
        conn.close()


def test_query_manager_search_fts(indexed_repo) -> None:
    _, idx_dir = indexed_repo
    from nexus_code_search.db import open_database

    conn = open_database(idx_dir)
    try:
        qm = GraphQueryManager(conn)
        results = qm.search("add", limit=5)
        names = [r["name"] for r in results]
        assert "add" in names
    finally:
        conn.close()


def test_query_manager_explore_aggregates(indexed_repo) -> None:
    _, idx_dir = indexed_repo
    from nexus_code_search.db import open_database

    conn = open_database(idx_dir)
    try:
        qm = GraphQueryManager(conn)
        payload = qm.explore("add", depth=2)
        assert payload["matches"] >= 1
        first = payload["results"][0]
        assert first["callers"]
        assert "impact" in first
    finally:
        conn.close()
