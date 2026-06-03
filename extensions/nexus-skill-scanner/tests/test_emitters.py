"""Output-emitter tests: terminal, JSON, Markdown, SARIF."""

from __future__ import annotations

import json
from pathlib import Path

from nexus_skill_scanner import Scanner
from nexus_skill_scanner.emitters import render


def _result(malicious: Path, repo_root: Path):
    return Scanner(repo_root=repo_root).scan([malicious])


def test_json_is_valid_and_structured(malicious_skill: Path, repo_root: Path) -> None:
    out = render(_result(malicious_skill, repo_root), "json")
    payload = json.loads(out)
    assert payload["band"] == "critical"
    assert payload["findings"]
    f = payload["findings"][0]
    assert {"detection_class", "severity", "file", "framework_ids"} <= set(f)


def test_sarif_is_valid_2_1_0(malicious_skill: Path, repo_root: Path) -> None:
    out = render(_result(malicious_skill, repo_root), "sarif")
    sarif = json.loads(out)
    assert sarif["version"] == "2.1.0"
    run = sarif["runs"][0]
    assert run["tool"]["driver"]["name"] == "nexus-skill-scanner"
    assert run["results"]
    # Every result references a defined rule.
    rule_ids = {r["id"] for r in run["tool"]["driver"]["rules"]}
    for res in run["results"]:
        assert res["ruleId"] in rule_ids
        assert res["level"] in {"error", "warning", "note"}


def test_markdown_has_summary_and_detail(malicious_skill: Path, repo_root: Path) -> None:
    out = render(_result(malicious_skill, repo_root), "markdown")
    assert "# Skill-Security Scan Report" in out
    assert "## Summary" in out
    assert "## Findings" in out


def test_terminal_renders_findings(malicious_skill: Path, repo_root: Path) -> None:
    out = render(_result(malicious_skill, repo_root), "terminal")
    assert "score:" in out
    assert "CRITICAL" in out


def test_clean_result_renders_no_findings(clean_skill: Path, repo_root: Path) -> None:
    result = Scanner(repo_root=repo_root).scan([clean_skill])
    assert "No findings" in render(result, "terminal")
    assert json.loads(render(result, "json"))["findings"] == []
