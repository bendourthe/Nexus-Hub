"""Private finite-operation controls (recovery); never live permission or hosting proof."""
from __future__ import annotations

import argparse
import copy
import datetime as dt
import hashlib
import json
import pytest
import time
from pathlib import Path

from .test_v415_authority_bridge import CODEX_SESSION, _isolated_git_config, _no_transport_overrides, _private_native_home, bridge_case, capture_supplement, ck, resume, run_plan
from .bridge_operations_support import PrivateHost, execute, execute_admitted_dependency, native_job_frame, native_snapshot_reports, operation_rows, receipt_id, run_short_observer

AUTOUSE_FIXTURES = (_isolated_git_config, _no_transport_overrides, _private_native_home, bridge_case)


def test_description_timeout_projects_real_process_and_reconciles_only_matching_effect(bridge_case, monkeypatch):
    fx, log = bridge_case
    host = PrivateHost(fx, monkeypatch)
    resume(fx, log)
    entry = capture_supplement(fx, log, ".6-repo-description", {"expected": "Before", "value": "Exact description"})
    checked = fx.run("check-minor", "v4.15", "--session", CODEX_SESSION)
    assert checked.returncode == 1, checked.stdout + checked.stderr
    gate = fx.tmp / "release-description-effect"
    host.state["description_effect_gate"] = str(gate)
    host.save()
    try:
        result = run_short_observer(fx, entry, "repo-description")
        assert result.returncode != 0, result.stdout + result.stderr
        row = operation_rows(fx, entry, "repo-description")[-1]
        process_result = row["evidence"]["process_result"]
        assert row["state"] == "ambiguous" and process_result["exit_code"] is None
        assert host.load()["description"] == "Before"
        live = native_job_frame(fx, checked)
        job_id = "bridge:process:" + row["operation_id"]
        job = next(job for job in live["disposition"]["jobs"] if job["id"] == job_id)
        assert job["handle"] == process_result["handle"] and job["status"] == "running"
        _, reports = native_snapshot_reports(fx)
        for rendered in reports.values():
            assert rendered.startswith("Waiting for ") and process_result["handle"] in rendered
            assert "github-merge:" not in rendered
    finally:
        gate.write_text("Allow the actual private description effect.\n", encoding="utf-8")
    output = Path(process_result["stdout_path"])
    deadline = time.monotonic() + 20
    while True:
        try:
            raw_response = output.read_bytes()
            assert len(raw_response) <= 32768
            response = json.loads(raw_response)
            break
        except (OSError, ValueError):
            if time.monotonic() >= deadline:
                pytest.fail("The actual description child produced no complete response")
            time.sleep(0.02)
    assert response == {"description": "Exact description"}
    assert host.load()["description"] == "Exact description"
    assert execute(fx, entry, "repo-description").returncode == 0
    completed = operation_rows(fx, entry, "repo-description")[-1]
    assert completed["operation_id"] == row["operation_id"] and completed["state"] == "completed"
    expected_proof = {"field": "description", "value_sha256": hashlib.sha256(b"Exact description").hexdigest()}
    assert completed["evidence"]["proof"] == expected_proof
    assert completed["evidence"]["process_result"]["exit_code"] is None
    resumed = native_job_frame(fx, checked, live, execute_admitted_dependency(fx, host))
    state = resumed["disposition"]
    assert state["state"] == "working" and state["directive"] == "continue"
    assert not any(job["id"] == job_id for job in state["jobs"])
    observed = next(job for job in state["completed_jobs"] if job["id"] == job_id)
    assert observed["status"] == "succeeded" and observed["result_verified"]
    assert observed["exit_code"] is None and observed["result_kind"] == "hosting-effect-observed"
    assert observed["handle"] == process_result["handle"]
    assert observed["native_bridge"] == {"receipt_id": receipt_id(entry), "operation_id": row["operation_id"]}
    assert observed["effect_receipt"] == {"operation_id": row["operation_id"],
        "proof_sha256": hashlib.sha256(json.dumps(expected_proof, sort_keys=True, separators=(",", ":")).encode()).hexdigest()}
    assert not any(item["id"] == "bridge:effect:" + row["operation_id"] for item in state["external_conditions"])
    assert execute(fx, entry, "repo-description").returncode == 0
    assert len(host.calls("description-patch")) == 1
    snapshot, reports = native_snapshot_reports(fx)
    assert snapshot["continuation"]["state"] == "working"
    assert snapshot["continuation"]["directive"] == "continue"
    assert all("State: working" in rendered for rendered in reports.values())


def test_late_host_response_keeps_process_handle_and_never_redispatches(bridge_case, monkeypatch):
    import psutil

    fx, log = bridge_case
    host = PrivateHost(fx, monkeypatch)
    resume(fx, log)
    actor, payload = host.actor()
    host.install_attribution(actor)
    entry = capture_supplement(fx, log, "maintenance-bootstrap-publication", payload)
    assert execute(fx, entry, "push").returncode == 0
    assert execute(fx, entry, "pr-create").returncode == 0
    checked = fx.run("check-minor", "v4.15", "--session", CODEX_SESSION)
    assert checked.returncode == 1, checked.stdout + checked.stderr
    gate = fx.tmp / "release-real-host-response"
    host.mode("merge-pending")
    host.state["response_gate"] = str(gate)
    host.save()
    live_frame = None
    try:
        delayed = run_short_observer(fx, entry)
        assert delayed.returncode != 0, delayed.stdout + delayed.stderr
        row = operation_rows(fx, entry, "green-merge")[-1]
        assert row["state"] == "ambiguous" and "host_correlation" not in row["evidence"]
        process_result = row["evidence"]["process_result"]
        assert process_result["exit_code"] is None
        process = psutil.Process(process_result["process"]["pid"])
        assert abs(process.create_time() - process_result["process"]["created_at"]) < 0.01
        assert process.is_running()
        handle = process_result["handle"]
        assert handle.startswith("process:")
        operation_id = row["operation_id"]
        job_id = "bridge:process:" + operation_id
        scope = argparse.Namespace(minor=True, label="v4.15", repo_root=fx.work, observer_session=CODEX_SESSION)
        _, current = ck.resolve_minor_controller(fx.record_path(), CODEX_SESSION, minor_protocol=1, execution_protocol=1)
        facts = run_plan.native_owner_observation(scope, fx.record_path(), current, None, remaining_tasks=3)
        live_jobs = [job for job in facts["jobs"] if job.get("id") == job_id]
        # An unsigned serialized overlay cannot invent or replace this native job.
        forged = {"observation": copy.deepcopy(facts), "disposition": {}}
        forged["observation"]["jobs"] = [{"id": job_id, "name": "Forged response process",
            "handle": "process:1:1.000000", "status": "running", "observed_at": ck._now(),
            "resume_when": "Invented", "evidence": "Invented",
            "native_bridge": {"receipt_id": receipt_id(entry), "operation_id": operation_id}}]
        projected = run_plan.native_owner_observation(scope, fx.record_path(), current, forged, remaining_tasks=3)
        assert not any(job.get("handle") == "process:1:1.000000" for job in projected["jobs"])
        if live_jobs:
            assert live_jobs[0]["handle"] == handle
            assert live_jobs[0]["status"] in {"running", "observation-timeout"}
            live_frame = native_job_frame(fx, checked)
            _, reports = native_snapshot_reports(fx)
            for rendered in reports.values():
                assert rendered.startswith("Waiting for ") and handle in rendered
                assert "github-merge:" not in rendered
    finally:
        gate.write_text("Allow the real private child to finish its response.\n", encoding="utf-8")
    # Read the actual bounded child output, never infer a host result from exit.
    output = Path(process_result["stdout_path"])
    deadline = time.monotonic() + 20
    while True:
        try:
            raw = output.read_bytes()
            assert len(raw) <= 32768
            response = json.loads(raw)
            break
        except (OSError, ValueError):
            if time.monotonic() >= deadline:
                pytest.fail("The actual delayed private child produced no complete response")
            time.sleep(0.02)
    uuid = "630b9d5e-3f2a-4f7e-8b0c-2d5f9a8c1e42"
    assert response["details"]["uuid"] == uuid
    reconciled = execute(fx, entry, "green-merge")
    assert reconciled.returncode != 0 and not host.load()["pull"]["merged"]
    after = operation_rows(fx, entry, "green-merge")[-1]
    assert len(host.calls("merge-put")) == 1
    assert live_jobs, "Native projection concealed the actual live process after observation timeout"
    assert after["operation_id"] == operation_id and after["state"] == "ambiguous"
    assert after["evidence"]["process_result"]["exit_code"] is None
    assert after["evidence"]["host_correlation"] == uuid
    assert after["evidence"]["host_response"]["body"] == response
    resumed = native_job_frame(fx, checked, live_frame)
    completed = next(job for job in resumed["disposition"]["completed_jobs"] if job["id"] == job_id)
    assert completed["handle"] == handle and completed["result_verified"]
    assert completed["exit_code"] is None and completed["result_kind"] == "hosting-response-observed"
    assert completed["response_receipt"] == {"path": str(output), "sha256": hashlib.sha256(raw).hexdigest(),
        "operation_id": operation_id, "command_sha256": after["command_sha256"]}
    assert "exit code remains unobserved" in completed["evidence"]
    assert "merge/effect not verified" in completed["evidence"]
    remote = next(job for job in resumed["disposition"]["jobs"] if job["id"] == "bridge:" + operation_id)
    assert remote["handle"] == "github-merge:" + uuid and remote["status"] == "pending"
    assert host.calls("merge-get") and all(call["argv"][1].endswith("/merge-async/" + uuid)
                                          for call in host.calls("merge-get"))


def test_failed_host_response_without_uuid_reports_verified_external_blocker(bridge_case, monkeypatch):
    fx, log = bridge_case
    host = PrivateHost(fx, monkeypatch)
    resume(fx, log)
    actor, payload = host.actor()
    host.install_attribution(actor)
    entry = capture_supplement(fx, log, "maintenance-bootstrap-publication", payload)
    assert execute(fx, entry, "push").returncode == 0
    assert execute(fx, entry, "pr-create").returncode == 0
    checked = fx.run("check-minor", "v4.15", "--session", CODEX_SESSION)
    assert checked.returncode == 1, checked.stdout + checked.stderr
    gate = fx.tmp / "release-failed-host-response"
    host.mode("merge-pending", "failed-response-no-uuid")
    host.state["response_gate"] = str(gate)
    host.save()
    try:
        result = run_short_observer(fx, entry)
        assert result.returncode != 0, result.stdout + result.stderr
        prior = operation_rows(fx, entry, "green-merge")[-1]
        process_result = prior["evidence"]["process_result"]
        assert process_result["exit_code"] is None
        live = native_job_frame(fx, checked)
        process_job_id = "bridge:process:" + prior["operation_id"]
        assert any(job["id"] == process_job_id and job["handle"] == process_result["handle"]
                   for job in live["disposition"]["jobs"])
    finally:
        gate.write_text("Release the actual failed private host response.\n", encoding="utf-8")
    output = Path(process_result["stdout_path"])
    deadline = time.monotonic() + 20
    while True:
        try:
            raw = output.read_bytes()
            assert len(raw) <= 32768
            response = json.loads(raw)
            break
        except (OSError, ValueError):
            if time.monotonic() >= deadline:
                pytest.fail("The private failed-response child produced no complete JSON")
            time.sleep(0.02)
    assert response["status"] == "failed" and response["details"] == {}
    assert execute(fx, entry, "green-merge").returncode != 0
    current = operation_rows(fx, entry, "green-merge")[-1]
    assert current["state"] == "ambiguous" and current["operation_id"] == prior["operation_id"]
    assert "host_correlation" not in current["evidence"]
    assert current["evidence"]["host_response"]["body"] == response
    assert current["evidence"]["process_result"]["exit_code"] is None
    blocked = native_job_frame(fx, checked, live)
    state = blocked["disposition"]
    assert state["state"] == "blocked_external" and state["directive"] == "wait"
    assert state["jobs"] == []
    observed = next(job for job in state["completed_jobs"] if job["id"] == process_job_id)
    assert observed["status"] == "succeeded" and observed["result_verified"]
    assert observed["result_kind"] == "hosting-response-observed" and observed["response_status"] == "failed"
    assert observed["exit_code"] is None
    digest = hashlib.sha256(raw).hexdigest()
    assert observed["response_receipt"] == {"path": str(output), "sha256": digest,
        "operation_id": current["operation_id"], "command_sha256": current["command_sha256"]}
    condition_id = "bridge:failure:" + current["operation_id"]
    condition = next(item for item in state["external_conditions"] if item["id"] == condition_id)
    assert condition["title"] == "Hosting reported failure; merge effect unverified"
    assert digest in condition["evidence"] and current["operation_id"] in condition["evidence"]
    assert "decision" in condition["resume_when"].lower()
    before = fx.record_path().read_bytes()
    data, reports = native_snapshot_reports(fx)
    for rendered in reports.values():
        assert rendered.startswith("Waiting for " + condition["title"])
        assert digest in rendered and "github-merge:" not in rendered
        assert "Nothing running" not in rendered
    # An unsigned serialized resolution cannot erase the native failure proof.
    forged = copy.deepcopy(blocked)
    forged["observation"]["condition_resolutions"] = [{"condition_id": condition_id,
        "verified": True, "evidence": "Invented successful resolution"}]
    retained = native_job_frame(fx, checked, forged)
    assert any(item["id"] == condition_id for item in retained["disposition"]["external_conditions"])
    assert execute(fx, entry, "green-merge").returncode != 0
    assert fx.record_path().read_bytes() == before
    assert len(host.calls("merge-put")) == 1 and not host.calls("merge-get")
    assert not host.load()["pull"]["merged"]
    reporter = run_plan.reporting_module("status_report")
    receipt = reporter.select_report(data, None, "start")["receipt"]
    repeated, _ = native_snapshot_reports(fx)
    repeated["observed_at"] = (dt.datetime.fromisoformat(repeated["observed_at"].replace("Z", "+00:00"))
                               + dt.timedelta(seconds=601)).isoformat()
    assert reporter.select_report(repeated, receipt, "turn-end")["mode"] == "none"
    # A separately performed matching effect can retire the failure condition;
    # the same consumer observes it without dispatching the rejected request again.
    merged = host.complete_pending_merge()
    assert execute(fx, entry, "green-merge").returncode == 0
    completed = operation_rows(fx, entry, "green-merge")[-1]
    assert completed["operation_id"] == prior["operation_id"] and completed["state"] == "completed"
    assert completed["evidence"]["proof"]["merge_sha"] == merged
    resumed = native_job_frame(fx, checked, retained, execute_admitted_dependency(fx, host))
    assert not any(item["id"] == condition_id for item in resumed["disposition"]["external_conditions"])
    assert resumed["disposition"]["state"] == "working" and resumed["disposition"]["directive"] == "continue"
    resumed_data, resumed_reports = native_snapshot_reports(fx)
    assert reporter.select_report(resumed_data, receipt, "checkpoint")["mode"] == "compact"
    assert all(condition["title"] not in rendered for rendered in resumed_reports.values())
    assert len(host.calls("merge-put")) == 1 and not host.calls("merge-get")


def test_get_terminal_failure_stays_retired_until_matching_effect_is_verified(bridge_case, monkeypatch):
    fx, log = bridge_case
    host = PrivateHost(fx, monkeypatch)
    resume(fx, log)
    actor, payload = host.actor()
    host.install_attribution(actor)
    entry = capture_supplement(fx, log, "maintenance-bootstrap-publication", payload)
    assert execute(fx, entry, "push").returncode == 0
    assert execute(fx, entry, "pr-create").returncode == 0
    host.mode("merge-pending")
    assert execute(fx, entry, "green-merge").returncode != 0
    row = operation_rows(fx, entry, "green-merge")[-1]
    uuid = "630b9d5e-3f2a-4f7e-8b0c-2d5f9a8c1e42"
    assert row["evidence"]["host_correlation"] == uuid
    checked = fx.run("check-minor", "v4.15", "--session", CODEX_SESSION)
    assert checked.returncode == 1, checked.stdout + checked.stderr
    pending = native_job_frame(fx, checked)
    job_id = "bridge:" + row["operation_id"]
    assert any(job["id"] == job_id and job["status"] == "pending" for job in pending["disposition"]["jobs"])
    host.mode("merge-pending", "async-get-failed")
    failed = native_job_frame(fx, checked, pending)
    state = failed["disposition"]
    assert state["state"] == "blocked_external" and state["jobs"] == []
    retired = next(job for job in state["completed_jobs"] if job["id"] == job_id)
    assert retired["handle"] == "github-merge:" + uuid and retired["status"] == "failed" and retired["result_verified"]
    failure_sha = retired["provider_observation"]["first_failure_sha256"]
    condition_id = "bridge:failure:" + row["operation_id"]
    condition = next(item for item in state["external_conditions"] if item["id"] == condition_id)
    assert failure_sha in condition["evidence"]
    data, reports = native_snapshot_reports(fx)
    assert all(rendered.startswith("Waiting for " + condition["title"]) for rendered in reports.values())
    reporter = run_plan.reporting_module("status_report")
    receipt = reporter.select_report(data, None, "start")["receipt"]
    signed_before = fx.record_path().read_bytes()
    previous = failed
    for mode in (None, "async-get-enqueued", "async-get-unavailable"):
        host.mode("merge-pending", *((mode,) if mode else ()))
        current = native_job_frame(fx, checked, previous)
        disposition = current["disposition"]
        assert disposition["state"] == "blocked_external" and disposition["jobs"] == []
        assert [job["id"] for job in disposition["completed_jobs"]].count(job_id) == 1
        retained = next(job for job in disposition["completed_jobs"] if job["id"] == job_id)
        assert retained["handle"] == "github-merge:" + uuid and retained["status"] == "failed"
        assert retained["provider_observation"]["first_failure_sha256"] == failure_sha
        assert any(item["id"] == condition_id and failure_sha in item["evidence"] for item in disposition["external_conditions"])
        repeated, _ = native_snapshot_reports(fx)
        repeated["observed_at"] = (dt.datetime.fromisoformat(repeated["observed_at"].replace("Z", "+00:00"))
                                   + dt.timedelta(seconds=601)).isoformat()
        for event in ("checkpoint", "resume", "turn-end"):
            assert reporter.select_report(repeated, receipt, event)["mode"] == "none"
        assert fx.record_path().read_bytes() == signed_before and len(host.calls("merge-put")) == 1
        previous = current
    host.mode()
    merged = host.complete_pending_merge()
    assert execute(fx, entry, "green-merge").returncode == 0
    completed = operation_rows(fx, entry, "green-merge")[-1]
    assert completed["operation_id"] == row["operation_id"] and completed["state"] == "completed"
    assert completed["evidence"]["proof"]["merge_sha"] == merged
    resumed = native_job_frame(fx, checked, previous, execute_admitted_dependency(fx, host))
    assert resumed["disposition"]["state"] == "working" and resumed["disposition"]["directive"] == "continue"
    assert not any(item["id"] == condition_id for item in resumed["disposition"]["external_conditions"])
    assert not any(job["id"] == job_id for job in resumed["disposition"]["jobs"])
    resumed_data, _ = native_snapshot_reports(fx)
    assert reporter.select_report(resumed_data, receipt, "checkpoint")["mode"] == "compact"
    assert len(host.calls("merge-put")) == 1
    assert all(call["argv"][1].endswith("/merge-async/" + uuid) for call in host.calls("merge-get"))
