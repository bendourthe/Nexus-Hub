"""Property and explicit tests for age-decaying tiling."""

from __future__ import annotations

import random

import pytest

from nexus_memory.tiling import tile


def _assert_invariants(n: int, budget: int, ranges: list[tuple[int, int]]) -> None:
    assert sum(hi - lo for lo, hi in ranges) == n
    covered: list[int] = []
    for lo, hi in ranges:
        assert 0 <= lo < hi <= n
        size = hi - lo
        assert size & (size - 1) == 0
        assert lo % size == 0
        covered.extend(range(lo, hi))
    assert covered == list(range(n))
    if n > 0:
        minimum = len(tile(n, 1))
        assert len(ranges) <= max(budget, minimum)
    sizes = [hi - lo for lo, hi in ranges]
    for earlier, later in zip(sizes, sizes[1:]):
        assert later <= earlier


@pytest.mark.parametrize(
    "n,budget",
    [
        (0, 10),
        (1, 10),
        (5, 10),
        (10, 10),
        (11, 10),
        (16, 8),
        (32, 8),
        (100, 20),
        (256, 16),
        (1000, 40),
    ],
)
def test_tiling_invariants(n: int, budget: int) -> None:
    ranges = tile(n, budget)
    _assert_invariants(n, budget, ranges)


def test_under_budget_is_all_singletons() -> None:
    ranges = tile(7, 20)
    assert ranges == [(i, i + 1) for i in range(7)]


def test_exactly_at_budget_is_all_singletons() -> None:
    ranges = tile(8, 8)
    assert ranges == [(i, i + 1) for i in range(8)]


def test_far_over_budget_stays_within_budget() -> None:
    ranges = tile(500, 12)
    assert len(ranges) <= 12
    _assert_invariants(500, 12, ranges)
    assert ranges[-1][1] - ranges[-1][0] == 1


def test_impossible_tiny_budget_returns_coarsest_cover() -> None:
    ranges = tile(198, 3)
    assert ranges == tile(198, 1)
    _assert_invariants(198, 3, ranges)


def test_random_pairs_obey_invariants() -> None:
    rng = random.Random(20260823)
    for _ in range(40):
        n = rng.randint(0, 400)
        budget = rng.randint(1, 80)
        _assert_invariants(n, budget, tile(n, budget))
