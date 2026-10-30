import csv
import io
import unittest

import batch
import report
import web
from feature import csv_row


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
        for name in ("A", "A,B", 'q"uote', "line\nbreak"):
            with self.subTest(name=name):
                rows = list(csv.reader(io.StringIO(csv_row(name, 3.5), newline="")))
                self.assertEqual(rows, [[web.display(name, 3.5)]])

    def test_matches_every_existing_display(self):
        for module in (web, batch, report):
            with self.subTest(module=module.__name__):
                self.assertEqual(csv_row("A", 1.2), module.display("A", 1.2) + "\r\n")

    def test_exactly_one_row_terminator(self):
        self.assertEqual(csv_row("A", 1.2).count("\r\n"), 1)
        self.assertTrue(csv_row("A", 1.2).endswith("\r\n"))


if __name__ == "__main__":
    unittest.main()
