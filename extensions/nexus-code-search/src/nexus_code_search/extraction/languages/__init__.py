"""Per-language extractor modules + registry.

Adding a new language: implement an `Extractor` subclass that returns
(nodes, edges) and register the file-extension keys in
`LANGUAGE_EXTRACTORS`. The orchestrator dispatches by extension only - it
does not introspect file contents.
"""

from __future__ import annotations

from nexus_code_search.extraction.languages.base import Extractor
from nexus_code_search.extraction.languages.c import CExtractor
from nexus_code_search.extraction.languages.cpp import CppExtractor
from nexus_code_search.extraction.languages.csharp import CSharpExtractor
from nexus_code_search.extraction.languages.go import GoExtractor
from nexus_code_search.extraction.languages.java import JavaExtractor
from nexus_code_search.extraction.languages.php import PhpExtractor
from nexus_code_search.extraction.languages.python import PythonExtractor
from nexus_code_search.extraction.languages.ruby import RubyExtractor
from nexus_code_search.extraction.languages.rust import RustExtractor
from nexus_code_search.extraction.languages.typescript import TypeScriptExtractor

LANGUAGE_EXTRACTORS: dict[str, type[Extractor]] = {
    ".py": PythonExtractor,
    ".pyi": PythonExtractor,
    ".ts": TypeScriptExtractor,
    ".tsx": TypeScriptExtractor,
    ".mts": TypeScriptExtractor,
    ".cts": TypeScriptExtractor,
    ".go": GoExtractor,
    ".rs": RustExtractor,
    ".java": JavaExtractor,
    ".cs": CSharpExtractor,
    ".csx": CSharpExtractor,
    ".rb": RubyExtractor,
    ".php": PhpExtractor,
    ".c": CExtractor,
    ".h": CExtractor,
    ".cpp": CppExtractor,
    ".cc": CppExtractor,
    ".cxx": CppExtractor,
    ".hpp": CppExtractor,
    ".hh": CppExtractor,
    ".hxx": CppExtractor,
}

__all__ = [
    "Extractor",
    "LANGUAGE_EXTRACTORS",
    "CExtractor",
    "CppExtractor",
    "CSharpExtractor",
    "GoExtractor",
    "JavaExtractor",
    "PhpExtractor",
    "PythonExtractor",
    "RubyExtractor",
    "RustExtractor",
    "TypeScriptExtractor",
]
