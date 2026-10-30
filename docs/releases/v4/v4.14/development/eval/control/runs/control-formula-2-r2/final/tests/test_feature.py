import unittest

from feature import discounted_total


class DiscountedTotal(unittest.TestCase):
    def test_below_threshold_has_no_discount(self):
        self.assertEqual(discounted_total(9, 2), 20)

    def test_at_threshold_is_discounted(self):
        self.assertEqual(discounted_total(10, 2), 19.8)

    def test_above_threshold_is_discounted(self):
        self.assertAlmostEqual(discounted_total(20, 5), 102 * 0.9)

    def test_zero_quantity_charges_fee_only(self):
        self.assertEqual(discounted_total(0, 10), 2)


if __name__ == "__main__":
    unittest.main()
