"""affected_tests algorithm tests (T032).

The algorithm walks the reverse-import graph: for each changed file, find
every file whose `import` nodes name the changed file's module, recurse up
to `depth` hops, and filter the result to test files.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from nexus_code_search.config import CodeSearchConfig
from nexus_code_search.db.schema import open_database
from nexus_code_search.extraction import ExtractionOrchestrator
from nexus_code_search.graph.affected import affected_tests


def _make_repo(tmp_path: Path) -> Path:
    """Build a small fixture project with a clear dependency graph:

        src/utils.py        (leaf)
            <- src/api.py        (imports utils)
                <- tests/test_api.py   (imports api)
            <- tests/test_utils.py     (imports utils directly)
        src/db.py           (independent; should NOT be affected by utils changes)
            <- tests/test_db.py        (imports db)
    """
    (tmp_path / "src").mkdir()
    (tmp_path / "tests").mkdir()
    (tmp_path / "src" / "__init__.py").write_text("", encoding="utf-8")
    (tmp_path / "src" / "utils.py").write_text(
        "def add(a, b):\n    return a + b\n", encoding="utf-8"
    )
    (tmp_path / "src" / "api.py").write_text(
        "from src.utils import add\n\n"
        "def handle(x, y):\n    return add(x, y)\n",
        encoding="utf-8",
    )
    (tmp_path / "src" / "db.py").write_text(
        "def connect():\n    return None\n", encoding="utf-8"
    )
    (tmp_path / "tests" / "__init__.py").write_text("", encoding="utf-8")
    (tmp_path / "tests" / "test_utils.py").write_text(
        "from src.utils import add\n\n"
        "def test_add():\n    assert add(1, 2) == 3\n",
        encoding="utf-8",
    )
    (tmp_path / "tests" / "test_api.py").write_text(
        "from src.api import handle\n\n"
        "def test_handle():\n    assert handle(1, 2) == 3\n",
        encoding="utf-8",
    )
    (tmp_path / "tests" / "test_db.py").write_text(
        "from src.db import connect\n\n"
        "def test_connect():\n    assert connect() is None\n",
        encoding="utf-8",
    )
    return tmp_path


@pytest.fixture
def indexed_repo(tmp_path: Path) -> tuple[Path, Path]:
    """Build the fixture repo and run the graph extraction."""
    repo = _make_repo(tmp_path)
    config = CodeSearchConfig(hub_root=None)
    index_dir = tmp_path / ".nexus" / "code-index"
    with ExtractionOrchestrator(repo, config, index_dir) as orch:
        orch.run(force=True)
    return repo, index_dir


def test_affected_tests_finds_direct_importers(indexed_repo) -> None:
    repo, index_dir = indexed_repo
    conn = open_database(index_dir)
    try:
        result = affected_tests(
            conn,
            repo_root=repo,
            changed_files=[repo / "src" / "utils.py"],
            depth=5,
        )
    finally:
        conn.close()
    # tests/test_utils.py imports utils directly; tests/test_api.py imports
    # api which imports utils (transitive); tests/test_db.py is unrelated.
    assert "tests/test_utils.py" in result
    assert "tests/test_api.py" in result
    assert "tests/test_db.py" not in result


def test_affected_tests_skips_unrelated_files(indexed_repo) -> None:
    repo, index_dir = indexed_repo
    conn = open_database(index_dir)
    try:
        result = affected_tests(
            conn,
            repo_root=repo,
            changed_files=[repo / "src" / "db.py"],
            depth=5,
        )
    finally:
        conn.close()
    assert result == ["tests/test_db.py"]


def test_affected_tests_accepts_string_paths(indexed_repo) -> None:
    repo, index_dir = indexed_repo
    conn = open_database(index_dir)
    try:
        result = affected_tests(
            conn,
            repo_root=repo,
            changed_files=["src/utils.py"],
            depth=5,
        )
    finally:
        conn.close()
    assert "tests/test_utils.py" in result


def test_affected_tests_respects_depth(indexed_repo) -> None:
    """With depth=1, only direct importers should be returned (not transitive)."""
    repo, index_dir = indexed_repo
    conn = open_database(index_dir)
    try:
        result = affected_tests(
            conn,
            repo_root=repo,
            changed_files=[repo / "src" / "utils.py"],
            depth=1,
        )
    finally:
        conn.close()
    # Depth-1 walk from utils.py finds src/api.py (imports utils) and
    # tests/test_utils.py (imports utils). It does NOT walk further out
    # to tests/test_api.py (which imports api, not utils).
    assert "tests/test_utils.py" in result
    assert "tests/test_api.py" not in result


def test_affected_tests_empty_when_no_changes(indexed_repo) -> None:
    repo, index_dir = indexed_repo
    conn = open_database(index_dir)
    try:
        result = affected_tests(
            conn, repo_root=repo, changed_files=[], depth=5
        )
    finally:
        conn.close()
    assert result == []
