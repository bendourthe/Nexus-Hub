"""Tests for the append-only fixed-width store (v3.19.1 Phase 3)."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

from nexus_memory.config import (
    ENV_ALLOW_IN_REPO,
    InRepoStoreError,
    StoreConfig,
    default_store_root,
)
from nexus_memory.store import (
    BlankRecordError,
    EntryTooLongError,
    MemoryStore,
)

SRC = Path(__file__).resolve().parents[1] / "src"


def test_round_trip_append_and_get(tmp_path: Path) -> None:
    store = MemoryStore(tmp_path)
    assert store.append("first") == 0
    assert store.append("second") == 1
    assert store.count() == 2
    assert store.get(0) == "first"
    assert store.get(1) == "second"
    assert store.slice(0, 2) == ["first", "second"]


def test_padding_is_exact_width(tmp_path: Path) -> None:
    cfg = StoreConfig(record_width=64, max_entry_length=32)
    store = MemoryStore(tmp_path, config=cfg)
    store.append("x")
    store.append("")  # empty entry is allowed
    store.append("y" * 32)
    size = store.log_path.stat().st_size
    assert size == 3 * 64
    assert store.get(0) == "x"
    assert store.get(1) == ""
    assert store.get(2) == "y" * 32


def test_over_length_entry_is_rejected(tmp_path: Path) -> None:
    cfg = StoreConfig(record_width=64, max_entry_length=8)
    store = MemoryStore(tmp_path, config=cfg)
    with pytest.raises(EntryTooLongError):
        store.append("123456789")
    assert store.count() == 0


def test_utf8_round_trips_under_forced_locale(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PYTHONIOENCODING", "ascii")
    store = MemoryStore(tmp_path)
    store.append("cafe resume")  # ASCII stand-in plus
    store.append("caf\u00e9 r\u00e9sum\u00e9")
    assert store.get(1) == "caf\u00e9 r\u00e9sum\u00e9"


def test_repair_truncates_only_the_incomplete_tail(tmp_path: Path) -> None:
    store = MemoryStore(tmp_path)
    store.append("keep-me")
    store.append("also-keep")
    with open(store.log_path, "ab") as fh:
        fh.write(b"\x00" * 17)
    assert store.log_path.stat().st_size % store.width != 0
    removed = store.repair()
    assert removed == 17
    assert store.count() == 2
    assert store.get(0) == "keep-me"
    assert store.get(1) == "also-keep"
    assert store.repair() == 0


def test_blank_record_raises_actionable_error(tmp_path: Path) -> None:
    store = MemoryStore(tmp_path)
    store.append("ok")
    raw = bytearray(store.log_path.read_bytes())
    # Impossible length in the first record.
    raw[0:4] = (0xFFFFFFFF).to_bytes(4, "little")
    store.log_path.write_bytes(bytes(raw))
    with pytest.raises(BlankRecordError) as caught:
        store.get(0)
    assert "python -m nexus_memory repair" in str(caught.value)
    assert str(tmp_path) in str(caught.value)


def test_relocated_root_is_honored(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    relocated = tmp_path / "synced" / "mem"
    monkeypatch.setenv("NEXUS_MEMORY_ROOT", str(relocated))
    assert default_store_root() == relocated
    store = MemoryStore()
    store.append("in-synced-folder")
    assert (relocated / "entries.log").is_file()
    assert MemoryStore(relocated).get(0) == "in-synced-folder"


def test_config_round_trip(tmp_path: Path) -> None:
    store = MemoryStore(tmp_path)
    from nexus_memory.cli import main

    assert main(["--root", str(tmp_path), "config", "set", "read_budget", "80"]) == 0
    assert main(["--root", str(tmp_path), "config", "show"]) == 0
    reloaded = MemoryStore(tmp_path)
    assert reloaded.config.read_budget == 80
    # read budget is a reading budget: nothing is recomputed
    store.append("still-here")
    assert MemoryStore(tmp_path).get(0) == "still-here"


def test_multiprocess_concurrent_append(tmp_path: Path) -> None:
    workers = 4
    per_worker = 15
    env = os.environ.copy()
    env["PYTHONPATH"] = str(SRC)
    procs = []
    for i in range(workers):
        code = (
            "from nexus_memory.store import MemoryStore\n"
            f"s = MemoryStore(r'{tmp_path}')\n"
            f"for n in range({per_worker}):\n"
            f"    s.append(f'w{i}-{{n}}')\n"
        )
        procs.append(
            subprocess.Popen(
                [sys.executable, "-c", code],
                env=env,
                cwd=str(tmp_path),
            )
        )
    codes = [p.wait(timeout=60) for p in procs]
    assert codes == [0] * workers
    store = MemoryStore(tmp_path)
    assert store.count() == workers * per_worker
    seen = [store.get(i) for i in range(store.count())]
    assert len(seen) == len(set(seen))
    assert store.log_path.stat().st_size == store.count() * store.width


class _GitTrue:
    returncode = 0
    stdout = "true\n"


class _GitFalse:
    returncode = 128
    stdout = "false\n"


def test_creating_a_store_inside_a_git_repo_is_refused(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv(ENV_ALLOW_IN_REPO, raising=False)
    monkeypatch.setattr(
        "nexus_memory.config.subprocess.run",
        lambda *args, **kwargs: _GitTrue(),
    )
    with pytest.raises(InRepoStoreError):
        MemoryStore(tmp_path / "memory")


def test_allow_in_repo_override_creates_inside_git(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv(ENV_ALLOW_IN_REPO, "1")
    monkeypatch.setattr(
        "nexus_memory.config.subprocess.run",
        lambda *args, **kwargs: _GitTrue(),
    )
    store = MemoryStore(tmp_path / "memory")
    store.append("accepted-in-repo")
    assert (tmp_path / "memory" / ".nexus-memory-store").is_file()
    assert store.get(0) == "accepted-in-repo"


def test_missing_git_does_not_refuse_a_normal_root(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv(ENV_ALLOW_IN_REPO, raising=False)

    def _raise(*args, **kwargs):
        raise FileNotFoundError("git")

    monkeypatch.setattr("nexus_memory.config.subprocess.run", _raise)
    store = MemoryStore(tmp_path)
    store.append("no-git-binary")
    assert store.get(0) == "no-git-binary"


def test_git_reporting_not_a_worktree_allows_create(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv(ENV_ALLOW_IN_REPO, raising=False)
    monkeypatch.setattr(
        "nexus_memory.config.subprocess.run",
        lambda *args, **kwargs: _GitFalse(),
    )
    store = MemoryStore(tmp_path)
    store.append("outside")
    assert store.get(0) == "outside"


@pytest.mark.skipif(os.name == "nt", reason="POSIX permission bits are not enforced on Windows")
def test_store_files_are_owner_only(tmp_path: Path) -> None:
    import stat

    store = MemoryStore(tmp_path)
    store.append("private")
    assert stat.S_IMODE(store.root.stat().st_mode) == 0o700
    assert stat.S_IMODE(store.log_path.stat().st_mode) == 0o600
    marker = store.root / ".nexus-memory-store"
    assert marker.is_file()
    assert stat.S_IMODE(marker.stat().st_mode) == 0o600


def test_marker_is_written_on_create(tmp_path: Path) -> None:
    MemoryStore(tmp_path)
    marker = tmp_path / ".nexus-memory-store"
    assert marker.read_text(encoding="utf-8").startswith("nexus-memory-store")


def test_readme_states_stdlib_and_zero_outbound() -> None:
    readme = (Path(__file__).resolve().parents[1] / "README.md").read_text(encoding="utf-8")
    assert "Python standard library only" in readme
    assert "zero outbound calls" in readme
    assert "zero API keys" in readme
    assert "zero model downloads" in readme
    assert "calling agent" in readme


def test_save_config_never_exposes_a_truncated_file(tmp_path: Path, monkeypatch) -> None:
    """The destination stays whole right up to the atomic swap.

    Deterministic regression test for the concurrency seam recorded as BG-1:
    ``Path.write_text`` truncates before writing, so a reader that opened
    ``config.json`` in that window got an empty string and raised
    JSONDecodeError. The multiprocess test only caught it intermittently -- it
    failed once in CI and passed on the retry -- so this asserts the property
    directly instead of racing for it.
    """
    import json as _json

    from nexus_memory import config as config_mod

    config_mod.save_config(tmp_path, StoreConfig())
    path = tmp_path / config_mod.CONFIG_NAME
    original = path.read_text(encoding="utf-8")

    seen: list[str] = []
    real_replace = config_mod.os.replace

    def spy(src, dst, *args, **kwargs):
        # Exactly what a concurrent reader would observe an instant before the swap.
        seen.append(Path(dst).read_text(encoding="utf-8"))
        return real_replace(src, dst, *args, **kwargs)

    monkeypatch.setattr(config_mod.os, "replace", spy)
    config_mod.save_config(tmp_path, StoreConfig(read_budget=42))

    assert seen, "save_config must publish through os.replace, not a truncating write"
    assert seen[0] == original, "the destination was modified before the atomic swap"
    assert _json.loads(path.read_text(encoding="utf-8"))["read_budget"] == 42


def test_save_config_leaves_no_temp_file_behind(tmp_path: Path) -> None:
    """The sibling temp file is always cleaned up, success or failure."""
    from nexus_memory import config as config_mod

    config_mod.save_config(tmp_path, StoreConfig(read_budget=55))
    leftovers = sorted(p.name for p in tmp_path.glob(f"{config_mod.CONFIG_NAME}.tmp.*"))

    assert leftovers == []
