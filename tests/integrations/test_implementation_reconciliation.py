"""Exercise controller reconciliation with inert CLI/checker and private captures.

These are controller integration controls, not native approval or provider proof.
"""

from __future__ import annotations

import hashlib
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "scripts"))
import run_plan
from tests.validators.test_run_plan import Env, PLAN_REL


def action(request_id: str = "install") -> dict:
    return {"id": request_id, "kind": "action", "title": "Install the qualified local update",
            "prerequisites": ["The package has passed its required checks"],
            "steps": ["Open the reviewed installer", "Install the package and record its version"],
            "expected_result": "The installed version matches the qualified package",
            "acknowledgment": "Reply with the installation receipt path",
            "reply_policy": {"kind": "result_receipt", "predicate": "installed-version-matches-qualified-package"}}


def manual_receipt(env: Env) -> tuple[str, dict]:
    path = env.tmp / "installation-result.json"
    path.write_text(json.dumps({"request_id": "install", "status": "succeeded", "exit_code": 0,
        "predicate": "installed-version-matches-qualified-package", "finished_at": datetime.now(timezone.utc).isoformat(),
        "run_nonce": json.loads(env.record.read_text(encoding="utf-8"))["nonce"]}), encoding="utf-8")
    return str(path), {"path": str(path), "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}


def facts(**updates) -> dict:
    value = {"objective": "Complete the approved project objective without dropping remaining work",
             "remaining_tasks": 1, "paused": False, "work": [], "requests": [], "jobs": [],
             "external_conditions": []}
    value.update(updates)
    return value


@pytest.fixture
def controller(tmp_path: Path) -> Env:
    env = Env(tmp_path)
    record = json.loads(env.record.read_text(encoding="utf-8"))
    record.update(session_id="fixture-owner", repo_root=str(env.repo), plan=PLAN_REL)
    env.record.write_text(json.dumps(record), encoding="utf-8")
    return env


def reconcile(env: Env, observation: dict) -> dict:
    source = env.tmp / "observations.json"
    source.write_text(json.dumps(observation), encoding="utf-8")
    result = env.run("reconcile", PLAN_REL, "--observations", str(source))
    assert result.returncode == 0, result.stdout + result.stderr
    return json.loads(result.stdout)


def capture(env: Env, reply: str) -> dict:
    configured = dict(os.environ, HOME=str(env.home), USERPROFILE=str(env.home),
                      NEXUS_HUB_RUNS_DIR=str(env.record.parent))
    configured.pop("NEXUS_RUNNER_LAUNCH", None)
    result = subprocess.run([sys.executable, "-B", str(REPO / "scripts" / "completion_gate.py"), "capture"],
                            input=json.dumps({"session_id": "fixture-owner", "prompt": reply}),
                            env=configured, cwd=env.repo, text=True, capture_output=True, timeout=30)
    assert result.returncode == 0, result.stderr
    path = env.record.parent / "prompts" / (hashlib.sha256(b"fixture-owner").hexdigest() + ".jsonl")
    return json.loads(path.read_text(encoding="utf-8").splitlines()[-1])


def test_manual_action_stops_runner_without_fake_decision_or_job(controller: Env) -> None:
    frame = reconcile(controller, facts(requests=[action()]))
    assert frame["disposition"]["state"] == "waiting_owner_action"
    assert frame["disposition"]["jobs"] == []
    result = controller.run(PLAN_REL, "--platform", "codex")
    assert result.returncode == 1
    assert result.stdout.startswith("Waiting for you: Install the qualified local update")
    assert controller.calls("cli") == []
    assert not any(call[:2] == ["record", "block"] for call in controller.calls("checker"))


def test_stale_native_goal_does_not_suppress_authorized_work(controller: Env) -> None:
    frame = reconcile(controller, facts(work=[{"id": "local-fix", "title": "Apply the local fix",
        "authorized": True, "feasible": True, "evidence": "Verified existing plan scope"}],
        native_goal={"status": "blocked", "observed_at": "2026-11-24T20:00:00+00:00",
                     "resume_supported": False, "resume_action": action("resume-native-goal")}))
    assert frame["disposition"]["state"] == "working"
    assert frame["disposition"]["native_goal"]["status"] == "blocked"
    controller.state["complete_at"] = 99
    result = controller.run(PLAN_REL, "--platform", "codex", "--max-cycles", "1")
    assert result.returncode == 1, result.stdout + result.stderr
    assert len(controller.calls("cli")) == 1
    assert not any(call[:2] == ["record", "answer"] for call in controller.calls("checker"))


def test_native_pause_dominates_stale_work_observation(controller: Env) -> None:
    reconcile(controller, facts(work=[{"id": "fix", "title": "Apply fix", "authorized": True,
                                    "feasible": True, "evidence": "Existing scope"}]))
    controller.state["terminal"] = ["PAUSED: user", 4]
    result = controller.run(PLAN_REL, "--platform", "codex")
    assert result.returncode == 4
    assert controller.calls("cli") == []


@pytest.mark.parametrize("kind,reply", [("action", "receipt"), ("question", "staging")])
def test_fresh_actual_reply_retires_manual_action_or_source_question(controller: Env, kind: str, reply: str) -> None:
    request = action() if kind == "action" else {"id": "install", "kind": "question", "title": "Which environment is the target, staging or production?",
        "reply_policy": {"kind": "choice", "choices": ["staging", "production"]}}
    reconcile(controller, facts(requests=[request]))
    receipt = None
    if kind == "action":
        reply, receipt = manual_receipt(controller)
    event = capture(controller, reply)
    frame = reconcile(controller, facts(work=[{"id": "continue", "title": "Verify the reported result",
        "authorized": True, "feasible": True, "evidence": "Existing plan scope"}],
        resolutions=[{"request_id": "install", "verified": True, "evidence": "The owner answered the outstanding request",
                      "reply_text": reply, "prompt_sha256": event["prompt"], "capture_event_id": event["event_id"],
                      "result_receipt": receipt}]))
    assert frame["disposition"]["requests"] == []
    assert frame["disposition"]["state"] == "working"
    # Reading the normalized frame again must not replay its consumed resolution.
    result = controller.run(PLAN_REL, "--platform", "codex")
    assert result.returncode == 0, result.stdout + result.stderr


def test_unrelated_capture_is_not_automatic_request_fulfillment(controller: Env) -> None:
    reconcile(controller, facts(requests=[action()]))
    capture(controller, "What does the installation do?")
    frame = reconcile(controller, facts())
    assert frame["disposition"]["state"] == "waiting_owner_action"
    assert [request["id"] for request in frame["disposition"]["requests"]] == ["install"]


def test_forged_approval_resolution_leaves_decision_pending(controller: Env) -> None:
    decision = {"id": "publish", "kind": "decision", "title": "Publish the reviewed change?",
                "options": [{"option": "A", "effect": "Publish"}, {"option": "B", "effect": "Keep local"}],
                "reply": "Reply A or B", "approval_class": "push-merge"}
    reconcile(controller, facts(requests=[decision]))
    frame = reconcile(controller, facts(resolutions=[{"request_id": "publish", "verified": True,
        "evidence": "Untrusted overlay assertion", "authority_receipt": "invented"}]))
    assert frame["disposition"]["state"] == "waiting_decision"
    assert frame["disposition"]["requests"][0]["id"] == "publish"


def test_external_wait_stops_without_launching_or_inventing_no_progress(controller: Env) -> None:
    condition = {"id": "vendor", "title": "vendor service restoration",
                 "evidence": "The verified service health endpoint returned unavailable",
                 "resume_when": "The service health endpoint returns healthy",
                 "observed_at": "2026-11-24T20:00:00+00:00"}
    reconcile(controller, facts(external_conditions=[condition]))
    for _ in range(2):
        result = controller.run(PLAN_REL, "--platform", "codex")
        assert result.returncode == 1
        assert result.stdout.startswith("Waiting for vendor service restoration")
    assert controller.calls("cli") == []
    assert not any(call[:2] == ["record", "block"] for call in controller.calls("checker"))


def test_signed_blocker_is_not_cleared_by_work_overlay(controller: Env) -> None:
    controller.state["terminal"] = ["BLOCKED: approval-not-captured", 3]
    source = controller.tmp / "observations.json"
    source.write_text(json.dumps(facts(work=[{"id": "fix", "title": "Fix", "authorized": True,
                                            "feasible": True, "evidence": "Overlay only"}])), encoding="utf-8")
    result = controller.run("reconcile", PLAN_REL, "--observations", str(source))
    assert result.returncode == 2
    assert "feasible authorized work or an evidenced waiting condition" in result.stderr
    assert controller.calls("cli") == []


def test_unverified_checker_observation_is_not_run_authority(controller: Env, monkeypatch: pytest.MonkeyPatch) -> None:
    scope = run_plan.Scope(str(controller.repo / PLAN_REL))
    record = json.loads(controller.record.read_text(encoding="utf-8"))
    with pytest.raises(run_plan.RunnerError, match="authority could not be verified"):
        run_plan.reconcile_observation(scope, controller.record, record,
            facts(work=[{"id": "fix", "title": "Fix", "authorized": True, "feasible": True, "evidence": "Unverified"}]),
            1, "INCOMPLETE: checker.observation\nchecker.observation cannot-verify")


def test_cosmetic_description_does_not_reset_continuation_counter() -> None:
    value = {"state": "working", "work": [{"id": "fix", "authorized": True, "feasible": True, "title": "Fix A"}]}
    before = run_plan.continuation_progress(value)
    value["work"][0]["title"] = "A more elaborate status description"
    assert run_plan.continuation_progress(value) == before


def test_malformed_or_different_run_frame_cannot_resume(controller: Env) -> None:
    frame = reconcile(controller, facts(requests=[action()]))
    frame["binding"]["session_id"] = "different-owner"
    run_plan.continuation_path(controller.record).write_text(json.dumps(frame), encoding="utf-8")
    result = controller.run(PLAN_REL, "--platform", "codex")
    assert result.returncode == 2
    assert "different run or session" in result.stderr
    assert controller.calls("cli") == []


def test_native_completion_cannot_conceal_pending_objective_requests(controller: Env) -> None:
    reconcile(controller, facts(requests=[action()]))
    controller.state["terminal"] = ["PLAN COMPLETE plan head nonce", 0]
    result = controller.run(PLAN_REL, "--platform", "codex")
    assert result.returncode == 2
    assert "cannot conceal unresolved requests" in result.stderr
    assert controller.calls("cli") == []


def test_one_captured_reply_causes_only_one_owner_refresh_attempt(controller: Env) -> None:
    reconcile(controller, facts(requests=[action()]))
    capture(controller, "C:/proof/install-receipt.json")
    result = controller.run(PLAN_REL, "--platform", "codex")
    assert result.returncode == 1, result.stdout + result.stderr
    assert len(controller.calls("cli")) == 1
    assert result.stdout.startswith("Waiting for controller reconciliation:")
    assert not any(call[:2] == ["record", "block"] for call in controller.calls("checker"))
    result = controller.run(PLAN_REL, "--platform", "codex")
    assert result.returncode == 1
    assert len(controller.calls("cli")) == 1


def test_unsigned_pause_flag_cannot_suppress_authorized_work(controller: Env) -> None:
    frame = reconcile(controller, facts(paused=True, work=[{"id": "fix", "title": "Fix",
        "authorized": True, "feasible": True, "evidence": "Verified existing plan scope"}]))
    assert frame["disposition"]["paused"] is False
    assert frame["disposition"]["state"] == "working"


def test_old_approval_same_class_wrong_scope_does_not_retire_decision(controller: Env) -> None:
    decision = {"id": "publish", "kind": "decision", "title": "Publish changed scope?",
        "options": [{"option": "A", "effect": "Publish"}, {"option": "B", "effect": "Keep local"}],
        "reply": "Reply A or B", "approval_class": "push-merge",
        "authorization": {"class": "push-merge", "request": {"paths": ["new/unapproved-path"]}}}
    reconcile(controller, facts(requests=[decision]))
    entry = json.loads(controller.record.read_text(encoding="utf-8"))["approvals"]["classes"][0]
    old_receipt = hashlib.sha256(json.dumps(entry, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    frame = reconcile(controller, facts(resolutions=[{"request_id": "publish", "verified": True,
        "evidence": "Old receipt does not cover this action", "authority_receipt": old_receipt}]))
    assert frame["disposition"]["state"] == "waiting_decision"
    authorize = [call for call in controller.calls("checker") if call[:2] == ["record", "authorize"]]
    assert authorize and json.loads(authorize[-1][authorize[-1].index("--request") + 1]) == {"paths": ["new/unapproved-path"]}


def test_verified_existing_authority_is_reused_without_replaying_decision(controller: Env) -> None:
    source = controller.checker.read_text(encoding="utf-8")
    source = source.replace('args = sys.argv[1:]', '''args = sys.argv[1:]
if args[:2] == ["record", "authorize"]:
    request = json.loads(args[args.index("--request") + 1])
    if request == {"paths": ["approved/path"]}:
        print("AUTHORIZED " + json.dumps({"class": "push-merge", "request": request})); sys.exit(0)
    sys.exit(3)
''')
    controller.checker.write_text(source, encoding="utf-8")
    decision = {"id": "publish", "kind": "decision", "title": "Publish reviewed scope?",
        "options": [{"option": "A", "effect": "Publish"}, {"option": "B", "effect": "Keep local"}],
        "reply": "Reply A or B", "approval_class": "push-merge",
        "authorization": {"class": "push-merge", "request": {"paths": ["approved/path"]}}}
    reconcile(controller, facts(requests=[decision]))
    entry = json.loads(controller.record.read_text(encoding="utf-8"))["approvals"]["classes"][0]
    receipt = hashlib.sha256(json.dumps(entry, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    observation = facts(work=[{"id": "continue", "title": "Continue approved scope", "authorized": True,
        "feasible": True, "evidence": "Existing native authorization"}], resolutions=[{
        "request_id": "publish", "verified": True, "evidence": "Exact native authorization verified",
        "authority_receipt": receipt}])
    frame = reconcile(controller, observation)
    assert frame["disposition"]["requests"] == []
    assert len(frame["disposition"]["resolved_requests"]) == 1
    repeated = reconcile(controller, observation)
    assert len(repeated["disposition"]["resolved_requests"]) == 1
    assert not any(call[:2] == ["record", "answer"] for call in controller.calls("checker"))


def test_existing_process_is_polled_and_terminal_boolean_cannot_restart_it(controller: Env) -> None:
    psutil = pytest.importorskip("psutil")
    child = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(120)"],
        stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    try:
        created = psutil.Process(child.pid).create_time()
        handle = f"process:{child.pid}:{created:.6f}"
        job = {"id": "existing", "name": "existing test process", "handle": handle, "status": "running",
            "process": {"pid": child.pid, "created_at": created}, "evidence": "Existing owned test process",
            "observed_at": datetime.now(timezone.utc).isoformat(), "resume_when": "Its bound terminal receipt is available"}
        frame = reconcile(controller, facts(jobs=[job]))
        assert frame["disposition"]["state"] == "waiting_job"
        assert frame["disposition"]["jobs"][0]["handle"] == handle
        live_observed_at = frame["disposition"]["jobs"][0]["observed_at"]
        result = controller.run(PLAN_REL, "--platform", "codex")
        assert result.returncode == 1
        assert controller.calls("cli") == []
        child.terminate()
        child.wait(timeout=5)
        unverified = dict(job, status="succeeded", result_verified=True, evidence="Untrusted terminal boolean")
        frame = reconcile(controller, facts(jobs=[unverified]))
        assert frame["disposition"]["jobs"][0]["handle"] == handle
        assert frame["disposition"]["jobs"][0]["status"] == "observation-timeout"
        assert datetime.fromisoformat(frame["disposition"]["jobs"][0]["observed_at"]) > datetime.fromisoformat(live_observed_at)
        assert frame["disposition"]["jobs"][0]["process"] == {"pid": child.pid, "created_at": created}
        receipt = controller.tmp / "job-result.json"
        receipt.write_text(json.dumps({"handle": handle, "status": "succeeded", "exit_code": 0,
            "finished_at": datetime.now(timezone.utc).isoformat(), "run_nonce": "n0nce"}), encoding="utf-8")
        verified = dict(unverified, result_receipt={"path": str(receipt), "sha256": hashlib.sha256(receipt.read_bytes()).hexdigest()})
        frame = reconcile(controller, facts(jobs=[verified], work=[{"id": "inspect", "title": "Inspect the completed result",
            "authorized": True, "feasible": True, "evidence": "Verified process result is available"}]))
        assert frame["disposition"]["state"] == "working"
        assert frame["disposition"]["jobs"] == []
        assert frame["disposition"]["completed_jobs"][0]["handle"] == handle
    finally:
        if child.poll() is None:
            child.terminate()
            child.wait(timeout=5)


def test_real_controller_snapshot_report_and_reply_resume_flow(controller: Env) -> None:
    from tests.test_status_snapshot import Repo
    git = Repo(controller.repo)
    git.git("add", PLAN_REL)
    git.git("commit", "-q", "-m", "fixture plan")
    reconcile(controller, facts(requests=[action()]))
    scripts = REPO / "catalog/skills/workflow/implement-phase/scripts"
    def report() -> str:
        snapshot = subprocess.run([sys.executable, "-B", str(scripts / "status_snapshot.py"),
            "--repo", str(controller.repo), "--scope", "v0.2.0", "--continuation", str(run_plan.continuation_path(controller.record))],
            text=True, capture_output=True, timeout=30)
        assert snapshot.returncode == 0, snapshot.stderr
        result = subprocess.run([sys.executable, "-B", str(scripts / "status_report.py"), "--event", "request"],
            input=snapshot.stdout, text=True, capture_output=True, timeout=30)
        assert result.returncode == 0, result.stderr
        return result.stdout
    waiting = report()
    assert waiting.startswith("Waiting for you")
    assert "Install the qualified local update" in waiting
    assert "installation receipt path" in waiting
    reply, receipt = manual_receipt(controller)
    event = capture(controller, reply)
    reconcile(controller, facts(work=[{"id": "verify", "title": "Verify the reported installation", "authorized": True,
        "feasible": True, "evidence": "Existing scope; owner supplied the result"}], resolutions=[{
        "request_id": "install", "verified": True, "evidence": "Fresh owner result received",
        "reply_text": reply, "prompt_sha256": event["prompt"], "capture_event_id": event["event_id"], "result_receipt": receipt}]))
    # The inert CLI performs the observed task effect before its stub checker completes.
    stub = controller.tmp / "stub_cli.py"
    source = stub.read_text(encoding="utf-8")
    source = source.replace('sys.exit(int(os.environ.get("STUB_CLI_RC", "0")))',
        'from pathlib import Path\np = Path(' + repr(str(controller.repo / PLAN_REL)) + ')\np.write_text(p.read_text().replace("[ ] T001", "[x] T001"))\nsys.exit(0)')
    stub.write_text(source, encoding="utf-8")
    controller.state["complete_at"] = 1
    resumed = controller.run(PLAN_REL, "--platform", "codex")
    assert resumed.returncode == 0, resumed.stdout + resumed.stderr
    assert len(controller.calls("cli")) == 1
    completed = report()
    assert "100%" in completed
    assert "Verified complete" in completed


def test_unrelated_genuine_reply_cannot_be_labeled_a_manual_result(controller: Env) -> None:
    reconcile(controller, facts(requests=[action()]))
    _reply, receipt = manual_receipt(controller)
    event = capture(controller, "What time is it?")
    frame = reconcile(controller, facts(resolutions=[{"request_id": "install", "verified": True,
        "reply_text": "What time is it?", "prompt_sha256": event["prompt"], "capture_event_id": event["event_id"],
        "result_receipt": receipt, "evidence": "An unrelated genuine question is not an acknowledgment"}]))
    assert frame["disposition"]["state"] == "waiting_owner_action"


def test_failed_probe_cannot_clear_an_external_condition(controller: Env) -> None:
    condition = {"id": "vendor", "title": "vendor restoration", "evidence": "Verified health check failed",
        "resume_when": "The health check succeeds", "observed_at": datetime.now(timezone.utc).isoformat()}
    reconcile(controller, facts(external_conditions=[condition]))
    path = controller.tmp / "failed-probe.json"
    path.write_text(json.dumps({"condition_id": "vendor", "status": "failed", "exit_code": 1,
        "resume_when": condition["resume_when"], "run_nonce": "n0nce", "finished_at": datetime.now(timezone.utc).isoformat()}), encoding="utf-8")
    frame = reconcile(controller, facts(condition_resolutions=[{"condition_id": "vendor", "verified": True,
        "evidence": "Failed probe must not close the outage", "verification_receipt": {
            "path": str(path), "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}}]))
    assert frame["disposition"]["state"] == "blocked_external"


def test_same_path_and_session_with_replaced_native_nonce_rejects_old_state(controller: Env) -> None:
    reconcile(controller, facts(requests=[action()]))
    record = json.loads(controller.record.read_text(encoding="utf-8"))
    record["nonce"] = "replacement-run"
    controller.record.write_text(json.dumps(record), encoding="utf-8")
    result = controller.run(PLAN_REL, "--platform", "codex")
    assert result.returncode == 2
    assert "different run or session" in result.stderr
    assert controller.calls("cli") == []


def test_old_nonce_result_cannot_clear_current_external_condition(controller: Env) -> None:
    condition = {"id": "vendor", "title": "vendor restoration", "evidence": "Verified health check failed",
        "resume_when": "The health check succeeds", "observed_at": datetime.now(timezone.utc).isoformat()}
    reconcile(controller, facts(external_conditions=[condition]))
    path = controller.tmp / "old-run-success.json"
    path.write_text(json.dumps({"condition_id": "vendor", "status": "succeeded", "exit_code": 0,
        "resume_when": condition["resume_when"], "run_nonce": "earlier-run",
        "finished_at": datetime.now(timezone.utc).isoformat()}), encoding="utf-8")
    frame = reconcile(controller, facts(condition_resolutions=[{"condition_id": "vendor", "verified": True,
        "evidence": "Prior-run success must not clear this outage", "verification_receipt": {
            "path": str(path), "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}}]))
    assert frame["disposition"]["state"] == "blocked_external"


def test_external_condition_cannot_substitute_its_resumption_predicate(controller: Env) -> None:
    condition = {"id": "vendor", "title": "vendor restoration", "evidence": "Verified health check failed",
        "resume_when": "The health check succeeds", "observed_at": datetime.now(timezone.utc).isoformat()}
    reconcile(controller, facts(external_conditions=[condition]))
    path = controller.tmp / "observations.json"
    path.write_text(json.dumps(facts(external_conditions=[dict(condition, resume_when="A failed probe is enough")])), encoding="utf-8")
    result = controller.run("reconcile", PLAN_REL, "--observations", str(path))
    assert result.returncode == 2
    assert "cannot change its identity or resumption predicate" in result.stderr


def test_current_successful_probe_clears_only_its_bound_external_condition(controller: Env) -> None:
    condition = {"id": "vendor", "title": "vendor restoration", "evidence": "Verified health check failed",
        "resume_when": "The health check succeeds", "observed_at": datetime.now(timezone.utc).isoformat()}
    reconcile(controller, facts(external_conditions=[condition]))
    path = controller.tmp / "current-success.json"
    path.write_text(json.dumps({"condition_id": "vendor", "status": "succeeded", "exit_code": 0,
        "resume_when": condition["resume_when"], "run_nonce": "n0nce",
        "finished_at": datetime.now(timezone.utc).isoformat()}), encoding="utf-8")
    frame = reconcile(controller, facts(work=[{"id": "continue", "title": "Continue restored dependency work", "authorized": True,
        "feasible": True, "evidence": "Current successful health probe"}], condition_resolutions=[{
        "condition_id": "vendor", "verified": True, "evidence": "Fresh bound success", "verification_receipt": {
            "path": str(path), "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}}]))
    assert frame["disposition"]["state"] == "working"
    assert frame["disposition"]["external_conditions"] == []
    assert frame["observation"]["condition_resolutions"] == []
    from tests.test_status_snapshot import Repo, load
    git = Repo(controller.repo)
    git.git("add", PLAN_REL)
    git.git("commit", "-q", "-m", "private condition fixture")
    sidecar = run_plan.continuation_path(controller.record)
    before = sidecar.read_bytes(), controller.record.read_bytes()
    scripts = REPO / "catalog/skills/workflow/implement-phase/scripts"
    report = load("status_report")
    for _ in range(2):
        produced = subprocess.run([sys.executable, "-B", str(scripts / "status_snapshot.py"),
            "--repo", str(controller.repo), "--scope", "v0.2.0", "--continuation", str(sidecar)],
            text=True, capture_output=True, timeout=30)
        assert produced.returncode == 0, produced.stderr
        snapshot = json.loads(produced.stdout)
        assert report.continuation(snapshot)["external_conditions"] == []
        for mode in ("compact", "full"):
            assert condition["title"] not in report.render(snapshot, mode)
    assert before == (sidecar.read_bytes(), controller.record.read_bytes())
    assert controller.calls("cli") == []
