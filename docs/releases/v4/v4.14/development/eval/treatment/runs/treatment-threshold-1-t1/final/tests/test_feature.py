import pytest

from feature import alert


@pytest.mark.parametrize(
    ("value", "expected"),
    [(9, "OK"), (10, "ALERT"), (11, "ALERT")],
)
def test_alert_matches_threshold(value, expected):
    assert alert(value) == expected
