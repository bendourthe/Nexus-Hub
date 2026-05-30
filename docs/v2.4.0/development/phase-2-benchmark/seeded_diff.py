"""Seeded benchmark fixture for the multi-agent-code-review pipeline (Phase 2 / T012).

This file contains three deliberately-planted cases so the review pipeline can be
checked for true positives and the absence of false positives:

  1. paginate()      - a CORRECTNESS bug (off-by-one: page * size skips the first page).
  2. find_user()     - a SECURITY bug (SQL injection: user input concatenated into the query).
  3. clamp()         - a CLEAN function with no defects (the false-positive control).

Expected pipeline behavior (report-only mode):
  - correctness persona surfaces a P0/P1 finding on paginate() at the offset line.
  - security persona surfaces a P0 SQL-injection finding on find_user() at the query line.
  - no persona emits a substantiated (>= anchor 75) finding on clamp().
"""

from __future__ import annotations


def paginate(items: list, page: int, size: int) -> list:
    # BUG (correctness): for 1-based pages this skips the first page.
    # Correct offset is (page - 1) * size.
    offset = page * size
    return items[offset:offset + size]


def find_user(cursor, username: str):
    # BUG (security): username is concatenated directly into the SQL string.
    query = "SELECT * FROM users WHERE name = '" + username + "'"
    cursor.execute(query)
    return cursor.fetchone()


def clamp(value: int, low: int, high: int) -> int:
    # CLEAN: correct, total, no defect. Should not draw a substantiated finding.
    if value < low:
        return low
    if value > high:
        return high
    return value
