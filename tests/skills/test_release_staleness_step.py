"""Tests for the advisory release staleness step (v3.15.5 Phase 5).

The step itself adds no code: it is command + skill behavior that composes
`scripts/check_model_prompting_freshness.py --advisory`, whose runtime behavior
(in-sync, added, removed, UNKNOWN, and never-non-zero-in-advisory) is already
covered exhaustively by `tests/validators/test_check_model_prompting_freshness.py`.

What this module guards is the part prose can silently lose: that both release
entry points DECLARE the step, and that they declare it as advisory,
self-gating, and offline-degrading.

The load-bearing test is `test_freshness_checker_is_not_wired_into_any_gate`. The
plan's explicit worry is that a future editor "fixes" this into a blocking gate,
which would couple the release clock to the vendor's model-release clock. That
test fails the moment the freshness checker appears in the Makefile or CI.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

# v4.0.0: `ci.yml` calls scripts/ci/run.py rather than naming each guard in its
# own `run:` step, so CI reachability is resolved through the profile
# definitions. See tests/validators/_ci_reachability.py for why greping the
# YAML would be both wrong and dangerous to "fix".
from tests.validators._ci_reachability import assert_wired_into_ci

_ROOT = Path(__file__).resolve().parents[2]
_UPDATE_CMD = _ROOT / "catalog" / "commands" / "update.md"
_RUNBOOK = (
    _ROOT / "catalog" / "skills" / "workflow" / "implement-phase"
    / "references" / "implement-phase-runbook.md"
)
_MAKEFILE = _ROOT / "Makefile"
_CI = _ROOT / ".github" / "workflows" / "ci.yml"

FRESHNESS_SCRIPT = "check_model_prompting_freshness"
SCHEMA_SCRIPT = "verify_model_prompting_profiles"


@pytest.fixture(scope="module")
def update_cmd() -> str:
    return _UPDATE_CMD.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def runbook() -> str:
    return _RUNBOOK.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# The step must NOT be a gate anywhere. This is the whole design.
# ---------------------------------------------------------------------------


def _executable_lines(path: Path) -> str:
    """The file's runnable surface, with comment-only lines removed.

    Both the Makefile and ci.yml deliberately CARRY A COMMENT naming the
    freshness checker to explain why it is absent, so a naive substring check
    would flag its own documentation. Only an actual invocation counts.
    """
    kept = [
        line
        for line in path.read_text(encoding="utf-8").splitlines()
        if not line.lstrip().startswith("#")
    ]
    return "\n".join(kept)


@pytest.mark.parametrize(
    ("label", "path"),
    [pytest.param("Makefile", _MAKEFILE, id="makefile"), pytest.param("ci.yml", _CI, id="ci")],
)
def test_freshness_checker_is_not_wired_into_any_gate(label: str, path: Path) -> None:
    """Gating profile freshness would let a vendor's model release wedge a release.

    If this fails, someone made the advisory check blocking. That is the one
    change this design forbids: models ship on the vendor's clock, so a stale
    profile layer must never stop Nexus-Hub from shipping. A COMMENT naming the
    script is fine and expected; an invocation is not.
    """
    assert FRESHNESS_SCRIPT not in _executable_lines(path), (
        f"{label} invokes {FRESHNESS_SCRIPT}.py, making profile freshness a blocking "
        f"gate. It is ADVISORY by design; see /update release governance step 6."
    )


@pytest.mark.parametrize(
    ("label", "path"),
    [pytest.param("Makefile", _MAKEFILE, id="makefile"), pytest.param("ci.yml", _CI, id="ci")],
)
def test_each_gate_file_documents_why_the_checker_is_absent(label: str, path: Path) -> None:
    """The absence must be explained, or a future editor reads it as an oversight."""
    comments = "\n".join(
        line for line in path.read_text(encoding="utf-8").splitlines()
        if line.lstrip().startswith("#")
    )

    assert FRESHNESS_SCRIPT in comments or "advisory" in comments.lower(), (
        f"{label} does not explain why the advisory freshness checker is not a gate; "
        f"without a note the omission looks accidental."
    )


@pytest.mark.parametrize(
    ("label", "path"),
    [pytest.param("Makefile", _MAKEFILE, id="makefile"), pytest.param("ci.yml", _CI, id="ci")],
)
def test_the_structural_sibling_IS_wired_into_every_gate(label: str, path: Path) -> None:
    """The contrast that makes the split meaningful: shape is gated, freshness is not."""
    if label == "ci.yml":
        # v4.0.0: ci.yml calls scripts/ci/run.py rather than naming each guard,
        # so reachability is resolved through the profile definitions.
        assert_wired_into_ci(f"{SCHEMA_SCRIPT}.py")
        return

    body = path.read_text(encoding="utf-8")
    assert SCHEMA_SCRIPT in body, (
        f"{label} no longer runs {SCHEMA_SCRIPT}.py. The profile layer's STRUCTURE "
        f"is a hard gate even though its freshness is not."
    )


# ---------------------------------------------------------------------------
# /update release must declare the step, and declare its contract
# ---------------------------------------------------------------------------


def test_update_release_declares_the_staleness_step(update_cmd: str) -> None:
    assert "Model-prompting-profile staleness check" in update_cmd
    assert "[[model-prompting-research]]" in update_cmd


def test_the_step_comes_after_the_platform_contract_step(update_cmd: str) -> None:
    """Ordering matters: the plan places it after governance step 4."""
    contract = update_cmd.index("Platform read-contract re-verification")
    staleness = update_cmd.index("Model-prompting-profile staleness check")

    assert contract < staleness


@pytest.mark.parametrize(
    "claim",
    [
        "ADVISORY",
        "never blocks the release",
        "self-gates",
        "silent no-op",
        "logged no-op offline",
        "never re-stamps a freshness marker",
        "--advisory",
    ],
)
def test_update_release_states_the_advisory_contract(update_cmd: str, claim: str) -> None:
    assert claim in update_cmd, f"/update release does not state: {claim!r}"


def test_update_release_spells_out_the_contrast_with_the_hard_gate(update_cmd: str) -> None:
    """The plan asks for this explicitly, so a future editor cannot mistake the two."""
    section = update_cmd[update_cmd.index("Model-prompting-profile staleness check"):]

    assert "opposite of step 4" in section
    assert "wedge every Nexus-Hub release" in section


def test_update_release_offers_the_command_on_drift(update_cmd: str) -> None:
    section = update_cmd[update_cmd.index("Model-prompting-profile staleness check"):]

    assert "/tune-prompting" in section
    assert "DRIFTED" in section


def test_the_mirroring_sentence_mentions_the_new_step(update_cmd: str) -> None:
    """The 'this mirrors the implement-phase gate' line must cover step 5 too."""
    line = next(l for l in update_cmd.splitlines() if l.startswith("This mirrors the"))

    assert "prompting-staleness" in line


# ---------------------------------------------------------------------------
# The implement-phase final gate must mirror it, by REFERENCE not duplication
# ---------------------------------------------------------------------------


def test_the_final_phase_gate_mirrors_the_step(runbook: str) -> None:
    gate = runbook[runbook.index("### 9.0"):runbook.index("### 9A")]

    assert "[[model-prompting-research]]" in gate
    assert "ADVISORY" in gate or "advisory" in gate


def test_the_final_phase_gate_defers_instead_of_duplicating(runbook: str) -> None:
    """The plan says 'Do not duplicate logic; reference the skill.'"""
    gate = runbook[runbook.index("### 9.0"):runbook.index("### 9A")]

    assert "Do NOT duplicate its logic" in gate
    assert "governance step 6" in gate, "the gate should point at the canonical description"


def test_the_final_phase_gate_states_it_never_blocks(runbook: str) -> None:
    gate = runbook[runbook.index("### 9.0"):runbook.index("### 9A")]

    assert "NEVER blocks" in gate or "never blocks" in gate


def test_both_entry_points_name_the_same_script(update_cmd: str, runbook: str) -> None:
    """One implementation, two callers: neither may invent its own mechanism."""
    gate = runbook[runbook.index("### 9.0"):runbook.index("### 9A")]

    assert f"{FRESHNESS_SCRIPT}.py" in update_cmd
    assert f"{FRESHNESS_SCRIPT}.py" in gate


# ---------------------------------------------------------------------------
# The step is command + skill behavior, NOT a base-*.md lockstep change
# ---------------------------------------------------------------------------


def test_the_step_did_not_leak_into_the_lockstep_templates() -> None:
    """The plan is explicit that this is not a base-*.md change."""
    templates = sorted((_ROOT / "templates" / "ai-instructions").glob("base-*.md"))
    if not templates:
        pytest.skip("no instruction templates present")

    offenders = [
        t.name
        for t in templates
        if FRESHNESS_SCRIPT in t.read_text(encoding="utf-8")
        or "staleness check" in t.read_text(encoding="utf-8").lower()
    ]

    assert not offenders, (
        f"the staleness step leaked into lockstep template(s): {offenders}. It is "
        f"command + skill behavior, not always-loaded instruction text."
    )


def test_update_md_stays_a_thin_dispatcher(update_cmd: str) -> None:
    """The step must delegate, not inline the procedure."""
    section = update_cmd[update_cmd.index("Model-prompting-profile staleness check"):]
    section = section[: section.index("This mirrors the")]

    # A rough proxy for "did someone paste the runbook in here": the canonical
    # description is a handful of paragraphs, not a procedure with many steps.
    numbered_steps = re.findall(r"^\s*\d+\.\s", section, re.M)

    assert len(numbered_steps) <= 2, (
        f"the staleness step looks inlined ({len(numbered_steps)} numbered steps); "
        f"the procedure belongs in the skill's runbook."
    )
