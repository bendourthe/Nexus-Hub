"""End-to-end scanner tests: the planted-malicious / known-clean gate.

Mirrors SkillSpector's two-stage validation: the malicious fixture MUST score
HIGH/CRITICAL and the clean fixture MUST score LOW. Also covers scoring,
fence-awareness, and the CLI severity gate.
"""

from __future__ import annotations

from pathlib import Path

from nexus_skill_scanner import Scanner, scan_target
from nexus_skill_scanner.cli import run
from nexus_skill_scanner.types import Band, Severity


def test_malicious_fixture_scores_high(malicious_skill: Path, repo_root: Path) -> None:
    result = Scanner(repo_root=repo_root).scan([malicious_skill])
    assert result.band.rank >= Band.HIGH.rank
    # The planted exec()/compile() are CRITICAL and drive the band.
    assert result.max_severity() is Severity.CRITICAL
    classes = {f.detection_class for f in result.findings}
    assert 12 in classes  # behavioral AST (exec/compile)
    assert 2 in classes  # credential exfiltration


def test_clean_fixture_scores_low(clean_skill: Path, repo_root: Path) -> None:
    result = Scanner(repo_root=repo_root).scan([clean_skill])
    assert result.band is Band.LOW
    # Every dangerous-looking construct in the clean skill sits inside a fence
    # and must be suppressed.
    assert result.findings == []


def test_fence_suppression_is_the_difference(clean_skill: Path, repo_root: Path) -> None:
    # The clean skill contains "exec(", "eval(", a hardcoded password, and an
    # "ignore all previous instructions" line -- all inside fences. None should
    # be flagged.
    result = Scanner(repo_root=repo_root).scan([clean_skill])
    titles = {f.title for f in result.findings}
    assert "Dynamic code execution: exec()" not in titles
    assert not any("secret" in t.lower() for t in titles)


def test_findings_carry_framework_ids(malicious_skill: Path, repo_root: Path) -> None:
    result = Scanner(repo_root=repo_root).scan([malicious_skill])
    for finding in result.findings:
        assert finding.framework_ids, f"{finding.title} has no framework IDs"
        assert finding.class_name


def test_executable_multiplier_increases_score(repo_root: Path, tmp_path: Path) -> None:
    # The same CRITICAL construct weighs more in a .py file than in prose.
    (tmp_path / "evil.py").write_text("eval(x)\n", encoding="utf-8")
    py = Scanner(repo_root=repo_root).scan([tmp_path / "evil.py"])
    assert py.score == min(100, round(Severity.CRITICAL.points * 1.3))


def test_cli_gate_fails_on_malicious(malicious_skill: Path) -> None:
    code = run([str(malicious_skill), "--fail-on", "high", "--format", "json"])
    assert code == 1


def test_cli_gate_passes_on_clean(clean_skill: Path) -> None:
    code = run([str(clean_skill), "--fail-on", "high", "--format", "json"])
    assert code == 0


def test_cli_missing_target_returns_2() -> None:
    assert run(["does-not-exist-xyz", "--format", "json"]) == 2


def test_scan_target_convenience(malicious_skill: Path) -> None:
    result = scan_target(malicious_skill)
    assert result.findings
    assert result.score > 50
