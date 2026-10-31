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


def test_credentials_fingerprint_ignores_token_values_but_not_other_content(tmp_path: Path) -> None:
    target = tmp_path / ".credentials.json"
    target.write_text('{"claudeAiOauth": {"accessToken": "a", "refreshToken": "b", "expiresAt": 1, "scopes": ["x"]}, "organizationUuid": "o"}', encoding="utf-8")
    first = spike.fingerprint(target)
    target.write_text('{"claudeAiOauth": {"accessToken": "c", "refreshToken": "d", "expiresAt": 2, "scopes": ["x"]}, "organizationUuid": "o"}', encoding="utf-8")
    assert spike.fingerprint(target) == first
    target.write_text('{"claudeAiOauth": {"accessToken": "c", "refreshToken": "d", "expiresAt": 2, "scopes": ["x", "y"]}, "organizationUuid": "o"}', encoding="utf-8")
    assert spike.fingerprint(target) != first


def test_a_paid_request_that_could_pass_the_cap_is_not_started(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(spike, "PAID_COSTS", [("earlier", 0.90)])
    monkeypatch.setattr(spike, "run", lambda *a, **k: pytest.fail("no request may start past the cap"))
    assert spike.claude_attribution({}, "label", 1.00).startswith("not-run")


# --- No probe without a sign-in reaches an external host (fix cycle 1, WN-36) ---------------------


def test_the_offline_sink_records_the_host_of_each_attempt_and_forwards_nothing() -> None:
    import socket

    sink = spike.OfflineSink()
    try:
        env = sink.env()
        assert env["HTTPS_PROXY"] == env["HTTP_PROXY"] == env["ALL_PROXY"] == f"http://127.0.0.1:{sink.port}"
        assert env["NO_PROXY"] == "" and env["no_proxy"] == ""  # not even a local address bypasses the sink
        for line in (b"CONNECT api.openai.com:443 HTTP/1.1\r\n\r\n", b"GET http://example.test/x HTTP/1.1\r\n\r\n"):
            with socket.create_connection(("127.0.0.1", sink.port), timeout=5) as conn:
                conn.sendall(line)
                assert conn.recv(64).startswith(b"HTTP/1.1 502")
        deadline = spike.time.monotonic() + 5
        while len(sink.attempts) < 2 and spike.time.monotonic() < deadline:
            spike.time.sleep(0.02)
        assert sink.hosts() == ["api.openai.com", "example.test"]
    finally:
        sink.close()


def test_every_free_probe_is_offline_and_the_paid_one_is_not() -> None:
    import inspect

    scratch = spike.Scratch()
    try:
        plain, offline = scratch.env(), scratch.offline_env(CODEX_HOME="x")
        assert "HTTPS_PROXY" not in plain and offline["HTTPS_PROXY"].startswith("http://127.0.0.1:") and offline["CODEX_HOME"] == "x"
    finally:
        scratch.cleanup()
        spike.SINK.close()
    for name in ("claude_init", "claude_effort", "codex_effort", "codex_report"):
        assert "offline_env" in inspect.getsource(getattr(spike, name)), name
    assert "offline_env" not in inspect.getsource(spike.claude_attribution)  # a paid request must reach its API


def test_the_matrix_does_not_call_the_effort_probes_local_and_names_what_the_sink_recorded(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    out = tmp_path / "matrix.md"
    monkeypatch.setattr(spike.SINK, "attempts", ["CONNECT api.openai.com:443 HTTP/1.1", "CONNECT chatgpt.com:443 HTTP/1.1"])
    spike.write_matrix(out, [], {"codex": "codex-cli 0.136.0"}, {}, {})
    text = out.read_text(encoding="utf-8")
    assert "are local" not in text and "Nothing here is \"local\"" in text
    assert "api.openai.com, chatgpt.com" in text and "None of them was contacted." in text

    monkeypatch.setattr(spike.SINK, "attempts", [])
    spike.write_matrix(out, [], {}, {}, {})
    assert "this run cannot tell which" in out.read_text(encoding="utf-8")
