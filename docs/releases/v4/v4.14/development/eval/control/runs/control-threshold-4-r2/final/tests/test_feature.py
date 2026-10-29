import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


def load_feature():
    spec = importlib.util.spec_from_file_location("subject_feature", ROOT / "feature.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class AlertBehavior(unittest.TestCase):
    def test_alert_matches_threshold(self):
        feature = load_feature()
        for value, expected in [(9, "OK"), (10, "ALERT"), (11, "ALERT")]:
            with self.subTest(value=value):
                self.assertEqual(feature.alert(value), expected)
