import csv
import io
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from feature import csv_row  # noqa: E402


class CsvRow(unittest.TestCase):
    def test_plain_name(self):
        self.assertEqual(csv_row("A", 1.2), "A: 1.20\r\n")

    def test_negative_value(self):
        self.assertEqual(csv_row("negative", -1.25), "negative: -1.25\r\n")

    def test_comma_in_name_is_quoted(self):
        self.assertEqual(csv_row("A,B", 2), '"A,B: 2.00"\r\n')

    def test_quote_in_name_is_doubled(self):
        self.assertEqual(csv_row('say "hi"', 1), '"say ""hi"": 1.00"\r\n')

    def test_newline_in_name_is_quoted(self):
        self.assertEqual(csv_row("a\nb", 1), '"a\nb: 1.00"\r\n')

    def test_single_field_round_trip(self):
        row = csv_row("A,B", 2)
        rows = list(csv.reader(io.StringIO(row, newline="")))
        self.assertEqual(rows, [["A,B: 2.00"]])

    def test_single_row_with_crlf_terminator(self):
        row = csv_row("A", 1.2)
        self.assertTrue(row.endswith("\r\n"))
        self.assertEqual(row.count("\r\n"), 1)


if __name__ == "__main__":
    unittest.main()
