"""Private finite-operation controls (release notes and description); never live permission or hosting proof."""
from __future__ import annotations

import copy
import hashlib
import pytest
import subprocess
import time
from pathlib import Path

from .test_codex_transcript_approval import Transcript
from .test_v415_authority_bridge import CODEX_SESSION, _isolated_git_config, _no_transport_overrides, _private_native_home, bridge_case, capture_supplement, ck, cm, resume
from .bridge_operations_support import FLAGS, NEW_OWNER, PrivateHost, assert_original_approvals_and_exact_capture_append, command, execute, native_job_frame, native_snapshot_reports, operation_rows, receipt_id, run_cut

AUTOUSE_FIXTURES = (_isolated_git_config, _no_transport_overrides, _private_native_home, bridge_case)


def test_initial_notes_are_prepared_without_a_release_or_tag(bridge_case, monkeypatch):
    fx, log = bridge_case
    host = PrivateHost(fx, monkeypatch)
    resume(fx, log)
    body = "Private exact initial release notes.\n"
    entry = capture_supplement(fx, log, ".6-release-notes", {"notes": body})
    before_tags = host.git(fx.work, "tag", "--list")
    assert host.load()["release"] is None
    result = execute(fx, entry, "prepare-release-notes")
    assert result.returncode == 0, result.stdout + result.stderr
    artifact = fx.record_path().parent / "release-notes" / (
        fx.record_path().stem + "-" + receipt_id(entry) + "-v4.15.6.md")
    assert artifact.read_bytes() == body.encode("utf-8")
    assert host.load()["release"] is None
    assert host.git(fx.work, "tag", "--list") == before_tags
    assert not host.calls("release-edit")
    row = operation_rows(fx, entry, "prepare-release-notes")[-1]
    assert row["state"] == "completed"
    assert row["evidence"]["proof"] == {
        "path": str(artifact), "notes_sha256": hashlib.sha256(body.encode()).hexdigest(),
        "effect": "prepared", "release_published": False}
    assert execute(fx, entry, "prepare-release-notes").returncode == 0
    context, current = ck.resolve_minor_controller(
        fx.record_path(), CODEX_SESSION, minor_protocol=1, execution_protocol=1)
    assert ck.project(current, "v4.15.6")["v415_authority"][0]["execution"] == "prepared; release not observed"
    # Published-body verification must never manufacture or edit a release.
    assert execute(fx, entry, "release-notes").returncode != 0
    host.state["release"] = {"tagName": "v4.15.6", "isDraft": False, "body": body}
    host.save()
    assert execute(fx, entry, "release-notes").returncode == 0
    host.state["release"]["body"] = "Subsequent owner edit."
    host.save()
    assert execute(fx, entry, "release-notes").returncode != 0
    assert host.load()["release"]["body"] == "Subsequent owner edit."
    assert not host.calls("release-edit")
    artifact.write_text("Later private owner edit.\n", encoding="utf-8")
    assert execute(fx, entry, "prepare-release-notes").returncode != 0
    assert artifact.read_text() == "Later private owner edit.\n"


def test_description_concurrency_and_old_receipt_survive_new_capture_and_owner(bridge_case, monkeypatch):
    fx, log = bridge_case
    host = PrivateHost(fx, monkeypatch)
    original = copy.deepcopy(fx.record())
    resume(fx, log)
    notes = capture_supplement(fx, log, ".6-release-notes", {"notes": "Private initial notes.\n"})
    entry = capture_supplement(fx, log, ".6-repo-description", {"expected": "Before", "value": "Exact description"})
    host.state["effect_delay"] = 0.15
    host.save()
    argv = command(fx, entry, "repo-description")
    before = fx.record_path().read_bytes()
    for extra in (["--operation-id", "f" * 64], ["--retry"]):
        invalid = subprocess.run(argv + extra, cwd=fx.work, env=fx.env, capture_output=True,
                                 text=True, timeout=90, creationflags=FLAGS)
        assert invalid.returncode != 0 and fx.record_path().read_bytes() == before
        assert not host.calls("description-patch")
    processes = [subprocess.Popen(argv, cwd=fx.work, env=fx.env, stdout=subprocess.PIPE,
                                  stderr=subprocess.PIPE, text=True, creationflags=FLAGS) for _ in range(2)]
    try:
        outputs = [process.communicate(timeout=90) for process in processes]
    finally:
        for process in processes:
            if process.poll() is None:
                process.kill()
                process.wait(timeout=15)
    assert any(process.returncode == 0 for process in processes), outputs
    assert execute(fx, entry, "repo-description").returncode == 0
    assert len(host.calls("description-patch")) == 1
    rows = operation_rows(fx, entry, "repo-description")
    assert [row["state"] for row in rows] == ["ambiguous", "completed"]
    assert rows[0]["evidence"]["reason"] == "reserved-before-dispatch"
    old_identity = rows[-1]["operation_id"]
    second_log = Transcript(Path(fx.env["USERPROFILE"]), fx.work, time.time() - 10, session=NEW_OWNER)
    resume(fx, second_log, session=NEW_OWNER)
    assert execute(fx, entry, "repo-description", session=NEW_OWNER).returncode == 0
    assert execute(fx, entry, "repo-description").returncode != 0
    assert operation_rows(fx, entry, "repo-description")[-1]["operation_id"] == old_identity
    assert_original_approvals_and_exact_capture_append(original, fx.record(), [
        (cm.AUTHORITY_BRIDGE_ACTION, CODEX_SESSION), (cm.AUTHORITY_BRIDGE_ACTION, CODEX_SESSION)],
        [(original["session_id"], CODEX_SESSION, log.path), (CODEX_SESSION, NEW_OWNER, second_log.path)], fx.runs)
    assert fx.record()["v415_authority_receipts"][0] == notes
    assert len(host.calls("description-patch")) == 1


@pytest.mark.parametrize("phase", ["before", "after"])
def test_crash_recovery_never_redispatches_description(bridge_case, monkeypatch, phase):
    fx, log = bridge_case
    host = PrivateHost(fx, monkeypatch)
    resume(fx, log)
    entry = capture_supplement(fx, log, ".6-repo-description", {"expected": "Before", "value": "Exact description"})
    stopped = run_cut(fx, entry, "repo-description", phase)
    assert stopped.returncode == (81 if phase == "before" else 82), stopped.stdout + stopped.stderr
    rows = operation_rows(fx, entry, "repo-description")
    assert len(rows) == 1 and rows[0]["state"] == "ambiguous"
    assert len(host.calls("description-patch")) == int(phase == "after")
    for _ in range(2):
        recovered = execute(fx, entry, "repo-description")
        assert (recovered.returncode == 0) == (phase == "after")
    assert len(host.calls("description-patch")) == int(phase == "after")
    assert operation_rows(fx, entry, "repo-description")[-1]["state"] == (
        "completed" if phase == "after" else "ambiguous")
    if phase == "before":
        checked = fx.run("check-minor", "v4.15", "--session", CODEX_SESSION)
        assert checked.returncode == 1, checked.stdout + checked.stderr
        blocked = native_job_frame(fx, checked)
        state = blocked["disposition"]
        assert state["state"] == "blocked_external" and state["jobs"] == []
        condition_id = "bridge:effect:" + rows[0]["operation_id"]
        condition = next(item for item in state["external_conditions"] if item["id"] == condition_id)
        assert condition["evidence"] and "reconcile" in condition["resume_when"].lower()
        _, reports = native_snapshot_reports(fx)
        for rendered in reports.values():
            assert rendered.startswith("Waiting for " + condition["title"])
            assert "process:" not in rendered and "github-merge:" not in rendered


def test_description_precondition_and_unknown_effect_keep_finite_identity(bridge_case, monkeypatch):
    fx, log = bridge_case
    host = PrivateHost(fx, monkeypatch)
    resume(fx, log)
    entry = capture_supplement(fx, log, ".6-repo-description", {"expected": "Before", "value": "Exact description"})
    before = fx.record_path().read_bytes()
    host.state["description"] = "External change"
    host.save()
    denied = execute(fx, entry, "repo-description")
    assert denied.returncode != 0
    assert fx.record_path().read_bytes() == before and not host.calls("description-patch")
    host.state["description"] = "Before"
    host.state["modes"] = ["reads-unavailable"]
    host.save()
    uncertain = execute(fx, entry, "repo-description")
    assert uncertain.returncode != 0
    identity = operation_rows(fx, entry, "repo-description")[-1]["operation_id"]
    assert host.load()["description"] == "Exact description"
    assert len(host.calls("description-patch")) == 1
    host.mode()
    assert execute(fx, entry, "repo-description").returncode == 0
    assert operation_rows(fx, entry, "repo-description")[-1]["operation_id"] == identity
    assert len(host.calls("description-patch")) == 1


def test_captured_t027_budget_never_dispatches_or_changes_global_caps(bridge_case, monkeypatch):
    fx, log = bridge_case
    host = PrivateHost(fx, monkeypatch)
    original = copy.deepcopy(fx.record())
    resume(fx, log)
    entry = capture_supplement(fx, log, ".9-t027-budget", {"usd_total": 10, "spawn_total": 6})
    before = fx.record_path().read_bytes()
    result = execute(fx, entry, "t027-budget")
    assert result.returncode != 0 and "inactive" in result.stdout
    assert fx.record_path().read_bytes() == before
    assert_original_approvals_and_exact_capture_append(original, fx.record(), [
        (cm.AUTHORITY_BRIDGE_ACTION, CODEX_SESSION)], [(original["session_id"], CODEX_SESSION, log.path)], fx.runs)
    assert not fx.record()["v415_publication_operations"]
    assert not host.journal.exists()
