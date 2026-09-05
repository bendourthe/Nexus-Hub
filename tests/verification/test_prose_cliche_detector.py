"""Tests for the anti-slop-editing offline prose-cliche detector (v4.5.0 Phase 4).

Three fixtures drive the suite: prose seeded with known counts per pattern, clean
human prose that must produce zero findings (with deliberately tricky cases), and a
document carrying one chatbot leftover. The detector is run as a subprocess, the way
an agent or a hook would run it, following the precedent in
test_visual_defect_detector.py.

Run from the repo root:

    python -m pytest tests/verification/test_prose_cliche_detector.py -v
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = (
    REPO_ROOT
    / "catalog"
    / "skills"
    / "developer-experience"
    / "anti-slop-editing"
    / "scripts"
    / "detect_prose_cliches.py"
)
FIXTURES = Path(__file__).parent / "fixtures" / "prose"

# Expected counts in seeded.md, by pattern id. Exact, so a regex that widens or
# narrows shows up as a count change rather than a silent drift.
SEEDED_COUNTS = {
    "chatbot-leftover": 5,
    "dwelling-instruction": 1,
    "naming-ceremony": 1,
    "understated-significance": 1,
    "presumed-knowledge": 1,
    "isolated-part": 1,
    "lone-trusted-source": 1,
    "mock-humility": 1,
    "announced-punchline": 1,
    "discovery-frame": 1,
    "retroactive-significance": 1,
    "obituary": 1,
    "head-sized-praise": 1,
    "negation-chain": 2,
    "verb-reversal": 1,
    "totality-claim": 1,
    "performative-honesty": 3,
    "throat-clearing-opener": 1,
    "faux-insight-setup": 1,
    "importance-puffery": 1,
    "weasel-attribution": 1,
    "binary-contrast": 1,
    "echoing-run": 1,
    "repeated-opener": 1,
    "stacked-questions": 1,
    "em-dash": 1,
    "curly-quote": 2,
    "spaced-hyphen-connector": 2,
    "ellipsis-character": 1,
    "closing-summary-marker": 2,
}


def _run(*args: str, stdin: str | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
        input=stdin,
        cwd=REPO_ROOT,
        check=False,
    )


def _payload(result: subprocess.CompletedProcess[str]) -> dict[str, object]:
    return json.loads(result.stdout)


def _counts_by_id(payload: dict[str, object]) -> dict[str, int]:
    out: dict[str, int] = {}
    for f in payload["findings"]:  # type: ignore[index]
        out[f["id"]] = out.get(f["id"], 0) + 1  # type: ignore[index]
    return out


@pytest.fixture(scope="module")
def seeded() -> dict[str, object]:
    result = _run(str(FIXTURES / "seeded.md"), "--json")
    assert result.returncode == 0, result.stderr
    return _payload(result)


@pytest.mark.parametrize(("pattern_id", "expected"), sorted(SEEDED_COUNTS.items()))
def test_seeded_fixture_counts_each_pattern_exactly(
    seeded: dict[str, object], pattern_id: str, expected: int
) -> None:
    assert _counts_by_id(seeded).get(pattern_id, 0) == expected


def test_seeded_fixture_has_no_unexpected_pattern_ids(
    seeded: dict[str, object],
) -> None:
    unexpected = set(_counts_by_id(seeded)) - set(SEEDED_COUNTS)
    assert not unexpected, (
        f"detector emitted ids the fixture did not plant: {sorted(unexpected)}"
    )


def test_clean_prose_produces_zero_findings() -> None:
    """The false-positive test, which is the one that matters."""
    result = _run(str(FIXTURES / "clean.md"), "--json")
    assert result.returncode == 0, result.stderr
    payload = _payload(result)
    assert payload["findings"] == [], payload["findings"]
    assert payload["counts"] == {"advisory": 0, "defect": 0}


def test_chatbot_leftover_is_a_defect() -> None:
    result = _run(str(FIXTURES / "leftover.md"), "--json")
    payload = _payload(result)
    ids = {(f["id"], f["class"]) for f in payload["findings"]}  # type: ignore[index]
    assert ids == {("chatbot-leftover", "defect")}
    assert payload["counts"] == {"advisory": 0, "defect": 1}


def test_exit_code_is_zero_by_default_even_with_findings() -> None:
    assert _run(str(FIXTURES / "seeded.md")).returncode == 0


@pytest.mark.parametrize(
    ("fixture", "fail_on", "expected_code"),
    [
        ("leftover.md", "defect", 1),
        ("clean.md", "defect", 0),
        ("seeded.md", "advisory", 1),
        ("leftover.md", "advisory", 0),
        ("clean.md", "any", 0),
        ("leftover.md", "any", 1),
    ],
)
def test_fail_on_gates_only_the_named_class(
    fixture: str, fail_on: str, expected_code: int
) -> None:
    assert (
        _run(str(FIXTURES / fixture), "--fail-on", fail_on).returncode == expected_code
    )


def test_human_output_names_class_id_line_and_column() -> None:
    result = _run(str(FIXTURES / "leftover.md"))
    assert result.returncode == 0
    assert "[defect] chatbot-leftover: I hope this helps" in result.stdout
    assert ":7:1:" in result.stdout, result.stdout
    assert result.stdout.strip().endswith("1 defect, 0 advisory")


def test_json_findings_carry_line_column_span_and_rule() -> None:
    payload = _payload(_run(str(FIXTURES / "leftover.md"), "--json"))
    (finding,) = payload["findings"]  # type: ignore[misc]
    assert finding == {
        "class": "defect",
        "col": 1,
        "id": "chatbot-leftover",
        "line": 7,
        "rule": "lexical",
        "span": "I hope this helps",
    }


def test_structural_findings_state_their_rule_and_threshold(
    seeded: dict[str, object],
) -> None:
    rules = {f["id"]: f["rule"] for f in seeded["findings"] if f["rule"] != "lexical"}  # type: ignore[index]
    assert rules["echoing-run"].startswith(
        "rhythm rule 1: 3 consecutive sentences share the skeleton"
    )
    assert rules["repeated-opener"].startswith(
        "rhythm rule 2: 3 consecutive sentences open on 'tests'"
    )
    assert (
        rules["stacked-questions"] == "rhythm rule 3: 3 consecutive question sentences"
    )


def test_reads_stdin_when_source_is_dash() -> None:
    result = _run("-", "--json", stdin="Turns out, the cache was never enabled.\n")
    payload = _payload(result)
    assert payload["source"] == "<stdin>"
    assert [f["id"] for f in payload["findings"]] == ["discovery-frame"]  # type: ignore[index]


def test_quoted_mention_of_a_pattern_is_not_a_finding() -> None:
    """A review that quotes a leftover, or the catalog that names one, is not committing it."""
    quoted = 'The draft ended with "I hope this helps", which the review flagged.\n'
    inline = "The draft ended with `I hope this helps`, which the review flagged.\n"
    committed = "The draft ended well. I hope this helps.\n"
    assert _payload(_run("-", "--json", stdin=quoted))["findings"] == []
    assert _payload(_run("-", "--json", stdin=inline))["findings"] == []
    ids = [f["id"] for f in _payload(_run("-", "--json", stdin=committed))["findings"]]  # type: ignore[index]
    assert ids == ["chatbot-leftover"]


def test_missing_file_exits_two() -> None:
    result = _run(str(FIXTURES / "does-not-exist.md"))
    assert result.returncode == 2
    assert "no such file" in result.stderr


def test_detector_imports_only_the_standard_library() -> None:
    text = SCRIPT.read_text(encoding="utf-8")
    imports = {
        line.split()[1].split(".")[0]
        for line in text.splitlines()
        if line.startswith(("import ", "from ")) and "__future__" not in line
    }
    assert imports <= {"argparse", "json", "re", "sys", "dataclasses", "pathlib"}, (
        imports
    )
