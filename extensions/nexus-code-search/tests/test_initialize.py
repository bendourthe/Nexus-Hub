"""Tests for the MCP initialize response carrying server instructions (T005)."""

from __future__ import annotations

from nexus_code_search.server import SERVER_INSTRUCTIONS


def test_server_instructions_is_non_empty() -> None:
    assert SERVER_INSTRUCTIONS
    assert SERVER_INSTRUCTIONS.strip()


def test_server_instructions_names_the_server() -> None:
    assert "nexus-code-search" in SERVER_INSTRUCTIONS


def test_server_instructions_lists_each_tool() -> None:
    for tool in ("index_codebase", "search_code", "clear_index", "get_indexing_status"):
        assert tool in SERVER_INSTRUCTIONS, f"missing tool reference: {tool}"


def test_server_instructions_cite_mcp_registry_policy() -> None:
    assert "MCP Registry Policy" in SERVER_INSTRUCTIONS
    assert "already-local" in SERVER_INSTRUCTIONS


def test_server_instructions_point_at_related_skill() -> None:
    assert "code-semantic-search" in SERVER_INSTRUCTIONS


def test_server_instructions_length_in_expected_band() -> None:
    n = len(SERVER_INSTRUCTIONS)
    assert 200 <= n <= 4000, f"instructions length {n} outside expected band"
