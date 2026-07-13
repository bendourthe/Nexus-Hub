"""Tests for scripts/verify_platform_contracts.py (v3.12.0 Phase 5.1).

The checker is layer 3 of the platform verification (code-vs-contract). These tests
prove it passes on the real repo and fails on injected drift.
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.verify_platform_contracts import (  # noqa: E402
    CONTRACT_DOC,
    INSTALLER_PS1,
    INSTALLER_SH,
    check,
)


def _real_inputs() -> tuple[str, str, str]:
    return (
        CONTRACT_DOC.read_text(encoding="utf-8"),
        INSTALLER_SH.read_text(encoding="utf-8"),
        INSTALLER_PS1.read_text(encoding="utf-8"),
    )


def test_passes_on_real_repo():
    doc, sh, ps = _real_inputs()
    assert check(doc, sh, ps) == [], "code and contract doc must agree on the real repo"


def test_flags_doc_drift_when_paths_missing():
    _, sh, ps = _real_inputs()
    # An empty contract doc omits every read-path -> a drift problem per platform.
    problems = check("", sh, ps)
    assert problems, "an empty contract doc must be flagged as drift"
    assert any("does not mention" in p for p in problems)


def test_flags_dropped_installer_delivery():
    doc, _, _ = _real_inputs()
    # A (non-empty) installer text that omits the nexus-ai key must be flagged.
    fake_installer = "should_install codex claude gemini gemini-cli opencode antigravity2"
    problems = check(doc, fake_installer, fake_installer)
    assert any("nexus-ai" in p and "not referenced" in p for p in problems)
