import pytest

from feature import discounted_total


@pytest.mark.parametrize(
    "quantity, unit_price, expected",
    [
        (9, 2, 20),
        (10, 2, 19.8),
        (11, 2, 21.6),
        (0, 5, 2),
        (1, 3, 5),
        (100, 1, 91.8),
    ],
)
def test_discounted_total_applies_discount_from_ten_units(quantity, unit_price, expected):
    assert discounted_total(quantity, unit_price) == pytest.approx(expected)


def test_discounted_total_matches_spec_examples_exactly():
    assert discounted_total(9, 2) == 20
    assert discounted_total(10, 2) == 19.8


def test_discounted_total_below_threshold_equals_existing_total():
    from web import total

    for quantity in range(0, 10):
        assert discounted_total(quantity, 4) == total(quantity, 4)
