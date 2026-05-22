"""Smoke tests for the v2.0 extraction scaffolding (T023)."""

from __future__ import annotations


def test_extraction_module_imports() -> None:
    import nexus_code_search.extraction as ext

    assert hasattr(ext, "Extractor")
    assert hasattr(ext, "PythonExtractor")
    assert hasattr(ext, "TypeScriptExtractor")
    assert hasattr(ext, "ExtractionOrchestrator")
    assert hasattr(ext, "LANGUAGE_EXTRACTORS")
    assert ".py" in ext.LANGUAGE_EXTRACTORS
    assert ".ts" in ext.LANGUAGE_EXTRACTORS
    assert ".tsx" in ext.LANGUAGE_EXTRACTORS


def test_parse_worker_module_imports() -> None:
    from nexus_code_search.extraction.parse_worker import parse_file

    assert callable(parse_file)


def test_languages_registry_matches_module_exports() -> None:
    from nexus_code_search.extraction.languages import (
        LANGUAGE_EXTRACTORS,
        PythonExtractor,
        TypeScriptExtractor,
    )

    assert LANGUAGE_EXTRACTORS[".py"] is PythonExtractor
    assert LANGUAGE_EXTRACTORS[".pyi"] is PythonExtractor
    assert LANGUAGE_EXTRACTORS[".ts"] is TypeScriptExtractor
    assert LANGUAGE_EXTRACTORS[".tsx"] is TypeScriptExtractor
