"""Registration of the v4.13.2 completion gate and approval capture on every platform.

The gate must reach each platform with a VERIFIED continuation lever on that
platform's documented event (docs/policy/completion-levers.json), and approval
capture must reach each documented prompt-submit event. Both ride
catalog/hooks/settings.json through the native adapters, except Cursor and
Antigravity, which build their own hooks.json. Those two now merge only
Nexus-Hub's entries into a user-edited file and prune only those on teardown.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.lib.integrations._cascade_hook_compat import translate_child_result
from scripts.lib.integrations._codex_native import build_hook_entries
from scripts.lib.integrations._copilot_native import build_copilot_hooks
from scripts.lib.integrations._hooks_common import script_basename
from scripts.lib.integrations._kimi_native import build_kimi_hooks
from scripts.lib.integrations._settings_hooks import (
    GEMINI_CLI_SPEC,
    QWEN_SPEC,
    build_settings_hooks,
)
from scripts.lib.integrations.antigravity import Antigravity20Integration
from scripts.lib.integrations.cursor import CursorIntegration

REPO = Path(__file__).resolve().parents[2]
HOOKS = REPO / "catalog" / "hooks"
SETTINGS = json.loads((HOOKS / "settings.json").read_text(encoding="utf-8"))
BASE = "/home/u/.x/hooks"


def _scripts_on(events: dict, event: str) -> list[str]:
    found = []
    for group in events.get(event, []):
        for handler in group.get("hooks", []):
            for field in ("command", "commandWindows", "bash", "powershell"):
                if isinstance(handler.get(field), str):
                    found.append(handler[field])
    return found


def test_catalog_registers_both_hooks() -> None:
    stop = [h["command"] for g in SETTINGS["hooks"]["Stop"] for h in g["hooks"]]
    prompt = [h["command"] for g in SETTINGS["hooks"]["UserPromptSubmit"] for h in g["hooks"]]
    assert "bash .claude/hooks/completion-gate.sh" in stop
    assert "bash .claude/hooks/approval-capture.sh" in prompt
    assert {script_basename(c) for c in stop} >= {"completion-gate.sh"}


def test_codex_registers_gate_on_stop_and_capture_on_prompt() -> None:
    events, scripts, _ = build_hook_entries(SETTINGS, HOOKS, BASE)
    assert any("completion-gate" in c for c in _scripts_on(events, "Stop"))
    assert any("approval-capture" in c for c in _scripts_on(events, "UserPromptSubmit"))
    assert {"completion-gate.sh", "completion-gate.ps1"} <= scripts


@pytest.mark.parametrize(("spec", "stop_event"), [(GEMINI_CLI_SPEC, "AfterAgent"), (QWEN_SPEC, "Stop")])
@pytest.mark.parametrize("windows", [False, True])
def test_settings_platforms_register_gate_on_their_turn_end_event(spec, stop_event: str, windows: bool) -> None:
    events, _, _ = build_settings_hooks(spec, SETTINGS, HOOKS, BASE, windows)
    commands = _scripts_on(events, stop_event)
    suffix = "completion-gate.ps1" if windows else "completion-gate.sh"
    assert any(suffix in c for c in commands), commands


@pytest.mark.parametrize("windows", [False, True])
def test_kimi_registers_gate_on_stop(windows: bool) -> None:
    entries, _, _ = build_kimi_hooks(SETTINGS, HOOKS, BASE, windows)
    suffix = "completion-gate.ps1" if windows else "completion-gate.sh"
    stop = [e["command"] for e in entries if e["event"] == "Stop"]
    assert any(suffix in c for c in stop), stop
    assert any("approval-capture" in e["command"] for e in entries if e["event"] == "UserPromptSubmit")


def test_copilot_routes_the_gate_through_the_bridge_on_stop() -> None:
    config, _, _ = build_copilot_hooks(SETTINGS, HOOKS, BASE)
    blob = json.dumps(config["hooks"])
    assert "copilot Stop --handler completion-gate.sh" in blob
    assert "--handler approval-capture.sh" in blob


@pytest.mark.parametrize(
    ("host", "expected"),
    [
        ("antigravity", {"decision": "continue"}),
        ("copilot", {"decision": "block"}),
    ],
)
@pytest.mark.parametrize("via", ["json", "exit-2"])
def test_bridge_translates_a_stop_block(host: str, expected: dict, via: str) -> None:
    if via == "json":
        kwargs = {"stdout": json.dumps({"decision": "block", "reason": "R ids"}), "stderr": "", "returncode": 0}
    else:
        kwargs = {"stdout": "", "stderr": "R ids", "returncode": 2}
    output, code = translate_child_result(host, "Stop", **kwargs)
    assert code == 0
    assert output["decision"] == expected["decision"]
    assert output["reason"] == "R ids"
    if host == "copilot":
        assert output["hookSpecificOutput"] == {"hookEventName": "Stop", "decision": "block", "reason": "R ids"}


@pytest.mark.parametrize("host", ["antigravity", "copilot"])
def test_bridge_lets_an_allowed_or_failed_stop_end(host: str) -> None:
    assert translate_child_result(host, "Stop", stdout="", stderr="", returncode=0) == ({}, 0)
    assert translate_child_result(host, "Stop", stdout="", stderr="boom", returncode=1) == ({}, 0)


# ----- Cursor hooks.json merge ----------------------------------------------------

USER_STOP = {"command": "echo user-stop-hook"}


def _cursor_write(ctx):
    cursor = CursorIntegration()
    root = ctx.target_root / ".cursor"
    hooks_dst = root / "hooks"
    hooks_dst.mkdir(parents=True, exist_ok=True)
    return cursor, root, cursor._write_hooks_json(root, hooks_dst, ctx, "workspace")


def test_cursor_registers_gate_and_capture(install_ctx) -> None:
    _, root, _ = _cursor_write(install_ctx)
    data = json.loads((root / "hooks.json").read_text(encoding="utf-8"))
    assert any("completion-gate" in e["command"] for e in data["hooks"]["stop"])
    assert any("approval-capture" in e["command"] for e in data["hooks"]["beforeSubmitPrompt"])


def test_cursor_merge_keeps_user_entries_and_is_idempotent(install_ctx) -> None:
    root = install_ctx.target_root / ".cursor"
    root.mkdir(parents=True)
    (root / "hooks.json").write_text(json.dumps({"version": 1, "hooks": {"stop": [USER_STOP]}}), encoding="utf-8")
    _, _, first = _cursor_write(install_ctx)
    once = (root / "hooks.json").read_bytes()
    _, _, second = _cursor_write(install_ctx)
    data = json.loads(once)
    assert first.action == "updated"
    assert second.action == "unchanged"
    assert (root / "hooks.json").read_bytes() == once
    assert USER_STOP in data["hooks"]["stop"]
    assert any("completion-gate" in e["command"] for e in data["hooks"]["stop"])
    assert (root / "hooks.json.nexus-hub.bak").exists()


def test_cursor_teardown_leaves_the_user_hook_byte_identical(install_ctx) -> None:
    root = install_ctx.target_root / ".cursor"
    root.mkdir(parents=True)
    original = {"version": 1, "hooks": {"stop": [USER_STOP]}}
    (root / "hooks.json").write_text(json.dumps(original, indent=2) + "\n", encoding="utf-8")
    before = (root / "hooks.json").read_bytes()
    cursor, _, _ = _cursor_write(install_ctx)
    cursor.teardown(install_ctx)
    assert (root / "hooks.json").read_bytes() == before


def test_cursor_malformed_hooks_json_is_kept(install_ctx) -> None:
    root = install_ctx.target_root / ".cursor"
    root.mkdir(parents=True)
    (root / "hooks.json").write_text("{not json", encoding="utf-8")
    _, _, action = _cursor_write(install_ctx)
    assert action.action == "kept"
    assert (root / "hooks.json").read_text(encoding="utf-8") == "{not json"


# ----- Antigravity hooks.json merge -----------------------------------------------

USER_SET = {"my-hooks": {"enabled": True, "Stop": [{"hooks": [{"command": "echo mine"}]}]}}


def _antigravity_write(ctx):
    integration = Antigravity20Integration()
    parent = ctx.target_root / ".agents"
    hooks_dst = parent / "hooks"
    hooks_dst.mkdir(parents=True, exist_ok=True)
    return integration, parent, integration._write_hooks_json(parent, hooks_dst, ctx, "workspace")


def test_antigravity_registers_gate_on_stop_through_the_bridge(install_ctx) -> None:
    _, parent, _ = _antigravity_write(install_ctx)
    data = json.loads((parent / "hooks.json").read_text(encoding="utf-8"))
    stop = data["nexus-hub-guardrails"]["Stop"][0]["hooks"][0]["command"]
    assert "antigravity Stop --" in stop
    assert "completion-gate" in stop


def test_antigravity_merge_and_teardown_preserve_user_sets(install_ctx) -> None:
    parent = install_ctx.target_root / ".agents"
    parent.mkdir(parents=True)
    (parent / "hooks.json").write_text(json.dumps(USER_SET, indent=2) + "\n", encoding="utf-8")
    before = (parent / "hooks.json").read_bytes()
    integration, _, action = _antigravity_write(install_ctx)
    merged = json.loads((parent / "hooks.json").read_text(encoding="utf-8"))
    assert action.action == "updated"
    assert merged["my-hooks"] == USER_SET["my-hooks"]
    assert "nexus-hub-guardrails" in merged
    integration.teardown(install_ctx)
    assert json.loads((parent / "hooks.json").read_text(encoding="utf-8")) == USER_SET
    assert before  # the original bytes were captured before any change


def test_windsurf_does_not_register_the_inert_gate() -> None:
    from scripts.lib.integrations import windsurf

    text = Path(windsurf.__file__).read_text(encoding="utf-8")
    assert "completion-gate" not in text, "Cascade's post_cascade_response cannot refuse a stop"
