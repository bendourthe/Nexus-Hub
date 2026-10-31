"""Hardening of the write side found by the Phase 6 deep pass (v4.14.6 fix cycle 1).

Each test pins one defect: the human-presence refusal on every `remove-override` and on a `reset` that would
lower a safety barrier, the panel confirmation that no longer carries a usable secret on disk, an ownership
record that survives concurrent commands, and the robustness of `set`, `reset`, and `owned-keys` on unusual files.
Every test works inside `tmp_path`; no real tool configuration is read or written.
"""
from __future__ import annotations

import hashlib
import json
import os
import stat
import subprocess
import sys
import time
import tomllib
from pathlib import Path
from typing import Any

import pytest

from scripts.lib.settings_control import apply, readers, writers
from tests.settings_control.conftest import CLAUDE_IDS, Machine

NOWIN = getattr(subprocess, "CREATE_NO_WINDOW", 0)
ROOT = Path(__file__).resolve().parents[2]
NONCE = "c" * 64


def person(ctx: apply.Context, answer: str = "yes") -> apply.Context:
    ctx.is_tty = lambda: True
    ctx.ask = lambda prompt: answer
    return ctx


def claude(m: Machine) -> dict[str, Any]:
    return json.loads(m.path("claude-user").read_text(encoding="utf-8"))


def record(m: Machine) -> dict[str, Any]:
    return json.loads((m.home / ".nexus-hub" / "settings-control.json").read_text(encoding="utf-8"))


def snapshot(m: Machine) -> dict[str, bytes]:
    out: dict[str, bytes] = {}
    for base in (m.home,):
        for path in sorted(base.rglob("*")):
            if path.is_file() and path.name not in {"settings-control.lock", "settings-control.json"}:
                out[str(path.relative_to(base))] = path.read_bytes()
    return out


def token(m: Machine, **fields: Any) -> Path:
    m.env["NEXUS_SETTINGS_PANEL_NONCE"] = NONCE
    body = {"token_sha256": hashlib.sha256(NONCE.encode("ascii")).hexdigest(), "action": "set", "control": "posture", "value": "full-auto", "tool": "claude", "issued_at": 990.0, **fields}
    path = m.home / ".nexus-hub" / "settings-panel-token.json"
    path.parent.mkdir(exist_ok=True)
    path.write_text(json.dumps(body), encoding="utf-8")
    if os.name != "nt":
        path.chmod(0o600)
    return path


# --- Every remove-override needs a person and never an agent ----------------------


@pytest.mark.parametrize(("control", "tool"), [("effort", "claude"), ("posture", "copilot-cli")], ids=["not-weakening", "weakening"])
def test_every_remove_override_is_refused_inside_an_agent_session(machine: Machine, admitted: dict[str, Any], control: str, tool: str) -> None:
    machine.put("claude-user", '{"env": {"CLAUDE_CODE_EFFORT_LEVEL": "high"}}\n')
    machine.put("copilot-user", '{"permissions": {"disableBypassPermissionsMode": "disable"}}\n')
    machine.env["CLAUDECODE"] = "1"
    before = snapshot(machine)

    with pytest.raises(apply.Refusal, match="CLAUDECODE"):
        apply.remove_override(person(machine.context(admitted)), control, tool)  # a terminal does not help

    token(machine, action="remove-override", control=control, value=None, tool=tool)
    with pytest.raises(apply.Refusal, match="CLAUDECODE"):
        apply.remove_override(machine.context(admitted), control, tool)  # nor does a panel confirmation

    assert {k: v for k, v in snapshot(machine).items() if "token" not in k} == {k: v for k, v in before.items() if "token" not in k}


def test_a_dry_run_remove_override_needs_nobody(machine: Machine, admitted: dict[str, Any]) -> None:
    machine.put("claude-user", '{"env": {"CLAUDE_CODE_EFFORT_LEVEL": "high"}}\n')
    machine.env["CLAUDECODE"] = "1"

    doc = apply.remove_override(machine.context(admitted), "effort", "claude", dry_run=True)

    assert doc["results"][0]["status"] == "would-remove"


# --- reset restores a weaker value only for a person ------------------------------


def _weaker_before(m: Machine) -> dict[str, bytes]:
    """A person had Full auto (and a git-guardrails switch off), then chose safer values through Nexus-Hub."""
    m.put("claude-user", '{\n  "permissions": {\n    "defaultMode": "bypassPermissions"\n  }\n}\n')
    m.put("nexus-guardrails", '{"block_git_bypass_flags": false}\n')
    return snapshot(m)


@pytest.mark.parametrize(("control", "value", "tool"), [("posture", "ask", "claude"), ("git_guardrails", "on", None)])
def test_a_reset_that_would_lower_a_safety_barrier_is_refused_in_an_agent_session(machine: Machine, catalog: dict[str, Any], control: str, value: str, tool: str | None) -> None:
    _weaker_before(machine)
    apply.set_control(machine.context(catalog), control, value, tool)
    safer = snapshot(machine)
    machine.env["CLAUDECODE"] = "1"

    with pytest.raises(apply.Refusal, match="CLAUDECODE"):
        apply.reset_control(person(machine.context(catalog)), control, tool)

    assert snapshot(machine) == safer
    assert len(record(machine)["entries"]) >= 1  # nothing was dropped


@pytest.mark.parametrize(("control", "value", "tool"), [("posture", "ask", "claude"), ("git_guardrails", "on", None)])
def test_such_a_reset_needs_a_terminal_and_yes_or_a_panel_confirmation(machine: Machine, catalog: dict[str, Any], control: str, value: str, tool: str | None) -> None:
    original = _weaker_before(machine)
    apply.set_control(machine.context(catalog), control, value, tool)
    safer = snapshot(machine)

    with pytest.raises(apply.Refusal, match="needs a person"):
        apply.reset_control(machine.context(catalog), control, tool)
    with pytest.raises(apply.Refusal, match="not 'yes'"):
        apply.reset_control(person(machine.context(catalog), "no"), control, tool)
    assert snapshot(machine) == safer

    token(machine, action="reset", control=control, value=None, tool=tool)
    doc = apply.reset_control(machine.context(catalog), control, tool)
    assert doc["exit_code"] == 0 and doc["confirmation"] == {"required": True, "kind": "confirmed"}
    assert snapshot(machine) == original


def test_such_a_reset_runs_in_a_terminal_after_yes(machine: Machine, catalog: dict[str, Any]) -> None:
    original = _weaker_before(machine)
    apply.set_control(machine.context(catalog), "posture", "ask", "claude")

    doc = apply.reset_control(person(machine.context(catalog)), "posture", "claude")

    assert doc["confirmation"]["kind"] == "confirmed" and snapshot(machine) == original
    assert "bypassPermissions" in "\n".join(machine.said)  # the printout names what comes back


def test_a_reset_back_to_a_safe_value_stays_open_to_an_agent(machine: Machine, catalog: dict[str, Any]) -> None:
    path = machine.put("claude-user", '{"model": "sonnet"}\n')
    before = path.read_bytes()
    apply.set_control(person(machine.context(catalog)), "posture", "full-auto", "claude")
    machine.env["CLAUDECODE"] = "1"

    doc = apply.reset_control(machine.context(catalog), "posture", "claude")

    assert doc["exit_code"] == 0 and doc["confirmation"] == {"required": False, "kind": None}
    assert path.read_bytes() == before


def test_a_dry_run_reset_of_a_weaker_value_needs_nobody_and_writes_nothing(machine: Machine, catalog: dict[str, Any]) -> None:
    _weaker_before(machine)
    apply.set_control(machine.context(catalog), "posture", "ask", "claude")
    safer = snapshot(machine)
    machine.env["CLAUDECODE"] = "1"

    doc = apply.reset_control(machine.context(catalog), "posture", "claude", dry_run=True)

    assert doc["confirmation"] == {"required": True, "kind": None} and doc["results"][0]["status"] == "would-restore"
    assert snapshot(machine) == safer


# --- The panel confirmation ----------------------------------------------------------


def test_the_confirmation_file_holds_no_usable_secret(machine: Machine, catalog: dict[str, Any]) -> None:
    machine.put("claude-user", "{}\n")
    path = token(machine)
    digest = json.loads(path.read_text(encoding="utf-8"))["token_sha256"]
    machine.env["NEXUS_SETTINGS_PANEL_NONCE"] = digest  # whoever only reads the file can offer nothing but the digest

    with pytest.raises(apply.Refusal, match="needs a person"):
        apply.set_control(machine.context(catalog), "posture", "full-auto", "claude")

    assert not path.exists()


@pytest.mark.parametrize("nonce", [None, "", "short", "d" * 64], ids=["absent", "empty", "short", "wrong"])
def test_a_planted_file_without_the_nonce_of_its_own_process_is_refused_and_consumed(machine: Machine, catalog: dict[str, Any], nonce: str | None) -> None:
    machine.put("claude-user", "{}\n")
    before = snapshot(machine)
    path = token(machine)
    if nonce is None:
        machine.env.pop("NEXUS_SETTINGS_PANEL_NONCE")
    else:
        machine.env["NEXUS_SETTINGS_PANEL_NONCE"] = nonce

    with pytest.raises(apply.Refusal):
        apply.set_control(machine.context(catalog), "posture", "full-auto", "claude")

    assert not path.exists() and {k: v for k, v in snapshot(machine).items() if "token" not in k} == before


def test_the_old_token_format_with_a_plain_secret_is_not_honored(machine: Machine, catalog: dict[str, Any]) -> None:
    machine.put("claude-user", "{}\n")
    path = token(machine)
    body = json.loads(path.read_text(encoding="utf-8"))
    body.pop("token_sha256")
    body["token"] = "a" * 32
    path.write_text(json.dumps(body), encoding="utf-8")

    with pytest.raises(apply.Refusal):
        apply.set_control(machine.context(catalog), "posture", "full-auto", "claude")


def test_a_reset_confirmation_names_the_action(machine: Machine, catalog: dict[str, Any]) -> None:
    _weaker_before(machine)
    apply.set_control(machine.context(catalog), "posture", "ask", "claude")
    token(machine, action="set")  # a confirmation for a set does not confirm a reset

    with pytest.raises(apply.Refusal):
        apply.reset_control(machine.context(catalog), "posture", "claude")


# --- The ownership record under concurrent commands -----------------------------------

WORKER = """
import json, sys, time
from pathlib import Path
sys.path.insert(0, sys.argv[1])
from scripts.lib.settings_control import apply, catalog
root, home, go, control, value, tool = sys.argv[1:7]
Path(go + "." + control + "." + tool).write_text("ready", encoding="utf-8")
ctx = apply.Context(
    catalog.load_catalog(), home=Path(home), env={"PATH": ""}, project=Path(home).parent / "project", platform="linux",
    claude_ids=json.loads(sys.argv[7]), which=lambda command: "/stub/" + command, version_runner=lambda argv: ("2.1.283", None),
    is_tty=lambda: False, ask=lambda prompt: "", say=lambda text: None,
)
while not Path(go).exists():
    time.sleep(0.002)
doc = apply.set_control(ctx, control, value, None if tool == "-" else tool)
print(json.dumps({"exit": doc["exit_code"], "statuses": sorted({r["status"] for r in doc["results"]})}))
"""
JOBS = [
    ("effort", "high", "-"), ("model", "claude-opus-5-5", "claude"), ("model", "gpt-6.2", "codex"),
    ("posture", "ask", "-"), ("attribution", "off", "-"), ("git_guardrails", "on", "-"),
]


@pytest.mark.parametrize("trial", range(3))
def test_concurrent_commands_keep_every_record_entry_and_every_value(machine: Machine, catalog: dict[str, Any], trial: int) -> None:
    machine.put("claude-user", '{\n  "model": "sonnet",\n  "env": {"KEEP": "yes"}\n}\n')
    machine.put("codex-user", 'model = "gpt-6.1-sol"\n')
    original = snapshot(machine)
    go = machine.home.parent / "go"
    workers = [
        subprocess.Popen(
            [sys.executable, "-B", "-c", WORKER, str(ROOT), str(machine.home), str(go), control, value, tool, json.dumps(CLAUDE_IDS)],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.DEVNULL, text=True, creationflags=NOWIN,
        )
        for control, value, tool in JOBS
    ]
    deadline = time.monotonic() + 90
    while len(list(go.parent.glob("go.*"))) < len(JOBS) and time.monotonic() < deadline:
        time.sleep(0.05)  # every worker is waiting at the gate
    go.write_text("go", encoding="utf-8")
    outcomes = []
    for worker in workers:
        out, err = worker.communicate(timeout=180)
        assert worker.returncode == 0, err
        outcomes.append(json.loads(out))

    assert [o["exit"] for o in outcomes] == [0] * len(JOBS), outcomes
    held = {tuple(e["key_path"]) for e in record(machine)["entries"]}
    for key in [("model",), ("effortLevel",), ("permissions", "defaultMode"), ("attribution", "commit"), ("attribution", "pr"), ("block_git_bypass_flags",), ("model_reasoning_effort",), ("approval_policy",)]:
        assert key in held, f"{key} was written but is not in the record"
    data = claude(machine)
    assert data["permissions"]["defaultMode"] == "default" and data["effortLevel"] == "high" and data["attribution"] == {"commit": "", "pr": ""}
    assert data["env"] == {"KEEP": "yes"}
    for control in ("effort", "posture", "attribution", "git_guardrails"):
        apply.reset_control(machine.context(catalog), control)
    apply.reset_control(machine.context(catalog), "model", "claude")
    apply.reset_control(machine.context(catalog), "model", "codex")
    assert snapshot(machine) == original and record(machine)["entries"] == []


def test_a_refused_write_removes_only_its_own_entries_from_a_record_another_command_changed(machine: Machine, catalog: dict[str, Any], monkeypatch: pytest.MonkeyPatch) -> None:
    machine.put("claude-user", '{"model": "sonnet"}\n')
    machine.put("codex-user", 'model = "gpt-6.1-sol"\n')
    real_commit = writers.commit
    state = {"calls": 0}

    def commit(plan: writers.Plan) -> bool:
        state["calls"] += 1
        if state["calls"] == 2:  # the second file group is refused after the first one was recorded
            raise writers.WriterRefusal("refused for the test")
        return real_commit(plan)

    monkeypatch.setattr(writers, "commit", commit)
    doc = apply.set_control(machine.context(catalog), "effort", "high")

    held = {(e["tool"], tuple(e["key_path"])) for e in record(machine)["entries"]}
    assert ("claude", ("effortLevel",)) in held and not any(tool == "codex" for tool, _ in held)
    assert doc["exit_code"] == 1


def test_a_second_command_waits_for_the_lock_and_gives_up_with_a_clear_message(machine: Machine, catalog: dict[str, Any], monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(apply, "LOCK_SECONDS", 0.2)
    machine.put("claude-user", "{}\n")
    ctx = machine.context(catalog)

    with apply.record_lock(machine.home):
        with pytest.raises(apply.RecordError, match="another nexus-hub settings command"):
            apply.set_control(ctx, "model", "claude-opus-5-5", "claude")

    assert apply.set_control(ctx, "model", "claude-opus-5-5", "claude")["exit_code"] == 0


# --- Robustness on unusual files and values --------------------------------------------


def test_a_read_only_settings_file_is_refused_cleanly_with_no_leftovers_and_no_record_entry(machine: Machine, catalog: dict[str, Any]) -> None:
    path = machine.put("claude-user", '{"model": "sonnet"}\n')
    before = path.read_bytes()
    os.chmod(path, stat.S_IREAD)
    try:
        doc = apply.set_control(machine.context(catalog), "model", "claude-opus-5-5", "claude")
    finally:
        os.chmod(path, stat.S_IREAD | stat.S_IWRITE)

    assert doc["exit_code"] == 1 and doc["results"][0]["status"] == "refused" and "read-only" in doc["results"][0]["detail"]
    assert path.read_bytes() == before
    assert sorted(p.name for p in path.parent.iterdir()) == ["settings.json"]
    assert not (machine.home / ".nexus-hub" / "settings-control.json").exists() or record(machine)["entries"] == []


def test_a_toml_file_holding_only_comments_after_a_reset_survives(machine: Machine, catalog: dict[str, Any]) -> None:
    apply.set_control(machine.context(catalog), "model", "gpt-6.2", "codex")
    path = machine.path("codex-user")
    path.write_text("# my notes about this machine\n" + path.read_text(encoding="utf-8"), encoding="utf-8")

    doc = apply.reset_control(machine.context(catalog), "model", "codex")

    assert doc["results"][0]["status"] == "restored"
    assert path.read_text(encoding="utf-8").strip() == "# my notes about this machine"


def test_a_created_toml_file_is_still_deleted_when_nothing_else_is_in_it(machine: Machine, catalog: dict[str, Any]) -> None:
    apply.set_control(machine.context(catalog), "model", "gpt-6.2", "codex")

    apply.reset_control(machine.context(catalog), "model", "codex")

    assert not machine.path("codex-user").exists()


def test_deeply_nested_json_is_refused_without_a_traceback(machine: Machine, catalog: dict[str, Any]) -> None:
    deep = '{"a":' * 5000 + "1" + "}" * 5000
    path = machine.put("claude-user", deep)

    with pytest.raises(writers.WriterRefusal, match="nested too deeply"):
        writers.load(path, "json")
    assert readers.read_file("claude-user", path, "~/.claude/settings.json").status == "invalid"
    doc = apply.set_control(machine.context(catalog), "model", "claude-opus-5-5", "claude")

    assert doc["results"][0]["status"] == "refused" and path.read_text(encoding="utf-8") == deep


def test_toml_dates_are_read_and_a_write_around_them_leaves_them_alone(machine: Machine, catalog: dict[str, Any]) -> None:
    text = 'since = 1979-05-27T07:32:00Z\nclock = 07:32:00\nmodel = "gpt-6.1-sol"\n'
    path = machine.put("codex-user", text)

    read = readers.read_file("codex-user", path, "~/.codex/config.toml")
    assert read.status == "ok" and read.data["model"] == "gpt-6.1-sol"
    doc = apply.set_control(machine.context(catalog), "model", "gpt-6.2", "codex")
    assert doc["results"][0]["status"] == "written"
    apply.reset_control(machine.context(catalog), "model", "codex")

    assert path.read_text(encoding="utf-8") == text


def test_a_forged_record_entry_for_a_row_that_is_not_settable_is_ignored(machine: Machine, catalog: dict[str, Any]) -> None:
    copilot = machine.put("copilot-user", '{"defaultPermissionMode": "ask"}\n')
    before = copilot.read_bytes()
    forged = {
        "kind": "file", "tool": "copilot-cli", "file": "~/.copilot/settings.json", "key_path": ["defaultPermissionMode"],
        "previous": {"present": True, "value": "allow-all"}, "new": {"present": True, "value": "ask"}, "created_depth": 1, "file_created": False, "at": "2026-01-01T00:00:00Z",
    }
    record_file = machine.home / ".nexus-hub" / "settings-control.json"
    record_file.parent.mkdir()
    record_file.write_text(json.dumps({"schema_version": 1, "entries": [forged]}), encoding="utf-8")

    doc = apply.reset_control(person(machine.context(catalog)), "posture", "copilot-cli")

    assert doc["results"] == [] and any("matches no catalog write" in note for note in doc["ignored"])
    assert copilot.read_bytes() == before
    assert apply.owned_keys(machine.context(catalog))["files"] == {}


@pytest.mark.parametrize("text", ["claude-opus-5-5\n", "a\n", "x\r"])
def test_a_trailing_newline_is_not_part_of_a_model_id_or_a_key_segment(text: str) -> None:
    assert apply.MODEL_ID.match(text) is None
    assert writers.SEGMENT.match(text) is None
    with pytest.raises(writers.WriterRefusal):
        writers.check_segments(("model", text))


def test_a_record_entry_whose_model_id_ends_in_a_newline_is_ignored(machine: Machine, catalog: dict[str, Any]) -> None:
    entry = {
        "kind": "file", "tool": "claude", "file": "~/.claude/settings.json", "key_path": ["modelSettings", "claude-opus-5-5\n", "effortLevel"],
        "previous": {"present": False}, "new": {"present": True, "value": "high"}, "created_depth": 1, "file_created": False, "at": "2026-01-01T00:00:00Z",
    }

    assert apply.match_entry(catalog, entry) is None


@pytest.mark.parametrize("value", ["  ", "", " opus", "opus ", "-opus", "--model", "a\nb"])
def test_a_blank_padded_or_option_like_model_value_is_refused_before_anything_is_written(machine: Machine, catalog: dict[str, Any], value: str) -> None:
    machine.put("claude-user", "{}\n")
    before = snapshot(machine)

    with pytest.raises(apply.UsageError):
        apply.set_control(machine.context(catalog), "model", value, "claude")

    assert snapshot(machine) == before


def test_owned_keys_stays_fast_on_a_large_record(machine: Machine, catalog: dict[str, Any]) -> None:
    entries = [
        {
            "kind": "file", "tool": "claude", "file": "~/.claude/settings.json", "key_path": ["modelSettings", f"model-{i}", "effortLevel"],
            "previous": {"present": False}, "new": {"present": True, "value": "high"}, "created_depth": 1, "file_created": False, "at": "2026-01-01T00:00:00Z",
        }
        for i in range(40000)
    ]
    record_file = machine.home / ".nexus-hub" / "settings-control.json"
    record_file.parent.mkdir()
    record_file.write_text(json.dumps({"schema_version": 1, "entries": entries}), encoding="utf-8")

    started = time.monotonic()
    owned = apply.owned_keys(machine.context(catalog))

    assert len(owned["files"]["~/.claude/settings.json"]) == 40000
    assert time.monotonic() - started < 6.0
