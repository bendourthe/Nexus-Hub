"""Portable effort writes, native equivalence and project-bound reversible sync."""
from __future__ import annotations

import json

import pytest
import tomllib

from scripts.lib.settings_control import apply
from scripts.lib.settings_control.effort import LEVELS, codex_levels
from tests.settings_control.conftest import Machine


def cache(machine: Machine, levels: tuple[str, ...] = LEVELS, model: str = "gpt-test") -> None:
    root = machine.path("codex-user").parent
    root.mkdir(parents=True, exist_ok=True)
    (root / "models_cache.json").write_text(json.dumps({"models": [{"slug": model, "supported_reasoning_levels": [{"effort": x} for x in levels]}]}), encoding="utf-8")


@pytest.mark.parametrize("requested", LEVELS)
def test_all_six_choices_map_to_valid_claude_and_advertised_codex_levels(machine, catalog, requested):
    machine.put("claude-user", '{"model":"opus", "env":{"KEEP":"yes"}}\n')
    machine.put("codex-user", '# keep\nmodel = "gpt-test"\n')
    cache(machine)
    original = {key: machine.path(key).read_bytes() for key in ("claude-user", "codex-user")}

    result = apply.set_control(machine.context(catalog), "effort", requested)

    claude = json.loads(machine.path("claude-user").read_text())
    assert claude["effortLevel"] == ("xhigh" if requested in ("max", "ultra") else requested)
    assert claude["env"] == {"KEEP": "yes", "CLAUDE_CODE_EFFORT_LEVEL": "max" if requested == "ultra" else requested}
    assert "ultracode" not in claude
    codex_native = "xhigh" if requested in ("max", "ultra") else requested
    assert tomllib.loads(machine.path("codex-user").read_text())["model_reasoning_effort"] == codex_native
    native = [r for r in result["after"] if r["tool"] in ("claude", "codex")]
    assert all(r["state"] == "in-effect" and r["matches_default"] and r["value"] == requested for r in native)
    assert {r["tool"]: r["mapped_effort"] for r in native} == {"claude": "max" if requested == "ultra" else requested, "codex": codex_native}

    apply.reset_control(machine.context(catalog), "effort")
    assert all(machine.path(key).read_bytes() == raw for key, raw in original.items())


@pytest.mark.parametrize("requested", LEVELS)
def test_deleted_authoritative_claude_environment_key_is_detected_and_recreated(machine, catalog, requested):
    ctx = machine.context(catalog)
    apply.set_control(ctx, "effort", requested)
    source = machine.path("claude-user")
    settings = json.loads(source.read_text())
    del settings["env"]["CLAUDE_CODE_EFFORT_LEVEL"]
    source.write_text(json.dumps(settings), encoding="utf-8")

    drift = machine.records(catalog)["effort", "claude", "cli"]

    assert drift["matches_default"] is False
    assert drift["mapped_effort"] == ("max" if requested == "ultra" else requested)
    assert drift["value"] != requested
    repaired = apply.set_control(ctx, "effort", requested)
    row = next(r for r in repaired["after"] if r["tool"] == "claude")
    assert row["matches_default"] and row["value"] == requested
    assert json.loads(source.read_text())["env"]["CLAUDE_CODE_EFFORT_LEVEL"] == drift["mapped_effort"]


@pytest.mark.parametrize(("levels", "requested", "expected"), [(LEVELS[:4], "max", "xhigh"), (LEVELS[:5], "ultra", "xhigh"), (("low", "high"), "medium", "low")])
def test_codex_uses_nearest_advertised_level_without_invalid_names(machine, catalog, levels, requested, expected):
    machine.put("codex-user", {"model": "gpt-test"})
    cache(machine, levels)

    result = apply.set_control(machine.context(catalog), "effort", requested)

    assert tomllib.loads(machine.path("codex-user").read_text())["model_reasoning_effort"] == expected
    row = next(r for r in result["after"] if r["tool"] == "codex")
    assert row["matches_default"] and row["mapped_effort"] == expected and row["value"] == requested


@pytest.mark.parametrize("content", ['not json', '{"models":null}', '{"models":[{"slug":"gpt-test","supported_reasoning_levels":"ultra"}]}'])
def test_invalid_capability_cache_uses_common_levels(machine, content):
    machine.put("codex-user", {"model": "gpt-test"})
    (machine.path("codex-user").parent / "models_cache.json").write_text(content)
    assert codex_levels(machine.home, machine.env, {"model": "gpt-test"}) == LEVELS[:4]


@pytest.mark.parametrize("levels", [("max", "ultra"), ()])
def test_capabilities_with_no_common_client_level_are_refused(machine, catalog, levels):
    machine.put("codex-user", {"model": "gpt-test", "model_reasoning_effort": "low"})
    cache(machine, levels)
    original = machine.path("codex-user").read_bytes()

    result = apply.set_control(machine.context(catalog), "effort", "ultra")

    assert any(r["tool"] == "codex" and r["status"] == "refused" for r in result["results"])
    assert machine.path("codex-user").read_bytes() == original


def test_existing_project_keys_sync_and_restore_without_touching_permission_rules(machine, catalog):
    machine.put("claude-project", '{"effortLevel":"low","permissions":{"defaultMode":"plan"},"env":{"CLAUDE_CODE_EFFORT_LEVEL":"low","KEEP":"yes"}}\n')
    machine.put("claude-project-local", '{"effortLevel":"medium","env":{"CLAUDE_CODE_EFFORT_LEVEL":"medium"}}\n')
    machine.trust_project()
    machine.put("codex-project", '# local\nmodel_reasoning_effort = "low"\napproval_policy = "on-request"\n')
    before = {key: machine.path(key).read_bytes() for key in ("claude-project", "claude-project-local", "codex-project")}

    result = apply.set_control(machine.context(catalog), "effort", "ultra")

    claude = json.loads(machine.path("claude-project").read_text())
    assert claude["effortLevel"] == "xhigh" and claude["env"]["CLAUDE_CODE_EFFORT_LEVEL"] == "max"
    assert claude["permissions"]["defaultMode"] == "plan" and claude["env"]["KEEP"] == "yes"
    assert tomllib.loads(machine.path("codex-project").read_text())["model_reasoning_effort"] == "xhigh"
    assert next(r for r in result["after"] if r["tool"] == "claude")["matches_default"]

    apply.reset_control(machine.context(catalog), "effort")
    assert all(machine.path(key).read_bytes() == raw for key, raw in before.items())


def test_project_ownership_never_crosses_workspace_boundaries(machine, catalog, tmp_path):
    machine.put("claude-project", '{"effortLevel":"low"}\n')
    first = machine.path("claude-project")
    apply.set_control(machine.context(catalog), "effort", "high")
    second = tmp_path / "other-project"
    second.mkdir()
    machine.project = second
    machine.put("claude-project", '{"effortLevel":"medium"}\n')
    other = machine.path("claude-project")
    apply.set_control(machine.context(catalog), "effort", "xhigh")
    apply.reset_control(machine.context(catalog), "effort")
    assert json.loads(other.read_text())["effortLevel"] == "medium"
    assert json.loads(first.read_text())["effortLevel"] == "high"
    machine.project = first.parent.parent
    apply.reset_control(machine.context(catalog), "effort")
    assert json.loads(first.read_text())["effortLevel"] == "low"


def test_untrusted_codex_project_is_unchanged_and_no_new_project_keys_are_created(machine, catalog):
    machine.put("codex-project", 'model_reasoning_effort = "low"\n')
    before = machine.path("codex-project").read_bytes()
    apply.set_control(machine.context(catalog), "effort", "high")
    assert machine.path("codex-project").read_bytes() == before
    assert not machine.path("claude-project").exists() and not machine.path("claude-project-local").exists()


def test_existing_profiles_map_their_own_model_and_reset_exactly(machine, catalog):
    machine.put("codex-user", '# hand chosen\nmodel = "gpt-test"\n[profiles.work]\nmodel_reasoning_effort = "low"\n[profiles.custom]\nmodel = "other"\nmodel_reasoning_effort = "low"\n[profiles.empty]\nmodel = "other"\n')
    cache(machine)
    before = machine.path("codex-user").read_bytes()

    apply.set_control(machine.context(catalog), "effort", "ultra")

    profiles = tomllib.loads(machine.path("codex-user").read_text())["profiles"]
    assert profiles["work"]["model_reasoning_effort"] == "xhigh"
    assert profiles["custom"]["model_reasoning_effort"] == "xhigh"
    assert "model_reasoning_effort" not in profiles["empty"]
    apply.reset_control(machine.context(catalog), "effort")
    assert machine.path("codex-user").read_bytes() == before
