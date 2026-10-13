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


# --- AR-12 (v3.16.2 MT-1): gate-type parity across schema, table, library ---
#
# The gate types are declared in three places: the `gates` row of the Fields
# table, the Human-Judgment Gates table, and the skill body's Verification
# checklist. Every library and worked-example gate must use one of them. These
# helpers return the drift they find so the mutation tests below can prove the
# check fails on a wrong document, not only that it passes on the right one.

GATE_KEYS = ("type", "question", "unblocks_on", "while_waiting")
YAML_FENCE = re.compile(r"```yaml\n(.*?)```", flags=re.DOTALL)


def _read(name: str) -> str:
    return (REFERENCES / name).read_text(encoding="utf-8")


def _gate_types_in_fields_row(schema_text: str) -> set[str]:
    row = re.search(r"^\| `gates` \|.*$", schema_text, flags=re.MULTILINE)
    assert row, "schema does not declare the gates field"
    declared = re.search(r"declares its `type` \(([^)]*)\)", row.group(0))
    assert declared, "the gates row does not enumerate its gate types"
    return set(re.findall(r"`([a-z-]+)`", declared.group(1)))


def _gate_types_in_judgment_table(schema_text: str) -> set[str]:
    section = schema_text.split("## Human-Judgment Gates", 1)[1].split("\n## ", 1)[0]
    return set(re.findall(r"^\| `([a-z-]+)` \|", section, flags=re.MULTILINE))


def _gate_types_in_skill_verification(skill_text: str) -> set[str]:
    section = skill_text.split("## Verification", 1)[1].split("\n## ", 1)[0]
    declared = re.search(r"names its `type` \(([^)]*)\)", section)
    assert declared, "the skill Verification checklist does not enumerate gate types"
    return {t.strip() for t in declared.group(1).split("/")}


def _yaml_gates(text: str) -> list[tuple[str, dict]]:
    """Every gate entry in every fenced YAML block of a document."""
    gates = []
    for block in YAML_FENCE.findall(text):
        loop = yaml.safe_load(block)
        for gate in loop.get("gates") or []:
            gates.append((loop.get("name", "?"), gate))
    return gates


def gate_type_parity_errors(
    schema_text: str, library_text: str, skill_text: str
) -> list[str]:
    errors = []
    table = _gate_types_in_judgment_table(schema_text)
    if len(table) != 4:
        errors.append(f"Human-Judgment Gates table declares {sorted(table)}, expected four")
    for label, found in (
        ("Fields-table gates row", _gate_types_in_fields_row(schema_text)),
        ("skill Verification checklist", _gate_types_in_skill_verification(skill_text)),
    ):
        if found != table:
            errors.append(f"{label} declares {sorted(found)}; table has {sorted(table)}")
    for source, text in (("loop-schema.md", schema_text), ("loop-library.md", library_text)):
        for loop_name, gate in _yaml_gates(text):
            if gate.get("type") not in table:
                errors.append(f"{source} {loop_name} uses undeclared type {gate.get('type')!r}")
            missing = [k for k in GATE_KEYS if not gate.get(k)]
            if missing:
                errors.append(f"{source} {loop_name} gate lacks {missing}")
    return errors


def test_gate_types_agree_across_fields_row_table_verification_and_library() -> None:
    errors = gate_type_parity_errors(
        _read("loop-schema.md"), _read("loop-library.md"), _skill_body()
    )
    assert not errors, "\n".join(errors)


@pytest.mark.parametrize(
    "target,old,new",
    [
        ("schema", "| `private-data` | The next step", "| `private` | The next step"),
        (
            "schema",
            "(`owner`, `safety`, `publication`, or `private-data`)",
            "(`owner`, `safety`, or `publication`)",
        ),
        (
            "skill",
            "(owner / safety / publication / private-data)",
            "(owner / safety / publication)",
        ),
        ("library", "  - type: safety\n", "  - type: destructive\n"),
        ("library", "    while_waiting: Hold", "    while_waiting_note: Hold"),
    ],
)
def test_gate_type_parity_check_fails_on_a_drifted_document(
    target: str, old: str, new: str
) -> None:
    texts = {
        "schema": _read("loop-schema.md"),
        "library": _read("loop-library.md"),
        "skill": _skill_body(),
    }
    assert old in texts[target], f"mutation anchor missing from {target}: {old!r}"
    texts[target] = texts[target].replace(old, new, 1)
    assert gate_type_parity_errors(texts["schema"], texts["library"], texts["skill"]), (
        f"parity check accepted a drifted {target}"
    )


# --- AR-12 (v3.16.2 MT-1): the duplicated ship-pr-until-green block ---
#
# The schema's worked example and the library entry are the same loop, so its
# `gates` block and its shared required fields exist twice. Drift between the
# two copies is the concrete risk MT-1 named.

SHARED_SHIP_PR_FIELDS = (
    "name",
    "goal",
    "iteration_cap",
    "check_command",
    "exit_condition",
    "driver",
    "maturity",
    "tags",
)


def _ship_pr_block(text: str) -> str:
    blocks = [
        b for b in YAML_FENCE.findall(text) if b.startswith("name: ship-pr-until-green\n")
    ]
    assert len(blocks) == 1, (
        f"expected exactly one ship-pr-until-green block, found {len(blocks)}"
    )
    return blocks[0]


def _gates_lines(block: str) -> str:
    lines = block.splitlines()
    start = lines.index("gates:")
    end = start + 1
    while end < len(lines) and lines[end].startswith(" "):
        end += 1
    return "\n".join(lines[start:end])


def ship_pr_duplicate_drift(schema_text: str, library_text: str) -> list[str]:
    schema_block = _ship_pr_block(schema_text)
    library_block = _ship_pr_block(library_text)
    drift = []
    if _gates_lines(schema_block) != _gates_lines(library_block):
        drift.append("the ship-pr-until-green gates block differs between the two files")
    schema_loop, library_loop = yaml.safe_load(schema_block), yaml.safe_load(library_block)
    for field in SHARED_SHIP_PR_FIELDS:
        if schema_loop.get(field) != library_loop.get(field):
            drift.append(f"ship-pr-until-green field {field} differs between the copies")
    return drift


def test_ship_pr_until_green_duplicate_blocks_are_identical() -> None:
    drift = ship_pr_duplicate_drift(_read("loop-schema.md"), _read("loop-library.md"))
    assert not drift, "\n".join(drift)


@pytest.mark.parametrize(
    "old,new",
    [
        ("Approve a force-push that rewrites", "Approve a force push that rewrites"),
        ("unpushed and idle.", "unpushed."),
        ("iteration_cap: 10\ncheck_command: gh pr checks", "iteration_cap: 12\ncheck_command: gh pr checks"),
    ],
)
def test_duplicate_block_check_detects_drift_in_one_copy(old: str, new: str) -> None:
    library = _read("loop-library.md")
    assert old in library, f"mutation anchor missing from loop-library.md: {old!r}"
    assert ship_pr_duplicate_drift(_read("loop-schema.md"), library.replace(old, new, 1))


def test_duplicate_block_check_rejects_a_second_copy_in_one_file() -> None:
    library = _read("loop-library.md")
    second_copy = "```yaml\n" + _ship_pr_block(library) + "```\n"
    with pytest.raises(AssertionError, match="exactly one ship-pr-until-green block"):
        ship_pr_duplicate_drift(_read("loop-schema.md"), library + "\n" + second_copy)


# --- AR-12 (v3.16 CD-1 and CD-3): re-entrancy, instance identity, prompt growth ---


def _reentrancy_section() -> str:
    body = _skill_body()
    assert "## Re-entrancy and Instance Identity" in body, "re-entrancy section missing"
    return body.split("## Re-entrancy and Instance Identity", 1)[1].split("\n## ", 1)[0]


@pytest.mark.parametrize(
    "phrase",
    [
        "recursive budget multiplication",
        "Instance identity is host-owned",
        "`LOOP_INSTANCE`",
        "`LOOP_LINEAGE`",
        "Refuse unintended same-instance re-entry",
        "Refuse on ambiguous identity",
        "Fail closed",
        "Allow deliberate distinct child loops",
        "never added on top of it",
        "Refuse an exhausted child budget",
        "prompt-growth exhaustion",
        "inter-round compaction",
        "Nexus-Hub ships no runtime that sets, propagates, or enforces these markers",
    ],
)
def test_reentrancy_section_states_each_obligation(phrase: str) -> None:
    assert phrase in _reentrancy_section(), f"re-entrancy section no longer states {phrase!r}"


@pytest.mark.parametrize(
    "name",
    [
        "ai-billing-safeguards",
        "using-git-worktrees",
        "agent-orchestration-primitives",
        "context-compression",
        "prompt-token-optimization",
    ],
)
def test_reentrancy_section_cross_links_resolve(name: str) -> None:
    assert f"[[{name}]]" in _reentrancy_section()
    assert list((ROOT / "catalog" / "skills").glob(f"*/{name}/SKILL.md")), (
        f"{name} is not a catalog skill"
    )


def test_reentrancy_guidance_does_not_name_the_upstream_project() -> None:
    """Reverse-engineering attribution rule: provenance lives in the matrix row only."""
    lowered = (_skill_body() + _read("loop-schema.md")).lower()
    for token in ("no-mistakes", "no_mistakes", "nested_gate_context"):
        assert token not in lowered, f"distributed artifact names the upstream: {token}"
    matrix = (ROOT / "docs" / "policy" / "mcp-reverse-engineering-matrix.md").read_text(
        encoding="utf-8"
    )
    assert "Re-entrancy and Instance Identity" in matrix, "provenance matrix row missing"


def test_instance_record_carries_the_host_owned_identity() -> None:
    section = _read("loop-schema.md").split("## Instance State", 1)[1]
    assert "`LOOP_INSTANCE` and `LOOP_LINEAGE`" in section
    assert "ambiguous identity and is refused" in section
