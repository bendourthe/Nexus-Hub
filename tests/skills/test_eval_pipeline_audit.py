"""Contract tests for the eval-pipeline-audit skill (v3.16.1 Phase 2).

This skill is a router. Its value comes entirely from what it does NOT do:
it inventories an evaluation process, ranks the gaps, and hands each one to
the skill that owns the method. The moment it starts explaining how to compute
Recall@k or how to validate a judge, it becomes a second copy of guidance that
already has an owner, and the two copies begin to drift.

That makes the non-duplication boundary the load-bearing assertion here, not a
stylistic preference. `test_does_not_duplicate_specialist_formulas` fails if a
specialist formula appears in the body, and it is the test most likely to catch
a well-meaning future edit ("this would be more useful if it just showed the
formula").

The rest guard the things a router can silently lose: the fixed ten-concern
inventory order, the routing table that names an owner per gap area, the
local-data rules that keep production traces on the host, and correct
registration in all three catalogs plus both AI selections.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parents[2]

_SKILL_DIR = _ROOT / "catalog" / "skills" / "ai-development" / "eval-pipeline-audit"
_SKILL = _SKILL_DIR / "SKILL.md"
_TRIGGER_CASES = _SKILL_DIR / "evals" / "trigger-cases.json"
_AGENT_DESCRIPTOR = _SKILL_DIR / "agents" / "openai.yaml"

_SKILLS_JSON = _ROOT / "data" / "skills.json"
_SKILL_INDEX = _ROOT / "data" / "SKILL_INDEX.md"
_MARKETPLACE = _ROOT / "data" / "marketplace.json"
_BUNDLES = _ROOT / "data" / "bundles.json"

SKILL_NAME = "eval-pipeline-audit"

# The ten concerns, in the order the skill walks them. Order is part of the
# contract: an audit that jumps to a recommendation finds evidence for the
# opinion it started with.
REQUIRED_CONCERNS = (
    "Objectives",
    "Datasets",
    "Split provenance",
    "Evaluators",
    "Thresholds",
    "Traces",
    "Human labels",
    "Regression cases",
    "Feedback loops",
    "Deployment gates",
)

# Artifact names from the Phase 1 contract that this skill must speak.
REQUIRED_ARTIFACT_VOCABULARY = (
    "dataset_manifest",
    "split_manifest",
    "evaluator_result",
    "trace_sample",
    "human_annotation",
    "regression_case",
    "adjudication_record",
)

# Every skill the routing table must name as owning at least one gap area.
REQUIRED_ROUTING_TARGETS = (
    "rag-implementation",
    "ai-output-evaluation",
    "skill-eval-loop",
    "prompt-engineering",
    "egress-redaction",
)

# Specialist content that belongs to an owner skill and must NOT be reproduced
# here. Each pattern is the definitional form, not a passing mention: naming
# Recall@k while routing is correct, defining it is duplication.
FORBIDDEN_SPECIALIST_PATTERNS = {
    "Recall@k formula": r"Recall@k\s*=",
    "Precision@k formula": r"Precision@k\s*=",
    "NDCG formula": r"NDCG@k\s*=|DCG@k\s*=",
    "MRR formula": r"MRR\s*=\s*mean",
    "Wilson interval formula": r"halfwidth\s*=",
    "confusion-matrix arithmetic": r"true[_ ]positive[_ ]rate\s*=",
}


@pytest.fixture(scope="module")
def skill() -> str:
    assert _SKILL.is_file(), f"Missing the Phase 2 skill at {_SKILL}."
    return _SKILL.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def frontmatter(skill: str) -> str:
    parts = skill.split("---", 2)
    assert len(parts) >= 3, "SKILL.md must open with a YAML frontmatter block."
    return parts[1]


@pytest.fixture(scope="module")
def body(skill: str) -> str:
    return skill.split("---", 2)[2]


@pytest.fixture(scope="module")
def skills_json() -> dict:
    return json.loads(_SKILLS_JSON.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def bundles() -> dict:
    return json.loads(_BUNDLES.read_text(encoding="utf-8"))


# --------------------------------------------------------------------------- #
# Schema and trigger surface
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize(
    "field", ["name", "description", "summary_l0", "overview_l1"]
)
def test_frontmatter_has_required_fields(frontmatter: str, field: str) -> None:
    assert re.search(rf"^{field}:", frontmatter, re.M), (
        f"SKILL.md frontmatter is missing `{field}`. The MCP skill server "
        "depends on all four Tier-1 fields being present and YAML-parseable."
    )


def test_summary_l0_is_quoted_and_within_budget(frontmatter: str) -> None:
    m = re.search(r'^summary_l0: "(.+)"$', frontmatter, re.M)
    assert m, "summary_l0 must be a quoted string (the MCP server parses it as YAML)."
    words = len(m.group(1).split())
    assert words <= 15, (
        f"summary_l0 is {words} words. Tier-1 metadata is loaded for every "
        "catalog skill in every session, so the <=15 word budget is real."
    )


def test_description_declares_triggers_and_a_skip_boundary(frontmatter: str) -> None:
    # The lookahead character class MUST include 0-9: the sibling keys are
    # `summary_l0` and `overview_l1`, so a bare [a-z_]+ never matches them and
    # the description silently runs on through the rest of the frontmatter.
    m = re.search(r"^description: (.+?)(?=\n[a-z_0-9]+: )", frontmatter, re.S | re.M)
    assert m, "SKILL.md must declare a `description`."
    description = m.group(1)
    assert "SKIP" in description, (
        "The description must carry an explicit SKIP clause. Without it, a "
        "pushy description over-triggers on ordinary testing and prompt work."
    )
    for phrase in ("audit our evals", "review our evaluation setup"):
        assert phrase in description, (
            f"The description must list the trigger phrase {phrase!r} verbatim. "
            "Under-triggering is the documented failure mode of clean, narrow "
            "descriptions."
        )


def test_skip_clause_names_the_look_alike_owners(frontmatter: str) -> None:
    skip = frontmatter.split("SKIP", 1)
    assert len(skip) == 2
    for owner in ("unit-tests", "prompt-engineering", "rag-implementation", "ai-output-evaluation"):
        assert owner in skip[1], (
            f"The SKIP clause must route look-alike requests to {owner}. A SKIP "
            "clause that says 'do not use for X' without naming where X goes "
            "leaves the agent with nowhere to route."
        )


# --------------------------------------------------------------------------- #
# The audit method
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize("concern", REQUIRED_CONCERNS)
def test_body_covers_each_inventory_concern(body: str, concern: str) -> None:
    assert concern in body, (
        f"The inventory is missing the {concern!r} concern. All ten exist "
        "because each is a way an evaluation pipeline can pass while the "
        "system it measures is broken."
    )


def test_inventory_concerns_appear_in_the_documented_order(body: str) -> None:
    positions = [body.index(c) for c in REQUIRED_CONCERNS]
    assert positions == sorted(positions), (
        "The ten concerns must appear in their documented order. The order is "
        "part of the method: objectives and datasets before evaluators and "
        "thresholds, so a threshold is judged against a stated objective "
        "rather than the other way round."
    )


def test_inventory_precedes_recommendation(body: str) -> None:
    assert body.index("Step 1: Inventory") < body.index("Step 3: Route"), (
        "Inventory must come before routing. An audit that starts from a "
        "recommendation finds evidence for the recommendation."
    )


def test_findings_use_a_three_state_status(body: str) -> None:
    for state in ("present", "partial", "absent"):
        assert state in body, (
            f"Findings must use the three-state {state!r} vocabulary. A binary "
            "pass/fail hides the partial cases, which are most of them."
        )


def test_severity_is_defined_by_consequence(body: str) -> None:
    assert "BLOCKING" in body, "Severity levels must include BLOCKING."
    blocking = body.split("BLOCKING", 1)[1][:600].lower()
    assert "passing score" in blocking or "while the system is broken" in blocking, (
        "BLOCKING must be defined by consequence (the pipeline can report a "
        "passing score while the system is broken), not by distance from best "
        "practice. Severity assigned by tidiness reorders the work wrongly."
    )


def test_recommendations_are_capped(body: str) -> None:
    assert re.search(r"at most three|next-three|Cap the recommendation", body), (
        "The report must cap its recommendation list. An audit returning "
        "fourteen action items returns none."
    )


# --------------------------------------------------------------------------- #
# Artifact vocabulary and routing
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize("artifact", REQUIRED_ARTIFACT_VOCABULARY)
def test_uses_the_shared_artifact_vocabulary(body: str, artifact: str) -> None:
    assert artifact in body, (
        f"The audit must name the `{artifact}` artifact from the Phase 1 "
        "contract. Shared names are what make a finding checkable ('is there a "
        "split_manifest?') rather than impressionistic ('is this rigorous?')."
    )


@pytest.mark.parametrize("target", REQUIRED_ROUTING_TARGETS)
def test_routing_table_names_each_owner(body: str, target: str) -> None:
    assert f"[[{target}]]" in body, (
        f"The routing table must hand gaps to {target} as a wiki-link. A "
        "coordinating skill that does not name its owners is not routing."
    )


@pytest.mark.parametrize("label,pattern", sorted(FORBIDDEN_SPECIALIST_PATTERNS.items()))
def test_does_not_duplicate_specialist_formulas(body: str, label: str, pattern: str) -> None:
    match = re.search(pattern, body)
    assert not match, (
        f"The skill reproduces the {label}, which belongs to an owner skill. "
        f"Found {match.group(0)!r}. Naming a metric while routing is correct; "
        "defining it creates a second copy that starts drifting immediately. "
        "Route to the owner instead."
    )


def test_declares_itself_a_router(body: str) -> None:
    assert re.search(r"This is a router|delegat", body, re.I), (
        "The body must state that it delegates rather than implements. This is "
        "the instruction that stops the next editor from inlining a method."
    )


# --------------------------------------------------------------------------- #
# Local-data safeguards
# --------------------------------------------------------------------------- #

def test_declares_local_first_handling(body: str) -> None:
    for rule, needle in (
        ("local-by-default", "Local by default"),
        ("bounded excerpts", "Bounded excerpts"),
        ("identifier redaction", "Redact identifiers"),
        ("explicit authorization", "authorization"),
    ):
        assert needle in body, (
            f"The local-data section is missing the {rule} rule. This skill "
            "reads production traces and human labels; losing one of these "
            "rules turns an audit into a data-spreading operation."
        )
    assert "[[egress-redaction]]" in body, (
        "Any egress must defer to egress-redaction's per-category policy."
    )


# --------------------------------------------------------------------------- #
# Required sections
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize(
    "heading",
    ["When to Use This Skill", "Instructions", "Common Rationalizations", "Verification", "Related Skills"],
)
def test_has_required_sections(body: str, heading: str) -> None:
    assert re.search(rf"^##\s+{re.escape(heading)}", body, re.M), (
        f"SKILL.md must contain a '## {heading}' section per the repo schema."
    )


def test_verification_items_are_binary(body: str) -> None:
    section = body.split("## Verification", 1)[1].split("## ", 1)[0]
    items = re.findall(r"^- \[ \] (.+)$", section, re.M)
    assert len(items) >= 5, f"Expected at least 5 verification items, found {len(items)}."
    vague = [i for i in items if re.search(r"\b(looks good|seems|appropriate|reasonable)\b", i, re.I)]
    assert not vague, (
        f"Verification items must describe an observable state, not a judgment: {vague}"
    )


def test_skill_is_ascii_and_within_the_size_norm(skill: str) -> None:
    assert skill.isascii(), "English Markdown in this repo is ASCII-only."
    lines = len(skill.split("\n"))
    assert lines <= 500, (
        f"SKILL.md is {lines} lines, over the 500-line Tier-2 target. A "
        "coordinating skill exceeding the norm is a sign it started "
        "implementing what it should route."
    )


# --------------------------------------------------------------------------- #
# Bundled resources
# --------------------------------------------------------------------------- #

def test_trigger_cases_meet_the_minimum_shape() -> None:
    assert _TRIGGER_CASES.is_file(), f"Missing {_TRIGGER_CASES}."
    data = json.loads(_TRIGGER_CASES.read_text(encoding="utf-8"))
    assert data["skill"] == SKILL_NAME
    cases = data["cases"]
    positives = [c for c in cases if c["should_trigger"]]
    negatives = [c for c in cases if not c["should_trigger"]]
    assert len(positives) >= 3, f"Need >=3 positive cases, found {len(positives)}."
    assert len(negatives) >= 3, f"Need >=3 near-miss negatives, found {len(negatives)}."
    ids = [c["id"] for c in cases]
    assert len(ids) == len(set(ids)), f"Duplicate case ids: {ids}"
    for case in cases:
        assert case["assert"], f"Case {case['id']} has no assertion text."


def test_negative_cases_are_drawn_from_the_skip_clause(frontmatter: str) -> None:
    """Near-miss negatives must route to skills the SKIP clause actually names."""
    data = json.loads(_TRIGGER_CASES.read_text(encoding="utf-8"))
    skip = frontmatter.split("SKIP", 1)[1]
    known = {"unit-tests", "prompt-engineering", "rag-implementation",
             "ai-output-evaluation", "integration-test-generator", "skill-eval-loop"}
    for case in data["cases"]:
        if case["should_trigger"]:
            continue
        named = [s for s in known if s in case["assert"]]
        assert named, (
            f"Negative case {case['id']} does not name the skill it should route "
            "to. A negative that only says 'not here' cannot be acted on."
        )
        assert any(s in skip or s == "skill-eval-loop" for s in named), (
            f"Negative case {case['id']} routes to {named}, which the SKIP "
            "clause does not fence off. Negatives should be drawn from the "
            "skill's own declared boundary, not invented."
        )


def test_agent_descriptor_is_thin_and_not_truncated() -> None:
    assert _AGENT_DESCRIPTOR.is_file(), f"Missing {_AGENT_DESCRIPTOR}."
    text = _AGENT_DESCRIPTOR.read_text(encoding="utf-8")
    assert text.isascii()
    assert "interface:" in text and "display_name:" in text and "short_description:" in text
    assert len(text.split("\n")) <= 8, "The descriptor should stay thin."
    assert text.rstrip().endswith("."), (
        "short_description must end at a sentence boundary. The pre-existing "
        "descriptors in this category were hard-sliced at 200 characters and "
        "ended mid-word; do not reintroduce that."
    )


# --------------------------------------------------------------------------- #
# Registration
# --------------------------------------------------------------------------- #

def test_registered_exactly_once_in_skills_json(skills_json: dict) -> None:
    matches = [s for s in skills_json["skills"] if s["name"] == SKILL_NAME]
    assert len(matches) == 1, f"Expected exactly 1 skills.json entry, found {len(matches)}."
    entry = matches[0]
    assert entry["category"] == "ai-development"
    assert entry["path"].endswith("eval-pipeline-audit/")
    assert entry["summary_l0"].startswith('"') and entry["summary_l0"].endswith('"'), (
        "skills.json stores summary_l0 wrapped in literal quotes (the "
        "convention confirmed across the catalog); description stays unwrapped."
    )
    assert not entry["description"].startswith('"')


def test_registered_in_skill_index() -> None:
    text = _SKILL_INDEX.read_text(encoding="utf-8")
    rows = [ln for ln in text.splitlines() if ln.startswith(f"| {SKILL_NAME} |")]
    assert len(rows) == 1, f"Expected exactly 1 SKILL_INDEX row, found {len(rows)}."
    assert "ai-development" in rows[0]


def test_all_three_catalog_counts_agree(skills_json: dict) -> None:
    index_text = _SKILL_INDEX.read_text(encoding="utf-8")
    marketplace = json.loads(_MARKETPLACE.read_text(encoding="utf-8"))

    json_count = len(skills_json["skills"])
    index_rows = len(re.findall(r"^\| [a-z0-9-]+ \| ", index_text, re.M))
    index_total = int(re.search(r"\*\*Total: (\d+) skills", index_text).group(1))
    marketplace_sum = sum(c["skill_count"] for c in marketplace["categories"])

    assert json_count == index_rows == index_total == marketplace_sum, (
        "Catalog counts disagree - skills.json="
        f"{json_count}, SKILL_INDEX rows={index_rows}, SKILL_INDEX total="
        f"{index_total}, marketplace sum={marketplace_sum}. Registering a skill "
        "means updating all three files together."
    )


@pytest.mark.parametrize("collection,key", [("modules", "ai-engineering"), ("bundles", "ai-engineer")])
def test_included_in_both_ai_selections(bundles: dict, collection: str, key: str) -> None:
    entry = next((e for e in bundles[collection] if e["id"] == key), None)
    assert entry is not None, f"No {collection} entry with id {key!r}."
    assert SKILL_NAME in entry["skills"], (
        f"{SKILL_NAME} must be in the {key} {collection[:-1]}. Phase 7 verifies "
        "focused installs resolve it; absence here makes an AI-engineering "
        "install ship the evaluation skills without their audit entry point."
    )
    assert entry["skills"].count(SKILL_NAME) == 1, "Duplicate entry."


def test_every_selection_skill_resolves_to_a_real_catalog_dir(bundles: dict) -> None:
    """Every selection must resolve, with no allowlist.

    Written to verify the two AI selections, this swept the rest and found four
    pre-existing broken references (v3.16.1 NI-1), all repaired in this phase.
    The check carries no exceptions deliberately: once Phase 6 makes selection
    operational, an unresolvable id means a focused install either fails or
    silently drops a skill the user asked for, and the Phase 5 contract requires
    that to fail before any write.
    """
    available = {p.parent.name for p in (_ROOT / "catalog" / "skills").glob("*/*/SKILL.md")}
    broken = [
        (collection, entry["id"], name)
        for collection in ("modules", "bundles")
        for entry in bundles[collection]
        for name in entry["skills"]
        if name not in available
    ]
    assert not broken, (
        f"Selection entries name skills with no catalog directory: {broken}. "
        "A focused install resolving one of these fails or silently drops it."
    )


def test_no_selection_lists_a_duplicate_skill(bundles: dict) -> None:
    """A duplicate inflates a bundle's count and can double-copy on install."""
    dupes = {}
    for collection in ("modules", "bundles"):
        for entry in bundles[collection]:
            seen = [s for s in set(entry["skills"]) if entry["skills"].count(s) > 1]
            if seen:
                dupes[f"{collection}:{entry['id']}"] = sorted(seen)
    assert not dupes, f"Duplicate skill ids in selection entries: {dupes}"
