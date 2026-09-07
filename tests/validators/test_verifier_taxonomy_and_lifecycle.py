"""Contracts for the v4.8.0 verifier taxonomy, research finish line, and skill lifecycle.

Three of these contracts are about a distinction that is easy to erode. The
completion-evidence block is ADVISORY in this release for a stated reason (no
measured baseline exists to set a threshold from), and the stocktake's
obviated_by_model column PROPOSES retirement and never deletes. A later edit
that quietly drops either qualifier changes what the catalog does to a user's
work, so both words are asserted rather than trusted.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
CATALOG = ROOT / "catalog"

EVAL_SKILL = CATALOG / "skills" / "developer-experience" / "ai-output-evaluation"
TAXONOMY = EVAL_SKILL / "references" / "verifier-taxonomy.md"
EVALUATOR_VALIDATION = EVAL_SKILL / "references" / "evaluator-validation.md"

RESEARCH_CMD = CATALOG / "commands" / "research.md"
COMPILATION = (
    CATALOG / "skills" / "specialized-domains" / "deep-research-compilation" / "SKILL.md"
)
EVAL_LOOP = CATALOG / "skills" / "workflow" / "skill-eval-loop" / "SKILL.md"
STOCKTAKE_DIR = CATALOG / "skills" / "workflow" / "skill-stocktake"
STOCKTAKE = STOCKTAKE_DIR / "SKILL.md"
FIXTURE = STOCKTAKE_DIR / "assets" / "obviated-fixture.json"

VERIFIER_CLASSES = ("Deterministic", "Evidence-based", "Model-based", "Human")

KNOWLEDGE_WORK_DELIVERABLES = (
    "Deep research",
    "Report generation",
    "Spreadsheet or financial analysis",
    "Document review",
    "Competitive intelligence",
    "Data cleanup and enrichment",
    "Presentation generation",
)

# Both surfaces must carry the same block; a research run and a compile run that
# report different evidence would make the metric incomparable between them.
COMPLETION_EVIDENCE_SURFACES = (RESEARCH_CMD, COMPILATION)

COMPLETION_EVIDENCE_METRICS = (
    "Citation coverage",
    "Duplicate sources",
    "URL resolution",
    "Required sections present",
    "Source freshness",
)


# --- Part one: the taxonomy -------------------------------------------------


def test_taxonomy_exists_and_is_linked_from_step_1() -> None:
    assert TAXONOMY.is_file()
    body = (EVAL_SKILL / "SKILL.md").read_text(encoding="utf-8")
    step1 = body.split("### Step 1:", 1)[1].split("\n### ", 1)[0]
    assert "references/verifier-taxonomy.md" in step1, (
        "the taxonomy must be cited in Step 1, where dimensions are defined and "
        "the grader is chosen"
    )


@pytest.mark.parametrize("cls", VERIFIER_CLASSES)
def test_taxonomy_declares_each_verifier_class_with_a_weakness(cls: str) -> None:
    """A class listed without its weakness reads as a recommendation."""
    text = TAXONOMY.read_text(encoding="utf-8")
    row = re.search(rf"^\| {re.escape(cls)} \|(.*)$", text, flags=re.MULTILINE)
    assert row, f"the taxonomy omits the {cls} class"
    cells = [c.strip() for c in row.group(1).split("|") if c.strip()]
    assert len(cells) >= 3, f"{cls} row is missing Examples, Strength, or weakness"


@pytest.mark.parametrize("deliverable", KNOWLEDGE_WORK_DELIVERABLES)
def test_natural_verifier_table_covers_each_deliverable(deliverable: str) -> None:
    text = TAXONOMY.read_text(encoding="utf-8")
    assert f"| {deliverable} |" in text


def test_taxonomy_states_all_three_rules() -> None:
    text = TAXONOMY.read_text(encoding="utf-8")
    assert "Combine at least two classes" in text
    assert "The producer is never the sole approver" in text
    assert "Verify progress, not only the final artifact" in text


def test_taxonomy_cross_links_resolve() -> None:
    """Two of the three rules point into other bundles; a broken relative path
    fails silently at runtime."""
    text = TAXONOMY.read_text(encoding="utf-8")
    for rel in re.findall(r"\]\((\.\./[^)]+\.md)\)", text):
        assert (TAXONOMY.parent / rel).resolve().is_file(), f"broken link: {rel}"


def test_progress_rule_names_cost_not_only_quality() -> None:
    text = TAXONOMY.read_text(encoding="utf-8")
    rule = text.split("**Verify progress", 1)[1]
    assert "quality per unit cost" in rule
    assert "trace_log" in rule


# --- Part two: the research finish line -------------------------------------


@pytest.mark.parametrize(
    "path", COMPLETION_EVIDENCE_SURFACES, ids=lambda p: p.parent.name
)
def test_surface_carries_a_completion_evidence_section(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    assert "## Completion evidence" in text, f"{path.name} has no completion-evidence section"


@pytest.mark.parametrize(
    "path", COMPLETION_EVIDENCE_SURFACES, ids=lambda p: p.parent.name
)
def test_completion_evidence_is_explicitly_advisory(path: Path) -> None:
    """The advisory stance is scaffolding with a stated reason. Dropping the word
    silently turns a report into a gate."""
    section = path.read_text(encoding="utf-8").split("## Completion evidence", 1)[1]
    section = section.split("\n## ", 1)[0]
    assert "ADVISORY" in section or "advisory" in section
    assert "never blocks" in section, (
        "state that it never blocks, not merely that it is advisory"
    )
    assert "baseline" in section, (
        "state WHY it is advisory (no measured baseline yet), so a later release "
        "knows what would justify making it blocking"
    )


@pytest.mark.parametrize(
    "path", COMPLETION_EVIDENCE_SURFACES, ids=lambda p: p.parent.name
)
@pytest.mark.parametrize("metric", COMPLETION_EVIDENCE_METRICS)
def test_completion_evidence_reports_every_metric(path: Path, metric: str) -> None:
    section = path.read_text(encoding="utf-8").split("## Completion evidence", 1)[1]
    assert metric in section.split("\n## ", 1)[0]


@pytest.mark.parametrize(
    "path", COMPLETION_EVIDENCE_SURFACES, ids=lambda p: p.parent.name
)
def test_uncited_claim_counts_against_coverage(path: Path) -> None:
    """Dropping an uncited claim from the denominator would make the metric
    improve as the deliverable got worse."""
    section = path.read_text(encoding="utf-8").split("## Completion evidence", 1)[1]
    section = section.split("\n## ", 1)[0].lower()
    assert "denominator" in section
    assert "uncovered" in section


@pytest.mark.parametrize(
    "path", COMPLETION_EVIDENCE_SURFACES, ids=lambda p: p.parent.name
)
def test_unresolved_url_is_recorded_with_a_reason_and_does_not_fail_the_run(
    path: Path,
) -> None:
    section = path.read_text(encoding="utf-8").split("## Completion evidence", 1)[1]
    section = section.split("\n## ", 1)[0]
    for reason in ("timeout", "non-200", "paywall"):
        assert reason in section, f"unresolved reasons must name {reason}"
    assert "never as a hard failure" in section


@pytest.mark.parametrize(
    "path", COMPLETION_EVIDENCE_SURFACES, ids=lambda p: p.parent.name
)
def test_completion_evidence_adds_no_new_outbound_call(path: Path) -> None:
    """The zero-new-egress promise: only URLs the run already fetched are counted."""
    section = path.read_text(encoding="utf-8").split("## Completion evidence", 1)[1]
    section = section.split("\n## ", 1)[0]
    assert "already fetched" in section
    assert "no new fetch" in section or "introduces no new fetch" in section


@pytest.mark.parametrize(
    "path", COMPLETION_EVIDENCE_SURFACES, ids=lambda p: p.parent.name
)
def test_completion_evidence_links_the_taxonomy_and_the_link_resolves(
    path: Path,
) -> None:
    section = path.read_text(encoding="utf-8").split("## Completion evidence", 1)[1]
    section = section.split("\n## ", 1)[0]
    rels = re.findall(r"\]\((\.\.?/[^)]*verifier-taxonomy\.md)\)", section)
    assert rels, f"{path.name} does not link the verifier taxonomy"
    for rel in rels:
        assert (path.parent / rel).resolve().is_file(), f"broken link: {rel}"


# --- Part three: the skill lifecycle ----------------------------------------


def test_graduation_rule_states_its_default_n() -> None:
    text = EVAL_LOOP.read_text(encoding="utf-8")
    assert "Graduation: capability case to regression case" in text
    rule = text.split("**Graduation:", 1)[1].split("\n\n", 1)[0]
    assert "default 3" in rule, "N must carry a stated default"
    assert "capability" in rule.lower() and "regression" in rule.lower()


def test_graduated_case_is_retired_not_edited_to_keep_passing() -> None:
    """Rewriting a case to match new output is how a regression set stops
    testing anything."""
    rule = EVAL_LOOP.read_text(encoding="utf-8").split("**Graduation:", 1)[1]
    rule = rule.split("\n\n", 1)[0]
    assert "never edited" in rule
    assert "RETIRED" in rule or "retired" in rule


def test_holdout_hygiene_note_exists_and_is_reciprocal() -> None:
    text = EVALUATOR_VALIDATION.read_text(encoding="utf-8")
    assert "Graduation never touches the held-out split" in text
    assert "skill-eval-loop" in text, "the note must point back at the owning skill"
    rule = EVAL_LOOP.read_text(encoding="utf-8").split("**Graduation:", 1)[1]
    rel = re.search(r"\]\((\.\./[^)]*evaluator-validation\.md)\)", rule)
    assert rel, "the graduation rule must cross-link holdout hygiene"
    assert (EVAL_LOOP.parent / rel.group(1)).resolve().is_file()


def test_stocktake_documents_the_obviated_column_in_its_cache_contract() -> None:
    text = STOCKTAKE.read_text(encoding="utf-8")
    assert "obviated_by_model" in text.split("## Instructions", 1)[0], (
        "the column must appear in the Cache Layout contract, not only in prose"
    )
    assert "### The `obviated_by_model` column" in text


def test_obviated_column_permits_exactly_three_values() -> None:
    section = STOCKTAKE.read_text(encoding="utf-8").split(
        "### The `obviated_by_model` column", 1
    )[1]
    assert "`obviated`" in section
    assert "`review`" in section
    assert "empty" in section


def test_absent_refresh_record_emits_an_empty_column_not_an_omitted_one() -> None:
    """An omitted column reads as 'checked, nothing found' when the truth is
    'not checked'."""
    section = STOCKTAKE.read_text(encoding="utf-8").split(
        "### The `obviated_by_model` column", 1
    )[1]
    assert "never omitted" in section
    assert "EMPTY" in section or "empty" in section


def test_disagreement_is_review_never_obviated() -> None:
    section = STOCKTAKE.read_text(encoding="utf-8").split(
        "### The `obviated_by_model` column", 1
    )[1]
    assert "Disagreement is `review`, never `obviated`" in section


def test_obviated_flag_never_deletes_and_cites_the_maintainer_rule() -> None:
    text = STOCKTAKE.read_text(encoding="utf-8")
    row = [
        line
        for line in text.splitlines()
        if line.startswith("|") and "obviated_by_model` row means" in line
    ]
    assert row, "the rationalizations table must cover the delete misreading"
    assert "never deletes" in row[0]
    assert "Delete existing skills without maintainer approval" in row[0], (
        "cite the AGENTS.md prohibition verbatim rather than paraphrasing it"
    )


def test_stocktake_cross_links_the_record_producer() -> None:
    section = STOCKTAKE.read_text(encoding="utf-8").split(
        "### The `obviated_by_model` column", 1
    )[1]
    assert "[[model-prompting-research]]" in section


def test_fixture_exists_is_linked_and_yields_exactly_one_populated_row() -> None:
    assert FIXTURE.is_file(), "the populated-row fixture is missing"
    assert "assets/obviated-fixture.json" in STOCKTAKE.read_text(encoding="utf-8"), (
        "the fixture would be an orphan bundle if SKILL.md did not link it"
    )
    data = json.loads(FIXTURE.read_text(encoding="utf-8"))
    values = [s["obviated_by_model"] for s in data["skills"].values()]
    obviated = [v for v in values if v.startswith("obviated")]
    review = [v for v in values if v.startswith("review")]
    empty = [v for v in values if v == ""]
    assert len(obviated) == 1, f"expected exactly one obviated row, got {len(obviated)}"
    assert len(review) == 1, "the fixture must also cover the disagreement case"
    assert len(empty) >= 1, "the fixture must show empty as the normal value"
    assert obviated[0].startswith("obviated (20"), (
        "a populated value carries the record date"
    )
    assert '"' in obviated[0], "a populated value quotes the vendor sentence"


def test_current_catalog_yields_no_populated_obviated_rows() -> None:
    """The live catalog has had no model-refresh-driven retirement proposal, so a
    populated row anywhere outside the fixture would be unevidenced."""
    hits = [
        p
        for p in CATALOG.rglob("*.json")
        if p != FIXTURE and "obviated_by_model" in p.read_text(encoding="utf-8")
    ]
    assert not hits, f"unexpected obviated_by_model data outside the fixture: {hits}"


def test_fixture_is_marked_as_illustrative_not_a_real_claim() -> None:
    """A fixture naming a real skill as obsolete would be read as a finding."""
    data = json.loads(FIXTURE.read_text(encoding="utf-8"))
    assert "ILLUSTRATIVE FIXTURE DATA" in data["_comment"]
    for path in data["skills"]:
        assert not (ROOT / path).exists(), (
            f"fixture references a real catalog path ({path}); use a fixture path"
        )


@pytest.mark.parametrize(
    "path", COMPLETION_EVIDENCE_SURFACES, ids=lambda p: p.parent.name
)
def test_local_corpus_reports_zero_urls_with_a_reason(path: Path) -> None:
    """Found by exercising the block on a real local-sourced deliverable: a bare
    `0` for URL resolution beside four healthy metrics reads as a broken run."""
    section = path.read_text(encoding="utf-8").split("## Completion evidence", 1)[1]
    section = section.split("\n## ", 1)[0]
    assert "local corpus, no web sources" in section
    assert "0 of 0" in section


# --- DF-1: the Goal's REVIEW half, closed after the v4.8.0 Goal review --------

MULTI_AGENT_REVIEW = CATALOG / "skills" / "code-review" / "multi-agent-code-review" / "SKILL.md"


def test_review_cluster_names_the_verifier_class_per_finding() -> None:
    """The Goal said "every REVIEW and research deliverable names the verifier
    class that grades it". The research half shipped in v4.8.0; this is the
    review half, closed against DF-1."""
    text = MULTI_AGENT_REVIEW.read_text(encoding="utf-8")
    assert "Name the verifier class per finding" in text
    for cls in ("deterministic", "evidence-based", "model-based", "human"):
        assert cls in text, f"the rule omits the {cls} class"


def test_review_cluster_link_to_the_taxonomy_resolves() -> None:
    text = MULTI_AGENT_REVIEW.read_text(encoding="utf-8")
    rel = re.search(r"\]\((\.\./[^)]*verifier-taxonomy\.md)\)", text)
    assert rel, "the review cluster does not link the taxonomy"
    assert (MULTI_AGENT_REVIEW.parent / rel.group(1)).resolve().is_file()


def test_single_lens_personas_do_not_restate_the_rule() -> None:
    """Rule ownership: the coordinating skill owns it, the personas inherit it.
    Restating it in each persona is the duplication the ownership discipline
    exists to prevent."""
    restaters = [
        p.parent.name
        for p in (CATALOG / "skills" / "code-review").glob("*/SKILL.md")
        if p != MULTI_AGENT_REVIEW
        and "Name the verifier class per finding" in p.read_text(encoding="utf-8")
    ]
    assert not restaters, f"these skills restate an owned rule: {restaters}"
