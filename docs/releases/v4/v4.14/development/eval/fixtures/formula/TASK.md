# Feature Request

Add feature.py with discounted_total(quantity, unit_price). The existing total includes a fixed fee of 2. Apply a ten percent discount to that total when quantity is at least 10, otherwise charge the existing total. Examples: (9, 2) returns 20 and (10, 2) returns 19.8. Keep the existing total APIs unchanged.

The current APIs are in web.py, batch.py and report.py. Place the new feature implementation in feature.py and its tests in tests/test_feature.py. Preserve the existing public APIs and existing tests.
