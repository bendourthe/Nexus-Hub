"""AST-based extraction subsystem for nexus-code-search v2.0.

The extraction pipeline turns source files into NodeKind / EdgeKind records
backed by SQLite. It is intentionally separable from the v1.0.0 chunk +
keyword index so callers can mix-and-match: a project might run only the
keyword search for fast iteration, or the AST graph for symbol-precise
queries, or both.

Local-only by policy: no network calls, no model downloads, no telemetry.

Public surface:
    Extractor               Abstract base class every per-language extractor
                            implements.
    PythonExtractor         Per-language extractor for `.py` sources.
    TypeScriptExtractor     Per-language extractor for `.ts`, `.tsx` sources.
    LANGUAGE_EXTRACTORS     Registry mapping file-extension -> Extractor class.
    ExtractionOrchestrator  High-level entry point: walks files, dispatches
                            to the right extractor, persists rows.
    parse_file              Lower-level helper used by orchestrator + worker.
"""

from __future__ import annotations

from nexus_code_search.extraction.languages import (
    LANGUAGE_EXTRACTORS,
    Extractor,
    PythonExtractor,
    TypeScriptExtractor,
)
from nexus_code_search.extraction.orchestrator import ExtractionOrchestrator
from nexus_code_search.extraction.parse_worker import parse_file

__all__ = [
    "Extractor",
    "ExtractionOrchestrator",
    "LANGUAGE_EXTRACTORS",
    "PythonExtractor",
    "TypeScriptExtractor",
    "parse_file",
]
