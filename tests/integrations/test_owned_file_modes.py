"""File modes for the owned-file writer (v4.8 WN-K).

`_atomic_replace_bytes` stages content beside the destination and renames it
into place. Two properties govern the staging file's mode, and both were
defects before this test existed:

1. The staging file was created with `0o666`, which is `0o666 & ~umask` in
   practice. On a host with `umask 000` that is a WORLD-WRITABLE file sitting in
   the user's config directory for the window between creation and the rename,
   in code that ships in `scripts/` and runs during a user's install. CodeQL
   flagged it as `py/overly-permissive-file`.
2. `os.replace` carries the SOURCE's mode, so a refresh silently rewrote the
   permissions of a destination the user may have chmod'ed deliberately.

The sibling implementation in `scripts/lib/installer/instruction_merge.py`
already got both right (it stats the destination and reapplies its mode); this
copy had simply not adopted the convention.

**These assertions spy on `os.open` / `os.chmod` rather than reading back
`stat().st_mode`, deliberately.** On Windows `stat.S_IMODE` reflects only the
read-only bit and reports `0o666` for any writable file, so a mode-readback
test would be vacuous on one of the two operating systems this project
supports and would have "passed" against the original defect.
"""

from __future__ import annotations

import os
import stat
from pathlib import Path

import pytest

from scripts.lib.integrations._owned import _STAGING_MODE, _atomic_replace_bytes


@pytest.fixture
def spy(monkeypatch):
    """Record the mode argument of every os.open / os.chmod call."""
    calls: dict[str, list[int]] = {"open": [], "chmod": []}
    real_open, real_chmod = os.open, os.chmod

    def spy_open(path, flags, mode=0o777, *a, **kw):
        calls["open"].append(mode)
        return real_open(path, flags, mode, *a, **kw)

    def spy_chmod(path, mode, *a, **kw):
        calls["chmod"].append(mode)
        return real_chmod(path, mode, *a, **kw)

    monkeypatch.setattr(os, "open", spy_open)
    monkeypatch.setattr(os, "chmod", spy_chmod)
    return calls


def test_staging_mode_is_owner_only() -> None:
    """The constant itself, so the intent survives a refactor of the caller."""
    assert _STAGING_MODE == 0o600
    assert not _STAGING_MODE & (stat.S_IWGRP | stat.S_IWOTH), (
        "the staging file must not be group- or world-writable under any umask"
    )


def test_new_file_is_staged_owner_only(tmp_path: Path, spy) -> None:
    dst = tmp_path / "fresh.md"
    _atomic_replace_bytes(dst, b"hello")

    assert dst.read_bytes() == b"hello"
    assert spy["open"], "os.open was never called; the spy is not wired"
    for mode in spy["open"]:
        assert not mode & (stat.S_IWGRP | stat.S_IWOTH), (
            f"staging file opened with a group/world-writable mode {oct(mode)}"
        )
    assert not spy["chmod"], (
        "a brand-new file has no destination mode to preserve, so it should keep "
        "the restrictive staging mode rather than be widened"
    )


def test_existing_destination_mode_is_preserved(tmp_path: Path, spy) -> None:
    """A user who chmod'ed their file keeps that mode across a refresh."""
    dst = tmp_path / "existing.md"
    dst.write_bytes(b"before")
    target_mode = stat.S_IMODE(dst.stat().st_mode)

    _atomic_replace_bytes(dst, b"after")

    assert dst.read_bytes() == b"after"
    assert spy["chmod"] == [target_mode], (
        "the destination's own mode must be reapplied to the staging file before "
        f"the rename; expected {[oct(target_mode)]}, got {[oct(m) for m in spy['chmod']]}"
    )


def test_umask_cannot_widen_the_staging_file(tmp_path: Path, spy) -> None:
    """The regression that mattered: 0o666 under umask 000 was world-writable.

    Asserted on the requested mode rather than the resulting one, because the
    kernel applies the umask and Windows ignores the mode entirely.
    """
    previous = os.umask(0o000)
    try:
        _atomic_replace_bytes(tmp_path / "under-open-umask.md", b"x")
    finally:
        os.umask(previous)

    assert spy["open"], "os.open was never called"
    assert all(m == _STAGING_MODE for m in spy["open"]), (
        f"expected every staging open at {oct(_STAGING_MODE)}, got "
        f"{[oct(m) for m in spy['open']]}"
    )


def test_no_staging_file_survives_a_successful_write(tmp_path: Path) -> None:
    _atomic_replace_bytes(tmp_path / "clean.md", b"x")
    leftovers = [p.name for p in tmp_path.iterdir() if p.name.startswith(".")]
    assert not leftovers, f"staging files left behind: {leftovers}"


def test_no_staging_file_survives_a_failed_write(tmp_path: Path, monkeypatch) -> None:
    """The finally-clause guarantee. A staging file left in a config directory
    is both confusing and, before this fix, a permissive one."""
    dst = tmp_path / "boom.md"

    def explode(*_a, **_kw):
        raise OSError("simulated rename failure")

    monkeypatch.setattr(os, "replace", explode)
    with pytest.raises(OSError):
        _atomic_replace_bytes(dst, b"x")

    leftovers = [p.name for p in tmp_path.iterdir() if p.name.startswith(".")]
    assert not leftovers, f"staging files left behind after a failure: {leftovers}"


def test_sibling_implementation_still_preserves_mode() -> None:
    """Cross-check the convention this fix adopted, so the two copies cannot
    silently diverge again in the other direction."""
    source = (
        Path(__file__).resolve().parents[2]
        / "scripts"
        / "lib"
        / "installer"
        / "instruction_merge.py"
    ).read_text(encoding="utf-8")
    body = source.split("def _atomic_replace_bytes", 1)[1].split("\ndef ", 1)[0]
    assert "stat().st_mode" in body or "st_mode" in body
    assert "os.chmod" in body
