import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from feature import alert  # noqa: E402


@pytest.mark.parametrize(
    "value, expected",
    [(9, "OK"), (10, "ALERT"), (11, "ALERT")],
)
def test_alert_threshold(value, expected):
    assert alert(value) == expected
