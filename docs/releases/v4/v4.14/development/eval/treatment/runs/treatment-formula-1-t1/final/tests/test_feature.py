import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import batch  # noqa: E402
import report  # noqa: E402
import web  # noqa: E402
from feature import discounted_total  # noqa: E402


@pytest.mark.parametrize(
    "quantity, unit_price, expected",
    [
        (9, 2, 20),
        (10, 2, 19.8),
        (11, 2, 21.6),
        (1, 5, 7),
        (0, 10, 2),
        (100, 1, 91.8),
    ],
)
def test_discounted_total_matches_examples(quantity, unit_price, expected):
    assert discounted_total(quantity, unit_price) == pytest.approx(expected)


def test_below_threshold_equals_existing_total():
    assert discounted_total(9, 2) == web.total(9, 2)


def test_threshold_applies_ten_percent_to_fee_inclusive_total():
    assert discounted_total(10, 2) == pytest.approx(web.total(10, 2) * 0.9)


def test_existing_total_apis_are_unchanged():
    for module in (web, batch, report):
        assert module.total(10, 2) == 22
        assert module.total(2, 3) == 8
