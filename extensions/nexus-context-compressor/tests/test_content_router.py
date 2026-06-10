"""Tests for the ContentRouter (Phase 3 T009).

Covers the stability-gate assertions (correct classification of JSON / code /
log / text, and dispatch of each to the right strategy) plus mixed-content
splitting on fenced blocks, fenced-JSON routing to SmartCrusher, store threading
for reversible routed drops, and safe handling of prose and degenerate inputs.
"""

from __future__ import annotations

import json

from nexus_context_compressor.ccr.marker import find_marker, parse_marker
from nexus_context_compressor.ccr.retrieve import NOT_FOUND, retrieve
from nexus_context_compressor.ccr.store import CCRStore
from nexus_context_compressor.transforms.code_compressor import CodeCompressorConfig
from nexus_context_compressor.transforms.content_router import (
    ContentType,
    RouterConfig,
    classify,
    route,
)

CFG = RouterConfig(code_compressor=CodeCompressorConfig(min_body_lines=2, ccr_min_lines=3))

PROSE = "Here is some prose explaining the change."
PY_FENCE = (
    "```python\n"
    "def add(a, b):\n"
    "    total = a + b\n"
    "    doubled = total * 2\n"
    "    return doubled\n"
    "```"
)


# --- Classification -----------------------------------------------------------


def test_classify_json_array():
    assert classify(json.dumps([{"a": i} for i in range(5)])) is ContentType.JSON_ARRAY


def test_classify_json_object():
    assert classify(json.dumps({"a": 1, "b": 2})) is ContentType.JSON_OBJECT


def test_classify_log():
    text = "INFO starting up\nINFO tick 1\nERROR boom\nWARN slow request"
    assert classify(text) is ContentType.LOG


def test_classify_timestamped_log():
    text = "2026-06-09 10:00 started\n2026-06-09 10:01 tick\n2026-06-09 10:02 done"
    assert classify(text) is ContentType.LOG


def test_classify_code():
    assert classify("import os\n\ndef foo():\n    return 1") is ContentType.CODE


def test_classify_text():
    assert classify("This is an ordinary sentence with no structure.") is ContentType.TEXT


def test_classify_empty_and_non_string():
    assert classify("") is ContentType.TEXT
    assert classify(None) is ContentType.TEXT  # type: ignore[arg-type]


# --- Dispatch: whole-payload routing -----------------------------------------


def test_whole_json_array_is_crushed():
    payload = json.dumps([{"level": "INFO", "msg": "hb"} for _ in range(40)])
    result = route(payload, config=CFG)
    assert len(result.segments) == 1
    assert result.segments[0].content_type is ContentType.JSON_ARRAY
    assert "_ccr_dropped" in result.text
    assert result.tokens_after < result.tokens_before


def test_whole_code_payload_is_elided():
    code = "def f(a):\n    x = a + 1\n    y = x * 2\n    return y\n"
    result = route(code, config=CFG)
    assert result.segments[0].content_type is ContentType.CODE
    assert "def f(a):" in result.text
    assert "a + 1" not in result.text


def test_prose_passes_through_unchanged():
    result = route(PROSE, config=CFG)
    assert result.text == PROSE
    assert result.segments[0].content_type is ContentType.TEXT


# --- Dispatch: mixed content (fenced) ----------------------------------------


def test_mixed_content_splits_and_routes():
    content = f"{PROSE}\n\n{PY_FENCE}\n\nThat is all."
    result = route(content, config=CFG)
    types = [s.content_type for s in result.segments]
    assert ContentType.CODE in types
    # Prose on both sides preserved verbatim.
    assert result.text.startswith(PROSE)
    assert result.text.rstrip().endswith("That is all.")
    # Fence preserved; body elided.
    assert "```python" in result.text
    assert "def add(a, b):" in result.text
    assert "total = a + b" not in result.text


def test_fenced_json_routes_to_smartcrusher():
    arr = json.dumps([{"level": "INFO", "msg": "hb"} for _ in range(40)])
    content = f"Logs below:\n\n```json\n{arr}\n```\n"
    result = route(content, config=CFG)
    fence_seg = next(s for s in result.segments if s.is_code_fence)
    assert fence_seg.content_type is ContentType.JSON_ARRAY
    assert "_ccr_dropped" in result.text
    assert "```json" in result.text


def test_fenced_code_block_is_not_classified_as_json():
    body = "def g():\n    a = 1\n    b = 2\n    return a\n"
    content = "```python\n" + body + "```"
    result = route(content, config=CFG)
    fence_seg = next(s for s in result.segments if s.is_code_fence)
    assert fence_seg.content_type is ContentType.CODE


# --- Store threading / reversibility -----------------------------------------


def test_routed_code_drop_is_reversible(tmp_path):
    store = CCRStore(tmp_path / "ccr.db")
    try:
        content = f"{PROSE}\n\n{PY_FENCE}"
        result = route(content, config=CFG, store=store)
        marker = find_marker(result.text)
        assert marker is not None
        assert retrieve(marker.hash, store=store) is not NOT_FOUND
    finally:
        store.close()


def test_routed_json_drop_is_reversible(tmp_path):
    store = CCRStore(tmp_path / "ccr.db")
    try:
        payload = json.dumps([{"level": "INFO", "msg": "hb"} for _ in range(40)])
        result = route(payload, config=CFG, store=store)
        # The crushed array carries a standalone marker object; pull its hash.
        crushed = json.loads(result.text)
        marker_obj = next(r for r in crushed if isinstance(r, dict) and "_ccr_dropped" in r)
        parsed = parse_marker(marker_obj)
        assert parsed is not None
        assert retrieve(parsed.hash, store=store) is not NOT_FOUND
    finally:
        store.close()


# --- Determinism / degenerate inputs -----------------------------------------


def test_routing_is_deterministic():
    content = f"{PROSE}\n\n{PY_FENCE}"
    assert route(content, config=CFG).text == route(content, config=CFG).text


def test_empty_input_does_not_crash():
    result = route("", config=CFG)
    assert result.text == ""


def test_non_string_input_is_coerced():
    result = route(42, config=CFG)  # type: ignore[arg-type]
    assert isinstance(result.text, str)
