"""Contract tests for the canonical CI/CD lifecycle (v4.0.0 Phase 1).

These assertions encode section 13 of
`docs/releases/v4/v4.0/development/ci-cd-lifecycle-contract.md`. They are written
FAILING-FIRST on purpose: Phase 1 delivers the contract and these tests, and
Phases 2 through 7 turn each remaining assertion green.

The not-yet-true assertions carried `pytest.mark.xfail(strict=True)` rather than
being weakened or omitted. Strict xfail is self-closing: the moment the phase
that owns the surface lands, the test starts passing and pytest FAILS on the
unexpected pass, forcing the marker off. That is the property a plain skip or a
softened assertion would not give, and it is why the plan's "record the
expected-red assertions rather than weakening them" instruction was satisfied
without leaving the suite red at a phase boundary.

All 23 markers are now gone: 9 came off in Phase 2 and 14 in Phase 5. Not one
assertion was edited to make it pass, and none may be reintroduced -- an
assertion here that cannot pass is a defect in the surface, not in the test.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parents[2]
_DEV = _ROOT / "docs" / "releases" / "v4" / "v4.0" / "development"

CONTRACT = _DEV / "ci-cd-lifecycle-contract.md"
HARNESS_AUDIT = _DEV / "ci-cd-harness-audit.md"
WORKFLOW_AUDIT = _DEV / "ci-cd-workflow-audit.md"

CICD_ARCHITECT = _ROOT / "catalog" / "skills" / "infrastructure" / "cicd-architect" / "SKILL.md"
CD_GENERATOR = _ROOT / "catalog" / "skills" / "infrastructure" / "cd-pipeline-generator" / "SKILL.md"
CICD_INTEGRATION = _ROOT / "catalog" / "skills" / "tests-generation" / "cicd-integration" / "SKILL.md"
GIT_BRANCHING = _ROOT / "catalog" / "skills" / "workflow" / "git-branching-workflow" / "SKILL.md"
UPDATE_CMD = _ROOT / "catalog" / "commands" / "update.md"

TEMPLATES = _ROOT / "templates" / "ai-instructions"
LOCKSTEP_TEMPLATES = (
    "base-claude.md",
    "base-codex.md",
    "base-cursor.md",
    "base-gemini.md",
    "base-opencode.md",
)
INHERITED_TEMPLATES = (
    "base-google-shared.md",
    "base-aider.md",
    "base-kimi.md",
    "base-openclaw.md",
    "base-qwen.md",
    "base-windsurf.md",
    "generic-instructions.md",
)

CI_WORKFLOW = _ROOT / ".github" / "workflows" / "ci.yml"

PROFILES = ("fast", "full", "platform", "report", "release")

#: The heading every instruction template carries once the lifecycle rule ships.
LIFECYCLE_HEADING = "## Plan Lifecycle and CI/CD"

#: Start of the next top-level section, used to bound a block when slicing.
NEXT_SECTION = "\n## "


def _read(path: Path) -> str:
    assert path.is_file(), f"missing required artifact: {path.relative_to(_ROOT)}"
    return path.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# Statement 1 -- the five profiles are named and canonical.
# ---------------------------------------------------------------------------


def test_contract_document_exists_and_is_normative():
    text = _read(CONTRACT)
    assert "**Status**: normative" in text
    assert "provider-neutral" in text.lower()


@pytest.mark.parametrize("profile", PROFILES)
def test_contract_names_every_canonical_profile(profile: str):
    text = _read(CONTRACT)
    assert f"`{profile}`" in text, f"contract does not name the {profile} profile"


def test_contract_names_no_extra_profile_in_the_profile_table():
    """The profile table is the canonical roster; a sixth row is a contract change."""
    text = _read(CONTRACT)
    table = text.split("## 3. Repository-native profiles", 1)[1].split("## 4.", 1)[0]
    rows = re.findall(r"^\| `([a-z]+)` \|", table, flags=re.MULTILINE)
    assert tuple(rows) == PROFILES, f"profile table roster drifted: {rows}"


# ---------------------------------------------------------------------------
# Statements 2, 3, 5 -- phase lifecycle ordering.
# ---------------------------------------------------------------------------


def test_contract_forbids_non_final_push():
    text = _read(CONTRACT)
    assert "MUST NOT push, open a pull request, or start remote CI" in text


def test_contract_assigns_publication_to_the_final_phase():
    text = _read(CONTRACT)
    assert "The final phase MUST run the pipeline reconciliation" in text
    assert "publish its branch exactly once" in text


def test_contract_gates_release_on_green_integration():
    text = _read(CONTRACT)
    assert "MUST NOT begin until the integration result is green and merged" in text


def test_contract_states_that_a_push_event_cannot_prove_a_merge():
    text = _read(CONTRACT)
    assert "EXTERNAL repository-settings contract" in text


# ---------------------------------------------------------------------------
# Statement 7 -- one always-resolving aggregate required check.
# ---------------------------------------------------------------------------


def test_contract_requires_a_single_always_resolving_aggregate():
    text = _read(CONTRACT)
    assert "exactly one aggregate required check" in text
    assert "MUST run unconditionally" in text


def test_ci_workflow_has_exactly_one_always_resolving_aggregate_job():
    """This one is already TRUE at Phase 1; ci-required shipped in v3.17.6."""
    text = _read(CI_WORKFLOW)
    assert "\n  ci-required:\n" in text
    aggregate = text.split("\n  ci-required:\n", 1)[1]
    assert re.search(r"^\s+if: always\(\)\s*$", aggregate, flags=re.MULTILINE), (
        "the aggregate required job must run unconditionally"
    )
    assert "success|skipped)" in aggregate, (
        "the aggregate verdict must be an allowlist, so an unknown result fails closed"
    )


# ---------------------------------------------------------------------------
# Baseline audits -- Phase 1 deliverables.
# ---------------------------------------------------------------------------


def test_harness_audit_covers_every_owning_surface_group():
    text = _read(HARNESS_AUDIT)
    for heading in (
        "## A. Plan generation surfaces",
        "## B. Implementation and commit surfaces",
        "## C. Branch, release, and repository governance surfaces",
        "## D. Platform instruction templates",
        "## E. CI/CD skills",
        "## F. Installer and rendering paths",
    ):
        assert heading in text, f"harness audit is missing {heading}"


def test_harness_audit_rows_all_name_a_closing_phase():
    """Every audited row must map to a later plan task, not to a wish."""
    text = _read(HARNESS_AUDIT)
    rows = re.findall(r"^\| [A-F]\d+ \|.*$", text, flags=re.MULTILINE)
    assert len(rows) >= 20, f"expected a substantive audit, found {len(rows)} rows"
    for row in rows:
        cells = [c.strip() for c in row.strip("|").split("|")]
        closing_phase = cells[-2]
        assert re.fullmatch(r"[1-8]", closing_phase), (
            f"audit row does not name a closing phase: {row}"
        )


def test_workflow_audit_records_the_duplicate_post_merge_finding():
    text = _read(WORKFLOW_AUDIT)
    assert "### Finding W1" in text
    assert "duplicates itself after merge" in text


def test_workflow_audit_records_the_platform_proof_gap():
    text = _read(WORKFLOW_AUDIT)
    assert "### Finding W2" in text
    assert "Windows PowerShell 5.1" in text


def test_workflow_audit_records_already_closed_findings_as_closed():
    """A plan that lists a fixed problem as open teaches the reader to distrust it."""
    text = _read(WORKFLOW_AUDIT)
    section = text.split("## 4. Findings CLOSED before this plan started", 1)
    assert len(section) == 2, "the workflow audit must separate closed findings"
    assert "actions/setup-node@v4" in section[1]
    assert "check_required_check_coverage.py" in section[1]


def test_every_action_reference_is_sha_pinned():
    """Contract 10. Already true; this keeps it true."""
    workflows = sorted((_ROOT / ".github" / "workflows").glob("*.yml"))
    assert workflows, "no workflows found"
    offenders = []
    for wf in workflows:
        for line in wf.read_text(encoding="utf-8").splitlines():
            match = re.search(r"uses:\s*([^\s#]+)", line)
            if not match:
                continue
            ref = match.group(1)
            if ref.startswith("./"):
                continue
            if not re.search(r"@[0-9a-f]{40}$", ref):
                offenders.append(f"{wf.name}: {ref}")
    assert not offenders, f"unpinned action references: {offenders}"


# ---------------------------------------------------------------------------
# Statement 4 -- terminal reconciliation is delegated to cicd-architect.
# Landed in Phase 2; markers removed when these turned green.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("profile", PROFILES)
def test_cicd_architect_defines_every_repository_native_profile(profile: str):
    text = _read(CICD_ARCHITECT)
    assert f"`{profile}`" in text


def test_cicd_architect_defines_existing_pipeline_comparison():
    text = _read(CICD_ARCHITECT).lower()
    assert "existing-pipeline comparison" in text
    for step in ("detect", "compare", "propose", "approve", "apply", "record"):
        assert step in text, f"comparison mode is missing the {step} step"


@pytest.mark.parametrize("path", [CD_GENERATOR, CICD_INTEGRATION])
def test_related_cicd_skills_reference_the_canonical_owner(path: Path):
    """Already true at Phase 1, but only as a Related Skills footer link."""
    assert "[[cicd-architect]]" in _read(path)


@pytest.mark.parametrize("path", [CD_GENERATOR, CICD_INTEGRATION])
def test_related_cicd_skills_declare_conformance_not_just_a_footer_link(path: Path):
    """A Related Skills mention is a pointer; conformance is a rule.

    Phase 2 makes each skill state, in its body, that it invokes and conforms to
    the canonical lifecycle. Asserting only on the wikilink would pass today and
    prove nothing, which is what the Phase 1 audit rows E3 and E4 initially got
    wrong.
    """
    body = _read(path).split("## Related Skills", 1)[0].lower()
    assert "cicd-architect" in body, "the conformance statement must be in the body"
    assert "conform" in body, "the skill must state that it conforms to the canonical lifecycle"


def test_cicd_integration_does_not_default_to_validating_every_push():
    text = _read(CICD_INTEGRATION)
    assert "ordinary feature-branch push" in text.lower()


# ---------------------------------------------------------------------------
# Statement 6 -- the canonical templates carry the shared lifecycle rule.
# Landed in Phase 5; markers removed when these turned green.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("name", LOCKSTEP_TEMPLATES + INHERITED_TEMPLATES)
def test_every_substantive_template_carries_the_lifecycle_block_exactly_once(name: str):
    text = _read(TEMPLATES / name)
    assert text.count(LIFECYCLE_HEADING) == 1, (
        f"{name} must carry {LIFECYCLE_HEADING!r} exactly once, found {text.count(LIFECYCLE_HEADING)}"
    )


def test_git_branching_workflow_defers_publication_to_the_final_phase():
    text = _read(GIT_BRANCHING).lower()
    assert "final phase" in text
    assert "keep phase commits local" in text


def test_update_release_requires_green_integration_before_version_mutation():
    text = _read(UPDATE_CMD).lower()
    assert "integration" in text and "green" in text
    assert "before any version mutation" in text or "before version mutation" in text


# ---------------------------------------------------------------------------
# Template rollout aggregates (v4.0.0 Phase 5).
#
# The parity gate byte-locks only the lockstep five. The other seven
# substantive templates are outside its roster BY DESIGN, because they
# legitimately differ elsewhere -- which is exactly the gap recorded as known
# gap DF-1 for the Communication Contract. The lifecycle block has no valid
# per-platform variation either, so the same three aggregates apply.
# ---------------------------------------------------------------------------

SUBSTANTIVE = LOCKSTEP_TEMPLATES + INHERITED_TEMPLATES
STUBS = (
    "base-antigravity-10.md",
    "base-antigravity-20.md",
    "base-antigravity-cli.md",
    "base-gemini-cli.md",
)


def _lifecycle_body(name: str) -> str:
    text = _read(TEMPLATES / name)
    start = text.index(LIFECYCLE_HEADING)
    rest = text[start + len(LIFECYCLE_HEADING):]
    end = rest.find(NEXT_SECTION)
    return (rest if end == -1 else rest[:end]).strip()


def test_template_roster_matches_the_directory():
    """A new template must be classified, or it silently escapes the rollout."""
    on_disk = {p.name for p in TEMPLATES.glob("*.md")}
    classified = set(SUBSTANTIVE) | set(STUBS)
    assert on_disk == classified, (
        "templates/ai-instructions/ changed. Classify each new file as "
        "substantive (it carries behavioral rules) or a surface-note stub, then "
        f"update this roster. Unclassified: {sorted(on_disk - classified)}; "
        f"listed but missing: {sorted(classified - on_disk)}. "
        "A file classified SUBSTANTIVE must also carry the "
        f"{LIFECYCLE_HEADING!r} block, body-identical to the other eleven -- "
        "classifying it without adding the block turns this failure into a "
        "different one, which is the point: a new template must not silently "
        "escape the rollout."
    )


def test_all_twelve_substantive_templates_are_covered():
    """Guard the count, so a roster edit cannot quietly shrink coverage."""
    assert len(SUBSTANTIVE) == 12


@pytest.mark.parametrize("name", STUBS)
def test_surface_note_stubs_do_not_carry_the_lifecycle_block(name: str):
    assert LIFECYCLE_HEADING not in _read(TEMPLATES / name), (
        f"{name} is a surface-note stub and must not carry behavioral rules"
    )


def test_lifecycle_block_body_is_identical_across_all_twelve():
    """Stronger than the parity gate, which reaches only the lockstep five.

    The block has no valid per-platform variation, so any wording drift is a
    defect rather than a localization.
    """
    bodies = {name: _lifecycle_body(name) for name in SUBSTANTIVE}
    reference_name = SUBSTANTIVE[0]
    reference = bodies[reference_name]
    drifted = [n for n, b in bodies.items() if b != reference]
    assert not drifted, (
        f"lifecycle block drifted from {reference_name} in: {drifted}. "
        "The section is identical by intent."
    )


def test_lifecycle_block_points_at_its_owning_skill():
    """A rule with no pointer leaves the reader nowhere to go for the detail."""
    for name in SUBSTANTIVE:
        assert "cicd-architect" in _lifecycle_body(name), f"{name} lost the skill pointer"


# ---------------------------------------------------------------------------
# This repository follows the lifecycle it distributes.
# ---------------------------------------------------------------------------


def test_agents_md_states_the_lifecycle_for_this_repository():
    text = _read(_ROOT / "AGENTS.md")
    assert "**Plan lifecycle (v4.0.0).**" in text
    for claim in (
        "ONE local commit",
        "No non-final phase pushes",
        "pushes ONCE",
        "reject direct pushes",
        "ci-cd-lifecycle-contract.md",
    ):
        assert claim in text, f"AGENTS.md does not state: {claim!r}"


def test_claude_md_quick_reference_surfaces_the_lifecycle():
    text = _read(_ROOT / "CLAUDE.md")
    assert "Plan lifecycle" in text
    assert "one LOCAL commit" in text
