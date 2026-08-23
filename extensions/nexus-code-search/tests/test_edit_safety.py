"""Domain-contract tests for read-only edit-safety verdict tools."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from nexus_code_search.config import CodeSearchConfig, index_dir_for
from nexus_code_search.extraction import ExtractionOrchestrator
from nexus_code_search.graph.safety import evaluate_safety
from nexus_code_search.server import (
    TOOL_MINIMUM_PROFILE,
    _all_tools,
    _handle_safety_check,
    _tools_for_profile,
)

SAFETY_TOOLS = {
    "code_edit_safety",
    "code_delete_safety",
    "code_rename_safety",
}


@pytest.fixture
def safety_repo(tmp_path: Path) -> tuple[Path, CodeSearchConfig]:
    (tmp_path / "src").mkdir()
    (tmp_path / "tests").mkdir()
    (tmp_path / "src" / "service.py").write_text(
        "def runtime_target(value):\n"
        "    return value + 1\n\n"
        "def internal_target(value):\n"
        "    return value * 2\n\n"
        "def internal_user(value):\n"
        "    return internal_target(value)\n\n"
        "def tested_target(value):\n"
        "    return value - 1\n\n"
        "def dead_target(value):\n"
        "    return value\n",
        encoding="utf-8",
    )
    (tmp_path / "src" / "api.py").write_text(
        "from service import runtime_target\n\n"
        "def endpoint(value):\n"
        "    return runtime_target(value)\n",
        encoding="utf-8",
    )
    (tmp_path / "tests" / "test_service.py").write_text(
        "from service import tested_target\n\n"
        "def test_target():\n"
        "    assert tested_target(2) == 1\n",
        encoding="utf-8",
    )
    config = CodeSearchConfig(hub_root=None)
    index_dir = index_dir_for(tmp_path, config)
    with ExtractionOrchestrator(tmp_path, config, index_dir) as orchestrator:
        orchestrator.run()
    return tmp_path, config


def _snapshot_tree(root: Path) -> dict[str, bytes]:
    return {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in root.rglob("*")
        if path.is_file()
    }


@pytest.mark.parametrize(
    ("symbol", "tier", "test_covered"),
    [
        ("runtime_target", "runtime_dependency", False),
        ("tested_target", "external_contract", True),
        ("internal_target", "internal_dependency", False),
        ("dead_target", "no_known_callers", False),
        ("missing_target", "insufficient_data", False),
    ],
)
def test_verdict_taxonomy_uses_real_graph_evidence(
    safety_repo: tuple[Path, CodeSearchConfig],
    symbol: str,
    tier: str,
    test_covered: bool,
) -> None:
    root, config = safety_repo
    result = evaluate_safety(
        index_dir_for(root, config) / "codegraph.db", symbol, "edit"
    )
    assert result["verdict"]["tier"] == tier
    assert result["recommended_action"].strip()
    assert "\n" not in result["recommended_action"]
    assert result["evidence"]["test_coverage"]["present"] is test_covered
    assert result["evidence"]["cross_repo_visibility"] == "unavailable"


@pytest.mark.parametrize("operation", ["edit", "delete", "rename"])
def test_each_operation_has_a_stable_response_contract(
    safety_repo: tuple[Path, CodeSearchConfig], operation: str
) -> None:
    root, config = safety_repo
    result = evaluate_safety(
        index_dir_for(root, config) / "codegraph.db", "runtime_target", operation
    )
    assert result["operation"] == operation
    assert result["symbol"] == "runtime_target"
    assert set(result["verdict"]) == {"tier", "rank", "meaning"}
    assert set(result["evidence"]) == {
        "matches",
        "callers",
        "importers",
        "references",
        "production_dependents",
        "external_dependents",
        "internal_dependents",
        "test_coverage",
        "complexity",
        "cross_repo_visibility",
        "index",
    }


@pytest.mark.parametrize("tool_name", sorted(SAFETY_TOOLS))
def test_server_handlers_are_read_only_and_offline(
    safety_repo: tuple[Path, CodeSearchConfig],
    tool_name: str,
    monkeypatch,
) -> None:
    root, config = safety_repo
    for key, value in {
        "HTTP_PROXY": "http://127.0.0.1:9",
        "HTTPS_PROXY": "http://127.0.0.1:9",
        "ALL_PROXY": "socks5://127.0.0.1:9",
        "API_KEY": "must-not-be-read",
    }.items():
        monkeypatch.setenv(key, value)
    before = _snapshot_tree(root)
    response = _handle_safety_check(
        tool_name,
        {"root": str(root), "symbol": "runtime_target"},
        config,
    )
    after = _snapshot_tree(root)
    assert before == after
    payload = json.loads(response[0].text)
    assert payload["recommended_action"]


def test_missing_index_is_insufficient_and_does_not_create_files(tmp_path: Path) -> None:
    db_path = tmp_path / ".nexus" / "code-index" / "codegraph.db"
    before = _snapshot_tree(tmp_path)
    result = evaluate_safety(db_path, "anything", "delete")
    assert result["verdict"]["tier"] == "insufficient_data"
    assert result["evidence"]["index"]["present"] is False
    assert _snapshot_tree(tmp_path) == before


def test_safety_tools_are_standard_profile_only() -> None:
    by_profile = {
        profile: {tool.name for tool in _tools_for_profile(profile)}
        for profile in ("minimal", "standard", "full")
    }
    assert SAFETY_TOOLS.isdisjoint(by_profile["minimal"])
    assert SAFETY_TOOLS <= by_profile["standard"]
    assert SAFETY_TOOLS <= by_profile["full"]
    assert {TOOL_MINIMUM_PROFILE[name] for name in SAFETY_TOOLS} == {"standard"}


def test_scope_cap_is_exactly_three_new_safety_tools() -> None:
    declared = {tool.name for tool in _all_tools()}
    assert {name for name in declared if name.endswith("_safety")} == SAFETY_TOOLS
