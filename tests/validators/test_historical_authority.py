"""Exact historical authority, native capture and corrective migration transactions."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

from .test_check_plan_completion import _git, _isolated_git_config  # noqa: F401
from .test_completion_minor_record import SESSION, _no_transport_overrides  # noqa: F401
from .test_gap_migration_and_archive import Close

import approval_binding as ab
import check_plan_completion as ck
import completion_minor as cm
import minor_close as mc

SOURCE = "docs/archive/v0/v0.4/known-gaps.md"
PID = "v0.4#DF-1-P1-A"
RUNTIME = ("check_plan_completion.py", "completion_minor.py", "minor_close.py")


def scope_packet(repo, record):
    ledgers, unreadable = cm.load_ledgers(repo.work)
    assert not unreadable
    source = next(ledger for ledger in ledgers if ledger.rel == SOURCE)
    item = source.items[0]
    heading = item.title.removeprefix(" - ")
    manifest = {
        "schema": 1,
        "baseline_head": record["start_head"],
        "destination": "v0.6.0",
        "ledgers": {SOURCE: cm._lf_hash(source.text)},
        "records": [
            {
                "source": SOURCE,
                "raw_id": "1.P1.A",
                "alias": item.gid,
                "kind": "DF",
                "priority": "1",
                "heading_sha256": hashlib.sha256(heading.encode()).hexdigest(),
                "body_sha256": cm._lf_hash(item.body),
            }
        ],
    }
    path = repo.runs.parent / "requests" / "historical.json"
    path.parent.mkdir(exist_ok=True)
    path.write_bytes(ab.canonical(manifest))
    request = {
        "kind": cm.HISTORICAL_SCOPE,
        "minor": "v0.5",
        "baseline_head": record["start_head"],
        "destination": "v0.6.0",
        "ids": [PID],
        "named": [PID],
        "manifest": {
            "path": str(path),
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        },
        "repair": {
            "blocker": 0,
            "fingerprint": ab.blocker_fingerprint(record["blockers"][0]),
            "ids": [PID, "v0.5#WN-3"],
            "probe_command": [
                sys.executable,
                str(Path(ck.__file__).resolve()),
                "probe-condition",
                "--minor",
                "v0.5",
                "--member",
                "v0.5.2",
                "--repo",
                str(repo.work),
                "--session",
                SESSION,
                "--blocker",
                "0",
            ],
        },
        "tooling": {
            "base_head": record["start_head"],
            "max_fix_cycles": 3,
            "paths": {
                "scripts/" + name: hashlib.sha256(
                    (Path(ck.__file__).parent / name).read_bytes()
                ).hexdigest()
                for name in RUNTIME
            },
        },
    }
    return request


@pytest.fixture
def recovery(tmp_path, monkeypatch):
    repo = Close(tmp_path, monkeypatch)
    repo.write(
        SOURCE,
        "# Gaps\n\n## Open Items\n\n### 1.P1.A -- Original unresolved work (DF, P1)\n\n- **Reason**: Hardware proof still required.\n\n",
    )
    repo.standard()
    record = repo.forge()
    record["blockers"] = [
        {
            "category": "platform-unavailable",
            "version": "v0.5.2",
            "request": {},
            "open": True,
            "evidence": "Original failure retained",
            "why": "Legacy parsing and migration",
            "at": ck._now(),
        }
    ]
    repo.write_record(record, resign=True)
    request = scope_packet(repo, record)
    return repo, record, request


def signed_scope(repo, record, request):
    scope = cm.historical_scope_request(ck, repo.rctx(), record, request)
    scope.update(
        run_nonce=record["nonce"],
        scope_id=hashlib.sha256(ab.canonical(request)).hexdigest(),
        capture={
            "origin": "native-answer",
            "page_sha256": "0" * 64,
            "prompt_sha256": "1" * 64,
        },
    )
    record["approvals"]["supplemental_gap_migrations"] = [scope]
    repo.write_record(record, resign=True)
    return scope


def test_exact_scope_retains_raw_identity_and_original_bounds(recovery):
    repo, record, request = recovery
    original = copy.deepcopy(record["approvals"]["classes"])
    scope = signed_scope(repo, record, request)
    assert PID in cm.migration_class(record)[0]
    projected = ck.project(record, "v0.5.2")
    assert PID in cm.migration_class(projected)[0]
    item = next(
        ledger for ledger in cm.load_ledgers(repo.work)[0] if ledger.rel == SOURCE
    ).items[0]
    assert cm.migration_gate(repo.rctx(), record, (0, 4), item.gid, item) == (
        "met",
        "supplemental-approved",
    )
    assert record["approvals"]["classes"] == original
    with pytest.raises(ValueError, match="overlaps"):
        cm.historical_scope_request(ck, repo.rctx(), record, request)
    record["approvals"]["supplemental_gap_migrations"].append(copy.deepcopy(scope))
    assert cm.migration_gate(repo.rctx(), record, (0, 4), item.gid, item) == (
        "unmet",
        "supplemental-scope-ambiguous",
    )


@pytest.mark.parametrize(
    "change",
    [
        "baseline",
        "destination",
        "named",
        "duplicate",
        "manifest",
        "body",
        "heading",
        "priority",
        "probe",
        "fingerprint",
        "tooling",
        "kind",
        "omit",
        "original-bound",
    ],
)
def test_changed_scope_fails_before_capture(recovery, change):
    repo, record, request = recovery
    if change == "baseline":
        request["baseline_head"] = "0" * 40
    elif change == "destination":
        request["destination"] = "v0.7.0"
    elif change == "named":
        request["named"] = []
    elif change == "duplicate":
        request["ids"] *= 2
    elif change == "manifest":
        Path(request["manifest"]["path"]).write_text("{}")
    elif change == "probe":
        request["repair"]["probe_command"] += ["--other"]
    elif change == "fingerprint":
        request["repair"]["fingerprint"] = "0" * 64
    elif change == "tooling":
        request["tooling"]["paths"]["scripts/completion_minor.py"] = "0" * 64
    elif change == "original-bound":
        request["ids"].append("v0.5#WN-3")
        request["named"] = request["ids"][:]
    else:
        path = Path(request["manifest"]["path"])
        manifest = json.loads(path.read_bytes())
        if change == "body":
            manifest["records"][0]["body_sha256"] = "0" * 64
        elif change == "heading":
            manifest["records"][0]["heading_sha256"] = "0" * 64
        elif change == "priority":
            manifest["records"][0]["priority"] = "3"
        elif change == "kind":
            manifest["records"][0]["kind"] = "WN"
        elif change == "omit":
            manifest["records"] = []
        path.write_bytes(ab.canonical(manifest))
        request["manifest"]["sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
    with pytest.raises((ValueError, OSError)):
        cm.historical_scope_request(ck, repo.rctx(), record, request)


@pytest.mark.parametrize("change", ["nonce", "capture", "request", "manifest-link"])
def test_unbound_scope_grants_nothing(recovery, change):
    repo, record, request = recovery
    scope = signed_scope(repo, record, request)
    if change == "nonce":
        scope["run_nonce"] = "another"
    elif change == "capture":
        scope["capture"]["origin"] = "ordinary-blocker-answer"
    elif change == "request":
        scope["request"]["ids"] = ["v0.4#DF-Other"]
    else:
        scope["manifest_bytes_sha256"] = "0" * 64
    assert PID not in cm.migration_class(record)[0]


def native_answer(repo, request):
    blocked = repo.run(
        "record",
        "block",
        "--minor",
        "v0.5",
        "--session",
        SESSION,
        "--member",
        "v0.5.2",
        "--category",
        "approval-not-covered",
        "--approval-class",
        "gap-migration",
        "--evidence",
        "Exact source manifest and immutable baseline reviewed",
        "--purpose",
        "Retain historical open obligations",
        "--why",
        "Exact supplemental identities",
        "--request",
        json.dumps(request),
    )
    assert blocked.returncode == ck.EXIT_BLOCKED, blocked.stdout + blocked.stderr
    repo.paste(SESSION, "--action", "answer", "--blocker", "1", "--member", "v0.5.2")
    result = repo.run(
        "record", "answer", "--minor", "v0.5", "--session", SESSION, "--blocker", "1"
    )
    assert result.returncode == 0, result.stdout + result.stderr
    return repo.record()


def test_native_capture_bind_and_carry_preserves_original_authority(
    recovery, monkeypatch
):
    repo, original, request = recovery
    record = native_answer(repo, request)
    scope = record["approvals"]["supplemental_gap_migrations"][0]
    assert record["nonce"] == original["nonce"]
    assert record["approvals"]["classes"] == original["approvals"]["classes"]
    assert record["blockers"][0]["open"] and not record["blockers"][1]["open"]
    # Even genuine manual consent cannot replace this grant's required probe.
    repo.paste(SESSION, "--action", "answer", "--blocker", "0", "--member", "v0.5.2")
    manual = repo.run(
        "record",
        "answer",
        "--minor",
        "v0.5",
        "--session",
        SESSION,
        "--blocker",
        "0",
        "--member",
        "v0.5.2",
    )
    assert (
        manual.returncode == ck.EXIT_BLOCKED
        and "bound-condition-requires-fresh-probe" in manual.stdout
    )
    assert repo.record()["blockers"][0]["open"]
    # Ordinary migration cannot pass the technical blocker.
    assert repo.migrate(PID, "v0.5", "--session", SESSION).returncode == 3
    bound = repo.run(
        "record",
        "bind-probe",
        "--minor",
        "v0.5",
        "--session",
        SESSION,
        "--member",
        "v0.5.2",
        "--blocker",
        "0",
        "--repair-scope",
        scope["scope_id"],
    )
    assert bound.returncode == 0, bound.stdout + bound.stderr
    saved = repo.record()
    binding = saved["approvals"]["condition_probe_bindings"][0]
    assert binding["original"] == original["blockers"][0] and binding["exit_code"] == 1
    assert (
        binding["output_sha256"]
        == hashlib.sha256(binding["output"].encode()).hexdigest()
    )
    assert saved["blockers"][0]["open"]
    assert (
        repo.run(
            "record",
            "bind-probe",
            "--minor",
            "v0.5",
            "--session",
            SESSION,
            "--member",
            "v0.5.2",
            "--blocker",
            "0",
            "--repair-scope",
            scope["scope_id"],
        ).returncode
        != 0
    )
    for pid in request["repair"]["ids"]:
        result = repo.migrate(
            pid, "v0.5", "--session", SESSION, "--repair-scope", scope["scope_id"]
        )
        assert result.returncode == 0, result.stdout + result.stderr
    assert repo.gaps_minor() == ("met", [])
    assert "1.P1.A -- Original unresolved work (DF, P1)" in repo.read(
        "docs/releases/v0/v0.6/known-gaps.md"
    )
    assert repo.record()["blockers"][0]["open"]
    # Release predicates are supplied here; real ledger verification still runs.
    monkeypatch.setattr(
        cm,
        "evaluate_member",
        lambda *a: SimpleNamespace(lines=[("integration.checks", "met")]),
    )
    args = argparse.Namespace(
        repo=str(repo.work), minor="v0.5", member="v0.5.2", session=SESSION, blocker=0
    )
    assert cm.cmd_probe_condition(ck, args) == 0


@pytest.mark.parametrize(
    "change", ["other-blocker", "pause", "fingerprint", "session", "foreign-owner"]
)
def test_repair_scope_does_not_waive_other_guards(recovery, monkeypatch, change):
    repo, record, request = recovery
    scope = signed_scope(repo, record, request)
    session = SESSION
    if change == "other-blocker":
        record["blockers"].append({"open": True, "category": "user-edit-guard"})
    elif change == "pause":
        record["pause"] = "pause"
    elif change == "fingerprint":
        record["blockers"][0]["evidence"] += " changed"
    elif change == "session":
        session = "another"
    else:
        monkeypatch.setattr(
            cm, "_owned_member", lambda *a: ("owned-by-another-run", "v0.5.2")
        )
    repo.write_record(record, resign=True)
    with pytest.raises(ValueError):
        cm.repair_scope_record(ck, repo.rctx(), "v0.5", session, scope["scope_id"])


def test_rollback_keeps_concurrent_destination_edit(tmp_path):
    source, target = tmp_path / "source", tmp_path / "target"
    source.write_text("after")
    target.write_text("human edit")
    plan = SimpleNamespace(
        source=SimpleNamespace(path=source, text="before"),
        source_after="after",
        target_path=target,
        target_before="old",
        target_after="new",
    )
    with pytest.raises(mc.Refused, match="repair-rollback-conflict"):
        mc._restore_repair(plan)
    assert source.read_text() == "before" and target.read_text() == "human edit"


def test_supplement_destination_is_shared_by_ordinary_write_and_verify(recovery):
    repo, record, request = recovery
    signed_scope(repo, record, request)
    with pytest.raises(mc.Refused, match="supplemental-destination-not-approved"):
        mc.plan_migration(
            repo.rctx(),
            "v0.5",
            record,
            PID,
            "vendor-feature",
            "Unproved hardware",
            "2026-10-31",
            to="v0.5.0",
        )
    ledgers = cm.load_ledgers(repo.work)[0]
    source = next(ledger for ledger in ledgers if ledger.rel == SOURCE)
    item = copy.copy(source.items[0])
    item.target = "v0.5.0"
    assert cm.verify_migration(repo.rctx(), record, "v0.5", ledgers, source, item) == (
        "unmet",
        "supplemental-destination-not-approved",
    )


def bound_recovery(recovery):
    repo, record, request = recovery
    scope = signed_scope(repo, record, request)
    entry = record["blockers"][0]
    entry["request"] = {"verification": {"command": request["repair"]["probe_command"]}}
    record["approvals"]["condition_probe_bindings"] = [
        {
            "scope_id": scope["scope_id"],
            "blocker": 0,
            "old_fingerprint": request["repair"]["fingerprint"],
            "new_fingerprint": ab.blocker_fingerprint(entry),
            "at": entry["at"],
        }
    ]
    repo.write_record(record, resign=True)
    args = argparse.Namespace(
        minor="v0.5",
        session=SESSION,
        repair_scope=scope["scope_id"],
        to=None,
        reason="vendor-feature",
        dry_run=False,
    )
    return repo, args


@pytest.mark.parametrize(
    "stage", ["planning", "writing", "lease-exit", "concurrent-user-edit"]
)
def test_record_change_rolls_back_only_owned_migration_bytes(
    recovery, monkeypatch, stage
):
    from contextlib import contextmanager

    repo, args = bound_recovery(recovery)
    source_before = (repo.work / SOURCE).read_bytes()
    target = repo.work / "docs/releases/v0/v0.6/known-gaps.md"

    def mutate_record():
        path = repo.record_path()
        path.write_bytes(path.read_bytes() + b" ")

    if stage == "planning":
        original = mc.plan_migration

        def plan(*a, **kw):
            result = original(*a, **kw)
            mutate_record()
            return result

        monkeypatch.setattr(mc, "plan_migration", plan)
    elif stage == "lease-exit":
        original = ck.minor_transaction

        @contextmanager
        def transaction(record):
            with original(record) as lease:
                yield lease
                mutate_record()

        monkeypatch.setattr(ck, "minor_transaction", transaction)
    else:
        original = mc.apply_migration

        def apply(plan):
            original(plan)
            if stage == "concurrent-user-edit":
                target.write_bytes(target.read_bytes() + b"Human addition\n")
            mutate_record()

        monkeypatch.setattr(mc, "apply_migration", apply)
    with pytest.raises((ck.MinorConflict, mc.Refused)):
        mc._corrective_migrate(
            repo.rctx(), args, PID, "Still unproved hardware", "2026-10-31"
        )
    assert (repo.work / SOURCE).read_bytes() == source_before
    if stage == "concurrent-user-edit":
        assert target.read_bytes().endswith(b"Human addition\n")
    else:
        assert not target.exists()


@pytest.mark.parametrize("change", ["id", "destination", "body", "unsigned-probe"])
def test_corrective_migrate_rejects_scope_drift_without_writes(recovery, change):
    repo, args = bound_recovery(recovery)
    pid = PID
    if change == "id":
        pid = "v0.4#DF-Other"
    elif change == "destination":
        args.to = "v0.5.0"
    elif change == "body":
        path = repo.work / SOURCE
        path.write_text(path.read_text().replace("Hardware proof", "Different proof"))
    else:
        record = repo.record()
        record["approvals"]["condition_probe_bindings"] = []
        repo.write_record(record, resign=True)
    with pytest.raises((mc.Refused, ValueError)):
        mc._corrective_migrate(
            repo.rctx(), args, pid, "Still unproved hardware", "2026-10-31"
        )
    assert not (repo.work / "docs/releases/v0/v0.6/known-gaps.md").exists()


@pytest.mark.parametrize(
    "change", ["command", "evidence", "timestamp", "stale-receipt", "valid"]
)
def test_resolve_enforces_signed_probe_and_freshness(
    recovery, monkeypatch, tmp_path, change
):
    import datetime as dt

    repo, args = bound_recovery(recovery)
    record = repo.record()
    entry = record["blockers"][0]
    original_time = dt.datetime.now(dt.timezone.utc) - dt.timedelta(seconds=20)
    bound_time = dt.datetime.now(dt.timezone.utc) - dt.timedelta(seconds=2)
    entry["at"] = bound_time.isoformat()
    binding = record["approvals"]["condition_probe_bindings"][0]
    binding["at"] = entry["at"]
    # Fixture produces the signed binding; subsequent blocker edits remain unsigned.
    repo.write_record(record, resign=True)
    command = entry["request"]["verification"]["command"][:]
    if change == "command":
        command = [sys.executable, "-c", "print(1)"]
        entry["request"]["verification"]["command"] = command
    elif change == "evidence":
        entry["evidence"] += " replaced"
    elif change == "timestamp":
        entry["at"] = original_time.isoformat()
    repo.write_record(record, resign=False)
    output = tmp_path / "probe-output.txt"
    output.write_text("probe observed\n")
    completed = (
        original_time + dt.timedelta(seconds=1)
        if change == "stale-receipt"
        else dt.datetime.now(dt.timezone.utc)
    )
    receipt = tmp_path / "receipt.json"
    receipt.write_text(
        json.dumps(
            {
                "condition": ab.blocker_fingerprint(entry),
                "command": command,
                "completed_at": completed.isoformat(),
                "exit_code": 0,
                "output_path": str(output),
                "output_sha256": hashlib.sha256(output.read_bytes()).hexdigest(),
            }
        )
    )
    monkeypatch.setattr(ck, "_approved_remote_status", lambda *a: "met")
    monkeypatch.setattr(ab, "current_host_context", lambda *a, **kw: {})
    monkeypatch.setattr(ab, "full_access_authorization", lambda *a, **kw: True)
    resolve = argparse.Namespace(
        minor="v0.5",
        repo=str(repo.work),
        member="v0.5.2",
        session=SESSION,
        blocker=0,
        fingerprint=ab.blocker_fingerprint(entry),
        evidence_file=str(receipt),
    )
    result = ck.cmd_record_resolve(resolve)
    assert result == (0 if change == "valid" else ck.EXIT_BLOCKED)
    assert repo.record()["blockers"][0]["open"] == (change != "valid")
