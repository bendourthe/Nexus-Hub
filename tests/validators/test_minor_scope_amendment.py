"""Native minor amendments use disposable capture fixtures and no live approvals."""

import copy
import hashlib
import hmac
import json
import subprocess
import sys
from pathlib import Path

import pytest

from .test_completion_minor_record import Minor, SESSION, ck, cm, minor, _git, _isolated_git_config, _no_transport_overrides


def amendment_input(fx: Minor, version: str = "v0.5.11", slug: str = "added") -> tuple[str, dict]:
    """Add a committed, integrated candidate after the original approval."""
    rel = fx.plan(version, slug)
    fx.commit("add candidate plan")
    _git(fx.work, "branch", "-f", "develop", "HEAD")
    fx.publish("develop")
    descriptor = {"version": version, "plan_path": rel,
                  "plan_sha256": ck.plan_hash_text((fx.work / rel).read_text()),
                  "source_branch": f"feat/{version}-{slug}", "target_branch": "develop",
                  "release_version": version, "tag": version,
                  "approvals": {"classes": [{"class": "push-merge"},
                                              {"class": "release", "bound": version}],
                                "cleanup": {"branches": [], "worktrees": []}}}
    value = {"members": [descriptor]}
    path = fx.tmp / "amendment.json"
    path.write_text(json.dumps(value))
    return str(path), value


def amend_fixture(fx: Minor) -> tuple[dict, dict]:
    """Exercise native render/capture/consume for sibling archive and rollback tests."""
    assert fx.create().returncode == 0
    before = fx.record()
    path, _ = amendment_input(fx)
    fx.paste(SESSION, "--action", "amend-minor", "--amendment", path)
    result = fx.run("record", "amend-minor", "--minor", "v0.5", "--session", SESSION,
                    "--amendment", path)
    assert result.returncode == 0, result.stdout + result.stderr
    return before, fx.record()


def test_legacy_payload_remains_identical(minor):
    assert minor.create().returncode == 0
    record = minor.record()
    payload = {name: record.get(name) for name in ck._SIGNED_FIELDS + ck._SIGNED_MINOR_FIELDS}
    expected = hmac.new(ck._secret(create=False), ck._canonical(payload), hashlib.sha256).hexdigest()
    assert ck._sign(record, ck._secret(create=False)) == expected


def test_native_amend_preserves_original_members_and_scopes_grants(minor):
    before, record = amend_fixture(minor)
    assert record["members"] == before["members"]
    assert record["approvals"] == before["approvals"]
    assert record["nonce"] == before["nonce"]
    members = cm.effective_members(ck, record)
    assert [m["version"] for m in members] == ["v0.5.2", "v0.5.10", "v0.5.11"]
    assert members[-1] is record["minor_amendment_members"][0]
    assert cm._verified(ck, minor.rctx(), "v0.5", record, minor_protocol=1)
    projected = ck.project(record, "v0.5.11")
    assert {c["class"] for c in projected["approvals"]["classes"]} == {"push-merge", "release"}
    accepted = record["minor_amendments"][0]["accepted"]
    assert projected["approvals"]["authorization_context"] == accepted["authorization_context"]
    assert projected["approvals"]["page_sha256"] == accepted["page_sha256"]
    assert projected["approvals"]["autonomy_policy"] is None
    with pytest.raises(ck.MinorConflict, match="protocol"):
        ck._sign(record, ck._secret(create=False))
    assert not cm._verified(ck, minor.rctx(), "v0.5", record)


@pytest.mark.parametrize("removed", ck.MINOR_AMENDMENT_FIELDS)
def test_partial_format_cannot_be_signed(minor, removed):
    _, record = amend_fixture(minor)
    del record[removed]
    with pytest.raises(ck.MinorConflict):
        ck._sign(record, ck._secret(create=False), minor_protocol=1)


def test_history_rewrite_refused_at_native_writer(minor):
    _, record = amend_fixture(minor)
    snapshot = cm.load_minor(ck, minor.rctx(), "v0.5", SESSION, minor_protocol=1).record
    snapshot["minor_amendments"][0]["page"]["members"][0]["tag"] = "v0.5.99"
    snapshot["approvals_hmac"] = ck._sign(snapshot, ck._secret(create=False), minor_protocol=1)
    with pytest.raises(ck.MinorConflict):
        ck._write_record(snapshot.record_path, snapshot)


def test_original_native_publication_writer_preserves_amendment(minor):
    _, amended = amend_fixture(minor)
    result = minor.run("record", "member-start", "--minor", "v0.5", "--session", SESSION,
                       "--member", "v0.5.2", "--head", _git(minor.work, "rev-parse", "HEAD"))
    assert result.returncode == 0, result.stdout + result.stderr
    current = minor.record()
    assert current["minor_amendments"] == amended["minor_amendments"]
    assert current["members"][0]["start_head"]
    assert cm._verified(ck, minor.rctx(), "v0.5", current, minor_protocol=1)


def test_coherent_old_payload_and_mixed_legacy_signer_cannot_verify(minor):
    _, record = amend_fixture(minor)
    legacy_payload = {k: record.get(k) for k in ck._SIGNED_FIELDS + ck._SIGNED_MINOR_FIELDS}
    legacy_hmac = hmac.new(ck._secret(create=False), ck._canonical(legacy_payload), hashlib.sha256).hexdigest()
    assert legacy_hmac != record["approvals_hmac"]
    with pytest.raises(ck.MinorConflict):
        cm.load_minor(ck, minor.rctx(), "v0.5", SESSION)
    with pytest.raises(ck.MinorConflict):
        ck.resolve_minor_controller(minor.record_path(), SESSION)
    assert ck.resolve_minor_controller(minor.record_path(), SESSION, minor_protocol=1)[1]


@pytest.mark.parametrize("change", ["hash", "duplicate", "duplicate-new-branch", "old-bypass", "worktree", "bad-gap-reason"])
def test_amendment_refuses_invalid_input_without_mutation(minor, change):
    assert minor.create().returncode == 0
    path, value = amendment_input(minor)
    before = minor.record_path().read_bytes()
    member = value["members"][0]
    if change == "hash":
        member["plan_sha256"] = "0" * 64
    elif change == "duplicate":
        value["members"].append(copy.deepcopy(member))
    elif change == "duplicate-new-branch":
        rel = minor.plan("v0.5.12", "second")
        minor.commit("add second candidate")
        _git(minor.work, "branch", "-f", "develop", "HEAD")
        minor.publish("develop")
        second = copy.deepcopy(member)
        second.update(version="v0.5.12", release_version="v0.5.12", tag="v0.5.12", plan_path=rel,
                      plan_sha256=ck.plan_hash_text((minor.work / rel).read_text()))
        second["approvals"]["classes"][1]["bound"] = "v0.5.12"
        value["members"].append(second)
    elif change == "old-bypass":
        member["approvals"]["classes"].append({"class": "unattended-with-bypass"})
    elif change == "worktree":
        member["approvals"]["cleanup"]["worktrees"].append(str(minor.work))
    else:
        value["gap_migration"] = {"items": [{"id": "v0.5#WN-3", "reason": "arbitrary"}], "named_high_risk_ids": []}
    Path(path).write_text(json.dumps(value))
    result = minor.render(SESSION, "--action", "amend-minor", "--amendment", path)
    assert result.returncode != 0
    assert minor.record_path().read_bytes() == before


def test_amendment_refuses_active_runner_and_stale_page(minor):
    assert minor.create().returncode == 0
    path, _ = amendment_input(minor)
    before = minor.record_path().read_bytes()
    lock = minor.lock(minor.record_path())
    result = minor.render(SESSION, "--action", "amend-minor", "--amendment", path)
    assert result.returncode != 0
    lock.unlink()
    minor.paste(SESSION, "--action", "amend-minor", "--amendment", path)
    current = minor.record()
    current["approvals"]["spend_caps"] = {"usd": 1}
    minor.write_record(current, resign=True)
    changed = minor.record_path().read_bytes()
    result = minor.run("record", "amend-minor", "--minor", "v0.5", "--session", SESSION, "--amendment", path)
    assert result.returncode != 0
    assert minor.record_path().read_bytes() == changed
    assert before != changed


def test_resume_and_legacy_blocker_answer_precede_native_amendment(minor):
    assert minor.create().returncode == 0
    original = minor.record()
    blocked = minor.run("record", "block", "--minor", "v0.5", "--session", SESSION,
                        "--member", "v0.5.2", "--category", "approval-not-covered", "--evidence", "fixture legacy decision")
    assert blocked.returncode == ck.EXIT_BLOCKED
    path, _ = amendment_input(minor)
    refusal = minor.render(SESSION, "--action", "amend-minor", "--amendment", path)
    assert refusal.returncode == ck.EXIT_BLOCKED
    session = "new-amendment-owner"
    minor.paste(session, "--action", "resume")
    resumed = minor.run("record", "resume", "--minor", "v0.5", "--session", session)
    assert resumed.returncode == 0, resumed.stdout + resumed.stderr
    assert minor.record()["blockers"][0]["open"]
    minor.paste(session, "--action", "answer", "--blocker", "0", "--member", "v0.5.2")
    answer = minor.run("record", "answer", "--minor", "v0.5", "--session", session, "--blocker", "0", "--member", "v0.5.2")
    assert answer.returncode == 0, answer.stdout + answer.stderr
    before_amendment = minor.record()
    minor.paste(session, "--action", "amend-minor", "--amendment", path)
    result = minor.run("record", "amend-minor", "--minor", "v0.5", "--session", session, "--amendment", path)
    assert result.returncode == 0, result.stdout + result.stderr
    current = minor.record()
    assert current["members"] == original["members"]
    assert current["blockers"] == before_amendment["blockers"]
    assert not current["blockers"][0]["open"]
    assert cm._verified(ck, minor.rctx(), "v0.5", current, minor_protocol=1)


@pytest.mark.parametrize("field", ["version", "plan_path", "plan_sha256", "source_branch", "target_branch", "tag", "approvals"])
def test_malformed_descriptor_types_fail_closed(minor, field):
    assert minor.create().returncode == 0
    path, value = amendment_input(minor)
    value["members"][0][field] = {"malformed": []}
    Path(path).write_text(json.dumps(value))
    before = minor.record_path().read_bytes()
    result = minor.render(SESSION, "--action", "amend-minor", "--amendment", path)
    assert result.returncode == ck.EXIT_MALFORMED
    assert "Traceback" not in result.stderr
    assert minor.record_path().read_bytes() == before


def test_amended_record_cannot_be_replaced_by_a_downgraded_record(minor):
    _, record = amend_fixture(minor)
    before = minor.record_path().read_bytes()
    for name in ck.MINOR_AMENDMENT_FIELDS:
        record.pop(name)
    record["schema"] = 1
    record.pop("scope")
    record["approvals_hmac"] = ck._sign(record, ck._secret(create=False))
    with pytest.raises(ck.MinorConflict, match="history-removed"):
        ck._write_record(minor.record_path(), record)
    assert minor.record_path().read_bytes() == before


def test_second_native_amendment_preserves_history_and_runtime(minor):
    _, first = amend_fixture(minor)
    path, _ = amendment_input(minor, "v0.5.12", "second")
    minor.paste(SESSION, "--action", "amend-minor", "--amendment", path)
    result = minor.run("record", "amend-minor", "--minor", "v0.5", "--session", SESSION, "--amendment", path)
    assert result.returncode == 0, result.stdout + result.stderr
    current = minor.record()
    assert current["minor_amendments"][:1] == first["minor_amendments"]
    assert current["minor_amendment_members"][:1] == first["minor_amendment_members"]
    assert current["minor_amendments"][1]["page"]["previous_history_sha256"] == cm._amendment_digest(first["minor_amendments"])
    assert cm._verified(ck, minor.rctx(), "v0.5", current, minor_protocol=1)


def test_added_member_does_not_inherit_original_policy_or_reset_aggregate_caps(minor, monkeypatch):
    original_approvals = minor.approvals
    policy = {"planned_actions": [{"class": "ask-first:user-edit-baseline", "paths": ["src/old.txt"]}]}
    def approvals(*extra):
        path = original_approvals(*extra)
        value = json.loads(path.read_text())
        value.update(autonomy=policy, spend_caps={"usd": 2})
        path.write_text(json.dumps(value))
        return path
    monkeypatch.setattr(minor, "approvals", approvals)
    before, record = amend_fixture(minor)
    assert record["approvals"] == before["approvals"]
    original = ck.project(record, "v0.5.2")
    added = ck.project(record, "v0.5.11")
    assert original["approvals"]["autonomy_policy"]["planned_actions"] == policy["planned_actions"]
    assert added["approvals"]["autonomy_policy"] is None
    assert added["approvals"]["spend_caps"] == {"usd": 2}
    assert record["minor_amendments"][0]["page"]["spend_caps"] == {"usd": 2}


@pytest.mark.parametrize("phase", ["render", "consume"])
def test_amendment_status_failure_refuses_without_mutation(minor, phase):
    assert minor.create().returncode == 0
    path, _ = amendment_input(minor)
    if phase == "consume":
        minor.paste(SESSION, "--action", "amend-minor", "--amendment", path)
    before = minor.record_path().read_bytes()
    # Only the disposable child checker sees the failed Git observation.
    injector = minor.tmp / "status-failure.py"
    injector.write_text(
        "import sys\n"
        "sys.path.insert(0, sys.argv[1])\n"
        "import check_plan_completion as ck\n"
        "original = ck._run\n"
        "failures = 0\n"
        "def fault(argv, *args, **kwargs):\n"
        "    global failures\n"
        "    if argv[3:] == ['status', '--porcelain']:\n"
        "        failures += 1\n"
        "        return 128, 'fatal: index file corrupt'\n"
        "    return original(argv, *args, **kwargs)\n"
        "ck._run = fault\n"
        "result = ck.main(sys.argv[2:])\n"
        "print('INJECTED_STATUS_FAILURES=' + str(failures), file=sys.stderr)\n"
        "raise SystemExit(result)\n",
        encoding="utf-8",
    )
    action = ["render", "--action", "amend-minor"] if phase == "render" else ["amend-minor"]
    result = subprocess.run(
        [sys.executable, str(injector), str(Path(ck.__file__).parent), "record", *action,
         "--minor", "v0.5", "--session", SESSION, "--amendment", path],
        cwd=minor.work, env=minor.env, capture_output=True, text=True, check=False, timeout=300,
    )
    assert "INJECTED_STATUS_FAILURES=1" in result.stderr, result.stdout + result.stderr
    assert result.returncode == ck.EXIT_MALFORMED, result.stdout + result.stderr
    assert "amendment requires a clean controller worktree" in result.stderr
    assert "Traceback" not in result.stderr
    assert minor.record_path().read_bytes() == before
