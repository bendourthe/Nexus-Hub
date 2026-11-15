import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from feature import discounted_total  # noqa: E402


class DiscountedTotal(unittest.TestCase):
    def test_below_threshold_charges_existing_total(self):
        self.assertEqual(discounted_total(9, 2), 20)

    def test_at_threshold_applies_ten_percent_discount(self):
        self.assertEqual(discounted_total(10, 2), 19.8)

    def test_above_threshold_applies_ten_percent_discount(self):
        self.assertEqual(discounted_total(20, 5), 91.8)

    def test_zero_quantity_charges_fixed_fee_only(self):
        self.assertEqual(discounted_total(0, 10), 2)


if __name__ == "__main__":
    unittest.main()
