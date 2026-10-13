"""Local-persistence and error-surface contract for the egress-redaction skill.

v4.13 AR-13 (originally v3.16 CD-2) extends the skill's single BLOCK / REDACT /
HASH / PASS policy from the egress boundary to two boundaries where nothing
leaves the host: local persistence and error surfaces. The contract held here:

- the default-policy table stays the ONE source of truth (no parallel table);
- every synthetic case's action is the policy table's default for its category,
  and an unclassified value fails closed to BLOCK;
- no persisted or emitted form echoes the raw value or any fragment of it;
- the frontmatter metadata describes the widened scope.

Each check is a function returning the problems it found, so the mutation
tests prove it fails on a wrong document rather than only passing a right one.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[2]
SKILL_MD = ROOT / "catalog" / "skills" / "security" / "egress-redaction" / "SKILL.md"

BOUNDARIES = ("Local persistence", "Error surface")
UNCLASSIFIED = "Unclassified"
ACTIONS = ("BLOCK", "REDACT", "HASH", "PASS")
FRAGMENT = 6  # the shortest echoed fragment that counts as a leak


def _skill_text() -> str:
    return SKILL_MD.read_text(encoding="utf-8")


def _frontmatter(text: str) -> dict:
    return yaml.safe_load(text.split("---", 2)[1])


def _cells(line: str) -> list[str]:
    return [c.strip() for c in line.strip().strip("|").split("|")]


def _table_after(text: str, header_prefix: str) -> list[list[str]]:
    lines = text.splitlines()
    start = next(i for i, line in enumerate(lines) if line.startswith(header_prefix))
    rows = []
    for line in lines[start + 2 :]:
        if not line.startswith("|"):
            break
        rows.append(_cells(line))
    return rows


def policy_table_count(text: str) -> int:
    return sum(1 for line in text.splitlines() if re.match(r"^\| Category \| Default action", line))


def default_policy(text: str) -> dict[str, str]:
    rows = _table_after(text, "| Category | Default action on egress |")
    return {category: action.split()[0] for category, action in rows}


def synthetic_cases(text: str) -> list[dict[str, str]]:
    keys = ("case", "boundary", "category", "value", "action", "form")
    rows = _table_after(text, "| Case | Boundary | Category | Synthetic sensitive value |")
    return [dict(zip(keys, (c.strip("`") for c in row))) for row in rows]


def case_errors(case: dict[str, str], policy: dict[str, str]) -> list[str]:
    errors = []
    value, form, action = case["value"], case["form"], case["action"]
    label = case["case"]
    if value in form:
        errors.append(f"{label}: form echoes the raw value")
    fragments = {value[i : i + FRAGMENT] for i in range(len(value) - FRAGMENT + 1)}
    leaked = sorted(f for f in fragments if f in form)
    if leaked:
        errors.append(f"{label}: form echoes a fragment of the raw value: {leaked[0]!r}")
    if case["boundary"] not in BOUNDARIES:
        errors.append(f"{label}: unknown boundary {case['boundary']!r}")
    if case["category"] == UNCLASSIFIED:
        if action != "BLOCK":
            errors.append(f"{label}: unclassified value must fail closed to BLOCK, not {action}")
    elif case["category"] not in policy:
        errors.append(f"{label}: category {case['category']!r} is not in the policy table")
    elif action != policy[case["category"]]:
        errors.append(
            f"{label}: action {action} disagrees with the policy default "
            f"{policy[case['category']]} for {case['category']}"
        )
    if action == "REDACT" and "[redacted:" not in form:
        errors.append(f"{label}: REDACT form carries no typed marker")
    if action == "HASH" and "[hash:" not in form:
        errors.append(f"{label}: HASH form carries no hash marker")
    if action == "BLOCK" and ("[redacted:" in form or "[hash:" in form):
        errors.append(f"{label}: BLOCK form writes a REDACT or HASH stand-in instead")
    return errors


def all_case_errors(text: str) -> list[str]:
    policy = default_policy(text)
    errors = []
    for case in synthetic_cases(text):
        errors.extend(case_errors(case, policy))
    return errors


# --- the single policy table ---


def test_exactly_one_default_policy_table() -> None:
    assert policy_table_count(_skill_text()) == 1, (
        "egress-redaction must keep ONE default-policy table; a second table for the "
        "new boundaries creates two sources of truth for one classification"
    )


def test_policy_table_covers_exactly_the_taxonomy() -> None:
    text = _skill_text()
    taxonomy = {row[0] for row in _table_after(text, "| Category | Recognition cue |")}
    assert set(default_policy(text)) == taxonomy


def test_policy_defaults_use_only_the_four_actions() -> None:
    assert set(default_policy(_skill_text()).values()) <= set(ACTIONS)


def test_parallel_policy_table_is_detected() -> None:
    text = _skill_text()
    extra = "\n| Category | Default action at persistence |\n|---|---|\n| Credentials | BLOCK |\n"
    assert policy_table_count(text + extra) == 2


# --- synthetic cases ---


def test_synthetic_cases_obey_the_policy_and_never_echo_raw_values() -> None:
    errors = all_case_errors(_skill_text())
    assert not errors, "\n".join(errors)


@pytest.mark.parametrize("boundary", BOUNDARIES)
def test_each_boundary_has_cases_including_a_fail_closed_one(boundary: str) -> None:
    cases = [c for c in synthetic_cases(_skill_text()) if c["boundary"] == boundary]
    assert len(cases) >= 3, f"{boundary} has only {len(cases)} synthetic cases"
    assert any(c["category"] == UNCLASSIFIED for c in cases), (
        f"{boundary} has no unclassified case proving the fail-closed rule"
    )
    assert any(c["category"] == "Credentials" for c in cases), (
        f"{boundary} has no credential case, the leak class AR-13 exists for"
    )


def test_embedded_credential_url_is_the_canonical_persistence_case() -> None:
    cases = {c["case"]: c for c in synthetic_cases(_skill_text())}
    p1 = cases["P1"]
    assert p1["boundary"] == "Local persistence" and p1["category"] == "Credentials"
    assert "https://git.example.invalid/" in p1["form"] and "@" not in p1["form"]


def _mutated(row_id: str, column: int, new: str) -> str:
    text = _skill_text()
    line = next(line for line in text.splitlines() if line.startswith(f"| {row_id} |"))
    cells = _cells(line)
    cells[column] = new
    return text.replace(line, "| " + " | ".join(cells) + " |", 1)


@pytest.mark.parametrize(
    "row_id,column,new,expected",
    [
        ("P2", 5, "`owner: jane.doe@example.invalid`", "echoes the raw value"),
        ("E1", 5, "`auth failed for token ending 0EXAMPLE0002`", "fragment"),
        ("P4", 4, "PASS", "fail closed"),
        ("E4", 4, "HASH", "fail closed"),
        ("P1", 4, "REDACT", "disagrees with the policy default"),
        ("E3", 2, "Shoe sizes", "not in the policy table"),
        ("P3", 5, "`client: 9c1e4a7b`", "no hash marker"),
        ("E2", 5, "`config load failed: api_key=[redacted:api-key]`", "BLOCK form"),
    ],
)
def test_case_check_fails_on_a_wrong_case(
    row_id: str, column: int, new: str, expected: str
) -> None:
    errors = all_case_errors(_mutated(row_id, column, new))
    assert any(expected in e for e in errors), f"check missed the mutation: {errors}"


# --- boundary guidance and metadata agreement ---


@pytest.mark.parametrize(
    "phrase",
    [
        "## Local Persistence and Error Surfaces",
        "`scheme://user:token@host/path`",
        "never a second policy table",
        "**Unclassified values fail closed.**",
        "never echoes a raw sensitive value",
        "It does not make a host, a library, or a logging framework redact anything",
        "- **Local persistence**:",
        "- **Error surface**:",
    ],
)
def test_body_states_the_boundary_guidance(phrase: str) -> None:
    assert phrase in _skill_text(), f"egress-redaction no longer states {phrase!r}"


@pytest.mark.parametrize("field", ("description", "overview_l1"))
def test_frontmatter_describes_the_widened_scope(field: str) -> None:
    value = _frontmatter(_skill_text())[field].lower()
    assert "persist" in value and "error" in value, (
        f"{field} still describes an egress-only skill"
    )


def test_summary_l0_names_the_new_boundaries_within_the_word_cap() -> None:
    summary = _frontmatter(_skill_text())["summary_l0"]
    assert "persistence" in summary and "errors" in summary
    assert len(summary.split()) <= 15


def test_distributed_body_does_not_name_the_upstream_project() -> None:
    lowered = _skill_text().lower()
    assert "no-mistakes" not in lowered and "no_mistakes" not in lowered
    matrix = (ROOT / "docs" / "policy" / "mcp-reverse-engineering-matrix.md").read_text(
        encoding="utf-8"
    )
    assert "Local Persistence and Error Surfaces" in matrix, "provenance matrix row missing"
