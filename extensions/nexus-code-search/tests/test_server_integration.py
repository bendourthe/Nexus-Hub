"""Integration smoke: exercise the tool handler functions end-to-end.

Uses the internal _handle_* functions directly rather than spinning up
the stdio transport, because MCP's stdio_server expects an actual
stream. The handlers are the real logic; the stdio layer is thin.
"""
from __future__ import annotations

import json
from pathlib import Path

from nexus_code_search.config import CodeSearchConfig
from nexus_code_search.server import (
    _handle_clear,
    _handle_index,
    _handle_search,
    _handle_status,
)
from nexus_code_search.types import IndexState


def _json(content_list) -> dict:
    return json.loads(content_list[0].text)


def test_end_to_end_index_and_search(sample_tree: Path, default_config: CodeSearchConfig) -> None:
    args = {"root": str(sample_tree)}

    idx_payload = _json(_handle_index(args, default_config))
    assert idx_payload["state"] == IndexState.IDLE.value
    assert idx_payload["files_processed"] >= 1

    search_args = {"root": str(sample_tree), "query": "compute_total"}
    search_payload = _json(_handle_search(search_args, default_config))
    assert search_payload["total_chunks"] >= 1
    assert search_payload["results"], "expected at least one search result"

    # First result should come from main.py since that's where compute_total lives.
    top = search_payload["results"][0]
    assert top["file_path"] == "src/main.py"


def test_search_with_no_index_returns_note(
    tmp_path: Path, default_config: CodeSearchConfig
) -> None:
    args = {"root": str(tmp_path), "query": "anything"}
    payload = _json(_handle_search(args, default_config))
    assert payload["results"] == []
    assert "note" in payload


def test_clear_index_removes_files(sample_tree: Path, default_config: CodeSearchConfig) -> None:
    _handle_index({"root": str(sample_tree)}, default_config)
    cleared = _json(_handle_clear({"root": str(sample_tree)}, default_config))
    assert cleared["cleared"] is True


def test_get_indexing_status_reflects_state(
    sample_tree: Path, default_config: CodeSearchConfig
) -> None:
    status_before = _json(_handle_status({"root": str(sample_tree)}, default_config))
    assert status_before["state"] == IndexState.IDLE.value
    assert status_before["files_processed"] == 0

    _handle_index({"root": str(sample_tree)}, default_config)
    status_after = _json(_handle_status({"root": str(sample_tree)}, default_config))
    assert status_after["files_processed"] >= 1
    assert status_after["last_updated"] is not None


def test_search_hybrid_mode_degrades_to_keyword_when_disabled(
    sample_tree: Path, default_config: CodeSearchConfig
) -> None:
    _handle_index({"root": str(sample_tree)}, default_config)
    payload = _json(
        _handle_search(
            {"root": str(sample_tree), "query": "x", "mode": "hybrid"},
            default_config,
        )
    )
    assert payload["requested_mode"] == "hybrid"
    assert payload["mode"] == "keyword"
    assert payload["degraded"] is False
