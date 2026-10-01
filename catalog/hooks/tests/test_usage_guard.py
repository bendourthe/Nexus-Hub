"""Tests for catalog/hooks/usage-guard.py (v4.13.7 Phase 7).

The probe is stubbed for the decision tests, so nothing here touches the
network or a real credential. A few tests use the real probe against a primed
cache file or a Copilot state file under a temporary NEXUS_HOME, which the probe
reads without any network call, and a few run the hook as a subprocess through
the real Cursor and Copilot compatibility wrappers.

Payload fixtures follow the signatures in
docs/releases/v4/v4.13/development/v4.13.7-decisions.md ("Handoff guard
decisions" (2) and (4)): the Claude Code keys were captured live on 2026-10-01;
the Codex, Cursor, Qwen, Gemini CLI, Kimi, and VS Code fields are the documented
base fields quoted there. The Copilot fixture is the payload AFTER
copilot-hook-compat.py has translated it, which is what the hook receives.

Run with: pytest catalog/hooks/tests/test_usage_guard.py -q
"""

from __future__ import annotations

import importlib.util
import io
import json
import os
import shutil
import subprocess
import sys
import time
import types
from contextlib import redirect_stdout
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pytest

HOOKS_DIR = Path(__file__).resolve().parent.parent
GUARD_PATH = HOOKS_DIR / "usage-guard.py"
PROBE_PATH = HOOKS_DIR / "_usage_probe.py"
REPO_ROOT = HOOKS_DIR.parents[1]
COPILOT_WRAPPER = REPO_ROOT / "scripts" / "lib" / "integrations" / "_cascade_hook_compat.py"
CURSOR_WRAPPER = HOOKS_DIR / "cursor-hook-compat.py"

SECRET = "sk-ant-oat01-example-fixture-guard-do-not-leak-0099"

ENV_KEYS = (
    "NEXUS_DISABLED_HOOKS",
    "NEXUS_HOOK_PROFILE",
    "NEXUS_HANDOFF_THRESHOLD",
    "NEXUS_USAGE_PROBE_DISABLED",
    "NEXUS_USAGE_PROBE_PROVIDERS",
    "QWEN_PROJECT_DIR",
    "CLAUDE_CODE_ENTRYPOINT",
    "CLAUDE_PROJECT_DIR",
    "CURSOR_PROJECT_DIR",
)


def _load_guard() -> types.ModuleType:
    spec = importlib.util.spec_from_file_location("usage_guard_under_test", GUARD_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _iso(epoch: float) -> str:
    return datetime.fromtimestamp(epoch, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# ----- fixtures ---------------------------------------------------------------------


class FakeResult:
    def __init__(self, data: dict[str, Any]) -> None:
        self.data = data

    def to_dict(self) -> dict[str, Any]:
        return self.data


def reading(
    platform: str,
    percent: float,
    name: str = "weekly",
    status: str = "ok",
    fetched_at: str | None = None,
    resets_at: str | None = "2026-10-05T00:00:00Z",
    extra_windows: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    windows = [{"name": name, "percent": percent, "resets_at": resets_at, "source": "fixture"}]
    windows.extend(extra_windows or [])
    return {
        "platform": platform,
        "status": status,
        "cached": True,
        "fetched_at": fetched_at or _iso(time.time()),
        "windows": windows if status != "unavailable" else [],
        "reason": None,
    }


@pytest.fixture()
def env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    for key in ENV_KEYS:
        monkeypatch.delenv(key, raising=False)
    home = tmp_path / "nexus-home"
    monkeypatch.setenv("NEXUS_HOME", str(home))
    return home


@pytest.fixture()
def guard(env: Path, monkeypatch: pytest.MonkeyPatch) -> types.ModuleType:
    module = _load_guard()
    module.readings = {}
    module.probe_calls = []

    def probe(platform: str) -> FakeResult:
        module.probe_calls.append(platform)
        return FakeResult(module.readings.get(platform) or reading(platform, 0, status="unavailable"))

    monkeypatch.setattr(module, "_load_probe", lambda: types.SimpleNamespace(probe=probe))
    return module


@pytest.fixture()
def project(tmp_path: Path) -> Path:
    root = tmp_path / "project"
    (root / ".git").mkdir(parents=True)
    return root


@pytest.fixture()
def dirs(tmp_path: Path) -> dict[str, Path]:
    claude = tmp_path / "proj-hooks" / ".claude" / "hooks"
    codex = tmp_path / "home" / ".codex" / "hooks"
    cursor = tmp_path / "home" / ".cursor" / "hooks"
    copilot = tmp_path / "home" / ".copilot" / "hooks" / "nexus-hub-scripts"
    for path in (claude, codex, cursor, copilot):
        path.mkdir(parents=True)
    (copilot / "copilot-hook-compat.py").write_text("# wrapper\n", encoding="utf-8")
    return {
        "claude": claude,
        "codex": codex,
        "cursor": cursor,
        "cursor-imported": claude,
        "copilot": copilot,
        "qwen": tmp_path / "home" / ".qwen" / "hooks",
        "gemini-cli": tmp_path / "home" / ".gemini" / "hooks",
        "kimi": tmp_path / "home" / ".kimi-code" / "hooks",
    }


# Event names per platform for the three kinds the guard answers.
EVENTS = {
    "claude": {"prompt": "UserPromptSubmit", "tool": "PostToolUse", "stop": "Stop"},
    "codex": {"prompt": "UserPromptSubmit", "tool": "PostToolUse", "stop": "Stop"},
    "cursor": {"tool": "postToolUse", "stop": "stop"},
    "copilot": {"tool": "PostToolUse", "stop": "Stop"},
}
CONTEXT_KINDS = {
    "claude": ("prompt", "tool"),
    "codex": ("prompt", "tool"),
    "cursor": ("tool",),
    "copilot": ("tool",),
}
PLATFORMS = ("claude", "codex", "cursor", "copilot")


def payload(platform: str, kind: str, cwd: Path, session: str = "s-1", **extra: Any) -> dict[str, Any]:
    """A payload in the platform's documented shape."""
    if platform == "claude":
        body: dict[str, Any] = {
            "session_id": session,
            "transcript_path": "/t/x.jsonl",
            "cwd": str(cwd),
            "hook_event_name": EVENTS["claude"][kind],
            "permission_mode": "default",
            "prompt_id": "p-1",
            "scratchpad_dir": "/tmp/scratch",
        }
        if kind == "prompt":
            body["prompt"] = "do the thing"
        if kind == "tool":
            body.update(tool_name="Bash", tool_input={"command": "ls"}, tool_response={"stdout": ""})
        if kind == "stop":
            body.update(stop_hook_active=False, last_assistant_message="done")
    elif platform == "codex":
        body = {
            "session_id": session,
            "transcript_path": "/t/x.jsonl",
            "cwd": str(cwd),
            "hook_event_name": EVENTS["codex"][kind],
            "model": "gpt-5-codex",
            "permission_mode": "default",
            "turn_id": "turn-1",
        }
        if kind == "tool":
            body.update(tool_name="Bash", tool_input={"command": "ls"})
        if kind == "stop":
            body["stop_hook_active"] = False
    elif platform == "cursor":
        body = {
            "conversation_id": session,
            "generation_id": "g-1",
            "model": "auto",
            "hook_event_name": EVENTS["cursor"].get(kind, "beforeSubmitPrompt"),
            "cursor_version": "2.4.0",
            "workspace_roots": [str(cwd)],
            "transcript_path": None,
        }
        if kind == "tool":
            body.update(tool_name="Shell", tool_input={"command": "ls"}, tool_output="{}")
        if kind == "stop":
            body.update(status="completed", loop_count=0)
    elif platform == "copilot":
        body = {
            "hook_event_name": EVENTS["copilot"].get(kind, "UserPromptSubmit"),
            "tool_name": "run_in_terminal" if kind == "tool" else "",
            "tool_input": {"command": "ls"} if kind == "tool" else {},
            "session_id": session,
            "cwd": str(cwd),
            "timestamp": "2026-10-01T12:00:00.000Z",
        }
        if kind == "stop":
            body["stop_hook_active"] = False
    else:
        raise AssertionError(platform)
    body.update(extra)
    return body


def run(guard: types.ModuleType, dirs: dict[str, Path], platform: str, body: dict[str, Any]) -> dict[str, Any] | None:
    return guard.evaluate(body, time.monotonic(), dirs[platform])


def expected_shape(platform: str, kind: str, message: str) -> dict[str, Any]:
    event = EVENTS[platform][kind]
    if platform == "cursor":
        return {"followup_message": message} if kind == "stop" else {"additional_context": message}
    if kind == "stop":
        if platform == "copilot":
            return {"hookSpecificOutput": {"hookEventName": "Stop", "decision": "block", "reason": message}}
        return {"decision": "block", "reason": message}
    return {"hookSpecificOutput": {"hookEventName": event, "additionalContext": message}}


def message_of(output: dict[str, Any]) -> str:
    for key in ("additional_context", "followup_message", "reason"):
        if key in output:
            return output[key]
    specific = output["hookSpecificOutput"]
    return specific.get("additionalContext") or specific["reason"]


# ----- per-platform behavior ------------------------------------------------------


@pytest.mark.parametrize("platform", PLATFORMS)
def test_below_threshold_emits_nothing(guard, dirs, project, platform):
    guard.readings[platform] = reading(platform, 98.9)
    for kind in EVENTS[platform]:
        assert run(guard, dirs, platform, payload(platform, kind, project)) is None
    assert guard.probe_calls, "the probe must have been consulted"


@pytest.mark.parametrize(
    ("platform", "kind"),
    [(p, k) for p in PLATFORMS for k in CONTEXT_KINDS[p]],
)
def test_first_crossing_has_the_exact_output_shape(guard, dirs, project, platform, kind):
    guard.readings[platform] = reading(platform, 99.2)
    output = run(guard, dirs, platform, payload(platform, kind, project))
    message = guard.directive(platform, {"name": "weekly", "percent": 99.2, "resets_at": "2026-10-05T00:00:00Z"})
    assert output == expected_shape(platform, kind, message)


@pytest.mark.parametrize("platform", PLATFORMS)
def test_second_tool_call_in_the_same_session_is_silent(guard, dirs, project, platform):
    guard.readings[platform] = reading(platform, 100)
    assert run(guard, dirs, platform, payload(platform, "tool", project)) is not None
    assert run(guard, dirs, platform, payload(platform, "tool", project)) is None
    if "prompt" in EVENTS[platform]:
        assert run(guard, dirs, platform, payload(platform, "prompt", project)) is None


@pytest.mark.parametrize("platform", PLATFORMS)
def test_a_new_session_hears_the_directive_again(guard, dirs, project, platform):
    guard.readings[platform] = reading(platform, 100)
    assert run(guard, dirs, platform, payload(platform, "tool", project, session="a")) is not None
    assert run(guard, dirs, platform, payload(platform, "tool", project, session="b")) is not None


@pytest.mark.parametrize("platform", PLATFORMS)
def test_stop_continuation_fires_exactly_once(guard, dirs, project, platform):
    guard.readings[platform] = reading(platform, 99.5)
    run(guard, dirs, platform, payload(platform, "tool", project))
    first = run(guard, dirs, platform, payload(platform, "stop", project))
    message = guard.directive(platform, {"name": "weekly", "percent": 99.5, "resets_at": "2026-10-05T00:00:00Z"})
    assert first == expected_shape(platform, "stop", message)
    assert run(guard, dirs, platform, payload(platform, "stop", project)) is None


@pytest.mark.parametrize("platform", PLATFORMS)
def test_stop_without_a_prior_directive_still_asks_once(guard, dirs, project, platform):
    guard.readings[platform] = reading(platform, 100)
    assert run(guard, dirs, platform, payload(platform, "stop", project)) is not None
    assert run(guard, dirs, platform, payload(platform, "tool", project)) is None
    assert run(guard, dirs, platform, payload(platform, "stop", project)) is None


@pytest.mark.parametrize(
    ("platform", "flag"),
    [
        ("claude", {"stop_hook_active": True}),
        ("codex", {"stop_hook_active": True}),
        ("copilot", {"stop_hook_active": True}),
        ("cursor", {"loop_count": 1}),
    ],
)
def test_a_flag_set_by_another_hook_does_not_suppress_the_continuation(
    guard, dirs, project, platform, flag
):
    # The completion gate blocks every chained turn, so the flag is set even
    # though this guard never continued. Regression for review finding F1.
    guard.readings[platform] = reading(platform, 100)
    run(guard, dirs, platform, payload(platform, "tool", project))
    assert run(guard, dirs, platform, payload(platform, "stop", project, **flag)) is not None
    assert run(guard, dirs, platform, payload(platform, "stop", project, **flag)) is None


@pytest.mark.parametrize(
    ("platform", "flag"),
    [
        ("claude", {"stop_hook_active": True}),
        ("codex", {"stop_hook_active": True}),
        ("copilot", {"stop_hook_active": True}),
        ("cursor", {"loop_count": 1}),
    ],
)
def test_first_crossing_at_a_flagged_stop_continues_once_and_stays_bounded(
    guard, dirs, project, platform, flag
):
    guard.readings[platform] = reading(platform, 99.5)
    first = run(guard, dirs, platform, payload(platform, "stop", project, **flag))
    assert first is not None
    for _ in range(10):
        assert run(guard, dirs, platform, payload(platform, "stop", project, **flag)) is None
    assert run(guard, dirs, platform, payload(platform, "tool", project)) is None


@pytest.mark.parametrize(
    ("platform", "flag"),
    [
        ("claude", {"stop_hook_active": True}),
        ("codex", {"stop_hook_active": True}),
        ("copilot", {"stop_hook_active": True}),
        ("cursor", {"loop_count": 1}),
    ],
)
def test_a_window_skipped_at_a_flagged_stop_is_warned_at_the_next_tool_call(
    guard, dirs, project, platform, flag
):
    # Our continuation for five_hour caused the flagged turn end, so weekly is
    # not continued there; it must still be announced, not silently recorded.
    guard.readings[platform] = reading(platform, 99.5, name="five_hour")
    assert run(guard, dirs, platform, payload(platform, "stop", project)) is not None
    guard.readings[platform] = reading(
        platform, 99.5, name="five_hour",
        extra_windows=[{"name": "weekly", "percent": 99.9, "resets_at": None, "source": "x"}],
    )
    assert run(guard, dirs, platform, payload(platform, "stop", project, **flag)) is None
    warned = run(guard, dirs, platform, payload(platform, "tool", project))
    assert warned is not None and "weekly usage is at 99.9%" in message_of(warned)


@pytest.mark.parametrize("platform", PLATFORMS)
def test_stop_loop_is_bounded_over_many_turn_ends(guard, dirs, project, platform):
    guard.readings[platform] = reading(platform, 100)
    outputs = [run(guard, dirs, platform, payload(platform, "stop", project)) for _ in range(25)]
    assert sum(1 for o in outputs if o is not None) == 1


def _write_handoff(project: Path, stamp: float, trigger: str) -> None:
    path = project / ".nexus-hub" / "handoff.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"# Handoff | {_iso(stamp)} | claude | {trigger}\n\n## Goal\n", encoding="utf-8")


@pytest.mark.parametrize("platform", PLATFORMS)
def test_usage_limit_handoff_newer_than_the_trigger_suppresses_the_stop(guard, dirs, project, platform):
    guard.readings[platform] = reading(platform, 100)
    run(guard, dirs, platform, payload(platform, "tool", project))
    _write_handoff(project, time.time() + 1, "usage-limit weekly 100")
    assert run(guard, dirs, platform, payload(platform, "stop", project)) is None


@pytest.mark.parametrize("trigger", ["checkpoint", "manual"])
def test_a_non_usage_limit_handoff_does_not_suppress(guard, dirs, project, trigger):
    guard.readings["claude"] = reading("claude", 100)
    run(guard, dirs, "claude", payload("claude", "tool", project))
    _write_handoff(project, time.time() + 1, trigger)
    assert run(guard, dirs, "claude", payload("claude", "stop", project)) is not None


def test_a_handoff_older_than_the_trigger_does_not_suppress(guard, dirs, project):
    guard.readings["claude"] = reading("claude", 100)
    _write_handoff(project, time.time() - 3600, "usage-limit weekly 99.4")
    run(guard, dirs, "claude", payload("claude", "tool", project))
    assert run(guard, dirs, "claude", payload("claude", "stop", project)) is not None


def test_handoff_in_the_repository_root_is_found_from_a_subdirectory(guard, dirs, project):
    sub = project / "src" / "pkg"
    sub.mkdir(parents=True)
    guard.readings["codex"] = reading("codex", 100)
    run(guard, dirs, "codex", payload("codex", "tool", sub))
    _write_handoff(project, time.time() + 1, "usage-limit weekly 100")
    assert run(guard, dirs, "codex", payload("codex", "stop", sub)) is None


# ----- events with no context channel ----------------------------------------------


def test_cursor_before_submit_prompt_is_silent_and_skips_the_probe(guard, dirs, project):
    guard.readings["cursor"] = reading("cursor", 100)
    body = payload("cursor", "prompt", project, hook_event_name="beforeSubmitPrompt")
    assert run(guard, dirs, "cursor", body) is None
    assert guard.probe_calls == []


def test_copilot_user_prompt_submit_is_silent_and_skips_the_probe(guard, dirs, project):
    guard.readings["copilot"] = reading("copilot", 100)
    body = payload("copilot", "prompt", project)
    assert body["hook_event_name"] == "UserPromptSubmit"
    assert run(guard, dirs, "copilot", body) is None
    assert guard.probe_calls == []


# ----- probe status --------------------------------------------------------------


@pytest.mark.parametrize("platform", PLATFORMS)
def test_unavailable_probe_is_silent(guard, dirs, project, platform):
    guard.readings[platform] = reading(platform, 100, status="unavailable")
    for kind in EVENTS[platform]:
        assert run(guard, dirs, platform, payload(platform, kind, project)) is None


def test_stale_reading_under_thirty_minutes_still_acts(guard, dirs, project):
    guard.readings["claude"] = reading("claude", 100, status="stale", fetched_at=_iso(time.time() - 600))
    assert run(guard, dirs, "claude", payload("claude", "tool", project)) is not None


@pytest.mark.parametrize("fetched_at", [None, "not-a-date", "OLD"])
def test_stale_reading_older_than_thirty_minutes_or_undated_is_silent(guard, dirs, project, fetched_at):
    stamp = _iso(time.time() - 1900) if fetched_at == "OLD" else fetched_at
    data = reading("claude", 100, status="stale")
    data["fetched_at"] = stamp
    guard.readings["claude"] = data
    assert run(guard, dirs, "claude", payload("claude", "tool", project)) is None


@pytest.mark.parametrize("status", ["error", "", None])
def test_unknown_probe_status_is_silent(guard, dirs, project, status):
    data = reading("claude", 100)
    data["status"] = status
    guard.readings["claude"] = data
    assert run(guard, dirs, "claude", payload("claude", "tool", project)) is None


def test_highest_crossing_window_is_named(guard, dirs, project):
    guard.readings["claude"] = reading(
        "claude", 99.1, name="five_hour",
        extra_windows=[{"name": "weekly", "percent": 99.8, "resets_at": None, "source": "x"}],
    )
    output = run(guard, dirs, "claude", payload("claude", "tool", project))
    assert "weekly usage is at 99.8%" in message_of(output)
    assert "(resets" not in message_of(output)


def test_a_second_window_crossing_later_gets_its_own_directive(guard, dirs, project):
    guard.readings["claude"] = reading("claude", 99.0, name="five_hour")
    first = run(guard, dirs, "claude", payload("claude", "tool", project))
    assert "five_hour" in message_of(first)
    guard.readings["claude"] = reading(
        "claude", 99.0, name="five_hour",
        extra_windows=[{"name": "weekly", "percent": 99.5, "resets_at": None, "source": "x"}],
    )
    second = run(guard, dirs, "claude", payload("claude", "tool", project))
    assert second is not None and "weekly" in message_of(second)


@pytest.mark.parametrize("bad", [None, "99", True, float("nan"), {"x": 1}])
def test_malformed_window_percent_is_ignored(guard, dirs, project, bad):
    data = reading("claude", 0)
    data["windows"] = [{"name": "weekly", "percent": bad, "resets_at": None, "source": "x"}, "junk", None]
    guard.readings["claude"] = data
    assert run(guard, dirs, "claude", payload("claude", "tool", project)) is None


# ----- threshold -----------------------------------------------------------------


@pytest.mark.parametrize(
    ("percent", "fires"),
    [(98.9, False), (99.0, True), (100.0, True)],
)
def test_default_threshold_edges(guard, dirs, project, percent, fires):
    guard.readings["claude"] = reading("claude", percent)
    output = run(guard, dirs, "claude", payload("claude", "tool", project))
    assert (output is not None) is fires


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("", 99), ("abc", 99), ("0", 99), ("101", 99), ("-5", 99), ("99.5", 99),
        ("1", 1), ("50", 50), (" 80 ", 80), ("100", 100), ("1000", 99),
    ],
)
def test_threshold_parsing(guard, monkeypatch, raw, expected):
    monkeypatch.setenv("NEXUS_HANDOFF_THRESHOLD", raw)
    assert guard.threshold() == expected


def test_configured_threshold_is_honored(guard, dirs, project, monkeypatch):
    monkeypatch.setenv("NEXUS_HANDOFF_THRESHOLD", "1")
    guard.readings["codex"] = reading("codex", 3)
    assert run(guard, dirs, "codex", payload("codex", "tool", project)) is not None


# ----- platform detection --------------------------------------------------------


def _foreign_payloads(cwd: Path) -> dict[str, dict[str, Any]]:
    stamp = "2026-10-01T12:00:00Z"
    return {
        "qwen": {
            "session_id": "q", "transcript_path": "/t", "cwd": str(cwd), "hook_event_name": "PostToolUse",
            "timestamp": stamp, "permission_mode": "default", "tool_name": "run_shell_command",
        },
        "gemini-cli": {
            "session_id": "g", "transcript_path": "/t", "cwd": str(cwd), "hook_event_name": "AfterTool",
            "timestamp": stamp, "tool_name": "run_shell_command",
        },
        "kimi": {
            "hook_event_name": "PostToolUse", "session_id": "k", "session_title": "t",
            "client_type": "cli", "cwd": str(cwd), "tool_name": "Shell",
        },
    }


@pytest.mark.parametrize("platform", ["qwen", "gemini-cli", "kimi"])
def test_platforms_without_a_usage_source_stay_silent_with_claude_at_100(
    guard, dirs, project, monkeypatch, platform
):
    # The misclassification case: a Claude credential over the threshold, and
    # the Claude Code environment inherited from a launching terminal.
    monkeypatch.setenv("CLAUDE_CODE_ENTRYPOINT", "cli")
    for key in PLATFORMS:
        guard.readings[key] = reading(key, 100)
    body = _foreign_payloads(project)[platform]
    for event in ("PostToolUse", "UserPromptSubmit", "Stop", "AfterTool", "AfterAgent", "BeforeAgent"):
        body = {**body, "hook_event_name": event}
        assert run(guard, dirs, platform, body) is None
    assert guard.probe_calls == []


def test_qwen_project_dir_marks_a_payload_as_qwen(guard, dirs, project, monkeypatch):
    monkeypatch.setenv("QWEN_PROJECT_DIR", str(project))
    guard.readings["claude"] = reading("claude", 100)
    body = payload("claude", "tool", project)
    body.pop("scratchpad_dir")
    monkeypatch.setenv("CLAUDE_CODE_ENTRYPOINT", "cli")
    assert run(guard, dirs, "claude", body) is None


def test_copilot_payload_with_claude_at_100_and_no_copilot_state_is_silent(dirs, project, env):
    # Real probe, real files: a primed Claude cache at 100% and no copilot.json.
    module = _load_guard()
    _prime_claude_cache(env, 100)
    output = module.evaluate(payload("copilot", "tool", project), time.monotonic(), dirs["copilot"])
    assert output is None
    probe = module._load_probe()
    assert probe.probe("copilot").status == "unavailable"


@pytest.mark.parametrize(
    "mutation",
    [
        {"timestamp": 1790000000000},
        {"timestamp": None},
        {"permission_mode": "default"},
        {"turn_id": "t"},
    ],
)
def test_copilot_signature_rejects_other_payload_shapes(guard, dirs, project, mutation):
    guard.readings["copilot"] = reading("copilot", 100)
    body = payload("copilot", "tool", project)
    body.update(mutation)
    if body.get("timestamp") is None:
        body.pop("timestamp")
    assert run(guard, dirs, "copilot", body) is None


def test_copilot_payload_outside_the_copilot_hooks_dir_is_silent(guard, dirs, project):
    guard.readings["copilot"] = reading("copilot", 100)
    assert run(guard, dirs, "codex", payload("copilot", "tool", project)) is None


def test_claude_payload_without_scratchpad_needs_the_entrypoint(guard, dirs, project, monkeypatch):
    guard.readings["claude"] = reading("claude", 100)
    body = payload("claude", "tool", project)
    body.pop("scratchpad_dir")
    assert run(guard, dirs, "claude", body) is None
    monkeypatch.setenv("CLAUDE_CODE_ENTRYPOINT", "cli")
    assert run(guard, dirs, "claude", body) is not None


def test_cursor_payload_through_an_imported_claude_path_is_silent(guard, dirs, project):
    guard.readings["cursor"] = reading("cursor", 100)
    assert run(guard, dirs, "cursor-imported", payload("cursor", "tool", project)) is None
    assert guard.probe_calls == []


def test_one_cursor_tool_call_produces_exactly_one_directive(guard, dirs, project):
    # Cursor runs both its native hooks.json entry and the imported Claude one.
    guard.readings["cursor"] = reading("cursor", 100)
    body = payload("cursor", "tool", project)
    outputs = [
        run(guard, dirs, "cursor", body),
        run(guard, dirs, "cursor-imported", body),
    ]
    assert sum(1 for o in outputs if o is not None) == 1


@pytest.mark.parametrize(
    "body",
    [
        {},
        {"hook_event_name": "PostToolUse"},
        {"hook_event_name": "PostToolUse", "session_id": "x", "cwd": "/"},
        {"hook_event_name": "SomethingNew", "scratchpad_dir": "/s"},
    ],
)
def test_unrecognized_payloads_are_silent(guard, dirs, project, body):
    for key in PLATFORMS:
        guard.readings[key] = reading(key, 100)
    for where in ("claude", "codex", "cursor", "copilot"):
        assert run(guard, dirs, where, dict(body)) is None


# ----- stdin, switches, budget, state --------------------------------------------


@pytest.mark.parametrize("raw", ["", "not json", "[]", "42", '"text"', "{", "\x00\x01"])
def test_malformed_stdin_is_silent(guard, monkeypatch, raw):
    monkeypatch.setattr(sys, "stdin", io.StringIO(raw))
    out = io.StringIO()
    with redirect_stdout(out):
        assert guard.main() == 0
    assert out.getvalue() == ""


@pytest.mark.parametrize(
    ("key", "value"),
    [
        ("NEXUS_DISABLED_HOOKS", "usage-guard"),
        ("NEXUS_DISABLED_HOOKS", "secret-scan, usage-guard ,git-guardrails"),
        ("NEXUS_HOOK_PROFILE", "minimal"),
    ],
)
def test_disable_switches_silence_the_hook(guard, project, monkeypatch, key, value):
    monkeypatch.setenv(key, value)
    monkeypatch.setenv("CLAUDE_CODE_ENTRYPOINT", "cli")
    guard.readings["claude"] = reading("claude", 100)
    monkeypatch.setattr(sys, "stdin", io.StringIO(json.dumps(payload("claude", "tool", project))))
    out = io.StringIO()
    with redirect_stdout(out):
        assert guard.main() == 0
    assert out.getvalue() == ""
    assert guard.probe_calls == []


def test_other_disabled_hooks_do_not_silence_it(guard, monkeypatch):
    monkeypatch.setenv("NEXUS_DISABLED_HOOKS", "usage-guard-extra,usage")
    monkeypatch.setenv("NEXUS_HOOK_PROFILE", "full")
    assert guard.hook_disabled() is False


def test_budget_overrun_is_silent(guard, dirs, project, monkeypatch):
    monkeypatch.setattr(guard, "HOOK_BUDGET_SECONDS", 0.7)
    monkeypatch.setattr(guard, "BUDGET_MARGIN_SECONDS", 0.5)

    def slow_probe(platform: str) -> FakeResult:
        time.sleep(1.5)
        return FakeResult(reading(platform, 100))

    monkeypatch.setattr(guard, "_load_probe", lambda: types.SimpleNamespace(probe=slow_probe))
    started = time.monotonic()
    assert run(guard, dirs, "claude", payload("claude", "tool", project)) is None
    assert time.monotonic() - started < 1.2


def test_a_probe_that_raises_is_silent(guard, dirs, project, monkeypatch):
    def broken(platform: str) -> FakeResult:
        raise RuntimeError("boom")

    monkeypatch.setattr(guard, "_load_probe", lambda: types.SimpleNamespace(probe=broken))
    assert run(guard, dirs, "claude", payload("claude", "tool", project)) is None


def test_unwritable_state_never_repeats_the_prompt(guard, dirs, project, env):
    (env / "state").mkdir(parents=True)
    (env / "state" / "usage-guard").write_text("not a directory", encoding="utf-8")
    guard.readings["claude"] = reading("claude", 100)
    for kind in ("tool", "tool", "stop", "stop"):
        assert run(guard, dirs, "claude", payload("claude", kind, project)) is None


def test_held_lock_makes_the_hook_silent(guard, dirs, project, env, monkeypatch):
    monkeypatch.setattr(guard, "LOCK_WAIT_SECONDS", 0.05)
    state = env / "state" / "usage-guard"
    state.mkdir(parents=True)
    (state / "claude-s-1.json.lock").write_text("", encoding="utf-8")
    guard.readings["claude"] = reading("claude", 100)
    assert run(guard, dirs, "claude", payload("claude", "tool", project)) is None


def test_stale_lock_is_broken(guard, dirs, project, env):
    state = env / "state" / "usage-guard"
    state.mkdir(parents=True)
    lock = state / "claude-s-1.json.lock"
    lock.write_text("", encoding="utf-8")
    old = time.time() - 60
    os.utime(lock, (old, old))
    guard.readings["claude"] = reading("claude", 100)
    assert run(guard, dirs, "claude", payload("claude", "tool", project)) is not None
    assert not lock.exists()


def test_state_file_records_the_trigger(guard, dirs, project, env):
    guard.readings["codex"] = reading("codex", 99.3)
    run(guard, dirs, "codex", payload("codex", "tool", project, session="sess-42"))
    state = json.loads((env / "state" / "usage-guard" / "codex-sess-42.json").read_text(encoding="utf-8"))
    assert state["triggered_window"] == "weekly"
    assert state["continuation_sent"] is False
    assert state["schema"] == 2
    assert set(state["windows"]) == {"weekly"}
    assert state["windows"]["weekly"]["continuation_sent"] is False
    assert datetime.strptime(state["triggered_at"], "%Y-%m-%dT%H:%M:%SZ")
    run(guard, dirs, "codex", payload("codex", "stop", project, session="sess-42"))
    state = json.loads((env / "state" / "usage-guard" / "codex-sess-42.json").read_text(encoding="utf-8"))
    assert state["continuation_sent"] is True


def test_unusual_session_ids_become_a_hashed_filename(guard, dirs, project, env):
    guard.readings["claude"] = reading("claude", 100)
    run(guard, dirs, "claude", payload("claude", "tool", project, session="../../etc/x y"))
    names = [p.name for p in (env / "state" / "usage-guard").iterdir()]
    assert len(names) == 1 and names[0].startswith("claude-") and ".." not in names[0]
    assert len(names[0]) == len("claude-") + 32 + len(".json")


def test_old_session_state_is_pruned(guard, dirs, project, env):
    state = env / "state" / "usage-guard"
    state.mkdir(parents=True)
    old_file = state / "claude-old.json"
    old_file.write_text("{}", encoding="utf-8")
    old = time.time() - 8 * 24 * 3600
    os.utime(old_file, (old, old))
    guard.readings["claude"] = reading("claude", 100)
    run(guard, dirs, "claude", payload("claude", "tool", project))
    assert not old_file.exists()


# ----- message content and leaks -------------------------------------------------


def test_directive_wording(guard):
    text = guard.directive("codex", {"name": "weekly", "percent": 99.0, "resets_at": "2026-10-05T00:00:00Z"})
    assert text.startswith("Usage limit: Codex weekly usage is at 99% (resets 2026-10-05T00:00:00Z).")
    assert "run the session-handoff procedure (/handoff)" in text
    assert "write .nexus-hub/handoff.md and print its paste-ready prompt" in text
    assert "Start no new work." in text
    assert "usage-limit weekly 99." in text
    assert text.isascii()
    assert "—" not in text and " - " not in text


def test_no_credential_or_raw_response_reaches_output_or_state(guard, dirs, project, env):
    data = reading("claude", 100)
    data["reason"] = f"raw body {SECRET}"
    data["token"] = SECRET
    data["windows"][0]["raw"] = SECRET
    data["windows"][0]["source"] = SECRET
    guard.readings["claude"] = data
    outputs = [
        run(guard, dirs, "claude", payload("claude", kind, project))
        for kind in ("prompt", "tool", "stop")
    ]
    assert outputs[0] is not None and outputs[2] is not None
    dumped = json.dumps(outputs)
    assert SECRET not in dumped
    for path in env.rglob("*"):
        if path.is_file():
            assert SECRET not in path.read_text(encoding="utf-8", errors="replace"), path


# ----- real probe: cache path latency and subprocess delivery --------------------


def _prime_claude_cache(home: Path, percent: float) -> None:
    cache = home / "state" / "usage-probe" / "claude.json"
    cache.parent.mkdir(parents=True, exist_ok=True)
    cache.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "platform": "claude",
                "data_at": time.time(),
                "windows": [
                    {"name": "five_hour", "percent": 12.0, "resets_at": None, "source": "anthropic-oauth-usage"},
                    {"name": "weekly", "percent": percent, "resets_at": "2026-10-05T00:00:00Z", "source": "anthropic-oauth-usage"},
                ],
            }
        ),
        encoding="utf-8",
    )


def _write_copilot_state(home: Path, percent: float) -> None:
    path = home / "state" / "usage-probe" / "copilot.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "provider": "copilot",
                "fetched_at": _iso(time.time()),
                "approximate": False,
                "windows": [{"name": "monthly", "percent": percent, "resets_at": "2026-11-01T00:00:00Z", "source": "personal"}],
            }
        ),
        encoding="utf-8",
    )


def test_cached_path_latency_p95_under_150_ms(dirs, project, env):
    module = _load_guard()
    _prime_claude_cache(env, 100)
    samples = []
    for index in range(50):
        body = payload("claude", "tool", project, session=f"lat-{index}")
        start = time.perf_counter()
        output = module.evaluate(body, time.monotonic(), dirs["claude"])
        samples.append(time.perf_counter() - start)
        assert output is not None
    samples.sort()
    p95 = samples[int(len(samples) * 0.95) - 1]
    assert p95 < 0.150, f"p95 {p95 * 1000:.1f} ms"


def _subprocess_env(home: Path) -> dict[str, str]:
    env = {k: v for k, v in os.environ.items() if k not in ENV_KEYS}
    env["NEXUS_HOME"] = str(home)
    return env


def _install_scripts(target: Path) -> None:
    target.mkdir(parents=True, exist_ok=True)
    shutil.copy2(GUARD_PATH, target / "usage-guard.py")
    shutil.copy2(PROBE_PATH, target / "_usage_probe.py")


def test_subprocess_claude_hook_emits_once_then_continues_once(tmp_path, project, env):
    hooks = tmp_path / "sub" / ".claude" / "hooks"
    _install_scripts(hooks)
    _prime_claude_cache(env, 100)
    run_env = _subprocess_env(env)

    def call(kind: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(hooks / "usage-guard.py")],
            input=json.dumps(payload("claude", kind, project, session="sub-1")),
            text=True, capture_output=True, env=run_env, timeout=60,
        )

    first = call("prompt")
    assert first.returncode == 0 and first.stderr == ""
    body = json.loads(first.stdout)
    assert body["hookSpecificOutput"]["hookEventName"] == "UserPromptSubmit"
    assert body["hookSpecificOutput"]["additionalContext"].startswith("Usage limit: Claude Code weekly usage is at 100%")
    assert call("tool").stdout == ""
    stop = json.loads(call("stop").stdout)
    assert stop["decision"] == "block" and stop["reason"].startswith("Usage limit:")
    assert call("stop").stdout == ""


def test_subprocess_cursor_native_through_the_compat_launcher(tmp_path, project, env):
    hooks = tmp_path / "home" / ".cursor" / "hooks"
    _install_scripts(hooks)
    shutil.copy2(CURSOR_WRAPPER, hooks / "cursor-hook-compat.py")
    cache = env / "state" / "usage-probe" / "cursor.json"
    cache.parent.mkdir(parents=True, exist_ok=True)
    cache.write_text(
        json.dumps({
            "schema_version": 1, "platform": "cursor", "data_at": time.time(),
            "windows": [{"name": "monthly", "percent": 99.6, "resets_at": None, "source": "cursor-dashboard-rpc"}],
        }),
        encoding="utf-8",
    )

    def call(kind: str, **extra: Any) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(hooks / "cursor-hook-compat.py"), sys.executable, str(hooks / "usage-guard.py")],
            input=json.dumps(payload("cursor", kind, project, session="cur-1", **extra)),
            text=True, capture_output=True, env=_subprocess_env(env), timeout=60,
        )

    tool = call("tool")
    assert tool.returncode == 0
    assert json.loads(tool.stdout) == {
        "additional_context": json.loads(tool.stdout)["additional_context"]
    }
    assert "Cursor monthly usage is at 99.6%" in json.loads(tool.stdout)["additional_context"]
    assert json.loads(call("tool").stdout) == {}
    # loop_count from another hook's follow-up does not suppress this guard.
    stop = json.loads(call("stop", loop_count=1).stdout)
    assert list(stop) == ["followup_message"]
    assert json.loads(call("stop", loop_count=2).stdout) == {}
    assert json.loads(call("stop").stdout) == {}


def test_subprocess_copilot_through_the_real_wrapper(tmp_path, project, env):
    scripts = tmp_path / "home" / ".copilot" / "hooks" / "nexus-hub-scripts"
    _install_scripts(scripts)
    shutil.copy2(COPILOT_WRAPPER, scripts / "copilot-hook-compat.py")
    _write_copilot_state(env, 99.4)
    native = {
        "timestamp": "2026-10-01T12:00:00.000Z",
        "cwd": str(project),
        "session_id": "cop-1",
        "transcript_path": "/t",
    }

    def call(event: str, **extra: Any) -> subprocess.CompletedProcess[str]:
        body = {**native, "hook_event_name": event, **extra}
        return subprocess.run(
            [
                sys.executable, str(scripts / "copilot-hook-compat.py"), "copilot", event,
                "--handler", "usage-guard.py", "--", sys.executable, str(scripts / "usage-guard.py"),
            ],
            input=json.dumps(body), text=True, capture_output=True, env=_subprocess_env(env), timeout=60,
        )

    assert json.loads(call("UserPromptSubmit", prompt="hi").stdout) == {}
    tool = json.loads(call("PostToolUse", tool_name="run_in_terminal", tool_input={"command": "ls"}).stdout)
    context = tool["hookSpecificOutput"]["additionalContext"]
    assert tool["hookSpecificOutput"]["hookEventName"] == "PostToolUse"
    assert tool["additionalContext"] == context
    assert "GitHub Copilot monthly usage is at 99.4%" in context
    stop = json.loads(call("Stop", stop_hook_active=True).stdout)
    assert stop["hookSpecificOutput"] == {"hookEventName": "Stop", "decision": "block", "reason": context}
    assert json.loads(call("Stop", stop_hook_active=False).stdout) == {}


def test_subprocess_copilot_without_a_state_file_is_silent(tmp_path, project, env):
    scripts = tmp_path / "home" / ".copilot" / "hooks" / "nexus-hub-scripts"
    _install_scripts(scripts)
    shutil.copy2(COPILOT_WRAPPER, scripts / "copilot-hook-compat.py")
    _prime_claude_cache(env, 100)
    body = {"timestamp": "2026-10-01T12:00:00.000Z", "cwd": str(project), "session_id": "c2",
            "hook_event_name": "PostToolUse", "tool_name": "x", "tool_input": {}}
    proc = subprocess.run(
        [sys.executable, str(scripts / "copilot-hook-compat.py"), "copilot", "PostToolUse",
         "--handler", "usage-guard.py", "--", sys.executable, str(scripts / "usage-guard.py")],
        input=json.dumps(body), text=True, capture_output=True, env=_subprocess_env(env), timeout=60,
    )
    assert json.loads(proc.stdout) == {}


# ----- window periods and multiple windows (review findings F2 and F4) -----------


def test_a_window_that_resets_warns_again_in_the_same_session(guard, dirs, project):
    guard.readings["claude"] = reading("claude", 99.5, name="five_hour", resets_at="2026-10-01T12:00:00Z")
    assert run(guard, dirs, "claude", payload("claude", "tool", project)) is not None
    assert run(guard, dirs, "claude", payload("claude", "stop", project)) is not None
    guard.readings["claude"] = reading("claude", 10, name="five_hour", resets_at="2026-10-01T17:00:00Z")
    assert run(guard, dirs, "claude", payload("claude", "tool", project)) is None
    guard.readings["claude"] = reading("claude", 99.7, name="five_hour", resets_at="2026-10-01T17:00:00Z")
    again = run(guard, dirs, "claude", payload("claude", "tool", project))
    assert again is not None and "99.7%" in message_of(again)
    assert run(guard, dirs, "claude", payload("claude", "stop", project)) is not None
    assert run(guard, dirs, "claude", payload("claude", "stop", project)) is None


def test_a_new_reset_time_alone_starts_a_new_period(guard, dirs, project):
    guard.readings["codex"] = reading("codex", 100, resets_at="2026-10-04T00:00:00Z")
    assert run(guard, dirs, "codex", payload("codex", "tool", project)) is not None
    guard.readings["codex"] = reading("codex", 100, resets_at="2026-10-11T00:00:00Z")
    assert run(guard, dirs, "codex", payload("codex", "tool", project)) is not None


def test_small_reset_jitter_is_the_same_period(guard, dirs, project):
    guard.readings["claude"] = reading("claude", 99.5, resets_at="2026-10-05T00:00:00Z")
    assert run(guard, dirs, "claude", payload("claude", "tool", project)) is not None
    guard.readings["claude"] = reading("claude", 99.6, resets_at="2026-10-05T00:00:41Z")
    assert run(guard, dirs, "claude", payload("claude", "tool", project)) is None


@pytest.mark.parametrize(("dip", "warns"), [(98.9, False), (95.0, False), (93.9, True)])
def test_hysteresis_keeps_a_wavering_reading_quiet(guard, dirs, project, dip, warns):
    guard.readings["claude"] = reading("claude", 99.0)
    assert run(guard, dirs, "claude", payload("claude", "tool", project)) is not None
    guard.readings["claude"] = reading("claude", dip)
    run(guard, dirs, "claude", payload("claude", "tool", project))
    guard.readings["claude"] = reading("claude", 99.0)
    assert (run(guard, dirs, "claude", payload("claude", "tool", project)) is not None) is warns


def test_low_threshold_still_clears_after_a_reset(guard, dirs, project, monkeypatch):
    monkeypatch.setenv("NEXUS_HANDOFF_THRESHOLD", "1")
    guard.readings["claude"] = reading("claude", 3)
    assert run(guard, dirs, "claude", payload("claude", "tool", project)) is not None
    guard.readings["claude"] = reading("claude", 0)
    run(guard, dirs, "claude", payload("claude", "tool", project))
    guard.readings["claude"] = reading("claude", 2)
    assert run(guard, dirs, "claude", payload("claude", "tool", project)) is not None


def test_every_window_over_the_threshold_gets_its_continuation(guard, dirs, project):
    guard.readings["claude"] = reading(
        "claude", 99.5, name="five_hour",
        extra_windows=[{"name": "weekly", "percent": 90, "resets_at": None, "source": "x"}],
    )
    assert run(guard, dirs, "claude", payload("claude", "tool", project, session="s2")) is not None
    guard.readings["claude"] = reading(
        "claude", 100, name="five_hour",
        extra_windows=[{"name": "weekly", "percent": 100, "resets_at": None, "source": "x"}],
    )
    assert run(guard, dirs, "claude", payload("claude", "tool", project, session="s2")) is not None
    stops = [run(guard, dirs, "claude", payload("claude", "stop", project, session="s2")) for _ in range(4)]
    named = [message_of(s).split(" usage is")[0].rsplit(" ", 1)[-1] for s in stops if s]
    assert sorted(named) == ["five_hour", "weekly"]


def test_no_state_file_is_written_while_usage_is_low(guard, dirs, project, env):
    guard.readings["claude"] = reading("claude", 40)
    for kind in ("prompt", "tool", "stop"):
        assert run(guard, dirs, "claude", payload("claude", kind, project)) is None
    assert not (env / "state" / "usage-guard").exists()
