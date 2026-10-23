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

    real_probe = module._load_probe()
    monkeypatch.setattr(real_probe, "probe", probe)
    monkeypatch.setattr(module, "_load_probe", lambda: real_probe)
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
    output = guard.evaluate(body, time.monotonic(), dirs[platform])
    # Simulate the agent claiming this context before its next hook. This is
    # a private transport fixture, not evidence of a rendered host question.
    if output is not None:
        decision = guard.pending_decision(platform, body)
        if decision is not None and decision["delivery"]["state"] == "offered":
            guard.decision_transition(platform, Path(decision["project"]), decision["id"],
                                      "claim", tool="private-transport-fixture")
    return output


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
    body = payload(platform, kind, project)
    output = run(guard, dirs, platform, body)
    message = guard.decision_directive(guard.pending_decision(platform, body), guard.directive(
        platform, {"name": "weekly", "percent": 99.2, "resets_at": "2026-10-05T00:00:00Z"}))
    assert output == expected_shape(platform, kind, message)


@pytest.mark.parametrize("platform", PLATFORMS)
def test_second_tool_call_in_the_same_session_is_silent(guard, dirs, project, platform):
    guard.readings[platform] = reading(platform, 100)
    assert run(guard, dirs, platform, payload(platform, "tool", project)) is not None
    assert run(guard, dirs, platform, payload(platform, "tool", project)) is None
    if "prompt" in EVENTS[platform]:
        assert run(guard, dirs, platform, payload(platform, "prompt", project)) is None


@pytest.mark.parametrize("platform", PLATFORMS)
def test_a_new_session_reuses_the_pending_decision(guard, dirs, project, platform):
    guard.readings[platform] = reading(platform, 100)
    assert run(guard, dirs, platform, payload(platform, "tool", project, session="a")) is not None
    assert run(guard, dirs, platform, payload(platform, "tool", project, session="b")) is None


@pytest.mark.parametrize("platform", PLATFORMS)
def test_stop_does_not_duplicate_an_existing_question(guard, dirs, project, platform):
    guard.readings[platform] = reading(platform, 99.5)
    assert run(guard, dirs, platform, payload(platform, "tool", project)) is not None
    for _ in range(5):
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
def test_a_prior_hook_flag_does_not_duplicate_the_question(
    guard, dirs, project, platform, flag
):
    # The completion gate blocks every chained turn, so the flag is set even
    # though this guard never continued. Regression for review finding F1.
    guard.readings[platform] = reading(platform, 100)
    assert run(guard, dirs, platform, payload(platform, "tool", project)) is not None
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
def test_additional_window_at_flagged_stop_reuses_the_question(
    guard, dirs, project, platform, flag
):
    # Our continuation for five_hour caused the flagged turn end, so weekly is
    # not continued there; it must still be announced, not silently recorded.
    guard.readings[platform] = reading(platform, 99.5, name="five_hour")
    body = payload(platform, "stop", project)
    assert run(guard, dirs, platform, body) is not None
    ident = guard.pending_decision(platform, body)["id"]
    guard.readings[platform] = reading(platform, 100, name="five_hour",
        extra_windows=[{"name": "weekly", "percent": 100, "resets_at": None}])
    assert run(guard, dirs, platform, payload(platform, "stop", project, **flag)) is None
    assert run(guard, dirs, platform, payload(platform, "tool", project)) is None
    assert guard.pending_decision(platform, body)["id"] == ident


@pytest.mark.parametrize("platform", PLATFORMS)
def test_stop_loop_is_bounded_over_many_turn_ends(guard, dirs, project, platform):
    guard.readings[platform] = reading(platform, 100)
    outputs = [run(guard, dirs, platform, payload(platform, "stop", project)) for _ in range(25)]
    assert sum(1 for o in outputs if o is not None) == 1


# The handoff is a prompt printed in the chat, so the only handoff evidence a hook
# can read is the user's `handoff` answer in .nexus-hub/usage-decision.json.


def _write_legacy_handoff_file(project: Path, stamp: float, trigger: str) -> None:
    path = project / ".nexus-hub" / "handoff.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"# Handoff | {_iso(stamp)} | claude | {trigger}\n\n## Goal\n", encoding="utf-8")


@pytest.mark.parametrize("platform", PLATFORMS)
def test_a_handoff_answer_newer_than_the_trigger_suppresses_the_stop(guard, dirs, project, platform):
    guard.readings[platform] = reading(platform, 100)
    run(guard, dirs, platform, payload(platform, "tool", project))
    _write_decision(project, "handoff", time.time() + 1)
    assert run(guard, dirs, platform, payload(platform, "stop", project)) is None


@pytest.mark.parametrize("trigger", ["usage-limit weekly 100", "checkpoint", "manual"])
def test_a_handoff_file_is_never_evidence(guard, dirs, project, trigger):
    guard.readings["claude"] = reading("claude", 100)
    body = payload("claude", "tool", project)
    assert run(guard, dirs, "claude", body)
    before = guard.pending_decision("claude", body)
    _write_legacy_handoff_file(project, time.time() + 1, trigger)
    assert guard.usage_limit_handoff_time("claude", body) is None
    assert run(guard, dirs, "claude", payload("claude", "stop", project)) is None
    assert guard.pending_decision("claude", body) == before


@pytest.mark.parametrize("decision", ["pending", "credits", "wait"])
def test_only_a_handoff_answer_counts_as_a_handoff(guard, project, decision):
    body = payload("claude", "stop", project)
    _write_decision(project, decision, time.time() - 5)
    assert guard.usage_limit_handoff_time("claude", body) is None
    stamp = time.time() - 5
    _write_decision(project, "handoff", stamp)
    assert guard.usage_limit_handoff_time("claude", body) == pytest.approx(int(stamp), abs=1)


def test_a_future_dated_handoff_answer_is_ignored(guard, dirs, project):
    guard.readings["claude"] = reading("claude", 100)
    body = payload("claude", "tool", project)
    assert run(guard, dirs, "claude", body)
    _write_decision(project, "handoff", time.time() + 24 * 3600)
    assert guard.usage_limit_handoff_time("claude", body) is None
    assert guard.pending_decision("claude", body)["decision"] == "pending"
    assert run(guard, dirs, "claude", payload("claude", "stop", project)) is None


def test_a_handoff_answer_within_the_clock_skew_allowance_still_counts(guard, dirs, project):
    guard.readings["claude"] = reading("claude", 100)
    run(guard, dirs, "claude", payload("claude", "tool", project))
    _write_decision(project, "handoff", time.time() + 60)
    assert run(guard, dirs, "claude", payload("claude", "stop", project)) is None


def test_a_handoff_answer_older_than_the_trigger_does_not_suppress(guard, dirs, project):
    guard.readings["claude"] = reading("claude", 100)
    _write_decision(project, "handoff", time.time() - 3600)
    body = payload("claude", "tool", project)
    assert run(guard, dirs, "claude", body)
    assert guard.pending_decision("claude", body)["decision"] == "pending"


def test_a_handoff_answer_in_the_repository_root_is_found_from_a_subdirectory(guard, dirs, project):
    sub = project / "src" / "pkg"
    sub.mkdir(parents=True)
    guard.readings["codex"] = reading("codex", 100)
    run(guard, dirs, "codex", payload("codex", "tool", sub))
    _write_decision(project, "handoff", time.time() + 1)
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
    guard.readings["claude"] = reading("claude", 99.1, name="five_hour",
        extra_windows=[{"name": "weekly", "percent": 99.9, "resets_at": None}])
    out = run(guard, dirs, "claude", payload("claude", "tool", project))
    assert "weekly usage is at 99.9%" in message_of(out)


def test_a_second_window_crossing_later_reuses_the_question(guard, dirs, project):
    guard.readings["claude"] = reading("claude", 100, name="five_hour")
    assert run(guard, dirs, "claude", payload("claude", "tool", project)) is not None
    guard.readings["claude"] = reading("claude", 100, name="weekly")
    assert run(guard, dirs, "claude", payload("claude", "tool", project)) is None


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

    monkeypatch.setattr(guard._load_probe(), "probe", slow_probe)
    started = time.monotonic()
    assert run(guard, dirs, "claude", payload("claude", "tool", project)) is None
    assert time.monotonic() - started < 1.2


def test_a_probe_that_raises_is_silent(guard, dirs, project, monkeypatch):
    def broken(platform: str) -> FakeResult:
        raise RuntimeError("boom")

    monkeypatch.setattr(guard._load_probe(), "probe", broken)
    assert run(guard, dirs, "claude", payload("claude", "tool", project)) is None


def test_unwritable_state_never_repeats_the_prompt(guard, dirs, project, env):
    (env / "state").mkdir(parents=True)
    (env / "state" / "usage-guard").write_text("not a directory", encoding="utf-8")
    guard.readings["claude"] = reading("claude", 100)
    for kind in ("tool", "tool", "stop", "stop"):
        assert run(guard, dirs, "claude", payload("claude", kind, project)) is None


def test_held_lock_makes_the_hook_silent(guard, dirs, project, env, monkeypatch):
    guard.readings["claude"] = reading("claude", 100)
    with guard._load_probe().ActivityLock(adopter=True) as activity:
        assert activity.held
        assert run(guard, dirs, "claude", payload("claude", "tool", project)) is None


def test_old_lock_timestamp_does_not_steal_os_ownership(guard, dirs, project, env):
    guard.readings["claude"] = reading("claude", 100)
    with guard._load_probe().ActivityLock(adopter=True) as activity:
        lock = env / "state" / "usage-probe" / "activity.lock"
        os.utime(lock, (time.time() - 3600, time.time() - 3600))
        assert run(guard, dirs, "claude", payload("claude", "tool", project)) is None
    assert run(guard, dirs, "claude", payload("claude", "tool", project)) is not None


def test_state_file_records_the_trigger(guard, dirs, project, env):
    guard.readings["codex"] = reading("codex", 99.3)
    body = payload("codex", "tool", project, session="sess-42")
    run(guard, dirs, "codex", body)
    state = guard.pending_decision("codex", body)
    assert state["schema"] == 3 and state["decision"] == "pending"
    assert state["confirmed_usage"][0]["percent"] == 99.3
    assert state["project"] == str(project.resolve())
    assert state["delivery"]["state"] == "claimed"


def test_unusual_session_ids_become_a_hashed_filename(guard, dirs, project, env):
    guard.readings["claude"] = reading("claude", 100)
    run(guard, dirs, "claude", payload("claude", "tool", project, session="../../etc/x y"))
    names = [p.name for p in (env / "state" / "usage-guard" / "decisions").iterdir()]
    assert len(names) == 1 and len(names[0]) == 64 + len(".json")
    assert ".." not in names[0]


def test_legacy_session_state_is_preserved(guard, dirs, project, env):
    state = env / "state" / "usage-guard"
    state.mkdir(parents=True)
    old_file = state / "claude-old.json"
    old_file.write_text("{}", encoding="utf-8")
    os.utime(old_file, (time.time() - 8 * 24 * 3600,) * 2)
    guard.readings["claude"] = reading("claude", 100)
    run(guard, dirs, "claude", payload("claude", "tool", project))
    assert old_file.read_text() == "{}", "new owner preserves legacy state"


# ----- message content and leaks -------------------------------------------------


def test_directive_wording(guard):
    text = guard.directive("codex", {"name": "weekly", "percent": 99.0, "resets_at": None})
    assert text.startswith("Usage limit: Codex weekly usage is at 99%")
    assert "unknown (do not guess)" in text
    assert "cannot read pay-per-use credits here" in text
    assert text.isascii()


WEEKLY = {"name": "weekly", "percent": 100.0, "resets_at": "2026-10-13T14:00:00Z"}


@pytest.mark.parametrize(
    ("credit", "expected"),
    [
        (
            {"state": "capped", "percent": 12.5, "used": 62.5, "limit": 500.0, "unit": "USD"},
            ["credits used so far: $62.50 of $500.00 (12.5%)", "at 50%, 75%, and 90% of the allowance"],
        ),
        (
            {"state": "uncapped", "percent": None, "used": 120.0, "limit": None, "unit": "USD"},
            ["no spending cap ($120.00 this period)", "every $50.00 spent", "credit-reminders.json"],
        ),
        (
            {"state": "uncapped", "percent": None, "used": None, "limit": None, "unit": "USD"},
            ["no spending cap", "it will not remind them"],
        ),
        (
            {"state": "none", "percent": None, "used": 0.0, "limit": 0.0, "unit": "USD"},
            ["no pay-per-use credits (disabled, or a zero allowance)", "will fail until the window resets (resets 2026-10-13T14:00:00Z)", "enables credits"],
        ),
        (
            {"state": "exhausted", "percent": 100.0, "used": 500.0, "limit": 500.0, "unit": "USD"},
            ["already used up ($500.00 of $500.00 (100%))", "raises the limit"],
        ),
        (
            {"state": "capped", "percent": 16.49, "used": 824.5, "limit": 5000.0, "unit": "credit"},
            ["824.5 credits of 5,000 credits (16.5%)"],
        ),
    ],
)
def test_directive_describes_each_credit_state(guard, credit, expected):
    text = guard.directive("claude", WEEKLY, credit, 50.0, False)
    for phrase in expected:
        assert phrase in text
    assert text.isascii() and " - " not in text


def test_the_step_applies_under_a_cap_only_when_enabled(guard):
    capped = {"state": "capped", "percent": 10.0, "used": 50.0, "limit": 500.0, "unit": "USD"}
    assert "every $25.00 spent" not in guard.directive("claude", WEEKLY, capped, 25.0, False)
    assert "every $25.00 spent" in guard.directive("claude", WEEKLY, capped, 25.0, True)


# ----- ask first: credits or handoff (v4.13.11) ----------------------------------


def _write_decision(project: Path, decision: str, stamp: float, **extra: Any) -> None:
    path = project / ".nexus-hub" / "usage-decision.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"decision": decision, "recorded_at": _iso(stamp), **extra}), encoding="utf-8")


def _credits(
    percent: float | None = None,
    state: str = "capped",
    used: float | None = None,
    limit: float | None = 500.0,
    unit: str = "USD",
) -> list[dict[str, Any]]:
    if used is None and percent is not None and limit:
        used = percent * limit / 100
    return [{
        "name": "extra_credits", "percent": percent, "resets_at": None, "source": "fixture",
        "state": state, "used": used, "limit": limit, "unit": unit,
    }]


def _approve(guard, dirs, project, extra: list[dict[str, Any]], session: str = "s-1") -> None:
    guard.readings["claude"] = reading("claude", 100, extra_windows=extra)
    assert run(guard, dirs, "claude", payload("claude", "tool", project, session=session)) is not None
    _answer_fixture(guard, project, "credits")
    assert run(guard, dirs, "claude", payload("claude", "tool", project, session=session)) is None



def _answer_fixture(guard, project, decision, platform="claude"):
    """Private host-ID fixtures; never evidence of a real rendered interaction."""
    body = payload(platform, "tool", project)
    state = guard.pending_decision(platform, body)
    claim = guard.decision_transition(platform, project, state["id"], "claim", tool="fixture-native")
    token = claim["decision"]["delivery"]["claim_id"]
    guard.decision_transition(platform, project, state["id"], "delivered", claim_id=token,
                             request_id="private-fixture-request")
    return guard.decision_transition(platform, project, state["id"], "answer", claim_id=token,
                                    request_id="private-fixture-request", response_id="private-fixture-response",
                                    answer=decision)


def _write_settings(env: Path, **providers: dict[str, Any]) -> None:
    path = env / "config" / "credit-reminders.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"providers": providers}), encoding="utf-8")


@pytest.mark.parametrize("platform", PLATFORMS)
@pytest.mark.parametrize("decision", ["pending", "credits", "wait", "handoff"])
def test_a_recorded_answer_suppresses_the_turn_end_continuation(guard, dirs, project, platform, decision):
    guard.readings[platform] = reading(platform, 100)
    body = payload(platform, "tool", project)
    assert run(guard, dirs, platform, body)
    if decision != "pending":
        _answer_fixture(guard, project, decision, platform)
    assert run(guard, dirs, platform, payload(platform, "stop", project)) is None
    assert guard.pending_decision(platform, body)["decision"] == decision


def test_an_answer_older_than_the_question_does_not_count(guard, dirs, project):
    guard.readings["claude"] = reading("claude", 100)
    _write_decision(project, "credits", time.time() - 3600)
    body = payload("claude", "tool", project)
    assert run(guard, dirs, "claude", body)
    assert guard.pending_decision("claude", body)["decision"] == "pending"


@pytest.mark.parametrize(
    "body",
    [
        {"decision": "credits", "recorded_at": "2099-01-01T00:00:00Z"},
        {"decision": "yes", "recorded_at": "NOW"},
        {"decision": ["credits"], "recorded_at": "NOW"},
        {"decision": "credits", "recorded_at": "NOW", "platform": "codex"},
        {"decision": "credits"},
    ],
)
def test_a_malformed_or_foreign_answer_is_ignored(guard, dirs, project, body):
    guard.readings["claude"] = reading("claude", 100)
    current = payload("claude", "tool", project)
    assert run(guard, dirs, "claude", current)
    before = guard.pending_decision("claude", current)
    if body.get("recorded_at") == "NOW":
        body = {**body, "recorded_at": _iso(time.time() + 1)}
    path = project / ".nexus-hub" / "usage-decision.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(body), encoding="utf-8")
    assert run(guard, dirs, "claude", payload("claude", "stop", project)) is None
    assert guard.pending_decision("claude", current) == before


def test_a_credits_answer_is_remembered_by_later_sessions(guard, dirs, project):
    guard.readings["claude"] = reading("claude", 100)
    assert run(guard, dirs, "claude", payload("claude", "tool", project, session="a"))
    _answer_fixture(guard, project, "credits")
    for kind in ("prompt", "tool", "stop"):
        assert run(guard, dirs, "claude", payload("claude", kind, project, session="b")) is None
    assert guard.pending_decision("claude", payload("claude", "stop", project))["decision"] == "credits"


def test_a_pending_answer_is_not_an_approval(guard, dirs, project):
    guard.readings["claude"] = reading("claude", 100)
    assert run(guard, dirs, "claude", payload("claude", "tool", project, session="a"))
    assert run(guard, dirs, "claude", payload("claude", "tool", project, session="b")) is None
    assert guard.pending_decision("claude", payload("claude", "stop", project))["decision"] == "pending"


def test_directive_asks_once_as_an_interactive_three_way_choice(guard):
    text = guard.decision_directive({"id": "private-fixture"}, "Usage limit: fixture.")
    assert "functions.request_user_input_async" in text
    assert "Wait for reset (Recommended), Hand off, Continue on credits" in text
    assert "Never preselect credits" in text
    assert "one concise text question" in text
    assert "do not retry or fall back" in text
    assert text.isascii()


def test_spend_directive_reports_facts_without_another_question(guard):
    credit = {"state": "capped", "percent": 60.0, "used": 300.0, "limit": 500.0, "unit": "USD"}
    text = guard.spend_directive("claude", credit)
    assert "$300.00" in text and "existing choice remains recorded" in text
    assert "do not ask a duplicate question" in text
    assert "AskUserQuestion" not in text and text.isascii()


@pytest.mark.parametrize("platform", PLATFORMS)
def test_an_open_question_is_never_asked_again_across_automatic_continuations(guard, dirs, project, platform):
    """One ask per open decision, however many Stop hooks or goals continue the turn."""
    guard.readings[platform] = reading(platform, 100)
    assert run(guard, dirs, platform, payload(platform, "tool", project)) is not None
    _write_decision(project, "pending", time.time() + 1)
    for prior in (False, True, False, True):
        flag = {"loop_count": 1 if prior else 0} if platform == "cursor" else {"stop_hook_active": prior}
        assert run(guard, dirs, platform, payload(platform, "stop", project, **flag)) is None
        assert run(guard, dirs, platform, payload(platform, "tool", project)) is None
        assert run(guard, dirs, platform, payload(platform, "prompt", project)) is None
    assert not guard.approval_path(platform).exists()


def test_an_approval_ends_when_the_window_moves_to_a_new_period(guard, dirs, project):
    guard.readings["claude"] = reading("claude", 100)
    run(guard, dirs, "claude", payload("claude", "tool", project, session="a"))
    _answer_fixture(guard, project, "credits")
    run(guard, dirs, "claude", payload("claude", "tool", project, session="a"))
    guard.readings["claude"] = reading("claude", 100, resets_at="2026-10-12T00:00:00Z")
    assert run(guard, dirs, "claude", payload("claude", "tool", project, session="b")) is not None


def test_credit_reminders_fire_once_per_tier_and_never_at_turn_end(guard, dirs, project):
    guard.readings["claude"] = reading("claude", 100, extra_windows=_credits(10))
    first = run(guard, dirs, "claude", payload("claude", "tool", project))
    assert "credits used so far: $50.00 of $500.00 (10%)" in message_of(first)
    _answer_fixture(guard, project, "credits")
    assert run(guard, dirs, "claude", payload("claude", "tool", project)) is None
    seen = []
    for percent in (30, 49.9, 50, 60, 74, 80, 85, 92, 99):
        guard.readings["claude"] = reading("claude", 100, extra_windows=_credits(percent))
        assert run(guard, dirs, "claude", payload("claude", "stop", project)) is None
        output = run(guard, dirs, "claude", payload("claude", "tool", project))
        if output is not None:
            text = message_of(output)
            assert text.startswith("Usage credits: Claude Code pay-per-use credits used so far:")
            assert text.isascii()
            seen.append(percent)
    assert seen == [50, 80, 92]


def test_a_jump_past_several_tiers_asks_once(guard, dirs, project):
    guard.readings["claude"] = reading("claude", 100, extra_windows=_credits(5))
    run(guard, dirs, "claude", payload("claude", "tool", project))
    _answer_fixture(guard, project, "credits")
    run(guard, dirs, "claude", payload("claude", "tool", project))
    guard.readings["claude"] = reading("claude", 100, extra_windows=_credits(95))
    assert run(guard, dirs, "claude", payload("claude", "tool", project)) is not None
    assert run(guard, dirs, "claude", payload("claude", "tool", project, session="other")) is None


def test_tiers_already_passed_at_approval_are_not_asked_again(guard, dirs, project):
    guard.readings["claude"] = reading("claude", 100, extra_windows=_credits(60))
    run(guard, dirs, "claude", payload("claude", "tool", project))
    _answer_fixture(guard, project, "credits")
    assert run(guard, dirs, "claude", payload("claude", "tool", project)) is None
    guard.readings["claude"] = reading("claude", 100, extra_windows=_credits(70))
    assert run(guard, dirs, "claude", payload("claude", "tool", project)) is None
    guard.readings["claude"] = reading("claude", 100, extra_windows=_credits(75))
    assert run(guard, dirs, "claude", payload("claude", "tool", project)) is not None


def test_a_credit_window_alone_never_triggers_the_usage_limit(guard, dirs, project):
    guard.readings["claude"] = reading("claude", 10, extra_windows=_credits(100))
    for kind in ("prompt", "tool", "stop"):
        assert run(guard, dirs, "claude", payload("claude", kind, project)) is None


def test_usage_limit_stop_time_counts_a_pending_question(guard, project):
    body = payload("claude", "stop", project)
    assert guard.usage_limit_stop_time("claude", body) is None
    stamp = time.time() - 5
    _write_decision(project, "pending", stamp)
    assert guard.usage_limit_stop_time("claude", body) == pytest.approx(int(stamp), abs=1)
    _write_decision(project, "wait", stamp)
    assert guard.usage_limit_stop_time("claude", body) == pytest.approx(int(stamp), abs=1)
    _write_decision(project, "handoff", stamp)
    assert guard.usage_limit_stop_time("claude", body) == pytest.approx(int(stamp), abs=1)
    _write_decision(project, "credits", time.time() - 5)
    assert guard.usage_limit_stop_time("claude", body) is None


def test_uncapped_credits_remind_every_step_of_spend(guard, dirs, project):
    _approve(guard, dirs, project, _credits(state="uncapped", used=20.0, limit=None))
    seen = []
    for used in (30, 49.99, 50, 60, 99, 100, 175, 180):
        guard.readings["claude"] = reading(
            "claude", 100, extra_windows=_credits(state="uncapped", used=used, limit=None)
        )
        assert run(guard, dirs, "claude", payload("claude", "stop", project)) is None
        output = run(guard, dirs, "claude", payload("claude", "tool", project))
        if output is not None:
            assert f"${used:,.2f} this period" in message_of(output)
            seen.append(used)
    assert seen == [50, 100, 175]


def test_the_step_comes_from_the_settings_file(guard, dirs, project, env):
    _write_settings(env, claude={"step": 100, "when_capped": False})
    _approve(guard, dirs, project, _credits(state="uncapped", used=10.0, limit=None))
    guard.readings["claude"] = reading("claude", 100, extra_windows=_credits(state="uncapped", used=60.0, limit=None))
    assert run(guard, dirs, "claude", payload("claude", "tool", project)) is None
    guard.readings["claude"] = reading("claude", 100, extra_windows=_credits(state="uncapped", used=101.0, limit=None))
    output = run(guard, dirs, "claude", payload("claude", "tool", project))
    assert output is not None and "every $100.00 spent" in message_of(output)


def test_a_zero_step_turns_spend_reminders_off(guard, dirs, project, env):
    _write_settings(env, claude={"step": 0})
    _approve(guard, dirs, project, _credits(state="uncapped", used=10.0, limit=None))
    guard.readings["claude"] = reading("claude", 100, extra_windows=_credits(state="uncapped", used=900.0, limit=None))
    assert run(guard, dirs, "claude", payload("claude", "tool", project)) is None


@pytest.mark.parametrize("bad", [{"step": -5}, {"step": "50"}, {"step": True}, {"step": 1e12}, "junk"])
def test_invalid_settings_fall_back_to_the_default_step(guard, env, bad):
    _write_settings(env, claude=bad)
    assert guard.reminder_settings("claude") == (50.0, False)
    assert guard.reminder_settings("codex") == (500.0, False)
    assert guard.reminder_settings("copilot") == (0.0, False)


def test_a_capped_allowance_uses_the_step_too_when_enabled(guard, dirs, project, env):
    _write_settings(env, claude={"step": 100, "when_capped": True})
    _approve(guard, dirs, project, _credits(4))  # $20 of $500
    seen = []
    for used in (90, 110, 150, 210, 250, 260):
        guard.readings["claude"] = reading("claude", 100, extra_windows=_credits(used / 5))
        if run(guard, dirs, "claude", payload("claude", "tool", project)) is not None:
            seen.append(used)
    assert seen == [110, 210, 250]  # $100 and $200 steps, then the 50% tier


def test_running_out_of_credits_is_announced_once(guard, dirs, project):
    _approve(guard, dirs, project, _credits(95))
    exhausted = _credits(100.0, state="exhausted")
    guard.readings["claude"] = reading("claude", 100, extra_windows=exhausted)
    output = run(guard, dirs, "claude", payload("claude", "tool", project))
    text = message_of(output)
    assert "are used up" in text and "raise the limit" in text and "further requests will fail" in text
    for kind in ("tool", "tool", "stop"):
        assert run(guard, dirs, "claude", payload("claude", kind, project)) is None
    guard.readings["claude"] = reading("claude", 100, extra_windows=_credits(10))
    run(guard, dirs, "claude", payload("claude", "tool", project))
    guard.readings["claude"] = reading("claude", 100, extra_windows=exhausted)
    assert run(guard, dirs, "claude", payload("claude", "tool", project)) is not None


@pytest.mark.parametrize("state", ["none", "exhausted"])
def test_no_usable_credits_say_continuing_will_fail(guard, dirs, project, state):
    guard.readings["claude"] = reading("claude", 100, extra_windows=_credits(100.0 if state == "exhausted" else None, state=state, limit=0.0 if state == "none" else 500.0))
    text = message_of(run(guard, dirs, "claude", payload("claude", "tool", project)))
    assert "will fail" in text and "waiting for the reset" in text


def test_a_wait_answer_is_not_an_approval(guard, dirs, project):
    guard.readings["claude"] = reading("claude", 100)
    body = payload("claude", "tool", project)
    assert run(guard, dirs, "claude", body)
    _answer_fixture(guard, project, "wait")
    assert run(guard, dirs, "claude", payload("claude", "stop", project)) is None
    assert guard.pending_decision("claude", body)["decision"] == "wait"
    assert not guard.approval_path("claude").exists()


@pytest.mark.parametrize("window", [{"state": "bogus"}, {"unit": "US Dollars!"}, {"unit": None}])
def test_a_malformed_credit_reading_counts_as_unknown(guard, window):
    data = reading("claude", 100, extra_windows=[{**_credits(10)[0], **window}])
    assert guard.spend_info(data, time.time()) is None


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
    assert outputs[0] is not None and outputs[2] is None
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
        assert (output is not None) is (index == 0)
        if index == 0:
            state = module.pending_decision("claude", body)
            module.decision_transition("claude", project, state["id"], "claim", tool="private-latency-fixture")
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


def _claim_wrapper_fixture(home: Path, project: Path, platform: str, script: Path) -> None:
    """An actual CLI delivery claim in a private wrapper fixture; no UI evidence."""
    module = _load_guard()
    state = module.pending_decision(platform, payload(platform, "tool", project))
    assert state is not None
    result = subprocess.run([sys.executable, "-I", "-B", str(script), "--decision-action", "claim",
        "--project", str(project), "--platform", platform, "--decision-id", state["id"],
        "--tool", "private-wrapper-fixture"], capture_output=True, text=True,
        env=_subprocess_env(home), timeout=10)
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)["claimed"] is True


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
    _claim_wrapper_fixture(env, project, "claude", hooks / "usage-guard.py")
    assert call("tool").stdout == ""
    assert call("stop").stdout == ""
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
    _claim_wrapper_fixture(env, project, "cursor", hooks / "usage-guard.py")
    assert json.loads(call("tool").stdout) == {}
    # loop_count from another hook's follow-up does not suppress this guard.
    stop = json.loads(call("stop", loop_count=1).stdout)
    assert stop == {}
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
    _claim_wrapper_fixture(env, project, "copilot", scripts / "usage-guard.py")
    stop = json.loads(call("Stop", stop_hook_active=True).stdout)
    assert stop == {}
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


def test_reset_does_not_duplicate_an_unanswered_question(guard, dirs, project):
    guard.readings["claude"] = reading("claude", 99.5, name="five_hour", resets_at="2026-10-01T12:00:00Z")
    body = payload("claude", "tool", project)
    assert run(guard, dirs, "claude", body)
    ident = guard.pending_decision("claude", body)["id"]
    guard.readings["claude"] = reading("claude", 10, name="five_hour", resets_at="2026-10-01T17:00:00Z")
    assert run(guard, dirs, "claude", body) is None
    guard.readings["claude"] = reading("claude", 99.7, name="five_hour", resets_at="2026-10-01T17:00:00Z")
    assert run(guard, dirs, "claude", body) is None
    assert guard.pending_decision("claude", body)["id"] == ident


def test_a_new_reset_time_alone_starts_a_new_period(guard, dirs, project):
    guard.readings["codex"] = reading("codex", 100, resets_at="2026-10-04T00:00:00Z")
    body = payload("codex", "tool", project)
    assert run(guard, dirs, "codex", body)
    ident = guard.pending_decision("codex", body)["id"]
    _answer_fixture(guard, project, "credits", "codex")
    guard.readings["codex"] = reading("codex", 100, resets_at="2026-10-11T00:00:00Z")
    assert run(guard, dirs, "codex", body)
    assert guard.pending_decision("codex", body)["id"] != ident


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
    assert run(guard, dirs, "claude", payload("claude", "tool", project)) is None


def test_low_threshold_still_clears_after_a_reset(guard, dirs, project, monkeypatch):
    monkeypatch.setenv("NEXUS_HANDOFF_THRESHOLD", "1")
    body = payload("claude", "tool", project)
    guard.readings["claude"] = reading("claude", 3)
    assert run(guard, dirs, "claude", body)
    ident = guard.pending_decision("claude", body)["id"]
    guard.readings["claude"] = reading("claude", 0)
    assert run(guard, dirs, "claude", body) is None
    guard.readings["claude"] = reading("claude", 2)
    assert run(guard, dirs, "claude", body) is None
    assert guard.pending_decision("claude", body)["id"] == ident


def test_additional_crossing_windows_never_duplicate_pending_delivery(guard, dirs, project):
    guard.readings["claude"] = reading("claude", 99.5, name="five_hour")
    body = payload("claude", "tool", project)
    assert run(guard, dirs, "claude", body)
    guard.readings["claude"] = reading("claude", 100, name="five_hour",
        extra_windows=[{"name": "weekly", "percent": 100, "resets_at": None}])
    assert run(guard, dirs, "claude", body) is None
    for _ in range(4):
        assert run(guard, dirs, "claude", payload("claude", "stop", project)) is None


def test_no_state_file_is_written_while_usage_is_low(guard, dirs, project, env):
    guard.readings["claude"] = reading("claude", 40)
    for kind in ("prompt", "tool", "stop"):
        assert run(guard, dirs, "claude", payload("claude", kind, project)) is None
    assert not (env / "state" / "usage-guard").exists()


@pytest.mark.parametrize("platform", ["claude", "codex", "cursor"])
def test_pending_stop_preserves_the_later_credit_answer(guard, dirs, project, monkeypatch, platform):
    started = int(time.time())
    clock = [started]
    monkeypatch.setattr(guard.time, "time", lambda: clock[0])
    reset = _iso(started + 3600)
    guard.readings[platform] = reading(platform, 100, resets_at=reset, extra_windows=_credits(10))
    assert run(guard, dirs, platform, payload(platform, "tool", project, session="ask")) is not None
    _write_decision(project, "pending", started + 1)
    clock[0] = started + 2
    assert run(guard, dirs, platform, payload(platform, "stop", project, session="ask")) is None
    _answer_fixture(guard, project, "credits", platform)
    clock[0] = started + 4
    assert run(guard, dirs, platform, payload(platform, CONTEXT_KINDS[platform][0], project, session="ask")) is None
    approval = guard.pending_decision(platform, payload(platform, "tool", project))["approval"]
    assert approval["windows"]["weekly"] == reset
    clock[0] = started + 5
    assert run(guard, dirs, platform, payload(platform, "tool", project, session="later")) is None
    guard.readings[platform] = reading(platform, 100, resets_at=reset, extra_windows=_credits(50))
    assert "Usage credits:" in message_of(run(guard, dirs, platform, payload(platform, "tool", project, session="later")))


@pytest.mark.parametrize("platform", ["claude", "codex", "cursor"])
@pytest.mark.parametrize("decision", ["wait", "handoff"])
def test_reminder_does_not_allow_replayed_answer_to_replace_choice(guard, dirs, project, monkeypatch, platform, decision):
    guard.readings[platform] = reading(platform, 100, extra_windows=_credits(10))
    assert run(guard, dirs, platform, payload(platform, "tool", project))
    _answer_fixture(guard, project, "credits", platform)
    before = guard.pending_decision(platform, payload(platform, "tool", project))
    with pytest.raises(ValueError):
        _answer_fixture(guard, project, decision, platform)
    assert guard.pending_decision(platform, payload(platform, "tool", project)) == before


@pytest.mark.parametrize("platform", ["claude", "codex", "cursor"])
def test_provider_reminder_file_takes_precedence_over_shared_legacy_settings(guard, env, platform):
    _write_settings(env, **{platform: {"step": 100, "when_capped": False}})
    provider_file = env / "config" / f"credit-reminders-{platform}.json"
    provider_file.write_text(json.dumps({"providers": {platform: {"step": 0, "when_capped": True}}}), encoding="utf-8")
    assert guard.reminder_settings(platform) == (0.0, True)


@pytest.mark.parametrize("platform", ["claude", "codex", "cursor"])
def test_malformed_provider_reminder_file_retains_shared_legacy_settings(guard, env, platform):
    _write_settings(env, **{platform: {"step": 100, "when_capped": True}})
    (env / "config" / f"credit-reminders-{platform}.json").write_text("{not json", encoding="utf-8")
    assert guard.reminder_settings(platform) == (100.0, True)
