import pytest

from feature import alert


@pytest.mark.parametrize(
    ("value", "expected"),
    [(9, "OK"), (10, "ALERT"), (11, "ALERT")],
)
def test_alert_returns_status_for_threshold(value, expected):
    assert alert(value) == expected
