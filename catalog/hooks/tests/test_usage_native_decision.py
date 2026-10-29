"""Private fixture protocol tests; these do not prove a rendered host dialog."""
from __future__ import annotations
import importlib.util
import json
import time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import pytest

HOOKS = Path(__file__).resolve().parents[1]

def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

@pytest.fixture
def case(tmp_path, monkeypatch):
    home = tmp_path / "home"
    monkeypatch.setenv("NEXUS_HOME", str(home))
    guard = load("usage_native_protocol_test", HOOKS / "usage-guard.py")
    project = tmp_path / "project"
    (project / ".git").mkdir(parents=True)
    reset = guard._iso_now(time.time() + 3600)
    reading = {"status": "ok", "fetched_at": guard._iso_now(time.time()),
               "windows": [{"name": "weekly", "percent": 99.5,
                            "resets_at": reset, "source": "private-test"}]}
    monkeypatch.setattr(guard, "run_probe", lambda *_: reading)
    payload = {"session_id": "one", "turn_id": "t", "model": "test",
               "hook_event_name": "PostToolUse", "cwd": str(project)}
    return guard, project, payload, reading, home

def offer(case):
    guard, project, payload, _, _ = case
    out = guard.evaluate(payload, time.monotonic())
    assert out
    return guard.pending_decision("codex", payload)

def test_one_offer_across_sessions_and_additional_windows(case):
    guard, project, payload, reading, _ = case
    data = offer(case)
    assert guard.decision_transition("codex", project, data["id"], "claim", tool="private-fixture")["claimed"]
    payload["session_id"] = "two"
    reading["windows"].append({"name": "five_hour", "percent": 100,
                              "resets_at": guard._iso_now(time.time() + 1000)})
    status = json.dumps(guard.evaluate(payload, time.monotonic()))
    assert data["id"] in status and "Stop new work" in status
    assert "Do not claim or ask another question" in status
    assert guard.evaluate(payload, time.monotonic()) is None
    assert guard.pending_decision("codex", payload)["id"] == data["id"]

def test_claim_bind_answer_is_immutable(case):
    guard, project, payload, _, _ = case
    data = offer(case)
    claim = guard.decision_transition("codex", project, data["id"], "claim",
                                      tool="functions.request_user_input_async")
    token = claim["decision"]["delivery"]["claim_id"]
    assert claim["claimed"]
    assert not guard.decision_transition("codex", project, data["id"], "claim", tool="text")["claimed"]
    guard.decision_transition("codex", project, data["id"], "delivered", claim_id=token,
                             request_id="private-fixture-request")
    with pytest.raises(ValueError):
        guard.decision_transition("codex", project, data["id"], "answer", claim_id=token,
                                  request_id="wrong", response_id="fixture-response", answer="credits")
    guard.decision_transition("codex", project, data["id"], "answer", claim_id=token,
                             request_id="private-fixture-request", response_id="fixture-response", answer="wait")
    with pytest.raises(ValueError):
        guard.decision_transition("codex", project, data["id"], "answer", claim_id=token,
                                  request_id="private-fixture-request", response_id="fixture-response", answer="credits")
    assert guard.pending_decision("codex", payload)["decision"] == "wait"

def test_ambiguous_delivery_does_not_fallback(case):
    guard, project, payload, _, _ = case
    data = offer(case)
    claim = guard.decision_transition("codex", project, data["id"], "claim", tool="native-api")
    token = claim["decision"]["delivery"]["claim_id"]
    guard.decision_transition("codex", project, data["id"], "uncertain", claim_id=token)
    assert not guard.decision_transition("codex", project, data["id"], "claim", tool="text")["claimed"]
    assert guard.evaluate(payload, time.monotonic()) is None
    assert guard.pending_decision("codex", payload)["decision"] == "pending"

def test_repository_cannot_approve_credits(case):
    guard, project, payload, _, _ = case
    (project / ".nexus-hub").mkdir()
    (project / ".nexus-hub" / "usage-decision.json").write_text(json.dumps(
        {"decision": "credits", "recorded_at": guard._iso_now(time.time())}))
    assert offer(case)["decision"] == "pending"

def test_no_answer_without_request_or_response(case):
    guard, project, payload, _, _ = case
    data = offer(case)
    with pytest.raises(ValueError):
        guard.decision_transition("codex", project, data["id"], "answer", answer="credits")
    with pytest.raises(ValueError):
        guard.decision_transition("codex", project, "stale-id", "claim", tool="text")
    assert guard.pending_decision("codex", payload)["decision"] == "pending"

def test_os_lock_excludes_writer_and_has_no_stale_eviction(case):
    guard, _, _, _, home = case
    probe = guard._load_probe()
    with probe.ActivityLock(home, adopter=True) as first:
        assert first.held
        with probe.ActivityLock(home, adopter=True) as second:
            assert not second.held
    with probe.ActivityLock(home, adopter=True) as third:
        assert third.held

def test_adoption_marker_prevents_probe_and_decision_writes(case, monkeypatch):
    guard, _, payload, _, home = case
    home.mkdir()
    (home / ".runtime-adoption.lock").write_text("private-test")
    monkeypatch.setattr(guard, "run_probe", lambda *_: pytest.fail("probe started during adoption"))
    assert guard.evaluate(payload, time.monotonic()) is None
    assert not (home / "state").exists()

def test_probe_locked_is_cache_only(case, monkeypatch):
    guard, _, _, _, home = case
    probe = guard._load_probe()
    sentinel = object()
    monkeypatch.setattr(probe, "cached_probe", lambda _: sentinel)
    monkeypatch.setattr(probe, "_probe_unlocked", lambda _: pytest.fail("live probe while adopter owns lock"))
    with probe.ActivityLock(home, adopter=True) as activity:
        assert activity.held
        assert probe.probe("codex") is sentinel

def test_delivery_directive_names_actual_api_and_safe_order(case):
    guard, _, payload, _, _ = case
    output = guard.evaluate(payload, time.monotonic())
    text = json.dumps(output)
    assert "functions.request_user_input_async" in text
    assert text.index("Wait for reset (Recommended)") < text.index("Hand off, Continue on credits")
    assert "do not retry or fall back" in text

@pytest.mark.parametrize("answer", ["pending", "wait", "handoff", "credits"])
def test_gate_uses_shared_decision_without_rewriting_progress(case, monkeypatch, tmp_path, answer):
    guard, project, payload, reading, _ = case
    state = offer(case)
    if answer != "pending":
        claim = guard.decision_transition("codex", project, state["id"], "claim", tool="private-fixture")
        token = claim["decision"]["delivery"]["claim_id"]
        guard.decision_transition("codex", project, state["id"], "delivered", claim_id=token,
                                 request_id="private-gate-request")
        guard.decision_transition("codex", project, state["id"], "answer", claim_id=token,
                                 request_id="private-gate-request", response_id="private-gate-response", answer=answer)
    gate = load("native_usage_gate_fixture", HOOKS.parents[1] / "scripts" / "completion_gate.py")
    monkeypatch.setattr(gate, "_usage_guard", lambda _: (guard, HOOKS))
    record = tmp_path / "run.json"
    record.write_text("{}")
    assert gate.usage_limit_stop(payload, record, {}, project, time.monotonic() + 5) is (answer != "credits")
    assert record.read_text() == "{}"


def test_competing_claims_deliver_only_once(case):
    guard, project, payload, _, _ = case
    state = offer(case)
    def claim(_):
        try:
            return guard.decision_transition("codex", project, state["id"], "claim", tool="private-fixture-api")["claimed"]
        except ValueError:
            return False  # The non-owner must not deliver.
    with ThreadPoolExecutor(max_workers=2) as pool:
        assert list(pool.map(claim, range(2))).count(True) == 1
    assert guard.pending_decision("codex", payload)["decision"] == "pending"


def test_project_or_platform_cannot_reuse_another_claim(case, tmp_path):
    guard, project, _, _, _ = case
    state = offer(case)
    other = tmp_path / "other"
    other.mkdir()
    for platform, path in (("claude", project), ("codex", other)):
        with pytest.raises(ValueError):
            guard.decision_transition(platform, path, state["id"], "claim", tool="text")


def test_recovered_real_request_can_bind_uncertain_delivery(case):
    guard, project, payload, _, _ = case
    state = offer(case)
    claim = guard.decision_transition("codex", project, state["id"], "claim", tool="private-fixture-api")
    token = claim["decision"]["delivery"]["claim_id"]
    guard.decision_transition("codex", project, state["id"], "uncertain", claim_id=token)
    guard.decision_transition("codex", project, state["id"], "delivered", claim_id=token,
                             request_id="recovered-private-request")
    guard.decision_transition("codex", project, state["id"], "answer", claim_id=token,
                             request_id="recovered-private-request", response_id="private-response", answer="handoff")
    assert guard.pending_decision("codex", payload)["decision"] == "handoff"


def test_marker_recheck_after_lock_acquisition_releases_writer(case, monkeypatch):
    guard, _, _, _, home = case
    probe = guard._load_probe()
    checks = iter((False, True))
    monkeypatch.setattr(probe, "adoption_active", lambda *_: next(checks))
    with probe.ActivityLock(home) as writer:
        assert not writer.held
    monkeypatch.setattr(probe, "adoption_active", lambda *_: False)
    with probe.ActivityLock(home, adopter=True) as adopter:
        assert adopter.held


def test_gate_needs_confirmed_usage_and_preserves_unknown_score(case, monkeypatch, tmp_path):
    guard, project, payload, reading, _ = case
    offer(case)
    gate = load("unknown_usage_gate_fixture", HOOKS.parents[1] / "scripts" / "completion_gate.py")
    monkeypatch.setattr(gate, "_usage_guard", lambda _: (guard, HOOKS))
    record = tmp_path / "run.json"
    record.write_text('{"progress": null}')
    reading.update(status="unavailable", windows=[])
    assert not gate.usage_limit_stop(payload, record, {}, project, time.monotonic() + 5)
    assert record.read_text() == '{"progress": null}'


def test_real_cli_binding_in_fixture_home(case):
    import os
    import subprocess
    import sys
    guard, project, payload, _, home = case
    state = offer(case)
    environment = dict(os.environ, NEXUS_HOME=str(home), PYTHONDONTWRITEBYTECODE="1")
    def cli(action, *extra):
        result = subprocess.run([sys.executable, "-I", "-B", str(HOOKS / "usage-guard.py"),
            "--decision-action", action, "--project", str(project), "--platform", "codex",
            "--decision-id", state["id"], *extra], env=environment, capture_output=True,
            text=True, timeout=10)
        assert result.returncode == 0, result.stderr
        return json.loads(result.stdout)
    claimed = cli("claim", "--tool", "private-fixture-api")
    token = claimed["decision"]["delivery"]["claim_id"]
    cli("delivered", "--claim-id", token, "--request-id", "private-cli-request")
    answered = cli("answer", "--claim-id", token, "--request-id", "private-cli-request",
                   "--response-id", "private-cli-response", "--answer", "wait")
    assert answered["decision"]["decision"] == "wait"
    assert guard.pending_decision("codex", payload)["response_id"] == "private-cli-response"


def test_os_releases_writer_ownership_when_child_exits(case):
    import subprocess
    import sys
    guard, _, _, _, home = case
    code = ("import sys,os;from pathlib import Path;sys.path.insert(0,sys.argv[1]);"
            "import _usage_probe as p;l=p.ActivityLock(Path(sys.argv[2]),adopter=True);"
            "l.__enter__();assert l.held;os._exit(0)")
    result = subprocess.run([sys.executable, "-I", "-B", "-c", code, str(HOOKS), str(home)],
                            capture_output=True, text=True, timeout=10)
    assert result.returncode == 0, result.stderr
    with guard._load_probe().ActivityLock(home, adopter=True) as adopter:
        assert adopter.held


@pytest.mark.parametrize("corrupt", [
    {"id": "not-a-decision-id"}, {"recorded_at": "2099-01-01T00:00:00Z"},
    {"created_at": "invalid"}, {"decision": "credits"}, {"decision": ["credits"]},
    {"delivery": {"state": "delivered", "request_id": "unbound"}},
])
def test_malformed_home_ledger_cannot_authorize(case, corrupt):
    guard, project, payload, _, _ = case
    data = offer(case)
    data.update(corrupt)  # Private tamper fixture.
    guard.save_state(guard.decision_path("codex", project), data)
    assert guard.pending_decision("codex", payload) is None


def test_approval_starts_at_submitted_answer_and_reuses_existing_age_ceiling(case, monkeypatch):
    guard, project, payload, reading, _ = case
    reading["windows"][0]["resets_at"] = None
    data = offer(case)
    clock = time.time() + 60
    monkeypatch.setattr(guard.time, "time", lambda: clock)
    claim = guard.decision_transition("codex", project, data["id"], "claim", tool="private-fixture")
    token = claim["decision"]["delivery"]["claim_id"]
    guard.decision_transition("codex", project, data["id"], "delivered", claim_id=token,
                             request_id="private-delayed-request")
    guard.decision_transition("codex", project, data["id"], "answer", claim_id=token,
                             request_id="private-delayed-request", response_id="private-response", answer="credits")
    final = guard.pending_decision("codex", payload)
    assert final["approval"]["approved_at"] == final["recorded_at"]
    assert final["recorded_at"] != final["created_at"]
    assert guard._decision_active(final, reading["windows"], clock)
    assert not guard._decision_active(final, reading["windows"], clock + guard.APPROVAL_MAX_AGE_SECONDS + 1)


@pytest.mark.parametrize("answer", ["wait", "handoff", "credits"])
def test_additional_crossing_window_reuses_one_genuine_answer(case, answer):
    guard, project, payload, reading, _ = case
    data = offer(case)
    claim = guard.decision_transition("codex", project, data["id"], "claim", tool="private-fixture")
    token = claim["decision"]["delivery"]["claim_id"]
    guard.decision_transition("codex", project, data["id"], "delivered", claim_id=token,
                             request_id="private-additional-request")
    guard.decision_transition("codex", project, data["id"], "answer", claim_id=token,
                             request_id="private-additional-request", response_id="private-response", answer=answer)
    reading["windows"].append({"name": "five_hour", "percent": 100,
                              "resets_at": guard._iso_now(time.time() + 1000)})
    payload["session_id"] = "another-session"
    status = guard.evaluate(payload, time.monotonic())
    if answer == "credits":
        assert status is None
    else:
        assert data["id"] in json.dumps(status)
        assert "Do not claim or ask another question" in json.dumps(status)
    assert guard.evaluate(payload, time.monotonic()) is None
    result = guard.pending_decision("codex", payload)
    assert result["id"] == data["id"] and result["decision"] == answer


def answer_fixture(case, choice):
    """Bind private host-ID fixtures, never live authorization evidence."""
    guard, project, payload, _, _ = case
    data = guard.pending_decision("codex", payload)
    claim = guard.decision_transition("codex", project, data["id"], "claim", tool="private-fixture")
    token = claim["decision"]["delivery"]["claim_id"]
    guard.decision_transition("codex", project, data["id"], "delivered", claim_id=token,
                             request_id="private-reset-request")
    guard.decision_transition("codex", project, data["id"], "answer", claim_id=token,
                             request_id="private-reset-request", response_id="private-reset-response", answer=choice)
    return guard.pending_decision("codex", payload)


@pytest.mark.parametrize("choice", ["wait", "handoff", "credits"])
def test_answered_unknown_reset_clear_requires_new_question_and_preserves_history(case, choice):
    guard, project, payload, reading, _ = case
    reading["windows"][0]["resets_at"] = None
    old = offer(case)
    answered = answer_fixture(case, choice)
    reading["windows"][0]["percent"] = 0
    assert guard.evaluate(payload, time.monotonic()) is None
    reading["windows"][0]["percent"] = 100
    assert guard.evaluate(payload, time.monotonic())
    current = guard.pending_decision("codex", payload)
    assert current["id"] != old["id"] and current["decision"] == "pending"
    history = guard.decision_path("codex", project).parent / "history" / (old["id"] + ".json")
    saved = json.loads(history.read_text())
    for key in ("id", "decision", "recorded_at", "response_id", "delivery", "windows"):
        assert saved[key] == answered[key]
    with pytest.raises(ValueError):
        guard.decision_transition("codex", project, old["id"], "answer", answer="credits")


def test_unanswered_unknown_reset_clear_reuses_same_question(case):
    guard, _, payload, reading, _ = case
    reading["windows"][0]["resets_at"] = None
    old = offer(case)
    claim = guard.decision_transition("codex", case[1], old["id"], "claim", tool="private-fixture")
    assert claim["claimed"]
    reading["windows"][0]["percent"] = 0
    assert guard.evaluate(payload, time.monotonic()) is None
    reading["windows"][0]["percent"] = 100
    assert guard.evaluate(payload, time.monotonic()) is None
    assert guard.pending_decision("codex", payload)["id"] == old["id"]


def test_answer_history_is_idempotent_and_never_overwrites_collision(case):
    guard, project, payload, _, _ = case
    offer(case)
    answered = answer_fixture(case, "wait")
    path = guard.decision_path("codex", project)
    assert guard.archive_answer(path, answered)
    history = path.parent / "history" / (answered["id"] + ".json")
    original = history.read_bytes()
    assert guard.archive_answer(path, answered)
    assert history.read_bytes() == original
    history.write_text("private-collision-fixture")
    assert not guard.archive_answer(path, answered)
    assert history.read_text() == "private-collision-fixture"


def test_history_failure_refuses_to_rotate_answered_decision(case, monkeypatch):
    guard, _, payload, reading, _ = case
    reading["windows"][0]["resets_at"] = None
    offer(case)
    answered = answer_fixture(case, "credits")
    monkeypatch.setattr(guard, "archive_answer", lambda *_: False, raising=False)
    reading["windows"][0]["percent"] = 0
    assert guard.evaluate(payload, time.monotonic()) is None
    reading["windows"][0]["percent"] = 100
    output = guard.evaluate(payload, time.monotonic())
    text = json.dumps(output)
    assert "prior credits episode expired" in text and "no new spending authority" in text
    assert "do not ask another question" in text
    assert "BLOCKED" not in text and "PAUSED" not in text
    current = guard.pending_decision("codex", payload)
    for key in ("id", "decision", "response_id", "delivery"):
        assert current[key] == answered[key]
    assert guard.evaluate(payload, time.monotonic()) is None


def test_lost_offered_output_is_recovered_without_second_ui_delivery(case):
    guard, project, payload, _, _ = case
    first = guard.evaluate(payload, time.monotonic())  # Simulate lost context before any agent claim.
    old = guard.pending_decision("codex", payload)
    recovered = guard.evaluate(dict(payload, session_id="recovery"), time.monotonic())
    assert recovered == first and recovered is not None
    assert guard.pending_decision("codex", payload)["id"] == old["id"]
    assert guard.decision_transition("codex", project, old["id"], "claim", tool="private-fixture")["claimed"]
    assert guard.evaluate(payload, time.monotonic()) is None
    assert not guard.decision_transition("codex", project, old["id"], "claim", tool="text")["claimed"]


@pytest.mark.parametrize("choice", ["wait", "handoff", "credits"])
def test_future_named_reset_change_rotates_answered_episode(case, choice):
    guard, project, payload, reading, _ = case
    reading["windows"][0]["resets_at"] = guard._iso_now(time.time() + 86400)
    old = offer(case)
    answer_fixture(case, choice)
    reading["windows"][0]["resets_at"] = guard._iso_now(time.time() + 8 * 86400)
    assert guard.evaluate(payload, time.monotonic())
    assert guard.pending_decision("codex", payload)["id"] != old["id"]
    history = guard.decision_path("codex", project).parent / "history" / (old["id"] + ".json")
    assert json.loads(history.read_text())["decision"] == choice


def test_host_warning_bootstrap_keeps_unknown_facts_and_reuses_pending(case):
    guard, project, _, _, _ = case
    first = guard.offer_warning("gemini-cli", project, "private-fixture-host-warning-1")
    data = first["decision"]
    assert first["directive"] and data["decision"] == "pending"
    assert data["windows"] == {} and data["confirmed_usage"] == [] and data["credit"] is None
    again = guard.offer_warning("gemini-cli", project, "private-fixture-host-warning-2")
    assert again["decision"]["id"] == data["id"] and again["directive"] == first["directive"]
    claim = guard.decision_transition("gemini-cli", project, data["id"], "claim", tool="private-fixture")
    assert claim["claimed"]
    assert guard.offer_warning("gemini-cli", project, "private-fixture-host-warning-2")["directive"] is None


def test_host_warning_answer_covers_only_that_warning_episode(case):
    guard, project, _, _, _ = case
    data = guard.offer_warning("gemini-cli", project, "private-fixture-warning-1")["decision"]
    claim = guard.decision_transition("gemini-cli", project, data["id"], "claim", tool="private-fixture")
    token = claim["decision"]["delivery"]["claim_id"]
    guard.decision_transition("gemini-cli", project, data["id"], "delivered", claim_id=token,
                             request_id="private-warning-request")
    guard.decision_transition("gemini-cli", project, data["id"], "answer", claim_id=token,
                             request_id="private-warning-request", response_id="private-warning-response", answer="credits")
    assert guard.offer_warning("gemini-cli", project, "private-fixture-warning-1")["directive"] is None
    fresh = guard.offer_warning("gemini-cli", project, "private-fixture-warning-2")
    assert fresh["directive"] and fresh["decision"]["id"] != data["id"]
    history = guard.decision_path("gemini-cli", project).parent / "history" / (data["id"] + ".json")
    assert json.loads(history.read_text())["response_id"] == "private-warning-response"


@pytest.mark.parametrize("platform,reference", [("../codex", "fixture"), ("codex", ""), ("codex", "bad\nreference")])
def test_host_warning_bootstrap_rejects_missing_reference_or_unsafe_platform(case, platform, reference):
    guard, project, _, _, _ = case
    with pytest.raises(ValueError):
        guard.offer_warning(platform, project, reference)


def test_host_warning_without_probe_cannot_grant_gate_exemption(case, monkeypatch, tmp_path):
    guard, project, payload, reading, _ = case
    guard.offer_warning("codex", project, "private-fixture-host-warning")
    reading.update(status="unavailable", windows=[])
    gate = load("warning_bootstrap_gate_fixture", HOOKS.parents[1] / "scripts" / "completion_gate.py")
    monkeypatch.setattr(gate, "_usage_guard", lambda _: (guard, HOOKS))
    record = tmp_path / "record.json"
    record.write_text("{}")
    assert not gate.usage_limit_stop(payload, record, {}, project, time.monotonic() + 5)
    assert record.read_text() == "{}"


def test_real_cli_bootstraps_unknown_host_warning_in_private_home(case):
    import os
    import subprocess
    import sys
    guard, project, payload, _, home = case
    result = subprocess.run([sys.executable, "-I", "-B", str(HOOKS / "usage-guard.py"),
        "--decision-action", "offer-warning", "--project", str(project), "--platform", "gemini-cli",
        "--warning-reference", "private-cli-host-warning-fixture"],
        env=dict(os.environ, NEXUS_HOME=str(home), PYTHONDONTWRITEBYTECODE="1"),
        capture_output=True, text=True, timeout=10)
    assert result.returncode == 0, result.stderr
    output = json.loads(result.stdout)
    assert output["created"] and output["decision"]["windows"] == {}
    assert output["decision"]["confirmed_usage"] == [] and output["decision"]["credit"] is None
    assert "unknown" in output["directive"]


def test_host_warning_credit_answer_never_authorizes_later_tracked_period(case):
    guard, project, payload, _, _ = case
    old = guard.offer_warning("codex", project, "private-host-warning-fixture")["decision"]
    answer_fixture(case, "credits")
    assert guard.evaluate(payload, time.monotonic())
    current = guard.pending_decision("codex", payload)
    assert current["id"] != old["id"] and current["decision"] == "pending"
    assert current["origin"] == "tracked"


def test_source_less_host_warning_does_not_invent_gate_confirmation(case, monkeypatch, tmp_path):
    guard, project, _, _, _ = case
    guard.offer_warning("gemini-cli", project, "private-no-source-host-warning")
    payload = {"timestamp": guard._iso_now(time.time()), "hook_event_name": "AfterAgent", "cwd": str(project)}
    gate = load("source_less_warning_gate_fixture", HOOKS.parents[1] / "scripts" / "completion_gate.py")
    monkeypatch.setattr(gate, "_usage_guard", lambda _: (guard, HOOKS))
    record = tmp_path / "run.json"
    record.write_text("{}")
    assert not gate.usage_limit_stop(payload, record, {}, project, time.monotonic() + 5)


def test_credit_reminders_preserve_original_question_cost_snapshot(case):
    guard, project, payload, reading, _ = case
    reading["windows"].append({"name": "extra_credits", "state": "capped", "percent": 10,
        "used": 10, "limit": 100, "unit": "USD", "resets_at": None})
    offer(case)
    answered = answer_fixture(case, "credits")
    reading["windows"][1].update(percent=50, used=50)
    assert guard.evaluate(payload, time.monotonic())
    current = guard.pending_decision("codex", payload)
    assert current["credit"] == answered["credit"]
    assert current["current_credit"]["used"] == 50
    path = guard.decision_path("codex", project)
    assert guard.archive_answer(path, current)
    saved = json.loads((path.parent / "history" / (current["id"] + ".json")).read_text())
    assert saved["credit"]["used"] == 10 and "current_credit" not in saved


@pytest.mark.parametrize("delivery", ["claimed", "delivered", "uncertain"])
def test_new_prompt_gets_existing_pending_status_once(case, delivery):
    guard, project, payload, _, _ = case
    data = offer(case)
    claim = guard.decision_transition("codex", project, data["id"], "claim", tool="private-fixture")
    token = claim["decision"]["delivery"]["claim_id"]
    if delivery == "delivered":
        guard.decision_transition("codex", project, data["id"], "delivered", claim_id=token, request_id="private-status-request")
    elif delivery == "uncertain":
        guard.decision_transition("codex", project, data["id"], "uncertain", claim_id=token)
    before = guard.pending_decision("codex", payload)
    new = dict(payload, session_id="new-session", hook_event_name="UserPromptSubmit")
    status = guard.evaluate(new, time.monotonic())
    text = json.dumps(status)
    assert data["id"] in text and "Stop new work" in text
    assert "Do not claim or ask another question" in text
    assert "--decision-action" not in text
    assert guard.evaluate(new, time.monotonic()) is None
    assert guard.evaluate(dict(new, hook_event_name="PostToolUse"), time.monotonic()) is None
    assert guard.evaluate(dict(new, session_id="stop-only", hook_event_name="Stop"), time.monotonic()) is None
    after = guard.pending_decision("codex", payload)
    assert after["id"] == before["id"] and after["delivery"] == before["delivery"]
    assert after["decision"] == "pending"
    assert not guard.decision_transition("codex", project, data["id"], "claim", tool="text")["claimed"]


@pytest.mark.parametrize("choice", ["wait", "handoff"])
def test_saved_stop_answer_reaches_each_new_session_once(case, choice):
    guard, _, payload, _, _ = case
    offer(case)
    answered = answer_fixture(case, choice)
    new = dict(payload, session_id="new-answer-session", hook_event_name="UserPromptSubmit")
    status = json.dumps(guard.evaluate(new, time.monotonic()))
    assert answered["id"] in status and choice in status
    assert "Do not claim or ask another question" in status
    assert guard.evaluate(new, time.monotonic()) is None
    after = guard.pending_decision("codex", payload)
    for key in ("id", "decision", "delivery", "recorded_at", "response_id"):
        assert after[key] == answered[key]


def test_status_session_storage_stays_bounded(case):
    guard, project, payload, _, _ = case
    data = offer(case)
    guard.decision_transition("codex", project, data["id"], "claim", tool="private-fixture")
    for number in range(130):
        new = dict(payload, session_id=f"bounded-{number}")
        assert guard.evaluate(new, time.monotonic())
    after = guard.pending_decision("codex", payload)
    assert len(after["status_sessions"]) == 128
    assert guard.evaluate(new, time.monotonic()) is None


@pytest.mark.parametrize("value", [None, [], "unsafe/id"])
def test_unknown_session_gets_conservative_status_without_notice_write(case, value):
    guard, project, payload, _, _ = case
    data = offer(case)
    guard.decision_transition("codex", project, data["id"], "claim", tool="private-fixture")
    before = guard.pending_decision("codex", payload)
    for _ in range(2):
        assert "Stop new work" in json.dumps(guard.evaluate(dict(payload, session_id=value), time.monotonic()))
    assert guard.pending_decision("codex", payload) == before


def test_notice_failure_still_reports_stop_and_preserves_authority(case, monkeypatch):
    guard, project, payload, _, _ = case
    data = offer(case)
    guard.decision_transition("codex", project, data["id"], "claim", tool="private-fixture")
    before = guard.pending_decision("codex", payload)
    monkeypatch.setattr(guard, "save_state", lambda *_: False)
    status = json.dumps(guard.evaluate(dict(payload, session_id="write-failure"), time.monotonic()))
    assert data["id"] in status and "Stop new work" in status
    assert "no spending authority" in status
    assert guard.pending_decision("codex", payload) == before


def test_status_normalizes_oversized_notice_map_and_uses_valid_fallback(case):
    guard, project, payload, _, _ = case
    data = offer(case)
    guard.decision_transition("codex", project, data["id"], "claim", tool="private-fixture")
    current = guard.pending_decision("codex", payload)
    current["status_sessions"] = {f"old-{n}": "pending" for n in range(140)}
    assert guard.save_state(guard.decision_path("codex", project), current)
    new = dict(payload, session_id=["malformed"], conversation_id="fallback-session")
    assert guard.evaluate(new, time.monotonic())
    saved = guard.pending_decision("codex", payload)
    assert len(saved["status_sessions"]) == 128
    assert saved["status_sessions"]["fallback-session"] == "pending"
    assert guard.evaluate(new, time.monotonic()) is None
