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
