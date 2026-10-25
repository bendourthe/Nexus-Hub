# Feature Request

Add feature.py with csv_row(name, value). Return one CSV row containing a single field whose text uses the existing display format. Use standard CSV quoting and a CRLF row terminator. Examples: ("A", 1.2) returns "A: 1.20\r\n" and a name containing a comma requires the field to be quoted. Keep the existing display APIs unchanged.

The current APIs are in web.py, batch.py and report.py. Place the new feature implementation in feature.py and its tests in tests/test_feature.py. Preserve the existing public APIs and existing tests.
