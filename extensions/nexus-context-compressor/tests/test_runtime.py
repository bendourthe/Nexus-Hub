"""Tests for the Phase 4 runtime seam (``compress_output`` and the rewired
``compress``).

``compress_output`` is the single-blob entry point the PreToolUse hook (via the
CLI) and the internal MCP ``context_compress`` tool call on raw tool output. It
must compress structured content, persist drops reversibly, never expand a
payload, and never lose output. ``compress`` (the messages API) now routes each
message's content, staying an identity transform on prose.
"""

from __future__ import annotations

import json

import nexus_context_compressor as ncc
import pytest
from nexus_context_compressor.ccr import NOT_FOUND, CCRStore, retrieve
from nexus_context_compressor.transforms.content_router import RouteResult


@pytest.fixture(autouse=True)
def _isolated_store(monkeypatch, tmp_path):
    """Point the default CCR store at a temp file so tests never touch ~/.nexus-hub."""
    monkeypatch.setenv("NEXUS_CCR_STORE_PATH", str(tmp_path / "ccr.db"))


def _dupe_array(n: int = 40) -> str:
    return json.dumps([{"level": "INFO", "msg": "ok", "code": 200} for _ in range(n)])


# --- compress_output ------------------------------------------------------


def test_compress_output_compresses_json_array():
    result = ncc.compress_output(_dupe_array())
    assert isinstance(result, RouteResult)
    assert result.tokens_after < result.tokens_before
    # The compressed payload carries a CCR marker standing in for the dropped span.
    records = json.loads(result.text)
    assert any(isinstance(r, dict) and "_ccr_dropped" in r for r in records)


def test_compress_output_persists_drops_reversibly():
    result = ncc.compress_output(_dupe_array(), persist=True)
    marker = next(
        r["_ccr_dropped"]
        for r in json.loads(result.text)
        if isinstance(r, dict) and "_ccr_dropped" in r
    )
    with CCRStore() as store:
        original = retrieve(marker, store=store)
    assert original is not NOT_FOUND
    assert len(original) >= 1
    assert original[0] == {"level": "INFO", "msg": "ok", "code": 200}


def test_compress_output_no_persist_is_pure(tmp_path):
    # With persist=False no store is opened, so nothing is written.
    ncc.compress_output(_dupe_array(), persist=False)
    store_file = tmp_path / "ccr.db"
    # Either the file was never created, or it holds no spans.
    if store_file.exists():
        with CCRStore(store_file) as store:
            assert len(store) == 0


def test_compress_output_never_expands_small_json():
    # A tiny array is below the crush threshold; reserialization would pretty-print
    # and grow it, but the never-expand guard returns the original verbatim.
    tiny = "[1, 2, 3]"
    result = ncc.compress_output(tiny)
    assert result.text == tiny
    assert result.tokens_after <= result.tokens_before


def test_compress_output_passes_through_prose():
    prose = "This is a plain sentence with nothing structured to compress."
    result = ncc.compress_output(prose)
    assert result.text == prose


def test_compress_output_handles_non_string():
    result = ncc.compress_output(None)
    assert result.text == ""
    result = ncc.compress_output(12345)
    assert result.text == "12345"


# --- compress (messages API) ---------------------------------------------


def test_compress_messages_is_identity_on_prose():
    messages = [
        {"role": "user", "content": "hello world"},
        {"role": "assistant", "content": "hi there, how can I help?"},
    ]
    result = ncc.compress(messages)
    assert result.messages == messages
    assert result.transforms_applied == []
    assert result.ratio == 1.0


def test_compress_messages_routes_structured_content():
    messages = [{"role": "tool", "content": _dupe_array()}]
    result = ncc.compress(messages, store=None)
    assert result.tokens_after < result.tokens_before
    assert result.transforms_applied == ["content_router"]
    # The structured content was compressed in place; the message shape is kept.
    assert result.messages[0]["role"] == "tool"


def test_compress_messages_accepts_plain_strings_and_dicts():
    mixed = ["a plain string", {"role": "user", "content": "a mapping"}]
    result = ncc.compress(mixed)
    assert result.messages == mixed


def test_compress_empty_input():
    result = ncc.compress([])
    assert result.tokens_before == 0
    assert result.ratio == 1.0
    assert result.transforms_applied == []
