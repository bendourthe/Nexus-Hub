"""The opt-in application-audit profile must be additive, strict, and honest.

Three groups of property are tested here, and they fail in different ways:

1. **Compatibility.** A schema-v1 record and a schema-v2 record without the
   profile must be evaluated exactly as before, including the number of diff
   keys and the absence of `computed_health`. A profile that changes existing
   output is not additive, whatever its own behavior.
2. **Fail-closed validation.** Malformed identity is a usage error and
   incomplete identity is a closure failure. Those are different exit codes and
   conflating them either hides a broken denominator or reports a diff list the
   gate could not actually compute.
3. **Honesty.** Health is evaluator-owned, self-attestation cannot reach
   `complete`, content observation never upgrades execution provenance, and a
   record can never approve its own mutation.
"""

from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parents[2]
_BUNDLE = _ROOT / "catalog" / "skills" / "code-review" / "security-review"
_GATE_PATH = _BUNDLE / "scripts" / "closure-gate.py"
_FIXTURE = _ROOT / "tests" / "fixtures" / "security-audit" / "application-audit-complete.json"
_CASES = _ROOT / "tests" / "fixtures" / "security-audit" / "cases.json"


def _load_gate():
    spec = importlib.util.spec_from_file_location("closure_gate_profile", _GATE_PATH)
    assert spec and spec.loader, f"cannot load {_GATE_PATH}"
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


gate = _load_gate()


@pytest.fixture
def record() -> dict:
    return json.loads(_FIXTURE.read_text(encoding="utf-8"))


def _evaluate(record: dict) -> dict:
    return gate.evaluate_review_record(record)


def _diff(result: dict, name: str) -> list[str]:
    return result["diffs"][name]


# --------------------------------------------------------------------------
# 1. Compatibility
# --------------------------------------------------------------------------


def test_the_structurally_complete_fixture_has_truthful_degraded_health(record: dict) -> None:
    """Baseline. Every rejection below is attributable to its mutation."""
    result = _evaluate(record)
    assert result["status"] == "clean"
    assert result["failure_count"] == 0
    assert result["computed_health"] == "degraded"


def test_a_schema_v2_record_without_the_profile_is_unchanged() -> None:
    cases = json.loads(_CASES.read_text(encoding="utf-8"))
    plain = next(c for c in cases["cases"] if c["id"] == "clean-no-remediation")["record"]

    result = _evaluate(copy.deepcopy(plain))
    assert "computed_health" not in result, (
        "a record without the profile gained a new top-level key"
    )
    assert len(result["diffs"]) == len(gate.DIFF_NAMES) + len(gate.V2_DIFF_NAMES), (
        "a record without the profile gained new diff keys"
    )
    for name in gate.APPLICATION_AUDIT_DIFF_NAMES:
        assert name not in result["diffs"]


def test_every_existing_case_still_produces_its_expected_result() -> None:
    """The whole pre-existing corpus, so compatibility is proven not assumed.

    The corpus records its expectations as `exit_code` and `diffs`. An earlier
    version of this test read `status` and `failure_count` instead, so both of
    its branches were dead and it asserted NOTHING across all twelve cases
    while reporting green. Asserting the case count first is what keeps that
    from happening again: a corpus that stops loading now fails loudly instead
    of passing an empty loop.
    """
    cases = json.loads(_CASES.read_text(encoding="utf-8"))["cases"]
    assert len(cases) >= 12, f"expected the full corpus, loaded {len(cases)}"

    checked = 0
    for case in cases:
        result = _evaluate(copy.deepcopy(case["record"]))
        expected = case["expect"]

        expected_exit = expected["exit_code"]
        actual_exit = 1 if result["failure_count"] else 0
        assert actual_exit == expected_exit, f"{case['id']} exit code"

        for name, ids in expected["diffs"].items():
            assert result["diffs"][name] == ids, f"{case['id']} diff {name}"
        checked += 1

    assert checked == len(cases), "every case must be asserted, not skipped"


def test_the_profile_requires_schema_version_two(record: dict) -> None:
    record["schema_version"] = 1
    with pytest.raises(gate.RecordError):
        _evaluate(record)


# --------------------------------------------------------------------------
# 2. Malformed identity is a usage error, incomplete identity is a diff
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    "mutation",
    [
        pytest.param(lambda p: p.pop("run_id"), id="missing-run-id"),
        pytest.param(lambda p: p.update(profile_version=99), id="unknown-version"),
        pytest.param(lambda p: p.update(profile_version=True), id="boolean-version"),
        pytest.param(lambda p: p.update(run_id="   "), id="blank-run-id"),
        pytest.param(
            lambda p: p["target_identity"].update(kind="something-else"),
            id="unknown-identity-kind",
        ),
        pytest.param(lambda p: p.pop("target_identity"), id="missing-identity"),
        pytest.param(lambda p: p.pop("execution_boundary"), id="missing-boundary"),
    ],
)
def test_malformed_identity_is_a_usage_error(record: dict, mutation) -> None:
    mutation(record["application_audit"])
    with pytest.raises(gate.RecordError):
        _evaluate(record)


def test_an_incomplete_manifest_is_a_closure_failure_not_a_usage_error(record: dict) -> None:
    """Well-formed but partial coverage. The denominator is understood.

    The unmeasured class is exactly where an undeclared change hides, so this
    must degrade rather than pass.
    """
    record["application_audit"]["target_identity"]["coverage"] = ["tracked", "dirty"]
    record["application_audit"]["claimed_health"] = "degraded"
    result = _evaluate(record)
    assert _diff(result, "application_audit_identity_incomplete")
    assert result["computed_health"] == "failed"


def test_an_immutable_checkout_needs_its_checkout_identity(record: dict) -> None:
    record["application_audit"]["target_identity"] = {"kind": "immutable_checkout"}
    record["application_audit"].pop("target_revalidation", None)
    record["application_audit"]["claimed_health"] = "degraded"
    result = _evaluate(record)
    assert _diff(result, "application_audit_identity_incomplete")


# --------------------------------------------------------------------------
# 3. Health is evaluator-owned
# --------------------------------------------------------------------------


def test_a_producer_claim_never_sets_health(record: dict) -> None:
    """The claim is recorded so a disagreement is visible, and nothing else."""
    record["application_audit"]["claimed_health"] = "complete"
    record["application_audit"]["stages"][0]["state"] = "FAILED"
    record["application_audit"]["stages"][0]["reason_code"] = "TOOL_CRASHED"

    result = _evaluate(record)
    assert result["computed_health"] == "failed"
    assert _diff(result, "provenance_insufficient_for_claimed_health"), (
        "a claim contradicting the computed value must itself be a failure"
    )


def test_a_self_attested_required_run_cannot_reach_complete(record: dict) -> None:
    """Nothing in the record proves that stage ran, so `complete` is unreachable."""
    record["application_audit"]["stages"][0]["provenance"] = "self_attested"
    record["application_audit"]["claimed_health"] = "degraded"

    result = _evaluate(record)
    assert result["computed_health"] == "degraded"


def test_content_observation_does_not_upgrade_execution_provenance(record: dict) -> None:
    """Re-hashing an artifact proves what the bytes are, not who produced them."""
    profile = record["application_audit"]
    profile["stages"][0]["provenance"] = "self_attested"
    for artifact in profile["observed_artifacts"]:
        artifact["provenance"] = "content_observed"
    profile["claimed_health"] = "degraded"

    result = _evaluate(record)
    assert result["computed_health"] == "degraded", (
        "observed artifacts must not lift a self-attested execution stage"
    )


def test_a_failed_required_stage_yields_failed(record: dict) -> None:
    record["application_audit"]["stages"][1]["state"] = "FAILED"
    record["application_audit"]["stages"][1]["reason_code"] = "GRAPH_UNAVAILABLE"
    record["application_audit"]["claimed_health"] = "failed"
    assert _evaluate(record)["computed_health"] == "failed"


def test_an_unavailable_required_stage_degrades_rather_than_passing(record: dict) -> None:
    """An unavailable owner never proves the surface it would have checked."""
    record["application_audit"]["stages"][1]["state"] = "UNAVAILABLE"
    record["application_audit"]["stages"][1]["reason_code"] = "TOOL_NOT_REGISTERED"
    record["application_audit"]["claimed_health"] = "degraded"
    assert _evaluate(record)["computed_health"] == "degraded"


def test_a_non_run_stage_without_a_reason_code_is_unactionable(record: dict) -> None:
    record["application_audit"]["stages"][2].pop("reason_code")
    result = _evaluate(record)
    assert _diff(result, "stages_without_terminal_receipt")


def test_an_unknown_terminal_state_is_rejected(record: dict) -> None:
    record["application_audit"]["stages"][0]["state"] = "PROBABLY_FINE"
    result = _evaluate(record)
    assert _diff(result, "stages_without_terminal_receipt")


# --------------------------------------------------------------------------
# 4. Boundary
# --------------------------------------------------------------------------


def test_an_outbound_stage_without_authorization_is_contradictory(record: dict) -> None:
    """Offline-only means DECLINED, so a claimed run is conflicting evidence."""
    profile = record["application_audit"]
    profile["execution_boundary"]["authorized"] = False
    profile["stages"][2]["state"] = "RAN"
    profile["stages"][2].pop("reason_code", None)
    profile["claimed_health"] = "failed"

    result = _evaluate(record)
    assert _diff(result, "contradictory_or_duplicate_receipts")
    assert result["computed_health"] == "failed"


# --------------------------------------------------------------------------
# 5. Surfaces, graph, artifacts
# --------------------------------------------------------------------------


def test_a_supported_surface_with_no_receipt_is_a_silent_omission(record: dict) -> None:
    """"We did not look" must never read the same as "we found nothing"."""
    profile = record["application_audit"]
    profile["surface_receipts"] = [
        entry for entry in profile["surface_receipts"] if entry["surface"] != "typescript-source"
    ]
    result = _evaluate(record)
    assert "sha256:" + hashlib.sha256(b"typescript-source").hexdigest() in _diff(
        result, "surfaces_without_positive_or_negative_evidence"
    )


def test_contradictory_surface_receipts_fail_rather_than_last_writer_wins(record: dict) -> None:
    profile = record["application_audit"]
    profile["surface_receipts"].append(
        {"surface": "python-source", "result": "negative_checked", "evidence_digest": "9" * 64}
    )
    result = _evaluate(record)
    assert _diff(result, "contradictory_or_duplicate_receipts")


def test_an_unqualified_graph_receipt_is_rejected(record: dict) -> None:
    record["application_audit"]["graph_receipts"][0]["qualified"] = False
    result = _evaluate(record)
    assert _diff(result, "graph_receipts_without_qualified_identity")


def test_graph_quality_below_complete_degrades(record: dict) -> None:
    record["application_audit"]["graph_receipts"][0].update(quality="ambiguous", ambiguity="multiple", result_count=2, reason_code="GRAPH_AMBIGUOUS")
    record["application_audit"]["claimed_health"] = "degraded"
    assert _evaluate(record)["computed_health"] == "degraded"


def test_an_unknown_graph_quality_is_rejected(record: dict) -> None:
    record["application_audit"]["graph_receipts"][0]["quality"] = "probably-fine"
    result = _evaluate(record)
    assert _diff(result, "graph_receipts_without_qualified_identity")


def test_an_artifact_bound_to_another_run_is_rejected(record: dict) -> None:
    """Cross-run substitution: a digest from another run proves nothing here."""
    record["application_audit"]["observed_artifacts"][0]["run_id"] = "some-other-run"
    result = _evaluate(record)
    assert _diff(result, "artifacts_without_bound_digest")


def test_an_artifact_without_a_digest_is_rejected(record: dict) -> None:
    record["application_audit"]["observed_artifacts"][0].pop("digest")
    result = _evaluate(record)
    assert _diff(result, "artifacts_without_bound_digest")


# --------------------------------------------------------------------------
# 6. Mutable-target decision table
# --------------------------------------------------------------------------


def test_an_unproven_change_fails_with_no_envelope(record: dict) -> None:
    """The default for an unproven change is failure, not tolerance."""
    profile = record["application_audit"]
    profile["target_revalidation"] = {
        "before_digest": "e" * 64,
        "after_digest": "f" * 64,
        "changed": True,
    }
    profile["claimed_health"] = "failed"

    result = _evaluate(record)
    assert _diff(result, "mutable_target_change_unproven")
    assert result["computed_health"] == "failed"


def test_a_producer_boolean_does_not_prove_an_out_of_scope_change(record: dict) -> None:
    profile = record["application_audit"]
    profile["target_revalidation"] = {
        "before_digest": "e" * 64,
        "after_digest": "f" * 64,
        "changed": True,
        "change_proven_out_of_scope": True,
        "reason_code": "OUT_OF_SCOPE_CHANGE_PROVEN",
    }
    profile["claimed_health"] = "degraded"

    result = _evaluate(record)
    assert _diff(result, "mutable_target_change_unproven")
    assert result["computed_health"] == "failed"


def test_a_proven_change_still_needs_both_digests(record: dict) -> None:
    profile = record["application_audit"]
    profile["target_revalidation"] = {
        "changed": True,
        "change_proven_out_of_scope": True,
        "reason_code": "OUT_OF_SCOPE_CHANGE_PROVEN",
    }
    result = _evaluate(record)
    assert _diff(result, "mutable_target_change_unproven")


# --------------------------------------------------------------------------
# 7. Approval receipts
# --------------------------------------------------------------------------


def _approval(**overrides) -> dict:
    receipt = {
        "origin": "trusted_host",
        "run_id": "run-2026-09-08-appsec-0001",
        "proposed_patch_digest": "a" * 64,
        "permitted_paths": ["pkg/module.py"],
        "approver_identity": "maintainer-session-1",
        "expiry": "2026-09-08T23:59:59Z",
        "nonce": "n-0001",
        "patcher_identity": "security-patch-advisor",
        "revoked": False,
    }
    receipt.update(overrides)
    return receipt


def test_a_record_cannot_self_declare_trusted_approval_origin(record: dict) -> None:
    record["application_audit"]["approval_receipt"] = _approval()
    result = _evaluate(record)
    assert _diff(result, "approval_receipts_without_trusted_origin")
    assert result["computed_health"] == "failed"


def test_profile_diagnostics_never_publish_supplied_identifiers(record: dict) -> None:
    marker = "credential_CANARY_private@example.invalid"
    record["application_audit"]["run_id"] = marker
    record["application_audit"]["observed_artifacts"][0]["digest"] = "malformed"
    record["application_audit"]["observed_artifacts"][0]["id"] = marker
    result = _evaluate(record)
    assert result["status"] == "failure"
    assert marker not in json.dumps(result)
    assert all(value.startswith("sha256:") for values in result["diffs"].values() for value in values)


@pytest.mark.parametrize("origin", ["input_supplied", "self_attested", "unknown"])
def test_an_untrusted_origin_never_authorizes_mutation(record: dict, origin: str) -> None:
    """A record that supplies its own permission slip describes an attack."""
    record["application_audit"]["approval_receipt"] = _approval(origin=origin)
    result = _evaluate(record)
    assert _diff(result, "approval_receipts_without_trusted_origin")


def test_trusted_origin_is_necessary_but_not_sufficient(record: dict) -> None:
    """Without exact patch binding, a genuine approval authorizes nothing else."""
    receipt = _approval()
    receipt.pop("proposed_patch_digest")
    record["application_audit"]["approval_receipt"] = receipt
    result = _evaluate(record)
    assert _diff(result, "approval_receipts_without_trusted_origin")


def test_a_cross_run_approval_is_rejected(record: dict) -> None:
    record["application_audit"]["approval_receipt"] = _approval(run_id="a-different-run")
    result = _evaluate(record)
    assert _diff(result, "approval_receipts_without_trusted_origin")


def test_a_revoked_approval_is_rejected(record: dict) -> None:
    record["application_audit"]["approval_receipt"] = _approval(revoked=True)
    result = _evaluate(record)
    assert _diff(result, "approval_receipts_without_trusted_origin")


# --------------------------------------------------------------------------
# 8. The record is untrusted input
# --------------------------------------------------------------------------


def test_duplicate_json_members_are_rejected_at_the_gate(tmp_path: Path) -> None:
    """The gate's own loader must reject the silent-last-wins case.

    Without this, a record carrying two `computed_health` values parses as
    whichever came second and the evidence that both were claimed is destroyed
    before any check runs.
    """
    target = tmp_path / "record.json"
    target.write_text('{"schema_version": 2, "schema_version": 1}', encoding="utf-8")
    with pytest.raises(gate.RecordError) as exc:
        gate._load_record(target)
    assert "duplicate_object_member" in str(exc.value)


def test_a_command_string_in_a_record_is_never_executed(record: dict, tmp_path: Path) -> None:
    """Commands are accounting data. A marker file proves nothing ran."""
    marker = tmp_path / "executed.marker"
    profile = record["application_audit"]
    profile["stages"][0]["command"] = f"python -c \"open(r'{marker}','w').write('x')\""

    _evaluate(record)
    assert not marker.exists(), "a command inside the record was executed"


def test_a_path_in_a_record_is_metadata_not_a_read_instruction(record: dict) -> None:
    """An artifact path is recorded, never opened by the evaluator."""
    record["application_audit"]["observed_artifacts"][0]["path"] = "/etc/shadow"
    result = _evaluate(record)
    assert result["status"] in {"clean", "failure"}


# --------------------------------------------------------------------------
# 9. The command-line contract, exercised as a user would
# --------------------------------------------------------------------------

_MALFORMED = _ROOT / "tests" / "fixtures" / "security-audit" / "application-audit-malformed.json"


def _run_cli(path: Path) -> tuple[int, dict]:
    import subprocess

    completed = subprocess.run(
        [sys.executable, str(_GATE_PATH), str(path)],
        capture_output=True,
        text=True,
        check=False,
    )
    payload = json.loads(completed.stdout) if completed.stdout.strip() else {}
    return completed.returncode, payload


def test_the_cli_exits_zero_on_the_complete_fixture() -> None:
    """Run as a real invocation, which is the only way the sibling imports and
    the `sys.path` insert are proven to work outside a test loader."""
    code, payload = _run_cli(_FIXTURE)
    assert code == 0, payload
    assert payload["computed_health"] == "degraded"


def test_the_cli_exits_one_and_names_every_violation_on_the_malformed_fixture() -> None:
    """One record violating several honesty rules at once.

    It would read as a clean, complete audit if any single guard were missing,
    so the assertion is that EVERY violation is named rather than just the
    first one found.
    """
    code, payload = _run_cli(_MALFORMED)
    assert code == 1
    assert payload["computed_health"] == "failed"

    named = {name for name, ids in payload["diffs"].items() if ids}
    assert {
        "application_audit_identity_incomplete",
        "surfaces_without_positive_or_negative_evidence",
        "artifacts_without_bound_digest",
        "approval_receipts_without_trusted_origin",
        "provenance_insufficient_for_claimed_health",
    } <= named, f"only {sorted(named)} were reported"


def test_the_malformed_fixture_claims_health_it_has_not_earned() -> None:
    """Guards the fixture itself, so it cannot rot into a passing record.

    A fixture whose claim quietly became true would make the test above assert
    nothing while still reporting green.
    """
    payload = json.loads(_MALFORMED.read_text(encoding="utf-8"))
    assert payload["application_audit"]["claimed_health"] == "complete"


@pytest.mark.parametrize("mutation", [
    lambda p: p["stages"][0].pop("provenance"),
    lambda p: p["stages"][0].update(stage_identity={}),
    lambda p: p["stages"][0].update(required="false"),
    lambda p: p.update(stages=[]),
    lambda p: p.update(supported_surfaces=[]),
    lambda p: p.update(graph_receipts=[]),
    lambda p: p.update(observed_artifacts=[]),
    lambda p: p["observed_artifacts"][0].update(digest="fake"),
    lambda p: p["observed_artifacts"][0].update(stage_id="missing"),
    lambda p: p["surface_receipts"][0].pop("evidence_digest"),
    lambda p: p["surface_receipts"].append(copy.deepcopy(p["surface_receipts"][0])),
    lambda p: p["graph_receipts"][0].update(availability="UNAVAILABLE"),
    lambda p: p["target_revalidation"].update(after_digest="f" * 64, changed=False),
    lambda p: p.update(target_revalidation={}),
])
def test_invalid_evidence_is_failed_not_degraded(record: dict, mutation) -> None:
    mutation(record["application_audit"])
    result = _evaluate(record)
    assert result["status"] == "failure"
    assert result["computed_health"] == "failed"


def test_authorization_requires_a_json_boolean(record: dict) -> None:
    record["application_audit"]["execution_boundary"]["authorized"] = "false"
    with pytest.raises(gate.RecordError):
        _evaluate(record)


def test_present_null_profile_is_invalid(record: dict) -> None:
    record["application_audit"] = None
    with pytest.raises(gate.RecordError):
        _evaluate(record)


@pytest.mark.parametrize("changed_path,expected_health", [("notes.txt", "degraded"), ("src/app.py", "failed")])
def test_observed_manifests_determine_change_relevance(record: dict, tmp_path: Path, changed_path: str, expected_health: str) -> None:
    import hashlib

    import _target_manifest

    (tmp_path / "src").mkdir()
    (tmp_path / "src/app.py").write_text("before")
    (tmp_path / "notes.txt").write_text("before")
    before = _target_manifest.build_target_manifest(tmp_path)
    (tmp_path / changed_path).write_text("after")
    after = _target_manifest.build_target_manifest(tmp_path)
    profile = record["application_audit"]
    profile["scope_paths"] = ["src"]
    profile["bound_input_paths"] = []
    profile["scope_fingerprint"] = hashlib.sha256(b'["src"]').hexdigest()
    profile["target_identity"]["manifest_digest"] = before["manifest_digest"]
    profile["target_root_fingerprint"] = before["target_root_fingerprint"]
    profile["target_revalidation"] = {
        "before_digest": before["manifest_digest"], "after_digest": after["manifest_digest"],
        "changed": True, "reason_code": "OUT_OF_SCOPE_CHANGE_PROVEN",
    }
    profile["claimed_health"] = expected_health
    profile["run_fingerprint"] = gate.profile_fingerprint(profile)
    for collection in ("stages", "surface_receipts", "graph_receipts", "observed_artifacts"):
        for receipt in profile[collection]:
            receipt["run_fingerprint"] = profile["run_fingerprint"]
    for receipt in profile["graph_receipts"]:
        receipt["target_root_fingerprint"] = profile["target_root_fingerprint"]
        receipt["scope_fingerprint"] = profile["scope_fingerprint"]
    result = gate.evaluate_review_record(record, observed_manifests=(before, after))
    assert result["computed_health"] == expected_health
    assert bool(result["diffs"]["mutable_target_change_unproven"]) == (expected_health == "failed")
