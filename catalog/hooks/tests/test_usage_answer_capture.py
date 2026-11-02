"""Submitted usage answers must end the interruption without agent CLI writes."""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Event

import pytest

from catalog.hooks.tests.test_usage_native_decision import offer

pytest_plugins = ("catalog.hooks.tests.test_usage_native_decision",)


@pytest.mark.parametrize("platform,tool", [
    ("claude", "AskUserQuestion"), ("cursor", "AskQuestion"),
    ("codex", "functions.request_user_input"),
])
def test_submitted_tool_answer_ends_interruption(case, platform, tool):
    guard, _, payload, _, _ = case
    if platform == "claude":
        payload.pop("turn_id")
        payload["scratchpad_dir"] = "private-fixture"
    elif platform == "cursor":
        payload.update(cursor_version="test", hook_event_name="postToolUse")
    assert guard.evaluate(payload, time.monotonic())
    data = guard.pending_decision(platform, payload)
    question = f"Usage limit [usage-decision:{data['id']}]: choose how to continue"
    if platform == "codex":
        tool_input = {"questions": [{"id": "usage_" + data["id"], "question": question}]}
        response = {"answers": {"usage_" + data["id"]: {"answers": ["Continue on credits"]}}}
    elif platform == "cursor":
        tool_input = {"questions": [{"id": "usage_" + data["id"], "prompt": question}]}
        response = {"answers": [{"questionId": "usage_" + data["id"], "optionIds": ["credits"]}]}
    else:
        tool_input = {"questions": [{"header": "Usage limit", "question": question}]}
        response = {"answers": {question: "Continue on credits"}}
    answered = dict(payload, tool_name=tool, tool_input=tool_input, tool_use_id="actual-call-1")
    answered["tool_output" if platform == "cursor" else "tool_response"] = (
        json.dumps(response) if platform == "cursor" else response)
    assert guard.evaluate(answered, time.monotonic()) is None
    assert guard.pending_decision(platform, payload)["decision"] == "credits"
    assert guard.evaluate(payload, time.monotonic()) is None
    assert guard.evaluate(dict(payload, hook_event_name="stop" if platform == "cursor" else "Stop"),
                          time.monotonic()) is None


def test_offered_instructions_are_sent_once_and_stop_allows_pending(case):
    guard, _, payload, _, _ = case
    offer(case)
    for _ in range(3):
        assert guard.evaluate(payload, time.monotonic()) is None
        assert guard.evaluate(dict(payload, hook_event_name="Stop"), time.monotonic()) is None


def test_stop_first_blocks_at_most_once(case):
    guard, _, payload, _, _ = case
    payload["hook_event_name"] = "Stop"
    assert guard.evaluate(payload, time.monotonic())["decision"] == "block"
    for _ in range(3):
        assert guard.evaluate(payload, time.monotonic()) is None


def test_stop_hook_active_never_probes_or_blocks(case, monkeypatch):
    guard, _, payload, _, _ = case
    monkeypatch.setattr(guard, "run_probe", lambda *_: pytest.fail("continuation probed"))
    assert guard.evaluate(dict(payload, hook_event_name="Stop", stop_hook_active=True), time.monotonic()) is None


def test_archive_failure_after_reset_cannot_block_same_decision_again(case, monkeypatch):
    guard, _, payload, reading, _ = case
    stop = dict(payload, hook_event_name="Stop")
    assert guard.evaluate(stop, time.monotonic())["decision"] == "block"
    assert guard.evaluate(dict(payload, hook_event_name="UserPromptSubmit", prompt="credits"), time.monotonic()) is None
    reading["windows"][0]["resets_at"] = guard._iso_now(time.time() + 86400)
    monkeypatch.setattr(guard, "archive_answer", lambda *_: False)
    assert guard.evaluate(stop, time.monotonic()) is None
    assert guard.evaluate(stop, time.monotonic()) is None
    assert "history" in json.dumps(guard.evaluate(payload, time.monotonic()))
    assert guard.evaluate(payload, time.monotonic()) is None


@pytest.mark.parametrize("answer,expected", [("credits", "credits"), ("/usage credits", "credits"),
                                           ("wait", "wait"), ("/usage handoff", "handoff")])
def test_prompt_answer_persists_without_probe(case, monkeypatch, answer, expected):
    guard, _, payload, _, _ = case
    offer(case)
    monkeypatch.setattr(guard, "run_probe", lambda *_: pytest.fail("answer must not need usage probe"))
    assert guard.evaluate(dict(payload, hook_event_name="UserPromptSubmit", prompt=answer), time.monotonic()) is None
    assert guard.pending_decision("codex", payload)["decision"] == expected


@pytest.mark.parametrize("answer", ["credits", "wait", "handoff"])
def test_one_answer_survives_probe_lock_contention(case, monkeypatch, answer):
    guard, _, payload, _, home = case
    original = offer(case)
    probe = guard._load_probe()
    monkeypatch.setattr(guard, "run_probe", lambda *_: pytest.fail("answer replay must not probe"))
    with probe.ActivityLock() as activity:
        assert activity.held
        assert guard.evaluate(dict(payload, hook_event_name="UserPromptSubmit", prompt=answer), time.monotonic()) is None
        assert guard.pending_decision("codex", payload)["decision"] == "pending"
        receipt = guard._answer_receipt_path(original["id"])
        assert receipt.is_file() and home not in receipt.parents
    assert guard.evaluate(payload, time.monotonic()) is None
    assert guard.pending_decision("codex", payload)["decision"] == answer
    assert not receipt.exists()


def test_first_receipt_wins_when_capture_races(case, monkeypatch):
    guard, project, payload, _, _ = case
    offer(case)
    paused, resume = Event(), Event()
    original = guard._submitted_answer
    def delayed(data, event):
        answer = original(data, event)
        if event.get("prompt") == "credits":
            paused.set()
            assert resume.wait(5)
        return answer
    monkeypatch.setattr(guard, "_submitted_answer", delayed)
    with ThreadPoolExecutor(max_workers=1) as pool:
        future = pool.submit(guard.capture_answer, "codex", project,
            dict(payload, hook_event_name="UserPromptSubmit", prompt="credits"))
        assert paused.wait(5)
        with guard._load_probe().ActivityLock() as activity:
            assert activity.held
            assert guard.capture_answer("codex", project,
                dict(payload, hook_event_name="UserPromptSubmit", prompt="wait"))
        resume.set()
        assert future.result(timeout=5)
    assert guard.pending_decision("codex", payload)["decision"] == "wait"


@pytest.mark.parametrize("writer", ["recovery", "legacy"])
def test_every_answer_writer_honors_queued_wait(case, writer, capsys):
    guard, project, payload, _, _ = case
    state = offer(case)
    if writer == "legacy":
        claim = guard.decision_transition("codex", project, state["id"], "claim", tool="fixture")
        token = claim["decision"]["delivery"]["claim_id"]
        guard.decision_transition("codex", project, state["id"], "delivered", claim_id=token,
                                  request_id="actual-fixture-request")
    with guard._load_probe().ActivityLock() as activity:
        assert activity.held
        assert guard.capture_answer("codex", project,
            dict(payload, hook_event_name="UserPromptSubmit", prompt="wait"))
    if writer == "recovery":
        assert guard.usage_cli(["decide", "--project", str(project), "--platform", "codex", "--answer", "credits"]) == 1
        assert "already answered: wait" in capsys.readouterr().err
    else:
        with pytest.raises(ValueError, match="already answered: wait"):
            guard.decision_transition("codex", project, state["id"], "answer", claim_id=token,
                request_id="actual-fixture-request", response_id="actual-fixture-response", answer="credits")
    assert guard.pending_decision("codex", payload)["decision"] == "wait"


@pytest.mark.parametrize("alias,subdirectory", [("claude-code", False), ("claude", True)])
def test_legacy_schema_three_identity_still_answers_original_id(case, alias, subdirectory):
    guard, project, _, _, _ = case
    state = guard.offer_warning("claude", project, "legacy-warning")["decision"]
    raw_project = project / "legacy subdirectory" if subdirectory else project
    raw_project.mkdir(exist_ok=True)
    canonical = guard.decision_path("claude", project)
    canonical.unlink()
    state.update(platform=alias, project=str(raw_project))
    legacy = guard._identity_path(alias, raw_project)
    assert guard.save_state(legacy, state)
    assert guard.pending_decision(alias, {}, (raw_project,))["id"] == state["id"]
    claim = guard.decision_transition(alias, raw_project, state["id"], "claim", tool="fixture")
    token = claim["decision"]["delivery"]["claim_id"]
    guard.decision_transition(alias, raw_project, state["id"], "delivered", claim_id=token, request_id="legacy-request")
    guard.decision_transition(alias, raw_project, state["id"], "answer", claim_id=token,
        request_id="legacy-request", response_id="legacy-response", answer="wait")
    answered = guard.pending_decision("claude", {"cwd": str(project)})
    assert answered["decision"] == "wait" and answered["response_id"] == "legacy-response"
    assert canonical.is_file() and not legacy.exists()
    # A stale older reader must not replace the canonical answer with its pending duplicate.
    assert guard.save_state(legacy, state)
    guard.run_probe = lambda *_: {"status": "ok", "fetched_at": guard._iso_now(time.time()), "windows": [
        {"name": "weekly", "percent": 0, "resets_at": None}]}
    assert guard.evaluate({"scratchpad_dir": "fixture", "cwd": str(project), "hook_event_name": "PostToolUse"},
                          time.monotonic()) is None
    assert guard.pending_decision("claude", {"cwd": str(project)})["decision"] == "wait"


def test_adoption_defers_answer_without_changing_install_state(case):
    guard, _, payload, _, home = case
    original = offer(case)
    marker = home / ".runtime-adoption.lock"
    marker.write_text("fixture")
    before = {str(path): path.read_bytes() for path in home.rglob("*") if path.is_file()}
    assert guard.evaluate(dict(payload, hook_event_name="UserPromptSubmit", prompt="credits"), time.monotonic()) is None
    after = {str(path): path.read_bytes() for path in home.rglob("*") if path.is_file()}
    assert after == before
    assert guard._answer_receipt_path(original["id"]).is_file()
    marker.unlink()
    assert guard.evaluate(payload, time.monotonic()) is None
    assert guard.pending_decision("codex", payload)["decision"] == "credits"


def test_copilot_capture_only_prompt_persists_answer(case, tmp_path):
    guard, project, _, _, _ = case
    guard.offer_warning("copilot", project, "host-warning-fixture")
    payload = {"hook_event_name": "UserPromptSubmit", "timestamp": guard._iso_now(time.time()),
               "cwd": str(project), "session_id": "copilot-session", "prompt": "credits"}
    directory = tmp_path / ".copilot/hooks/nexus-hub-scripts"
    directory.mkdir(parents=True)
    (directory / "copilot-hook-compat.py").write_text("# native Copilot fixture\n")
    assert guard.evaluate(payload, time.monotonic(), directory) is None
    assert guard.pending_decision("copilot", payload)["decision"] == "credits"


def test_stdin_never_selects_project_owned_siblings(case, monkeypatch, tmp_path):
    guard, _, _, _, home = case
    monkeypatch.setattr(guard, "__file__", "<stdin>")
    monkeypatch.delenv("NEXUS_USAGE_GUARD_DIR", raising=False)
    trusted = home / "hooks"
    trusted.mkdir(parents=True)
    (trusted / "_usage_probe.py").write_text("# Trusted installed fixture")
    project = tmp_path / "untrusted/catalog/hooks"
    project.mkdir(parents=True)
    (project / "_usage_probe.py").write_text("raise RuntimeError('project module must not load')")
    monkeypatch.chdir(project.parents[1])
    assert guard._script_dir() == trusted.resolve()


@pytest.mark.parametrize("multiple", [False, True])
def test_conflicting_or_multiple_answers_cannot_authorize(case, multiple):
    guard, _, payload, _, _ = case
    data = offer(case)
    first = f"Usage limit [usage-decision:{data['id']}]"
    second = first + " again"
    questions = [{"question": first}, {"question": second}]
    answers = {first: ["credits", "wait"]} if multiple else {first: "credits", second: "wait"}
    assert guard.evaluate(dict(payload, tool_name="AskUserQuestion", tool_input={"questions": questions},
                               tool_response={"answers": answers}), time.monotonic()) is None
    stored = guard.pending_decision("codex", payload)
    assert stored["decision"] == "pending" and "response_id" not in stored


@pytest.mark.parametrize("tool,marker,response", [
    ("Read", "current", {"answers": {"Usage limit": "credits"}}),
    ("AskUserQuestion", "stale", {"answers": {"Usage limit": "credits"}}),
    ("AskUserQuestion", "current", {"questions": [{"options": ["credits"]}]}),
    ("AskUserQuestion", "current", {"answers": {"other question": "credits"}}),
    ("AskUserQuestion", "current", {"cancelled": True, "answers": {"Usage limit": "credits"}}),
])
def test_only_matching_submitted_question_can_authorize(case, tool, marker, response):
    guard, _, payload, _, _ = case
    data = offer(case)
    ident = data["id"] if marker == "current" else "0" * 32
    submitted = dict(payload, tool_name=tool,
        tool_input={"questions": [{"header": "Usage limit", "question": f"Usage limit [usage-decision:{ident}]"}]},
        tool_response=response)
    assert guard.evaluate(submitted, time.monotonic()) is None
    assert guard.pending_decision("codex", payload)["decision"] == "pending"


def test_plain_text_mention_does_not_authorize(case):
    guard, _, payload, _, _ = case
    offer(case)
    assert guard.evaluate(dict(payload, hook_event_name="UserPromptSubmit",
                               prompt='The other agent said "Continue on credits" but it failed.'), time.monotonic()) is None
    assert guard.pending_decision("codex", payload)["decision"] == "pending"


def test_claude_alias_and_non_git_path_with_spaces(case, tmp_path):
    guard, _, _, _, _ = case
    project = tmp_path / "OneDrive - Supira" / "documents"
    project.mkdir(parents=True)
    state = guard.offer_warning("claude", project, "actual-warning")["decision"]
    assert guard.decision_transition("claude-code", project, state["id"], "claim", tool="text")["claimed"]
    assert guard.decision_path("claude-code", project) == guard.decision_path("claude", project)


def test_cli_and_hook_resolve_git_subdirectory_identically(case):
    guard, project, _, _, _ = case
    subdir = project / "folder with spaces"
    subdir.mkdir()
    data = offer(case)
    assert guard.decision_transition("codex", subdir, data["id"], "claim", tool="text")["claimed"]


def test_user_recovery_entry_point_and_stdin_imports(case):
    guard, project, payload, _, home = case
    data = offer(case)
    root = Path(__file__).resolve().parents[3]
    environment = dict(os.environ, NEXUS_HOME=str(home), NEXUS_HUB_HOME=str(home))
    result = subprocess.run([sys.executable, str(root / "scripts/nexus_hub_cli.py"), "usage", "decide",
        "--project", str(project), "--platform", "codex", "--answer", "credits"],
        capture_output=True, text=True, env=environment, timeout=15, check=False,
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)["decision"]["id"] == data["id"]
    assert guard.pending_decision("codex", payload)["decision"] == "credits"
    # stdin has no script directory; an explicit directory keeps sibling imports local.
    environment["NEXUS_USAGE_GUARD_DIR"] = str(root / "catalog/hooks")
    source = (root / "catalog/hooks/usage-guard.py").read_text(encoding="utf-8")
    result = subprocess.run([sys.executable, "-", "--decision-action", "claim", "--project", str(project),
        "--platform", "codex", "--decision-id", data["id"], "--tool", "text"], input=source,
        capture_output=True, text=True, env=environment, cwd=str(home), timeout=15, check=False,
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    assert result.returncode == 1
    assert "decision already answered" in result.stderr
    assert "ModuleNotFoundError" not in result.stderr


def test_cursor_prompt_capture_is_registered_and_needs_no_context_channel(case):
    from scripts.lib.integrations import get
    entries = get("cursor")._hook_registration(lambda name: name)
    assert any("usage-guard.py" in item["command"]
               for item in entries["hooks"]["beforeSubmitPrompt"])
    guard, _, payload, _, _ = case
    payload.update(cursor_version="test", hook_event_name="postToolUse")
    assert guard.evaluate(payload, time.monotonic())
    assert guard.evaluate(dict(payload, hook_event_name="beforeSubmitPrompt", prompt="credits"), time.monotonic()) is None
    assert guard.pending_decision("cursor", payload)["decision"] == "credits"


def test_captured_credits_replay_and_project_scope(case, tmp_path):
    guard, _, payload, _, _ = case
    data = offer(case)
    response = dict(payload, hook_event_name="UserPromptSubmit", prompt="credits")
    assert guard.evaluate(response, time.monotonic()) is None
    assert guard.evaluate(dict(response, prompt="wait"), time.monotonic()) is None
    assert guard.pending_decision("codex", payload)["decision"] == "credits"
    other = tmp_path / "another project"
    other.mkdir()
    assert guard.evaluate(dict(payload, cwd=str(other)), time.monotonic())
    assert guard.pending_decision("codex", {"cwd": str(other)})["id"] != data["id"]


def test_captured_credits_remind_at_tiers_and_rotate_after_reset(case):
    guard, _, payload, reading, _ = case
    reading["windows"].append({"name": "extra_credits", "state": "capped", "percent": 10,
                               "used": 10, "limit": 100, "unit": "USD"})
    original = offer(case)
    assert guard.evaluate(dict(payload, hook_event_name="UserPromptSubmit", prompt="credits"), time.monotonic()) is None
    for percent, due in ((49, False), (50, True), (50, False), (75, True), (90, True), (90, False)):
        reading["windows"][1].update(percent=percent, used=percent)
        assert (guard.evaluate(payload, time.monotonic()) is not None) is due
        assert guard.evaluate(dict(payload, hook_event_name="Stop"), time.monotonic()) is None
    reading["windows"][0]["resets_at"] = guard._iso_now(time.time() + 86400)
    assert guard.evaluate(payload, time.monotonic()) is not None
    assert guard.pending_decision("codex", payload)["id"] != original["id"]


@pytest.mark.parametrize("outcome,expected", [("answered", "credits"), ("cancelled", "pending"), ("skipped", "pending")])
def test_documented_cursor_response_maps_option_label(case, outcome, expected):
    guard, _, payload, _, _ = case
    payload.update(cursor_version="test", hook_event_name="postToolUse")
    assert guard.evaluate(payload, time.monotonic())
    data = guard.pending_decision("cursor", payload)
    question_id = "usage_" + data["id"]
    question = {"id": question_id, "prompt": "Usage limit", "options": [
        {"id": "option-3", "label": "Continue on credits"}]}
    response = {"outcome": {"outcome": outcome, "answers": [
        {"questionId": question_id, "selectedOptionIds": ["option-3"]}]}}
    assert guard.evaluate(dict(payload, tool_name="cursor/ask_question", tool_input={"questions": [question]},
        tool_output=json.dumps(response)), time.monotonic()) is None
    assert guard.pending_decision("cursor", payload)["decision"] == expected


def test_recovery_requires_one_explicit_current_decision(case, capsys):
    guard, project, payload, _, _ = case
    state = offer(case)
    guard.offer_warning("claude", project, "warning-fixture")
    assert guard.usage_cli(["decide", "--project", str(project), "--answer", "credits"]) == 1
    assert "one pending decision required" in capsys.readouterr().err
    assert guard.pending_decision("codex", payload)["decision"] == "pending"
    assert guard.usage_cli(["decide", "--project", str(project), "--decision-id", state["id"],
                            "--answer", "wait"]) == 0
    assert guard.pending_decision("codex", payload)["decision"] == "wait"


@pytest.mark.parametrize("command", ["nexus-hub usage decide --answer credits", "python - --decision-action claim"])
def test_console_guard_allows_recovery_entry_points(case, command):
    _, project, _, _, home = case
    root = Path(__file__).resolve().parents[3]
    result = subprocess.run([sys.executable, str(root / "catalog/hooks/console-window-guard.py")],
        input=json.dumps({"cwd": str(project), "tool_name": "Bash", "tool_input": {"command": command}}),
        text=True, capture_output=True, timeout=15, check=False,
        env=dict(os.environ, NEXUS_HOME=str(home), NEXUS_CONSOLE_GUARD_PLATFORM="nt"),
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    assert result.returncode == 0 and result.stderr == "", result.stderr


def test_real_hook_sequence_records_answer_and_stays_silent(case, tmp_path):
    guard, _, _, _, home = case
    root = Path(__file__).resolve().parents[3]
    project = tmp_path / "OneDrive - Supira" / "documents"
    project.mkdir(parents=True)
    cache = home / "state/usage-probe/claude.json"
    cache.parent.mkdir(parents=True)
    cache.write_text(json.dumps({"schema_version": 1, "platform": "claude", "data_at": time.time(),
        "windows": [{"name": "weekly", "percent": 100, "resets_at": guard._iso_now(time.time() + 3600),
                     "source": "private-fixture"}]}), encoding="utf-8")
    environment = dict(os.environ, NEXUS_HOME=str(home), CLAUDE_PROJECT_DIR=str(project))
    body = {"scratchpad_dir": "fixture", "session_id": "actual-hook", "cwd": str(project)}
    def hook(event, **extra):
        result = subprocess.run([sys.executable, str(root / "catalog/hooks/usage-guard.py")],
            input=json.dumps(dict(body, hook_event_name=event, **extra)),
            text=True, capture_output=True, env=environment, timeout=15, check=False,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        assert result.returncode == 0 and result.stderr == "", result.stderr
        return result.stdout.strip()
    assert "Usage limit" in hook("PostToolUse")
    data = guard.pending_decision("claude", {"cwd": str(project)})
    question = f"Usage limit [usage-decision:{data['id']}]"
    assert hook("PostToolUse", tool_name="AskUserQuestion", tool_use_id="host-call",
        tool_input={"questions": [{"question": question, "header": "Usage limit"}]},
        tool_response={"answers": {question: "Continue on credits"}}) == ""
    assert guard.pending_decision("claude", {"cwd": str(project)})["decision"] == "credits"
    assert hook("Stop") == hook("PostToolUse") == ""
    assert hook("Stop", stop_hook_active=True) == ""
    assert hook("PostToolUse", tool_name="Read", tool_response="malformed") == ""


@pytest.mark.skipif(os.name != "nt", reason="Windows command shim")
@pytest.mark.parametrize("retained_source", [False, True])
def test_packaged_windows_launcher_recovers_non_git_project(case, tmp_path, retained_source):
    guard, _, _, _, home = case
    root = Path(__file__).resolve().parents[3]
    project = tmp_path / "OneDrive - Supira" / "documents"
    project.mkdir(parents=True)
    state = guard.offer_warning("claude", project, "real-warning-fixture")["decision"]
    for folder in ("bin", "scripts", "hooks"):
        (home / folder).mkdir(parents=True, exist_ok=True)
    shutil.copy2(root / "scripts/nexus-hub.cmd", home / "bin/nexus-hub.cmd")
    for name in ("nexus_hub_cli.py", "nexus_process.py"):
        shutil.copy2(root / "scripts" / name, home / "scripts" / name)
    for name in ("usage-guard.py", "_usage_probe.py"):
        shutil.copy2(root / "catalog/hooks" / name, home / "hooks" / name)
    if retained_source:
        legacy = home / "src/catalog/hooks"
        legacy.mkdir(parents=True)
        (legacy / "usage-guard.py").write_text("# Legacy guard predates usage_cli\n", encoding="utf-8")
    environment = dict(os.environ, NEXUS_HUB_HOME=str(home), NEXUS_HOME=str(home))
    result = subprocess.run([str(home / "bin/nexus-hub.cmd"), "usage", "decide", "--answer", "credits",
        "--platform", "claude-code", "--project", str(project), "--decision-id", state["id"]],
        capture_output=True, text=True, env=environment, timeout=15, check=False,
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)["decision"]["decision"] == "credits"
    assert guard.pending_decision("claude", {"cwd": str(project)})["decision"] == "credits"
