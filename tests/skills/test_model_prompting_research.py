"""Tests for the model-prompting-research skill bundle (v3.15.5 Phase 2).

Two halves, matching what is actually deterministic in this feature.

The planner and writer (`scripts/write_model_prompting_profile.py`) are real code
and are tested as such: the roster-to-fan-out mapping, the merge, the validation
that refuses a malformed research result, the Markdown mirror regeneration, and
the partial-write case that a budget cap produces. The load-bearing assertion is
the CROSS-CHECK: whatever the writer produces must pass the repo-level structural
gate `scripts/verify_model_prompting_profiles.py`, so the two cannot drift apart.

The research fan-out itself is agent behavior over live web calls and is NOT
unit-run. What IS asserted is that the shipped Dynamic-Workflow template carries
the three mandatory rules, its cross-links, and the budget kill switch, matching
the precedent set by the v3.15.4 visual-QA workflow-template tests.

The bundle script is loaded by path via importlib (it lives outside the test
tree), matching test_media_key_setup.py.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parents[2]
_BUNDLE = _ROOT / "catalog" / "skills" / "ai-development" / "model-prompting-research"
_WRITER_PATH = _BUNDLE / "scripts" / "write_model_prompting_profile.py"
_WORKFLOW_PATH = _BUNDLE / "assets" / "research-workflow.js"
_SKILL_MD = _BUNDLE / "SKILL.md"
_REPO_VALIDATOR = _ROOT / "scripts" / "verify_model_prompting_profiles.py"


def _load_writer():
    spec = importlib.util.spec_from_file_location("mpr_writer", _WRITER_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


writer = _load_writer()


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _claim(text: str = "Be explicit about the output shape.", **over) -> dict:
    base = {
        "claim": text,
        "source_url": "https://vendor.example/docs/prompting",
        "confidence": "high",
        "scope": "model-specific",
    }
    base.update(over)
    return base


def _payload(models: dict, **over) -> dict:
    base = {
        "platform": "claude-code",
        "roster_source": "api",
        "verified_at": "2026-07-27",
        "roster": ["model-a", "model-b", "model-c"],
        "models": models,
    }
    base.update(over)
    return base


@pytest.fixture
def bundle(tmp_path: Path) -> Path:
    """An empty bundle directory; the writer creates assets/ and references/."""
    (tmp_path / "assets").mkdir()
    (tmp_path / "references" / "models").mkdir(parents=True)
    return tmp_path


def _write(bundle: Path, payload: dict, *extra: str) -> subprocess.CompletedProcess[str]:
    """Run the writer's CLI so the real entry point is exercised."""
    payload_path = bundle / "_payload.json"
    payload_path.write_text(json.dumps(payload), encoding="utf-8")
    return subprocess.run(
        [
            sys.executable, str(_WRITER_PATH),
            "--bundle", str(bundle),
            "write", "--input", str(payload_path), *extra,
        ],
        capture_output=True, text=True, check=False, cwd=_ROOT,
    )


def _validate(bundle: Path) -> subprocess.CompletedProcess[str]:
    """Run the REPO-level structural gate against a written bundle."""
    return subprocess.run(
        [sys.executable, str(_REPO_VALIDATOR), "--bundle", str(bundle)],
        capture_output=True, text=True, check=False, cwd=_ROOT,
    )


def _index(bundle: Path) -> dict:
    return json.loads((bundle / "assets" / "profiles-index.json").read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# plan: the roster-to-fan-out mapping
# ---------------------------------------------------------------------------


def test_unprofiled_model_is_a_target() -> None:
    result = writer.plan_targets(["model-a", "model-b"], {})

    assert result["targets"] == ["model-a", "model-b"]


def test_model_with_verified_claims_is_not_a_target() -> None:
    models = {"model-a": {"claims": [_claim()]}}

    result = writer.plan_targets(["model-a", "model-b"], models)

    assert result["targets"] == ["model-b"]


def test_model_with_only_unverified_claims_is_still_a_target() -> None:
    """A hand-seeded claim no verify pass has confirmed does not count as done."""
    models = {"model-a": {"claims": [_claim(confidence="unverified")]}}

    result = writer.plan_targets(["model-a"], models)

    assert result["targets"] == ["model-a"]


def test_model_with_a_mix_of_verified_and_unverified_is_not_a_target() -> None:
    models = {"model-a": {"claims": [_claim(confidence="unverified"), _claim()]}}

    result = writer.plan_targets(["model-a"], models)

    assert result["targets"] == []


def test_model_with_an_empty_claims_list_is_a_target() -> None:
    result = writer.plan_targets(["model-a"], {"model-a": {"claims": []}})

    assert result["targets"] == ["model-a"]


def test_only_narrows_to_one_model_for_calibration() -> None:
    result = writer.plan_targets(["model-a", "model-b"], {}, only="model-b")

    assert result["targets"] == ["model-b"]
    assert result["in_roster"] is True
    assert "calibration" in result["reason"]


def test_only_flags_a_model_absent_from_the_live_roster() -> None:
    result = writer.plan_targets(["model-a"], {}, only="model-z")

    assert result["targets"] == ["model-z"]
    assert result["in_roster"] is False


def test_refresh_all_returns_every_rostered_model() -> None:
    models = {"model-a": {"claims": [_claim()]}}

    result = writer.plan_targets(["model-a", "model-b"], models, refresh_all=True)

    assert result["targets"] == ["model-a", "model-b"]


def test_plan_roster_is_sorted_and_deduped() -> None:
    result = writer.plan_targets(["model-b", "model-a", "model-b", "  "], {})

    assert result["roster"] == ["model-a", "model-b"]
    assert result["targets"] == ["model-a", "model-b"]


def _plan_cli(bundle: Path, *extra: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(_WRITER_PATH), "--bundle", str(bundle), "plan", *extra],
        capture_output=True, text=True, check=False, cwd=_ROOT,
    )


def test_plan_cli_reports_targets_as_json(bundle: Path) -> None:
    """The runbook's documented invocation: the caller scouts the work-list."""
    result = _plan_cli(bundle, "--roster", "model-a", "model-b")

    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)["targets"] == ["model-a", "model-b"]


def test_plan_cli_falls_back_to_the_recorded_roster(bundle: Path) -> None:
    """With no --roster, the planner reads the roster already in the index."""
    _write(bundle, _payload({"model-a": [_claim()]}, roster=["model-a", "model-b"]))

    result = _plan_cli(bundle)

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["roster"] == ["model-a", "model-b"]
    assert payload["targets"] == ["model-b"], "model-a is already verified"


def test_plan_cli_on_an_empty_bundle_is_not_an_error(bundle: Path) -> None:
    result = _plan_cli(bundle)

    assert result.returncode == 0
    assert json.loads(result.stdout)["targets"] == []


# ---------------------------------------------------------------------------
# write: the merge, and the cross-check against the repo validator
# ---------------------------------------------------------------------------


def test_written_layer_passes_the_repo_structural_gate(bundle: Path) -> None:
    """The load-bearing test: the writer cannot produce a layer the gate rejects."""
    result = _write(bundle, _payload({"model-a": [_claim()]}))
    assert result.returncode == 0, result.stdout + result.stderr

    validated = _validate(bundle)

    assert validated.returncode == 0, validated.stdout


def test_write_regenerates_the_markdown_mirror(bundle: Path) -> None:
    _write(bundle, _payload({"model-a": [_claim("Number the steps explicitly.")]}))

    mirror = (bundle / "references" / "models" / "model-a.md").read_text(encoding="utf-8")

    assert "# Prompting Profile: model-a" in mirror
    assert "Number the steps explicitly." in mirror
    assert "`high`" in mirror and "`model-specific`" in mirror
    assert "https://vendor.example/docs/prompting" in mirror
    assert "Does not apply to shared bodies" in mirror


def test_write_merges_without_clobbering_an_existing_model(bundle: Path) -> None:
    _write(bundle, _payload({"model-a": [_claim("First.")]}))

    _write(bundle, _payload({"model-b": [_claim("Second.")]}))

    index = _index(bundle)
    assert sorted(index["models"]) == ["model-a", "model-b"]
    assert index["models"]["model-a"]["claims"][0]["claim"] == "First."
    assert _validate(bundle).returncode == 0


def test_write_restamps_the_roster_and_its_hash(bundle: Path) -> None:
    _write(bundle, _payload({"model-a": [_claim()]}, roster=["model-b", "model-a"]))

    meta = _index(bundle)["meta"]

    assert meta["roster"] == ["model-a", "model-b"], "roster must be stored sorted"
    expected = hashlib.sha256("model-a\nmodel-b".encode("utf-8")).hexdigest()
    assert meta["roster_hash"] == expected


def test_write_widens_the_roster_to_cover_a_profiled_model(bundle: Path) -> None:
    """The index must never claim a model it has no roster entry for."""
    _write(bundle, _payload({"model-z": [_claim()]}, roster=["model-a"]))

    meta = _index(bundle)["meta"]

    assert "model-z" in meta["roster"]
    assert _validate(bundle).returncode == 0


def test_partial_write_leaves_a_valid_layer(bundle: Path) -> None:
    """The budget-cap case: 1 of 4 models verified must still validate."""
    payload = _payload({"model-a": [_claim()]}, roster=["model-a", "model-b", "model-c", "model-d"])

    result = _write(bundle, payload)

    assert result.returncode == 0
    assert _validate(bundle).returncode == 0
    assert "UNVERIFIED" in result.stdout
    for unprofiled in ("model-b", "model-c", "model-d"):
        assert unprofiled in result.stdout


def test_dry_run_writes_nothing(bundle: Path) -> None:
    result = _write(bundle, _payload({"model-a": [_claim()]}), "--dry-run")

    assert result.returncode == 0
    assert "DRY RUN" in result.stdout
    assert not (bundle / "assets" / "profiles-index.json").exists()


def test_mirror_escapes_a_pipe_in_claim_text(bundle: Path) -> None:
    """A raw pipe would silently break the Markdown table."""
    _write(bundle, _payload({"model-a": [_claim("Use A | B to separate options.")]}))

    mirror = (bundle / "references" / "models" / "model-a.md").read_text(encoding="utf-8")

    assert "A \\| B" in mirror


# ---------------------------------------------------------------------------
# write: a malformed research result must abort the whole write
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("claim_override", "expected"),
    [
        pytest.param({"scope": "shared-body"}, "scope must be one of", id="bad_scope"),
        pytest.param({"confidence": "pretty sure"}, "confidence must be one of", id="bad_confidence"),
        pytest.param({"source_url": "docs/local.md"}, "must be an http(s) URL", id="non_http_source"),
        pytest.param({"claim": "   "}, "must be a non-empty string", id="empty_claim"),
        pytest.param({"sources_url": "x"}, "unknown key", id="typo_key"),
        pytest.param({"note": 7}, "note must be a string", id="non_string_note"),
    ],
)
def test_malformed_claim_aborts_the_write(
    bundle: Path, claim_override: dict, expected: str
) -> None:
    result = _write(bundle, _payload({"model-a": [_claim(**claim_override)]}))

    assert result.returncode == 1, result.stdout
    assert expected in result.stderr, result.stderr
    assert not (bundle / "assets" / "profiles-index.json").exists(), "nothing may be written"


def test_missing_required_claim_key_aborts_the_write(bundle: Path) -> None:
    partial = _claim()
    del partial["scope"]

    result = _write(bundle, _payload({"model-a": [partial]}))

    assert result.returncode == 1
    assert "missing required key 'scope'" in result.stderr


@pytest.mark.parametrize(
    ("payload_override", "expected"),
    [
        pytest.param({"roster_source": "guessed"}, "roster_source must be one of", id="bad_source"),
        pytest.param({"verified_at": "July 2026"}, "verified_at must be a YYYY-MM-DD", id="bad_date"),
        pytest.param({"platform": "  "}, "platform must be a non-empty string", id="empty_platform"),
        pytest.param({"models": {}}, "models must be a non-empty object", id="no_models"),
    ],
)
def test_malformed_payload_aborts_the_write(
    bundle: Path, payload_override: dict, expected: str
) -> None:
    payload = _payload({"model-a": [_claim()]})
    payload.update(payload_override)

    result = _write(bundle, payload)

    assert result.returncode == 1
    assert expected in result.stderr
    assert not (bundle / "assets" / "profiles-index.json").exists()


def test_a_model_with_no_claims_aborts_the_write(bundle: Path) -> None:
    """Zero surviving claims means leave the model UNVERIFIED, not write an empty entry."""
    result = _write(bundle, _payload({"model-a": []}))

    assert result.returncode == 1
    assert "non-empty array of claims" in result.stderr


# ---------------------------------------------------------------------------
# The workflow template: the three mandatory rules and the kill switch
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def workflow_text() -> str:
    return _WORKFLOW_PATH.read_text(encoding="utf-8")


@pytest.mark.parametrize(
    "marker",
    [
        "GRACEFUL DEGRADATION (REQUIRED)",
        "SCOPE-FIRST TOKEN CAUTION (REQUIRED)",
        "SKILL-NATIVE (REQUIRED)",
    ],
)
def test_workflow_template_carries_the_three_mandatory_rules(
    workflow_text: str, marker: str
) -> None:
    assert marker in workflow_text


def test_workflow_template_is_marked_as_a_template_not_a_script(workflow_text: str) -> None:
    assert "TEMPLATE TO ADAPT" in workflow_text
    assert "NOT meant to run verbatim" in workflow_text


@pytest.mark.parametrize(
    "link", ["[[agent-orchestration-primitives]]", "[[ai-billing-safeguards]]", "[[adversarial-verifier]]"]
)
def test_workflow_template_cross_links(workflow_text: str, link: str) -> None:
    assert link in workflow_text


def test_workflow_template_declares_the_budget_cap_and_kill_switch(workflow_text: str) -> None:
    assert "PER_MODEL_BUDGET" in workflow_text
    assert "budget.remaining()" in workflow_text
    # The check must happen BEFORE a branch starts, which is what makes the
    # termination graceful rather than mid-verification.
    assert "budget.total && budget.remaining() < RESERVE" in workflow_text


def test_workflow_template_documents_the_offline_no_op(workflow_text: str) -> None:
    assert "OFFLINE" in workflow_text
    assert "LOGGED NO-OP" in workflow_text


def test_workflow_template_names_every_degradation_rung(workflow_text: str) -> None:
    for rung in ("Dynamic Workflow", "Isolated subagents", "single sequential agent"):
        assert rung in workflow_text


@pytest.mark.parametrize("forbidden", ["Date.now(", "Math.random("])
def test_workflow_template_avoids_runtime_forbidden_calls(
    workflow_text: str, forbidden: str
) -> None:
    """The workflow runtime throws on these; they would break resume."""
    assert forbidden not in workflow_text


def test_workflow_template_defaults_ambiguous_scope_to_model_specific(
    workflow_text: str,
) -> None:
    assert "model-specific" in workflow_text
    assert "in doubt" in workflow_text.lower()


# ---------------------------------------------------------------------------
# SKILL.md wiring
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "resource",
    [
        "research-runbook.md",
        "schema.md",
        "profiles-index.json",
        "research-workflow.js",
        "write_model_prompting_profile.py",
    ],
)
def test_skill_md_references_every_bundled_resource(resource: str) -> None:
    """Mirrors the orphan-bundle audit, but fails loudly at the skill level."""
    assert resource in _SKILL_MD.read_text(encoding="utf-8")


def test_skill_md_fences_off_its_two_same_category_neighbours() -> None:
    body = _SKILL_MD.read_text(encoding="utf-8")

    assert "[[model-routing]]" in body
    assert "[[prompt-engineering]]" in body
    assert "SKIP choosing a model" in body
