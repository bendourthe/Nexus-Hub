import csv
import io
import unittest

from feature import csv_row


class CsvRow(unittest.TestCase):
    def test_plain_name(self):
        self.assertEqual(csv_row("A", 1.2), "A: 1.20\r\n")

    def test_negative_value(self):
        self.assertEqual(csv_row("negative", -1.25), "negative: -1.25\r\n")

    def test_comma_in_name_is_quoted(self):
        self.assertEqual(csv_row("A,B", 2), '"A,B: 2.00"\r\n')

    def test_quote_in_name_is_doubled(self):
        self.assertEqual(csv_row('A"B', 2), '"A""B: 2.00"\r\n')

    def test_newline_in_name_is_quoted(self):
        self.assertEqual(csv_row("A\nB", 2), '"A\nB: 2.00"\r\n')

    def test_round_trips_to_single_field(self):
        for name in ("A", "A,B", 'A"B', "A\r\nB"):
            with self.subTest(name=name):
                rows = list(csv.reader(io.StringIO(csv_row(name, 1.2), newline="")))
                self.assertEqual(rows, [[f"{name}: 1.20"]])


if __name__ == "__main__":
    unittest.main()
