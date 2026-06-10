"""Tests for the CLI surface (``nexus_context_compressor.cli``).

The CLI powers the PreToolUse hook (``compress``), the Windows CLAUDE.md path,
and marker resolution (``retrieve``). These tests exercise the public functions
directly; subprocess behavior of the hook is covered by
``catalog/hooks/tests/test_compress_output_hook.py``.
"""

from __future__ import annotations

import io
import json

import pytest
from nexus_context_compressor import cli


@pytest.fixture(autouse=True)
def _isolated_store(monkeypatch, tmp_path):
    monkeypatch.setenv("NEXUS_CCR_STORE_PATH", str(tmp_path / "ccr.db"))


def _dupe_array(n: int = 40) -> str:
    return json.dumps([{"a": 1, "b": "x"} for _ in range(n)])


def test_run_compress_compresses_structured_output():
    out = cli.run_compress(_dupe_array(), persist=True)
    assert any(
        isinstance(r, dict) and "_ccr_dropped" in r for r in json.loads(out)
    )


def test_run_compress_round_trips_via_retrieve():
    out = cli.run_compress(_dupe_array(), persist=True)
    marker = next(
        r["_ccr_dropped"] for r in json.loads(out) if isinstance(r, dict) and "_ccr_dropped" in r
    )
    found, payload = cli.run_retrieve(marker)
    assert found is True
    assert json.loads(payload)[0] == {"a": 1, "b": "x"}


def test_run_compress_is_fail_open_on_prose():
    text = "nothing structured here"
    assert cli.run_compress(text) == text


def test_run_retrieve_miss_returns_false():
    found, payload = cli.run_retrieve("<<ccr:deadbeef0000 9_rows>>")
    assert found is False
    assert payload == ""


def test_run_retrieve_garbage_marker_is_a_miss():
    found, _ = cli.run_retrieve("not a marker at all")
    assert found is False


def test_main_compress_reads_stdin_writes_stdout(monkeypatch, capsys):
    monkeypatch.setattr("sys.stdin", io.StringIO(_dupe_array()))
    rc = cli.main(["compress"])
    captured = capsys.readouterr()
    assert rc == 0
    assert "_ccr_dropped" in captured.out
    # Metrics go to stderr, never stdout (which flows into context).
    assert "nexus-context-compressor" in captured.err


def test_main_retrieve_miss_exits_1(capsys):
    rc = cli.main(["retrieve", "<<ccr:deadbeef0000 9_rows>>"])
    assert rc == 1


def test_main_bare_prints_identity(capsys):
    rc = cli.main([])
    captured = capsys.readouterr()
    assert rc == 0
    assert "nexus-context-compressor" in captured.out
    assert "token counter" in captured.out
