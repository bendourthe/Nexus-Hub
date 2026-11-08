# Feature Request

Add feature.py with alert(value). Return "ALERT" when the existing numeric threshold is reached, otherwise "OK". Examples: 9 returns "OK", 10 and 11 return "ALERT". Keep the existing reached APIs unchanged.

The current APIs are in web.py, batch.py and report.py. Place the new feature implementation in feature.py and its tests in tests/test_feature.py. Preserve the existing public APIs and existing tests.
