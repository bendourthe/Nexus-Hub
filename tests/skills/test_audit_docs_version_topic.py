"""Unit coverage for audit-docs.py version/topic resolution across both docs schemes.

Regression guard for the v3.11.0 Phase 1 two-level minor-grouped layout
(``docs/v<MAJOR>/v<MAJOR>.<MINOR>/<topic>/...``) alongside the legacy flat layout
(``docs/<vSEMVER>/<topic>/...``). The audit-docs.py helper ships with a hyphen in
its filename, so it is loaded by path via importlib rather than imported.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

_MODULE_PATH = (
    Path(__file__).resolve().parents[2]
    / "catalog"
    / "skills"
    / "code-cleanup"
    / "docs-layout-refactor"
    / "scripts"
    / "audit-docs.py"
)


def _load_audit_docs():
    spec = importlib.util.spec_from_file_location("audit_docs", _MODULE_PATH)
    assert spec and spec.loader, f"cannot load {_MODULE_PATH}"
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


audit = _load_audit_docs()

DOCS_ROOT = Path("/repo/docs")


@pytest.mark.parametrize(
    "rel_path, expected_version, expected_topic",
    [
        # Two-level minor-grouped scheme (v3.11.0+).
        ("v3/v3.10/plans/foo.md", "v3.10", "plans"),
        ("v3/v3.11/comparisons/comparison-x.md", "v3.11", "comparisons"),
        ("v3/v3.10/known-gaps.md", "v3.10", None),
        ("v0/v0.1/plans/bootstrap.md", "v0.1", "plans"),
        # Archive equivalent reuses the same scheme one level down.
        ("archive/v3/v3.10/comparisons/comparison-x.md", "v3.10", "comparisons"),
        ("archive/v1/v1.0/plans/impl.md", "v1.0", "plans"),
        ("archive/v0/v0.8/known-gaps.md", "v0.8", None),
        # Legacy flat scheme still recognized.
        ("v3.9.0/plans/foo.md", "v3.9.0", "plans"),
        ("v3.9.0/known-gaps.md", "v3.9.0", None),
        ("v0.8.1/comparison-foo.md", "v0.8.1", None),
        # Non-version paths resolve to (None, None).
        ("DEVLOG.md", None, None),
        ("policy/matrix.md", None, None),
    ],
)
def test_resolve_version_topic(rel_path, expected_version, expected_topic):
    abs_path = DOCS_ROOT / rel_path
    version, topic = audit._resolve_version_topic(abs_path, DOCS_ROOT)
    assert version == expected_version
    assert topic == expected_topic


def test_wrappers_delegate_to_resolver():
    abs_path = DOCS_ROOT / "v3/v3.11/plans/foo.md"
    assert audit._version_dir(abs_path, DOCS_ROOT) == "v3.11"
    assert audit._topic_dir(abs_path, DOCS_ROOT) == "plans"
    # The legacy three-argument call signature still works.
    assert audit._topic_dir(abs_path, DOCS_ROOT, "v3.11") == "plans"
