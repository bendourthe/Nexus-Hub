import importlib.util
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import feature  # noqa: E402


def _load(name):
    spec = importlib.util.spec_from_file_location("subject_" + name, ROOT / (name + ".py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize(
    "value, expected",
    [(9, "OK"), (10, "ALERT"), (11, "ALERT"), (0, "OK"), (-5, "OK"), (9.99, "OK"), (10.0, "ALERT")],
)
def test_alert_returns_expected_status(value, expected):
    assert feature.alert(value) == expected


@pytest.mark.parametrize("name", ["web", "batch", "report"])
@pytest.mark.parametrize("value", [9, 10, 11])
def test_alert_agrees_with_each_reached_api(name, value):
    reached = _load(name).reached(value)
    assert (feature.alert(value) == "ALERT") is reached
