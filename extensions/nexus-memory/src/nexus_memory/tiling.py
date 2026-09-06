"""Age-decaying read tiling.

Given N entries and a line budget B, choose an ordered list of aligned
power-of-two ranges covering the store. Detail decays with age: recent
entries stay verbatim, ancient ones collapse. This is a pure function
over integers with no I/O.

When the store fits in the budget, each entry is its own range and
nothing is compressed. Otherwise a single decay parameter is binary-
searched so a range stays whole when its size is at most that parameter
times its age (distance from the newest edge). Because range sizes move
in powers of two the search can undershoot; leftover budget is spent by
repeatedly splitting the newest non-singleton range.
"""

from __future__ import annotations


def tile(n: int, budget: int) -> list[tuple[int, int]]:
    """Return aligned ranges covering ``[0, n)``, at most *budget* of them.

    Ranges are ``(lo, hi)`` with ``hi`` exclusive. Index ``n - 1`` is the
    newest entry. *budget* is a line count, one line per range.
    """
    if n < 0:
        raise ValueError(f"n must be >= 0, got {n}")
    if budget < 1 and n > 0:
        raise ValueError(f"budget must be >= 1 when n > 0, got {budget}")
    if n == 0:
        return []
    if n <= budget:
        return [(i, i + 1) for i in range(n)]

    coarsest = _tiling_for_decay(n, float(n))
    if len(coarsest) >= budget:
        # Aligned power-of-two cover of [0, n) has a hard minimum
        # (the binary weight of n, plus the newest singleton). A
        # budget below that minimum cannot be honored without a gap
        # or an unaligned range; return the coarsest legal tiling.
        return coarsest
    best = coarsest
    lo, hi = 0.0, float(n)
    for _ in range(48):
        mid = (lo + hi) / 2.0
        candidate = _tiling_for_decay(n, mid)
        if len(candidate) <= budget:
            best = candidate
            hi = mid
        else:
            lo = mid
    return _spend_remainder(best, budget)


def _tiling_for_decay(n: int, decay: float) -> list[tuple[int, int]]:
    """Cover ``[0, n)`` walking backward from the newest entry."""
    ranges: list[tuple[int, int]] = []
    pos = n
    while pos > 0:
        age = n - pos
        size = 1
        while True:
            nxt = size * 2
            if nxt > pos:
                break
            if (pos - nxt) % nxt != 0:
                break
            if nxt <= decay * age:
                size = nxt
                continue
            break
        ranges.append((pos - size, pos))
        pos -= size
    ranges.reverse()
    return ranges


def _spend_remainder(
    ranges: list[tuple[int, int]],
    budget: int,
) -> list[tuple[int, int]]:
    """Split the newest non-singleton until the budget is used or all are singles."""
    out = list(ranges)
    while len(out) < budget:
        split_at = None
        for i in range(len(out) - 1, -1, -1):
            lo, hi = out[i]
            if hi - lo > 1:
                split_at = i
                break
        if split_at is None:
            break
        lo, hi = out[split_at]
        mid = (lo + hi) // 2
        out[split_at : split_at + 1] = [(lo, mid), (mid, hi)]
    return out
