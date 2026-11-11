"""Exact user-authorized retirement preserves unfinished old authority and crash recovery."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path

import pytest

from .test_check_plan_completion import _isolated_git_config  # noqa: F401
from .test_completion_minor_record import SESSION, _no_transport_overrides  # noqa: F401
from .test_historical_authority import recovery as recovery, signed_scope, native_answer  # noqa: F401
import check_plan_completion as ck
import completion_minor as cm


@pytest.fixture
def owner_scope(recovery):
    repo, current, request = recovery
    old_plan = repo.plan("v0.4.0", "unfinished", folder="docs/archive/v0/v0.4/plans")
    repo.commit("record unfinished older work")
    old = repo.forge(token="v0.4", bound=())
    old_path = cm.record_file(ck, repo.rctx(), "v0.4")
    raw = old_path.read_bytes()
    spec = {
        "path": str(old_path),
        "sha256": hashlib.sha256(raw).hexdigest(),
        "minor": "v0.4",
        "nonce": old["nonce"],
        "members": [member["version"] for member in old["members"]],
    }
    request["owner_retirements"] = [spec]
    return repo, current, request, spec, raw, old_plan


def grant(owner_scope):
    repo, current, request, spec, raw, plan = owner_scope
    scope = signed_scope(repo, current, request)
    args = argparse.Namespace(
        minor="v0.5",
        repo=str(repo.work),
        session=SESSION,
        repair_scope=scope["scope_id"],
        record=spec["path"],
    )
    dest = (
        repo.runs
        / "retired"
        / (Path(spec["path"]).stem + "." + scope["scope_id"] + ".json")
    )
    return repo, args, spec, raw, plan, dest


def test_native_capture_retirement_preserves_unfinished_record(owner_scope):
    repo, current, request, spec, raw, plan = owner_scope
    saved = native_answer(repo, request)
    scope = saved["approvals"]["supplemental_gap_migrations"][0]
    result = repo.run(
        "record",
        "retire-owner",
        "--minor",
        "v0.5",
        "--session",
        SESSION,
        "--repair-scope",
        scope["scope_id"],
        "--record",
        spec["path"],
    )
    assert result.returncode == 0, result.stdout + result.stderr
    receipt = repo.record()["approvals"]["owner_retirement_receipts"][0]
    assert Path(receipt["retired_path"]).read_bytes() == raw
    assert json.loads(raw)["completed"] is None
    assert "- [ ] T001" in (repo.work / plan).read_text()
    assert not Path(spec["path"]).exists()
    assert not cm.other_minor_owns(ck, repo.rctx(), "v0.4.0", repo.record_path())
    assert repo.record()["approvals"]["classes"] == current["approvals"]["classes"]


@pytest.mark.parametrize(
    "stage", ["before-persist", "after-persist", "pre-commit-cas", "post-commit-cas"]
)
def test_interruption_respects_durable_retirement_commit(
    owner_scope, monkeypatch, stage
):
    repo, args, spec, raw, plan, dest = grant(owner_scope)
    original = ck._write_record

    def persist(path, record):
        if stage == "before-persist":
            raise RuntimeError("injected interruption")
        if stage == "pre-commit-cas":
            path.write_bytes(path.read_bytes() + b" ")
        original(path, record)
        if stage == "after-persist":
            raise RuntimeError("injected after commit")
        if stage == "post-commit-cas":
            path.write_bytes(path.read_bytes() + b" ")

    monkeypatch.setattr(ck, "_write_record", persist)
    with pytest.raises((RuntimeError, ck.MinorConflict)):
        cm.cmd_record_retire_owner(ck, args)
    committed = stage in {"after-persist", "post-commit-cas"}
    assert dest.exists() == committed
    assert Path(spec["path"]).exists() != committed
    assert (dest if committed else Path(spec["path"])).read_bytes() == raw
    assert "- [ ] T001" in (repo.work / plan).read_text()
    monkeypatch.setattr(ck, "_write_record", original)
    assert cm.cmd_record_retire_owner(ck, args) == 0
    assert len(repo.record()["approvals"]["owner_retirement_receipts"]) == 1


@pytest.mark.parametrize("change", ["none", "archived-bytes", "restored-source"])
def test_recovery_requires_exact_deterministic_destination(owner_scope, change):
    repo, args, spec, raw, _plan, dest = grant(owner_scope)
    ck._retire(Path(spec["path"]), destination=dest)
    if change == "archived-bytes":
        dest.write_bytes(raw + b" ")
    elif change == "restored-source":
        Path(spec["path"]).write_bytes(raw)
    assert cm.cmd_record_retire_owner(ck, args) == (
        0 if change == "none" else ck.EXIT_BLOCKED
    )
    assert dest.exists()
    if change == "none":
        assert len(repo.record()["approvals"]["owner_retirement_receipts"]) == 1


@pytest.mark.parametrize(
    "change", ["record-bytes", "runner", "unlisted-path", "destination-conflict"]
)
def test_retirement_refuses_scope_drift_without_losing_old_bytes(owner_scope, change):
    repo, args, spec, raw, _plan, dest = grant(owner_scope)
    if change == "record-bytes":
        Path(spec["path"]).write_bytes(raw + b" ")
    elif change == "runner":
        old = Path(spec["path"])
        old.with_name(old.stem + ".runner.lock").write_text(str(os.getpid()))
    elif change == "unlisted-path":
        args.record = str(repo.runs / ("0" * 64 + ".json"))
    else:
        dest.parent.mkdir(exist_ok=True)
        dest.write_bytes(b"Existing content")
    assert cm.cmd_record_retire_owner(ck, args) == ck.EXIT_BLOCKED
    assert Path(spec["path"]).exists()
    assert Path(spec["path"]).read_bytes() in (raw, raw + b" ")
    if change == "destination-conflict":
        assert dest.read_bytes() == b"Existing content"


@pytest.mark.parametrize(
    "change", ["nonce", "members", "younger-minor", "duplicate", "hash"]
)
def test_retirement_list_is_validated_before_capture(owner_scope, change):
    repo, current, request, spec, _raw, _plan = owner_scope
    if change == "nonce":
        spec["nonce"] = "wrong"
    elif change == "members":
        spec["members"] = ["v0.4.1"]
    elif change == "younger-minor":
        spec["minor"] = "v0.6"
    elif change == "duplicate":
        request["owner_retirements"] *= 2
    else:
        spec["sha256"] = "0" * 64
    with pytest.raises(ValueError):
        cm.historical_scope_request(ck, repo.rctx(), current, request)


def test_rollback_commit_classification_holds_both_native_locks(
    owner_scope, monkeypatch
):
    import subprocess
    import sys

    repo, args, spec, raw, _plan, _dest = grant(owner_scope)
    original = cm._retirement_committed
    observed = []
    child = "import sys;sys.path.insert(0,sys.argv[1]);import check_plan_completion as ck;from pathlib import Path\ntry:\n with ck._minor_os_lock(Path(sys.argv[2]),ck.Budget(0.2)): print('ACQUIRED')\nexcept ck.MinorConflict:\n print('BLOCKED');sys.exit(3)"

    def probe(path):
        return subprocess.run(
            [sys.executable, "-c", child, str(Path(ck.__file__).parent), str(path)],
            capture_output=True,
            text=True,
            env=repo.env,
            check=False,
        )

    def classify(*a):
        value = original(*a)
        free = probe(repo.runs / "free-test.mutation.lock")
        assert free.returncode == 0 and "ACQUIRED" in free.stdout
        for path in [repo.record_path(), Path(spec["path"])]:
            result = probe(path.with_name(path.stem + ".mutation.lock"))
            assert result.returncode == 3 and result.stdout.strip() == "BLOCKED", (
                result.stderr
            )
        observed.append(True)
        return value

    monkeypatch.setattr(cm, "_retirement_committed", classify)
    monkeypatch.setattr(
        ck,
        "_write_record",
        lambda *a: (_ for _ in ()).throw(RuntimeError("before commit")),
    )
    with pytest.raises(RuntimeError):
        cm.cmd_record_retire_owner(ck, args)
    assert observed == [True] and Path(spec["path"]).read_bytes() == raw


def test_uncertain_post_commit_preserves_authorized_archive(owner_scope, monkeypatch):
    repo, args, spec, raw, _plan, dest = grant(owner_scope)
    original = ck._write_record

    def persist(path, record):
        original(path, record)
        path.write_bytes(b"[]")
        raise RuntimeError("after committed write and external corruption")

    monkeypatch.setattr(ck, "_write_record", persist)
    with pytest.raises(ck.MinorConflict, match="commit-uncertain"):
        cm.cmd_record_retire_owner(ck, args)
    assert dest.read_bytes() == raw and not Path(spec["path"]).exists()
    assert repo.record_path().read_bytes() == b"[]"


def test_rollback_never_overwrites_a_recreated_slot(owner_scope, monkeypatch):
    repo, args, spec, raw, _plan, dest = grant(owner_scope)
    original = os.link

    def recreate(source, target):
        Path(target).write_bytes(b"New owner contents")
        return original(source, target)

    monkeypatch.setattr(os, "link", recreate)
    monkeypatch.setattr(
        ck,
        "_write_record",
        lambda *a: (_ for _ in ()).throw(RuntimeError("before commit")),
    )
    with pytest.raises(ck.MinorConflict, match="rollback-conflict"):
        cm.cmd_record_retire_owner(ck, args)
    assert Path(spec["path"]).read_bytes() == b"New owner contents"
    assert dest.read_bytes() == raw


def test_redirected_retirement_directory_is_refused(owner_scope, monkeypatch):
    repo, args, spec, raw, _plan, _dest = grant(owner_scope)
    original = Path.resolve
    directory = repo.runs.resolve() / "retired"
    external = repo.tmp.resolve() / "outside-runs"

    def redirected(path, *a, **kw):
        return external if path == directory else original(path, *a, **kw)

    monkeypatch.setattr(Path, "resolve", redirected)
    assert cm.cmd_record_retire_owner(ck, args) == ck.EXIT_BLOCKED
    assert Path(spec["path"]).read_bytes() == raw
    assert not external.exists()


@pytest.mark.parametrize("stage", ["after-move", "before-persist"])
def test_concurrent_recovery_receipt_prevents_parent_rollback(
    owner_scope, monkeypatch, stage
):
    from contextlib import contextmanager

    repo, args, spec, raw, _plan, dest = grant(owner_scope)
    original_lock, original_move, original_write = (
        ck._minor_os_lock,
        ck._retire,
        ck._write_record,
    )
    current_lock = repo.record_path().with_name(
        repo.record_path().stem + ".mutation.lock"
    )
    acquisitions = 0
    fail_once = True
    tick = 0

    def now():
        nonlocal tick
        tick += 1
        return f"2026-10-29T00:00:{tick:02d}+00:00"

    def move(*a, **kw):
        nonlocal fail_once
        result = original_move(*a, **kw)
        if stage == "after-move" and fail_once:
            fail_once = False
            raise RuntimeError("after move before receipt construction")
        return result

    def persist(*a, **kw):
        nonlocal fail_once
        if stage == "before-persist" and fail_once:
            fail_once = False
            raise RuntimeError("before receipt persistence")
        return original_write(*a, **kw)

    @contextmanager
    def locking(path, budget):
        nonlocal acquisitions
        if path == current_lock:
            acquisitions += 1
            if acquisitions == 2:
                # A genuine native recovery commits before the parent reacquires its lock.
                assert cm.cmd_record_retire_owner(ck, args) == 0
        with original_lock(path, budget) as held:
            yield held

    monkeypatch.setattr(ck, "_now", now)
    monkeypatch.setattr(ck, "_minor_os_lock", locking)
    monkeypatch.setattr(ck, "_retire", move)
    monkeypatch.setattr(ck, "_write_record", persist)
    with pytest.raises(RuntimeError):
        cm.cmd_record_retire_owner(ck, args)
    assert not Path(spec["path"]).exists() and dest.read_bytes() == raw
    assert len(repo.record()["approvals"]["owner_retirement_receipts"]) == 1


def test_one_native_grant_covers_only_its_two_exact_older_records(owner_scope):
    repo, current, request, first, first_raw, _plan = owner_scope
    repo.plan("v0.3.0", "other-unfinished", folder="docs/archive/v0/v0.3/plans")
    repo.commit("record second older workflow")
    other = repo.forge(token="v0.3", bound=())
    path = cm.record_file(ck, repo.rctx(), "v0.3")
    raw = path.read_bytes()
    second = {
        "path": str(path),
        "sha256": hashlib.sha256(raw).hexdigest(),
        "minor": "v0.3",
        "nonce": other["nonce"],
        "members": [member["version"] for member in other["members"]],
    }
    request["owner_retirements"].append(second)
    record = native_answer(repo, request)
    scope = record["approvals"]["supplemental_gap_migrations"][0]
    for spec, original in [(first, first_raw), (second, raw)]:
        result = repo.run(
            "record",
            "retire-owner",
            "--minor",
            "v0.5",
            "--session",
            SESSION,
            "--repair-scope",
            scope["scope_id"],
            "--record",
            spec["path"],
        )
        assert result.returncode == 0, result.stdout + result.stderr
        receipt = next(
            proof
            for proof in repo.record()["approvals"]["owner_retirement_receipts"]
            if proof["path"] == spec["path"]
        )
        assert Path(receipt["retired_path"]).read_bytes() == original
    assert len(repo.record()["approvals"]["owner_retirement_receipts"]) == 2
    assert repo.record()["approvals"]["classes"] == current["approvals"]["classes"]
