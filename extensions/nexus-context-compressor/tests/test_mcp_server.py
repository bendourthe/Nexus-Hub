"""Tests for the internal MCP server (``nexus_context_compressor.server``).

The server module imports cleanly without the optional ``mcp`` extra (mcp is
imported lazily only inside ``run_server``), so its tool *logic* -- ``do_compress``
and ``do_retrieve`` -- and its ``SERVER_INSTRUCTIONS`` are tested here without a
live MCP runtime. The two tools are the reversible compress/retrieve pair the
Phase 4 runtime integration exposes.
"""

from __future__ import annotations

import json

import pytest
from nexus_context_compressor import server


@pytest.fixture(autouse=True)
def _isolated_store(monkeypatch, tmp_path):
    monkeypatch.setenv("NEXUS_CCR_STORE_PATH", str(tmp_path / "ccr.db"))


def _dupe_array(n: int = 40) -> str:
    return json.dumps([{"id": 1, "status": "ok"} for _ in range(n)])


# --- tool logic -----------------------------------------------------------


def test_do_compress_returns_metrics_and_compresses():
    result = server.do_compress(_dupe_array(), persist=True)
    assert result["tokens_after"] < result["tokens_before"]
    assert 0.0 < result["ratio"] <= 1.0
    assert result["segments"] >= 1
    assert "_ccr_dropped" in result["compressed"]


def test_do_compress_retrieve_round_trip():
    compressed = server.do_compress(_dupe_array(), persist=True)["compressed"]
    marker = next(
        r["_ccr_dropped"]
        for r in json.loads(compressed)
        if isinstance(r, dict) and "_ccr_dropped" in r
    )
    out = server.do_retrieve(marker)
    assert out["found"] is True
    assert out["original"][0] == {"id": 1, "status": "ok"}


def test_do_retrieve_miss():
    out = server.do_retrieve("<<ccr:deadbeef0000 5_rows>>")
    assert out["found"] is False
    assert out["marker"] == "<<ccr:deadbeef0000 5_rows>>"


def test_do_compress_never_expands_small_payload():
    out = server.do_compress("[1, 2, 3]")
    assert out["compressed"] == "[1, 2, 3]"


def test_do_compress_results_are_json_serializable():
    # The call_tool handler json.dumps the result; ensure both tools' outputs are
    # serializable (catches accidental non-serializable values).
    json.dumps(server.do_compress(_dupe_array()))
    json.dumps(server.do_retrieve("<<ccr:deadbeef0000 5_rows>>"))


# --- server instructions (mirror nexus-web-fetch test_initialize) --------


def test_server_instructions_non_empty():
    assert server.SERVER_INSTRUCTIONS.strip()


def test_server_instructions_name_the_server_and_tools():
    assert "nexus-context-compressor" in server.SERVER_INSTRUCTIONS
    assert "context_compress" in server.SERVER_INSTRUCTIONS
    assert "context_retrieve" in server.SERVER_INSTRUCTIONS


def test_server_instructions_cite_mcp_registry_policy():
    assert "MCP Registry Policy" in server.SERVER_INSTRUCTIONS
    assert "re-full" in server.SERVER_INSTRUCTIONS


def test_server_instructions_point_at_related_skills():
    assert "context-compression" in server.SERVER_INSTRUCTIONS
    assert "prompt-token-optimization" in server.SERVER_INSTRUCTIONS


def test_server_instructions_length_in_expected_band():
    n = len(server.SERVER_INSTRUCTIONS)
    assert 200 <= n <= 4000, f"instructions length {n} outside expected band"


def test_module_imports_without_mcp_extra():
    # server.py must import cleanly even when `mcp` is absent (lazy import in
    # run_server). Reaching here at all proves it; assert the pure handlers exist.
    assert callable(server.do_compress)
    assert callable(server.do_retrieve)
    assert callable(server.run_server)
