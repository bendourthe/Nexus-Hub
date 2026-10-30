"""Approval capture is registered everywhere; the completion gate's Stop registration is not.

The completion gate (v4.13.2) was removed from the default install on 2026-10-28
(docs/decisions/implemented/tooling/2026-10-28-remove-completion-gate-stop-default.md):
it re-prompted at the end of every turn of a full /implement run, including turns
that were waiting on the user, CI, or an approval. Approval capture must still reach
each documented prompt-submit event. Both used to ride catalog/hooks/settings.json
through the native adapters, except Cursor and Antigravity, which build their own
hooks.json. Those two merge only Nexus-Hub's entries into a user-edited file and
prune only those on teardown, which is also how an older install loses its gate entry.
Every adapter below is exercised with an install that still carries the old entry.
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


def test_catalog_registers_capture_and_no_gate() -> None:
    every = [h["command"] for groups in SETTINGS["hooks"].values() for g in groups for h in g["hooks"]]
    prompt = [h["command"] for g in SETTINGS["hooks"]["UserPromptSubmit"] for h in g["hooks"]]
    assert "bash .claude/hooks/approval-capture.sh" in prompt
    assert "completion-gate.sh" not in {script_basename(c) for c in every}
    # The remaining Stop chain (usage guard, shell check) is untouched.
    stop = [h["command"] for g in SETTINGS["hooks"]["Stop"] for h in g["hooks"]]
    assert "python3 .claude/hooks/usage-guard.py" in stop


def test_codex_registers_capture_on_prompt_and_no_gate() -> None:
    events, scripts, _ = build_hook_entries(SETTINGS, HOOKS, BASE)
    assert not any("completion-gate" in c for event in events for c in _scripts_on(events, event))
    assert any("approval-capture" in c for c in _scripts_on(events, "UserPromptSubmit"))
    assert not {"completion-gate.sh", "completion-gate.ps1"} & scripts


@pytest.mark.parametrize(("spec", "stop_event"), [(GEMINI_CLI_SPEC, "AfterAgent"), (QWEN_SPEC, "Stop")])
@pytest.mark.parametrize("windows", [False, True])
def test_settings_platforms_register_no_gate_on_their_turn_end_event(spec, stop_event: str, windows: bool) -> None:
    events, scripts, _ = build_settings_hooks(spec, SETTINGS, HOOKS, BASE, windows)
    assert not any("completion-gate" in c for c in _scripts_on(events, stop_event))
    assert not any("completion-gate" in s for s in scripts)


@pytest.mark.parametrize("windows", [False, True])
def test_kimi_registers_capture_and_no_gate(windows: bool) -> None:
    entries, _, _ = build_kimi_hooks(SETTINGS, HOOKS, BASE, windows)
    assert not [e for e in entries if "completion-gate" in e["command"]]
    assert any("approval-capture" in e["command"] for e in entries if e["event"] == "UserPromptSubmit")


def test_copilot_registers_capture_and_no_gate() -> None:
    config, _, _ = build_copilot_hooks(SETTINGS, HOOKS, BASE)
    blob = json.dumps(config["hooks"])
    assert "completion-gate" not in blob
    assert "--handler approval-capture.sh" in blob


# ----- an install that still carries the old entry loses it on the next merge -----------

OLD_BASE = "/home/u/.nexus/hooks"
STALE_STOP = {"hooks": [{"type": "command", "command": f"bash {OLD_BASE}/completion-gate.sh"}]}
USER_STOP_GROUP = {"hooks": [{"type": "command", "command": "bash /home/u/my/stop-notes.sh"}]}
LOOKALIKE_GROUP = {"hooks": [{"type": "command", "command": "bash /home/u/my/completion-gate.sh"}]}


def _commands_in(path: Path, event: str) -> list[str]:
    data = json.loads(path.read_text(encoding="utf-8"))
    return [h.get("command", "") for g in data["hooks"].get(event, []) for h in g["hooks"]]


def test_codex_merge_retires_a_stale_gate_and_keeps_user_handlers(install_ctx, tmp_path: Path) -> None:
    from scripts.lib.integrations._codex_native import merge_hooks_json

    dst = tmp_path / "hooks.json"
    dst.write_text(json.dumps({"hooks": {"Stop": [STALE_STOP, USER_STOP_GROUP, LOOKALIKE_GROUP]}}), encoding="utf-8")
    events, _, _ = build_hook_entries(SETTINGS, HOOKS, OLD_BASE)
    merge_hooks_json(install_ctx, "codex", dst, events, OLD_BASE)
    stop = _commands_in(dst, "Stop")
    assert f"bash {OLD_BASE}/completion-gate.sh" not in stop
    assert "bash /home/u/my/stop-notes.sh" in stop
    assert "bash /home/u/my/completion-gate.sh" in stop


@pytest.mark.parametrize(("spec", "stop_event"), [(GEMINI_CLI_SPEC, "AfterAgent"), (QWEN_SPEC, "Stop")])
def test_settings_json_merge_retires_a_stale_gate(install_ctx, tmp_path: Path, spec, stop_event: str) -> None:
    from scripts.lib.integrations._settings_hooks import merge_settings_hooks

    dst = tmp_path / "settings.json"
    dst.write_text(
        json.dumps({"theme": "dark", "hooks": {stop_event: [STALE_STOP, USER_STOP_GROUP]}}), encoding="utf-8"
    )
    events, _, _ = build_settings_hooks(spec, SETTINGS, HOOKS, OLD_BASE, False)
    merge_settings_hooks(install_ctx, "x", dst, events, OLD_BASE)
    assert f"bash {OLD_BASE}/completion-gate.sh" not in _commands_in(dst, stop_event)
    assert "bash /home/u/my/stop-notes.sh" in _commands_in(dst, stop_event)
    assert json.loads(dst.read_text(encoding="utf-8"))["theme"] == "dark"


def test_kimi_managed_block_is_regenerated_without_the_gate(install_ctx, tmp_path: Path) -> None:
    from scripts.lib.integrations._kimi_native import merge_config_hooks, render_hooks_block

    old_entries, _, _ = build_kimi_hooks(SETTINGS, HOOKS, BASE, False)
    old_entries.append({"event": "Stop", "command": f"bash {BASE}/completion-gate.sh", "timeout": 30})
    config = tmp_path / "config.toml"
    config.write_text("default_model = \"m\"\n\n" + render_hooks_block(old_entries), encoding="utf-8")
    assert "completion-gate" in config.read_text(encoding="utf-8")
    new_entries, _, _ = build_kimi_hooks(SETTINGS, HOOKS, BASE, False)
    merge_config_hooks(install_ctx, "kimi", config, render_hooks_block(new_entries))
    text = config.read_text(encoding="utf-8")
    assert "completion-gate" not in text
    assert 'default_model = "m"' in text
    assert "approval-capture" in text


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


def test_cursor_registers_capture_and_no_gate(install_ctx) -> None:
    _, root, _ = _cursor_write(install_ctx)
    data = json.loads((root / "hooks.json").read_text(encoding="utf-8"))
    assert not any("completion-gate" in e["command"] for e in data["hooks"]["stop"])
    assert any("usage-guard" in e["command"] for e in data["hooks"]["stop"])
    assert any("approval-capture" in e["command"] for e in data["hooks"]["beforeSubmitPrompt"])


def test_cursor_merge_retires_a_stale_gate_and_keeps_user_entries(install_ctx) -> None:
    """An install from before 2026-10-28 carries a Nexus-owned `stop` gate entry."""
    cursor, root, _ = _cursor_write(install_ctx)
    path = root / "hooks.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    guard = next(e for e in data["hooks"]["stop"] if "usage-guard" in e["command"])
    stale = {"command": guard["command"].replace("usage-guard.py", "completion-gate.sh")}
    data["hooks"]["stop"] = [stale, USER_STOP, *data["hooks"]["stop"]]
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    _cursor_write(install_ctx)
    after = json.loads(path.read_text(encoding="utf-8"))
    assert not any("completion-gate" in e["command"] for e in after["hooks"]["stop"])
    assert USER_STOP in after["hooks"]["stop"]
    assert any("usage-guard" in e["command"] for e in after["hooks"]["stop"])


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
    assert not any("completion-gate" in e["command"] for e in data["hooks"]["stop"])
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


def test_antigravity_registers_no_stop_gate(install_ctx) -> None:
    _, parent, _ = _antigravity_write(install_ctx)
    text = (parent / "hooks.json").read_text(encoding="utf-8")
    assert "Stop" not in json.loads(text)["nexus-hub-guardrails"]
    assert "completion-gate" not in text


def test_antigravity_rewrite_retires_a_stale_stop_gate(install_ctx) -> None:
    """The managed set is replaced wholesale, so an older install loses its `Stop` entry."""
    _, parent, _ = _antigravity_write(install_ctx)
    path = parent / "hooks.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    data["nexus-hub-guardrails"]["Stop"] = [
        {"hooks": [{"command": 'python ".agents/hooks/antigravity-hook-compat.py" antigravity Stop -- bash completion-gate.sh'}]}
    ]
    data.update(USER_SET)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    _antigravity_write(install_ctx)
    after = json.loads(path.read_text(encoding="utf-8"))
    assert "Stop" not in after["nexus-hub-guardrails"]
    assert after["my-hooks"] == USER_SET["my-hooks"]


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
