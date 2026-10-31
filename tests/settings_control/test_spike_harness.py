"""Unit tests for the proof-spike harness safety properties (v4.14.6 Phase 1, T006).

The harness is scaffolding, but its guards are the reason the spike may run on a
maintainer's machine: the real-file hash guard, redaction, the scratch-home
sweep, and the fixed candidate count. No tool is started by these tests.
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location("settings_proof_spike", REPO_ROOT / "scripts" / "dev" / "settings_proof_spike.py")
spike = importlib.util.module_from_spec(SPEC)
sys.modules["settings_proof_spike"] = spike
SPEC.loader.exec_module(spike)


@pytest.mark.parametrize(
    "secret",
    ["sk-ant-api03-abcdefghijklmnop1234", "ghp_abcdefghijklmnopqrstuvwxyz0123", "eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0", "a" * 44 + "b" * 8],
)
def test_redact_removes_token_shaped_values(secret: str) -> None:
    assert secret not in spike.redact(f'model="{secret}"')


def test_redact_keeps_the_matched_field_and_bounds_length() -> None:
    assert spike.redact('permissionMode="acceptEdits"') == 'permissionMode="acceptEdits"'
    assert len(spike.redact("x" * 500)) <= 200


def test_candidate_count_is_fixed_and_ids_are_unique() -> None:
    ids = [rid for rid, _, _ in spike.CANDIDATES]
    assert len(ids) == len(set(ids)) == 39


def test_hash_guard_detects_a_change_after_settling(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    target = tmp_path / "settings.json"
    target.write_text("one", encoding="utf-8")
    monkeypatch.setattr(spike, "real_files", lambda: [target])
    monkeypatch.setattr(spike.time, "sleep", lambda _seconds: None)
    before = spike.hash_real_files()
    target.write_text("two", encoding="utf-8")
    after, changed = spike.settled_changes(before)
    assert changed == [str(target)] and after[str(target)] != before[str(target)]


def test_hash_guard_accepts_a_transient_rewrite_that_returns(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    target = tmp_path / "settings.json"
    target.write_text("one", encoding="utf-8")
    monkeypatch.setattr(spike, "real_files", lambda: [target])
    before = spike.hash_real_files()
    target.write_text("two", encoding="utf-8")

    def restore(_seconds: float) -> None:
        target.write_text("one", encoding="utf-8")

    monkeypatch.setattr(spike.time, "sleep", restore)
    _, changed = spike.settled_changes(before)
    assert changed == []


def test_absent_file_hashes_as_absent(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(spike, "real_files", lambda: [tmp_path / "missing.json"])
    assert list(spike.hash_real_files().values()) == ["absent"]


def test_scratch_home_is_isolated_and_cleaned() -> None:
    scratch = spike.Scratch()
    root = scratch.root
    env = scratch.env(CLAUDE_CONFIG_DIR=str(scratch.home))
    assert env["HOME"] == env["USERPROFILE"] == str(scratch.home)
    assert not any(key.startswith(("ANTHROPIC", "CLAUDE_CODE", "OPENAI")) for key in env if key != "CLAUDE_CONFIG_DIR")
    assert (root / spike.MARKER).is_file()
    scratch.cleanup()
    assert not root.exists()


def test_sweep_removes_only_marked_scratch_homes(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(spike.tempfile, "gettempdir", lambda: str(tmp_path))
    marked = tmp_path / "nexus-spike-aaa"
    marked.mkdir()
    (marked / spike.MARKER).write_text("scratch", encoding="utf-8")
    unmarked = tmp_path / "nexus-spike-bbb"
    unmarked.mkdir()
    assert spike.sweep_stale() == 1
    assert not marked.exists() and unmarked.exists()


def test_judge_marks_mismatch_not_proven() -> None:
    assert spike.judge({"model": "a"}, {"model": "b"})[1] == "not-proven"
    assert spike.judge({"model": "a"}, {"model": "a"})[1] == "proven"
    assert spike.judge({"error": "timed out"}, {"model": "a"})[1] == "not-observed"
