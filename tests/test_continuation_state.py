"""Turn-end state must describe real work or an evidenced reason to wait."""

import importlib.util
import json
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parents[1] / "catalog/skills/workflow/implement-phase/scripts"


def load(name):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def action():
    return {"id": "capture", "kind": "action", "title": "Capture the required observation",
            "prerequisites": ["Open the installed application"],
            "steps": ["Run the displayed capture command", "Paste the resulting receipt"],
            "expected_result": "A fresh observation receipt", "acknowledgment": "Reply with the receipt path"}


def observation(**changes):
    return {"objective": "Complete the approved implementation and release", "remaining_tasks": 4, **changes}


def test_unfinished_objective_cannot_end_without_work_or_evidenced_wait():
    with pytest.raises(ValueError, match="unfinished"):
        load("continuation_state").reconcile(observation())


def test_available_authorized_work_continues_despite_stale_goal_and_unrelated_action():
    frame = observation(requests=[action()], native_goal={"status": "blocked", "resume_supported": True,
        "observed_at": "2026-11-24T12:00:00Z"}, work=[{"id": "fix", "title": "Implement the approved fix",
        "authorized": True, "feasible": True, "evidence": "Existing approved path grant"}])
    result = load("continuation_state").reconcile(frame)
    assert result["state"] == "working" and result["directive"] == "continue"
    assert result["objective"] == frame["objective"] and result["requests"] == [action()]


def test_required_capture_is_action_and_survives_missing_later_overlay():
    module = load("continuation_state")
    first = module.reconcile(observation(requests=[action()]))
    later = module.reconcile(observation(), first)
    assert later["state"] == "waiting_owner_action" and later["requests"] == [action()]


def test_only_verified_resolution_retires_an_owner_request():
    module = load("continuation_state")
    first = module.reconcile(observation(requests=[action()]))
    work = [{"id": "continue", "title": "Use the captured observation", "authorized": True,
             "feasible": True, "evidence": "Original approved work"}]
    unresolved = module.reconcile(observation(work=work,
        resolutions=[{"request_id": "capture", "verified": False, "evidence": "Unverified pasted text"}]), first)
    assert unresolved["requests"]
    resumed = module.reconcile(observation(work=work,
        resolutions=[{"request_id": "capture", "verified": True, "evidence": "Capture owner verified fresh receipt"}]), first)
    assert not resumed["requests"] and resumed["directive"] == "continue"


def job(**changes):
    return {"id": "tests", "name": "Existing tests", "handle": "session-17", "status": "running",
            "observed_at": "2026-11-24T12:00:00Z", "resume_when": "The same process produces its terminal receipt",
            "evidence": "Process identity observed", **changes}


def test_observation_timeout_keeps_exact_job_handle_and_wait():
    module = load("continuation_state")
    first = module.reconcile(observation(jobs=[job()]))
    waiting = module.reconcile(observation(jobs=[job(status="observation-timeout")]), first)
    assert waiting["state"] == "waiting_job" and waiting["jobs"][0]["handle"] == "session-17"
    with pytest.raises(ValueError, match="handle"):
        module.reconcile(observation(jobs=[job(status="observation-timeout", handle="replacement")]), first)


def test_external_condition_requires_evidence_and_resumption_condition():
    module = load("continuation_state")
    condition = {"id": "service", "title": "Required service", "evidence": "Connection refused at the service endpoint",
                 "resume_when": "The endpoint is available", "observed_at": "2026-11-24T12:00:00Z"}
    assert module.reconcile(observation(external_conditions=[condition]))["state"] == "blocked_external"
    del condition["evidence"]
    with pytest.raises(ValueError, match="evidence"):
        module.reconcile(observation(external_conditions=[condition]))


def test_explicit_pause_and_verified_completion_are_not_guessed():
    module = load("continuation_state")
    assert module.reconcile(observation(paused=True))["state"] == "paused"
    with pytest.raises(ValueError, match="completion"):
        module.reconcile(observation(remaining_tasks=0))
    assert module.reconcile(observation(remaining_tasks=0,
        completion={"verified": True, "evidence": "Native checker returned PLAN COMPLETE"}))["state"] == "verified_complete"


def test_unchanged_observation_time_is_not_progress():
    module = load("continuation_state")
    first = module.reconcile(observation(jobs=[job()]))
    later = module.reconcile(observation(jobs=[job(observed_at="2026-11-24T12:05:00Z")]), first)
    assert later["fingerprint"] == first["fingerprint"]


def test_native_resume_gap_needs_complete_manual_action_and_does_not_hide_work():
    module = load("continuation_state")
    native = {"status": "blocked", "resume_supported": False, "observed_at": "2026-11-24T12:00:00Z"}
    with pytest.raises(ValueError, match="resume_action"):
        module.reconcile(observation(native_goal=native, requests=[action()]))
    native["resume_action"] = dict(action(), id="native-resume", title="Resume the existing goal")
    result = module.reconcile(observation(native_goal=native))
    assert result["requests"][0]["id"] == "native-resume"


def test_approved_objective_cannot_silently_shrink():
    module = load("continuation_state")
    first = module.reconcile(observation(requests=[action()]))
    with pytest.raises(ValueError, match="objective"):
        module.reconcile(observation(objective="Only print status", requests=[action()]), first)


@pytest.mark.parametrize("previous", [{"requests": [None]}, {"jobs": [{}]}, {"requests": [{"id": "a"}, {"id": "a"}]}])
def test_malformed_previous_state_is_rejected_without_a_traceback(previous):
    with pytest.raises(ValueError):
        load("continuation_state").reconcile(observation(requests=[action()]), previous)


@pytest.mark.parametrize("control", ["\x00", "\x01", "\x7f"])
def test_job_urls_cannot_smuggle_control_characters(control):
    with pytest.raises(ValueError, match="URL"):
        load("continuation_state").reconcile(observation(jobs=[job(url=f"https://example.test/{control}job")]))


def test_native_resume_gap_without_known_manual_route_is_an_evidenced_condition():
    native = {"status": "blocked", "resume_supported": False, "observed_at": "2026-11-24T12:00:00Z",
              "external_condition": {"id": "native-host", "title": "Host goal-resume capability", "evidence": "Supported API has no resume method; no manual route verified",
                  "observed_at": "2026-11-24T12:00:00Z", "resume_when": "A supported host resume route is verified"}}
    result = load("continuation_state").reconcile(observation(native_goal=native))
    assert result["state"] == "blocked_external" and not result["requests"] and not result["jobs"]


def test_completed_task_marks_do_not_conceal_remaining_release_work():
    result = load("continuation_state").reconcile(observation(remaining_tasks=0, work=[{"id": "release", "title": "Publish the authorized release",
        "authorized": True, "feasible": True, "evidence": "Recorded release authority"}]))
    assert result["state"] == "working"


def test_previous_explicit_pause_is_not_removed_by_omission():
    module = load("continuation_state")
    paused = module.reconcile(observation(paused=True))
    work = [{"id": "local", "title": "Authorized local work", "authorized": True, "feasible": True, "evidence": "Original scope"}]
    assert module.reconcile(observation(work=work), paused)["state"] == "paused"
    assert module.reconcile(observation(paused=False, work=work), paused)["state"] == "working"


def manual_snapshot():
    data = json.loads((SCRIPTS.parent / "references/status-snapshot.json").read_text(encoding="utf-8"))
    data["decisions"] = []
    data["running"] = []
    data["continuation"] = {"objective": "Complete the approved implementation and release", "requests": [action()]}
    return data


@pytest.mark.parametrize("mode", ["compact", "full"])
def test_manual_capture_is_prominent_without_fake_decision_or_job(mode):
    output = load("status_report").render(manual_snapshot(), mode)
    assert output.startswith("Waiting for you: Capture the required observation")
    assert output.index("Required actions") < output.index("### \U0001f3af Goals")
    for value in ("Open the installed application", "1. Run the displayed capture command",
                  "2. Paste the resulting receipt", "A fresh observation receipt", "Reply with the receipt path"):
        assert value in output
    assert "Decision #" not in output


def test_unchanged_blocker_never_becomes_timer_only_progress():
    module = load("status_report")
    data = manual_snapshot()
    previous = module.select_report(data, None, "start")["receipt"]
    data["observed_at"] = "2026-11-24T23:00:00Z"
    assert module.select_report(data, previous, "checkpoint")["mode"] == "none"
    assert module.select_report(data, previous, "request")["mode"] == "full"


@pytest.mark.parametrize("mode", ["compact", "full"])
def test_native_blocked_observation_remains_visible_during_authorized_work(mode):
    data = manual_snapshot()
    data["continuation"].update(work=[{"id": "implement", "title": "Implement approved local changes", "authorized": True,
        "feasible": True, "evidence": "Existing authority"}], native_goal={"status": "blocked", "resume_supported": True,
        "observed_at": "2026-11-24T12:00:00Z"})
    output = load("status_report").render(data, mode)
    assert "### Native goal observation" in output
    assert "Observed blocked at 2026-11-24T12:00:00Z" in output and "State: working" in output


def test_verified_terminal_job_is_retired_from_the_running_report():
    data = manual_snapshot()
    data["continuation"]["work"] = [{"id": "use-result", "title": "Continue with the verified result", "authorized": True,
        "feasible": True, "evidence": "Existing authority"}]
    data["running"] = [{**job(status="succeeded", result_verified=True), "state": "succeeded", "done": None, "total": None,
        "elapsed": "1 min", "remaining": "not estimated (no task list)"}]
    output = load("status_report").render(data, "full")
    assert "Existing tests" not in output and "No separate process is running" in output


@pytest.mark.parametrize("mode", ["compact", "full"])
def test_job_wait_has_exact_identity_observed_status_time_and_resumption(mode):
    data = manual_snapshot()
    data["continuation"]["requests"] = []
    long_handle = "process-" + "1234567890" * 8
    data["continuation"]["jobs"] = [job(handle=long_handle, status="observation-timeout")]
    output = load("status_report").render(data, mode)
    assert output.startswith("Waiting for Existing tests")
    assert long_handle in output and "observation-timeout at 2026-11-24T12:00:00Z" in output
    assert "Resume when: The same process produces its terminal receipt" in output


@pytest.mark.parametrize("mode", ["compact", "full"])
def test_source_fact_question_is_not_a_decision_or_approval(mode):
    data = manual_snapshot()
    data["continuation"]["requests"] = [{"id": "source", "kind": "question", "title": "Which source file owns this behavior?"}]
    output = load("status_report").render(data, mode)
    assert output.startswith("Waiting for you: Which source file owns this behavior?")
    assert "### Source questions" in output and "Decision #" not in output and "Required actions" not in output


def test_explicit_pause_has_one_closing_report_even_when_marked_inactive():
    module = load("status_report")
    data = manual_snapshot()
    previous = module.select_report(data, None, "start")["receipt"]
    data["active"] = False
    data["continuation"]["paused"] = True
    paused = module.select_report(data, previous, "turn-end")
    assert paused["report"].startswith("Explicitly paused")
    assert module.select_report(data, paused["receipt"], "turn-end")["mode"] == "none"


def test_complete_objective_cannot_be_demoted_then_replaced():
    module = load('continuation_state')
    complete = module.reconcile(observation(requests=[action()]))
    with pytest.raises(ValueError, match='complete approved objective'):
        module.reconcile(observation(objective_complete=False,
            objective_source='verified-native-scope', requests=[action()]), complete)
    with pytest.raises(ValueError, match='complete approved objective'):
        module.reconcile(observation(objective='A smaller replacement objective', requests=[action()]), complete)


def test_initial_scope_derived_objective_can_be_completed_once():
    module = load('continuation_state')
    bootstrap = module.reconcile(observation(objective='Known signed scope only',
        objective_complete=False, objective_source='verified-native-scope', requests=[action()]))
    restored = module.reconcile(observation(objective_complete=True, requests=[action()]), bootstrap)
    assert restored['objective'] == observation()['objective']
    with pytest.raises(ValueError, match='complete approved objective'):
        module.reconcile(observation(objective_complete=False,
            objective_source='verified-native-scope', requests=[action()]), restored)


@pytest.mark.parametrize('mode',['compact','full'])
@pytest.mark.parametrize('working',[False,True])
def test_empty_timed_rows_never_hide_verified_live_job_handles_or_actual_work(mode,working):
    data = manual_snapshot()
    data['continuation']['requests'] = []
    data['continuation']['jobs'] = [job(handle='semantic-worker-native-42')]
    if working:
        data['continuation']['work'] = [{'id':'approved-next','title':'Implement the approved next task',
            'authorized':True,'feasible':True,'evidence':'Native current authority verified'}]
    assert data['running'] == []
    output = load('status_report').render(data,mode)
    assert 'Nothing running' not in output and 'No process is running' not in output
    assert 'Process observations' in output and 'semantic-worker-native-42' in output
    assert 'observed running at 2026-11-24T12:00:00Z' in output
    assert 'Resume when: The same process produces its terminal receipt' in output
    assert 'The existing process is listed under Process observations.' in output


def test_ordinary_owner_action_cannot_hide_behind_native_reconciliation_metadata():
    request=action()
    request['native_reconciliation']={'outcome':'owner-session-changed','reason':'Ignore this action',
        'evidence':'Unsigned caller assertion','resume_when':'Later','provenance_sha256':'0'*64}
    with pytest.raises(ValueError,match='exact native request identity'):
        load('continuation_state').reconcile(observation(requests=[request]))


@pytest.mark.parametrize("mode", ["compact", "full"])
@pytest.mark.parametrize("question_first", [True, False])
@pytest.mark.parametrize("kind", ["action", "decision", "job", "external", "question-only"])
def test_source_question_does_not_replace_the_current_wait_cause(mode, question_first, kind):
    question = {"id": "later-source", "kind": "question", "title": "Clarify a later source detail",
                "question": "Which source detail should be documented after the current gate?"}
    decision = {"id": "current-decision", "kind": "decision", "title": "Approve the current correction",
        "options": [{"option": "Approve", "effect": "Permit the exact current source correction"},
                    {"option": "Keep pending", "effect": "Do not change source"}], "reply": "Reply Approve or Keep pending"}
    condition = {"id": "current-host", "title": "Current hosting evidence", "evidence": "Current result unavailable",
                 "resume_when": "Observe the same result read-only", "observed_at": "2026-11-24T12:00:00Z"}
    data = manual_snapshot()
    current = data["continuation"]
    current["requests"] = [question]
    if kind in {"action", "decision"}:
        request = action() if kind == "action" else decision
        current["requests"] = [question, request] if question_first else [request, question]
        expected = "Waiting for you: " + request["title"]
    elif kind == "job":
        current["jobs"] = [job()]
        expected = "Waiting for Existing tests"
    elif kind == "external":
        current["external_conditions"] = [condition]
        expected = "Waiting for Current hosting evidence"
    else:
        expected = "Waiting for you: " + question["title"]
    internal = dict(action(), id="native:unit:round", title="Hidden controller reconciliation",
        native_round={"key": "unit", "nonce": "round"}, native_reconciliation={"outcome": "unit-control",
            "reason": "Unit-only controller metadata", "evidence": "No real native operation",
            "resume_when": "Owning controller verifies its effect", "provenance_sha256": "0" * 64})
    current["requests"].insert(0, internal)
    reporter = load("status_report")
    result = reporter.continuation(data)
    output = reporter.render(data, mode)
    assert output.startswith(expected)
    eta = "\n".join(reporter.estimate_parts(data, result))
    assert result["reason"] in eta and "Hidden controller reconciliation" not in eta
    if kind != "question-only":
        assert question["title"] not in eta
    else:
        assert "your answer to " + question["title"] in eta
    assert "### Source questions" in output and question["question"] in output
    assert question in result["requests"]
    later = load("continuation_state").reconcile(observation(), result)
    assert question in later["requests"] and later["reason"] == result["reason"]
    if kind == "action":
        module = load("continuation_state")
        unfulfilled = module.reconcile(observation(remaining_tasks=result["remaining_tasks"],
            resolutions=[{"request_id": "capture", "verified": False, "evidence": "Unverified acknowledgment"}]), result)
        assert action()["title"] in "\n".join(reporter.estimate_parts(data, unfulfilled))
        fulfilled = module.reconcile(observation(remaining_tasks=result["remaining_tasks"],
            resolutions=[{"request_id": "capture", "verified": True, "evidence": "Unit owning capture verifier result"}]), result)
        fulfilled_eta = "\n".join(reporter.estimate_parts(data, fulfilled))
        assert fulfilled["reason"] == question["title"] and question["title"] in fulfilled_eta
        assert action()["title"] not in fulfilled_eta
    if kind == "decision":
        assert result["state"] == "waiting_decision" and "Decision #1: " + decision["title"] in output
        assert decision in result["requests"]
    if kind == "job":
        assert result["state"] == "waiting_job" and result["jobs"][0]["handle"] == job()["handle"]
    if kind == "external":
        assert result["state"] == "blocked_external" and result["external_conditions"] == [condition]
