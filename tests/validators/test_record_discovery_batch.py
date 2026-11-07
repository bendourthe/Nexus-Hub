"""Bounded record discovery preserves fresh provenance and record reads."""
from __future__ import annotations

import json
import shutil
from pathlib import Path
from types import SimpleNamespace

import pytest

from .test_completion_minor_record import Minor, ck, cm, _git
from .test_completion_minor_record import _no_transport_overrides  # noqa: F401 - autouse fixture
from .test_check_plan_completion import _isolated_git_config  # noqa: F401 - autouse fixture


class GitObservation:
    def __init__(self):
        self.inside = False
        self.git_dir = "/repo/.git"
        self.worktree = "/repo"
        self.tracked = set()
        self.calls = []
        self.unavailable_at = None

    def __call__(self, argv, budget, cwd=None):
        self.calls.append(argv)
        if len(self.calls) == self.unavailable_at:
            return -1, ""
        if "--is-inside-work-tree" in argv:
            return (0, "true\n") if self.inside else (128, "")
        if "--absolute-git-dir" in argv:
            return 0, self.git_dir + "\n"
        if "--show-toplevel" in argv:
            return 0, self.worktree + "\n"
        assert "ls-files" in argv
        assert "--literal-pathspecs" in argv and "-z" in argv
        assert argv[-1] == "--"
        return 0, "".join(name + "\0" for name in sorted(self.tracked))


@pytest.fixture
def records(tmp_path, monkeypatch):
    paths = [tmp_path / f"record-{index:03}.json" for index in range(120)]
    for index, path in enumerate(paths):
        path.write_text(json.dumps({"schema": 1, "value": index}), encoding="utf-8")
    observation = GitObservation()
    monkeypatch.setattr(ck, "_run", observation)
    ctx = SimpleNamespace(git="git", budget=ck.Budget(20))
    return ctx, paths, observation


def test_many_historical_records_use_two_outside_git_probes(records):
    ctx, paths, observation = records
    with ck.record_read_batch(ctx, paths) as read:
        assert [read(path)["value"] for path in paths] == list(range(120))
    assert len(observation.calls) == 2
    assert ck.BUDGET_SECONDS == 20.0


def test_minor_discovery_does_not_probe_once_per_historical_record(records, monkeypatch):
    ctx, paths, observation = records
    ctx.root = paths[0].parent
    ctx.scoped_record_path = lambda _scope: paths[0]
    monkeypatch.setattr(ck, "_runs_dir", lambda: paths[0].parent)
    monkeypatch.setattr(cm, "_common_dir", lambda *_args: "/repo/.git")
    assert cm.minor_candidates(ck, ctx, "v0.5") == []
    assert len(observation.calls) == 2


def test_new_discovery_with_old_checker_refuses_before_observing_records(records, monkeypatch):
    ctx, _paths, observation = records
    monkeypatch.delattr(ck, "record_read_batch")
    with pytest.raises(cm.ObservationUnavailable, match="record.provenance"):
        cm.minor_candidates(ck, ctx, "v0.5")
    assert not observation.calls


def test_old_protocol_missing_batch_keeps_incompatibility_refusal(records, monkeypatch):
    ctx, _paths, observation = records
    monkeypatch.delattr(ck, "record_read_batch")
    monkeypatch.delattr(ck, "MINOR_AMENDMENT_PROTOCOL")
    with pytest.raises(ck.MinorConflict, match="minor-amendment-consumer-incompatible"):
        cm.minor_candidates(ck, ctx, "v0.5")
    assert not observation.calls


def test_empty_discovery_cannot_return_after_provenance_changes(records, monkeypatch):
    ctx, paths, observation = records
    ctx.root = paths[0].parent
    ctx.scoped_record_path = lambda _scope: paths[0]
    monkeypatch.setattr(ck, "_runs_dir", lambda: paths[0].parent)
    monkeypatch.setattr(cm, "_common_dir", lambda *_args: "/repo/.git")
    original = ck._read_record_json

    def initialize_git(context, path):
        observation.inside = True
        return original(context, path)

    monkeypatch.setattr(ck, "_read_record_json", initialize_git)
    with pytest.raises(cm.ObservationUnavailable, match="record.provenance"):
        cm.minor_candidates(ck, ctx, "v0.5")


def test_real_git_refuses_literal_tracked_record_and_accepts_untracked(tmp_path):
    root = tmp_path / "repo"
    root.mkdir()
    _git(root, "init", "-q")
    tracked = root / "[tracked].json"
    untracked = root / "t.json"
    for path in (tracked, untracked):
        path.write_text('{"schema":1}', encoding="utf-8")
    _git(root, "--literal-pathspecs", "add", "--", tracked.name)
    ctx = SimpleNamespace(git=shutil.which("git"), budget=ck.Budget(20))
    with ck.record_read_batch(ctx, [tracked, untracked]) as read:
        assert read(tracked) is None
        assert read(untracked) == {"schema": 1}


def test_inside_git_uses_literal_nul_membership_and_refuses_tracked(records):
    ctx, paths, observation = records
    observation.inside = True
    observation.tracked = {paths[0].name, paths[2].name}
    with ck.record_read_batch(ctx, paths) as read:
        assert read(paths[0]) is None
        assert read(paths[1])["value"] == 1
        assert read(paths[2]) is None
    assert len(observation.calls) == 8


@pytest.mark.parametrize("unavailable_at", [1, 2])
def test_outside_git_unavailable_initial_or_final_probe_refuses(records, unavailable_at):
    ctx, paths, observation = records
    observation.unavailable_at = unavailable_at
    with pytest.raises(cm.ObservationUnavailable, match="record.provenance"):
        with ck.record_read_batch(ctx, paths) as read:
            read(paths[0])


@pytest.mark.parametrize("unavailable_at", list(range(1, 9)))
def test_inside_git_unavailable_any_observation_refuses(records, unavailable_at):
    ctx, paths, observation = records
    observation.inside = True
    observation.unavailable_at = unavailable_at
    with pytest.raises(cm.ObservationUnavailable, match="record.provenance"):
        with ck.record_read_batch(ctx, paths) as read:
            read(paths[0])


@pytest.mark.parametrize("change", ["initialize", "track", "git-dir", "worktree"])
def test_changed_provenance_refuses_before_discovery_can_return(records, change):
    ctx, paths, observation = records
    observation.inside = change != "initialize"
    with pytest.raises(cm.ObservationUnavailable, match="record.provenance"):
        with ck.record_read_batch(ctx, paths) as read:
            assert read(paths[0])["value"] == 0
            if change == "initialize":
                observation.inside = True
            elif change == "track":
                observation.tracked.add(paths[0].name)
            elif change == "git-dir":
                observation.git_dir = "/different/.git"
            else:
                observation.worktree = "/different"


def test_reader_is_limited_to_listed_literal_paths_and_closed_after_exit(records):
    ctx, paths, _ = records
    with ck.record_read_batch(ctx, paths[:1]) as read:
        for outside in [paths[1], paths[0].parent / "other" / paths[0].name]:
            with pytest.raises(cm.ObservationUnavailable, match="record.provenance"):
                read(outside)
        assert read(paths[0])["value"] == 0
    with pytest.raises(cm.ObservationUnavailable, match="record.provenance"):
        read(paths[0])


def test_case_varied_path_cannot_bypass_literal_tracked_membership(records):
    ctx, paths, observation = records
    observation.inside = True
    observation.tracked = {paths[0].name}
    alias = paths[0].with_name(paths[0].name.upper())
    with ck.record_read_batch(ctx, paths[:1]) as read:
        with pytest.raises(cm.ObservationUnavailable, match="record.provenance"):
            read(alias)
        assert read(paths[0]) is None


def test_different_parent_batch_is_rejected(records):
    ctx, paths, observation = records
    with pytest.raises(cm.ObservationUnavailable, match="record.provenance"):
        with ck.record_read_batch(ctx, [paths[0], paths[0].parent / "other" / "x.json"]):
            pytest.fail("mixed-parent batch must not open")
    assert not observation.calls


def test_record_contents_are_never_cached(records):
    ctx, paths, _ = records
    path = paths[0]
    with ck.record_read_batch(ctx, [path]) as read:
        assert read(path)["value"] == 0
        path.write_text('{"schema":1,"value":"changed"}', encoding="utf-8")
        assert read(path)["value"] == "changed"
        path.write_text("malformed", encoding="utf-8")
        assert read(path) is None


def test_minor_snapshot_preserves_fresh_raw_bytes_and_context(records):
    ctx, paths, _ = records
    path = paths[0]
    path.write_text('{"schema":2,"value":"first"}', encoding="utf-8")
    with ck.record_read_batch(ctx, [path]) as read:
        first = read(path)
        path.write_text('{"schema":2,"value":"second"}', encoding="utf-8")
        second = read(path)
    assert isinstance(first, ck.MinorSnapshot) and isinstance(second, ck.MinorSnapshot)
    assert first.loaded_sha256 != second.loaded_sha256
    assert first.record_path == second.record_path == path.resolve()


def test_nested_cross_context_and_consecutive_batches_do_not_share_metadata(records):
    ctx, paths, observation = records
    other_ctx = SimpleNamespace(git="different-git", budget=ck.Budget(20))
    with ck.record_read_batch(ctx, paths[:1]) as outer:
        with ck.record_read_batch(other_ctx, paths[1:2]) as inner:
            assert inner(paths[1])["value"] == 1
            with pytest.raises(cm.ObservationUnavailable, match="record.provenance"):
                outer(paths[1])
        assert outer(paths[0])["value"] == 0
    with ck.record_read_batch(ctx, paths[:1]) as later:
        assert later(paths[0])["value"] == 0
    assert len(observation.calls) == 6
    assert [argv[0] for argv in observation.calls] == ["git", "different-git", "different-git", "git", "git", "git"]


def test_body_exception_does_not_leave_reader_active(records):
    ctx, paths, observation = records
    with pytest.raises(ValueError, match="body"):
        try:
            with ck.record_read_batch(ctx, paths[:1]) as read:
                raise ValueError("body")
        finally:
            with pytest.raises(cm.ObservationUnavailable, match="record.provenance"):
                read(paths[0])
            assert len(observation.calls) == 1


def test_known_integrity_failure_is_not_masked_by_unavailable_final_probe(records):
    ctx, paths, observation = records
    observation.unavailable_at = 2
    with pytest.raises(ck.MinorConflict, match="record-tampered"):
        try:
            with ck.record_read_batch(ctx, paths[:1]) as read:
                raise ck.MinorConflict("record-tampered")
        finally:
            with pytest.raises(cm.ObservationUnavailable, match="record.provenance"):
                read(paths[0])
            assert len(observation.calls) == 1


def test_caught_integrity_exception_still_requires_final_provenance(records):
    ctx, paths, observation = records
    observation.unavailable_at = 2
    with pytest.raises(cm.ObservationUnavailable, match="record.provenance"):
        with ck.record_read_batch(ctx, paths[:1]):
            try:
                raise ck.MinorConflict("record-tampered")
            except ck.MinorConflict:
                pass
    assert len(observation.calls) == 2


def test_genuine_private_hmac_failure_retains_integrity_refusal(tmp_path, monkeypatch, minor_git_seed):
    fixture = Minor(tmp_path, monkeypatch, minor_git_seed)
    created = fixture.create()
    assert created.returncode == 0, created.stdout + created.stderr
    path = fixture.record_path()
    record = json.loads(path.read_bytes())
    record["approvals_hmac"] = "0" * 64
    path.write_text(json.dumps(record), encoding="utf-8")
    before = path.read_bytes()
    ctx = fixture.rctx()
    observation = GitObservation()
    observation.unavailable_at = 2
    monkeypatch.setattr(ck, "_run", observation)
    monkeypatch.setattr(cm, "_common_dir", lambda *_args: "/repo/.git")
    with pytest.raises(ck.MinorConflict, match="record-tampered"):
        cm.minor_candidates(ck, ctx, "v0.5")
    assert len(observation.calls) == 1
    assert path.read_bytes() == before


def test_standalone_reader_keeps_fresh_per_path_provenance(records):
    ctx, paths, observation = records
    assert ck.read_record(ctx, paths[0])["value"] == 0
    assert ck.read_record(ctx, paths[1])["value"] == 1
    assert len(observation.calls) == 2


def test_empty_batch_never_observes_or_grants_a_path(records):
    ctx, paths, observation = records
    with ck.record_read_batch(ctx, []) as read:
        with pytest.raises(cm.ObservationUnavailable, match="record.provenance"):
            read(paths[0])
    assert not observation.calls
