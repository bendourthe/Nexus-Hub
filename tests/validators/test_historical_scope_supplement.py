"""Bounded historical-scope decisions in disposable repositories.

Synthetic captures, signed records, and hosting replies below prove local behavior
only. They are not genuine production authority or release evidence. The reviewed
production descriptor is substituted only inside each test process.
"""
from __future__ import annotations

import argparse
import copy
from contextlib import contextmanager

import pytest

from .test_check_plan_completion import _git, _isolated_git_config  # noqa: F401
from .test_completion_minor_record import Minor, SESSION, _no_transport_overrides  # noqa: F401

import approval_binding
import check_plan_completion as ck
import completion_minor as cm

MINOR = "v0.5"
VERSION = "v0.5.2"
PATHS = (
    "MANIFEST.sha256",
    "scripts/check_installer_smoke.py",
    "scripts/ci/verify_scenarios.py",
    "tests/ci/test_ci_scenarios.py",
    "tests/installer/test_installer_smoke_postconditions.py",
    "tests/skills/test_installer_parity_lifecycle.py",
)


def _member(record):
    return next(m for m in record["members"] if m["version"] == VERSION)


def _tree_rows(root, base, merge):
    raw = _git(root, "diff", "--raw", "--no-abbrev", "--no-renames", "-z", base, merge, "--")
    parts = raw.split("\0")
    rows = []
    for offset in range(0, len(parts) - 1, 2):
        old_mode, new_mode, old_blob, new_blob, status = parts[offset][1:].split()
        rows.append((parts[offset + 1], old_mode, new_mode, old_blob, new_blob, status))
    return tuple(sorted(rows))


@pytest.fixture
def scope_case(tmp_path, monkeypatch, minor_git_seed):
    fx = Minor(tmp_path, monkeypatch, minor_git_seed)
    created = fx.create()
    assert created.returncode == 0, created.stdout + created.stderr
    base = _git(fx.work, "rev-parse", "HEAD")
    record = fx.record()
    member = _member(record)
    member["start_head"] = base
    member["coordinator_paths"] = []
    member["implementation"] = {
        "base_head": base, "worktree": str(tmp_path / "former-worker"),
        "branch": member["source_branch"], "depends_on": [], "read_paths": [],
        "write_paths": ["src/owned.txt"], "started": ck._now(),
    }
    fx.write_record(record, resign=True)  # Disposable fixture authority only.
    _git(fx.work, "checkout", "-q", "-b", member["source_branch"])
    for path in PATHS:
        dest = fx.work / path
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text("historical fixture output\n", encoding="utf-8")
    fx.commit("six unclaimed historical files")
    second = _git(fx.work, "rev-parse", "HEAD")
    _git(fx.work, "checkout", "-q", "develop")
    _git(fx.work, "merge", "-q", "--no-ff", "-m", "merge disposable member", member["source_branch"])
    merge = _git(fx.work, "rev-parse", "HEAD")
    fx.publish("develop")
    fx.state["pr_by_branch"] = {member["source_branch"]: {
        "state": "MERGED", "checks": [{"name": "ci", "bucket": "pass"}], "merge_commit": merge,
    }}
    fx.save_state()
    descriptor = {
        "repo": "acme/demo", "minor": MINOR, "member": VERSION,
        "merge": merge, "first_parent": base, "second_parent": second,
        "tree": _git(fx.work, "rev-parse", merge + "^{tree}"),
        "rows": _tree_rows(fx.work, base, merge),
    }
    assert len(descriptor["rows"]) == 6
    monkeypatch.setattr(cm, "REVIEWED_HISTORICAL_SCOPE", descriptor)
    monkeypatch.chdir(fx.work)
    return fx, descriptor


def _cli(capsys, *args):
    capsys.readouterr()
    rc = ck.main(list(args))
    output = capsys.readouterr()
    return rc, output.out, output.err


def _args(descriptor, session=SESSION):
    return ["--minor", MINOR, "--member", VERSION, "--merge", descriptor["merge"], "--session", session]


def _render(fx, descriptor, capsys, *, session=SESSION):
    rc, out, err = _cli(capsys, "record", "render", "--action", "supplement-scope", *_args(descriptor, session))
    assert rc == 0, out + err
    line = out.splitlines()[0]
    assert "exact historical scope" in line.lower()
    return line


def _grant(fx, descriptor, capsys):
    line = _render(fx, descriptor, capsys)
    fx.capture(SESSION, line)
    rc, out, err = _cli(capsys, "record", "supplement-scope", *_args(descriptor))
    assert rc == 0, out + err
    return fx.record()


def _historical(fx, descriptor, record=None, merge=None):
    value = record if record is not None else fx.record()
    return cm._historical_claim_status(fx.rctx(), _member(value), merge or descriptor["merge"], value, ck=ck)


def _signed_write(fx, record):
    record["approvals_hmac"] = ck._sign(record, ck._secret(create=False) or b"")
    ck._write_record(fx.record_path(), record)


def _used(fx):
    return {str(p.relative_to(fx.runs)): p.read_bytes() for p in fx.runs.rglob("*.json") if p.parent.name == "consumed-prompts"}


def test_real_cli_capture_grants_only_exact_history_and_preserves_release_gates(scope_case, monkeypatch, capsys):
    fx, descriptor = scope_case
    before = fx.record()
    assert _historical(fx, descriptor) == "unmet"
    # The normal subprocess sees the immutable production descriptor, not the
    # in-process fixture substitution, and cannot approve this unrelated merge.
    production = fx.run("record", "render", "--action", "supplement-scope", *_args(descriptor))
    assert production.returncode != 0
    assert fx.record() == before
    before_release = (ck._tag_status(fx.rctx(), VERSION), ck._release_status(fx.rctx(), "acme/demo", VERSION))
    granted = _grant(fx, descriptor, capsys)
    assert _historical(fx, descriptor, granted) == "met"
    additions = _member(granted)["historical_scope_supplements"]
    assert len(additions) == 1
    assert {k: v for k, v in _member(granted).items() if k != "historical_scope_supplements"} == _member(before)
    assert {k: v for k, v in granted.items() if k not in ("members", "approvals_hmac")} == {
        k: v for k, v in before.items() if k not in ("members", "approvals_hmac")
    }
    assert (ck._tag_status(fx.rctx(), VERSION), ck._release_status(fx.rctx(), "acme/demo", VERSION)) == before_release
    assert before_release == ("unmet", "unmet")
    assert not fx.state["releases"] and not _git(fx.work, "tag", "--list", VERSION)
    # Neither a later commit nor active-worker ownership acquires this grant.
    (fx.work / PATHS[0]).write_text("a future change\n", encoding="utf-8")
    fx.commit("future output is not retrospectively approved")
    future = _git(fx.work, "rev-parse", "HEAD")
    assert _historical(fx, descriptor, granted, future) != "met"
    assert cm._implementation_paths(fx.rctx(), _member(granted), descriptor["first_parent"]) == "unmet"


def test_blocker_answer_is_not_a_supplement_and_uncaptured_decision_refuses(scope_case, capsys):
    fx, descriptor = scope_case
    record = fx.record()
    record["blockers"] = [{"category": "approval-not-covered", "open": False, "answered": ck._now(),
                            "answer_text": "Approve the six historical files", "version": VERSION} for _ in range(15)]
    fx.write_record(record, resign=True)
    assert _historical(fx, descriptor) == "unmet"
    forged = copy.deepcopy(record)
    _member(forged)["historical_scope_supplements"] = [{"page": {}, "accepted": {}}]
    before = fx.record_path().read_bytes()
    with pytest.raises(ck.MinorConflict):
        _signed_write(fx, forged)
    assert fx.record_path().read_bytes() == before
    _render(fx, descriptor, capsys)
    before, used = fx.record_path().read_bytes(), _used(fx)
    rc, out, err = _cli(capsys, "record", "supplement-scope", *_args(descriptor), "--text", "Approve")
    assert rc != 0, out + err
    assert fx.record_path().read_bytes() == before and _used(fx) == used


def test_all_reviewed_merge_bounds_and_inventory_are_required(scope_case, monkeypatch):
    fx, descriptor = scope_case
    record = fx.record()
    member = _member(record)
    assert cm.historical_scope_bounds(fx.rctx(), record, member, descriptor["merge"])
    changes = [(name, "0" * 40 if name in ("merge", "first_parent", "second_parent", "tree") else "other")
               for name in ("repo", "minor", "member", "merge", "first_parent", "second_parent", "tree")]
    for name, value in changes:
        changed = copy.deepcopy(descriptor)
        changed[name] = value
        with monkeypatch.context() as patch:
            patch.setattr(cm, "REVIEWED_HISTORICAL_SCOPE", changed)
            with pytest.raises((cm.MinorMalformed, cm.ObservationUnavailable), match="."):
                cm.historical_scope_bounds(fx.rctx(), record, member, descriptor["merge"])
    rows = descriptor["rows"]
    inventories = [rows[:-1], (*rows, rows[0]), (*rows, ("src/additional.txt", *rows[0][1:]))]
    for changed_rows in inventories:
        changed = {**descriptor, "rows": changed_rows}
        with monkeypatch.context() as patch:
            patch.setattr(cm, "REVIEWED_HISTORICAL_SCOPE", changed)
            with pytest.raises((cm.MinorMalformed, cm.ObservationUnavailable), match="."):
                cm.historical_scope_bounds(fx.rctx(), record, member, descriptor["merge"])
    for index in range(1, 6):
        changed_row = list(rows[0])
        changed_row[index] = "M" if index == 5 else ("100755" if index < 3 else "f" * 40)
        changed = {**descriptor, "rows": (tuple(changed_row), *rows[1:])}
        with monkeypatch.context() as patch:
            patch.setattr(cm, "REVIEWED_HISTORICAL_SCOPE", changed)
            with pytest.raises((cm.MinorMalformed, cm.ObservationUnavailable), match="."):
                cm.historical_scope_bounds(fx.rctx(), record, member, descriptor["merge"])


def test_rejects_alias_directory_sensitive_coordinator_and_nonfile_inventory(scope_case, monkeypatch):
    fx, descriptor = scope_case
    record = fx.record()
    row = descriptor["rows"][0]
    for path in ("./MANIFEST.sha256", "manifest.sha256", "scripts/", "scripts\\check_installer_smoke.py",
                 ".github/workflows/build.yml", "catalog/hooks/settings.json", "CHANGELOG.md", "src/known-gaps.md"):
        changed = {**descriptor, "rows": ((path, *row[1:]), *descriptor["rows"][1:])}
        with monkeypatch.context() as patch:
            patch.setattr(cm, "REVIEWED_HISTORICAL_SCOPE", changed)
            with pytest.raises((cm.MinorMalformed, cm.ObservationUnavailable), match="."):
                cm.historical_scope_bounds(fx.rctx(), record, _member(record), descriptor["merge"])
    # Git object modes catch symlinks/submodules without requiring Windows
    # developer mode or skipping the boundary on an unprivileged account.
    for mode in ("120000", "160000", "040000"):
        changed = {**descriptor, "rows": ((row[0], row[1], mode, *row[3:]), *descriptor["rows"][1:])}
        with monkeypatch.context() as patch:
            patch.setattr(cm, "REVIEWED_HISTORICAL_SCOPE", changed)
            with pytest.raises((cm.MinorMalformed, cm.ObservationUnavailable), match="."):
                cm.historical_scope_bounds(fx.rctx(), record, _member(record), descriptor["merge"])


def test_rendered_decision_rejects_foreign_session_and_changed_generation(scope_case, capsys):
    fx, descriptor = scope_case
    line = _render(fx, descriptor, capsys)
    fx.capture("foreign-session", line)
    before = fx.record_path().read_bytes()
    rc, out, err = _cli(capsys, "record", "supplement-scope", *_args(descriptor, "foreign-session"))
    assert rc != 0, out + err
    assert fx.record_path().read_bytes() == before
    fx.capture(SESSION, line)
    record = fx.record()
    record["blockers"].append({"category": "no-progress", "open": False, "evidence": "a concurrent legitimate update"})
    fx.write_record(record, resign=True)
    before, used = fx.record_path().read_bytes(), _used(fx)
    rc, out, err = _cli(capsys, "record", "supplement-scope", *_args(descriptor))
    assert rc != 0, out + err
    assert fx.record_path().read_bytes() == before and _used(fx) == used


def test_concurrent_change_before_lease_does_not_consume_capture(scope_case, monkeypatch, capsys):
    fx, descriptor = scope_case
    fx.capture(SESSION, _render(fx, descriptor, capsys))
    original_lease = ck.minor_lease
    written = []
    used = _used(fx)

    @contextmanager
    def race(path, expected, ctx):
        if not written:
            record = fx.record()
            record["blockers"].append({"category": "no-progress", "open": False, "evidence": "racing writer"})
            fx.write_record(record, resign=True)
            written.append(path.read_bytes())
        with original_lease(path, expected, ctx) as lease:
            yield lease

    monkeypatch.setattr(ck, "minor_lease", race)
    args = argparse.Namespace(minor=MINOR, repo=str(fx.work), session=SESSION, member=VERSION,
                              merge=descriptor["merge"], text=None)
    with pytest.raises(ck.MinorConflict, match="minor-record-changed"):
        cm.cmd_record_supplement_scope(ck, args)
    assert fx.record_path().read_bytes() == written[0] and _used(fx) == used


def test_authenticated_provenance_and_all_page_bounds_are_required(scope_case, capsys):
    fx, descriptor = scope_case
    granted = _grant(fx, descriptor, capsys)
    entry = _member(granted)["historical_scope_supplements"][0]
    assert _historical(fx, descriptor, granted) == "met"
    paths = [("page", name) for name in entry["page"]] + [("accepted", name) for name in entry["accepted"]]
    for section, name in paths:
        changed = copy.deepcopy(granted)
        target = _member(changed)["historical_scope_supplements"][0][section]
        target[name] = None if target[name] is not None else "forged"
        changed["approvals_hmac"] = ck._sign(changed, ck._secret(create=False) or b"")
        assert _historical(fx, descriptor, changed) != "met", (section, name)
    unsigned = copy.deepcopy(granted)
    unsigned["approvals_hmac"] = "0" * 64
    assert _historical(fx, descriptor, unsigned) != "met"
    # Historical authorization is the immutable signed entry, not a forever
    # dependency on prompt retention or a mutable latest-round receipt.
    decision_files = [p for p in fx.runs.rglob("*") if p.is_file()
                      and (p.parent.name in {"consumed-prompts", "prompts"}
                           or "pending" in p.name or "used" in p.name)]
    assert decision_files
    for path in decision_files:
        path.unlink()
    assert _historical(fx, descriptor, granted) == "met"


def test_replay_and_immutable_prefix_survive_later_legitimate_updates(scope_case, monkeypatch, capsys):
    fx, descriptor = scope_case
    monkeypatch.setattr(approval_binding, "_clock", lambda: 1)
    granted = _grant(fx, descriptor, capsys)
    before = fx.record_path().read_bytes()
    used = _used(fx)
    rc, out, err = _cli(capsys, "record", "supplement-scope", *_args(descriptor))
    assert rc != 0, out + err
    assert fx.record_path().read_bytes() == before and _used(fx) == used
    candidates = []
    original_time = _member(granted)["historical_scope_supplements"][0]["accepted"]["rendered_at"]
    assert original_time == 1 and not isinstance(original_time, bool)
    for numeric_alias in (1, 1.0, True):
        if type(numeric_alias) is type(original_time):
            continue
        changed = copy.deepcopy(granted)
        _member(changed)["historical_scope_supplements"][0]["accepted"]["rendered_at"] = numeric_alias
        assert changed == granted  # Python equality would miss this mutation.
        candidates.append(changed)
    changed = copy.deepcopy(granted)
    _member(changed)["historical_scope_supplements"] = []
    candidates.append(changed)
    changed = copy.deepcopy(granted)
    _member(changed)["historical_scope_supplements"][0]["accepted"]["text"] = "forged"
    candidates.append(changed)
    changed = copy.deepcopy(granted)
    changed["members"] = [m for m in changed["members"] if m["version"] != VERSION]
    candidates.append(changed)
    changed = copy.deepcopy(granted)
    _member(changed)["historical_scope_supplements"].append(copy.deepcopy(_member(changed)["historical_scope_supplements"][0]))
    candidates.append(changed)
    changed = copy.deepcopy(granted)
    changed["approvals"]["classes"].append({"class": "unrelated-authority"})
    _member(changed)["historical_scope_supplements"].append(copy.deepcopy(_member(changed)["historical_scope_supplements"][0]))
    candidates.append(changed)
    for value in candidates:
        with pytest.raises(ck.MinorConflict):
            _signed_write(fx, value)
        assert fx.record_path().read_bytes() == before
    # The ordinary block command changes record bytes while retaining the
    # original append-only supplement. Historical use must not require the
    # complete record to remain at the pre-consumption generation forever.
    rc, out, err = _cli(capsys, "record", "block", "--minor", MINOR, "--session", SESSION,
                         "--category", "no-progress", "--evidence", "disposable later update")
    assert rc == ck.EXIT_BLOCKED, out + err
    later = fx.record()
    assert fx.record_path().read_bytes() != before
    assert _member(later)["historical_scope_supplements"] == _member(granted)["historical_scope_supplements"]
    assert _historical(fx, descriptor, later) == "met"


def test_native_resume_and_controller_handoff_preserve_historical_supplement(scope_case, capsys):
    fx, descriptor = scope_case
    granted = _grant(fx, descriptor, capsys)
    record_path = fx.record_path()
    entry_bytes = approval_binding.canonical(_member(granted)["historical_scope_supplements"])
    next_session = "resumed-historical-scope-session"
    fx.capture(next_session, "Resume this disposable minor run", at=0.0)
    rc, out, err = _cli(capsys, "record", "render", "--minor", MINOR,
                         "--action", "resume", "--session", next_session)
    assert rc == 0, out + err
    fx.capture(next_session, out.splitlines()[0])
    rc, out, err = _cli(capsys, "record", "resume", "--minor", MINOR, "--session", next_session)
    assert rc == 0, out + err
    resumed = fx.record()
    assert resumed["session_id"] == next_session != granted["session_id"]
    assert approval_binding.canonical(_member(resumed)["historical_scope_supplements"]) == entry_bytes
    assert _historical(fx, descriptor, resumed) == "met"
    resumed_state = cm.load_minor(ck, fx.rctx(), MINOR, next_session)
    assert resumed_state.forced is None and resumed_state.record is not None

    target = fx.tmp / "next-controller"
    _git(fx.work, "worktree", "add", "-q", "-b", "next-controller", str(target), "origin/develop")
    head = _git(target, "rev-parse", "HEAD")
    assert head == descriptor["merge"]
    handoff_args = ["record", "controller-handoff", "--minor", MINOR, "--session", next_session,
                    "--repo", str(fx.work), "--to", str(target), "--head", head,
                    "--expected-generation", "0", "--apply"]
    before_refusal = record_path.read_bytes()
    rc, out, err = _cli(capsys, *handoff_args)
    assert rc != 0 and "member-release-history-not-in-target" in out + err
    assert record_path.read_bytes() == before_refusal

    # The canonical disposable fixture supplies the tag and local hosted-Release
    # reply. No controller or release predicate is patched or bypassed.
    fx.ship(VERSION)
    target_ctx = ck.RepoContext(target, ck.Budget(60))
    assert cm._tag_in(target_ctx, VERSION, head) == "met"
    assert ck._release_status(target_ctx, "acme/demo", VERSION) == "met"
    rc, out, err = _cli(capsys, *handoff_args)
    assert rc == 0 and out.startswith("TRANSFERRED "), out + err
    moved = ck.read_record(ck.RepoContext(target, ck.Budget(60)), record_path)
    assert isinstance(moved, ck.MinorSnapshot)
    assert moved["implementation_controller"]["repo_root"] == str(target)
    assert moved["implementation_controller"]["generation"] == 1
    assert moved["session_id"] == next_session
    assert approval_binding.canonical(_member(moved)["historical_scope_supplements"]) == entry_bytes
    assert {k: v for k, v in moved.items() if k not in ("implementation_controller", "approvals_hmac")} == {
        k: v for k, v in resumed.items() if k not in ("implementation_controller", "approvals_hmac")
    }
    target_ctx = ck.RepoContext(target, ck.Budget(60))
    cm.require_controller(ck, target_ctx, moved, record_path)
    moved_state = cm.load_minor(ck, ck.RepoContext(target, ck.Budget(60)), MINOR, next_session)
    assert moved_state.forced is None and moved_state.record is not None
    assert cm._historical_claim_status(ck.RepoContext(target, ck.Budget(60)), _member(moved),
                                       descriptor["merge"], moved, ck=ck) == "met"
