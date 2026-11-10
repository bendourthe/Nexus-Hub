import csv
import io

from web import display


def csv_row(name, value):
    buffer = io.StringIO()
    csv.writer(buffer, lineterminator="\r\n").writerow([display(name, value)])
    return buffer.getvalue()
