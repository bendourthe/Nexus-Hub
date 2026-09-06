"""BYO filter trust gate: untrusted skipped, trusted applied, edit invalidates."""

from __future__ import annotations

import json
from pathlib import Path

from nexus_context_compressor.filters import (
    apply_trusted_filters,
    run_inline_tests,
    trust,
    untrust,
)


def _filter_doc() -> dict:
    return {
        "filters": [
            {
                "name": "drop-debug",
                "pattern": r"^DEBUG\b",
                "action": "drop-line",
            }
        ],
        "tests": [
            {
                "name": "drops debug",
                "input": "DEBUG noisy\nINFO keep\n",
                "expected": "INFO keep\n",
            }
        ],
    }


def test_untrusted_filter_is_not_applied(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("NEXUS_COMPRESSOR_TRUST_STORE", str(tmp_path / "trust.json"))
    monkeypatch.setenv("NEXUS_COMPRESSOR_GLOBAL_FILTERS", str(tmp_path / "missing.json"))
    project = tmp_path / ".nexus-hub"
    project.mkdir()
    path = project / "compressor-filters.json"
    path.write_text(json.dumps(_filter_doc()), encoding="utf-8")
    text = "DEBUG noisy\nINFO keep\n"
    assert apply_trusted_filters(text, cwd=tmp_path) == text


def test_trusted_filter_is_applied(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("NEXUS_COMPRESSOR_TRUST_STORE", str(tmp_path / "trust.json"))
    monkeypatch.setenv("NEXUS_COMPRESSOR_GLOBAL_FILTERS", str(tmp_path / "missing.json"))
    project = tmp_path / ".nexus-hub"
    project.mkdir()
    path = project / "compressor-filters.json"
    path.write_text(json.dumps(_filter_doc()), encoding="utf-8")
    trust(path)
    out = apply_trusted_filters("DEBUG noisy\nINFO keep\n", cwd=tmp_path)
    assert out == "INFO keep\n"


def test_editing_a_trusted_filter_re_invalidates(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("NEXUS_COMPRESSOR_TRUST_STORE", str(tmp_path / "trust.json"))
    monkeypatch.setenv("NEXUS_COMPRESSOR_GLOBAL_FILTERS", str(tmp_path / "missing.json"))
    project = tmp_path / ".nexus-hub"
    project.mkdir()
    path = project / "compressor-filters.json"
    path.write_text(json.dumps(_filter_doc()), encoding="utf-8")
    trust(path)
    path.write_text(
        json.dumps(
            {
                "filters": [
                    {"name": "drop-info", "pattern": r"^INFO\b", "action": "drop-line"}
                ]
            }
        ),
        encoding="utf-8",
    )
    text = "DEBUG noisy\nINFO keep\n"
    assert apply_trusted_filters(text, cwd=tmp_path) == text
    trust(path)
    assert apply_trusted_filters(text, cwd=tmp_path) == "DEBUG noisy\n"


def test_untrust_stops_application(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("NEXUS_COMPRESSOR_TRUST_STORE", str(tmp_path / "trust.json"))
    monkeypatch.setenv("NEXUS_COMPRESSOR_GLOBAL_FILTERS", str(tmp_path / "missing.json"))
    project = tmp_path / ".nexus-hub"
    project.mkdir()
    path = project / "compressor-filters.json"
    path.write_text(json.dumps(_filter_doc()), encoding="utf-8")
    trust(path)
    untrust(path)
    text = "DEBUG noisy\nINFO keep\n"
    assert apply_trusted_filters(text, cwd=tmp_path) == text


def test_verify_runs_inline_tests(tmp_path: Path) -> None:
    path = tmp_path / "filters.json"
    path.write_text(json.dumps(_filter_doc()), encoding="utf-8")
    rows = run_inline_tests(path)
    assert rows == [("drops debug", True, "ok")]
