"""Untrusted references are rejected lexically before filesystem or network access."""

import os
from pathlib import Path

import pytest

from .test_historical_authority import recovery as recovery
from .test_check_plan_completion import _isolated_git_config  # noqa: F401
from .test_completion_minor_record import _no_transport_overrides  # noqa: F401
from .test_owner_retirement import owner_scope as owner_scope, grant
import check_plan_completion as ck
import completion_minor as cm


@pytest.mark.parametrize("target", ["owner", "manifest", "traversal"])
def test_unowned_reference_causes_no_target_filesystem_access(
    recovery, monkeypatch, target
):
    repo, current, request = recovery
    outside = (
        Path("//untrusted.invalid/share") if os.name == "nt" else repo.tmp / "unowned"
    ) / ("0" * 64 + ".json")
    assert outside.is_absolute()
    if target == "traversal":
        outside = repo.runs.parent / "requests" / ".." / "outside.json"
    original_link, original_resolve, original_stat, original_read = (
        Path.is_symlink,
        Path.resolve,
        Path.stat,
        Path.read_bytes,
    )

    def forbidden(path):
        return path == outside or path == outside.parent or ".." in path.parts

    def link(path):
        assert not forbidden(path), "untrusted link query reached the filesystem"
        return original_link(path)

    def resolve(path, *a, **kw):
        assert not forbidden(path), "untrusted path resolution reached the filesystem"
        return original_resolve(path, *a, **kw)

    def stat(path, *a, **kw):
        assert not forbidden(path), "untrusted stat reached the filesystem"
        return original_stat(path, *a, **kw)

    def read(path):
        assert not forbidden(path), "untrusted read reached the filesystem"
        return original_read(path)

    monkeypatch.setattr(Path, "is_symlink", link)
    monkeypatch.setattr(Path, "resolve", resolve)
    monkeypatch.setattr(Path, "stat", stat)
    monkeypatch.setattr(Path, "read_bytes", read)
    original_junction = getattr(Path, "is_junction", None)

    def junction(path):
        assert not forbidden(path), "untrusted junction query reached the filesystem"
        return original_junction(path) if original_junction else False

    monkeypatch.setattr(Path, "is_junction", junction, raising=False)
    with pytest.raises(AssertionError, match="untrusted link query"):
        outside.is_symlink()
    with pytest.raises(ValueError):
        if target == "owner":
            cm.validate_owner_record(
                ck,
                repo.rctx(),
                current,
                {
                    "path": str(outside),
                    "sha256": "0" * 64,
                    "minor": "v0.4",
                    "nonce": "unknown",
                    "members": ["v0.4.0"],
                },
            )
        else:
            request["manifest"]["path"] = str(outside)
            cm.historical_scope_request(ck, repo.rctx(), current, request)


def test_oversized_owner_record_is_not_read(recovery, monkeypatch):
    repo, current, _request = recovery
    target = repo.runs / ("0" * 64 + ".json")
    target.write_bytes(b" " * 1_000_001)
    original = Path.read_bytes

    def read(path):
        assert path != target, (
            "oversized control record was read before its bound was checked"
        )
        return original(path)

    monkeypatch.setattr(Path, "read_bytes", read)
    with pytest.raises(ValueError, match="bounded local record"):
        cm.validate_owner_record(
            ck,
            repo.rctx(),
            current,
            {
                "path": str(target),
                "sha256": "0" * 64,
                "minor": "v0.4",
                "nonce": "unknown",
                "members": ["v0.4.0"],
            },
        )


def test_private_reparse_detection_uses_local_attributes(tmp_path, monkeypatch):
    import stat
    from types import SimpleNamespace

    target = tmp_path / "local-entry"
    original = Path.lstat

    def metadata(path):
        if path == target:
            return SimpleNamespace(st_mode=stat.S_IFDIR, st_file_attributes=0x400)
        return original(path)

    monkeypatch.setattr(Path, "lstat", metadata)
    assert ck._private_reparse(target)


@pytest.mark.parametrize("route", ["validation", "native-recovery"])
def test_archived_owner_reparse_is_refused_before_following(
    owner_scope, monkeypatch, route
):
    import stat
    from types import SimpleNamespace

    repo, args, spec, raw, _plan, dest = grant(owner_scope)
    ck._retire(Path(spec["path"]), destination=dest)
    original_lstat, original_stat, original_read = (
        Path.lstat, Path.stat, Path.read_bytes
    )

    def metadata(path):
        if path == dest:
            return SimpleNamespace(st_mode=stat.S_IFREG, st_file_attributes=0x400)
        return original_lstat(path)

    def follow(path, *a, **kw):
        assert path != dest, "redirected archive was followed"
        return original_stat(path, *a, **kw)

    def read(path):
        assert path != dest, "redirected archive was read"
        return original_read(path)

    monkeypatch.setattr(Path, "lstat", metadata)
    monkeypatch.setattr(Path, "stat", follow)
    monkeypatch.setattr(Path, "read_bytes", read)
    with pytest.raises(AssertionError, match="redirected archive was followed"):
        dest.stat()
    if route == "validation":
        with pytest.raises(ValueError, match="redirected"):
            cm.validate_owner_record(ck, repo.rctx(), repo.record(), spec, archived=dest)
    else:
        assert cm.cmd_record_retire_owner(ck, args) == ck.EXIT_BLOCKED
    assert original_read(dest) == raw
    assert not Path(spec["path"]).exists()
