"""Per-language extractor modules + registry.

Adding a new language: implement an `Extractor` subclass that returns
(nodes, edges) and register the file-extension keys in
`LANGUAGE_EXTRACTORS`. The orchestrator dispatches by extension only - it
does not introspect file contents.
"""

from __future__ import annotations

from nexus_code_search.extraction.languages.base import Extractor
from nexus_code_search.extraction.languages.python import PythonExtractor
from nexus_code_search.extraction.languages.typescript import TypeScriptExtractor

LANGUAGE_EXTRACTORS: dict[str, type[Extractor]] = {
    ".py": PythonExtractor,
    ".pyi": PythonExtractor,
    ".ts": TypeScriptExtractor,
    ".tsx": TypeScriptExtractor,
    ".mts": TypeScriptExtractor,
    ".cts": TypeScriptExtractor,
}

__all__ = [
    "Extractor",
    "LANGUAGE_EXTRACTORS",
    "PythonExtractor",
    "TypeScriptExtractor",
]
