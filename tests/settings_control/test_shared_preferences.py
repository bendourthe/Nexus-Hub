"""Shared effort persistence and the settings switches' real write/read/reset contract."""
from __future__ import annotations

import json
from typing import Any

import pytest

from scripts.lib.settings_control import apply
from scripts.lib.settings_control import catalog as catalog_mod
from tests.settings_control.conftest import CLAUDE_IDS, Machine

GUARDS = (
    ("git_safety", "block_dangerous_git", True),
    ("secret_scan", "scan_secrets", True),
    ("edit_preservation", "protect_user_edits", True),
    ("large_file_warning", "warn_large_files", False),
)


def test_shared_effort_synchronizes_existing_user_override_and_resets_exactly(machine: Machine, catalog: dict[str, Any]) -> None:
    source = '{\n  "env": {"CLAUDE_CODE_EFFORT_LEVEL": "low", "KEEP": "yes"},\n  "model": "opus"\n}\n'
    machine.put("claude-user", source)
    machine.put("codex-user", '# user comment\nmodel_reasoning_effort = "low"\n')
    before = {key: machine.path(key).read_bytes() for key in ("claude-user", "codex-user")}
    ctx = machine.context(catalog)

    changed = apply.set_control(ctx, "effort", "high")

    assert changed["exit_code"] == 0
    preferences = machine.home / ".nexus-hub" / "preferences.json"
    assert json.loads(preferences.read_text()) == {"default_effort": "high"}
    native = json.loads(machine.path("claude-user").read_text())
    assert native["env"] == {"CLAUDE_CODE_EFFORT_LEVEL": "high", "KEEP": "yes"}
    assert all(native["modelSettings"][model]["effortLevel"] == "high" for model in CLAUDE_IDS)
    rows = machine.records(catalog)
    assert (rows["effort", "internal", "cli"]["state"], rows["effort", "internal", "cli"]["value"]) == ("in-effect", "high")
    assert rows["effort", "claude", "cli"]["state"] == "in-effect"

    restored = apply.reset_control(ctx, "effort")

    assert restored["exit_code"] == 0
    assert not preferences.exists()
    assert all(machine.path(key).read_bytes() == raw for key, raw in before.items())


def test_shared_effort_does_not_create_an_environment_override(machine: Machine, catalog: dict[str, Any]) -> None:
    machine.put("claude-user", {"env": {"KEEP": "yes"}})

    apply.set_control(machine.context(catalog), "effort", "medium")

    native = json.loads(machine.path("claude-user").read_text())
    assert native["env"] == {"KEEP": "yes"}
    assert machine.records(catalog)["effort", "claude", "cli"]["state"] == "in-effect"


@pytest.mark.parametrize("original_effort", ["low", "high"])
@pytest.mark.parametrize("other_env", ["", ', "KEEP": "yes"'])
def test_repeated_effort_then_override_removal_restores_the_original_bytes(machine: Machine, catalog: dict[str, Any], original_effort: str, other_env: str) -> None:
    source = '{\n  "env": {"CLAUDE_CODE_EFFORT_LEVEL": "' + original_effort + '"' + other_env + '},\n  "model": "opus"\n}\n'
    machine.put("claude-user", source)
    machine.put("codex-user", '# keep this comment\nmodel_reasoning_effort = "medium"\n')
    before = {key: machine.path(key).read_bytes() for key in ("claude-user", "codex-user")}
    ctx = machine.context(catalog)
    ctx.is_tty = lambda: True
    ctx.ask = lambda prompt: "yes"

    apply.set_control(ctx, "effort", "medium")
    apply.set_control(ctx, "effort", "high")
    removed = apply.remove_override(ctx, "effort", "claude")
    assert removed["exit_code"] == 0
    assert "CLAUDE_CODE_EFFORT_LEVEL" not in json.loads(machine.path("claude-user").read_text())["env"]
    apply.reset_control(ctx, "effort")
    apply.reset_control(ctx, "effort")

    assert all(machine.path(key).read_bytes() == raw for key, raw in before.items())
    assert not (machine.home / ".nexus-hub" / "preferences.json").exists()


def test_shared_effort_dry_run_creates_no_preference_file(machine: Machine, catalog: dict[str, Any]) -> None:
    doc = apply.set_control(machine.context(catalog), "effort", "high", dry_run=True)

    assert any(r["write"] == "internal.effort" and r["status"] == "would-write" for r in doc["results"])
    assert not (machine.home / ".nexus-hub").exists()


@pytest.mark.parametrize(("control", "key", "weakens"), GUARDS)
def test_guard_default_is_enabled_without_writing_a_file(machine: Machine, catalog: dict[str, Any], control: str, key: str, weakens: bool) -> None:
    row = machine.records(catalog)[control, "internal", "cli"]

    assert (row["state"], row["value"], row["native"]) == ("in-effect", "on", True)
    assert not machine.path("nexus-guardrails").exists()


@pytest.mark.parametrize(("control", "key", "weakens"), GUARDS)
def test_guard_toggle_round_trip_preserves_other_keys(machine: Machine, catalog: dict[str, Any], control: str, key: str, weakens: bool) -> None:
    source = '{\n  "unrelated": "keep"\n}\n'
    machine.put("nexus-guardrails", source)
    ctx = machine.context(catalog)
    ctx.is_tty = lambda: True
    ctx.ask = lambda prompt: "yes"

    dry_run = apply.set_control(ctx, control, "off", dry_run=True)
    assert dry_run["confirmation"]["required"] is weakens
    changed = apply.set_control(ctx, control, "off")

    assert changed["exit_code"] == 0
    assert json.loads(machine.path("nexus-guardrails").read_text()) == {"unrelated": "keep", key: False}
    assert machine.records(catalog)[control, "internal", "cli"]["value"] == "off"

    restored = apply.reset_control(ctx, control)

    assert restored["exit_code"] == 0
    assert machine.path("nexus-guardrails").read_text() == source
    assert machine.records(catalog)[control, "internal", "cli"]["value"] == "on"


@pytest.mark.parametrize(("control", "key", "weakens"), GUARDS[:3])
def test_guard_off_is_refused_without_a_person(machine: Machine, catalog: dict[str, Any], control: str, key: str, weakens: bool) -> None:
    with pytest.raises(apply.Refusal):
        apply.set_control(machine.context(catalog), control, "off")

    assert not machine.path("nexus-guardrails").exists()


@pytest.mark.parametrize("invalid", [0, 1, "false", None, []])
def test_invalid_guard_values_are_unknown_not_reported_disabled(machine: Machine, catalog: dict[str, Any], invalid: Any) -> None:
    machine.put("nexus-guardrails", {"scan_secrets": invalid})

    row = machine.records(catalog)["secret_scan", "internal", "cli"]

    assert row["state"] == "cannot-detect" and "boolean" in row["detail"]


@pytest.mark.parametrize("scope", ["shell", "project", "managed"])
def test_shared_effort_does_not_hide_external_overrides(machine: Machine, catalog: dict[str, Any], scope: str) -> None:
    if scope == "shell":
        machine.env["CLAUDE_CODE_EFFORT_LEVEL"] = "low"
    else:
        machine.put("claude-project" if scope == "project" else "claude-managed", {"effortLevel": "low"})

    apply.set_control(machine.context(catalog), "effort", "high")

    row = machine.records(catalog)["effort", "claude", "cli"]
    assert row["state"] == "overridden-by" and row["layer_value"] == "low"
    assert machine.records(catalog)["effort", "internal", "cli"]["value"] == "high"


def test_guard_catalog_cannot_forget_safety_weakening(catalog: dict[str, Any]) -> None:
    import copy

    changed = copy.deepcopy(catalog)
    next(w for w in changed["writes"] if w["id"] == "internal.secret_scan")["weakens_safety"] = False

    assert any("lowers a safety barrier" in finding for finding in catalog_mod.validate_structure(changed))
