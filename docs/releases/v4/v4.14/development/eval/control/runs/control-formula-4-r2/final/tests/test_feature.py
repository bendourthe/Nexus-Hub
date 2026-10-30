import pytest

from feature import discounted_total


@pytest.mark.parametrize(
    "quantity, unit_price, expected",
    [
        (9, 2, 20),
        (10, 2, 19.8),
        (11, 2, 21.6),
        (0, 5, 2),
        (100, 1, 91.8),
    ],
)
def test_discounted_total_applies_threshold(quantity, unit_price, expected):
    assert discounted_total(quantity, unit_price) == pytest.approx(expected)


def test_discounted_total_exact_values_from_request():
    assert discounted_total(9, 2) == 20
    assert discounted_total(10, 2) == 19.8
