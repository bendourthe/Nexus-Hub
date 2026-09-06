"""Risk scoring and severity-band derivation.

Scoring model (from ``docs/releases/v3/v3.0/comparisons/v3.0.0-comparison-skillspector.md`` Section 3):

    - Per-finding points: CRITICAL +50, HIGH +25, MEDIUM +10, LOW +5.
    - Executable-script multiplier: a finding whose host file is an executable
      script (a script the skill actually runs) is multiplied by 1.3 -- a
      dangerous construct that executes is weightier than the same construct
      quoted in prose.
    - The total is capped at 100 and mapped to a band:
        0-20   LOW
        21-50  MEDIUM
        51-80  HIGH
        81-100 CRITICAL
"""

from __future__ import annotations

from collections.abc import Iterable

from .types import Band, Finding

EXEC_MULTIPLIER = 1.3
MAX_SCORE = 100


def score_findings(findings: Iterable[Finding]) -> tuple[int, Band]:
    """Return the aggregate ``(score, band)`` for a set of findings."""
    total = 0.0
    for finding in findings:
        points = finding.severity.points
        if finding.executable:
            points *= EXEC_MULTIPLIER
        total += points
    score = min(MAX_SCORE, round(total))
    return score, Band.from_score(score)
