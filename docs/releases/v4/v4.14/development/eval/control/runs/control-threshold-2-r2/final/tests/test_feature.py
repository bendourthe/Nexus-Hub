import unittest

from feature import alert


class AlertFeature(unittest.TestCase):
    def test_alert_threshold(self):
        for value, expected in [(9, "OK"), (10, "ALERT"), (11, "ALERT")]:
            with self.subTest(value=value):
                self.assertEqual(alert(value), expected)
