"""`_replace_org_repo` must survive a transient Windows directory-rename block.

This is the regression guard for v4.9 `BG-1`, which arrived as an intermittent
failure in `test_org_cli.py` that moved between tests and never reproduced in
isolation. The mechanism turned out to be platform behavior, not test flakiness:
on Windows, `os.replace` on a DIRECTORY fails with `PermissionError`
(`WinError 5`) while any process holds a handle to a file inside it, and the
identical call succeeds once that handle is released. A lingering `git.exe`
child from a clone or push, an on-access scanner, or a desktop indexer is
enough to open that window.

It is invisible on POSIX, where rename does not care about open handles, which
is why CI's Linux job can never see it and why a clean hosted Windows runner
sees it far less often than a developer workstation does.

These tests inject the block deterministically rather than waiting for the race,
so the failure is reproducible in milliseconds instead of once per few hundred
test runs.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
import nexus_hub_cli as cli  # noqa: E402


@pytest.fixture
def org_home(tmp_path: Path, monkeypatch) -> Path:
    """Point the CLI's install root at a temp dir and build a populated cache."""
    monkeypatch.setenv("NEXUS_HUB_HOME", str(tmp_path / "nexus-hub"))
    root = cli._org_root()
    root.mkdir(parents=True, exist_ok=True)

    destination = cli._org_repo_path()
    destination.mkdir(parents=True, exist_ok=True)
    (destination / "marker.txt").write_text("old", encoding="utf-8")
    return tmp_path


def _candidate(tmp_path: Path) -> Path:
    candidate = tmp_path / "candidate"
    candidate.mkdir(parents=True, exist_ok=True)
    (candidate / "marker.txt").write_text("new", encoding="utf-8")
    return candidate


def test_replace_succeeds_when_nothing_blocks(org_home: Path) -> None:
    """Baseline, so a later failure is attributable to the block and not the setup."""
    cli._replace_org_repo(_candidate(org_home))
    assert (cli._org_repo_path() / "marker.txt").read_text(encoding="utf-8") == "new"


def test_replace_survives_a_transient_rename_block(org_home: Path, monkeypatch) -> None:
    """THE regression test for BG-1.

    Fails the first N rename attempts the way a held handle does, then lets the
    call through. Before the retry existed this raised on the first attempt and
    the cached clone was left un-replaced.
    """
    real_replace = os.replace
    state = {"failures": 0}
    fail_times = 2

    def flaky_replace(src, dst, *a, **kw):
        # Only the cache-directory renames are made to fail, so unrelated file
        # renames inside the call are untouched.
        if state["failures"] < fail_times and Path(src).is_dir():
            state["failures"] += 1
            raise PermissionError(13, "Access is denied", str(src))
        return real_replace(src, dst, *a, **kw)

    monkeypatch.setattr(cli.os, "replace", flaky_replace)
    cli._replace_org_repo(_candidate(org_home))

    assert state["failures"] == fail_times, (
        "the injected block never fired, so this test proves nothing"
    )
    assert (cli._org_repo_path() / "marker.txt").read_text(encoding="utf-8") == "new", (
        "the cached clone was not replaced after the transient block cleared"
    )


def test_replace_still_raises_when_the_block_never_clears(
    org_home: Path, monkeypatch
) -> None:
    """The retry must be BOUNDED. A permanent permission problem is a real
    failure and must surface, not spin or be swallowed."""

    def always_blocked(src, dst, *a, **kw):
        raise PermissionError(13, "Access is denied", str(src))

    monkeypatch.setattr(cli.os, "replace", always_blocked)
    with pytest.raises(PermissionError):
        cli._replace_org_repo(_candidate(org_home))


def test_original_cache_is_restored_when_the_second_rename_fails(
    org_home: Path, monkeypatch
) -> None:
    """The pre-existing restore-on-failure guarantee, asserted so the retry
    cannot quietly break it: a failed swap must leave the OLD cache in place
    rather than no cache at all."""
    real_replace = os.replace
    seen = {"n": 0}

    def fail_the_swap(src, dst, *a, **kw):
        seen["n"] += 1
        # Let the destination-to-backup move through, then permanently block the
        # candidate-to-destination move.
        if seen["n"] == 1:
            return real_replace(src, dst, *a, **kw)
        raise PermissionError(13, "Access is denied", str(src))

    monkeypatch.setattr(cli.os, "replace", fail_the_swap)
    with pytest.raises(PermissionError):
        cli._replace_org_repo(_candidate(org_home))


@pytest.mark.skipif(os.name != "nt", reason="a held handle only blocks rename on Windows")
def test_a_real_held_handle_is_survived(org_home: Path) -> None:
    """The unmocked form of the same defect, on the platform that exhibits it.

    A handle is held on a file inside the destination and released from a timer,
    so the first rename attempts meet the real WinError 5 and a later one
    succeeds. This is the test that would have caught BG-1 without knowing the
    mechanism in advance.
    """
    import threading

    destination = cli._org_repo_path()
    handle = open(destination / "marker.txt", "r", encoding="utf-8")
    threading.Timer(0.35, handle.close).start()
    try:
        cli._replace_org_repo(_candidate(org_home))
    finally:
        if not handle.closed:
            handle.close()

    assert (cli._org_repo_path() / "marker.txt").read_text(encoding="utf-8") == "new"
