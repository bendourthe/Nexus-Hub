"""End-to-end CCR round-trip: SmartCrusher + store + retrieve (Phase 2, T007).

This is the Phase 2 stability gate: a compressed payload's CCR marker resolves
back to the exact dropped originals, so compression is non-lossy. Also pins the
purity guarantee -- ``smart_crush`` with no store touches nothing -- so the
Phase 1 contract survives the Phase 2 wiring.
"""

from __future__ import annotations

from nexus_context_compressor.ccr.marker import DROPPED_KEY
from nexus_context_compressor.ccr.retrieve import NOT_FOUND, retrieve
from nexus_context_compressor.ccr.store import CCRStore
from nexus_context_compressor.transforms.smart_crusher import smart_crush


def _markers(records: list) -> list[dict]:
    return [r for r in records if isinstance(r, dict) and DROPPED_KEY in r]


def _repetitive(n: int = 50) -> list:
    """A repetitive array SmartCrusher will collapse into at least one span."""
    return [{"level": "INFO", "msg": "heartbeat", "code": 200} for _ in range(n)]


def test_every_dropped_span_is_persisted(tmp_path):
    with CCRStore(tmp_path / "ccr.db") as store:
        result = smart_crush(_repetitive(), store=store)
        assert result.dropped  # something was dropped
        assert len(store) == len(result.dropped)
        for span in result.dropped:
            assert span.hash in store


def test_each_marker_resolves_back_to_exact_originals(tmp_path):
    with CCRStore(tmp_path / "ccr.db") as store:
        result = smart_crush(_repetitive(), store=store)
        # Pair each emitted marker with the span it stood in for, in order.
        for marker, span in zip(_markers(result.records), result.dropped):
            assert retrieve(marker, store=store) == span.records


def test_round_trip_is_lossless(tmp_path):
    """Kept records + retrieved dropped records reconstruct the whole input."""
    records = _repetitive(80)
    with CCRStore(tmp_path / "ccr.db") as store:
        result = smart_crush(records, store=store)
        reconstructed: list = []
        for item in result.records:
            if isinstance(item, dict) and DROPPED_KEY in item:
                restored = retrieve(item, store=store)
                assert restored is not NOT_FOUND
                reconstructed.extend(restored)
            else:
                reconstructed.append(item)
        assert reconstructed == records


def test_round_trip_survives_a_store_restart(tmp_path):
    db = tmp_path / "ccr.db"
    records = _repetitive(60)
    writer = CCRStore(db)
    result = smart_crush(records, store=writer)
    marker = _markers(result.records)[0]
    expected = result.dropped[0].records
    writer.close()

    reader = CCRStore(db)
    try:
        assert retrieve(marker, store=reader) == expected
    finally:
        reader.close()


# -- purity guarantee (Phase 1 contract preserved) -----------------------------


def test_smart_crush_without_store_persists_nothing(tmp_path):
    # A store opened but never passed in stays empty: the default path is pure.
    with CCRStore(tmp_path / "ccr.db") as store:
        smart_crush(_repetitive())  # no store= argument
        assert len(store) == 0


def test_result_is_identical_with_and_without_store(tmp_path):
    records = _repetitive()
    without = smart_crush(records)
    with CCRStore(tmp_path / "ccr.db") as store:
        withstore = smart_crush(records, store=store)
    assert without.records == withstore.records
    assert [s.hash for s in without.dropped] == [s.hash for s in withstore.dropped]
