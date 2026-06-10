"""Tests for the CCR marker codec (Phase 2, shared by producer and consumer).

The codec is the single source of truth for the ``<<ccr:HASH N_rows>>`` grammar.
These tests pin the format and the producer/consumer round-trip so the writer
(SmartCrusher) and the reader (retrieve) can never drift.
"""

from __future__ import annotations

import pytest

from nexus_context_compressor.ccr.marker import (
    DROPPED_KEY,
    ParsedMarker,
    extract_hash,
    find_all_markers,
    find_marker,
    format_marker,
    make_marker_object,
    parse_marker,
)

_HASH = "0123456789ab"  # 12 lowercase hex chars, the documented hash width


def test_format_marker_matches_grammar():
    assert format_marker(_HASH, 48) == f"<<ccr:{_HASH} 48_rows>>"


def test_make_marker_object_wraps_the_string_under_the_dropped_key():
    obj = make_marker_object(_HASH, 7)
    assert obj == {DROPPED_KEY: f"<<ccr:{_HASH} 7_rows>>"}


def test_format_then_parse_is_a_round_trip():
    parsed = parse_marker(format_marker(_HASH, 123))
    assert parsed == ParsedMarker(hash=_HASH, count=123)


def test_parse_accepts_a_marker_object():
    parsed = parse_marker(make_marker_object(_HASH, 5))
    assert parsed is not None
    assert parsed.hash == _HASH
    assert parsed.count == 5


@pytest.mark.parametrize(
    "bad",
    [
        "not a marker",
        "<<ccr:tooshort 5_rows>>",  # hash not 12 hex chars
        "<<ccr:0123456789ab 5rows>>",  # missing the _ before rows
        "<<ccr:0123456789ab 5_rows>> trailing",  # trailing junk (anchored regex)
        "<<ccr:0123456789AB 5_rows>>",  # uppercase hex not allowed
        {"some_other_key": "value"},
        None,
        42,
        [],
    ],
)
def test_parse_returns_none_on_malformed_input(bad):
    assert parse_marker(bad) is None


def test_parse_tolerates_surrounding_whitespace():
    parsed = parse_marker(f"  <<ccr:{_HASH} 9_rows>>  ")
    assert parsed is not None and parsed.count == 9


def test_extract_hash_from_marker_string():
    assert extract_hash(format_marker(_HASH, 3)) == _HASH


def test_extract_hash_from_marker_object():
    assert extract_hash(make_marker_object(_HASH, 3)) == _HASH


def test_extract_hash_accepts_a_bare_hash():
    assert extract_hash(_HASH) == _HASH


def test_extract_hash_returns_none_on_garbage():
    assert extract_hash("definitely not a hash") is None
    assert extract_hash("0123456789ab extra") is None


# --- Embedded markers (Phase 3: CodeCompressor leaves markers inside comments) ---


def test_find_marker_inside_a_code_comment():
    line = f"    // <<ccr:{_HASH} 12_rows>>"
    parsed = find_marker(line)
    assert parsed == ParsedMarker(hash=_HASH, count=12)


def test_find_marker_inside_a_python_comment():
    line = f"        # <<ccr:{_HASH} 4_rows>>"
    parsed = find_marker(line)
    assert parsed is not None and parsed.hash == _HASH and parsed.count == 4


def test_parse_marker_rejects_what_find_marker_accepts():
    # The key distinction: parse_marker is anchored (the whole string must be a
    # marker); find_marker locates one embedded in surrounding text.
    embedded = f"// <<ccr:{_HASH} 3_rows>>"
    assert parse_marker(embedded) is None
    assert find_marker(embedded) is not None


def test_find_marker_returns_none_without_a_marker():
    assert find_marker("just a line of code") is None
    assert find_marker(None) is None  # type: ignore[arg-type]
    assert find_marker(42) is None  # type: ignore[arg-type]


def test_find_all_markers_returns_every_marker_in_order():
    blob = (
        f"def a():\n    # <<ccr:{_HASH} 5_rows>>\n"
        f"def b():\n    # <<ccr:abcdefabcdef 9_rows>>\n"
    )
    markers = find_all_markers(blob)
    assert [m.hash for m in markers] == [_HASH, "abcdefabcdef"]
    assert [m.count for m in markers] == [5, 9]


def test_find_all_markers_empty_when_none_present():
    assert find_all_markers("no markers here") == []
    assert find_all_markers(None) == []  # type: ignore[arg-type]
