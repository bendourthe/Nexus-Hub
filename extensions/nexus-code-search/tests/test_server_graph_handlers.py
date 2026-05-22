"""Direct tests for the v2.0 server tool handlers (T026 / T028).

Calls the per-tool handler functions in-process so the MCP protocol layer
isn't on the hot path of the test. Exercises every graph tool dispatch
branch in `_handle_graph_query`.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from nexus_code_search.config import CodeSearchConfig
from nexus_code_search.extraction import ExtractionOrchestrator
from nexus_code_search.server import (
    _handle_clear,
    _handle_graph_query,
    _handle_index_graph,
)


@pytest.fixture
def indexed_repo(tmp_path: Path) -> Path:
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "calc.py").write_text(
        "def add(a, b):\n    return a + b\n"
        "def mul(a, b):\n    return a * b\n"
        "def compute(x, y):\n    return add(mul(x, y), 1)\n",
        encoding="utf-8",
    )
    cfg = CodeSearchConfig(hub_root=None)
    with ExtractionOrchestrator(tmp_path, cfg, tmp_path / ".nexus" / "code-index") as orch:
        orch.run()
    return tmp_path


def _payload(result) -> dict:
    return json.loads(result[0].text)


def test_handle_index_graph_indexes_repo(tmp_path: Path) -> None:
    (tmp_path / "a.py").write_text("def hi(): pass\n", encoding="utf-8")
    cfg = CodeSearchConfig(hub_root=None)
    res = _handle_index_graph({"root": str(tmp_path)}, cfg)
    payload = _payload(res)
    assert payload["files_indexed"] >= 1
    assert payload["nodes_inserted"] >= 1


def test_handle_index_graph_rejects_missing_root(tmp_path: Path) -> None:
    cfg = CodeSearchConfig(hub_root=None)
    with pytest.raises(ValueError):
        _handle_index_graph({"root": str(tmp_path / "missing")}, cfg)


def test_handle_index_graph_requires_root_arg() -> None:
    cfg = CodeSearchConfig(hub_root=None)
    with pytest.raises(ValueError):
        _handle_index_graph({}, cfg)


def test_handle_graph_query_code_search(indexed_repo: Path) -> None:
    cfg = CodeSearchConfig(hub_root=None)
    res = _handle_graph_query(
        "code_search", {"root": str(indexed_repo), "query": "add"}, cfg
    )
    payload = _payload(res)
    assert any(r["name"] == "add" for r in payload["results"])


def test_handle_graph_query_code_callers(indexed_repo: Path) -> None:
    cfg = CodeSearchConfig(hub_root=None)
    res = _handle_graph_query(
        "code_callers", {"root": str(indexed_repo), "symbol": "add"}, cfg
    )
    payload = _payload(res)
    assert payload["matches"] >= 1
    assert any(r["caller"]["name"] == "compute" for r in payload["results"])


def test_handle_graph_query_code_callees(indexed_repo: Path) -> None:
    cfg = CodeSearchConfig(hub_root=None)
    res = _handle_graph_query(
        "code_callees", {"root": str(indexed_repo), "symbol": "compute"}, cfg
    )
    payload = _payload(res)
    assert payload["matches"] >= 1
    callee_names = {r["callee"]["name"] for r in payload["results"]}
    assert {"add", "mul"} <= callee_names


def test_handle_graph_query_code_impact(indexed_repo: Path) -> None:
    cfg = CodeSearchConfig(hub_root=None)
    res = _handle_graph_query(
        "code_impact", {"root": str(indexed_repo), "symbol": "add", "depth": 2}, cfg
    )
    payload = _payload(res)
    assert payload["depth"] == 2
    impact_names = {
        m["name"] for r in payload["results"] for m in r["impact"]
    }
    assert "compute" in impact_names


def test_handle_graph_query_code_node(indexed_repo: Path) -> None:
    cfg = CodeSearchConfig(hub_root=None)
    res = _handle_graph_query(
        "code_node", {"root": str(indexed_repo), "symbol": "add"}, cfg
    )
    payload = _payload(res)
    assert any(m["name"] == "add" for m in payload["matches"])


def test_handle_graph_query_code_context(indexed_repo: Path) -> None:
    cfg = CodeSearchConfig(hub_root=None)
    res = _handle_graph_query(
        "code_context", {"root": str(indexed_repo), "symbol": "compute"}, cfg
    )
    payload = _payload(res)
    assert payload["matches"] >= 1
    first = payload["results"][0]
    assert first["node"]["name"] == "compute"
    assert "siblings" in first
    sib_names = {s["name"] for s in first["siblings"]}
    assert {"add", "mul"} <= sib_names


def test_handle_graph_query_code_explore(indexed_repo: Path) -> None:
    cfg = CodeSearchConfig(hub_root=None)
    res = _handle_graph_query(
        "code_explore", {"root": str(indexed_repo), "symbol": "add", "depth": 2}, cfg
    )
    payload = _payload(res)
    assert payload["matches"] >= 1


def test_handle_clear_removes_graph_db(indexed_repo: Path) -> None:
    cfg = CodeSearchConfig(hub_root=None)
    db_path = indexed_repo / ".nexus" / "code-index" / "codegraph.db"
    assert db_path.exists()
    res = _handle_clear({"root": str(indexed_repo)}, cfg)
    payload = _payload(res)
    assert payload["cleared"] is True
    assert not db_path.exists()
