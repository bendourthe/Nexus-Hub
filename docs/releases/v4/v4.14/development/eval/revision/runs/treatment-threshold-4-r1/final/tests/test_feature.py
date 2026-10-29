import pytest

import batch
import report
import web
from feature import alert


@pytest.mark.parametrize("value, expected", [(9, "OK"), (10, "ALERT"), (11, "ALERT")])
def test_alert_uses_threshold(value, expected):
    assert alert(value) == expected


@pytest.mark.parametrize("module", [web, batch, report])
@pytest.mark.parametrize("value", [9, 10, 11])
def test_alert_matches_reached(module, value):
    assert (alert(value) == "ALERT") == module.reached(value)
