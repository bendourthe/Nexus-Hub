"""Failure-atomic edit-guard cache publication regressions."""

from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
from types import SimpleNamespace

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = (
    REPO_ROOT
    / "catalog"
    / "skills"
    / "workflow"
    / "user-edit-preservation"
    / "scripts"
    / "edit_guard.py"
)


@pytest.fixture
def guard(tmp_path, monkeypatch):
    spec = importlib.util.spec_from_file_location("publication_guard", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    work = tmp_path / "work"
    work.mkdir()
    monkeypatch.chdir(work)
    monkeypatch.setenv("NEXUS_EDIT_GUARD_DIR", str(tmp_path / "store"))
    monkeypatch.setenv("NEXUS_EDIT_GUARD_SESSION", "publication-test")
    return module, module.store_dir(), work


def args(path, **kw):
    return SimpleNamespace(
        path=str(path), source="read", force=False, session="publication-test", **kw
    )


def reviewed(guard):
    module, root, work = guard
    path = work / "notes.md"
    path.write_text("original baseline\n", encoding="utf-8")
    assert module.cmd_record(args(path), root) == 0
    key = module.key_for(path)
    path.write_text("original baseline\nuser change\n", encoding="utf-8")
    assert module.cmd_diff(args(path), root) == 0
    record_path = root / "records" / f"{key}.json"
    record = module.load_record(root, key)
    copy = module._copy_path(root, key, record)
    return path, key, record_path, record_path.read_bytes(), copy, copy.read_bytes()


@pytest.mark.parametrize("fail_at", ["metadata", "snapshot", "permissions"])
def test_failed_accept_preserves_reviewed_baseline(guard, monkeypatch, capsys, fail_at):
    module, root, _work = guard
    path, key, record_path, old_record, old_copy, old_bytes = reviewed(guard)
    original_replace = module._replace_private
    original_permissions = module._owner_only

    def fail_replace(source, destination):
        if (fail_at == "metadata" and destination.parent.name == "records") or (
            fail_at == "snapshot" and destination.parent.name == "copies"
        ):
            raise PermissionError("injected publication failure")
        return original_replace(source, destination)

    def fail_permissions(target, *, directory):
        if fail_at == "permissions" and target.parent.name == "copies":
            raise PermissionError("injected permission failure")
        return original_permissions(target, directory=directory)

    capsys.readouterr()
    with monkeypatch.context() as patch:
        patch.setattr(module, "_replace_private", fail_replace)
        patch.setattr(module, "_owner_only", fail_permissions)
        with pytest.raises(PermissionError):
            module.cmd_accept(args(path), root)
    assert record_path.read_bytes() == old_record
    assert old_copy.read_bytes() == old_bytes
    assert list((root / "copies").iterdir()) == [old_copy]
    assert "accepted:" not in capsys.readouterr().out
    assert module.cmd_check(args(path), root) == module.EXIT_CHANGED
    assert module.cmd_diff(args(path), root) == 0
    assert "+user change" in capsys.readouterr().out
    assert module.cmd_accept(args(path), root) == 0
    latest = module.load_record(root, key)
    assert latest["seq"] == 2 and "diffed" not in latest
    assert module._copy_path(root, key, latest).read_bytes() == path.read_bytes()
    assert old_copy.exists()
    assert module.cmd_check(args(path), root) == 0


def test_failed_commit_can_retry_without_consuming_diff(guard, monkeypatch):
    module, root, _ = guard
    path, key, record_path, old_record, _old_copy, _old_bytes = reviewed(guard)
    with monkeypatch.context() as patch:
        patch.setattr(
            module,
            "save_record",
            lambda *a: (_ for _ in ()).throw(OSError("failed commit")),
        )
        with pytest.raises(OSError):
            module.cmd_accept(args(path), root)
    assert record_path.read_bytes() == old_record
    assert module.cmd_accept(args(path), root) == 0
    assert module.load_record(root, key)["seq"] == 2


@pytest.mark.parametrize("phase", ["before-copy", "during-copy", "after-copy"])
def test_accept_never_rebaselines_new_unreviewed_content(guard, monkeypatch, phase):
    module, root, _ = guard
    path, _key, record_path, old_record, old_copy, old_bytes = reviewed(guard)
    if phase == "before-copy":
        original_record = module.cmd_record

        def changed_before_record(*a, **kw):
            path.write_text("new unreviewed change\n", encoding="utf-8")
            return original_record(*a, **kw)

        monkeypatch.setattr(module, "cmd_record", changed_before_record)
    else:
        original_copy = module.shutil.copyfile

        def changed_during_copy(source, destination):
            if phase == "during-copy":
                path.write_text("new unreviewed change\n", encoding="utf-8")
            result = original_copy(source, destination)
            if phase == "after-copy":
                path.write_text("new unreviewed change\n", encoding="utf-8")
            return result

        monkeypatch.setattr(module.shutil, "copyfile", changed_during_copy)
    assert module.cmd_accept(args(path), root) == module.EXIT_CHANGED
    assert record_path.read_bytes() == old_record
    assert old_copy.read_bytes() == old_bytes
    assert list((root / "copies").iterdir()) == [old_copy]


@pytest.mark.parametrize(
    "name",
    ["../escape", "/absolute", "0" * 64 + "." + "1" * 32 + ".bin", 123, "", None],
)
def test_snapshot_reference_cannot_escape_or_cross_keys(guard, name):
    module, root, work = guard
    path = work / "notes.md"
    key = module.key_for(path)
    with pytest.raises(module.GuardError):
        module._copy_path(root, key, {"copy_name": name})


def test_legacy_copy_remains_readable_and_migrates_on_accept(guard, capsys):
    module, root, _ = guard
    path, key, _record_path, old_record, old_copy, _old_bytes = reviewed(guard)
    record = json.loads(old_record)
    record.pop("copy_name")
    record["copy"] = True
    legacy = root / "copies" / f"{key}.bin"
    old_copy.rename(legacy)
    module.save_record(root, key, record)
    capsys.readouterr()
    assert module.cmd_diff(args(path), root) == 0
    assert "+user change" in capsys.readouterr().out
    assert module.cmd_accept(args(path), root) == 0
    assert legacy.exists()
    assert module.load_record(root, key)["copy_name"].startswith(key + ".")


@pytest.mark.parametrize(
    "winerror,windows,expected",
    [(5, True, 5), (5, False, 1), (32, True, 1), (None, True, 1)],
)
def test_permanent_or_unrelated_replace_error_is_never_success(
    guard, monkeypatch, winerror, windows, expected
):
    module, _root, _ = guard
    calls, delays = [], []
    error = PermissionError("injected persistent failure")
    if winerror is not None:
        error.winerror = winerror

    def replace(source, target):
        calls.append((source, target))
        raise error

    monkeypatch.setattr(
        module,
        "os",
        SimpleNamespace(name="nt" if windows else "posix", replace=replace),
    )
    monkeypatch.setattr(module.time, "sleep", delays.append)
    with pytest.raises(PermissionError) as caught:
        module._replace_private(Path("staging"), Path("target"))
    assert caught.value is error and len(calls) == expected
    assert sum(delays) <= 0.150000001


def test_transient_replace_retries_identical_prepared_bytes(guard, monkeypatch):
    module, root, _ = guard
    source, destination = root / "staged", root / "target"
    source.write_bytes(b"prepared bytes")
    destination.write_bytes(b"old bytes")
    real_replace = os.replace
    calls, delays = [], []

    def replace(staged, target):
        calls.append((staged, target))
        assert source.read_bytes() == b"prepared bytes"
        assert destination.read_bytes() == b"old bytes"
        if len(calls) < 3:
            error = PermissionError("injected Windows contention")
            error.winerror = 5
            raise error
        real_replace(staged, target)

    monkeypatch.setattr(module, "os", SimpleNamespace(name="nt", replace=replace))
    monkeypatch.setattr(module.time, "sleep", delays.append)
    module._replace_private(source, destination)
    assert len(calls) == 3 and delays == [0.01, 0.02]
    assert destination.read_bytes() == b"prepared bytes"


def test_orphan_retention_keeps_live_and_fresh_snapshots(guard):
    module, root, _ = guard
    _path, key, _record_path, _old_record, old_copy, _old_bytes = reviewed(guard)
    stale = root / "copies" / f"{key}.{'a' * 32}.bin"
    fresh = root / "copies" / f"{key}.{'b' * 32}.bin"
    stale.write_bytes(b"orphan")
    fresh.write_bytes(b"fresh")
    old_time = module.now().timestamp() - 31 * 86400
    os.utime(stale, (old_time, old_time))
    os.utime(old_copy, (old_time, old_time))
    module.prune(root)
    assert not stale.exists() and fresh.exists() and old_copy.exists()
    module._delete(root, key)
    assert not list((root / "copies").iterdir())


def test_copy_cap_transition_publishes_no_copy_only_after_commit(guard, monkeypatch):
    module, root, _ = guard
    path, key, record_path, old_record, old_copy, old_bytes = reviewed(guard)
    monkeypatch.setattr(module, "COPY_CAP_BYTES", 1)
    with monkeypatch.context() as patch:
        patch.setattr(
            module,
            "save_record",
            lambda *a: (_ for _ in ()).throw(OSError("injected commit failure")),
        )
        with pytest.raises(OSError):
            module.cmd_accept(args(path), root)
    assert record_path.read_bytes() == old_record and old_copy.read_bytes() == old_bytes
    assert module.cmd_accept(args(path), root) == 0
    record = module.load_record(root, key)
    assert record["copy"] is False and "copy_name" not in record
    assert list((root / "copies").iterdir()) == [old_copy]


def test_office_snapshot_uses_original_content_fingerprint(guard):
    import zipfile

    module, root, work = guard
    path = work / "deck.pptx"

    def write_slide(text):
        with zipfile.ZipFile(path, "w") as archive:
            archive.writestr("[Content_Types].xml", "<Types/>")
            archive.writestr(
                "ppt/slides/slide1.xml", f"<p:sld><a:t>{text}</a:t></p:sld>"
            )

    write_slide("baseline")
    assert module.cmd_record(args(path), root) == 0
    write_slide("reviewed user edit")
    assert module.cmd_diff(args(path), root) == 0
    assert module.cmd_accept(args(path), root) == 0
    key = module.key_for(path)
    record = module.load_record(root, key)
    assert record["kind"] == "office"
    snapshot = module._copy_path(root, key, record)
    assert (
        module.fingerprint(snapshot, suffix=path.suffix)["sha256"] == record["sha256"]
    )
    assert module.cmd_check(args(path), root) == 0


def test_purge_all_removes_fresh_orphan_and_staging_without_records(guard):
    module, root, work = guard
    key = module.key_for(work / "unrecorded.md")
    names = [f"{key}.{'a' * 32}.bin", f".{key}.{'b' * 32}.bin.123.tmp", f"{key}.bin"]
    for name in names:
        (root / "copies" / name).write_bytes(b"private orphan")
    unrelated = root / "copies" / "unrelated"
    unrelated.write_bytes(b"keep")
    assert module.cmd_purge(SimpleNamespace(path=None), root) == 0
    assert list((root / "copies").iterdir()) == [unrelated]


def test_purge_path_keeps_other_keys_and_removes_own_staging(guard):
    module, root, work = guard
    path = work / "unrecorded.md"
    key = module.key_for(path)
    other = module.key_for(work / "other.md")
    for selected in (key, other):
        for name in (
            f"{selected}.{'a' * 32}.bin",
            f".{selected}.{'b' * 32}.bin.123.tmp",
        ):
            (root / "copies" / name).write_bytes(b"private orphan")
    assert module.cmd_purge(args(path), root) == 0
    assert len(list((root / "copies").iterdir())) == 2
    assert all(other in item.name for item in (root / "copies").iterdir())


def test_stale_check_metadata_still_references_a_readable_snapshot(guard, monkeypatch):
    module, root, _ = guard
    path, key, _record_path, _old_record, _old_copy, _old_bytes = reviewed(guard)
    assert module.cmd_accept(args(path), root) == 0
    active = module._copy_path(root, key, module.load_record(root, key))
    aged = module.now().timestamp() - 31 * 86400
    os.utime(active, (aged, aged))
    original_save = module.save_record
    original_fingerprint = module.fingerprint
    interleaved = False

    def save_after_new_record(store, selected_key, record):
        nonlocal interleaved
        if "clean_check" in record and not interleaved:
            interleaved = True
            path.write_text("second generation during check\n", encoding="utf-8")
            force_args = args(path)
            force_args.force = True
            assert module.cmd_record(force_args, root) == 0
            module.prune(root)
        return original_save(store, selected_key, record)

    monkeypatch.setattr(module, "save_record", save_after_new_record)
    check_args = args(path)
    check_args.stamp = True
    assert module.cmd_check(check_args, root) == 0
    record = module.load_record(root, key)
    snapshot = module._copy_path(root, key, record)
    assert snapshot.is_file()
    assert original_fingerprint(snapshot)["sha256"] == record["sha256"]
    assert module.cmd_check(args(path), root) == module.EXIT_CHANGED


def test_repeated_unchanged_reads_reuse_snapshot(guard):
    module, root, work = guard
    path = work / "notes.md"
    path.write_text("unchanged baseline\n", encoding="utf-8")
    for _ in range(10):
        assert module.cmd_record(args(path), root) == 0
    assert len(list((root / "copies").iterdir())) == 1


def test_cli_reports_permanent_publication_failure_without_accept_success(
    guard, monkeypatch, capsys
):
    module, _root, _ = guard
    path, _key, record_path, old_record, old_copy, old_bytes = reviewed(guard)
    monkeypatch.setattr(
        module,
        "_replace_private",
        lambda *a: (_ for _ in ()).throw(
            PermissionError("injected permanent write failure")
        ),
    )
    capsys.readouterr()
    assert module.main(["accept", str(path)]) == module.EXIT_ERROR
    captured = capsys.readouterr()
    assert "error:" in captured.err and "accepted:" not in captured.out
    assert record_path.read_bytes() == old_record and old_copy.read_bytes() == old_bytes


def test_corrupt_snapshot_is_refused_even_when_source_is_unchanged(
    guard, monkeypatch, capsys
):
    module, root, _ = guard
    path, _key, record_path, old_record, old_copy, old_bytes = reviewed(guard)
    reviewed_bytes = path.read_bytes()
    original_copy = module.shutil.copyfile

    def corrupt_copy(source, destination):
        result = original_copy(source, destination)
        Path(destination).write_bytes(b"corrupted private snapshot")
        return result

    monkeypatch.setattr(module.shutil, "copyfile", corrupt_copy)
    capsys.readouterr()
    assert module.cmd_accept(args(path), root) == module.EXIT_CHANGED
    assert path.read_bytes() == reviewed_bytes
    assert record_path.read_bytes() == old_record and old_copy.read_bytes() == old_bytes
    assert list((root / "copies").iterdir()) == [old_copy]
    assert "accepted:" not in capsys.readouterr().out
    entries = [
        json.loads(line)
        for line in (root / "log.jsonl").read_text(encoding="utf-8").splitlines()
    ]
    assert not any(item["event"] == "accept" for item in entries)


def test_prune_removes_aged_orphan_without_record(guard):
    module, root, work = guard
    key = module.key_for(work / "unrecorded.md")
    copy = root / "copies" / f"{key}.{'a' * 32}.bin"
    staging = root / "copies" / f".{key}.{'b' * 32}.bin.123.tmp"
    old_time = module.now().timestamp() - 31 * 86400
    legacy = root / "copies" / f"{key}.bin"
    legacy_staging = root / "copies" / f".{key}.bin.123.tmp"
    for item in (copy, staging, legacy, legacy_staging):
        item.write_bytes(b"abandoned private data")
        os.utime(item, (old_time, old_time))
    module.prune(root)
    assert all(not item.exists() for item in (copy, staging, legacy, legacy_staging))


def test_failed_metadata_commit_preserves_a_reused_snapshot(guard, monkeypatch):
    module, root, work = guard
    path = work / "notes.md"
    path.write_text("unchanged baseline\n", encoding="utf-8")
    assert module.cmd_record(args(path), root) == 0
    key = module.key_for(path)
    record_path = root / "records" / f"{key}.json"
    before = record_path.read_bytes()
    snapshot = module._copy_path(root, key, module.load_record(root, key))
    snapshot_bytes = snapshot.read_bytes()
    with monkeypatch.context() as patch:
        patch.setattr(
            module,
            "save_record",
            lambda *a: (_ for _ in ()).throw(
                OSError("injected unchanged commit failure")
            ),
        )
        with pytest.raises(OSError):
            module.cmd_record(args(path), root)
    assert record_path.read_bytes() == before
    assert snapshot.read_bytes() == snapshot_bytes
    assert module.cmd_check(args(path), root) == 0


def test_no_copy_transition_does_not_erase_a_concurrent_new_generation(
    guard, monkeypatch
):
    module, root, _ = guard
    path, key, _record_path, _old_record, _old_copy, _old_bytes = reviewed(guard)
    original_save = module.save_record
    original_cap = module.COPY_CAP_BYTES
    entered = False

    def interleave_after_no_copy(store, selected, record):
        nonlocal entered
        result = original_save(store, selected, record)
        if record["copy"] is False and not entered:
            entered = True
            module.COPY_CAP_BYTES = original_cap
            path.write_text("concurrent new baseline\n", encoding="utf-8")
            force_args = args(path)
            force_args.force = True
            assert module.cmd_record(force_args, root) == 0
        return result

    monkeypatch.setattr(module, "save_record", interleave_after_no_copy)
    monkeypatch.setattr(module, "COPY_CAP_BYTES", 1)
    assert module.cmd_accept(args(path), root) == 0
    record = module.load_record(root, key)
    assert entered and record["copy"] is False and "copy_name" in record
    snapshot = module._copy_path(root, key, record)
    assert snapshot.is_file()
    assert module.fingerprint(snapshot)["sha256"] == record["sha256"]


def test_prune_observes_retirement_grace_after_loading_new_pointer(guard, monkeypatch):
    module, root, _ = guard
    path, key, _record_path, old_record, old_copy, old_bytes = reviewed(guard)
    aged = module.now().timestamp() - 31 * 86400
    os.utime(old_copy, (aged, aged))
    original_load = module.load_record
    interleaved = False

    def retire_on_pointer_lookup(store, selected):
        nonlocal interleaved
        if selected == key and not interleaved:
            interleaved = True
            force_args = args(path)
            force_args.force = True
            assert module.cmd_record(force_args, root) == 0
        return original_load(store, selected)

    with monkeypatch.context() as patch:
        patch.setattr(module, "load_record", retire_on_pointer_lookup)
        module.prune(root)
    assert interleaved and old_copy.read_bytes() == old_bytes
    module.save_record(root, key, json.loads(old_record))
    assert (
        module._copy_path(root, key, module.load_record(root, key)).read_bytes()
        == old_bytes
    )
    assert module.cmd_check(args(path), root) == module.EXIT_CHANGED


@pytest.mark.parametrize("live_legacy", [False, True])
def test_legacy_snapshot_retention_distinguishes_live_and_retired(guard, live_legacy):
    module, root, _ = guard
    _path, key, _record_path, old_record, old_copy, old_bytes = reviewed(guard)
    legacy = root / "copies" / f"{key}.bin"
    if live_legacy:
        old_copy.rename(legacy)
        record = json.loads(old_record)
        record.pop("copy_name")
        record["copy"] = True
        module.save_record(root, key, record)
    else:
        legacy.write_bytes(old_bytes)
    old_time = module.now().timestamp() - 31 * 86400
    os.utime(legacy, (old_time, old_time))
    module.prune(root)
    assert legacy.exists() is live_legacy
    record = module.load_record(root, key)
    assert module._copy_path(root, key, record).read_bytes() == old_bytes


def test_generation_metadata_never_exposes_stale_legacy_bytes_to_old_readers(
    guard, capsys
):
    module, root, work = guard
    path = work / "notes.md"
    path.write_text("approved A\n", encoding="utf-8")
    assert module.cmd_record(args(path), root) == 0
    key = module.key_for(path)
    # A fixed-file legacy baseline remains available to an older installed helper.
    legacy = root / "copies" / f"{key}.bin"
    legacy.write_bytes(path.read_bytes())
    path.write_text("approved B\n", encoding="utf-8")
    assert module.cmd_diff(args(path), root) == 0
    assert module.cmd_accept(args(path), root) == 0
    record = module.load_record(root, key)
    assert record["copy"] is False and "copy_name" in record
    assert module._has_copy(root, key, record)
    path.write_text("approved A\n", encoding="utf-8")
    # The legacy serialized contract only recognizes copy=True and the fixed filename.
    legacy_copy = legacy if record.get("copy") else None
    legacy_output = module.render_diff(
        path, record, module.fingerprint(path), legacy_copy
    )
    assert "no stored copy" in legacy_output
    capsys.readouterr()
    assert module.cmd_diff(args(path), root) == 0
    output = capsys.readouterr().out
    assert "-approved B" in output and "+approved A" in output


def test_generation_reader_accepts_a_subsequent_legacy_writer_record(guard, capsys):
    module, root, work = guard
    path = work / "notes.md"
    path.write_text("approved B\n", encoding="utf-8")
    assert module.cmd_record(args(path), root) == 0
    key = module.key_for(path)
    record = module.load_record(root, key)
    (root / "copies" / f"{key}.bin").write_bytes(path.read_bytes())
    record.pop("copy_name")
    record["copy"] = True
    module.save_record(root, key, record)
    path.write_text("approved A\n", encoding="utf-8")
    capsys.readouterr()
    assert module.cmd_diff(args(path), root) == 0
    output = capsys.readouterr().out
    assert "-approved B" in output and "+approved A" in output


@pytest.fixture
def conflict_detector():
    """Load only the detector; these suffix cases need no store or native guard call."""
    spec = importlib.util.spec_from_file_location("conflict_detector_guard", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.open_or_conflicting


@pytest.mark.parametrize("name, suffix", [
    ("claude-opus-4-5.md", "20251101"),
    ("model.md", "123"),
    ("model.md", "0003"),
])
def test_numeric_suffix_is_not_a_generic_machine_conflict(tmp_path, monkeypatch, conflict_detector, name, suffix):
    monkeypatch.setenv("COMPUTERNAME", "WORKSTATION")
    path = tmp_path / name
    path.write_text("published profile\n", encoding="utf-8")
    sibling = path.with_name(f"{path.stem}-{suffix}{path.suffix}")
    sibling.write_text("published dated or versioned profile\n", encoding="utf-8")
    assert conflict_detector(path) == []
    assert path.read_text(encoding="utf-8") == "published profile\n"
    assert sibling.read_text(encoding="utf-8") == "published dated or versioned profile\n"


@pytest.mark.parametrize("suffix", ["MACHINE", "ABC123", "DESKTOP-4F2A9C", "ABC-123"])
def test_machine_suffix_still_means_conflicting(tmp_path, monkeypatch, conflict_detector, suffix):
    monkeypatch.setenv("COMPUTERNAME", "OTHERHOST")
    path = tmp_path / "profile.md"
    path.write_text("baseline\n", encoding="utf-8")
    sibling = tmp_path / f"profile-{suffix}.md"
    sibling.write_text("conflicting copy\n", encoding="utf-8")
    assert conflict_detector(path) == [f"conflict copy {sibling.name}"]


@pytest.mark.parametrize("computer, suffix", [
    ("20251101", "20251101"), ("123", "123"), ("realMACHINE", "realmACHINE"),
])
def test_exact_local_suffix_still_blocks_including_numeric(tmp_path, monkeypatch, conflict_detector, computer, suffix):
    monkeypatch.setenv("COMPUTERNAME", computer)
    path = tmp_path / "profile.md"
    path.write_text("baseline\n", encoding="utf-8")
    sibling = tmp_path / f"profile-{suffix}.md"
    sibling.write_text("local conflict\n", encoding="utf-8")
    assert conflict_detector(path) == [f"conflict copy {sibling.name}"]


@pytest.mark.parametrize("lock_name", ["~$deck.pptx", "~$ck.pptx"])
def test_office_lock_still_blocks_beside_numeric_suffix(tmp_path, monkeypatch, conflict_detector, lock_name):
    monkeypatch.setenv("COMPUTERNAME", "WORKSTATION")
    path = tmp_path / "deck.pptx"
    path.write_bytes(b"detector checks filenames only")
    (tmp_path / "deck-20251101.pptx").write_bytes(b"dated sibling")
    (tmp_path / lock_name).write_bytes(b"lock")
    assert conflict_detector(path) == [f"lock file {lock_name}"]


def test_numeric_suffix_does_not_waive_missing_record_or_changed_bytes(guard, monkeypatch, capsys):
    module, root, work = guard
    monkeypatch.setenv("COMPUTERNAME", "WORKSTATION")
    path = work / "claude-opus-4-5.md"
    path.write_text("original profile\n", encoding="utf-8")
    sibling = work / "claude-opus-4-5-20251101.md"
    sibling.write_text("dated profile\n", encoding="utf-8")
    assert module.cmd_check(args(path), root) == module.EXIT_NO_RECORD
    assert module.cmd_record(args(path), root) == module.EXIT_OK
    key = module.key_for(path)
    record_path = root / "records" / f"{key}.json"
    baseline_record = record_path.read_bytes()
    assert module.cmd_check(args(path), root) == module.EXIT_OK
    capsys.readouterr()
    path.write_text("user changed profile\n", encoding="utf-8")
    assert module.cmd_check(args(path), root) == module.EXIT_CHANGED
    observed = capsys.readouterr().out
    assert "differs from the agent's last-known state" in observed
    assert "open or conflicting copy" not in observed
    assert record_path.read_bytes() == baseline_record
    assert path.read_text(encoding="utf-8") == "user changed profile\n"
    assert sibling.read_text(encoding="utf-8") == "dated profile\n"
