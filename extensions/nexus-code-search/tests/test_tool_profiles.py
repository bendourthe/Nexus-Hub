"""Tool-profile surface and token-accounting contracts."""

from __future__ import annotations

import re
from contextlib import asynccontextmanager
from pathlib import Path
from types import SimpleNamespace

import pytest
from nexus_code_search import server as server_module
from nexus_code_search.config import resolve_config
from nexus_code_search.server import (
    _all_tools,
    _tools_for_profile,
    tool_definition_token_count,
)
from nexus_code_search.tool_profiles import TOOL_MINIMUM_PROFILE

EXPECTED_TOOLS = {
    "minimal": {
        "index_codebase",
        "search_code",
        "clear_index",
        "get_indexing_status",
        "index_graph",
        "code_search",
        "code_node",
    },
    "standard": {
        "index_codebase",
        "search_code",
        "clear_index",
        "get_indexing_status",
        "index_graph",
        "code_search",
        "code_node",
        "code_callers",
        "code_callees",
        "code_impact",
        "code_context",
        "code_explore",
        "code_affected_tests",
        "code_edit_safety",
        "code_delete_safety",
        "code_rename_safety",
    },
}
EXPECTED_TOOLS["full"] = {tool.name for tool in _all_tools()}


@pytest.mark.parametrize("profile", ["minimal", "standard", "full"])
def test_profile_exposes_exact_declared_tool_set(profile: str) -> None:
    assert {tool.name for tool in _tools_for_profile(profile)} == EXPECTED_TOOLS[
        profile
    ]


def test_every_tool_has_one_lowest_profile_assignment() -> None:
    assert set(TOOL_MINIMUM_PROFILE) == EXPECTED_TOOLS["full"]
    assert len(TOOL_MINIMUM_PROFILE) == len(_all_tools())


def test_profile_policy_is_not_owned_by_transport_server() -> None:
    server = Path(server_module.__file__).read_text(encoding="utf-8")
    assert "TOOL_MINIMUM_PROFILE =" not in server
    assert "TOOL_PROFILE_RANK =" not in server


def test_default_profile_preserves_full_surface(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("NEXUS_CODE_SEARCH_TOOL_PROFILE", raising=False)
    config = resolve_config()
    assert config.tool_profile == "full"
    assert {
        tool.name for tool in _tools_for_profile(config.tool_profile)
    } == EXPECTED_TOOLS["full"]


def test_environment_override_selects_profile(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("NEXUS_CODE_SEARCH_TOOL_PROFILE", " STANDARD ")
    assert resolve_config().tool_profile == "standard"


def test_invalid_environment_override_fails_open(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("NEXUS_CODE_SEARCH_TOOL_PROFILE", "unknown")
    assert resolve_config().tool_profile == "full"
    assert {tool.name for tool in _tools_for_profile("unknown")} == EXPECTED_TOOLS[
        "full"
    ]


def test_tool_definition_cost_increases_with_profile_surface() -> None:
    counts = [
        tool_definition_token_count(name) for name in ("minimal", "standard", "full")
    ]
    assert counts[0] > 0
    assert counts == sorted(counts)
    assert len(set(counts)) == 3


def test_documented_profile_counts_match_fresh_measurement() -> None:
    readme = Path(__file__).parents[1] / "README.md"
    text = readme.read_text(encoding="utf-8")
    pattern = re.compile(
        r"^\| `(minimal|standard|full)` \| (\d+) \| ([\d,]+) \|", re.MULTILINE
    )
    documented = {
        profile: (int(tool_count), int(token_count.replace(",", "")))
        for profile, tool_count, token_count in pattern.findall(text)
    }
    assert set(documented) == {"minimal", "standard", "full"}
    for profile, (documented_tools, documented_tokens) in documented.items():
        actual_tools = len(_tools_for_profile(profile))
        actual_tokens = tool_definition_token_count(profile)
        assert documented_tools == actual_tools
        tolerance = max(5, round(actual_tokens * 0.02))
        assert abs(documented_tokens - actual_tokens) <= tolerance


@pytest.mark.asyncio
async def test_stdio_server_registers_selected_profile(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, object] = {}

    class FakeInitializationOptions:
        def model_copy(self, *, update: dict[str, object]) -> SimpleNamespace:
            captured["initialization_update"] = update
            return SimpleNamespace(**update)

    class FakeServer:
        def __init__(self, name: str) -> None:
            captured["server_name"] = name

        def list_tools(self):
            def register(callback):
                captured["list_tools"] = callback
                return callback

            return register

        def call_tool(self):
            def register(callback):
                captured["call_tool"] = callback
                return callback

            return register

        def create_initialization_options(self) -> FakeInitializationOptions:
            return FakeInitializationOptions()

        async def run(self, read_stream, write_stream, options) -> None:
            captured["run"] = (read_stream, write_stream, options)

    @asynccontextmanager
    async def fake_stdio_server():
        yield "read", "write"

    monkeypatch.setattr(server_module, "Server", FakeServer)
    monkeypatch.setattr(server_module, "stdio_server", fake_stdio_server)
    monkeypatch.setattr(
        server_module,
        "resolve_config",
        lambda: server_module.CodeSearchConfig(hub_root=None, tool_profile="minimal"),
    )

    await server_module.run_server()

    list_tools = captured["list_tools"]
    exposed = await list_tools()
    assert {tool.name for tool in exposed} == EXPECTED_TOOLS["minimal"]
    assert captured["server_name"] == "nexus-code-search"
    assert captured["run"][:2] == ("read", "write")
    assert "nexus-code-search" in captured["initialization_update"]["instructions"]
