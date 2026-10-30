import csv
import io

import pytest

from feature import csv_row


@pytest.mark.parametrize(
    "name, value, expected",
    [
        ("A", 1.2, "A: 1.20\r\n"),
        ("negative", -1.25, "negative: -1.25\r\n"),
        ("A,B", 2, '"A,B: 2.00"\r\n'),
        ('say "hi"', 3, '"say ""hi"": 3.00"\r\n'),
        ("two\nlines", 1, '"two\nlines: 1.00"\r\n'),
    ],
)
def test_csv_row_formats_and_quotes(name, value, expected):
    assert csv_row(name, value) == expected


@pytest.mark.parametrize("name", ["A", "A,B", 'say "hi"', "two\nlines"])
def test_csv_row_round_trips_as_single_field(name):
    rows = list(csv.reader(io.StringIO(csv_row(name, 1.2), newline="")))
    assert rows == [[f"{name}: 1.20"]]
