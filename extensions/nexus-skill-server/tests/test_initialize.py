"""Tests for the MCP initialize response carrying server instructions (T005)."""

from __future__ import annotations

from nexus_skill_server.server import SERVER_INSTRUCTIONS


def test_server_instructions_is_non_empty() -> None:
    assert SERVER_INSTRUCTIONS
    assert SERVER_INSTRUCTIONS.strip(), "instructions string must not be only whitespace"


def test_server_instructions_names_the_server() -> None:
    assert "nexus-skill-server" in SERVER_INSTRUCTIONS


def test_server_instructions_lists_each_tool() -> None:
    for tool in ("search_skills", "get_skill", "list_categories", "list_bundles", "get_bundle"):
        assert tool in SERVER_INSTRUCTIONS, f"missing tool reference: {tool}"


def test_server_instructions_cite_mcp_registry_policy() -> None:
    assert "MCP Registry Policy" in SERVER_INSTRUCTIONS
    assert "already-local" in SERVER_INSTRUCTIONS


def test_server_instructions_point_at_related_skill() -> None:
    assert "using-nexus-hub" in SERVER_INSTRUCTIONS


def test_server_instructions_length_in_expected_band() -> None:
    """Sanity check the instructions are useful (>= 200 chars) but not absurd
    (<= 4000 chars) so they remain cheap to surface on every initialize."""
    n = len(SERVER_INSTRUCTIONS)
    assert 200 <= n <= 4000, f"instructions length {n} outside expected band"
