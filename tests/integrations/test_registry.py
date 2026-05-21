"""Tests for the registry-level behavior of scripts.lib.integrations."""

from __future__ import annotations

from scripts.lib.integrations import INTEGRATION_REGISTRY, get, list_keys


def test_registry_is_populated():
    keys = list_keys()
    assert len(keys) >= 10, f"expected >=10 integrations, got {len(keys)}: {keys}"


def test_registry_contains_required_platforms():
    required = {
        "claude",
        "codex",
        "cursor",
        "gemini",
        "gemini-cli",
        "opencode",
        "antigravity",
        "antigravity2",
        "copilot",
        "nexus-ai",
    }
    assert required.issubset(set(list_keys()))


def test_get_known_returns_instance():
    integ = get("claude")
    assert integ.key == "claude"
    assert integ.display_name


def test_get_unknown_raises():
    import pytest

    with pytest.raises(KeyError):
        get("not-a-real-platform")


def test_each_integration_describes_itself():
    for key in list_keys():
        integ = INTEGRATION_REGISTRY[key]
        d = integ.describe()
        assert d["key"] == key
        assert d["display_name"]
        assert d["class"]
        assert isinstance(d["config"], dict)
