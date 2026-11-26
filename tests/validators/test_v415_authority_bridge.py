"""Fixed v4.15 authority receipts and finite private publication controls.

All captures, records and hosting effects in this module are disposable fixtures.
They supply no owner approval, installed-runtime proof or provider-trial evidence.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import subprocess
import sys
import time
from types import SimpleNamespace
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
import completion_minor as cm
import approval_binding as binding
import check_plan_completion as ck
import run_plan

from .test_codex_transcript_approval import Transcript, SESSION as CODEX_SESSION
from .test_minor_execution_permission import (
    ExecutionMinor, SESSION, _git, _isolated_git_config, _no_transport_overrides, _private_native_home,
)


@pytest.fixture
def bridge_case(tmp_path: Path, monkeypatch):
    fx = ExecutionMinor(tmp_path, monkeypatch)
    for path in (fx.work / "docs/releases/v4/v4.15/plans").glob("*.md"):
        if not path.name.startswith("v4.15.0-"):
            path.unlink()
    fx.commit("private single original member")
    fx.integrate()
    assert fx.create().returncode == 0
    fx.add_members(("v4.15.6", "v4.15.9"), transform=lambda version, text: text.replace("T001", "T027") if version == "v4.15.9" else text)
    home = Path(fx.env["USERPROFILE"])
    log = Transcript(home, fx.work, time.time() - 10, session=CODEX_SESSION)
    fx.env.pop("PYTHONPATH", None)
    fx.env.update(PYTHONNOUSERSITE="1", PYTHONDONTWRITEBYTECODE="1")
    monkeypatch.chdir(fx.work)
    return fx, log


def resume(fx, log: Transcript, session: str = CODEX_SESSION):
    before = copy.deepcopy(fx.record())
    rendered = fx.render(session, "--action", "resume", "--question", "--host-transcript", str(log.path))
    assert rendered.returncode == 0, rendered.stdout + rendered.stderr
    log.now = time.time() - 1
    log.user("Approve")
    result = fx.run("record", "resume", "--minor", "v4.15", "--session", session)
    assert result.returncode == 0, result.stdout + result.stderr
    after = fx.record()
    assert after["session_id"] == session
    assert after["approvals"]["classes"] == before["approvals"]["classes"]
    assert after["approvals"]["spend_caps"] == before["approvals"]["spend_caps"]
    return after


def request_file(fx, kind: str, payload: dict) -> Path:
    path = fx.tmp / (kind.lstrip(".") + ".json")
    path.write_text(json.dumps({"kind": kind, "payload": payload}), encoding="utf-8")
    return path


def capture_supplement(fx, log: Transcript, kind: str, payload: dict):
    path = request_file(fx, kind, payload)
    rendered = fx.render(CODEX_SESSION, "--action", cm.AUTHORITY_BRIDGE_ACTION, "--authority", str(path),
                         "--question", "--host-transcript", str(log.path))
    assert rendered.returncode == 0, rendered.stdout + rendered.stderr
    context, record = ck.resolve_minor_controller(fx.record_path(), CODEX_SESSION, minor_protocol=1, execution_protocol=1)
    secret = ck._secret(create=False)
    assert not binding.observe_issued_request(fx.runs, fx.record_path().stem, secret, record, rendered.stdout)
    displayed = json.loads(rendered.stdout)["review_page"]
    assert binding.observe_issued_request(fx.runs, fx.record_path().stem, secret, record, displayed)
    before = fx.record_path().read_bytes()
    missing = fx.run("record", cm.AUTHORITY_BRIDGE_ACTION, "--minor", "v4.15", "--session", CODEX_SESSION, "--authority", str(path))
    assert missing.returncode != 0
    assert fx.record_path().read_bytes() == before
    log.now = time.time() - 1
    log.user("Approve")
    result = fx.run("record", cm.AUTHORITY_BRIDGE_ACTION, "--minor", "v4.15", "--session", CODEX_SESSION, "--authority", str(path))
    assert result.returncode == 0, result.stdout + result.stderr
    entry = fx.record()["v415_authority_receipts"][-1]
    retry = fx.run("record", cm.AUTHORITY_BRIDGE_ACTION, "--minor", "v4.15", "--session", CODEX_SESSION, "--authority", str(path))
    assert retry.returncode == 0, retry.stdout + retry.stderr
    return entry


def test_bridge_has_only_the_four_reviewed_kinds():
    assert cm.AUTHORITY_BRIDGE_KINDS == {
        ".6-release-notes", ".6-repo-description", ".9-t027-budget", "maintenance-bootstrap-publication"}


@pytest.mark.parametrize("raw", ['{"kind":true}', '{"kind":"other"}', '{"kind":".9-t027-budget","kind":"other"}', '{"usd_total":NaN}'])
def test_bridge_payload_parser_rejects_unsafe_requests(raw: str):
    with pytest.raises(cm.MinorMalformed):
        cm.authority_bridge_payload(raw)


@pytest.mark.parametrize("usd,spawns", [(True, 6), (10, True), (-10, 6), (11, 6), (10, 7), (10, 6.0)])
def test_bridge_budget_has_exact_inactive_bounds(usd, spawns):
    with pytest.raises(cm.MinorMalformed):
        cm.authority_bridge_payload(json.dumps({"kind": ".9-t027-budget", "payload": {"usd_total": usd, "spawn_total": spawns}}))


def test_bridge_input_refuses_oversize_and_foreign_hardlinks(tmp_path):
    original = tmp_path / "request.json"
    original.write_bytes(b"x" * 32769)
    with pytest.raises(cm.MinorMalformed):
        cm._bridge_read_bytes(original)
    original.write_bytes(b"{}")
    alias = tmp_path / "alias.json"
    os.link(original, alias)
    with pytest.raises(cm.MinorMalformed):
        cm._bridge_read_bytes(original)
    with pytest.raises(cm.MinorMalformed):
        cm._bridge_read_bytes(alias)
    assert original.read_bytes() == alias.read_bytes() == b"{}"


@pytest.mark.parametrize("app,expected", [(None, 123), (-1, 123), (123, 123), (456, None)])
def test_effective_merge_app_constraints_never_weaken(monkeypatch, app, expected):
    responses = {
        "/branches/develop/protection": {"required_status_checks": {"strict": True, "contexts": [], "checks": [{"context": "gate", "app_id": 123}]}, "enforce_admins": {"enabled": True}},
        "/rules/branches/develop": [{"ruleset_id": 7, "type": "required_status_checks", "parameters": {"strict_required_status_checks_policy": True, "required_status_checks": [{"context": "gate", "integration_id": app}]}}],
        "/rulesets/7?includes_parents=true": {"id": 7, "target": "branch", "enforcement": "active", "bypass_actors": [], "rules": []},
    }
    monkeypatch.setattr(cm, "_bridge_api", lambda _ck, _ctx, _record, endpoint: responses[endpoint])
    native = SimpleNamespace(_required_contexts=lambda *_args: ["gate"])
    if expected is None:
        with pytest.raises(cm.MinorMalformed, match="conflicting-required-check-apps"):
            cm._bridge_server_gate(native, object(), {})
    else:
        assert cm._bridge_server_gate(native, object(), {})["required"] == {"gate": expected}


def test_native_children_inherit_no_bytecode_without_global_mutation(monkeypatch):
    monkeypatch.delenv("PYTHONDONTWRITEBYTECODE", raising=False)
    assert ck._env()["PYTHONDONTWRITEBYTECODE"] == "1"
    assert "PYTHONDONTWRITEBYTECODE" not in os.environ


def test_prewrite_recovery_digest_preserves_every_original_authority_bound():
    original = {"nonce": "private", "session_id": "old", "repo_root": "same", "implementation_controller": {"repo_root": "same"},
        "approvals": {"classes": [{"class": "release"}], "spend_caps": {"vendor": 0}, "transcript_decisions": []},
        "members": [{"version": "v4.15.6", "source_branch": "original", "approvals": {"classes": [{"class": "push-merge"}]}}]}
    resumed = copy.deepcopy(original)
    resumed.update(session_id="new", continuations=[{"private": "native-owner-transition"}], continuation_format=1, pause=None,
                   implementation_controller={"repo_root": "same", "git_common_dir": "same-common"}, approvals_hmac="new-hmac")
    resumed["approvals"]["transcript_decisions"].append({"private": "genuine-resume"})
    assert cm._bridge_recovery_digest(resumed) == cm._bridge_recovery_digest(original)
    for field in ("global-class", "global-cap", "member-class", "source-branch", "repo-root", "other-state"):
        changed = copy.deepcopy(resumed)
        if field == "global-class": changed["approvals"]["classes"].append({"class": "other"})
        elif field == "global-cap": changed["approvals"]["spend_caps"]["vendor"] = 10
        elif field == "member-class": changed["members"][0]["approvals"]["classes"].append({"class": "other"})
        elif field == "source-branch": changed["members"][0]["source_branch"] = "other"
        elif field == "repo-root": changed["repo_root"] = "other"
        else: changed["unrelated_state"] = "changed"
        assert cm._bridge_recovery_digest(changed) != cm._bridge_recovery_digest(original), field


def test_provider_observation_metadata_is_not_material_progress():
    state = run_plan.continuation_module()
    original = {"jobs": [{"id": "exact-operation", "handle": "github-merge:actual-uuid", "status": "pending",
        "observed_at": "2026-11-25T12:00:00+00:00", "observation_attempted_at": "2026-11-25T12:00:00+00:00",
        "provider_observation": {"status": "pending", "sha256": "a" * 64, "observed_at": "2026-11-25T12:00:00+00:00"},
        "provider_observation_hmac": "old-cache-seal"}]}
    changed = copy.deepcopy(original)
    changed["jobs"][0].update(observed_at="2026-11-25T12:10:01+00:00", observation_attempted_at="2026-11-25T12:10:01+00:00", provider_observation_hmac="new-cache-seal")
    changed["jobs"][0]["provider_observation"].update(observed_at="2026-11-25T12:10:01+00:00", sha256="b" * 64)
    assert state.semantic_fingerprint(changed) == state.semantic_fingerprint(original)
    for field, value in (("handle", "github-merge:other-uuid"), ("status", "observation-timeout")):
        real_change = copy.deepcopy(changed)
        real_change["jobs"][0][field] = value
        assert state.semantic_fingerprint(real_change) != state.semantic_fingerprint(original)


def test_async_job_observations_retain_only_the_actual_bound_handle(monkeypatch):
    identity = "630b9d5e-3f2a-4f7e-8b0c-2d5f9a8c1e42"
    entry = {"page": {"kind": "maintenance-bootstrap-publication"}}
    receipt = cm._amendment_digest(entry)
    row = {"operation": "green-merge", "operation_id": "a" * 64, "receipt_id": receipt,
           "target": {"head": "b" * 40, "number": 314}, "at": "2026-11-25T12:00:00+00:00",
           "evidence": {"host_correlation": identity}}
    monkeypatch.setattr(cm, "authority_bridge_operation_history", lambda *_args: {row["operation_id"]: row})
    monkeypatch.setattr(cm, "authority_bridge_history", lambda *_args: [entry])
    monkeypatch.setattr(cm, "_bridge_observe_effect", lambda *_args: None)
    details = {"uuid": identity, "expected_head_sha": "b" * 40, "merge_method": "merge", "merge_action": "direct_merge", "bypass_rules": False}
    observation = {"status": "pending", "details": details}
    calls = []
    def poll(_ck, _ctx, _record, endpoint):
        calls.append(endpoint)
        return observation
    monkeypatch.setattr(cm, "_bridge_api", poll)
    native = SimpleNamespace(_secret=lambda **_kwargs: b"private-unit-key", _now=lambda: "2026-11-25T12:01:00+00:00")
    record = {"nonce": "private-nonce", "repo": "bendourthe/Nexus-Hub"}
    pending = cm.authority_bridge_jobs(native, object(), record, [])[0]
    assert pending["status"] == "pending" and pending["handle"] == "github-merge:" + identity
    assert calls == ["/pulls/314/merge-async/" + identity]
    observation = None
    native._now = lambda: "2026-11-25T12:02:00+00:00"
    unavailable = cm.authority_bridge_jobs(native, object(), record, [pending])[0]
    assert unavailable["status"] == "observation-timeout"
    assert unavailable["observed_at"] == pending["observed_at"]
    assert unavailable["observation_attempted_at"] != pending["observed_at"]
    assert unavailable["handle"] == pending["handle"] and unavailable["url"] == pending["url"]
    assert "unavailable" in unavailable["evidence"]
    forged = copy.deepcopy(pending)
    forged["provider_observation"]["status"] = "merged"
    assert cm.authority_bridge_jobs(native, object(), record, [forged])[0]["provider_observation"]["status"] == "unverified"
    observation = {"status": "pending", "details": {**details, "uuid": "f" * 36}}
    assert cm.authority_bridge_jobs(native, object(), record, [pending])[0]["status"] == "observation-timeout"
    observation = {"status": "merged"}
    unmatched = cm.authority_bridge_jobs(native, object(), record, [pending])[0]
    assert unmatched["status"] == "observation-timeout" and not unmatched["result_verified"]
    assert "final merge tree" in unmatched["evidence"]
    assert row["evidence"] == {"host_correlation": identity}  # Polls never append native operation history.


def test_late_response_refuses_foreign_inode_swapped_only_during_inner_read(tmp_path, monkeypatch):
    directory = tmp_path / 'publication-jobs'
    directory.mkdir()
    operation, command, head = 'a' * 64, 'b' * 64, 'c' * 40
    def response(identity):
        return json.dumps({'status': 'pending', 'details': {'uuid': identity, 'expected_head_sha': head,
            'merge_method': 'merge', 'merge_action': 'direct_merge', 'bypass_rules': False}}).encode()
    raw = response('630b9d5e-3f2a-4f7e-8b0c-2d5f9a8c1e42')
    foreign_raw = response('12345678-1234-4234-9234-123456789abc')
    output, foreign, saved = directory / (operation + '.retained.stdout'), directory / 'foreign.stdout', directory / 'original.saved'
    output.write_bytes(raw)
    foreign.write_bytes(foreign_raw)
    identity = output.stat()
    record = type('PrivateRecord', (dict,), {})(nonce='private-unit')
    record.record_path = tmp_path / 'private-record.json'
    row = {'operation_id': operation, 'command_sha256': command, 'evidence': {}, 'target': {'head': head, 'number': 314}}
    result = {'operation_id': operation, 'run_nonce': record['nonce'], 'command_sha256': command, 'exit_code': None,
        'stdout_sha256': None, 'stdout_path': str(output), 'stdout_identity': {'device': identity.st_dev, 'inode': identity.st_ino}}
    reader = cm._bridge_read_bytes
    def swap(path, *args, **kwargs):
        os.replace(output, saved)
        os.replace(foreign, output)
        try:
            return reader(path, *args, **kwargs)
        finally:
            os.replace(output, foreign)
            os.replace(saved, output)
    monkeypatch.setattr(cm, '_bridge_read_bytes', swap)
    monkeypatch.setattr(run_plan, 'observe_authority_process', lambda *_args: {'state': 'ended'})
    with pytest.raises(cm.MinorMalformed, match='opened-identity-changed'):
        cm._bridge_async_result(object(), object(), record, row, result)
    assert output.read_bytes() == raw and foreign.read_bytes() == foreign_raw
    assert (output.stat().st_dev, output.stat().st_ino) == (identity.st_dev, identity.st_ino)


def test_failed_response_retires_only_observation_and_exposes_bound_failure(monkeypatch):
    entry = {'page': {'kind': 'maintenance-bootstrap-publication'}}
    entry["page"]["payload_sha256"] = cm._amendment_digest(entry["page"].get("payload", {}))
    receipt = cm._amendment_digest(entry)
    operation, command = 'a' * 64, 'b' * 64
    handle = 'process:123:1.000000'
    row = {'operation': 'green-merge', 'operation_id': operation, 'receipt_id': receipt, 'command_sha256': command,
        'state': 'ambiguous', 'at': '2026-11-25T12:00:00+00:00', 'target': {}, 'evidence': {
        'host_response': {'path': 'private-retained.stdout', 'sha256': 'd' * 64, 'body': {'status': 'failed', 'details': {}}},
        'process_result': {'operation_id': operation, 'run_nonce': 'private', 'command_sha256': command, 'exit_code': None,
            'handle': handle, 'process': {'pid': 123, 'created_at': 1.0}, 'job_created_at': 1.0}}}
    monkeypatch.setattr(cm, 'authority_bridge_operation_history', lambda *_args: {operation: row})
    monkeypatch.setattr(cm, 'authority_bridge_history', lambda *_args: [entry])
    monkeypatch.setattr(run_plan, 'observe_authority_process', lambda *_args: {'state': 'ended', 'handle': handle, 'observed_at': row['at'], 'reason': 'Unknown exit'})
    native = SimpleNamespace(_secret=lambda **_kwargs: b'private-unit', _now=lambda: row['at'])
    record = {'nonce': 'private', 'repo': 'bendourthe/Nexus-Hub'}
    jobs = cm.authority_bridge_jobs(native, object(), record, [])
    conditions, resolutions = cm.authority_bridge_host_failures(native, object(), record)
    assert len(jobs) == 1 and jobs[0]['handle'] == handle and jobs[0]['status'] == 'succeeded'
    assert jobs[0]['result_kind'] == 'hosting-response-observed' and jobs[0]['response_status'] == 'failed'
    assert jobs[0]['exit_code'] is None and jobs[0]['response_receipt']['sha256'] == 'd' * 64
    assert len(conditions) == 1 and conditions[0]['id'] == 'bridge:failure:' + operation and not resolutions
    state = run_plan.continuation_module().reconcile({'objective': 'Unfinished private objective', 'remaining_tasks': 1,
        'work': [], 'requests': [], 'jobs': jobs, 'external_conditions': conditions, 'completion': {'verified': False}})
    assert state['state'] == 'blocked_external' and not state['jobs']
    assert state['completed_jobs'][0]['exit_code'] is None
    assert row['evidence']['process_result']['exit_code'] is None


def test_absent_and_reused_pid_keep_same_unknown_exit_semantics(monkeypatch):
    import psutil
    result = {'process': {'pid': 123, 'created_at': 1.0}, 'handle': 'process:123:1.000000', 'exit_code': None}
    def absent(_pid):
        raise psutil.NoSuchProcess(123)
    monkeypatch.setattr(psutil, 'Process', absent)
    missing = run_plan.observe_authority_process(result)
    monkeypatch.setattr(psutil, 'Process', lambda _pid: SimpleNamespace(create_time=lambda: 2.0))
    reused = run_plan.observe_authority_process(result)
    assert missing['state'] == reused['state'] == 'ended'
    assert missing['reason'] == reused['reason'] and missing['handle'] == reused['handle'] == result['handle']
    assert run_plan.continuation_module().semantic_fingerprint(missing) == run_plan.continuation_module().semantic_fingerprint(reused)
    assert result['exit_code'] is None


def test_unconsumed_bridge_page_cannot_follow_native_record_changes(bridge_case):
    fx, log = bridge_case
    resume(fx, log)
    path = request_file(fx, ".6-release-notes", {"notes": "Private stale unconsumed page.\n"})
    rendered = fx.render(CODEX_SESSION, "--action", cm.AUTHORITY_BRIDGE_ACTION, "--authority", str(path),
                         "--question", "--host-transcript", str(log.path))
    assert rendered.returncode == 0, rendered.stdout + rendered.stderr
    context, record = ck.resolve_minor_controller(fx.record_path(), CODEX_SESSION, minor_protocol=1, execution_protocol=1)
    assert binding.observe_issued_request(fx.runs, fx.record_path().stem, ck._secret(create=False), record,
                                          json.loads(rendered.stdout)["review_page"])
    worker = fx.worker("v4.15.0")
    member = fx.member("v4.15.0")
    text = (worker / member["plan_path"]).read_text(encoding="utf-8")
    claims = fx.tmp / "stale-page-native-claims.json"
    claims.write_text(text.split("```json\n", 1)[1].split("\n```", 1)[0], encoding="utf-8")
    admitted = fx.run("record", "member-implement-start", "--minor", "v4.15", "--session", CODEX_SESSION,
        "--member", "v4.15.0", "--worktree", str(worker), "--head", _git(worker, "rev-parse", "HEAD"), "--claims", str(claims))
    assert admitted.returncode == 0, admitted.stdout + admitted.stderr
    before = fx.record_path().read_bytes()
    log.now = time.time() - 1
    log.user("Approve")
    stale = fx.run("record", cm.AUTHORITY_BRIDGE_ACTION, "--minor", "v4.15", "--session", CODEX_SESSION, "--authority", str(path))
    assert stale.returncode != 0 and "page-changed" in stale.stdout
    assert fx.record_path().read_bytes() == before
    assert "v415_authority_receipts" not in fx.record()


def test_consumed_supplement_write_recovers_after_genuine_owner_resume(bridge_case):
    fx, log = bridge_case
    resume(fx, log)
    payload = {"notes": "Private retained pre-write capture.\n"}
    path = request_file(fx, ".6-release-notes", payload)
    rendered = fx.render(CODEX_SESSION, "--action", cm.AUTHORITY_BRIDGE_ACTION, "--authority", str(path),
                         "--question", "--host-transcript", str(log.path))
    assert rendered.returncode == 0, rendered.stdout + rendered.stderr
    context, record = ck.resolve_minor_controller(fx.record_path(), CODEX_SESSION, minor_protocol=1, execution_protocol=1)
    assert binding.observe_issued_request(fx.runs, fx.record_path().stem, ck._secret(create=False), record,
                                          json.loads(rendered.stdout)["review_page"])
    log.now = time.time() - 1
    log.user("Approve")
    before = fx.record_path().read_bytes()
    driver = fx.tmp / "cut-after-bridge-capture.py"
    driver.write_text("import os,sys\n" + f"sys.path[:0]=[{str(ROOT)!r},{str(ROOT / 'scripts')!r}]\n"
        "import check_plan_completion as ck\nfrom tests.validators.member_declarations import install\n"
        "class Patch:\n    def setattr(self,obj,key,value): setattr(obj,key,value)\n"
        "install(Patch())\noriginal=ck._write_record\n"
        "def cut(path,record,*args,**kwargs):\n"
        "    if record.get('v415_authority_receipts'): os._exit(83)\n"
        "    return original(path,record,*args,**kwargs)\n"
        "ck._write_record=cut\nraise SystemExit(ck.main())\n", encoding="utf-8")
    stopped = subprocess.run([sys.executable, "-B", str(driver), "record", cm.AUTHORITY_BRIDGE_ACTION,
        "--minor", "v4.15", "--session", CODEX_SESSION, "--authority", str(path)], cwd=fx.work, env=fx.env,
        capture_output=True, text=True, timeout=90, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    assert stopped.returncode == 83, stopped.stdout + stopped.stderr
    assert fx.record_path().read_bytes() == before
    consumed = [row for row in binding.used_recovery_rounds(fx.runs, fx.record_path().stem, ck._secret(create=False))
                if row.get("action") == cm.AUTHORITY_BRIDGE_ACTION]
    assert len(consumed) == 1
    sealed_page = copy.deepcopy(consumed[0]["page"])
    next_owner = "12def678-1234-4234-9234-123456789abc"
    next_log = Transcript(Path(fx.env["USERPROFILE"]), fx.work, time.time() - 10, session=next_owner)
    resumed = resume(fx, next_log, session=next_owner)
    old_owner = fx.run("record", cm.AUTHORITY_BRIDGE_ACTION, "--minor", "v4.15", "--session", CODEX_SESSION, "--authority", str(path))
    assert old_owner.returncode != 0
    path.write_text(json.dumps({"kind": ".6-release-notes", "payload": {"notes": "Changed unapproved body.\n"}}), encoding="utf-8")
    before_wrong = fx.record_path().read_bytes()
    wrong = fx.run("record", cm.AUTHORITY_BRIDGE_ACTION, "--minor", "v4.15", "--session", next_owner, "--authority", str(path))
    assert wrong.returncode != 0 and fx.record_path().read_bytes() == before_wrong
    path.write_text(json.dumps({"kind": ".6-release-notes", "payload": payload}), encoding="utf-8")
    recovered = fx.run("record", cm.AUTHORITY_BRIDGE_ACTION, "--minor", "v4.15", "--session", next_owner, "--authority", str(path))
    assert recovered.returncode == 0, recovered.stdout + recovered.stderr
    saved = fx.record()
    assert saved["v415_authority_receipts"][0]["page"] == sealed_page
    assert saved["v415_authority_receipts"][0]["accepted"]["authorization_context"] == consumed[0]["capture"]
    assert saved["approvals"]["classes"] == resumed["approvals"]["classes"]
    assert saved["approvals"]["spend_caps"] == resumed["approvals"]["spend_caps"]
    assert not saved["v415_publication_operations"]
    again = fx.run("record", cm.AUTHORITY_BRIDGE_ACTION, "--minor", "v4.15", "--session", next_owner, "--authority", str(path))
    assert again.returncode == 0 and fx.record() == saved


def test_private_codex_resume_notes_capture_authorize_controller_and_report(bridge_case):
    fx, log = bridge_case
    original = copy.deepcopy(fx.record())
    old_bytes = fx.record_path().read_bytes()
    premature = fx.run("record", "authorize", "--minor", "v4.15", "--member", "v4.15.6", "--session", CODEX_SESSION,
                       "--approval-class", "push-merge", "--request", "{}")
    assert premature.returncode != 0
    assert fx.record_path().read_bytes() == old_bytes
    resume(fx, log)
    context, record = ck.resolve_minor_controller(fx.record_path(), CODEX_SESSION, minor_protocol=1, execution_protocol=1)
    view = ck.project(record, "v4.15.6")
    assert view["approvals"]["autonomy_policy"] is None
    args = argparse.Namespace(minor="v4.15", repo=str(fx.work), plan=None, member="v4.15.6", session=CODEX_SESSION,
                              approval_class="push-merge", request="{}")
    before = fx.record_path().read_bytes()
    assert not isinstance(ck.authorization_probe(args), int)
    assert fx.record_path().read_bytes() == before
    stale_owner = fx.run("record", "authorize", "--minor", "v4.15", "--member", "v4.15.6", "--session", SESSION,
                         "--approval-class", "push-merge", "--request", "{}")
    assert stale_owner.returncode != 0
    entry = capture_supplement(fx, log, ".6-release-notes", {"notes": "Private exact release6 notes.\n"})
    context, current = ck.resolve_minor_controller(fx.record_path(), CODEX_SESSION, minor_protocol=1, execution_protocol=1)
    identity = hashlib.sha256(binding.canonical(entry)).hexdigest()
    args.approval_class = cm.AUTHORITY_BRIDGE_ACTION
    args.request = json.dumps({"receipt_id": identity, "operation": "release-notes"})
    before = fx.record_path().read_bytes()
    authorized = ck.authorization_probe(args)
    assert not isinstance(authorized, int)
    assert authorized[2]["permission_verified"] is True
    assert authorized[2]["effect_observed"] is False
    assert authorized[2]["counters_consumed"] is False
    assert fx.record_path().read_bytes() == before
    issued = binding.issued_requests(fx.runs, fx.record_path().stem, ck._secret(create=False), current)
    results = cm.continuation_owner_results(ck, current, issued)
    assert any(row["authority_receipt"] == identity for row in results)
    scope = argparse.Namespace(minor=True, label="v4.15", repo_root=fx.work, observer_session=CODEX_SESSION)
    facts = run_plan.native_owner_observation(scope, fx.record_path(), current, None, remaining_tasks=3)
    assert facts and any(row["authority_receipt"] == identity for row in facts["resolutions"])
    with pytest.raises(ValueError, match="unfinished implementation requires"):
        run_plan.continuation_module().reconcile(facts)
    assert ck.project(current, "v4.15.6")["v415_authority"][0]["execution"] == "not observed"
    assert current["approvals"]["classes"] == original["approvals"]["classes"]
    assert current["approvals"]["spend_caps"] == original["approvals"]["spend_caps"]
    assert current["minor_amendment_members"] == original["minor_amendment_members"]
    # A concrete next action comes from a real admitted worker and native checker,
    # rather than inventing feasible work solely to make a report render.
    worker = fx.worker("v4.15.0")
    member = fx.member("v4.15.0")
    plan = worker / member["plan_path"]
    declaration = json.loads(plan.read_text(encoding="utf-8").split("```json\n", 1)[1].split("\n```", 1)[0])
    claims = fx.tmp / "original-worker-claims.json"
    claims.write_text(json.dumps(declaration), encoding="utf-8")
    admitted = fx.run("record", "member-implement-start", "--minor", "v4.15", "--session", CODEX_SESSION,
                      "--member", "v4.15.0", "--worktree", str(worker), "--head", _git(worker, "rev-parse", "HEAD"), "--claims", str(claims))
    assert admitted.returncode == 0, admitted.stdout + admitted.stderr
    source = next(path for path in declaration["write_paths"] if path.startswith("src/"))
    observed_source = worker / source
    observed_source.parent.mkdir(parents=True, exist_ok=True)
    observed_source.write_text("Private admitted fixture work.\n", encoding="utf-8")
    checked_member = fx.run("check-member", "--minor", "v4.15", "--member", "v4.15.0", "--session", CODEX_SESSION, "--json")
    assert checked_member.returncode == 1, checked_member.stdout + checked_member.stderr
    predicates = json.loads(checked_member.stdout.splitlines()[-1])["predicates"]
    assert predicates["implementation.identity"] == "met" and predicates["task.T001"] == "unmet"
    checked_minor = fx.run("check-minor", "v4.15", "--session", CODEX_SESSION)
    assert checked_minor.returncode == 1, checked_minor.stdout + checked_minor.stderr
    context, current = ck.resolve_minor_controller(fx.record_path(), CODEX_SESSION, minor_protocol=1, execution_protocol=1)
    # These are the native producer's scope/objective facts, not report-only prose.
    observation = {"objective": facts["objective"], "objective_complete": False, "objective_source": facts["objective_source"],
        "remaining_tasks": 3, "work": [{"id": "admitted-original-task", "title": "Finish the native admitted v4.15.0 task.T001",
        "authorized": predicates["implementation.identity"] == "met", "feasible": observed_source.is_file(),
        "evidence": "Native implementation.identity=met and task.T001=unmet; the exact admitted source was written and observed in the private worker."}]}
    frame = run_plan.reconcile_observation(scope, fx.record_path(), current, observation, checked_minor.returncode, checked_minor.stdout, readonly=True)
    run_plan.save_continuation(fx.record_path(), frame)
    before = fx.record_path().read_bytes()
    protected = copy.deepcopy(current["v415_authority_receipts"])
    controller = current["implementation_controller"]
    for changed in ({**controller, "repo_root": str(fx.tmp / "other-controller")},
                    {**controller, "git_common_dir": str(fx.tmp / "other-common")},
                    {**controller, "generation": 1}):
        invalid = copy.deepcopy(dict(current))
        invalid["implementation_controller"] = changed
        invalid["approvals_hmac"] = cm._sign(ck, invalid, ck._secret(create=False))
        with pytest.raises(cm.MinorMalformed):
            cm.authority_bridge_history(ck, context, invalid)
    assert current["v415_authority_receipts"] == protected
    # Fresh source CLI snapshot and renderer, using only the shared fixture declarations.
    driver = fx.tmp / "bridge-snapshot.py"
    driver.write_text("import runpy, sys\n" + f"sys.path.insert(0, {str(ROOT)!r})\n"
        "from tests.validators.member_declarations import install\n"
        "class Patch:\n    def setattr(self, obj, key, value): setattr(obj, key, value)\n"
        "install(Patch())\n" + f"sys.argv[0] = {str(ROOT / 'catalog/skills/workflow/implement-phase/scripts/status_snapshot.py')!r}\n"
        "runpy.run_path(sys.argv[0], run_name='__main__')\n", encoding="utf-8")
    snapshot = subprocess.run([sys.executable, "-B", str(driver), "--repo", str(fx.work), "--scope", "v4.15", "--record", str(fx.record_path()), "--runs-dir", str(fx.runs)], cwd=fx.work, env=fx.env,
                              capture_output=True, text=True, timeout=90, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    assert snapshot.returncode == 0, snapshot.stdout + snapshot.stderr
    data = json.loads(snapshot.stdout)
    report = run_plan.reporting_module("status_report").render(data, "full")
    assert "MINOR COMPLETE" not in report.splitlines()[0]
    assert "capture verified; permission captured; enforcement guarded consumer required; effect not observed" in report
    assert fx.record_path().read_bytes() == before


def test_fixed_host_observations_and_terminal_diagnostics_preserve_report_cadence():
    """Real shared reconciliation/reporting with unit history/API/process observations."""
    import importlib.util
    from unittest.mock import patch
    state = run_plan.continuation_module()
    entry = {'page': {'kind': 'maintenance-bootstrap-publication'}}
    entry["page"]["payload_sha256"] = cm._amendment_digest(entry["page"].get("payload", {}))
    receipt = cm._amendment_digest(entry)
    operation, command, head = 'a' * 64, 'b' * 64, 'c' * 40
    handle = 'process:123:1.000000'
    record = {'nonce': 'private-pure', 'repo': 'bendourthe/Nexus-Hub'}
    clock = ['2026-11-25T12:00:00+00:00']
    native = SimpleNamespace(_secret=lambda **_kw: b'private-pure-key', _now=lambda: clock[0])
    controls = []

    def source_result():
        return {'operation_id': operation, 'run_nonce': record['nonce'], 'command_sha256': command, 'exit_code': None,
            'handle': handle, 'process': {'pid': 123, 'created_at': 1.0}, 'job_created_at': 1.0}

    def row_for(kind):
        return {'operation': kind, 'operation_id': operation, 'receipt_id': receipt, 'command_sha256': command,
            'state': 'ambiguous', 'at': clock[0], 'target': {'head': head, 'number': 314},
            'evidence': {'process_result': source_result()}}

    def observation(jobs, conditions, resolutions=None, work=None):
        return {'objective': 'Private pure control objective', 'remaining_tasks': 1, 'requests': [], 'jobs': jobs,
            'external_conditions': conditions, 'condition_resolutions': resolutions or [], 'work': work or [], 'completion': {'verified': False}}

    for kind in ('push', 'pr-create', 'repo-description'):
        row = row_for(kind)
        lifecycle = {'state': 'running', 'handle': handle, 'observed_at': clock[0], 'reason': 'Actual observer unit seam'}
        with patch.object(cm, 'authority_bridge_operation_history', side_effect=lambda *_: {operation: row}), patch.object(cm, 'authority_bridge_history', return_value=[entry]), patch.object(run_plan, 'observe_authority_process', side_effect=lambda *_: lifecycle):
            jobs = cm.authority_bridge_jobs(native, object(), record, [])
            conditions, resolutions = cm.authority_bridge_host_failures(native, object(), record, jobs)
            assert len(jobs) == 1 and jobs[0]['handle'] == handle and jobs[0]['status'] == 'running'
            assert not conditions and not resolutions
            lifecycle['state'] = 'ended'
            ended = cm.authority_bridge_jobs(native, object(), record, jobs)
            conditions, resolutions = cm.authority_bridge_host_failures(native, object(), record, ended)
            assert ended[0]['status'] == 'succeeded' and ended[0]['result_kind'] == 'process-ended-observed'
            assert ended[0]['result_verified'] is True and ended[0]['exit_code'] is None
            assert 'exit remains unknown' in ended[0]['evidence']
            assert conditions[0]['id'] == 'bridge:effect:' + operation and not resolutions
            blocked = state.reconcile(observation(ended, conditions))
            assert blocked['state'] == 'blocked_external' and not blocked['jobs']
            row['state'] = 'completed'
            row['evidence'].update(effect_observed=True, proof={'private_matched_effect': kind})
            verified = cm.authority_bridge_jobs(native, object(), record, ended)
            conditions, resolutions = cm.authority_bridge_host_failures(native, object(), record, verified)
            assert verified[0]['result_kind'] == 'hosting-effect-observed' and verified[0]['exit_code'] is None
            assert resolutions[0]['condition_id'] == 'bridge:effect:' + operation and resolutions[0]['verified']
            resumed = state.reconcile(observation(verified, conditions, resolutions,
                [{'id': 'unit-work', 'title': 'Unit-only independent work', 'authorized': True, 'feasible': True,
                  'evidence': 'Unit seam for condition retirement; not native work acceptance.'}]), blocked)
            assert resumed['state'] == 'working' and not resumed['external_conditions']
            row['state'] = 'ambiguous'
            row['evidence'] = {}
            absent = cm.authority_bridge_jobs(native, object(), record, [])
            conditions, resolutions = cm.authority_bridge_host_failures(native, object(), record, absent)
            assert not absent and conditions[0]['id'] == 'bridge:effect:' + operation
        controls.append(kind + ':live-ended-unknown-matched-nohandle')

    row = row_for('green-merge')
    row['evidence'] = {'host_correlation': '630b9d5e-3f2a-4f7e-8b0c-2d5f9a8c1e42'}
    api = [{'status': 'failed', 'details': {'message': 'Private failure clock1'}}]
    with patch.object(cm, 'authority_bridge_operation_history', side_effect=lambda *_: {operation: row}), patch.object(cm, 'authority_bridge_history', return_value=[entry]), patch.object(cm, '_bridge_api', side_effect=lambda *_: api[0]), patch.object(cm, '_bridge_observe_effect', return_value=None):
        failed = cm.authority_bridge_jobs(native, object(), record, [])[0]
        first_digest = failed['provider_observation']['first_failure_sha256']
        conditions, resolutions = cm.authority_bridge_host_failures(native, object(), record, [failed])
        assert failed['status'] == 'failed' and first_digest in conditions[0]['evidence']
        initial = state.reconcile(observation([failed], conditions))
        clock[0] = '2026-11-25T12:10:01+00:00'
        api[0] = {'status': 'failed', 'details': {'message': 'Private failure clock2'}}
        repeated = cm.authority_bridge_jobs(native, object(), record, [failed])[0]
        conditions, resolutions = cm.authority_bridge_host_failures(native, object(), record, [repeated])
        assert repeated['provider_observation']['first_failure_sha256'] == first_digest
        same = state.reconcile(observation([repeated], conditions), initial)
        assert same['fingerprint'] == initial['fingerprint']
        report_spec = importlib.util.spec_from_file_location('_scratch_status_report', ROOT / 'catalog/skills/workflow/implement-phase/scripts/status_report.py')
        reporter = importlib.util.module_from_spec(report_spec)
        report_spec.loader.exec_module(reporter)
        def report_data(current_state):
            data = json.loads((ROOT / 'catalog/skills/workflow/implement-phase/references/status-snapshot.json').read_text(encoding='utf-8'))
            data.update(observed_at=clock[0], active=True, running=[], decisions=[], manual_actions=[], questions=[],
                continuation=copy.deepcopy(current_state))
            data.pop('continuation_observation', None)
            data.pop('previous_continuation', None)
            for key in ('external_conditions', 'condition_resolutions', 'resolutions', 'work', 'completion', 'native_goal'):
                data.pop(key, None)
            return data
        initial_report = reporter.select_report(report_data(initial), None, 'checkpoint')['receipt']
        previous_state = initial
        previous_job = failed
        for offset, status in enumerate(('pending', 'enqueued', 'pending', None, 'enqueued', None)):
            clock[0] = '2026-11-25T12:%02d:01+00:00' % (20 + offset)
            api[0] = None if status is None else {'status': status, 'details': {'uuid': row['evidence']['host_correlation'], 'expected_head_sha': head,
                'merge_method': 'merge', 'merge_action': 'direct_merge', 'bypass_rules': False}}
            current_job = cm.authority_bridge_jobs(native, object(), record, [previous_job])[0]
            current_conditions, _ = cm.authority_bridge_host_failures(native, object(), record, [current_job])
            current_state = state.reconcile(observation([current_job], current_conditions), previous_state)
            assert current_state['state'] == 'blocked_external' and not current_state['jobs']
            assert current_state['fingerprint'] == initial['fingerprint']
            assert [job['id'] for job in current_state['completed_jobs']] == [failed['id']]
            assert current_job['provider_observation']['terminal_diagnostic']['status'] == (status or 'unavailable')
            assert current_job['provider_observation']['terminal_diagnostic']['observed_at'] == clock[0]
            assert current_job['provider_observation_hmac'] != previous_job['provider_observation_hmac']
            for event in ('checkpoint', 'resume', 'turn-end'):
                assert reporter.select_report(report_data(current_state), initial_report, event)['mode'] == 'none'
            for mode in ('compact', 'full'):
                assert reporter.render(report_data(current_state), mode)
            previous_state, previous_job = current_state, current_job
        # A real outcome/effect change remains material; diagnostic exclusion is not global.
        material = copy.deepcopy(previous_state)
        material['completed_jobs'][0]['status'] = 'succeeded'
        material['completed_jobs'][0]['provider_observation']['status'] = 'merged'
        material['completed_jobs'][0]['provider_observation']['effect_sha256'] = 'e' * 64
        assert state.semantic_fingerprint(material) != state.semantic_fingerprint(previous_state)
        controls.append('alternating-terminal-diagnostics-reconcile-render-report-cadence-601s')
        for status in ('pending', 'enqueued'):
            api[0] = {'status': status, 'details': {'uuid': row['evidence']['host_correlation'], 'expected_head_sha': head,
                'merge_method': 'merge', 'merge_action': 'direct_merge', 'bypass_rules': False}}
            conflicting = cm.authority_bridge_jobs(native, object(), record, [repeated])[0]
            assert conflicting['status'] == 'failed' and conflicting['result_verified']
            assert conflicting['provider_observation']['terminal_diagnostic']['status'] == status
            assert conflicting['provider_observation']['first_failure_sha256'] == first_digest
            repeated = conflicting
        api[0] = None
        unknown = cm.authority_bridge_jobs(native, object(), record, [repeated])[0]
        assert unknown['status'] == 'failed' and unknown['handle'] == failed['handle']
        assert unknown['provider_observation']['first_failure_sha256'] == first_digest
        forged = copy.deepcopy(unknown)
        forged['provider_observation']['first_failure_sha256'] = 'f' * 64
        rejected = cm.authority_bridge_jobs(native, object(), record, [forged])[0]
        assert rejected['status'] == 'observation-timeout'
    controls.append('GET-failed-clock-sticky-pending-enqueued-unavailable-forged-cache')

    try:
        cm._bridge_process_result(record, row, {**source_result(), 'command_sha256': 'f' * 64})
    except cm.MinorMalformed:
        pass
    else:
        raise AssertionError('Mismatching operation result was accepted')
    controls.append('operation-result-command-binding')

    assert len(controls) == 6


"""Permanent candidate for the actual completed-cache lifetime used by two native producer passes."""


def test_completed_provider_cache_survives_double_native_projection_without_mutation(monkeypatch):
    """Use the SAME retained completed object twice, matching snapshot then controller reconciliation."""
    import hmac

    state = run_plan.continuation_module()
    reporter = run_plan.reporting_module("status_report")
    fixture = json.loads((ROOT / "catalog/skills/workflow/implement-phase/references/status-snapshot.json").read_text(encoding="utf-8"))
    entry = {"page": {"kind": "maintenance-bootstrap-publication"}}
    entry["page"]["payload_sha256"] = cm._amendment_digest(entry["page"].get("payload", {}))
    receipt = cm._amendment_digest(entry)
    operation, head = "a" * 64, "b" * 40
    key = b"private-unit-cache-key"
    clock = ["2026-11-25T12:00:00+00:00"]
    native = SimpleNamespace(_secret=lambda **_kw: key, _now=lambda: clock[0])
    record = {"nonce": "private-unit-cache", "repo": "bendourthe/Nexus-Hub"}
    uuid = "630b9d5e-3f2a-4f7e-8b0c-2d5f9a8c1e42"
    row = {"operation": "green-merge", "operation_id": operation, "receipt_id": receipt,
        "command_sha256": "c" * 64, "state": "ambiguous", "at": clock[0], "target": {"head": head, "number": 314},
        "evidence": {"host_correlation": uuid, "host_observation": {"status": "pending"}}}
    api = [{"status": "failed", "details": {"message": "Private fixture host failure"}}]
    monkeypatch.setattr(cm, "authority_bridge_history", lambda *_args: [entry])
    monkeypatch.setattr(cm, "authority_bridge_operation_history", lambda *_args: {operation: row})
    monkeypatch.setattr(cm, "_bridge_api", lambda *_args: copy.deepcopy(api[0]))
    monkeypatch.setattr(cm, "_bridge_observe_effect", lambda *_args: None)
    def observe(jobs):
        conditions, resolutions = cm.authority_bridge_host_failures(native, object(), record, jobs)
        return {"objective": "Retain the exact terminal hosted result", "remaining_tasks": 16, "requests": [],
            "jobs": jobs, "external_conditions": conditions, "condition_resolutions": resolutions,
            "work": [], "completion": {"verified": False}}
    def snapshot(disposition):
        data = copy.deepcopy(fixture)
        data.update(observed_at=clock[0], running=[], decisions=[], continuation=disposition)
        return data
    first = cm.authority_bridge_jobs(native, object(), record, [])
    previous = {"observation": {"jobs": []}, "disposition": state.reconcile(observe(first))}
    assert not previous["disposition"]["jobs"] and previous["disposition"]["completed_jobs"][0]["status"] == "failed"
    report_receipt = reporter.select_report(snapshot(previous["disposition"]), None, "checkpoint")["receipt"]
    for index, status in enumerate(("pending", "enqueued", None, "pending", None)):
        clock[0] = "2026-11-25T12:%02d:01+00:00" % (20 + index)
        api[0] = None if status is None else {"status": status, "details": {"uuid": uuid, "expected_head_sha": head,
            "merge_method": "merge", "merge_action": "direct_merge", "bypass_rules": False}}
        before = copy.deepcopy(previous)
        # native_owner_observation uses retired jobs when the current observation has no active jobs.
        retained = previous["disposition"]["completed_jobs"]
        cm.authority_bridge_jobs(native, object(), record, retained)  # snapshot/native projection pass
        second = cm.authority_bridge_jobs(native, object(), record, retained)  # same previous object, controller pass
        current = state.reconcile(observe(second), previous["disposition"])
        assert previous == before, "Read-only native projection mutated the caller's authenticated completed cache"
        cached = retained[0]
        expected = hmac.new(key, b"v415-bridge-job-observation\0" + binding.canonical({"nonce": record["nonce"],
            "operation_id": operation, "handle": cached["handle"], "observation": cached["provider_observation"]}), hashlib.sha256).hexdigest()
        assert hmac.compare_digest(cached["provider_observation_hmac"], expected)
        assert second[0]["status"] == "failed" and current["state"] == "blocked_external" and not current["jobs"]
        assert [job["id"] for job in current["completed_jobs"]] == [first[0]["id"]]
        assert current["fingerprint"] == previous["disposition"]["fingerprint"]
        for event in ("checkpoint", "resume", "turn-end"):
            assert reporter.select_report(snapshot(current), report_receipt, event)["mode"] == "none"
        for mode in ("compact", "full"):
            assert reporter.render(snapshot(current), mode).startswith("Waiting for Hosting reported failure")
        previous = {"observation": {"jobs": []}, "disposition": current}


"""Candidate additions to the owned bridge test module; not executed or integrated."""


@pytest.mark.parametrize("mode", ["fast", "gated", "overflow"])
def test_codeql_artifact_real_private_child_capture_and_report_resume(tmp_path, monkeypatch, mode):
    """Actual private child/file/HMAC boundary; receipt/owner facts are unit seams, never real admission."""
    import io
    import zipfile
    from tests.fixtures.gh_stub.launcher import make_stub

    home = tmp_path / "private-child-home"
    home.mkdir()
    for name in ("HOME", "USERPROFILE", "APPDATA", "LOCALAPPDATA", "CODEX_HOME", "NEXUS_HUB_RUNS_DIR", "TEMP", "TMP", "TMPDIR"):
        monkeypatch.setenv(name, str(home / name))
        (home / name).mkdir()
    monkeypatch.setenv("PYTHONDONTWRITEBYTECODE", "1")
    monkeypatch.setenv("PYTHONNOUSERSITE", "1")
    monkeypatch.delenv("PYTHONPATH", raising=False)
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, "w") as archive:
        archive.writestr("private-fixture.txt", b"Bounded immutable private artifact")
    raw = stream.getvalue()
    artifact_bytes = tmp_path / "private-artifact.zip"
    artifact_bytes.write_bytes(raw)
    gate = tmp_path / "release-private-response"
    journal = tmp_path / "private-read-journal.jsonl"
    program = tmp_path / "private-gh.py"
    program.write_text(
        "import json,os,sys,time\nfrom pathlib import Path\n"
        "expected=['api','--hostname','github.com','--method','GET','repos/bendourthe/Nexus-Hub/actions/artifacts/10/zip','-H','Accept: application/vnd.github+json','-H','X-GitHub-Api-Version: 2026-03-10']\n"
        "assert sys.argv[1:]==expected\n"
        "with Path(os.environ['PRIVATE_READ_JOURNAL']).open('a',encoding='utf-8') as f:f.write(json.dumps({'pid':os.getpid(),'argv':sys.argv[1:]})+'\\n')\n"
        "mode=os.environ['PRIVATE_READ_MODE']\n"
        "if mode=='gated':\n"
        " start=time.monotonic()\n"
        " while not Path(os.environ['PRIVATE_READ_GATE']).exists() and time.monotonic()-start<4:time.sleep(0.01)\n"
        " if not Path(os.environ['PRIVATE_READ_GATE']).exists():sys.exit(3)\n"
        "value=(b'x'*(16*1024*1024+1)) if mode=='overflow' else Path(os.environ['PRIVATE_READ_BYTES']).read_bytes()\n"
        "sys.stdout.buffer.write(value)\nsys.stdout.buffer.flush()\n", encoding="utf-8")
    executable = make_stub(tmp_path / "private-tools", "gh", program)
    for name, value in {"PRIVATE_READ_MODE": mode, "PRIVATE_READ_JOURNAL": str(journal),
            "PRIVATE_READ_GATE": str(gate), "PRIVATE_READ_BYTES": str(artifact_bytes)}.items():
        monkeypatch.setenv(name, value)
    private_key = b"private-test-native-observation-key"
    monkeypatch.setattr(ck, "_secret", lambda **_kw: private_key)
    class PrivateRecord(dict):
        record_path = tmp_path / "private-unit-record.json"
    record = PrivateRecord(nonce="private-read-only", minor="v4.15", session_id="private-unit-owner", approvals={"classes": ["original-private-class"],
        "spend_caps": {"usd_total": 10, "spawn_total": 6}})
    record.record_path.write_text(json.dumps(record), encoding="utf-8")
    record_before = record.record_path.read_bytes()
    payload = {"head": "a" * 40, "actor": {}, "write_paths": [".github/workflows/codeql.yml"]}
    entry = {"page": {"kind": "maintenance-bootstrap-publication", "payload": payload,
        "payload_sha256": cm._amendment_digest(payload)}}
    receipt = cm._amendment_digest(entry)
    monkeypatch.setattr(cm, "authority_bridge_history", lambda *_args: [entry])
    monkeypatch.setattr(cm, "authority_bridge_operation_history", lambda *_args: {})
    monkeypatch.setattr(cm, "_bridge_publication_actor", lambda *_args: (object(), {}))
    monkeypatch.setattr(binding, "current_host_context", lambda *_args, **_kw: {})
    monkeypatch.setattr(binding, "full_access_authorization", lambda *_args: True)
    monkeypatch.setattr(ck, "_host_cwds", lambda *_args: [])
    monkeypatch.setattr(ck, "historical_host_cwds", lambda *_args: [])
    context = {"artifact_id": 10, "artifact_digest": "sha256:" + hashlib.sha256(raw).hexdigest(),
        "artifact_size": len(raw), "run_id": 100, "run_attempt": 1, "publication_receipt_sha256": receipt}
    identity = cm._amendment_digest({"purpose": "codeql-artifact-observation", "context": context, "nonce": record["nonce"]})
    command = [str(executable), "api", "--hostname", "github.com", "--method", "GET", "repos/bendourthe/Nexus-Hub/actions/artifacts/10/zip",
        "-H", "Accept: application/vnd.github+json", "-H", "X-GitHub-Api-Version: 2026-03-10"]
    ctx = SimpleNamespace(gh=str(executable), git="C:/not-dispatched-private-git.exe", root=tmp_path,
        budget=ck.Budget(0.15 if mode == "gated" else 5))
    state = run_plan.continuation_module()
    reporter = run_plan.reporting_module("status_report")
    fixture = json.loads((ROOT / "catalog/skills/workflow/implement-phase/references/status-snapshot.json").read_text(encoding="utf-8"))
    scope = SimpleNamespace(minor=True, label=record["minor"], repo_root=ctx.root)
    controller_frames = []
    def native_read_owner(_scope, _path, _record, previous=None, **_kw):
        prior = (previous or {}).get("disposition", {})
        jobs = prior.get("jobs", []) + prior.get("completed_jobs", [])
        return {"requests": [], "resolutions": [], **cm.authority_bridge_read_state(ck, ctx, record, jobs)}
    monkeypatch.setattr(run_plan, "native_owner_observation", native_read_owner)
    def reconcile(previous=None):
        prior_frame = {"disposition": previous} if previous else None
        frame = run_plan.reconcile_observation(scope, record.record_path, record,
            {"objective": "Private read-only artifact prerequisite", "remaining_tasks": 16,
                "requests": [], "completion": {"verified": False}},
            1, "INCOMPLETE: private fixture task remains", prior_frame, readonly=True)
        controller_frames.append(frame)
        return frame["disposition"]
    def snapshot(value):
        data = copy.deepcopy(fixture)
        data.update(continuation=value, running=[], decisions=[])
        return data
    try:
        result = run_plan.dispatch_authority_operation(ctx, record.record_path, identity, command,
            run_nonce=record["nonce"], artifact_read=context)
        sidecar = run_plan.codeql_observation_directory(record.record_path, record["nonce"]) / (identity + ".json")
        before = sidecar.read_bytes()
        assert result["purpose"] == "codeql-artifact-observation" and "operation_id" not in result
        if mode == "gated":
            assert result["exit_code"] is None and run_plan.observe_authority_process(result)["state"] == "running"
            waiting = reconcile()
            assert waiting["state"] == "waiting_job" and waiting["jobs"][0]["handle"] == result["handle"]
            for report_mode in ("compact", "full"):
                rendered = reporter.render(snapshot(waiting), report_mode)
                assert result["handle"] in rendered and "Resume when:" in rendered
            gate.write_bytes(b"release")
        else:
            waiting = None
        deadline = time.monotonic() + 6
        while run_plan.observe_authority_process(result)["state"] != "ended" and time.monotonic() < deadline:
            time.sleep(0.02)
        assert run_plan.observe_authority_process(result)["state"] == "ended"
        final = reconcile(waiting)
        if mode == "overflow":
            assert final["state"] == "blocked_external" and not final["work"]
            assert final["completed_jobs"][0]["result_kind"] == "process-ended-observed"
            # This verifies bounded ACCEPTANCE, not a file quota: the current capture is file-backed.
            assert Path(result["stdout_path"]).stat().st_size > 16 * 1024 * 1024
        else:
            assert final["state"] == "working" and not final["jobs"] and not final["external_conditions"]
            assert final["completed_jobs"][0]["result_kind"] == "codeql-artifact-bytes-observed"
            if mode == "gated":
                assert final["completed_jobs"][0]["exit_code"] is None
            for report_mode in ("compact", "full"):
                assert "State: working" in reporter.render(snapshot(final), report_mode)
        if mode == "gated":
            scope = SimpleNamespace(minor=True, label=record["minor"], repo_root=ctx.root)
            saved = copy.deepcopy(controller_frames[-1])
            assert saved["disposition"] == final
            run_plan.save_continuation(record.record_path, saved)
            loaded = run_plan.read_continuation(scope, record.record_path, record)
            assert loaded == saved and loaded["disposition"]["completed_jobs"][0]["exit_code"] is None
            stored = run_plan.continuation_path(record.record_path).read_bytes()
            monkeypatch.setattr(run_plan, "observe_authority_process", lambda _proof: {"state": "unavailable"})
            ctx.budget = ck.Budget(2)
            artifact = {"id": 10, "digest": context["artifact_digest"], "size_in_bytes": len(raw)}
            with monkeypatch.context() as missing_dependency:
                missing_dependency.setitem(sys.modules, "psutil", None)
                assert cm._bridge_codeql_artifact(ck, ctx, record, entry, artifact, 100, 1) == raw
            current = reconcile(loaded["disposition"])
            assert current["state"] == "working" and not current["jobs"]
            assert current["completed_jobs"][0]["exit_code"] is None
            assert run_plan.continuation_path(record.record_path).read_bytes() == stored
            assert sidecar.read_bytes() == before
            for report_mode in ("compact", "full"):
                assert "State: working" in reporter.render(snapshot(current), report_mode)
            tampered = copy.deepcopy(saved)
            tampered["disposition"]["completed_jobs"][0]["read_observation"]["observed_at"] = "forged"
            run_plan.save_continuation(record.record_path, tampered)
            with pytest.raises(cm.ObservationUnavailable, match="response-pending"):
                cm._bridge_codeql_artifact(ck, ctx, record, entry, artifact, 100, 1)
            run_plan.save_continuation(record.record_path, saved)
        ctx.budget = ck.Budget(2)
        repeated = run_plan.dispatch_authority_operation(ctx, record.record_path, identity, command,
            run_nonce=record["nonce"], artifact_read=context)
        assert repeated["handle"] == result["handle"] and sidecar.read_bytes() == before
        assert len(journal.read_text(encoding="utf-8").splitlines()) == 1
        assert record.record_path.read_bytes() == record_before
        assert not (record.record_path.parent / "publication-jobs").exists()
    finally:
        gate.write_bytes(b"release")


"""Permanent test candidates for the reviewed hosted metadata/cache boundaries."""


@pytest.mark.parametrize("language", ["python", "javascript-typescript"])
def test_codeql_hosted_exact_workflow_metadata_ids(tmp_path, monkeypatch, language):
    """Execute the actual fixed producer fragment; synthetic scanner/API facts stay unit seams."""
    import textwrap

    workflow = (ROOT / ".github/workflows/codeql.yml").read_bytes()
    source_text = workflow.decode("utf-8").replace("\r\n", "\n")
    step = source_text.split("- name: Retain hosted CodeQL observations", 1)[1]
    fragment = textwrap.dedent(step.split("python -B - <<'PY'\n", 1)[1].split("\n          PY", 1)[0])
    paths = sorted(cm._BRIDGE_CODEQL_FILES)
    files = {path: hashlib.sha256(workflow if path == ".github/workflows/codeql.yml" else path.encode()).hexdigest() for path in paths}
    expected = {"head": "a" * 40, "base": "b" * 40, "preview_sha": "c" * 40, "tree": "d" * 40,
        "source_files": files, "run_id": 100, "run_attempt": 1, "pr_number": 314}
    invocation = "e" * 32
    source = {"head": expected["preview_sha"], "tree": expected["tree"], "parents": [expected["base"], expected["head"]],
        "worktree_dirty": False, "files": [{"path": path, "sha256": value} for path, value in files.items()],
        "analysis": {"schema": "codeql-worktree/1", "sha256": "f" * 64, "files": 42, "clean": True}}
    prefix = "security/codeql-" + language
    stem = prefix + "." + invocation
    category = "/language:" + language
    version = "2.23.0"
    pack = "codeql/python-queries" if language == "python" else "codeql/javascript-queries"
    members = {stem + ".sarif": json.dumps({"version": "2.1.0", "runs": [{"tool": {"driver": {"name": "CodeQL"}},
        "automationDetails": {"id": category}, "results": []}]}).encode(), stem + ".version.json": json.dumps({"version": version}).encode(),
        stem + ".packs.txt": (pack + "@1.5.0: /private/qlpack.yml\n").encode()}
    members.update({"summary.json": b"{}", "summary.md": b"Synthetic report", "metadata/environment.json": b"{}", "junit/native.xml": b"<testsuite/>"})
    manifest = {"schema": "ci-audit-invocation/1", "scope": "codeql-" + language, "invocation_id": invocation,
        "source": source, "source_sha256": cm._amendment_digest(source), "config_sha256": files["scripts/ci/codeql-config.yml"],
        "language": language, "category": category, "status": "complete", "output_valid": True, "scanner_exit_code": 0,
        "analysis_after": copy.deepcopy(source["analysis"]), "tool": {"name": "CodeQL", "version": version,
            "bundle": {"version": version, "executable_sha256": "1" * 64}, "query_packs": [{"name": pack, "version": "1.5.0",
                "content_sha256": "2" * 64, "metadata_sha256": "3" * 64}]},
        "outputs": [{"role": role, "path": stem + suffix, "sha256": hashlib.sha256(members[stem + suffix]).hexdigest(),
            "bytes": len(members[stem + suffix])} for role, suffix in (("primary", ".sarif"), ("version", ".version.json"), ("packs", ".packs.txt"))]}
    current = copy.deepcopy(manifest)
    current.update(status="running", output_valid=False, outputs=[], scanner_exit_code=None, tool={"name": "CodeQL", "version": "Unavailable (not observed)"})
    members[prefix + ".current.json"] = json.dumps(current).encode()
    members[prefix + ".manifest.json"] = json.dumps(manifest).encode()
    (tmp_path / ".github/workflows").mkdir(parents=True)
    (tmp_path / ".github/workflows/codeql.yml").write_bytes(workflow)
    (tmp_path / "reports/security").mkdir(parents=True)
    (tmp_path / "reports" / (prefix + ".manifest.json")).write_bytes(members[prefix + ".manifest.json"])
    env = {"AUDIT_LANGUAGE": language, "MANIFEST_SHA256": hashlib.sha256(members[prefix + ".manifest.json"]).hexdigest(),
        "INVOCATION_ID": invocation, "GITHUB_RUN_ID": "100", "GITHUB_RUN_ATTEMPT": "1", "PR_NUMBER": "314",
        "PR_HEAD": expected["head"], "PR_BASE": expected["base"], "JOB_DISPLAY_NAME": "Analyze (" + language + ")",
        "CODEQL_PATH": "/private/codeql/codeql", "CODEQL_VERSION": version, "SARIF_ID": "private-upload",
        "SARIF_IDS": '{"code-scanning":"private-upload"}'}
    for name, value in env.items():
        monkeypatch.setenv(name, value)
    monkeypatch.chdir(tmp_path)
    exec(compile(fragment, str(ROOT / ".github/workflows/codeql.yml") + ":Retain-hosted-fragment", "exec"), {})
    hosted_path = "hosted/codeql-" + language + ".json"
    members[hosted_path] = (tmp_path / "reports" / hosted_path).read_bytes()
    hosted = json.loads(members[hosted_path])
    assert all(type(hosted["github"][name]) is str for name in ("run_id", "run_attempt", "pr_number"))
    def api(_ck, _ctx, _record, suffix):
        if suffix == "/code-scanning/sarifs/private-upload":
            return {"processing_status": "complete"}
        assert suffix == "/code-scanning/analyses?sarif_id=private-upload&per_page=100"
        return [{"sarif_id": "private-upload", "commit_sha": expected["preview_sha"], "ref": "refs/pull/314/merge",
            "category": category, "error": "", "tool": {"name": "CodeQL", "version": version}}]
    monkeypatch.setattr(cm, "_bridge_api", api)
    assert cm._bridge_codeql_language_evidence(ck, object(), {}, members, language, expected)["language"] == language
    for name in ("run_id", "run_attempt", "pr_number"):
        for invalid in (True, float(expected[name]), "0" + str(expected[name]), "+" + str(expected[name]),
                " " + str(expected[name]), str(expected[name]) + " ", "1e2", "0", "-1"):
            changed = copy.deepcopy(hosted)
            changed["github"][name] = invalid
            members[hosted_path] = json.dumps(changed).encode()
            with pytest.raises(cm.MinorMalformed, match="hosted-run-binding"):
                cm._bridge_codeql_language_evidence(ck, object(), {}, members, language, expected)
    for name in ("run_id", "run_attempt", "pr_number"):
        hosted["github"][name] = expected[name]
    members[hosted_path] = json.dumps(hosted).encode()
    assert cm._bridge_codeql_language_evidence(ck, object(), {}, members, language, expected)["language"] == language


def test_codeql_read_terminal_cache_shared_previous_and_record_scope(tmp_path, monkeypatch):
    """Real HMAC/files, shared reconciliation/reports; lifecycle/history/owner are explicit unit seams."""
    import hmac
    import io
    import zipfile

    private_key = b"private-terminal-observation-unit-key"
    clock = ["2026-11-25T12:00:00+00:00"]
    lifecycle = ["ended"]
    monkeypatch.setattr(ck, "_secret", lambda **_kw: private_key)
    monkeypatch.setattr(ck, "_now", lambda: clock[0])
    monkeypatch.setattr(ck, "_runs_dir", lambda: tmp_path)
    monkeypatch.setattr(ck, "_host_cwds", lambda *_a: [])
    monkeypatch.setattr(ck, "historical_host_cwds", lambda *_a: [])
    monkeypatch.setattr(binding, "current_host_context", lambda *_a, **_kw: {})
    monkeypatch.setattr(binding, "full_access_authorization", lambda *_a: True)
    monkeypatch.setattr(cm, "_bridge_publication_actor", lambda *_a: (object(), {}))
    monkeypatch.setattr(cm, "authority_bridge_operation_history", lambda *_a: {})
    monkeypatch.setattr(run_plan, "observe_authority_process", lambda _frame: {"state": lifecycle[0]})
    payload = {"head": "a" * 40, "actor": {}, "write_paths": [".github/workflows/codeql.yml"]}
    entry = {"page": {"kind": "maintenance-bootstrap-publication", "payload": payload, "payload_sha256": cm._amendment_digest(payload)}}
    receipt_id = cm._amendment_digest(entry)
    monkeypatch.setattr(cm, "authority_bridge_history", lambda *_a: [entry])
    class PrivateRecord(dict):
        pass
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, "w") as zipped:
        zipped.writestr("private-proof.txt", b"Complete immutable unit artifact")
    raw = stream.getvalue()
    ctx = SimpleNamespace(gh="C:/private-unit-gh.exe")
    records, captures = [], []
    for index in (1, 2):
        record = PrivateRecord(nonce="private-run-" + str(index), approvals={"classes": ["original"], "spend_caps": {"usd_total": 10, "spawn_total": 6}})
        record.record_path = tmp_path / ("private-record-" + str(index) + ".json")
        record.record_path.write_text(json.dumps(record), encoding="utf-8")
        context = {"artifact_id": 10, "artifact_digest": "sha256:" + hashlib.sha256(raw).hexdigest(), "artifact_size": len(raw),
            "run_id": 100, "run_attempt": 1, "publication_receipt_sha256": receipt_id}
        identity = cm._amendment_digest({"purpose": "codeql-artifact-observation", "context": context, "nonce": record["nonce"]})
        directory = run_plan.codeql_observation_directory(record.record_path, record["nonce"])
        directory.mkdir(parents=True)
        stdout = directory / (identity + ".private.stdout")
        stdout.write_bytes(raw)
        info = stdout.stat()
        command = [ctx.gh, "api", "--hostname", "github.com", "--method", "GET", "repos/bendourthe/Nexus-Hub/actions/artifacts/10/zip",
            "-H", "Accept: application/vnd.github+json", "-H", "X-GitHub-Api-Version: 2026-03-10"]
        frame = {"purpose": "codeql-artifact-observation", "observation_id": identity, "read_context": context, "run_nonce": record["nonce"],
            "command_sha256": hashlib.sha256(binding.canonical(command)).hexdigest(), "stdout_path": str(stdout),
            "stdout_identity": {"device": info.st_dev, "inode": info.st_ino}, "exit_code": None, "status": "observation-timeout",
            "handle": "process:" + str(index) + ":1.000000", "process": {"pid": index, "created_at": 1.0},
            "job_created_at": 1.0, "observed_at": clock[0]}
        frame["observation_hmac"] = hmac.new(private_key, b"v415-codeql-artifact-observation\0" + binding.canonical(frame), hashlib.sha256).hexdigest()
        sidecar = directory / (identity + ".json")
        sidecar.write_bytes(binding.canonical(frame))
        records.append(record)
        captures.append((sidecar, sidecar.read_bytes(), stdout, frame))
    assert captures[0][0].parent != captures[1][0].parent
    state, reporter = run_plan.continuation_module(), run_plan.reporting_module("status_report")
    fixture = json.loads((ROOT / "catalog/skills/workflow/implement-phase/references/status-snapshot.json").read_text(encoding="utf-8"))
    def project(record, previous=None):
        jobs = (previous or {}).get("jobs", []) + (previous or {}).get("completed_jobs", [])
        return cm.authority_bridge_read_state(ck, ctx, record, jobs)
    def reconcile(observed, previous=None):
        return state.reconcile({"objective": "Private hosted read prerequisite", "remaining_tasks": 16, "requests": [],
            "completion": {"verified": False}, **observed}, previous)
    def snapshot(value):
        data = copy.deepcopy(fixture)
        data.update(observed_at=clock[0], continuation=value, running=[], decisions=[])
        return data
    previous = reconcile(project(records[0]))
    assert previous["state"] == "working" and previous["completed_jobs"][0]["exit_code"] is None
    assert previous["completed_jobs"][0]["result_kind"] == "codeql-artifact-bytes-observed"
    immutable_previous = copy.deepcopy(previous)
    report_receipt = reporter.select_report(snapshot(previous), None, "checkpoint")["receipt"]
    for index, mode in enumerate(("unavailable", "running", "unavailable", "ended"), 1):
        clock[0] = "2026-11-25T12:" + str(10 + index).zfill(2) + ":01+00:00"
        lifecycle[0] = mode
        first = project(records[0], previous)
        second = project(records[0], previous)
        assert previous == immutable_previous
        for observed in (first, second):
            current = reconcile(observed, previous)
            assert not current["jobs"] and current["completed_jobs"][0]["id"] == previous["completed_jobs"][0]["id"]
            assert current["completed_jobs"][0]["exit_code"] is None and current["fingerprint"] == previous["fingerprint"]
            for event in ("checkpoint", "resume", "turn-end"):
                assert reporter.select_report(snapshot(current), report_receipt, event)["mode"] == "none"
    other = reconcile(project(records[1]))
    assert other["completed_jobs"][0]["id"] != previous["completed_jobs"][0]["id"]
    lifecycle[0] = "unavailable"
    captures[0][2].write_bytes(b"x" * len(raw))
    changed = reconcile(project(records[0], previous), previous)
    assert changed["state"] == "blocked_external" and not changed["jobs"] and not changed["work"]
    assert changed["completed_jobs"][0]["exit_code"] is None
    assert previous == immutable_previous
    forged = copy.deepcopy(previous)
    forged["completed_jobs"][0]["read_observation"]["observed_at"] = clock[0]
    with pytest.raises(cm.ObservationUnavailable, match="terminal-observation-unverified"):
        project(records[0], forged)
    foreign = copy.deepcopy(captures[1][3])
    captures[0][0].write_bytes(binding.canonical(foreign))
    with pytest.raises(cm.ObservationUnavailable):
        project(records[0], previous)
    captures[0][0].write_bytes(captures[0][1])
    assert captures[1][0].read_bytes() == captures[1][1]
    assert all(json.loads(record.record_path.read_bytes()) == record for record in records)


"""Permanent untrusted descriptive-cache regression candidate."""


@pytest.mark.parametrize("disposition", [None, {"completed_jobs": [None]}, {"completed_jobs": None},
    {"completed_jobs": {}}, {"completed_jobs": ["not a job"]}])
def test_codeql_consumer_refuses_malformed_bound_terminal_cache(tmp_path, monkeypatch, disposition):
    """Actual saved-frame reader, synthetic transport receipt; malformed data cannot become proof."""
    class PrivateRecord(dict):
        record_path = tmp_path / "private-malformed-record.json"
    record = PrivateRecord(nonce="private-cache-run", session_id="private-cache-owner", minor="v4.15")
    record.record_path.write_text(json.dumps(record), encoding="utf-8")
    entry = {"page": {"kind": "maintenance-bootstrap-publication", "payload": {"write_paths": [".github/workflows/codeql.yml"]}}}
    context = {"artifact_id": 10, "artifact_digest": "sha256:" + "a" * 64, "artifact_size": 100,
        "run_id": 100, "run_attempt": 1, "publication_receipt_sha256": cm._amendment_digest(entry)}
    identity = cm._amendment_digest({"purpose": "codeql-artifact-observation", "context": context, "nonce": record["nonce"]})
    ctx = SimpleNamespace(root=tmp_path, gh="C:/private-unit-gh.exe")
    command = [ctx.gh, "api", "--hostname", "github.com", "--method", "GET", "repos/bendourthe/Nexus-Hub/actions/artifacts/10/zip",
        "-H", "Accept: application/vnd.github+json", "-H", "X-GitHub-Api-Version: 2026-03-10"]
    result = {"purpose": "codeql-artifact-observation", "observation_id": identity, "read_context": context,
        "run_nonce": record["nonce"], "command_sha256": hashlib.sha256(binding.canonical(command)).hexdigest(),
        "exit_code": None, "handle": "process:123:1.000000", "process": {"pid": 123, "created_at": 1.0}}
    monkeypatch.setattr(run_plan, "dispatch_authority_operation", lambda *_a, **_kw: copy.deepcopy(result))
    monkeypatch.setattr(run_plan, "observe_authority_process", lambda *_a: {"state": "unavailable"})
    scope = SimpleNamespace(minor=True, label="v4.15", repo_root=tmp_path)
    frame = {"contract": "implementation-continuation-v1", "binding": run_plan.continuation_binding(scope, record.record_path, record),
        "disposition": disposition}
    run_plan.save_continuation(record.record_path, frame)
    before = run_plan.continuation_path(record.record_path).read_bytes()
    with pytest.raises(cm.ObservationUnavailable, match="response-pending"):
        cm._bridge_codeql_artifact(ck, ctx, record, entry,
            {"id": 10, "digest": context["artifact_digest"], "size_in_bytes": 100}, 100, 1)
    assert run_plan.continuation_path(record.record_path).read_bytes() == before


"""One genuine private native coupling candidate; not executed or integrated."""


def test_private_codex_codeql_receipt_controller_saved_read_consumer(bridge_case, monkeypatch):
    """Real private native capture/record/authority; only hosting and later process observation are simulated."""
    import io
    import zipfile
    from .test_v415_authority_bridge_operations import PrivateHost, native_job_frame, native_snapshot_reports

    fx, log = bridge_case
    original = copy.deepcopy(fx.record())
    resume(fx, log)
    host = PrivateHost(fx, monkeypatch)
    actor, payload = host.actor()
    workflow = ".github/workflows/codeql.yml"
    target = actor / workflow
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes((ROOT / workflow).read_bytes())
    host.git(actor, "add", "--", workflow)
    host.git(actor, "commit", "-q", "-m", "private hosted read prerequisite")
    payload.update(head=host.git(actor, "rev-parse", "HEAD"), write_paths=sorted([*payload["write_paths"], workflow]))
    host.load()
    host.state.update(head=payload["head"], tree=host.git(actor, "rev-parse", "HEAD^{tree}"))
    host.save()
    entry = capture_supplement(fx, log, "maintenance-bootstrap-publication", payload)
    receipt_id = cm._amendment_digest(entry)
    ctx, record = ck.resolve_minor_controller(fx.record_path(), CODEX_SESSION, minor_protocol=1, execution_protocol=1)
    args = argparse.Namespace(minor="v4.15", repo=str(fx.work), plan=None, member="v4.15.6", session=CODEX_SESSION,
        approval_class=cm.AUTHORITY_BRIDGE_ACTION, request=json.dumps({"receipt_id": receipt_id, "operation": "green-merge"}))
    probe = ck.authorization_probe(args)
    assert not isinstance(probe, int) and probe[2]["permission_verified"] is True
    assert probe[2]["effect_observed"] is False and probe[2]["counters_consumed"] is False
    baseline = fx.record_path().read_bytes()
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, "w") as archive:
        archive.writestr("private-native-proof.txt", b"Private complete artifact bytes; not hosted CodeQL qualification")
    raw = stream.getvalue()
    artifact_file = fx.tmp / "private-native-artifact.zip"
    artifact_file.write_bytes(raw)
    gate = fx.tmp / "release-native-artifact"
    journal = fx.tmp / "native-artifact-get.jsonl"
    program = fx.tmp / "authority-tools/host.py"
    original_program = program.read_bytes()
    original_gh, original_path = ctx.gh, fx.env["PATH"]
    prefix = (
        'import json,os,sys,time\n'
        'from pathlib import Path\n'
        "expected=['api','--hostname','github.com','--method','GET','repos/bendourthe/Nexus-Hub/actions/artifacts/10/zip','-H','Accept: application/vnd.github+json','-H','X-GitHub-Api-Version: 2026-03-10']\n"
        'if sys.argv[1:]==expected:\n'
        "    with Path(os.environ['PRIVATE_NATIVE_JOURNAL']).open('a',encoding='utf-8') as f:f.write(json.dumps({'pid':os.getpid(),'argv':sys.argv[1:]})+'\\n')\n"
        '    start=time.monotonic()\n'
        "    while not Path(os.environ['PRIVATE_NATIVE_GATE']).exists() and time.monotonic()-start<300:time.sleep(0.01)\n"
        "    if not Path(os.environ['PRIVATE_NATIVE_GATE']).exists():sys.exit(3)\n"
        "    sys.stdout.buffer.write(Path(os.environ['PRIVATE_NATIVE_BYTES']).read_bytes());sys.stdout.buffer.flush()\n"
        '    raise SystemExit(0)\n'
    )
    compile(prefix + original_program.decode("utf-8"), str(program), "exec")
    program.write_bytes(prefix.encode("utf-8") + original_program)
    assert program.read_bytes().endswith(original_program)
    environment = {"PRIVATE_NATIVE_BYTES": str(artifact_file),
        "PRIVATE_NATIVE_GATE": str(gate), "PRIVATE_NATIVE_JOURNAL": str(journal)}
    fx.env.update(environment)
    for key, value in environment.items():
        monkeypatch.setenv(key, value)
    assert fx.env["PATH"] == original_path
    ctx, record = ck.resolve_minor_controller(fx.record_path(), CODEX_SESSION, minor_protocol=1, execution_protocol=1)
    assert ctx.gh == original_gh
    assert ctx.root != actor and cm.authority_bridge_history(ck, ctx, record)[-1] == entry
    artifact = {"id": 10, "digest": "sha256:" + hashlib.sha256(raw).hexdigest(), "size_in_bytes": len(raw)}
    context = {"artifact_id": 10, "artifact_digest": artifact["digest"], "artifact_size": len(raw),
        "run_id": 100, "run_attempt": 1, "publication_receipt_sha256": receipt_id}
    identity = cm._amendment_digest({"purpose": "codeql-artifact-observation", "context": context, "nonce": record["nonce"]})
    command = [ctx.gh, "api", "--hostname", "github.com", "--method", "GET", "repos/bendourthe/Nexus-Hub/actions/artifacts/10/zip",
        "-H", "Accept: application/vnd.github+json", "-H", "X-GitHub-Api-Version: 2026-03-10"]
    checked = fx.run("check-minor", "v4.15", "--session", CODEX_SESSION)
    assert checked.returncode == 1, checked.stdout + checked.stderr
    dispatch_record_path = fx.record_path()
    original_budget = ctx.budget
    try:
        ctx.budget = ck.Budget(0.15)
        captured = run_plan.dispatch_authority_operation(ctx, dispatch_record_path, identity, command,
            run_nonce=record["nonce"], artifact_read=context)
        ctx.budget = original_budget
        assert captured["exit_code"] is None and run_plan.observe_authority_process(captured)["state"] == "running"
        pending = native_job_frame(fx, checked)
        assert pending["disposition"]["state"] == "waiting_job"
        job = next(row for row in pending["disposition"]["jobs"] if row["id"] == "bridge:codeql-read:" + identity)
        assert job["handle"] == captured["handle"] and job["native_bridge"] == {"receipt_id": receipt_id, "observation_id": identity}
        fixture = json.loads((ROOT / "catalog/skills/workflow/implement-phase/references/status-snapshot.json").read_text(encoding="utf-8"))
        fixture.update(continuation=pending["disposition"], running=[], decisions=[])
        reporter = run_plan.reporting_module("status_report")
        for mode in ("compact", "full"):
            assert captured["handle"] in reporter.render(fixture, mode)
        gate.write_bytes(b"release")
        deadline = time.monotonic() + 6
        while run_plan.observe_authority_process(captured)["state"] != "ended" and time.monotonic() < deadline:
            time.sleep(0.02)
        assert run_plan.observe_authority_process(captured)["state"] == "ended"
        final = native_job_frame(fx, checked, pending)
        scope = argparse.Namespace(minor=True, label="v4.15", repo_root=fx.work, observer_session=CODEX_SESSION)
        loaded = run_plan.read_continuation(scope, fx.record_path(), record)
        assert loaded == final and final["disposition"]["state"] == "working"
        terminal = next(row for row in loaded["disposition"]["completed_jobs"] if row["id"] == job["id"])
        assert terminal["exit_code"] is None and terminal["result_kind"] == "codeql-artifact-bytes-observed"
        assert cm._bridge_codeql_terminal_valid(ck._secret(create=False), record, receipt_id, identity, captured, terminal)
        saved_bytes = run_plan.continuation_path(fx.record_path()).read_bytes()
        # A later real controller invocation gets its normal fresh observation budget.
        ctx, record = ck.resolve_minor_controller(fx.record_path(), CODEX_SESSION, minor_protocol=1, execution_protocol=1)
        assert fx.record_path().read_bytes() == baseline
        monkeypatch.setattr(run_plan, "observe_authority_process", lambda _proof: {"state": "unavailable"})
        assert cm._bridge_codeql_artifact(ck, ctx, record, entry, artifact, 100, 1) == raw
        assert run_plan.continuation_path(fx.record_path()).read_bytes() == saved_bytes
        resumed = native_job_frame(fx, checked, loaded)
        assert resumed["disposition"]["state"] == "working" and not resumed["disposition"]["jobs"]
        data, reports = native_snapshot_reports(fx)
        assert data["continuation"]["state"] == "working" and data["continuation"]["directive"] == "continue"
        assert all("State: working" in rendered for rendered in reports.values())
        assert len(journal.read_text(encoding="utf-8").splitlines()) == 1
        assert fx.record_path().read_bytes() == baseline
        unchanged = fx.record()
        assert unchanged["approvals"]["classes"] == original["approvals"]["classes"]
        assert unchanged["approvals"]["spend_caps"] == original["approvals"]["spend_caps"]
        assert not unchanged.get("v415_publication_operations")
    finally:
        gate.write_bytes(b"release")


"""Permanent runtime prerequisite regressions; authority facts below are explicit unit seams."""


@pytest.mark.parametrize("code", [0, 7, None])
def test_process_observer_retains_exit_and_handle_without_psutil(monkeypatch, code):
    proof = {"handle": "process:123:1.000000", "process": {"pid": 123, "created_at": 1.0}, "exit_code": code}
    before = copy.deepcopy(proof)
    monkeypatch.setitem(sys.modules, "psutil", None)
    result = run_plan.observe_authority_process(proof)
    assert result["handle"] == proof["handle"] and proof == before
    if code is None:
        assert result["state"] == "unavailable" and "psutil" in result["reason"]
    else:
        assert result["state"] == "ended" and "retained exit code" in result["reason"]
    invalid = dict(proof, handle="process:foreign")
    assert run_plan.observe_authority_process(invalid)["state"] == "unavailable"


def test_new_host_dispatch_refuses_missing_psutil_before_files_or_process(tmp_path, monkeypatch):
    monkeypatch.setitem(sys.modules, "psutil", None)
    def forbidden(*_args, **_kwargs):
        raise AssertionError("Missing prerequisite reached capture creation or dispatch")
    monkeypatch.setattr(run_plan.subprocess, "Popen", forbidden)
    monkeypatch.setattr(ck, "_restrict", forbidden)
    record = tmp_path / "private-unit-record.json"
    record.write_bytes(b"unchanged private fixture")
    ctx = SimpleNamespace(root=tmp_path, gh="C:/private-gh.exe", git="C:/private-git.exe", budget=ck.Budget(5))
    with pytest.raises(run_plan.RunnerError, match="native-process-observation-unavailable: psutil"):
        run_plan.dispatch_authority_operation(ctx, record, "a" * 64, [ctx.gh, "private-unit"], run_nonce="private-unit")
    assert not (tmp_path / "publication-jobs").exists()
    assert record.read_bytes() == b"unchanged private fixture"


def test_cached_artifact_read_needs_no_psutil_budget_or_write(tmp_path, monkeypatch):
    import hmac
    key = b"private-cached-observation-unit-key"
    monkeypatch.setattr(ck, "_secret", lambda **_kw: key)
    context = {"artifact_id": 10, "artifact_digest": "sha256:" + "b" * 64, "artifact_size": 100,
        "run_id": 100, "run_attempt": 1, "publication_receipt_sha256": "c" * 64}
    nonce = "private-read-run"
    identity = cm._amendment_digest({"purpose": "codeql-artifact-observation", "context": context, "nonce": nonce})
    record = tmp_path / "private-read-record.json"
    ctx = SimpleNamespace(root=tmp_path, gh="C:/private-gh.exe", git="C:/private-git.exe", budget=ck.Budget(0))
    command = [ctx.gh, "api", "--hostname", "github.com", "--method", "GET", "repos/bendourthe/Nexus-Hub/actions/artifacts/10/zip",
        "-H", "Accept: application/vnd.github+json", "-H", "X-GitHub-Api-Version: 2026-03-10"]
    retained = {"purpose": "codeql-artifact-observation", "observation_id": identity, "read_context": context,
        "run_nonce": nonce, "command_sha256": hashlib.sha256(binding.canonical(command)).hexdigest(),
        "handle": "process:123:1.000000", "process": {"pid": 123, "created_at": 1.0}, "exit_code": None}
    retained["observation_hmac"] = hmac.new(key, b"v415-codeql-artifact-observation\0" + binding.canonical(retained), hashlib.sha256).hexdigest()
    directory = run_plan.codeql_observation_directory(record, nonce)
    directory.mkdir(parents=True)
    path = directory / (identity + ".json")
    path.write_bytes(binding.canonical(retained))
    before = path.read_bytes()
    def forbidden(*_args, **_kwargs):
        raise AssertionError("Retained read attempted an environment or capture write")
    monkeypatch.setitem(sys.modules, "psutil", None)
    monkeypatch.setattr(ck, "_restrict", forbidden)
    monkeypatch.setattr(run_plan.subprocess, "Popen", forbidden)
    result = run_plan.dispatch_authority_operation(ctx, record, identity, command, run_nonce=nonce, artifact_read=context)
    assert result["handle"] == retained["handle"] and result["exit_code"] is None
    assert path.read_bytes() == before and sorted(directory.iterdir()) == [path]


def test_missing_process_prerequisite_stops_after_authorization_before_reservation(tmp_path, monkeypatch):
    events = []
    entry = {"page": {"kind": ".6-repo-description", "payload": {"expected": "Before", "value": "After"}}}
    entry["page"]["payload_sha256"] = cm._amendment_digest(entry["page"]["payload"])
    record = {"nonce": "private-order", "approvals": {"classes": ["original"], "spend_caps": {"usd_total": 10, "spawn_total": 6}}}
    before = copy.deepcopy(record)
    ctx = SimpleNamespace(root=tmp_path)
    monkeypatch.setattr(cm, "repo_context", lambda *_a: ctx)
    monkeypatch.setattr(cm, "_record_for_add_class", lambda *_a: record)
    monkeypatch.setattr(binding, "current_host_context", lambda *_a, **_kw: {})
    monkeypatch.setattr(ck, "_runs_dir", lambda: tmp_path)
    monkeypatch.setattr(ck, "_host_cwds", lambda *_a: [])
    monkeypatch.setattr(ck, "historical_host_cwds", lambda *_a: [])
    def authorize(*_args):
        events.append("native-authorization")
        return {"execution_authorized": True}
    monkeypatch.setattr(cm, "authority_bridge_authorization", authorize)
    monkeypatch.setattr(cm, "authority_bridge_history", lambda *_a: [entry])
    monkeypatch.setattr(cm, "authority_bridge_operation_history", lambda *_a: {})
    def forbidden(*_args, **_kwargs):
        raise AssertionError("Missing prerequisite reached target or reservation")
    monkeypatch.setattr(cm, "_bridge_effect_target", forbidden)
    monkeypatch.setattr(cm, "_bridge_save_operation", forbidden)
    reasons = []
    monkeypatch.setattr(ck, "_blocked", lambda reason: reasons.append(reason) or 3)
    monkeypatch.setitem(sys.modules, "psutil", None)
    args = SimpleNamespace(minor="v4.15", session="private-owner", receipt=cm._amendment_digest(entry), operation="repo-description")
    assert cm.cmd_execute_v415_authority.__wrapped__(ck, args) == 3
    assert events == ["native-authorization"] and "psutil" in reasons[0]
    assert record == before
    # A consumed finite operation must remain readable without another dispatch prerequisite.
    identity = cm._bridge_operation_id(entry, args.operation)
    monkeypatch.setattr(cm, "authority_bridge_operation_history", lambda *_a: {identity: {"state": "completed"}})
    assert cm.cmd_execute_v415_authority.__wrapped__(ck, args) == 0
    assert record == before


def test_missing_runtime_native_condition_is_concrete_stable_and_resolves(tmp_path, monkeypatch):
    import psutil as available_psutil
    entry = {"page": {"kind": ".6-repo-description", "payload": {"expected": "Before", "value": "After"}, "member": "v4.15.6"}}
    entry["page"]["payload_sha256"] = cm._amendment_digest(entry["page"]["payload"])
    record = {"nonce": "private-runtime-fact", "session_id": "private-owner"}
    record_path = tmp_path / "private-runtime-record.json"
    record_path.write_text(json.dumps(record), encoding="utf-8")
    before = record_path.read_bytes()
    monkeypatch.setattr(cm, "authority_bridge_history", lambda *_a: [entry])
    monkeypatch.setattr(cm, "authority_bridge_operation_history", lambda *_a: {})
    clock = ["2026-11-25T12:00:00+00:00"]
    monkeypatch.setattr(ck, "_now", lambda: clock[0])
    monkeypatch.setitem(sys.modules, "psutil", None)
    scope = SimpleNamespace(minor=True, label="v4.15", repo_root=tmp_path)
    def native(_scope, _path, _record, previous=None, **_kw):
        prior_conditions = (previous or {}).get("disposition", {}).get("external_conditions", [])
        conditions, resolutions = cm.authority_bridge_host_failures(ck, object(), record, [], prior_conditions)
        return {"requests": [], "resolutions": [], "jobs": [], "external_conditions": conditions, "condition_resolutions": resolutions}
    monkeypatch.setattr(run_plan, "native_owner_observation", native)
    identity = "bridge:runtime:" + cm._bridge_operation_id(entry, "repo-description")
    facts = {"objective": "Private native unit prerequisite", "remaining_tasks": 1, "requests": [],
        "condition_resolutions": [{"condition_id": identity, "verified": True}]}
    first = run_plan.reconcile_observation(scope, record_path, record, facts, 1, "INCOMPLETE: private task", readonly=True)
    assert first["disposition"]["state"] == "blocked_external"
    assert first["disposition"]["external_conditions"][0]["id"] == identity
    reporter = run_plan.reporting_module("status_report")
    fixture = json.loads((ROOT / "catalog/skills/workflow/implement-phase/references/status-snapshot.json").read_text(encoding="utf-8"))
    def snapshot(frame):
        value = copy.deepcopy(fixture)
        value.update(observed_at=clock[0], continuation=frame["disposition"], running=[], decisions=[])
        return value
    reported = reporter.select_report(snapshot(first), None, "checkpoint")["receipt"]
    for mode in ("compact", "full"):
        text = reporter.render(snapshot(first), mode)
        assert "psutil" in text and "qualified native Python runtime" in text
    clock[0] = "2026-11-25T12:10:01+00:00"
    second = run_plan.reconcile_observation(scope, record_path, record, facts, 1, "INCOMPLETE: private task", first, readonly=True)
    assert second["disposition"]["fingerprint"] == first["disposition"]["fingerprint"]
    for event in ("checkpoint", "resume", "turn-end"):
        assert reporter.select_report(snapshot(second), reported, event)["mode"] == "none"
    monkeypatch.setitem(sys.modules, "psutil", available_psutil)
    runnable = dict(facts, work=[{"id": "explicit-independent-unit-task", "title": "Continue the declared unit-fixture task",
        "authorized": True, "feasible": True, "evidence": "Explicit independent unit work, not native admission or a new grant."}])
    restored = run_plan.reconcile_observation(scope, record_path, record, runnable, 1, "INCOMPLETE: private task", second, readonly=True)
    assert restored["disposition"]["state"] == "working" and not restored["disposition"]["external_conditions"]
    assert reporter.select_report(snapshot(restored), reported, "checkpoint")["mode"] == "compact"
    assert record_path.read_bytes() == before


@pytest.mark.parametrize("created", [True, float("nan"), float("inf"), -1, 0, None, "1"])
def test_process_capability_refuses_invalid_self_birth(monkeypatch, created):
    import psutil
    monkeypatch.setattr(psutil, "Process", lambda: SimpleNamespace(create_time=lambda: created))
    with pytest.raises(run_plan.RunnerError, match="native-process-observation-unavailable: psutil"):
        run_plan.require_authority_process_capability()


def test_process_capability_refuses_unusable_imported_observer(monkeypatch):
    import psutil
    def unavailable():
        raise psutil.AccessDenied(123)
    monkeypatch.setattr(psutil, "Process", unavailable)
    with pytest.raises(run_plan.RunnerError, match="native-process-observation-unavailable: psutil.*AccessDenied"):
        run_plan.require_authority_process_capability()
