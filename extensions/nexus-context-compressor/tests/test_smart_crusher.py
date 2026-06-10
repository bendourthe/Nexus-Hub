"""Tests for the SmartCrusher deterministic JSON-array dedup (Phase 1 T003).

Covers the stability-gate assertions (1000 identical -> <=3 + marker; high-
variance preserved; stable hashes; correct metrics) plus determinism, the
lossless-accounting invariant, non-adjacent dedup, the budget cap, and the
documented `python -m` entry point.
"""

from __future__ import annotations

import json
import re

import pytest

from nexus_context_compressor.transforms.smart_crusher import (
    CrushResult,
    SmartCrusherConfig,
    main,
    smart_crush,
)

MARKER_RE = re.compile(r"^<<ccr:[0-9a-f]{12} \d+_rows>>$")


def _markers(result: CrushResult) -> list[dict]:
    return [r for r in result.records if isinstance(r, dict) and "_ccr_dropped" in r]


def _assert_lossless(result: CrushResult) -> None:
    """Every original row is either kept or recorded in a dropped span."""
    dropped_rows = sum(span.count for span in result.dropped)
    assert result.kept_count + dropped_rows == result.original_count


# --- Stability-gate assertions -------------------------------------------------


def test_thousand_identical_collapses_to_at_most_three_plus_marker():
    records = [{"level": "INFO", "msg": "heartbeat", "code": 200} for _ in range(1000)]
    result = smart_crush(records)
    assert result.kept_count <= 3
    assert len(_markers(result)) >= 1
    _assert_lossless(result)


def test_high_variance_array_is_preserved():
    # Distinct records, fewer than the keep budget -> nothing dropped.
    records = [{"id": i, "v": i * i, "name": f"row{i}"} for i in range(12)]
    result = smart_crush(records)
    assert result.kept_count == 12
    assert result.dropped == []
    assert result.records == records


def test_ccr_marker_hashes_are_stable_across_runs():
    records = [{"level": "INFO", "msg": "heartbeat", "code": 200} for _ in range(50)]
    first = smart_crush(records)
    second = smart_crush(records)
    assert first.records == second.records
    assert [s.hash for s in first.dropped] == [s.hash for s in second.dropped]


def test_crushresult_metrics_are_correct():
    records = [{"level": "INFO", "msg": "heartbeat", "code": 200} for _ in range(20)]
    result = smart_crush(records)
    assert result.original_count == 20
    assert result.kept_count == len(
        [r for r in result.records if not (isinstance(r, dict) and "_ccr_dropped" in r)]
    )
    assert len(result.dropped) == len(_markers(result))
    _assert_lossless(result)


# --- Behavior --------------------------------------------------------------


def test_below_min_items_returned_unchanged():
    records = [{"a": 1}, {"a": 2}, {"a": 3}]  # < min_items_to_analyze (5)
    result = smart_crush(records)
    assert result.records == records
    assert result.dropped == []
    assert result.original_count == 3


def test_marker_format_matches_spec():
    records = [{"x": 1} for _ in range(30)]
    result = smart_crush(records)
    markers = _markers(result)
    assert markers
    for marker in markers:
        assert MARKER_RE.match(marker["_ccr_dropped"]), marker["_ccr_dropped"]


def test_non_adjacent_duplicates_are_dropped():
    # A,B,A,B,... : pure adjacent comparison would keep everything; global
    # uniqueness must collapse the repeats.
    a = {"k": "a", "n": 1}
    b = {"k": "b", "n": 2}
    records = [a, b] * 20
    result = smart_crush(records)
    # Only two unique values exist; keep set should be small.
    assert result.kept_count <= 4
    _assert_lossless(result)


def test_first_and_last_records_survive():
    # A highly repetitive middle so the head/tail only survive via the anchors.
    records = (
        [{"i": 0, "tag": "FIRST"}]
        + [{"i": 1, "tag": "mid"}] * 48
        + [{"i": 49, "tag": "LAST"}]
    )
    result = smart_crush(records)
    assert result.records[0] == records[0]
    assert result.records[-1] == records[-1]
    _assert_lossless(result)


def test_budget_cap_is_respected():
    # 60 all-distinct records; the keep set must be capped at max_items.
    records = [{"id": i, "a": i, "b": i * 2, "c": i * 3} for i in range(60)]
    config = SmartCrusherConfig(max_items_after_crush=15)
    result = smart_crush(records, config)
    assert result.kept_count <= 15
    _assert_lossless(result)


def test_mixed_type_records_do_not_crash():
    records = ["a string", {"a": 1}, "a string", {"a": 1}, "another", {"a": 1}]
    result = smart_crush(records)
    _assert_lossless(result)
    assert result.original_count == 6


def test_crush_is_deterministic():
    records = [{"v": i % 3} for i in range(40)]  # repeating pattern 0,1,2,0,1,2,...
    assert smart_crush(records).records == smart_crush(records).records


# --- CLI entry point -------------------------------------------------------


def test_demo_cli_runs_and_emits_compressed_array(capsys):
    code = main(["--demo"])
    assert code == 0
    out = capsys.readouterr()
    parsed = json.loads(out.out)
    assert isinstance(parsed, list)
    kept = [r for r in parsed if not (isinstance(r, dict) and "_ccr_dropped" in r)]
    assert len(kept) <= 15
    assert "100 ->" in out.err


def test_top_level_shim_reexports_strategy():
    from nexus_context_compressor import smart_crusher as shim

    records = [{"x": 1} for _ in range(10)]
    assert shim.smart_crush(records).records == smart_crush(records).records
    assert shim.SmartCrusherConfig is SmartCrusherConfig
