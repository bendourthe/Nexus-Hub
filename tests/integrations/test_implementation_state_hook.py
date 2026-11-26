"""Typed Stop consumer delivery and raw-byte adapters, using disposable homes only."""
from __future__ import annotations

import json
import os
from pathlib import Path
import runpy
import shutil
import subprocess
import sys

import pytest

from scripts.lib.integrations import get
from scripts.lib.integrations._cascade_hook_compat import translate_child_result
from tests.integrations.test_implementation_reconciliation import (
    action, capture, controller, facts, manual_receipt,
)

REPO = Path(__file__).resolve().parents[2]
HOOKS = REPO / "catalog/hooks"


@pytest.mark.parametrize("fmt", ["top-level-block", "vscode-hook-specific-output", "cursor-followup-message", "antigravity-continue"])
def test_real_typed_stop_threshold_is_once_and_measured_progress_resets(controller, report_stop, fmt):
    report_stop.publish(facts(work=[{"id": "fix", "title": "Apply the approved fix", "authorized": True,
        "feasible": True, "evidence": "Existing fixture scope"}]))
    before = controller.record.read_bytes()
    results = [report_stop.stop(fmt=fmt) for _ in range(5)]
    assert all(result.returncode == 0 for result in results)
    assert all("Apply the approved fix" in result.stdout for result in results[:3])
    assert all(json.loads(result.stdout) for result in results[:3])
    assert results[3].stdout == "" and "the same unfinished condition remained unchanged" in results[3].stderr
    assert results[4].stdout == results[4].stderr == ""
    gate = controller.record.with_name(controller.record.stem + ".continuation.gate.json")
    assert json.loads(gate.read_text())["threshold_reported"] is True
    (controller.tmp / "counter").write_text("1", encoding="utf-8")
    assert "Apply the approved fix" in report_stop.stop(fmt=fmt).stdout
    assert json.loads(gate.read_text())["refusals"] == 0
    controller.state["head"] = "new-measured-head"
    assert "Apply the approved fix" in report_stop.stop(fmt=fmt).stdout
    state = json.loads(gate.read_text())
    assert state["refusals"] == 0 and state["threshold_reported"] is False
    assert controller.record.read_bytes() == before and controller.calls("cli") == []
    assert not any(call[:2] in (["record", "block"], ["record", "answer"]) for call in controller.calls("checker"))


def test_real_typed_stop_refreshes_reply_once_then_retires_verified_request(controller, report_stop):
    report_stop.publish(facts(requests=[action()]))
    before = controller.record.read_bytes()
    reply, receipt = manual_receipt(controller)
    event = capture(controller, reply)
    first = report_stop.stop()
    assert first.returncode == 0 and "A new user reply arrived" in json.loads(first.stdout)["reason"]
    waiting = report_stop.stop()
    assert waiting.returncode == 0 and waiting.stdout == ""
    assert "the captured reply received one refresh attempt" in waiting.stderr
    unchanged = report_stop.stop()
    assert unchanged.returncode == 0 and unchanged.stdout == unchanged.stderr == ""
    frame = report_stop.publish(facts(work=[{"id": "verify", "title": "Continue with the verified result",
        "authorized": True, "feasible": True, "evidence": "Existing fixture scope"}], resolutions=[{
        "request_id": "install", "reply_text": reply, "prompt_sha256": event["prompt"],
        "capture_event_id": event["event_id"], "result_receipt": receipt, "evidence": "Private owner result verified"}]))
    assert frame["disposition"]["requests"] == []
    assert len(frame["disposition"]["resolved_requests"]) == 1
    resumed = report_stop.stop()
    assert resumed.returncode == 0 and "Continue with the verified result" in json.loads(resumed.stdout)["reason"]
    assert controller.record.read_bytes() == before and controller.calls("cli") == []
    assert not any(call[:2] in (["record", "block"], ["record", "answer"]) for call in controller.calls("checker"))


def _runner(suffix: str) -> list[str]:
    if suffix == "sh":
        binary = shutil.which("bash")
        if not binary and Path("C:/Program Files/Git/bin/bash.exe").is_file():
            binary = "C:/Program Files/Git/bin/bash.exe"
        if not binary:
            pytest.skip("Bash is unavailable; shell adapter execution is not covered")
        return [binary, str(HOOKS / "implementation-state.sh")]
    binary = shutil.which("powershell") or shutil.which("pwsh")
    if not binary:
        pytest.skip("PowerShell is unavailable; Windows adapter execution is not covered")
    return [binary, "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(HOOKS / "implementation-state.ps1")]


def _environment(tmp_path: Path, suffix: str) -> tuple[dict[str, str], Path]:
    home = tmp_path / "private home"
    core = home / ".nexus-hub/scripts/completion_gate.py"
    core.parent.mkdir(parents=True)
    environment = os.environ.copy()
    for key in ("NEXUS_DISABLED_HOOKS", "NEXUS_HOOK_PROFILE", "NEXUS_RUNNER_LAUNCH"):
        environment.pop(key, None)
    environment.update(HOME=home.as_posix(), USERPROFILE=str(home), PYTHONIOENCODING="utf-8")
    binary = tmp_path / "bin"
    binary.mkdir()
    if suffix == "sh":
        python3 = binary / "python3"
        python3.write_text(f'#!/usr/bin/env bash\nexec "{Path(sys.executable).as_posix()}" "$@"\n', encoding="utf-8")
        python3.chmod(0o755)
    environment["PATH"] = os.pathsep.join((str(binary), str(Path(sys.executable).parent), environment.get("PATH", "")))
    return environment, core


def _core(core: Path) -> Path:
    core.write_text(
        "import os, pathlib, sys\n"
        "assert sys.argv[1:] == ['reconcile-stop']\n"
        "assert sys.dont_write_bytecode\n"
        "pathlib.Path(__file__).with_suffix('.stdin').write_bytes(sys.stdin.buffer.read())\n"
        "sys.stdout.write(os.environ.get('FIXTURE_STDOUT', ''))\n"
        "sys.stderr.write(os.environ.get('FIXTURE_STDERR', ''))\n"
        "raise SystemExit(int(os.environ.get('FIXTURE_EXIT', '0')))\n",
        encoding="utf-8",
    )
    return core.with_suffix(".stdin")


@pytest.mark.parametrize("suffix", ["sh", "ps1"])
@pytest.mark.parametrize("exit_code", [0, 2])
def test_shim_preserves_raw_payload_and_core_protocol(tmp_path, suffix, exit_code):
    environment, core = _environment(tmp_path, suffix)
    trace = _core(core)
    payload = b'\xef\xbb\xbf{"note":"caf\xc3\xa9"}\r\n'
    environment.update(FIXTURE_STDOUT='{"decision":"block","reason":"fixture"}\n', FIXTURE_STDERR="[Nexus-Hub: implementation-state] fixture\n", FIXTURE_EXIT=str(exit_code))
    result = subprocess.run(_runner(suffix), input=payload, capture_output=True, env=environment, cwd=tmp_path, timeout=30)
    assert trace.read_bytes() == payload
    assert result.returncode == exit_code
    assert json.loads(result.stdout) == {"decision": "block", "reason": "fixture"}
    assert result.stderr.decode("utf-8").strip() == "[Nexus-Hub: implementation-state] fixture"


@pytest.mark.parametrize("suffix", ["sh", "ps1"])
@pytest.mark.parametrize("control", [{"NEXUS_DISABLED_HOOKS": "other, implementation-state"}, {"NEXUS_HOOK_PROFILE": "minimal"}])
def test_disabled_consumer_is_silent_and_never_enters_core(tmp_path, suffix, control):
    environment, core = _environment(tmp_path, suffix)
    trace = _core(core)
    environment.update(control)
    result = subprocess.run(_runner(suffix), input=b"{}" * 100_000, capture_output=True, env=environment, cwd=tmp_path, timeout=30)
    assert result.returncode == 0 and result.stdout == result.stderr == b""
    assert not trace.exists()


@pytest.mark.parametrize("suffix", ["sh", "ps1"])
def test_missing_installed_core_never_uses_repository_core(tmp_path, suffix):
    environment, _ = _environment(tmp_path, suffix)
    impostor = tmp_path / "scripts/completion_gate.py"
    impostor.parent.mkdir()
    impostor.write_text("raise AssertionError('repository core executed')", encoding="utf-8")
    result = subprocess.run(_runner(suffix), input=b"{}", capture_output=True, env=environment, cwd=tmp_path, timeout=30)
    assert result.returncode == 0 and result.stdout == result.stderr == b""


@pytest.mark.parametrize("suffix", ["sh", "ps1"])
def test_runner_launch_does_not_disable_explicit_reconciliation(tmp_path, suffix):
    environment, core = _environment(tmp_path, suffix)
    trace = _core(core)
    environment["NEXUS_RUNNER_LAUNCH"] = "1"
    result = subprocess.run(_runner(suffix), input=b"{}", capture_output=True, env=environment, cwd=tmp_path, timeout=30)
    assert result.returncode == 0 and trace.read_bytes() == b"{}"


def test_default_stop_consumer_follows_usage_guard_and_retains_retirement():
    settings = json.loads((HOOKS / "settings.json").read_text())
    commands = [h["command"] for group in settings["hooks"]["Stop"] for h in group["hooks"]]
    assert commands[0].endswith("/usage-guard.py")
    assert commands[1] == "bash .claude/hooks/implementation-state.sh"
    assert not any("completion-gate" in command for command in commands)


@pytest.mark.parametrize(("key", "relative", "event"), [("claude", ".claude/settings.json", "Stop"), ("codex", ".codex/hooks.json", "Stop"), ("cursor", ".cursor/hooks.json", "stop"), ("antigravity2", ".agents/hooks.json", "Stop")])
def test_actual_temp_materialization_delivers_typed_consumer_and_shared_helper(install_ctx, key, relative, event):
    install_ctx.selection = {"resolved": {"skills": ["implement-phase"], "commands": [], "agents": []}}
    get(key).install(install_ctx)
    if key == "claude":
        # The Claude adapter delivers scripts; the existing native installer owns
        # settings registration. Exercise that real writer against this temp root.
        native = runpy.run_path(str(REPO / "tests/installer/test_native_hook_json.py"))
        harness = install_ctx.target_root / "native-hook-writer.ps1"
        harness.write_text(native["_HARNESS"], encoding="utf-8-sig")
        native["_invoke"](harness, install_ctx.target_root / ".claude", "Install-GitGuardrails")
    configuration = json.loads((install_ctx.target_root / relative).read_text(encoding="utf-8"))
    events = configuration["nexus-hub-guardrails"] if key == "antigravity2" else configuration["hooks"]
    commands = [handler["command"] for group in events[event] for handler in group.get("hooks", [group])]
    assert sum("implementation-state" in command for command in commands) == 1
    assert not any("completion-gate" in command for command in commands)
    if key != "antigravity2":
        assert next(i for i, c in enumerate(commands) if "usage-guard" in c) < next(i for i, c in enumerate(commands) if "implementation-state" in c)
    scripts = list(install_ctx.target_root.rglob("implementation-state.sh"))
    assert scripts
    for script in scripts:
        assert script.read_bytes() == (HOOKS / script.name).read_bytes()
        assert script.with_suffix(".ps1").read_bytes() == (HOOKS / "implementation-state.ps1").read_bytes()
    helpers = list(install_ctx.target_root.rglob("implement-phase/scripts/continuation_state.py"))
    assert helpers
    for helper in helpers:
        assert helper.read_bytes() == (REPO / "catalog/skills/workflow/implement-phase/scripts/continuation_state.py").read_bytes()


def test_antigravity_stop_translation_preserves_bounded_native_continue():
    output, code = translate_child_result("antigravity", "Stop", stdout='{"decision":"block","reason":"reconcile explicit facts"}', stderr="", returncode=0)
    assert code == 0 and output == {"decision": "continue", "reason": "reconcile explicit facts"}
    assert translate_child_result("antigravity", "Stop", stdout="", stderr="Waiting for the owned job", returncode=0) == ({}, 0)


@pytest.mark.parametrize("host", ["cursor", "antigravity"])
@pytest.mark.parametrize("waiting", [False, True])
def test_native_compat_runtime_forwards_continuation_but_never_followup_on_wait(tmp_path, host, waiting):
    suffix = "ps1" if os.name == "nt" else "sh"
    environment, core = _environment(tmp_path, suffix)
    trace = _core(core)
    payload = {"session_id": "fixture", "hook_event_name": "Stop"}
    if host == "cursor":
        payload["cursor_version"] = "fixture"
        expected = {} if waiting else {"followup_message": "reconcile explicit facts"}
        child = {} if waiting else expected
        prefix = [sys.executable, "-B", str(HOOKS / "cursor-hook-compat.py")]
    else:
        expected = {} if waiting else {"decision": "continue", "reason": "reconcile explicit facts"}
        child = {} if waiting else {"decision": "block", "reason": "reconcile explicit facts"}
        # The adapter deploys this shared runtime as antigravity-hook-compat.py.
        prefix = [sys.executable, "-B", str(REPO / "scripts/lib/integrations/_cascade_hook_compat.py"), "antigravity", "Stop", "--"]
    environment.update(FIXTURE_STDOUT="" if waiting else json.dumps(child), FIXTURE_STDERR="Waiting for the owned job\n" if waiting else "")
    result = subprocess.run([*prefix, *_runner(suffix)], input=json.dumps(payload).encode(), capture_output=True, env=environment, cwd=tmp_path, timeout=30)
    assert result.returncode == 0, result.stderr.decode(errors="replace")
    assert json.loads(result.stdout) == expected
    assert trace.is_file()
    if waiting:
        assert "Waiting for the owned job" in result.stderr.decode()
        assert "followup_message" not in result.stdout.decode()


@pytest.fixture
def report_stop(controller, monkeypatch, capsys):
    """Exercise the real default reporting core with explicitly inert owner facts.

    This does not exercise cmd_stop's signed-native controller authentication.
    """
    from types import SimpleNamespace
    import completion_gate as gate
    import check_plan_completion as checker
    import run_plan
    from tests.validators.test_run_plan import PLAN_REL

    monkeypatch.setattr(run_plan, "native_owner_observation", lambda *args, **kwargs: None)
    monkeypatch.setattr(checker, "_secret", lambda *args, **kwargs: None)
    scope = SimpleNamespace(minor=False, label=PLAN_REL, repo_root=controller.repo, observer_session="fixture-owner")
    record = json.loads(controller.record.read_text())

    def publish(observation, rc=1, output="INCOMPLETE: task.T002"):
        previous = run_plan.read_continuation(scope, controller.record, record)
        frame = run_plan.reconcile_observation(scope, controller.record, record, observation, rc, output, previous)
        run_plan.save_continuation(controller.record, frame)
        return frame

    def stop(delivered=None, rc=1, output="INCOMPLETE: task.T002", fmt="top-level-block"):
        monkeypatch.setenv("NEXUS_GATE_FORMAT", fmt)
        counter = controller.tmp / "counter"
        met = int(counter.read_text()) if counter.exists() and controller.state.get("progress", True) else 0
        score = [str(met), controller.state.get("head", "head")]
        code = gate._reconcile_stop({"session_id": "fixture-owner", "last_assistant_message": delivered},
            controller.record, record, controller.repo, rc, output, score)
        captured = capsys.readouterr()
        return SimpleNamespace(returncode=code, stdout=captured.out, stderr=captured.err)

    return SimpleNamespace(publish=publish, stop=stop)


@pytest.mark.parametrize("change", ["request", "job", "job-handle", "job-status", "condition", "legacy"])
def test_waiting_report_new_obligation_gets_fresh_correction_without_progress(controller, report_stop, change):
    request = action()
    job = {"id": "job-a", "name": "Private pending job", "url": "https://example.invalid/jobs/a",
        "status": "pending", "evidence": "Private controller fixture", "observed_at": "2026-11-24T20:00:00+00:00",
        "resume_when": "The bound job result is available"}
    condition = {"id": "service", "title": "Private service restoration", "evidence": "Private unavailable probe",
        "observed_at": "2026-11-24T20:00:00+00:00", "resume_when": "The original health predicate succeeds"}
    observation = facts(requests=[request], jobs=[job], external_conditions=[condition])
    report_stop.publish(observation)
    before = controller.record.read_bytes()
    results = [report_stop.stop(delivered="Incomplete waiting report") for _ in range(4)]
    assert all("Correct the waiting report" in result.stdout for result in results[:3])
    assert results[3].stdout == "" and "correction limit reached" in results[3].stderr
    gate = controller.record.with_name(controller.record.stem + ".continuation.gate.json")
    prior = json.loads(gate.read_text())
    if change == "request":
        observation["requests"].append(dict(action("second-action"), title="Record the second private action"))
    elif change == "job":
        observation["jobs"].append(dict(job, id="job-b", url="https://example.invalid/jobs/b"))
    elif change == "job-handle":
        observation["jobs"].append(dict(job, id="job-b", handle="private:job-b"))
    elif change == "job-status":
        observation["jobs"][0] = dict(job, status="running")
    elif change == "condition":
        observation["external_conditions"].append(dict(condition, id="replacement-service", resume_when="The replacement health predicate succeeds"))
    else:
        prior.pop("report_fingerprint", None)
        gate.write_text(json.dumps(prior), encoding="utf-8")
    report_stop.publish(observation)
    result = report_stop.stop(delivered="Incomplete waiting report")
    assert result.returncode == 0 and "Correct the waiting report" in result.stdout
    current = json.loads(gate.read_text())
    assert current["report_corrections"] == 1
    assert current["fingerprint"] == prior["fingerprint"]
    assert current["refusals"] == prior["refusals"] + 1
    assert current["threshold_reported"] == prior["threshold_reported"]
    assert current["report_fingerprint"]
    if change != "legacy":
        assert current["report_fingerprint"] != prior["report_fingerprint"]
    assert controller.record.read_bytes() == before and controller.calls("cli") == []


def test_waiting_report_cosmetic_updates_keep_exhausted_correction_limit(controller, report_stop):
    observation = facts(requests=[action("action-a"), action("action-b")],
        jobs=[{"id": "job-a", "name": "Private pending job", "handle": "private:job-a", "status": "pending",
            "evidence": "Private controller fixture", "observed_at": "2026-11-24T20:00:00+00:00",
            "resume_when": "The bound job result is available"}],
        external_conditions=[{"id": "service", "title": "Private service restoration", "evidence": "Unavailable",
            "observed_at": "2026-11-24T20:00:00+00:00", "resume_when": "The original predicate succeeds"}])
    report_stop.publish(observation)
    for _ in range(4):
        report_stop.stop(delivered="Incomplete waiting report")
    gate = controller.record.with_name(controller.record.stem + ".continuation.gate.json")
    prior = json.loads(gate.read_text())
    observation["requests"].reverse()
    observation["jobs"][0].update(name="A cosmetic job name", evidence="A new observation description",
        observed_at="2026-11-25T20:00:00+00:00")
    observation["external_conditions"][0].update(evidence="A new probe description",
        observed_at="2026-11-25T20:00:00+00:00")
    report_stop.publish(observation)
    result = report_stop.stop(delivered="Incomplete waiting report")
    current = json.loads(gate.read_text())
    assert result.returncode == 0 and result.stdout == result.stderr == ""
    assert current["report_fingerprint"] == prior["report_fingerprint"]
    assert current["report_corrections"] == prior["report_corrections"] + 1
    assert current["refusals"] == prior["refusals"] + 1


def test_waiting_report_old_action_steps_do_not_cover_new_pending_action(controller, report_stop):
    import run_plan

    observation = facts(requests=[action("first-action")])
    frame = report_stop.publish(observation)
    for _ in range(4):
        report_stop.stop(delivered="Incomplete waiting report")
    reporter = run_plan.reporting_module("status_report")
    disposition = frame["disposition"]
    old_report = "\n\n".join([reporter.state_heading(disposition), *reporter.required_parts(disposition)])
    observation["requests"].append(dict(action("second-action"), title="Provide the second private result",
        steps=["Perform the second private check", "Record its separate receipt"]))
    report_stop.publish(observation)
    result = report_stop.stop(delivered=old_report)
    assert "Correct the waiting report" in result.stdout
    assert "Perform the second private check" in result.stdout
    assert "Record its separate receipt" in result.stdout
    gate = controller.record.with_name(controller.record.stem + ".continuation.gate.json")
    assert json.loads(gate.read_text())["report_corrections"] == 1


def test_waiting_report_request_churn_does_not_reset_working_refusal_threshold(controller, report_stop):
    observation = facts(work=[{"id": "fix", "title": "Apply the approved private fix",
        "authorized": True, "feasible": True, "evidence": "Private fixture scope"}])
    results = []
    for index in range(5):
        observation["requests"].append(action("pending-" + str(index)))
        report_stop.publish(observation)
        results.append(report_stop.stop(delivered="Incomplete waiting report"))
    assert all("Apply the approved private fix" in result.stdout for result in results[:3])
    assert results[3].stdout == "" and "the same unfinished condition remained unchanged" in results[3].stderr
    assert results[4].stdout == results[4].stderr == ""
    gate = controller.record.with_name(controller.record.stem + ".continuation.gate.json")
    state = json.loads(gate.read_text())
    assert state["refusals"] == 4 and state["threshold_reported"] is True
    assert "report_corrections" not in state


@pytest.mark.parametrize("rc,output", [(4, "PAUSED: user"), (0, "PLAN COMPLETE plan head nonce")])
def test_waiting_report_terminal_pause_and_completion_do_not_request_correction(controller, report_stop, rc, output):
    report_stop.publish(facts(), rc=rc, output=output)
    delivered = "Explicitly paused by the owner" if rc == 4 else "Terminal report"
    result = report_stop.stop(delivered=delivered, rc=rc, output=output)
    assert result.returncode == 0 and result.stdout == ""
    gate = controller.record.with_name(controller.record.stem + ".continuation.gate.json")
    assert "report_corrections" not in json.loads(gate.read_text())


@pytest.mark.parametrize("change", ["new-round", "cosmetic", "legacy"])
def test_precreate_waiting_report_correction_tracks_pending_round(controller, monkeypatch, capsys, change):
    """Use inert verified-owner facts; no native record or approval is created."""
    from types import SimpleNamespace
    import approval_binding
    import check_plan_completion as checker
    import completion_gate as gate
    import run_plan

    path = controller.record.with_name("private-precreate.json")
    context = SimpleNamespace(root=controller.repo, plan=controller.repo / "private-plan.md")
    metadata = {"session_id": "fixture-owner", "nonce": "private-precreate"}
    request = dict(action("native:create:round-a"), title="Record private create round A")
    observation = facts(requests=[request])
    monkeypatch.setattr(checker, "precreate_owner_context", lambda *args, **kwargs: (context, path, metadata))
    monkeypatch.setattr(checker, "_secret", lambda *args, **kwargs: None)
    monkeypatch.setattr(approval_binding, "observe_issued_request", lambda *args, **kwargs: None)
    monkeypatch.setattr(run_plan, "precreate_owner_observation", lambda *args, **kwargs: observation)
    monkeypatch.setenv("NEXUS_GATE_FORMAT", "top-level-block")
    payload = {"last_assistant_message": "Incomplete private create report"}
    for index in range(4):
        assert gate._precreate_stop(payload, "fixture-owner") == 0
        delivered = capsys.readouterr()
        assert bool(delivered.out) is (index < 3)
    cache = path.with_name(path.stem + ".continuation.gate.json")
    prior = json.loads(cache.read_text())
    if change == "new-round":
        observation["requests"].append(dict(action("native:create:round-b"), title="Record private create round B",
            steps=["Capture the separate private round B line"]))
    elif change == "cosmetic":
        observation["display_note"] = "A cosmetic observation description"
        observation["requests"][0] = dict(request, requested_at=1234567890)
    else:
        prior.pop("report_fingerprint", None)
        cache.write_text(json.dumps(prior), encoding="utf-8")
    assert gate._precreate_stop(payload, "fixture-owner") == 0
    delivered = capsys.readouterr()
    current = json.loads(cache.read_text())
    assert current["fingerprint"] == prior["fingerprint"]
    if change == "cosmetic":
        assert delivered.out == delivered.err == ""
        assert current["report_corrections"] == 5
        assert current["report_fingerprint"] == prior["report_fingerprint"]
    else:
        assert delivered.out and current["report_corrections"] == 1
        if change == "new-round":
            assert "Capture the separate private round B line" in delivered.out
            assert current["report_fingerprint"] != prior["report_fingerprint"]
    assert not path.exists()
    assert controller.calls("cli") == []
