"""Smoke test for the code_affected_tests MCP handler (T032)."""

from __future__ import annotations

import json
from pathlib import Path

from nexus_code_search.config import CodeSearchConfig
from nexus_code_search.extraction import ExtractionOrchestrator
from nexus_code_search.server import _handle_affected_tests


def _json(content_list) -> dict:
    return json.loads(content_list[0].text)


def test_handle_affected_tests_returns_test_files(tmp_path: Path) -> None:
    (tmp_path / "src").mkdir()
    (tmp_path / "tests").mkdir()
    (tmp_path / "src" / "utils.py").write_text(
        "def add(a, b):\n    return a + b\n", encoding="utf-8"
    )
    (tmp_path / "tests" / "test_utils.py").write_text(
        "from src.utils import add\n\n"
        "def test_add():\n    assert add(1, 2) == 3\n",
        encoding="utf-8",
    )
    config = CodeSearchConfig(hub_root=None)
    index_dir = tmp_path / ".nexus" / "code-index"
    with ExtractionOrchestrator(tmp_path, config, index_dir) as orch:
        orch.run(force=True)

    payload = _json(
        _handle_affected_tests(
            {
                "root": str(tmp_path),
                "changed_files": ["src/utils.py"],
                "depth": 5,
            },
            config,
        )
    )
    assert payload["root"] == str(tmp_path)
    assert payload["affected_tests"] == ["tests/test_utils.py"]
    assert payload["depth"] == 5


def test_handle_affected_tests_rejects_non_list(tmp_path: Path) -> None:
    config = CodeSearchConfig(hub_root=None)
    index_dir = tmp_path / ".nexus" / "code-index"
    index_dir.mkdir(parents=True, exist_ok=True)
    # Bootstrap an empty db so open_database does not fail.
    from nexus_code_search.db.schema import open_database

    open_database(index_dir).close()
    try:
        _handle_affected_tests(
            {"root": str(tmp_path), "changed_files": "src/foo.py"},
            config,
        )
    except ValueError as exc:
        assert "list" in str(exc)
    else:
        raise AssertionError("expected ValueError on non-list changed_files")
