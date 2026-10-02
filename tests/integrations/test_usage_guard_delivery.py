"""usage-guard delivery per platform adapter (v4.13.7 Phase 7, sub-task 7.2).

Pins which platforms receive the hook, under which events, with its probe
module beside it, and which stay unregistered per the plan's platform table:

- Claude Code: ``settings.json`` on UserPromptSubmit, PostToolUse (no matcher), Stop.
- Codex: derived ``hooks.json`` on the same three events, 10-second timeout.
- Cursor: native ``hooks.json`` on postToolUse and stop only.
- Copilot: derived hooks on the three events, through copilot-hook-compat.py.
- Gemini CLI, Qwen, Kimi: receive it from settings.json and stay silent at runtime.
- Windsurf and Antigravity: curated lists, never receive it.

It also pins the Copilot wrapper changes the guard depends on.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.lib.integrations import _cascade_hook_compat as hook_compat
from scripts.lib.integrations import get
from scripts.lib.integrations._copilot_native import build_copilot_hooks
from scripts.lib.integrations._kimi_native import build_kimi_hooks
from scripts.lib.integrations._settings_hooks import (
    GEMINI_CLI_SPEC,
    QWEN_SPEC,
    build_settings_hooks,
)
from scripts.lib.integrations.base import InstallContext
from scripts.lib.integrations.codex import CodexIntegration
from scripts.lib.integrations.manifest import InstallManifest

REPO_ROOT = Path(__file__).resolve().parents[2]
SRC_HOOKS = REPO_ROOT / "catalog" / "hooks"
SETTINGS = json.loads((SRC_HOOKS / "settings.json").read_text(encoding="utf-8"))
GUARD_EVENTS = {"UserPromptSubmit", "PostToolUse", "Stop"}


def _ctx(target: Path) -> InstallContext:
    return InstallContext(
        repo_root=REPO_ROOT,
        target_root=target,
        scope="workspace",
        overwrite=False,
        dry_run=False,
        manifest=InstallManifest(),
        template_vars={"PROJECT_NAME": "test-project"},
    )


def _guard_events(hooks: dict) -> dict[str, list[dict]]:
    """event -> the groups or entries whose command runs usage-guard.py."""
    found: dict[str, list[dict]] = {}
    for event, groups in hooks.items():
        for group in groups:
            handlers = group.get("hooks", [group])
            for handler in handlers:
                command = " ".join(
                    str(handler.get(k, "")) for k in ("command", "bash", "commandWindows")
                )
                if "usage-guard.py" in command:
                    found.setdefault(event, []).append({**handler, "_matcher": group.get("matcher")})
    return found


def test_settings_json_registers_the_guard_on_three_events():
    found = _guard_events(SETTINGS["hooks"])
    assert set(found) == GUARD_EVENTS
    for event, handlers in found.items():
        assert len(handlers) == 1, event
        handler = handlers[0]
        assert handler["command"] == "python3 .claude/hooks/usage-guard.py"
        assert handler["timeout"] == 10
        assert handler["_matcher"] in ("", None), f"{event} must match every tool"


def test_codex_workspace_hooks_json_carries_the_guard(tmp_path):
    get("codex").install(_ctx(tmp_path))
    data = json.loads((tmp_path / ".codex" / "hooks.json").read_text(encoding="utf-8"))
    found = _guard_events(data["hooks"])
    assert set(found) == GUARD_EVENTS
    for handlers in found.values():
        assert handlers[0]["timeout"] == 10
        assert handlers[0]["_matcher"] is None
        assert "commandWindows" in handlers[0]
    hooks_dir = tmp_path / ".codex" / "hooks"
    assert (hooks_dir / "usage-guard.py").is_file()
    assert (hooks_dir / "_usage_probe.py").is_file()


def test_codex_install_note_says_untrusted_hooks_are_skipped():
    note = " ".join(CodexIntegration._trust_notes(REPO_ROOT))
    assert "/hooks" in note
    assert "skips an untrusted hook silently" in note
    assert "usage-guard" in note


def test_cursor_workspace_hooks_json_uses_post_tool_use_and_stop_only(tmp_path):
    get("cursor").install(_ctx(tmp_path))
    data = json.loads((tmp_path / ".cursor" / "hooks.json").read_text(encoding="utf-8"))
    found = _guard_events(data["hooks"])
    assert set(found) == {"postToolUse", "stop"}
    for handlers in found.values():
        command = handlers[0]["command"]
        assert "cursor-hook-compat.py" in command
        assert command.endswith('/usage-guard.py"'), command
        assert handlers[0]["timeout"] == 10
    stop_commands = [entry["command"] for entry in data["hooks"]["stop"]]
    assert any("completion-gate" in c for c in stop_commands)
    hooks_dir = tmp_path / ".cursor" / "hooks"
    assert (hooks_dir / "usage-guard.py").is_file()
    assert (hooks_dir / "_usage_probe.py").is_file()


def test_copilot_derived_hooks_carry_the_guard_and_its_probe():
    config, scripts, _ = build_copilot_hooks(SETTINGS, SRC_HOOKS, "/c")
    found = _guard_events(config["hooks"])
    assert set(found) == GUARD_EVENTS
    for event, handlers in found.items():
        assert f"copilot-hook-compat.py' copilot {event} --handler usage-guard.py" in handlers[0]["bash"]
        assert "matcher" not in handlers[0]
    assert {"usage-guard.py", "_usage_probe.py"} <= scripts


def test_copilot_workspace_install_lands_the_probe_beside_the_guard(tmp_path):
    get("copilot").install(_ctx(tmp_path))
    scripts = tmp_path / ".github" / "hooks" / "nexus-hub-scripts"
    assert (scripts / "usage-guard.py").is_file()
    assert (scripts / "_usage_probe.py").is_file()
    assert (scripts / "copilot-hook-compat.py").is_file()
    data = json.loads((tmp_path / ".github" / "hooks" / "nexus-hub.json").read_text(encoding="utf-8"))
    assert set(_guard_events(data["hooks"])) == GUARD_EVENTS


@pytest.mark.parametrize(
    ("spec", "expected"),
    [
        (GEMINI_CLI_SPEC, {"BeforeAgent", "AfterTool", "AfterAgent"}),
        (QWEN_SPEC, GUARD_EVENTS),
    ],
    ids=["gemini-cli", "qwen"],
)
def test_settings_class_platforms_receive_the_guard(spec, expected):
    events, scripts, _ = build_settings_hooks(spec, SETTINGS, SRC_HOOKS, "/g", False)
    assert set(_guard_events(events)) == expected
    assert "usage-guard.py" in scripts


def test_kimi_receives_the_guard():
    entries, scripts, _ = build_kimi_hooks(SETTINGS, SRC_HOOKS, "/k", False)
    events = {e["event"] for e in entries if "usage-guard.py" in e["command"]}
    assert events == GUARD_EVENTS
    assert "usage-guard.py" in scripts


@pytest.mark.parametrize("key", ["windsurf", "antigravity2"])
def test_curated_platforms_never_receive_the_guard(tmp_path, key):
    get(key).install(_ctx(tmp_path))
    for path in tmp_path.rglob("*"):
        if path.is_file() and path.suffix in {".json", ".toml"}:
            assert "usage-guard" not in path.read_text(encoding="utf-8", errors="replace"), path
    assert not list(tmp_path.rglob("usage-guard.py"))


# ----- Copilot wrapper changes ------------------------------------------------------


def test_copilot_wrapper_passes_timestamp_and_stop_flag_to_the_child():
    translated = hook_compat.translate_copilot_payload(
        {
            "timestamp": "2026-10-01T12:00:00.000Z",
            "session_id": "s",
            "cwd": "/repo",
            "hook_event_name": "Stop",
            "stop_hook_active": True,
        },
        "Stop",
    )
    assert translated["timestamp"] == "2026-10-01T12:00:00.000Z"
    assert translated["stop_hook_active"] is True


def test_copilot_wrapper_omits_fields_the_host_did_not_send():
    translated = hook_compat.translate_copilot_payload({"sessionId": "s", "toolName": "bash"}, "PostToolUse")
    assert "timestamp" not in translated and "stop_hook_active" not in translated


def test_copilot_wrapper_emits_both_context_shapes_for_post_tool_use():
    child = json.dumps({"hookSpecificOutput": {"hookEventName": "PostToolUse", "additionalContext": "ctx"}})
    output, code = hook_compat.translate_child_result(
        "copilot", "PostToolUse", stdout=child, stderr="", returncode=0
    )
    assert code == 0
    assert output == {
        "additionalContext": "ctx",
        "hookSpecificOutput": {"hookEventName": "PostToolUse", "additionalContext": "ctx"},
    }


def test_copilot_wrapper_keeps_other_events_top_level_only():
    child = json.dumps({"hookSpecificOutput": {"additionalContext": "ctx"}})
    output, _ = hook_compat.translate_child_result(
        "copilot", "SessionStart", stdout=child, stderr="", returncode=0
    )
    assert output == {"additionalContext": "ctx"}


def test_copilot_wrapper_translates_the_guard_stop_shape():
    child = json.dumps({"hookSpecificOutput": {"hookEventName": "Stop", "decision": "block", "reason": "go"}})
    output, code = hook_compat.translate_child_result("copilot", "Stop", stdout=child, stderr="", returncode=0)
    assert code == 0
    assert output["hookSpecificOutput"] == {"hookEventName": "Stop", "decision": "block", "reason": "go"}
    assert output["decision"] == "block" and output["reason"] == "go"
