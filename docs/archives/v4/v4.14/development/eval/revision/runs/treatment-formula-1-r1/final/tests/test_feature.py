import pytest

from feature import discounted_total


@pytest.mark.parametrize(
    "quantity, unit_price, expected",
    [
        (9, 2, 20),
        (10, 2, 19.8),
        (0, 5, 2),
        (1, 3, 5),
        (11, 1, 11.7),
        (100, 2, 181.8),
    ],
)
def test_discounted_total_matches_examples(quantity, unit_price, expected):
    assert discounted_total(quantity, unit_price) == pytest.approx(expected)


def test_discounted_total_below_threshold_equals_existing_total():
    from web import total

    assert discounted_total(9, 7) == total(9, 7)


def test_discounted_total_at_threshold_is_ninety_percent_of_existing_total():
    from web import total

    assert discounted_total(10, 7) == pytest.approx(total(10, 7) * 0.9)
