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
        self.assertEqual(csv_row('A"B', 1), '"A""B: 1.00"\r\n')

    def test_newline_in_name_is_quoted(self):
        self.assertEqual(csv_row("A\nB", 1), '"A\nB: 1.00"\r\n')

    def test_round_trips_as_single_field(self):
        rows = list(csv.reader(io.StringIO(csv_row("A,B", 2), newline="")))
        self.assertEqual(rows, [["A,B: 2.00"]])


if __name__ == "__main__":
    unittest.main()
