"""Tool-surface profiles and deterministic definition-cost accounting."""

from __future__ import annotations

import json
from collections.abc import Sequence

from mcp.types import Tool

from nexus_code_search.contextmap.tokens import estimate_tokens_offline

TOOL_PROFILE_RANK = {"minimal": 0, "standard": 1, "full": 2}

# Assign each tool to its lowest useful profile. ``tools_for_profile`` verifies
# this registry against the supplied definitions so surface drift fails loudly.
TOOL_MINIMUM_PROFILE = {
    "index_codebase": "minimal",
    "search_code": "minimal",
    "clear_index": "minimal",
    "get_indexing_status": "minimal",
    "index_graph": "minimal",
    "code_search": "minimal",
    "code_node": "minimal",
    "code_callers": "standard",
    "code_callees": "standard",
    "code_impact": "standard",
    "code_context": "standard",
    "code_explore": "standard",
    "code_affected_tests": "standard",
    "code_edit_safety": "standard",
    "code_delete_safety": "standard",
    "code_rename_safety": "standard",
    "generate_context_map": "full",
    "map_health": "full",
    "generate_knowledge_map": "full",
    "watch_for_changes": "full",
}


def tools_for_profile(profile: str, tools: Sequence[Tool]) -> list[Tool]:
    """Filter tool definitions for ``profile`` after validating the registry."""
    declared = {tool.name for tool in tools}
    assigned = set(TOOL_MINIMUM_PROFILE)
    if declared != assigned:
        missing = sorted(declared - assigned)
        stale = sorted(assigned - declared)
        raise RuntimeError(
            "Tool-profile registry drift: "
            f"unassigned={missing or 'none'}, stale={stale or 'none'}"
        )

    # Profile selection controls token cost, not authorization. Unknown values
    # therefore fail open to the backward-compatible full surface.
    selected = profile if profile in TOOL_PROFILE_RANK else "full"
    ceiling = TOOL_PROFILE_RANK[selected]
    return [
        tool
        for tool in tools
        if TOOL_PROFILE_RANK[TOOL_MINIMUM_PROFILE[tool.name]] <= ceiling
    ]


def definition_token_count(tools: Sequence[Tool]) -> int:
    """Estimate tokens for compact, deterministic MCP tool definitions."""
    payload = [
        tool.model_dump(mode="json", by_alias=True, exclude_none=True) for tool in tools
    ]
    serialized = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return estimate_tokens_offline(serialized)
