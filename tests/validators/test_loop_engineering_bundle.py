"""Structure and library-schema contracts for the loop-engineering skill bundle.

The loop skill's doctrine lives in `references/` files that `SKILL.md` links to
on demand (Tier 3 progressive disclosure). A broken link does not crash
anything -- the skill silently stops delegating -- so the link itself is the
contract these tests hold. The library tests pin the schema's required-field
set so the v4.8.0 run-contract extension stays additive.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[2]
SKILL_DIR = ROOT / "catalog" / "skills" / "workflow" / "loop-engineering"
SKILL_MD = SKILL_DIR / "SKILL.md"
REFERENCES = SKILL_DIR / "references"

BODY_LINE_CEILING = 500

REQUIRED_FIELDS = (
    "name",
    "goal",
    "iteration_cap",
    "check_command",
    "exit_condition",
    "driver",
    "maturity",
    "agents",
    "tags",
)

OPTIONAL_FIELDS = (
    "per_iteration_budget",
    "trace_log",
    "progress_check",
    "handoff",
    "gates",
    "scope",
    "permissions",
    "budgets",
    "state_contract",
    "audit_evidence",
    "evidence_freshness",
)

BUNDLED_REFERENCES = (
    "loop-schema.md",
    "loop-library.md",
    "loop-readiness-scorecard.md",
    "failure-mode-ownership.md",
)


def _skill_body() -> str:
    return SKILL_MD.read_text(encoding="utf-8")


def _library_loops() -> list[tuple[str, dict]]:
    """Parse every fenced YAML block in the loop library."""
    text = (REFERENCES / "loop-library.md").read_text(encoding="utf-8")
    blocks = re.findall(r"```yaml\n(.*?)```", text, flags=re.DOTALL)
    assert blocks, "loop-library.md declares no YAML loop definitions"
    return [(block, yaml.safe_load(block)) for block in blocks]


@pytest.mark.parametrize("filename", BUNDLED_REFERENCES)
def test_bundled_reference_exists(filename: str) -> None:
    assert (REFERENCES / filename).is_file(), f"missing bundled reference {filename}"


@pytest.mark.parametrize("filename", BUNDLED_REFERENCES)
def test_bundled_reference_is_linked_from_skill_body(filename: str) -> None:
    """Every bundled file must be referenced from SKILL.md (AGENTS.md orphan rule)."""
    assert f"references/{filename}" in _skill_body(), (
        f"{filename} is an orphan bundle: nothing in SKILL.md links to it, so the "
        "agent will never load it"
    )


def test_skill_body_stays_under_the_size_norm() -> None:
    lines = len(_skill_body().splitlines())
    assert lines <= BODY_LINE_CEILING, (
        f"SKILL.md is {lines} lines, over the {BODY_LINE_CEILING}-line norm; "
        "move content into references/ instead of growing the body"
    )


def test_scorecard_is_gated_before_assembly_and_recorded_in_instance_state() -> None:
    """The scorecard is an intake gate, not a footnote: both citations must exist."""
    body = _skill_body()
    when_to_use = body.split("## When to Use This Skill", 1)[1].split("\n## ", 1)[0]
    step_two = body.split("### Step 2:", 1)[1].split("\n### ", 1)[0]
    assert "loop-readiness-scorecard.md" in when_to_use, (
        "the scorecard must be cited in When to Use This Skill so scoring precedes "
        "assembly"
    )
    assert "loop-readiness-scorecard.md" in step_two, (
        "Step 2 must record the readiness total in the loop's instance state"
    )


def test_ownership_table_is_linked_from_stall_and_fault_detection() -> None:
    body = _skill_body()
    section = body.split("## Stall and Fault Detection", 1)[1].split("\n## ", 1)[0]
    assert "failure-mode-ownership.md" in section


def test_ownership_table_names_exactly_one_owner_per_mode() -> None:
    """Ten modes, ten rows, and no row that hedges between two owners."""
    text = (REFERENCES / "failure-mode-ownership.md").read_text(encoding="utf-8")
    rows = [
        line
        for line in text.splitlines()
        if line.startswith("| ") and line.count("|") == 6
    ]
    # Drop the header and the alignment separator.
    data_rows = [r for r in rows if not r.startswith("| Failure mode") and "---" not in r]
    assert len(data_rows) == 10, f"expected 10 failure-mode rows, found {len(data_rows)}"
    catalog_skills = {
        p.parent.name for p in (ROOT / "catalog" / "skills").glob("*/*/SKILL.md")
    }
    for row in data_rows:
        owner = row.split("|")[3]
        assert owner.strip(), f"row has an empty owner column: {row}"
        # The owner is the FIRST backtick-quoted token; anything after it locates
        # the rule inside that skill (a field name, a reference path). Assert the
        # owner is a real catalog skill rather than counting backticks, and that
        # no SECOND skill name appears, which is what a hedged owner looks like.
        named = re.findall(r"`([a-z0-9-]+)`", owner)
        assert named, f"owner column names no skill: {owner}"
        assert named[0] in catalog_skills, (
            f"owner {named[0]!r} is not a skill in the catalog: {owner}"
        )
        others = [n for n in named[1:] if n in catalog_skills]
        assert not others, (
            f"owner column names more than one owning skill ({named[0]} plus "
            f"{others}), which defeats one-owner-per-mode: {owner}"
        )


@pytest.mark.parametrize("field", REQUIRED_FIELDS)
def test_schema_still_declares_every_required_field(field: str) -> None:
    text = (REFERENCES / "loop-schema.md").read_text(encoding="utf-8")
    assert f"| `{field}` |" in text


@pytest.mark.parametrize("field", OPTIONAL_FIELDS)
def test_schema_declares_each_optional_field_as_optional(field: str) -> None:
    """An optional field's Purpose must begin with 'Optional' -- that word is what
    makes the run-contract extension additive rather than breaking."""
    text = (REFERENCES / "loop-schema.md").read_text(encoding="utf-8")
    match = re.search(rf"^\| `{re.escape(field)}` \| ([^|]*)", text, flags=re.MULTILINE)
    assert match, f"schema does not declare the {field} field"
    assert match.group(1).strip().startswith("Optional"), (
        f"{field} must be documented as Optional so existing definitions stay valid"
    )


def test_every_library_loop_carries_the_required_fields() -> None:
    for block, loop in _library_loops():
        missing = [f for f in REQUIRED_FIELDS if f not in loop]
        assert not missing, f"loop {loop.get('name')!r} is missing {missing}"


def test_no_library_loop_uses_an_undocumented_top_level_key() -> None:
    allowed = set(REQUIRED_FIELDS) | set(OPTIONAL_FIELDS)
    for _block, loop in _library_loops():
        unknown = sorted(set(loop) - allowed)
        assert not unknown, (
            f"loop {loop.get('name')!r} declares undocumented top-level keys "
            f"{unknown}; document them in loop-schema.md or remove them"
        )


def test_trace_log_field_documents_the_optional_score_and_its_aggregation() -> None:
    """The score field is only useful with a stated aggregation rule."""
    text = (REFERENCES / "loop-schema.md").read_text(encoding="utf-8")
    trace_row = re.search(r"^\| `trace_log` \|.*$", text, flags=re.MULTILINE)
    assert trace_row, "schema does not declare trace_log"
    assert "`score`" in trace_row.group(0)
    assert "Aggregation rule for `score`" in text


# The ownership table asserts that each owner's own SKILL.md states the rule it
# owns. Five owners had to be edited to make that true. Without these tests the
# table could keep quoting a heading whose rule sentence was later deleted, and
# the non-owners would go on deferring to a rule that no longer exists anywhere.
OWNER_RULE_SENTENCES = {
    "workflow/verification-before-completion": "Completion criteria are MULTI-DIMENSIONAL",
    "developer-experience/ai-output-evaluation": "held-out grading set the loop never sees",
    "developer-experience/tool-design": "**Tool thrashing** is the failure this limit prevents",
    "workflow/agent-memory": "State poisoning",
    "orchestration/agent-orchestration-primitives": "cascades through the whole fan-out",
}


@pytest.mark.parametrize(
    "skill_path,sentence", sorted(OWNER_RULE_SENTENCES.items())
)
def test_named_owner_actually_states_the_rule_it_owns(
    skill_path: str, sentence: str
) -> None:
    body = (ROOT / "catalog" / "skills" / skill_path / "SKILL.md").read_text(
        encoding="utf-8"
    )
    assert sentence in body, (
        f"{skill_path} no longer states the rule that "
        "references/failure-mode-ownership.md assigns it; either restore the "
        "sentence or reassign the owner"
    )


def test_ownership_table_records_which_owners_were_edited() -> None:
    """The plan requires the edits be recorded, not just made."""
    text = (REFERENCES / "failure-mode-ownership.md").read_text(encoding="utf-8")
    section = text.split("## Owners edited to state their rule", 1)
    assert len(section) == 2, "the ownership table does not record its owner edits"
    for skill_path in OWNER_RULE_SENTENCES:
        name = skill_path.split("/")[1]
        assert f"`{name}`" in section[1], f"{name} is not listed as an edited owner"
