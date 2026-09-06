"""Core result types for the skill-security scanner.

A scan produces a ``ScanResult`` carrying a list of ``Finding`` objects, a
numeric risk score, and a severity ``Band``. Severity points and band
thresholds follow the design in ``docs/releases/v3/v3.0/comparisons/v3.0.0-comparison-skillspector.md``
Section 3 (scoring) and Section 9.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class Severity(Enum):
    """Per-finding severity, ordered, with the risk-score point value.

    Point values: CRITICAL +50, HIGH +25, MEDIUM +10, LOW +5. A finding in an
    executable script is multiplied by ``EXEC_MULTIPLIER`` when scored (a
    dangerous construct that actually runs is weightier than the same construct
    quoted in prose).
    """

    CRITICAL = ("critical", 50, 4)
    HIGH = ("high", 25, 3)
    MEDIUM = ("medium", 10, 2)
    LOW = ("low", 5, 1)

    def __init__(self, label: str, points: int, rank: int) -> None:
        self.label = label
        self.points = points
        self.rank = rank

    @classmethod
    def from_label(cls, label: str) -> "Severity":
        for member in cls:
            if member.label == label.lower():
                return member
        raise ValueError(f"unknown severity: {label!r}")

    def __ge__(self, other: object) -> bool:
        if not isinstance(other, Severity):
            return NotImplemented
        return self.rank >= other.rank

    def __gt__(self, other: object) -> bool:
        if not isinstance(other, Severity):
            return NotImplemented
        return self.rank > other.rank


class Band(Enum):
    """The aggregate risk band derived from the total score (0-100)."""

    LOW = ("low", 0, 20)
    MEDIUM = ("medium", 21, 50)
    HIGH = ("high", 51, 80)
    CRITICAL = ("critical", 81, 100)

    def __init__(self, label: str, lo: int, hi: int) -> None:
        self.label = label
        self.lo = lo
        self.hi = hi
        self.rank = {"low": 1, "medium": 2, "high": 3, "critical": 4}[label]

    @classmethod
    def from_score(cls, score: int) -> "Band":
        for band in (cls.CRITICAL, cls.HIGH, cls.MEDIUM, cls.LOW):
            if score >= band.lo:
                return band
        return cls.LOW

    @classmethod
    def from_label(cls, label: str) -> "Band":
        for member in cls:
            if member.label == label.lower():
                return member
        raise ValueError(f"unknown band: {label!r}")

    def __ge__(self, other: object) -> bool:
        if not isinstance(other, Band):
            return NotImplemented
        return self.rank >= other.rank


@dataclass(frozen=True)
class Finding:
    """One detected construct.

    Attributes:
        detection_class: the 1-16 class number from the detection taxonomy.
        class_name: human-readable class name (e.g., "Prompt Injection").
        severity: per-finding severity.
        title: short finding label.
        message: plain-language explanation of what the construct does / why
            it is dangerous (the deterministic engine's best guess; the
            semantic-adjudication skill refines this).
        file: repository-relative file path of the match.
        line: 1-based line number (0 when not line-scoped, e.g. a JSON key).
        snippet: the matched construct, truncated for display.
        framework_ids: MITRE ATT&CK / ATLAS / D3FEND / NIST identifiers.
        executable: whether the host file is an executable script (drives the
            scoring multiplier).
        analyzer: the analyzer module that produced the finding.
    """

    detection_class: int
    class_name: str
    severity: Severity
    title: str
    message: str
    file: str
    line: int = 0
    snippet: str = ""
    framework_ids: tuple[str, ...] = ()
    executable: bool = False
    analyzer: str = ""

    def location(self) -> str:
        return f"{self.file}:{self.line}" if self.line else self.file


@dataclass
class ScanResult:
    """The aggregate result of scanning one or more targets."""

    target: str
    findings: list[Finding] = field(default_factory=list)
    files_scanned: int = 0
    score: int = 0
    band: Band = Band.LOW
    skipped_modules: list[str] = field(default_factory=list)

    def counts_by_severity(self) -> dict[str, int]:
        counts = {s.label: 0 for s in Severity}
        for finding in self.findings:
            counts[finding.severity.label] += 1
        return counts

    def max_severity(self) -> Severity | None:
        if not self.findings:
            return None
        return max((f.severity for f in self.findings), key=lambda s: s.rank)
