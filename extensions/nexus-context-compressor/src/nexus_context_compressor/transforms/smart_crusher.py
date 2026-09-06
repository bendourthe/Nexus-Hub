"""SmartCrusher: deterministic JSON-array dedup.

Given a JSON array of records (the common shape of tool output: log lines,
search hits, row dumps), SmartCrusher keeps the informative records and
collapses runs of low-variance duplicates into a single reversible CCR marker
``{"_ccr_dropped": "<<ccr:HASH N_rows>>"}``. The hash is a stable content hash
of the dropped span, so Phase 2's CCR store can resolve it back to the
originals -- compression is non-lossy.

The strategy is a pure-Python port (no Rust in v1), deterministic and
dependency-free: the same input always yields the same output and the same
marker hashes (no randomness, no uuid, no clock). Passing an optional ``store``
to :func:`smart_crush` persists each dropped span as a side effect (so the
marker is reversible via the CCR retrieval interface) without changing the
returned, still-deterministic :class:`CrushResult`; with no ``store`` (the
default) the function touches nothing outside itself.

Two mechanisms decide what survives:

1. **Distinctiveness scoring** (``_distinctiveness_scores``) -- how different each
   record is from its neighbours. This subsumes the variance, uniqueness, and
   change-point signals: a record unlike its predecessor scores high; a near-
   duplicate scores low and becomes a drop candidate.
2. **Positional anchors** -- the first and last records are always kept so the
   head and tail of the sequence survive even when the middle is collapsed.

Reference behavior: ``docs/releases/v3/v3.2/comparisons/v3.2.0-comparison-headroom.md`` Section 5a item 1.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from ..ccr.marker import make_marker_object

if TYPE_CHECKING:
    from ..ccr.store import CCRWriter

# Number of hex chars kept from the content hash in a CCR marker. Long enough to
# avoid collisions across the spans of a single payload, short enough to read.
_HASH_LEN = 12


@dataclass(frozen=True)
class SmartCrusherConfig:
    """Tunables for the crush.

    Attributes:
        min_items_to_analyze: arrays shorter than this are returned unchanged
            (too small to be worth compressing).
        max_items_after_crush: the hard cap on representative records kept. The
            stability gate ("100 items -> <=15") is this value.
        variance_threshold: the distinctiveness score at or above which a record
            is considered distinct enough to keep on its own merit.
    """

    min_items_to_analyze: int = 5
    max_items_after_crush: int = 15
    variance_threshold: float = 2.0


@dataclass(frozen=True)
class CCRSpan:
    """A contiguous run of dropped records, addressable by its content hash.

    Phase 2's CCR store persists ``records`` keyed by ``hash`` so a consumer can
    resolve the ``<<ccr:HASH N_rows>>`` marker back to the originals.
    """

    hash: str
    count: int
    records: list


@dataclass
class CrushResult:
    """The outcome of a crush.

    Attributes:
        records: the compressed array -- kept records interleaved with CCR
            marker objects in original order.
        dropped: the dropped spans, for the CCR store (Phase 2).
        original_count: number of records in the input array.
    """

    records: list
    dropped: list[CCRSpan] = field(default_factory=list)
    original_count: int = 0

    @property
    def kept_count(self) -> int:
        """Number of representative records kept (excluding CCR markers)."""
        return sum(1 for r in self.records if not _is_ccr_marker(r))


def _canonical(record: object) -> str:
    """Stable canonical serialization of a record, for hashing and comparison.

    ``sort_keys`` makes the result independent of dict key order, so two records
    that are equal as data hash identically regardless of how they were built.
    """
    return json.dumps(record, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def _is_ccr_marker(record: object) -> bool:
    return isinstance(record, dict) and "_ccr_dropped" in record


def _content_hash(records: list) -> str:
    """Deterministic content hash of a span of records.

    Uses SHA-256 over the canonical serialization of the span. Stable and
    reproducible across runs and machines (no salt, no randomness).
    """
    digest = hashlib.sha256()
    for record in records:
        digest.update(_canonical(record).encode("utf-8"))
        digest.update(b"\x00")  # record separator so [ab][c] != [a][bc]
    return digest.hexdigest()[:_HASH_LEN]


def _field_change_count(current: object, previous: object) -> int:
    """How much ``current`` differs from ``previous``.

    For two mappings, the number of top-level keys whose value changed (the
    variance / change-point signal: a record unlike its predecessor changed
    many fields). For non-mapping records, 1 if unequal else 0.
    """
    if isinstance(current, dict) and isinstance(previous, dict):
        keys = set(current) | set(previous)
        return sum(1 for key in keys if current.get(key) != previous.get(key))
    return 0 if current == previous else 1


def _distinctiveness_scores(
    records: list, config: SmartCrusherConfig
) -> list[float]:
    """Score how distinct each record is (higher = more worth keeping).

    THIS IS THE LOAD-BEARING HEURISTIC OF THE CRUSHER. It returns one score per
    record; near-identical or repeated records score low (collapsed into a CCR
    marker), while genuinely informative records score high (kept). The caller
    treats ``score >= config.variance_threshold`` as "distinct enough to keep".

    The score blends two signals so it is robust to non-adjacent repetition:

    1. **Global uniqueness.** Content seen anywhere earlier in the array scores
       0 -- a drop candidate. This catches non-adjacent repeats (e.g. an
       ``A, B, A, B`` alternation that pure adjacent comparison would never
       dedup) and exact duplicate runs alike.
    2. **Adjacent change magnitude.** A novel record is scored by how many
       fields it changed versus its predecessor (the variance / change-point
       signal). A record that drifts from its neighbour by only one field
       scores below the default ``variance_threshold`` of 2.0 and becomes a
       near-duplicate drop candidate; a record that changes many fields scores
       high and is prioritized when the keep set is over budget.

    The first record (index 0) has no predecessor, so it is treated as fully
    novel with a sentinel score above any field-change count -- the head of the
    array is never silently dropped, and a brand-new record is never starved
    out by the budget cap.

    Contract: ``len(returned) == len(records)``; every score ``>= 0.0``.

    Deferred refinements (see ``docs/releases/v3/v3.2/known-gaps.md``): near-duplicate
    fingerprinting for fuzzy (not exact) repeat detection, information-theoretic
    auto-sizing of the keep budget, and explicit error/outlier preservation.
    These are intentionally out of scope for the v1 deterministic port.
    """
    scores: list[float] = []
    seen: set[str] = set()
    previous: object = None
    # A first occurrence of brand-new content ranks above any field-change
    # count, so genuinely novel records win slots before near-duplicates.
    novel_sentinel = float(config.max_items_after_crush + 1)
    for index, record in enumerate(records):
        canonical = _canonical(record)
        if canonical in seen:
            scores.append(0.0)
        elif index == 0:
            scores.append(novel_sentinel)
        else:
            scores.append(float(_field_change_count(record, previous)))
        seen.add(canonical)
        previous = record
    return scores


def _select_keep_indices(
    records: list, scores: list[float], config: SmartCrusherConfig
) -> set[int]:
    """Choose which record indices survive the crush.

    Always keeps the first and last record (positional anchors), plus every
    record whose distinctiveness score clears the variance threshold. If that
    set exceeds ``max_items_after_crush``, keeps the anchors plus the
    highest-scoring records up to the budget (ties broken by index for
    determinism), so the cap dominates the keep set.
    """
    n = len(records)
    anchors = {0, n - 1}
    distinctive = {
        i for i, score in enumerate(scores) if score >= config.variance_threshold
    }
    keep = anchors | distinctive
    if len(keep) <= config.max_items_after_crush:
        return keep
    optional = sorted(
        (i for i in keep if i not in anchors),
        key=lambda i: (-scores[i], i),
    )
    room = max(0, config.max_items_after_crush - len(anchors))
    return anchors | set(optional[:room])


def _assemble(
    records: list, keep: set[int]
) -> tuple[list, list[CCRSpan]]:
    """Walk the array, emitting kept records and one CCR marker per dropped run."""
    out: list = []
    dropped: list[CCRSpan] = []
    n = len(records)
    i = 0
    while i < n:
        if i in keep:
            out.append(records[i])
            i += 1
            continue
        start = i
        while i < n and i not in keep:
            i += 1
        span = records[start:i]
        span_hash = _content_hash(span)
        out.append(make_marker_object(span_hash, len(span)))
        dropped.append(CCRSpan(hash=span_hash, count=len(span), records=list(span)))
    return out, dropped


def smart_crush(
    records: list,
    config: SmartCrusherConfig | None = None,
    store: CCRWriter | None = None,
) -> CrushResult:
    """Compress a JSON array by collapsing low-variance duplicate runs.

    Args:
        records: the JSON array (a list of records of any JSON-serializable shape).
        config: tunables; defaults to :class:`SmartCrusherConfig`.
        store: an optional CCR write seam (any object with
            ``put(hash, original)``, e.g. a
            :class:`~nexus_context_compressor.ccr.store.CCRStore`). When given,
            each dropped span is persisted so its ``<<ccr:HASH N_rows>>`` marker
            can later be resolved back to the originals; the returned
            :class:`CrushResult` is identical either way. With ``store=None``
            (the default) the call has no side effects and stays pure.

    Returns:
        A :class:`CrushResult` whose ``records`` interleave kept records with
        ``{"_ccr_dropped": ...}`` markers in original order. Arrays shorter than
        ``config.min_items_to_analyze`` are returned unchanged.
    """
    config = config or SmartCrusherConfig()
    records = list(records)
    original_count = len(records)
    if original_count < config.min_items_to_analyze:
        return CrushResult(records=records, dropped=[], original_count=original_count)
    scores = _distinctiveness_scores(records, config)
    if len(scores) != original_count:
        raise ValueError(
            "distinctiveness scores must align 1:1 with records "
            f"({len(scores)} scores for {original_count} records)"
        )
    keep = _select_keep_indices(records, scores, config)
    out, dropped = _assemble(records, keep)
    if store is not None:
        # Persist after assembly so the pure scoring/selection logic above is
        # unaffected: the store is a write-only side channel keyed by the same
        # span hash embedded in each marker, making every drop reversible.
        for span in dropped:
            store.put(span.hash, span.records)
    return CrushResult(records=out, dropped=dropped, original_count=original_count)


def _demo_records() -> list:
    """A deterministic 100-item array: mostly repetitive with a few change-points.

    Used by ``python -m nexus_context_compressor.smart_crusher --demo`` to
    exercise the stability gate without external input. No randomness.
    """
    records: list = []
    for index in range(100):
        # Long repetitive runs of an identical "INFO heartbeat" with three
        # injected change-points (an ERROR at 25, a WARN at 60, an ERROR at 90).
        if index == 25:
            records.append({"level": "ERROR", "msg": "disk full", "code": 507})
        elif index == 60:
            records.append({"level": "WARN", "msg": "retry backoff", "code": 429})
        elif index == 90:
            records.append({"level": "ERROR", "msg": "timeout", "code": 504})
        else:
            records.append({"level": "INFO", "msg": "heartbeat", "code": 200})
    return records


def main(argv: list[str] | None = None) -> int:
    """CLI: crush a JSON array from a file, stdin, or the built-in demo."""
    import argparse
    import sys

    parser = argparse.ArgumentParser(
        prog="python -m nexus_context_compressor.smart_crusher",
        description="Deterministic JSON-array dedup with reversible CCR markers.",
    )
    parser.add_argument(
        "path",
        nargs="?",
        help="JSON file containing an array; reads stdin if omitted.",
    )
    parser.add_argument(
        "--demo",
        action="store_true",
        help="Crush a built-in deterministic 100-item array.",
    )
    parser.add_argument("--min-items", type=int, default=SmartCrusherConfig.min_items_to_analyze)
    parser.add_argument("--max-items", type=int, default=SmartCrusherConfig.max_items_after_crush)
    parser.add_argument("--variance-threshold", type=float, default=SmartCrusherConfig.variance_threshold)
    args = parser.parse_args(argv)

    if args.demo:
        records = _demo_records()
    else:
        raw = sys.stdin.read() if args.path is None else open(args.path, encoding="utf-8").read()
        records = json.loads(raw)
    if not isinstance(records, list):
        print("error: input must be a JSON array", file=sys.stderr)
        return 2

    config = SmartCrusherConfig(
        min_items_to_analyze=args.min_items,
        max_items_after_crush=args.max_items,
        variance_threshold=args.variance_threshold,
    )
    result = smart_crush(records, config)
    print(json.dumps(result.records, indent=2, ensure_ascii=False))
    print(
        f"[smart_crusher] {result.original_count} -> {result.kept_count} kept "
        f"+ {len(result.dropped)} CCR marker(s)",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    import sys

    sys.exit(main())
