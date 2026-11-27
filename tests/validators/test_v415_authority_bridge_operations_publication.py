"""Private finite-operation controls (publication); never live permission or hosting proof."""
from __future__ import annotations

import copy
import datetime as dt
import json
import os
import subprocess

from .test_v415_authority_bridge import CODEX_SESSION, ROOT, _isolated_git_config, _no_transport_overrides, _private_native_home, bridge_case, capture_supplement, ck, cm, resume, run_plan
from .bridge_operations_support import FLAGS, PrivateHost, command, execute, execute_admitted_dependency, native_job_frame, native_snapshot_reports, operation_rows, receipt_id

AUTOUSE_FIXTURES = (_isolated_git_config, _no_transport_overrides, _private_native_home, bridge_case)


def test_publication_distinct_actor_real_guard_and_exact_checked_merge(bridge_case, monkeypatch):
    fx, log = bridge_case
    host = PrivateHost(fx, monkeypatch)
    resume(fx, log)
    actor, payload = host.actor()
    entry = capture_supplement(fx, log, "maintenance-bootstrap-publication", payload)
    before = fx.record_path().read_bytes()
    missing = execute(fx, entry, "push")
    assert missing.returncode != 0 and "attribution" in missing.stderr.lower()
    assert fx.record_path().read_bytes() == before and not host.calls("git-push")
    diagnostic = fx.record_path().parent / "publication-jobs" / (receipt_id(entry) + ".attribution.json")
    condition = json.loads(diagnostic.read_bytes())["condition"]
    assert condition == "guard-inactive"
    assert ck.project(fx.record(), "v4.15.6")["v415_authority"][-1]["enforcement"] == "blocked:attribution:" + condition
    guard_root = host.install_attribution(actor)
    assert guard_root.is_relative_to(fx.work / ".git")
    # A changed guard is also a preflight failure, before any allowance is spent.
    hook = guard_root / "pre-push"
    original_hook = hook.read_bytes()
    hook.write_bytes(original_hook + b"\n# private altered guard\n")
    denied = execute(fx, entry, "push")
    assert denied.returncode != 0 and "attribution" in denied.stderr.lower()
    assert fx.record_path().read_bytes() == before and not host.calls("git-push")
    condition = json.loads(diagnostic.read_bytes())["condition"]
    assert condition in {"guard-missing-or-modified", "hook-missing-or-modified"}
    assert ck.project(fx.record(), "v4.15.6")["v415_authority"][-1]["enforcement"] == "blocked:attribution:" + condition
    hook.write_bytes(original_hook)
    assert execute(fx, entry, "push").returncode == 0
    assert len(host.calls("git-push")) == 1
    assert host.git(fx.remote, "rev-parse", "refs/heads/" + cm.AUTHORITY_BRIDGE_BRANCH) == payload["head"]
    # Historical push completion cannot stand in for the current remote ref.
    host.git(fx.remote, "update-ref", "refs/heads/" + cm.AUTHORITY_BRIDGE_BRANCH,
             host.state["base"], payload["head"])
    before_pr = fx.record_path().read_bytes()
    assert execute(fx, entry, "pr-create").returncode != 0
    assert fx.record_path().read_bytes() == before_pr and not host.calls("pr-create")
    host.git(fx.remote, "update-ref", "refs/heads/" + cm.AUTHORITY_BRIDGE_BRANCH,
             payload["head"], host.state["base"])
    assert execute(fx, entry, "pr-create").returncode == 0
    assert len(host.calls("pr-create")) == 1
    for mode in ("wrong-pr-head", "wrong-pr-base", "wrong-preview-tree", "wrong-preview-parents",
                 "wrong-check-sha", "stale-check", "strict-false", "bypass", "rules-unavailable",
                 "ruleset-bypass", ("unbound-ruleset", "wrong-app"), "conflicting-app"):
        host.mode(*((mode,) if isinstance(mode, str) else mode))
        before_merge = fx.record_path().read_bytes()
        result = execute(fx, entry, "green-merge")
        assert result.returncode != 0, (mode, result.stdout, result.stderr)
        assert fx.record_path().read_bytes() == before_merge, mode
        assert not host.calls("merge-put"), mode
    # An unbound ruleset must retain the legacy app-123 requirement.
    host.mode("unbound-ruleset")
    assert execute(fx, entry, "green-merge").returncode == 0
    state = host.load()
    assert state["merged_sha"] != state["preview"]
    assert host.git(fx.remote, "rev-parse", "develop") == state["merged_sha"]
    assert len(host.calls("merge-put")) == 1
    assert execute(fx, entry, "green-merge").returncode == 0
    assert len(host.calls("git-push")) == len(host.calls("pr-create")) == len(host.calls("merge-put")) == 1


def test_async_acceptance_retains_identity_until_independent_merge_observed(bridge_case, monkeypatch):
    fx, log = bridge_case
    host = PrivateHost(fx, monkeypatch)
    resume(fx, log)
    actor, payload = host.actor()
    host.install_attribution(actor)
    entry = capture_supplement(fx, log, "maintenance-bootstrap-publication", payload)
    assert execute(fx, entry, "push").returncode == 0
    assert execute(fx, entry, "pr-create").returncode == 0
    host.mode("merge-pending")
    result = execute(fx, entry, "green-merge")
    assert result.returncode != 0 and not host.load()["pull"]["merged"]
    rows = operation_rows(fx, entry, "green-merge")
    identity = rows[-1]["operation_id"]
    assert rows[-1]["state"] == "ambiguous"
    assert rows[-1]["evidence"]["host_correlation"] == "630b9d5e-3f2a-4f7e-8b0c-2d5f9a8c1e42"
    assert rows[-1]["evidence"]["host_response"]["body"]["details"]["expected_head_sha"] == payload["head"]
    assert host.calls("merge-get")[-1]["argv"][1].endswith(
        "/merge-async/630b9d5e-3f2a-4f7e-8b0c-2d5f9a8c1e42")
    assert execute(fx, entry, "green-merge").returncode != 0
    assert len(host.calls("merge-put")) == 1
    # A real returned pending UUID enters the controller and both reports. Polls
    # may refresh the unsigned observation cache, never append clock-only events.
    checked = fx.run("check-minor", "v4.15", "--session", CODEX_SESSION)
    assert checked.returncode == 1, checked.stdout + checked.stderr
    signed_before = fx.record_path().read_bytes()
    pending = native_job_frame(fx, checked)
    job = next(job for job in pending["observation"]["jobs"] if job.get("native_bridge"))
    handle = "github-merge:630b9d5e-3f2a-4f7e-8b0c-2d5f9a8c1e42"
    endpoint = "https://api.github.com/repos/bendourthe/Nexus-Hub/pulls/314/merge-async/630b9d5e-3f2a-4f7e-8b0c-2d5f9a8c1e42"
    assert job["handle"] == handle and job["url"] == endpoint and job["status"] == "pending"
    first_data, _ = native_snapshot_reports(fx)
    reporter = run_plan.reporting_module("status_report")
    receipt = reporter.select_report(first_data, None, "start")["receipt"]
    pending = native_job_frame(fx, checked, pending)
    second_data, _ = native_snapshot_reports(fx)
    first_job = next(job for job in first_data["continuation"]["jobs"] if job.get("native_bridge"))
    second_job = next(job for job in second_data["continuation"]["jobs"] if job.get("native_bridge"))
    assert first_job["handle"] == second_job["handle"] == handle
    assert first_job["status"] == second_job["status"] == "pending"
    assert second_job["observed_at"] > first_job["observed_at"]
    # Advance only the report scheduling clock beyond the interval. Provider
    # timestamps, cache signatures and observations remain the actual poll output.
    after_interval = copy.deepcopy(second_data)
    after_interval["observed_at"] = (dt.datetime.fromisoformat(second_data["observed_at"].replace("Z", "+00:00"))
                                     + dt.timedelta(seconds=601)).isoformat()
    for event in ("checkpoint", "resume", "turn-end"):
        unchanged = reporter.select_report(after_interval, receipt, event, interval=300)
        assert unchanged["mode"] == "none" and unchanged["report"] == ""
    observed_at = next(job for job in pending["observation"]["jobs"] if job.get("native_bridge"))["observed_at"]
    host.mode("merge-pending", "async-get-unavailable")
    unavailable = native_job_frame(fx, checked, pending)
    waiting = next(job for job in unavailable["observation"]["jobs"] if job.get("native_bridge"))
    assert waiting["handle"] == handle and waiting["url"] == endpoint
    assert waiting["status"] == "observation-timeout" and waiting["observed_at"] == observed_at
    assert waiting["observation_attempted_at"] >= observed_at
    assert "unavailable" in waiting["evidence"] and "same returned UUID" in waiting["resume_when"]
    unavailable_data, reports = native_snapshot_reports(fx)
    changed = reporter.select_report(unavailable_data, receipt, "checkpoint")
    assert changed["mode"] == "compact"
    for rendered in reports.values():
        assert rendered.startswith("Waiting for "), rendered
        assert handle in rendered and endpoint in rendered and observed_at in rendered
        assert "observation-timeout" in rendered and "same returned UUID" in rendered
        assert "Nothing running" not in rendered
    assert fx.record_path().read_bytes() == signed_before
    assert len(host.calls("merge-put")) == 1
    assert all(call["argv"][1].endswith("/merge-async/630b9d5e-3f2a-4f7e-8b0c-2d5f9a8c1e42")
               for call in host.calls("merge-get"))
    host.mode("merge-pending")
    refreshed = native_job_frame(fx, checked, unavailable)
    assert next(job for job in refreshed["observation"]["jobs"] if job.get("native_bridge"))["status"] == "pending"
    assert fx.record_path().read_bytes() == signed_before
    merged = host.complete_pending_merge()
    # A mismatching independently observed result cannot complete the reservation.
    host.mode("wrong-final-tree")
    assert execute(fx, entry, "green-merge").returncode != 0
    assert operation_rows(fx, entry, "green-merge")[-1]["state"] == "ambiguous"
    host.mode()
    assert execute(fx, entry, "green-merge").returncode == 0
    row = operation_rows(fx, entry, "green-merge")[-1]
    assert row["operation_id"] == identity and row["state"] == "completed"
    assert row["evidence"]["proof"]["merge_sha"] == merged
    assert len(host.calls("merge-put")) == 1
    # Resume a genuinely admitted unfinished fixture task after the process result.
    # The native declaration and measured predicates provide its authorization.
    terminal = native_job_frame(fx, checked, refreshed, execute_admitted_dependency(fx, host))
    assert terminal["disposition"]["state"] == "working"
    assert terminal["disposition"]["directive"] == "continue"
    assert not any(job.get("handle") == handle for job in terminal["disposition"]["jobs"])
    retired = terminal["disposition"]["completed_jobs"]
    assert any(job["handle"] == handle and job["status"] == "succeeded" and job["result_verified"] for job in retired)
    resumed_data, _ = native_snapshot_reports(fx)
    assert reporter.select_report(resumed_data, changed["receipt"], "checkpoint")["mode"] == "compact"


def test_unused_publication_receipt_cannot_follow_a_changed_actor_head(bridge_case, monkeypatch):
    fx, log = bridge_case
    host = PrivateHost(fx, monkeypatch)
    resume(fx, log)
    actor, payload = host.actor()
    host.install_attribution(actor)
    entry = capture_supplement(fx, log, "maintenance-bootstrap-publication", payload)
    changed = actor / "src/private-maintenance.txt"
    changed.write_text("A later unreviewed private contribution.\n", encoding="utf-8")
    host.git(actor, "add", "--", "src/private-maintenance.txt")
    host.git(actor, "commit", "-q", "-m", "private changed candidate")
    assert host.git(actor, "rev-parse", "HEAD") != payload["head"]
    before = fx.record_path().read_bytes()
    assert execute(fx, entry, "push").returncode != 0
    assert fx.record_path().read_bytes() == before
    assert not host.calls("git-push") and not fx.record()["v415_publication_operations"]


def test_preparation_recovers_only_its_persisted_link_stage(bridge_case, monkeypatch):
    fx, log = bridge_case
    host = PrivateHost(fx, monkeypatch)
    resume(fx, log)
    body = "Private captured recovery notes.\n"
    entry = capture_supplement(fx, log, ".6-release-notes", {"notes": body})
    artifact = fx.record_path().parent / "release-notes" / (
        fx.record_path().stem + "-" + receipt_id(entry) + "-v4.15.6.md")
    driver = fx.tmp / "cut-notes-link.py"
    driver.write_text(
        "import os,sys\nfrom pathlib import Path\n"
        f"sys.path[:0] = [{str(ROOT)!r}, {str(ROOT / 'scripts')!r}]\n"
        "from tests.validators.member_declarations import install\n"
        "class Patch:\n    def setattr(self,obj,key,value): setattr(obj,key,value)\n"
        "install(Patch())\n"
        "import check_plan_completion as ck\n"
        "original=os.link\n"
        "def cut(src,dst,*args,**kwargs):\n"
        "    result=original(src,dst,*args,**kwargs)\n"
        f"    if Path(dst) == Path({str(artifact)!r}): os._exit(83)\n"
        "    return result\n"
        "os.link=cut\nraise SystemExit(ck.main())\n",
        encoding="utf-8")
    argv = command(fx, entry, "prepare-release-notes")
    argv[2] = str(driver)
    stopped = subprocess.run(argv, cwd=fx.work, env=fx.env, capture_output=True,
                             text=True, timeout=90, creationflags=FLAGS)
    assert stopped.returncode == 83, stopped.stdout + stopped.stderr
    assert artifact.read_bytes() == body.encode("utf-8") and artifact.stat().st_nlink == 2
    old_ids = {row["operation_id"] for row in operation_rows(fx, entry, "prepare-release-notes")}
    assert old_ids == {cm._bridge_operation_id(entry, "prepare-release-notes")}
    resumed = execute(fx, entry, "prepare-release-notes")
    assert resumed.returncode == 0, resumed.stdout + resumed.stderr
    assert artifact.read_bytes() == body.encode("utf-8") and artifact.stat().st_nlink == 1
    assert operation_rows(fx, entry, "prepare-release-notes")[-1]["state"] == "completed"
    assert {row["operation_id"] for row in operation_rows(fx, entry, "prepare-release-notes")} == old_ids
    assert not host.calls("release-edit") and host.load()["release"] is None


def test_preparation_refuses_foreign_hardlink_without_removing_it(bridge_case, monkeypatch):
    fx, log = bridge_case
    host = PrivateHost(fx, monkeypatch)
    resume(fx, log)
    body = "Private same bytes do not establish stage ownership.\n"
    entry = capture_supplement(fx, log, ".6-release-notes", {"notes": body})
    artifact = fx.record_path().parent / "release-notes" / (
        fx.record_path().stem + "-" + receipt_id(entry) + "-v4.15.6.md")
    artifact.parent.mkdir(parents=True, exist_ok=True)
    foreign = fx.tmp / "independent-owner-file.md"
    foreign.write_bytes(body.encode("utf-8"))
    os.link(foreign, artifact)
    result = execute(fx, entry, "prepare-release-notes")
    assert result.returncode != 0
    assert artifact.read_bytes() == foreign.read_bytes() == body.encode("utf-8")
    assert artifact.stat().st_nlink == foreign.stat().st_nlink == 2
    assert not any(row["state"] == "completed" for row in operation_rows(fx, entry, "prepare-release-notes"))
    assert not host.calls("release-edit") and host.load()["release"] is None
