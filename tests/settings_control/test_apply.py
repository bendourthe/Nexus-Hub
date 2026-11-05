"""set, reset, remove-override, record-editor-write, owned-keys, and the human-presence guard
(v4.14.6 Phase 3, T020 and T021).

The shipped catalog admits Claude and Codex `model`, posture, and effort, and git-guardrails.
Cells whose rows are still Not-Settable (editor keys, Copilot, Claude and Codex attribution) are exercised through `admitted`,
a copy with every row admitted in memory, so the writers stay data-driven without changing an admission decision.
"""
from __future__ import annotations

import copy
import hashlib
import io
import json
import os
import sys
import tomllib
from pathlib import Path
from typing import Any

import pytest

from scripts.lib.settings_control import apply, writers
from tests.settings_control.conftest import CLAUDE_IDS, Machine

CLAUDE_FILE = '{\n  "model": "sonnet",\n  "permissions": {\n    "allow": [\n      "Bash(ls:*)",\n      "Read"\n    ]\n  },\n  "env": {\n    "CLAUDE_CODE_EFFORT_LEVEL": "high",\n    "KEEP": "yes"\n  }\n}\n'
CODEX_FILE = '# Codex config\nmodel = "gpt-6.1-sol"   # chosen by hand\n\n[windows]\nsandbox = "unelevated"  # needed on Windows\n'
COPILOT_FILE = '{\n  "model": "auto",\n  "permissions": {\n    "disableBypassPermissionsMode": "disable"\n  }\n}\n'


def seed(m: Machine) -> dict[str, bytes]:
    m.put("claude-user", CLAUDE_FILE)
    m.put("codex-user", CODEX_FILE)
    m.put("copilot-user", COPILOT_FILE)
    return files(m)


def files(m: Machine) -> dict[str, bytes]:
    out = {}
    for file_id in ("claude-user", "codex-user", "copilot-user", "nexus-guardrails"):
        path = m.path(file_id)
        if path.exists():
            out[file_id] = path.read_bytes()
    return out


def claude(m: Machine) -> dict[str, Any]:
    return json.loads(m.path("claude-user").read_text(encoding="utf-8"))


def codex(m: Machine) -> dict[str, Any]:
    return tomllib.loads(m.path("codex-user").read_text(encoding="utf-8"))


def statuses(doc: dict[str, Any]) -> dict[tuple[str, str], str]:
    return {(r["tool"], ".".join(r["key_path"] or ["-"])): r["status"] for r in doc["results"]}


def record(m: Machine) -> dict[str, Any]:
    return json.loads((m.home / ".nexus-hub" / "settings-control.json").read_text(encoding="utf-8"))


def person(ctx: apply.Context, answer: str = "yes") -> apply.Context:
    ctx.is_tty = lambda: True
    ctx.ask = lambda prompt: answer
    return ctx


# --- set ---------------------------------------------------------------------


def test_set_posture_ask_writes_each_admitted_tool_and_needs_no_confirmation(machine: Machine, catalog: dict[str, Any]) -> None:
    seed(machine)

    doc = apply.set_control(machine.context(catalog), "posture", "ask")

    assert doc["exit_code"] == 0 and doc["confirmation"] == {"required": False, "kind": None}
    assert claude(machine)["permissions"]["defaultMode"] == "default"
    assert claude(machine)["permissions"]["allow"] == ["Bash(ls:*)", "Read"]
    assert codex(machine)["approval_policy"] == "on-request" and codex(machine)["sandbox_mode"] == "workspace-write"
    assert '# chosen by hand' in machine.path("codex-user").read_text(encoding="utf-8")
    assert statuses(doc)[("claude", "permissions.defaultMode")] == "written"
    assert statuses(doc)[("copilot-cli", "defaultPermissionMode")] == "not-settable"
    assert {e["tool"] for e in record(machine)["entries"]} == {"claude", "codex"}


@pytest.mark.parametrize(("control", "value", "tool"), [("posture", "ask", None), ("model", "claude-opus-5-5", "claude"), ("model", "gpt-6.2", "codex")])
def test_set_then_reset_restores_every_file_byte_for_byte(machine: Machine, catalog: dict[str, Any], control: str, value: str, tool: str | None) -> None:
    before = seed(machine)
    ctx = machine.context(catalog)

    apply.set_control(ctx, control, value, tool)
    assert files(machine) != before
    doc = apply.reset_control(ctx, control, tool)

    assert files(machine) == before
    assert doc["exit_code"] == 0 and record(machine)["entries"] == []


def test_repeated_set_then_reset_restores_the_original_value(machine: Machine, catalog: dict[str, Any]) -> None:
    before = seed(machine)
    ctx = machine.context(catalog)

    apply.set_control(ctx, "model", "claude-opus-5-5", "claude")
    apply.set_control(ctx, "model", "claude-haiku-5-5", "claude")
    entry = record(machine)["entries"][0]
    assert entry["previous"] == {"present": True, "value": "sonnet"} and entry["new"]["value"] == "claude-haiku-5-5"
    apply.reset_control(ctx, "model", "claude")

    assert files(machine) == before


def test_reset_after_a_hand_edit_refuses_names_both_values_and_drops_the_entry(machine: Machine, catalog: dict[str, Any]) -> None:
    seed(machine)
    ctx = machine.context(catalog)
    apply.set_control(ctx, "model", "claude-opus-5-5", "claude")
    machine.put("claude-user", claude(machine) | {"model": "claude-haiku-5-5"}, merge_into=False)
    edited = files(machine)

    doc = apply.reset_control(ctx, "model", "claude")

    [result] = doc["results"]
    assert result["status"] == "drifted" and '"claude-opus-5-5"' in result["detail"] and '"claude-haiku-5-5"' in result["detail"]
    assert files(machine) == edited and record(machine)["entries"] == []


def test_reset_of_a_key_the_user_deleted_is_drift_not_a_restore(machine: Machine, catalog: dict[str, Any]) -> None:
    seed(machine)
    ctx = machine.context(catalog)
    apply.set_control(ctx, "model", "claude-opus-5-5", "claude")
    data = claude(machine)
    del data["model"]
    machine.put("claude-user", data, merge_into=False)

    doc = apply.reset_control(ctx, "model", "claude")

    assert doc["results"][0]["status"] == "drifted" and "model" not in claude(machine)


def test_a_malformed_tool_file_is_refused_untouched_and_other_tools_proceed(machine: Machine, catalog: dict[str, Any]) -> None:
    machine.put("claude-user", '{"model": ')
    machine.put("codex-user", CODEX_FILE)
    broken = machine.path("claude-user").read_bytes()

    doc = apply.set_control(machine.context(catalog), "posture", "ask")

    assert doc["exit_code"] == 1
    assert machine.path("claude-user").read_bytes() == broken
    assert statuses(doc)[("claude", "permissions.defaultMode")] == "refused" and "not valid JSON" in doc["results"][0]["detail"]
    assert codex(machine)["approval_policy"] == "on-request"
    assert {e["tool"] for e in record(machine)["entries"]} == {"codex"}


def test_a_file_changed_between_read_and_write_is_refused_and_the_record_is_put_back(machine: Machine, catalog: dict[str, Any], monkeypatch: pytest.MonkeyPatch) -> None:
    seed(machine)
    real_commit = writers.commit

    def interfere(plan: writers.Plan) -> bool:
        plan.loaded.real.write_bytes(plan.loaded.raw + b" ")
        return real_commit(plan)

    monkeypatch.setattr(writers, "commit", interfere)

    doc = apply.set_control(machine.context(catalog), "model", "claude-opus-5-5", "claude")

    assert doc["results"][0]["status"] == "refused" and "changed while" in doc["results"][0]["detail"]
    assert not (machine.home / ".nexus-hub" / "settings-control.json").exists() or record(machine)["entries"] == []


def test_an_unreadable_record_stops_set_untouched_with_a_repair_hint(machine: Machine, catalog: dict[str, Any]) -> None:
    before = seed(machine)
    path = machine.home / ".nexus-hub" / "settings-control.json"
    path.parent.mkdir()
    path.write_text("{not json", encoding="utf-8")

    with pytest.raises(apply.RecordError, match="repair or delete"):
        apply.set_control(machine.context(catalog), "model", "claude-opus-5-5", "claude")

    assert files(machine) == before and path.read_text(encoding="utf-8") == "{not json"


@pytest.mark.parametrize("bad", ['{"schema_version": 2, "entries": []}', '{"schema_version": 1}', "[]"])
def test_a_record_of_the_wrong_shape_is_unreadable(machine: Machine, bad: str) -> None:
    path = machine.home / ".nexus-hub" / "settings-control.json"
    path.parent.mkdir()
    path.write_text(bad, encoding="utf-8")

    with pytest.raises(apply.RecordError):
        apply.load_record(machine.home)


def test_record_entries_that_match_no_catalog_write_are_ignored_and_reported(machine: Machine, catalog: dict[str, Any]) -> None:
    before = seed(machine)
    ctx = machine.context(catalog)
    apply.set_control(ctx, "model", "claude-opus-5-5", "claude")
    doc = record(machine)
    doc["entries"] += [
        {"kind": "file", "tool": "claude", "file": "/etc/passwd", "key_path": ["model"], "previous": {"present": False}, "new": {"present": True, "value": "x"}},
        {"kind": "file", "tool": "claude", "file": "~/.claude/settings.json", "key_path": ["hooks", "PreToolUse"], "previous": {"present": False}, "new": {"present": True, "value": "x"}},
        {"kind": "file", "tool": "nope", "file": "~/.claude/settings.json", "key_path": ["model"], "previous": {"present": False}, "new": {"present": False}},
        "garbage",
    ]
    (machine.home / ".nexus-hub" / "settings-control.json").write_text(json.dumps(doc), encoding="utf-8")
    after_set = files(machine)

    reset = apply.reset_control(ctx, "model", "claude")

    assert len(reset["ignored"]) == 4 and all("matches no catalog write" in note for note in reset["ignored"])
    assert files(machine) == before and after_set != before
    owned = apply.owned_keys(ctx)
    assert owned["files"] == {} and len(owned["ignored"]) == 4


def test_unknown_control_value_and_missing_tool_are_usage_errors(machine: Machine, catalog: dict[str, Any]) -> None:
    ctx = machine.context(catalog)
    with pytest.raises(apply.UsageError, match="known controls"):
        apply.set_control(ctx, "nope", "x")
    with pytest.raises(apply.UsageError, match="use one of: ask, accept-edits, full-auto"):
        apply.set_control(ctx, "posture", "yolo")
    with pytest.raises(apply.UsageError, match="chosen per tool"):
        apply.set_control(ctx, "model", "claude-opus-5-5")
    with pytest.raises(apply.UsageError, match="unknown tool"):
        apply.set_control(ctx, "model", "x", "emacs")
    with pytest.raises(apply.UsageError, match="never written"):
        apply.set_control(ctx, "effort", "max")
    with pytest.raises(apply.UsageError, match="not a usable model value"):
        apply.set_control(ctx, "model", "bad\nvalue", "claude")


def test_a_tool_with_no_admitted_write_for_a_control_reports_not_settable_and_exits_four(machine: Machine, catalog: dict[str, Any]) -> None:
    before = seed(machine)

    doc = apply.set_control(machine.context(catalog), "attribution", "off", "codex")

    assert doc["exit_code"] == 4 and files(machine) == before
    assert {r["status"] for r in doc["results"]} == {"not-settable"}


def test_effort_is_written_to_both_claude_keys_and_codex_from_the_shipped_catalog(machine: Machine, catalog: dict[str, Any]) -> None:
    seed(machine)

    doc = apply.set_control(machine.context(catalog), "effort", "high")

    assert doc["exit_code"] == 0
    assert claude(machine)["effortLevel"] == "high" and all(claude(machine)["modelSettings"][i]["effortLevel"] == "high" for i in CLAUDE_IDS)
    assert codex(machine)["model_reasoning_effort"] == "high"
    assert statuses(doc)[("copilot-cli", "effortLevel")] == "not-settable"


def test_dry_run_writes_nothing_and_asks_nobody(machine: Machine, catalog: dict[str, Any]) -> None:
    before = seed(machine)
    ctx = machine.context(catalog, ask=lambda prompt: pytest.fail("a dry run must not prompt"))

    doc = apply.set_control(ctx, "posture", "full-auto", dry_run=True)

    assert doc["exit_code"] == 0 and doc["confirmation"]["required"] is True
    assert {r["status"] for r in doc["results"]} >= {"would-write"}
    assert files(machine) == before and not (machine.home / ".nexus-hub").exists()


def test_a_tool_that_is_not_installed_is_skipped_and_nothing_is_created(machine: Machine, catalog: dict[str, Any]) -> None:
    del machine.commands["codex"]

    doc = apply.set_control(machine.context(catalog), "model", "gpt-6.1-sol", "codex")

    assert statuses(doc)[("codex", "model")] == "tool-not-installed" and doc["exit_code"] == 4
    assert not machine.path("codex-user").exists()


def test_the_codex_model_named_exception_writes_only_as_an_explicit_user_choice(machine: Machine, catalog: dict[str, Any]) -> None:
    seed(machine)

    apply.set_control(machine.context(catalog), "model", "gpt-6.2", "codex")

    assert codex(machine)["model"] == "gpt-6.2"
    codex_write = next(w for w in catalog["writes"] if w["id"] == "codex.model")
    assert apply.check_write_allowed(catalog, codex_write, "gpt-6.2") is None
    other = {**codex_write, "key_path": ["memories", "extract_model"]}
    assert "omitted key" in str(apply.check_write_allowed(catalog, other, "x"))


def test_codex_posture_is_skipped_when_the_file_uses_default_permissions(machine: Machine, catalog: dict[str, Any]) -> None:
    machine.put("codex-user", 'default_permissions = ":workspace"\n' + CODEX_FILE)
    before = machine.path("codex-user").read_bytes()

    doc = apply.set_control(machine.context(catalog), "posture", "ask", "codex")

    assert {r["status"] for r in doc["results"]} == {"skipped"} and "default_permissions" in doc["results"][0]["detail"]
    assert machine.path("codex-user").read_bytes() == before and doc["exit_code"] == 4


def test_untrusted_is_never_written(catalog: dict[str, Any]) -> None:
    write = next(w for w in catalog["writes"] if w["id"] == "codex.posture")
    assert apply.check_write_allowed(catalog, write, "untrusted") is not None
    assert apply.check_write_allowed(catalog, write, "never") is None


def test_missing_tomlkit_skips_codex_and_other_tools_proceed(machine: Machine, catalog: dict[str, Any], monkeypatch: pytest.MonkeyPatch) -> None:
    seed(machine)
    codex_before = machine.path("codex-user").read_bytes()
    monkeypatch.setitem(sys.modules, "tomlkit", None)

    doc = apply.set_control(machine.context(catalog), "posture", "ask")

    assert doc["exit_code"] == 1
    assert statuses(doc)[("claude", "permissions.defaultMode")] == "written"
    assert statuses(doc)[("codex", "approval_policy")] == "refused"
    assert any("pip install tomlkit" in r["detail"] for r in doc["results"])
    assert machine.path("codex-user").read_bytes() == codex_before


def test_an_absent_file_is_created_and_reset_deletes_it(machine: Machine, catalog: dict[str, Any]) -> None:
    ctx = machine.context(catalog)

    apply.set_control(ctx, "git_guardrails", "on")
    guard = machine.path("nexus-guardrails")
    assert json.loads(guard.read_text(encoding="utf-8")) == {"block_git_bypass_flags": True}
    assert record(machine)["entries"][0]["file_created"] is True
    apply.reset_control(ctx, "git_guardrails")

    assert not guard.exists() and record(machine)["entries"] == []


def test_a_created_file_that_gained_other_keys_survives_and_hands_over_the_deletion(machine: Machine, catalog: dict[str, Any]) -> None:
    ctx = machine.context(catalog)
    apply.set_control(ctx, "model", "gpt-6.1-sol", "codex")
    apply.set_control(ctx, "posture", "ask", "codex")
    path = machine.path("codex-user")

    apply.reset_control(ctx, "model", "codex")
    assert path.exists() and "model" not in codex(machine)
    apply.reset_control(ctx, "posture", "codex")

    assert not path.exists()


def test_the_record_is_owner_only(machine: Machine, catalog: dict[str, Any]) -> None:
    seed(machine)
    apply.set_control(machine.context(catalog), "model", "claude-opus-5-5", "claude")
    path = machine.home / ".nexus-hub" / "settings-control.json"

    if os.name == "nt":
        import subprocess

        shown = subprocess.run(["icacls", str(path)], capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW, check=True).stdout
        assert "OWNER RIGHTS" in shown and "Everyone" not in shown and "BUILTIN\\Users" not in shown
    else:
        assert path.stat().st_mode & 0o077 == 0


def test_set_reports_the_resulting_state_including_a_project_override(machine: Machine, catalog: dict[str, Any]) -> None:
    seed(machine)
    machine.put("claude-project", {"permissions": {"defaultMode": "plan"}})

    doc = apply.set_control(machine.context(catalog), "posture", "ask", "claude")

    [after] = [r for r in doc["after"] if r["surface"] == "cli"]
    assert after["state"] == "overridden-by" and "project" in after["layer"]


# --- The admitted-in-memory catalog: effort, models, editor keys -------------


def test_effort_writes_every_model_id_and_fallback_with_a_matching_user_override(machine: Machine, admitted: dict[str, Any]) -> None:
    before = seed(machine)
    ctx = machine.context(admitted)

    doc = apply.set_control(ctx, "effort", "high", "claude")

    data = claude(machine)
    assert data["effortLevel"] == "high"
    assert {m: v["effortLevel"] for m, v in data["modelSettings"].items()} == {m: "high" for m in CLAUDE_IDS}
    assert data["env"]["CLAUDE_CODE_EFFORT_LEVEL"] == "high" and data["permissions"]["allow"] == ["Bash(ls:*)", "Read"]
    [still] = [r for r in doc["after"] if r["tool"] == "claude"]
    assert still["state"] == "in-effect" and still["layer"] is None
    apply.reset_control(ctx, "effort", "claude")
    assert files(machine) == before


def test_ids_already_in_model_settings_are_covered_and_a_dotted_id_is_not_split(machine: Machine, admitted: dict[str, Any]) -> None:
    machine.put("claude-user", {"modelSettings": {"claude-3.5-sonnet.v2": {"effortLevel": "low"}, "bad id!": {"effortLevel": "low"}}})

    apply.set_control(machine.context(admitted), "effort", "xhigh", "claude")

    settings = claude(machine)["modelSettings"]
    assert settings["claude-3.5-sonnet.v2"]["effortLevel"] == "xhigh"
    assert settings["bad id!"]["effortLevel"] == "low"
    assert set(settings) == {"claude-3.5-sonnet.v2", "bad id!", *CLAUDE_IDS}


def test_codex_effort_and_copilot_effort_are_written_from_the_catalog(machine: Machine, admitted: dict[str, Any]) -> None:
    seed(machine)

    apply.set_control(machine.context(admitted), "effort", "xhigh")

    assert codex(machine)["model_reasoning_effort"] == "xhigh"
    assert json.loads(machine.path("copilot-user").read_text(encoding="utf-8"))["effortLevel"] == "xhigh"


def test_attribution_off_writes_each_leaf_and_keeps_other_sub_keys(machine: Machine, admitted: dict[str, Any]) -> None:
    machine.put("claude-user", {"attribution": {"commit": "x", "other": 1}})

    apply.set_control(machine.context(admitted), "attribution", "off", "claude")

    assert claude(machine)["attribution"] == {"commit": "", "other": 1, "pr": ""}


def test_editor_writes_are_returned_not_written_and_reset_returns_their_restores(machine: Machine, admitted: dict[str, Any]) -> None:
    seed(machine)
    ctx = person(machine.context(admitted))

    doc = apply.set_control(ctx, "posture", "full-auto", "claude")

    keys = {e["key"] for e in doc["editor_writes"]}
    assert keys == {"claudeCode.initialPermissionMode", "claudeCode.allowDangerouslySkipPermissions"}
    for write in doc["editor_writes"]:
        payload = {"write": write["write"], "previous": {"present": True, "value": "default"}, "new": write["value"], "profile": "Default"}
        apply.record_editor_write(ctx, json.dumps(payload))
    again = apply.record_editor_write(ctx, json.dumps({"write": "claude-vscode.initial_permission_mode", "previous": {"present": True, "value": "default"}, "new": "plan"}))
    assert again["recorded"]
    reset = apply.reset_control(ctx, "posture", "claude")

    restores = {e["key"]: e for e in reset["editor_restores"]}
    assert set(restores) == keys and restores["claudeCode.initialPermissionMode"]["restore"] == {"present": True, "value": "default"}
    assert restores["claudeCode.initialPermissionMode"]["profile"] == "Default"
    assert not [e for e in record(machine)["entries"] if e["file"] == "vscode-config"]


@pytest.mark.parametrize(
    "payload",
    ['not json', '[]', '{"write": "claude.model", "previous": {"present": false}, "new": "x"}', '{"write": "nope", "previous": {"present": false}, "new": "x"}',
     '{"write": "claude-vscode.initial_permission_mode", "previous": {"present": "yes"}, "new": "x"}',
     '{"write": "claude-vscode.initial_permission_mode", "previous": {"present": false}}'],
)
def test_record_editor_write_validates_its_payload(machine: Machine, admitted: dict[str, Any], payload: str) -> None:
    with pytest.raises(apply.UsageError):
        apply.record_editor_write(machine.context(admitted), payload)


def test_record_editor_write_refuses_a_row_that_is_not_settable(machine: Machine, catalog: dict[str, Any]) -> None:
    payload = '{"write": "claude-vscode.initial_permission_mode", "previous": {"present": false}, "new": "x"}'
    with pytest.raises(apply.UsageError, match="not settable"):
        apply.record_editor_write(machine.context(catalog), payload)


# --- remove-override ---------------------------------------------------------


def test_remove_override_removes_only_the_catalog_key_after_confirmation_and_reset_restores_it(machine: Machine, admitted: dict[str, Any]) -> None:
    before = seed(machine)
    ctx = machine.context(admitted)

    doc = apply.remove_override(person(ctx), "effort", "claude")

    assert doc["results"][0]["status"] == "removed" and doc["confirmation"] == {"required": True, "kind": "confirmed"}
    data = claude(machine)
    assert "CLAUDE_CODE_EFFORT_LEVEL" not in data["env"] and data["env"]["KEEP"] == "yes" and data["model"] == "sonnet"
    assert record(machine)["entries"][0]["kind"] == "override-removal"
    apply.reset_control(ctx, "effort", "claude")
    assert files(machine) == before


def test_remove_override_without_a_person_is_refused_untouched(machine: Machine, admitted: dict[str, Any]) -> None:
    before = seed(machine)

    with pytest.raises(apply.Refusal, match="needs a person"):
        apply.remove_override(machine.context(admitted), "effort", "claude")

    assert files(machine) == before


def test_remove_override_of_a_safety_block_is_refused_under_an_agent_marker_even_with_a_tty(machine: Machine, admitted: dict[str, Any]) -> None:
    before = seed(machine)
    machine.env["CLAUDECODE"] = "1"

    with pytest.raises(apply.Refusal, match="CLAUDECODE"):
        apply.remove_override(person(machine.context(admitted)), "posture", "copilot-cli")

    assert files(machine) == before


def test_remove_override_of_the_copilot_block_then_reset(machine: Machine, admitted: dict[str, Any]) -> None:
    before = seed(machine)
    ctx = person(machine.context(admitted))

    apply.remove_override(ctx, "posture", "copilot-cli")
    assert "disableBypassPermissionsMode" not in json.loads(machine.path("copilot-user").read_text(encoding="utf-8")).get("permissions", {})
    apply.reset_control(ctx, "posture", "copilot-cli")

    assert files(machine) == before


def test_remove_override_with_the_key_absent_does_nothing(machine: Machine, admitted: dict[str, Any]) -> None:
    machine.put("claude-user", '{"model": "sonnet"}\n')
    before = files(machine)

    doc = apply.remove_override(machine.context(admitted), "effort", "claude")

    assert doc["results"][0]["status"] == "absent" and files(machine) == before


def test_remove_override_is_not_available_for_a_control_that_is_not_settable(machine: Machine, catalog: dict[str, Any]) -> None:
    before = seed(machine)
    demoted = copy.deepcopy(catalog)
    for write in demoted["writes"]:
        if write["id"].startswith("claude.effort."):
            write["admission"] = "not-settable"
            write["not_settable_reason"] = "No Proof Record: test copy."
            write.pop("proof", None)

    doc = apply.remove_override(machine.context(demoted), "effort", "claude")

    assert doc["results"][0]["status"] == "not-settable" and doc["exit_code"] == 4 and files(machine) == before
    with pytest.raises(apply.UsageError, match="no removable override"):
        apply.remove_override(machine.context(catalog), "model", "claude")


def test_remove_override_of_the_legacy_effort_variable_works_from_the_shipped_catalog(machine: Machine, catalog: dict[str, Any]) -> None:
    before = seed(machine)
    ctx = person(machine.context(catalog))

    doc = apply.remove_override(ctx, "effort", "claude")

    assert doc["results"][0]["status"] == "removed"
    assert "CLAUDE_CODE_EFFORT_LEVEL" not in claude(machine)["env"]
    apply.reset_control(ctx, "effort", "claude")
    assert files(machine) == before


# --- Human presence (T021) ---------------------------------------------------


def full_auto(ctx: apply.Context) -> dict[str, Any]:
    return apply.set_control(ctx, "posture", "full-auto", "claude")


NONCE = "b" * 64


def write_token(m: Machine, **fields: Any) -> Path:
    """The panel's confirmation: a file holding only the digest of a nonce that the panel hands to the child it starts."""
    m.env["NEXUS_SETTINGS_PANEL_NONCE"] = NONCE
    token = {"token_sha256": hashlib.sha256(NONCE.encode("ascii")).hexdigest(), "action": "set", "control": "posture", "value": "full-auto", "tool": "claude", "issued_at": 990.0, **fields}
    path = m.home / ".nexus-hub" / "settings-panel-token.json"
    path.parent.mkdir(exist_ok=True)
    path.write_text(json.dumps(token), encoding="utf-8")
    if os.name != "nt":
        path.chmod(0o600)
    return path


def test_a_weakening_write_without_a_tty_is_refused_with_nothing_written(machine: Machine, catalog: dict[str, Any]) -> None:
    before = seed(machine)

    with pytest.raises(apply.Refusal, match="needs a person"):
        full_auto(machine.context(catalog))

    assert files(machine) == before and not (machine.home / ".nexus-hub").exists()


def test_a_tty_and_the_word_yes_allow_it_and_print_the_keys_and_the_cannot_remove_list(machine: Machine, catalog: dict[str, Any]) -> None:
    seed(machine)
    ctx = person(machine.context(catalog))

    doc = full_auto(ctx)

    assert claude(machine)["permissions"]["defaultMode"] == "bypassPermissions" and doc["confirmation"]["kind"] == "confirmed"
    said = "\n".join(machine.said)
    assert "permissions.defaultMode" in said and "bypassPermissions" in said and "Still prompts or blocks (Claude Code)" in said
    assert "deny blocks in every mode" in said


@pytest.mark.parametrize("answer", ["no", "", "y", "YES", "yes please"])
def test_anything_but_exactly_yes_refuses(machine: Machine, catalog: dict[str, Any], answer: str) -> None:
    before = seed(machine)

    with pytest.raises(apply.Refusal, match="not 'yes'"):
        full_auto(person(machine.context(catalog), answer))

    assert files(machine) == before


def test_an_undetectable_tty_counts_as_no_person(monkeypatch: pytest.MonkeyPatch) -> None:
    class Closed:
        def isatty(self) -> bool:
            raise ValueError("I/O operation on closed file")

    monkeypatch.setattr(sys, "stdin", Closed())
    assert apply._is_tty() is False
    monkeypatch.setattr(sys, "stdin", io.StringIO())
    assert apply._is_tty() is False


@pytest.mark.parametrize("marker", ["CLAUDECODE", "CLAUDE_CODE_CHILD_SESSION"])
def test_an_agent_marker_refuses_even_with_a_tty_and_no_flag_bypasses_it(machine: Machine, catalog: dict[str, Any], marker: str) -> None:
    before = seed(machine)
    machine.env[marker] = "1"

    with pytest.raises(apply.Refusal, match=marker):
        full_auto(person(machine.context(catalog)))

    assert files(machine) == before
    for flag in ("--confirm-full-auto", "--yes", "--force", "--i-am-human"):
        done = _cli(machine, ["set", "posture", "full-auto", flag])
        assert done.returncode == 2 and "unrecognized arguments" in done.stderr


def test_a_marker_from_any_tool_counts_not_only_the_target_tools(machine: Machine, catalog: dict[str, Any]) -> None:
    seed(machine)
    machine.env["CLAUDECODE"] = "1"

    with pytest.raises(apply.Refusal):
        apply.set_control(person(machine.context(catalog)), "posture", "full-auto", "codex")


def test_a_non_weakening_write_ignores_the_agent_marker(machine: Machine, catalog: dict[str, Any]) -> None:
    seed(machine)
    machine.env["CLAUDECODE"] = "1"

    doc = apply.set_control(machine.context(catalog), "posture", "ask")

    assert doc["exit_code"] == 0


def test_a_fresh_matching_panel_token_is_consumed_once_and_allows_the_write(machine: Machine, catalog: dict[str, Any]) -> None:
    seed(machine)
    token = write_token(machine)

    doc = full_auto(machine.context(catalog))

    assert doc["exit_code"] == 0 and not token.exists()
    assert claude(machine)["permissions"]["defaultMode"] == "bypassPermissions"
    with pytest.raises(apply.Refusal):  # the replay: the token file is gone
        full_auto(machine.context(catalog))


@pytest.mark.parametrize(
    "fields",
    [{"issued_at": 960.0}, {"issued_at": 1010.0}, {"value": "accept-edits"}, {"control": "model"}, {"tool": "codex"}, {"tool": None}, {"action": "remove-override"},
     {"token_sha256": "0" * 64}, {"token_sha256": "short"}, {"issued_at": "now"}, {"issued_at": True}],
    ids=["expired", "future", "other-value", "other-control", "other-tool", "no-tool", "other-action", "wrong-digest", "short-digest", "string-time", "bool-time"],
)
def test_an_expired_or_mismatched_token_is_refused_and_still_consumed(machine: Machine, catalog: dict[str, Any], fields: dict[str, Any]) -> None:
    before = seed(machine)
    token = write_token(machine, **fields)

    with pytest.raises(apply.Refusal):
        full_auto(machine.context(catalog))

    assert files(machine) == before and not token.exists()


def test_a_token_does_not_beat_an_agent_marker(machine: Machine, catalog: dict[str, Any]) -> None:
    before = seed(machine)
    machine.env["CLAUDECODE"] = "1"
    write_token(machine)

    with pytest.raises(apply.Refusal, match="CLAUDECODE"):
        full_auto(machine.context(catalog))

    assert files(machine) == before


@pytest.mark.skipif(os.name == "nt", reason="POSIX owner and mode check")
def test_a_token_that_other_users_can_read_is_refused(machine: Machine, catalog: dict[str, Any]) -> None:
    before = seed(machine)
    write_token(machine).chmod(0o644)

    with pytest.raises(apply.Refusal):
        full_auto(machine.context(catalog))

    assert files(machine) == before


def test_a_garbled_token_is_refused_and_removed(machine: Machine, catalog: dict[str, Any]) -> None:
    seed(machine)
    path = machine.home / ".nexus-hub" / "settings-panel-token.json"
    path.parent.mkdir()
    path.write_text("{garbled", encoding="utf-8")

    with pytest.raises(apply.Refusal):
        full_auto(machine.context(catalog))

    assert not path.exists()


def test_the_token_for_a_remove_override_names_the_action(machine: Machine, admitted: dict[str, Any]) -> None:
    seed(machine)
    write_token(machine, action="remove-override", control="effort", value=None, tool="claude")

    doc = apply.remove_override(machine.context(admitted), "effort", "claude")

    assert doc["results"][0]["status"] == "removed"


# --- owned-keys --------------------------------------------------------------


def test_owned_keys_lists_the_record_per_catalog_file_for_the_installers(machine: Machine, admitted: dict[str, Any]) -> None:
    seed(machine)
    ctx = person(machine.context(admitted))
    apply.set_control(ctx, "effort", "high", "claude")
    apply.set_control(ctx, "posture", "ask", "codex")
    apply.remove_override(ctx, "posture", "copilot-cli")

    owned = apply.owned_keys(ctx)

    claude_paths = owned["files"]["~/.claude/settings.json"]
    assert ["effortLevel"] in claude_paths and ["modelSettings", "claude-opus-5-5", "effortLevel"] in claude_paths
    assert owned["files"]["~/.codex/config.toml"] == [["approval_policy"], ["sandbox_mode"]]
    assert owned["files"]["~/.copilot/settings.json"] == [["permissions", "disableBypassPermissionsMode"]]


def test_owned_keys_is_empty_without_a_record_and_a_reset_clears_it(machine: Machine, catalog: dict[str, Any]) -> None:
    ctx = machine.context(catalog)
    assert apply.owned_keys(ctx)["files"] == {}
    seed(machine)
    apply.set_control(ctx, "model", "claude-opus-5-5", "claude")
    assert apply.owned_keys(ctx)["files"] == {"~/.claude/settings.json": [["model"]]}
    apply.reset_control(ctx, "model", "claude")
    assert apply.owned_keys(ctx)["files"] == {}


def test_owned_keys_fails_on_an_unreadable_record(machine: Machine, catalog: dict[str, Any]) -> None:
    path = machine.home / ".nexus-hub" / "settings-control.json"
    path.parent.mkdir()
    path.write_text("nope", encoding="utf-8")

    with pytest.raises(apply.RecordError):
        apply.owned_keys(machine.context(catalog))


# --- CLI exit codes ----------------------------------------------------------


def _cli(machine: Machine, args: list[str]) -> Any:
    import subprocess

    root = Path(__file__).resolve().parents[2]
    env = {**{k: v for k, v in os.environ.items() if not k.upper().startswith(("CLAUDE", "NEXUS", "CODEX"))}, "HOME": str(machine.home), "USERPROFILE": str(machine.home)}
    return subprocess.run(
        [sys.executable, "-B", str(root / "scripts" / "nexus_hub_cli.py"), "settings", *args],
        capture_output=True, text=True, stdin=subprocess.DEVNULL, timeout=120, check=False,
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0), env=env,
    )


def test_claude_attribution_is_refused_as_not_settable_until_the_commit_probe_is_completed(machine: Machine, catalog: dict[str, Any]) -> None:
    before = seed(machine)

    doc = apply.set_control(machine.context(catalog), "attribution", "off", "claude")

    assert doc["exit_code"] == 4 and files(machine) == before
    assert {r["status"] for r in doc["results"]} == {"not-settable"}
    assert "USD 0.7662" in next(w for w in catalog["writes"] if w["id"] == "claude.attribution")["not_settable_reason"]
