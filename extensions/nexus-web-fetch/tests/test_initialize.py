"""Tests for the MCP initialize response carrying server instructions (T005)."""

from __future__ import annotations

from nexus_web_fetch.server import SERVER_INSTRUCTIONS


def test_server_instructions_is_non_empty() -> None:
    assert SERVER_INSTRUCTIONS
    assert SERVER_INSTRUCTIONS.strip()


def test_server_instructions_names_the_server() -> None:
    assert "nexus-web-fetch" in SERVER_INSTRUCTIONS


def test_server_instructions_lists_the_fetch_url_tool() -> None:
    assert "fetch_url" in SERVER_INSTRUCTIONS


def test_server_instructions_cite_mcp_registry_policy() -> None:
    assert "MCP Registry Policy" in SERVER_INSTRUCTIONS
    assert "already-local" in SERVER_INSTRUCTIONS


def test_server_instructions_point_at_related_skills() -> None:
    assert "trend-research" in SERVER_INSTRUCTIONS
    assert "local-docs-lookup" in SERVER_INSTRUCTIONS


def test_server_instructions_length_in_expected_band() -> None:
    n = len(SERVER_INSTRUCTIONS)
    assert 200 <= n <= 4000, f"instructions length {n} outside expected band"
