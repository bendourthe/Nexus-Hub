"""Analyzer base contract and the per-file scanning unit.

Every analyzer receives a ``FileUnit`` (a discovered file with its text and a
few derived flags) and returns a list of ``Finding``. The scanner runs each
registered analyzer over each unit and aggregates the results. MCP-config
analyzers ignore non-config files; AST analyzers ignore non-Python files; text
analyzers run on Markdown and scripts alike but use the fence flag to suppress
documentation matches.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol

from ..frameworks import class_name, framework_ids_for
from ..types import Finding, Severity

# File suffixes the scanner treats as executable scripts (drives the scoring
# multiplier and gates the AST analyzer). A construct in one of these is
# weightier than the same construct quoted in Markdown prose.
EXECUTABLE_SUFFIXES = frozenset(
    {".py", ".sh", ".bash", ".js", ".mjs", ".cjs", ".ts", ".ps1", ".rb", ".pl"}
)
MARKDOWN_SUFFIXES = frozenset({".md", ".markdown"})

SNIPPET_MAX = 160


@dataclass
class FileUnit:
    """One file to analyze, with its text and derived flags."""

    path: Path
    rel: str
    text: str
    suffix: str = ""
    is_markdown: bool = False
    is_executable: bool = False

    @classmethod
    def from_path(cls, path: Path, rel: str, text: str) -> "FileUnit":
        suffix = path.suffix.lower()
        return cls(
            path=path,
            rel=rel,
            text=text,
            suffix=suffix,
            is_markdown=suffix in MARKDOWN_SUFFIXES,
            is_executable=suffix in EXECUTABLE_SUFFIXES,
        )


def make_finding(
    *,
    detection_class: int,
    severity: Severity,
    title: str,
    message: str,
    unit: FileUnit,
    line: int = 0,
    snippet: str = "",
    analyzer: str = "",
) -> Finding:
    """Construct a ``Finding`` with the class name, framework IDs, and the
    executable flag filled in from the taxonomy and the file unit."""
    return Finding(
        detection_class=detection_class,
        class_name=class_name(detection_class),
        severity=severity,
        title=title,
        message=message,
        file=unit.rel,
        line=line,
        snippet=(snippet[:SNIPPET_MAX].strip()),
        framework_ids=framework_ids_for(detection_class),
        executable=unit.is_executable,
        analyzer=analyzer or "unknown",
    )


class Analyzer(Protocol):
    """An analyzer inspects one file unit and returns findings."""

    name: str

    def analyze(self, unit: FileUnit) -> list[Finding]:
        ...


@dataclass
class AnalyzerResult:
    """Wraps a partial scan: findings plus any modules that were skipped
    (e.g. an optional engine whose dependency is absent)."""

    findings: list[Finding] = field(default_factory=list)
    skipped: list[str] = field(default_factory=list)
