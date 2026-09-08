#!/usr/bin/env python3
"""Fail a security review whose claims do not resolve to recorded evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any

_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    # Bundled siblings travel with this skill and are imported by name. The
    # insert is what makes that work both for `python scripts/closure-gate.py`
    # run from an arbitrary directory AND for a test harness that loads this
    # file by location, which does not put the file's directory on sys.path.
    sys.path.insert(0, str(_HERE))

import _strict_json

EXIT_CLEAN = 0
EXIT_CLOSURE_FAILURE = 1
EXIT_USAGE_ERROR = 2

SCHEMA_VERSION = 1
SCHEMA_VERSION_V2 = 2
SUPPORTED_SCHEMA_VERSIONS = {SCHEMA_VERSION, SCHEMA_VERSION_V2}
DISPOSITIONS = {
    "confirmed",
    "needs-live-validation",
    "corrected",
    "rejected",
}
REJECTION_RESULTS = {"observed-blocked", "observed-safe", "not-applicable"}
RECEIPT_STATES = {
    "RAN",
    "NOT_APPLICABLE",
    "UNAVAILABLE",
    "FAILED",
    "DECLINED",
}
COVERAGE_STATUSES = {"complete", "degraded"}
NON_RUN_APPLICABLE_STATES = {"UNAVAILABLE", "FAILED", "DECLINED"}
DIFF_NAMES = (
    "components_without_review_action_or_caveat",
    "findings_without_terminal_or_pending_disposition",
    "confirmed_findings_without_supporting_evidence",
    "rejected_findings_without_complete_rejection_record",
    "report_claims_without_matching_facts",
)
V2_DIFF_NAMES = (
    "applicable_scanners_without_successful_run",
    "malformed_or_unsupported_receipt_states",
    "corrected_scanner_findings_without_equivalent_rescan",
    "mismatched_detector_config_or_scope",
    "unresolved_new_after_scan_findings",
    "fixer_is_sole_verifier",
)

#: Emitted ONLY when the opt-in `application_audit` profile is present, so a
#: record without it keeps its previous output bytes exactly. Adding these keys
#: unconditionally would change every existing v2 record's output.
APPLICATION_AUDIT_DIFF_NAMES = (
    "application_audit_identity_incomplete",
    "stages_without_terminal_receipt",
    "surfaces_without_positive_or_negative_evidence",
    "graph_receipts_without_qualified_identity",
    "artifacts_without_bound_digest",
    "contradictory_or_duplicate_receipts",
    "mutable_target_change_unproven",
    "approval_receipts_without_trusted_origin",
    "provenance_insufficient_for_claimed_health",
)

PROFILE_VERSION = 1
GRAPH_QUALITIES = {"complete", "partial", "ambiguous", "unknown"}
PROVENANCE_ASSURANCES = {"content_observed", "self_attested"}
HEALTH_VALUES = {"complete", "degraded", "failed"}
REQUIRED_IDENTITY_FIELDS = (
    "run_id",
    "target_revision",
    "target_root_fingerprint",
    "scope_fingerprint",
    "routing_manifest_digest",
    "run_fingerprint",
)
#: A content manifest is complete only when it measured every one of these. The
#: unmeasured class is exactly where an undeclared change hides.
REQUIRED_MANIFEST_COVERAGE = ("tracked", "dirty", "untracked", "submodule", "link")


class RecordError(ValueError):
    """Raised when the review record cannot be evaluated safely."""


def _is_text(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _require_list(record: dict[str, Any], key: str) -> list[Any]:
    value = record.get(key)
    if not isinstance(value, list):
        raise RecordError(f"{key} must be a list")
    return value


def _require_object(value: object, location: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise RecordError(f"{location} must be an object")
    return value


def _index_records(items: list[Any], collection: str) -> dict[str, dict[str, Any]]:
    indexed: dict[str, dict[str, Any]] = {}
    for position, raw_item in enumerate(items):
        item = _require_object(raw_item, f"{collection}[{position}]")
        item_id = item.get("id")
        if not _is_text(item_id):
            raise RecordError(f"{collection}[{position}].id must be non-empty text")
        if item_id in indexed:
            raise RecordError(f"{collection} contains duplicate id: {item_id}")
        indexed[item_id] = item
    return indexed


def _text_list(value: object) -> list[str] | None:
    if not isinstance(value, list) or not all(_is_text(item) for item in value):
        return None
    return [item.strip() for item in value]


def _fact_is_supported(fact: dict[str, Any] | None) -> bool:
    return fact is not None and _is_text(fact.get("evidence"))


def _component_is_resolved(
    component: dict[str, Any], actions: dict[str, dict[str, Any]]
) -> bool:
    component_id = component["id"]
    status = component.get("status")
    if not isinstance(status, str):
        return False
    action_ids = _text_list(component.get("review_action_ids"))
    if action_ids is None:
        return False

    valid_actions = []
    for action_id in action_ids:
        action = actions.get(action_id)
        if action is None or action.get("component_id") != component_id:
            continue
        if all(
            _is_text(action.get(field)) for field in ("action", "result", "evidence")
        ):
            valid_actions.append(action_id)

    if status == "COVERED":
        return bool(valid_actions)
    if status in {"OMITTED", "UNCOVERED"}:
        return _is_text(component.get("caveat"))
    return False


def _live_validation_is_explicit(finding: dict[str, Any]) -> bool:
    receipt = finding.get("pending_validation")
    if not isinstance(receipt, dict):
        return False
    required = (
        "safe_test",
        "expected_vulnerable",
        "expected_safe",
        "potential_severity",
    )
    return all(_is_text(receipt.get(field)) for field in required)


def _rejection_is_complete(finding: dict[str, Any]) -> bool:
    record = finding.get("rejection_record")
    if not isinstance(record, dict) or not _is_text(record.get("counter_hypothesis")):
        return False

    input_sources = _text_list(record.get("actual_input_sources"))
    routes = record.get("routes")
    if not input_sources or not isinstance(routes, list) or not routes:
        return False

    routed_sources: list[str] = []
    for raw_route in routes:
        if not isinstance(raw_route, dict):
            return False
        source = raw_route.get("source")
        result = raw_route.get("result")
        evidence = raw_route.get("evidence")
        if (
            not _is_text(source)
            or not _is_text(result)
            or result not in REJECTION_RESULTS
            or not _is_text(evidence)
        ):
            return False
        routed_sources.append(source.strip())

    if len(input_sources) != len(set(input_sources)):
        return False
    if set(routed_sources) != set(input_sources) or len(routed_sources) != len(
        input_sources
    ):
        return False

    reachability_claim = record.get("reachability_claim", False)
    if not isinstance(reachability_claim, bool):
        return False
    if reachability_claim:
        reachability_evidence = _text_list(record.get("reachability_evidence"))
        if not reachability_evidence:
            return False
    return True


def _is_int(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _scope_fingerprint(scope: object) -> str | None:
    if not isinstance(scope, dict):
        return None
    fingerprint = scope.get("fingerprint")
    if not _is_text(fingerprint):
        return None
    return fingerprint.strip()


def _ran_fields_complete(receipt: dict[str, Any]) -> bool:
    text_fields = (
        "scanner_id",
        "scanner_version",
        "applicability_evidence",
        "config_fingerprint",
        "command",
        "started_at",
        "finished_at",
        "artifact_path",
    )
    return (
        all(_is_text(receipt.get(field)) for field in text_fields)
        and _is_int(receipt.get("exit_code"))
        and _scope_fingerprint(receipt.get("target_scope")) is not None
    )


def _not_applicable_complete(receipt: dict[str, Any]) -> bool:
    return all(
        _is_text(receipt.get(field))
        for field in ("scanner_id", "applicability_evidence", "omission_reason")
    )


def _non_run_complete(receipt: dict[str, Any]) -> bool:
    return all(
        _is_text(receipt.get(field))
        for field in ("scanner_id", "applicability_evidence", "omission_reason")
    )


def _failed_complete(receipt: dict[str, Any]) -> bool:
    return (
        _non_run_complete(receipt)
        and _is_text(receipt.get("command"))
        and _is_int(receipt.get("exit_code"))
    )


def _receipt_ran_successfully(receipt: dict[str, Any]) -> bool:
    return receipt.get("state") == "RAN" and _ran_fields_complete(receipt)


def _append_unique(values: list[str], item_id: str) -> None:
    if item_id not in values:
        values.append(item_id)


def _record_receipt_shape(receipt: dict[str, Any], diffs: dict[str, list[str]]) -> None:
    receipt_id = str(receipt["id"])
    state = receipt.get("state")
    if not isinstance(state, str) or state not in RECEIPT_STATES:
        _append_unique(diffs["malformed_or_unsupported_receipt_states"], receipt_id)
        return
    complete = False
    if state == "RAN":
        complete = _ran_fields_complete(receipt)
    elif state == "NOT_APPLICABLE":
        complete = _not_applicable_complete(receipt)
    elif state == "FAILED":
        complete = _failed_complete(receipt)
    else:
        complete = _non_run_complete(receipt)
    if not complete:
        _append_unique(diffs["malformed_or_unsupported_receipt_states"], receipt_id)


def _finding_is_dispositioned(finding: dict[str, Any] | None) -> bool:
    if finding is None:
        return False
    disposition = finding.get("disposition")
    if not isinstance(disposition, str) or disposition not in DISPOSITIONS:
        return False
    if disposition == "needs-live-validation":
        return _live_validation_is_explicit(finding)
    return True


def _evaluate_scanner_inventory(
    inventory: dict[str, dict[str, Any]],
    receipts_by_scanner: dict[str, list[dict[str, Any]]],
    coverage_status: str,
    diffs: dict[str, list[str]],
) -> None:
    for scanner_id, item in inventory.items():
        applicable = item.get("applicable")
        if not isinstance(applicable, bool) or not _is_text(item.get("evidence")):
            _append_unique(diffs["malformed_or_unsupported_receipt_states"], scanner_id)
            continue

        matching = receipts_by_scanner.get(scanner_id, [])
        if not matching:
            _append_unique(
                diffs["applicable_scanners_without_successful_run"], scanner_id
            )
            continue

        if not applicable:
            has_valid_na = any(
                receipt.get("state") == "NOT_APPLICABLE"
                and _not_applicable_complete(receipt)
                for receipt in matching
            )
            if has_valid_na:
                continue
            if any(receipt.get("state") == "NOT_APPLICABLE" for receipt in matching):
                continue
            _append_unique(
                diffs["applicable_scanners_without_successful_run"], scanner_id
            )
            continue

        if any(_receipt_ran_successfully(receipt) for receipt in matching):
            continue
        if any(receipt.get("state") == "RAN" for receipt in matching):
            continue

        honest_non_run = any(
            receipt.get("state") in NON_RUN_APPLICABLE_STATES
            and (
                _failed_complete(receipt)
                if receipt.get("state") == "FAILED"
                else _non_run_complete(receipt)
            )
            for receipt in matching
        )
        if honest_non_run and coverage_status == "degraded":
            continue
        _append_unique(diffs["applicable_scanners_without_successful_run"], scanner_id)


def _evaluate_remediations(
    remediations: dict[str, dict[str, Any]],
    receipts: dict[str, dict[str, Any]],
    findings: dict[str, dict[str, Any]],
    diffs: dict[str, list[str]],
) -> list[str]:
    fixer_identities: list[str] = []
    for rem_id, remediation in remediations.items():
        fixer = remediation.get("fixer_identity")
        if _is_text(fixer):
            fixer_identities.append(fixer.strip())
        else:
            _append_unique(diffs["malformed_or_unsupported_receipt_states"], rem_id)

        finding_ids = _text_list(remediation.get("finding_ids"))
        before_id = remediation.get("before_receipt_id")
        after_id = remediation.get("after_receipt_id")
        delta = remediation.get("finding_delta")
        if (
            finding_ids is None
            or not finding_ids
            or not _is_text(before_id)
            or not _is_text(after_id)
            or not isinstance(delta, dict)
        ):
            _append_unique(diffs["malformed_or_unsupported_receipt_states"], rem_id)
            continue

        before = receipts.get(before_id.strip())
        after = receipts.get(after_id.strip())
        for finding_id in finding_ids:
            finding = findings.get(finding_id)
            source = finding.get("source_scanner_id") if finding else None
            if finding is None or finding.get("disposition") != "corrected":
                continue
            if not _is_text(source):
                continue
            if before is None or after is None:
                _append_unique(
                    diffs["corrected_scanner_findings_without_equivalent_rescan"],
                    finding_id,
                )
                continue
            same_detector = (
                before.get("scanner_id") == source.strip()
                and after.get("scanner_id") == source.strip()
            )
            same_config = _is_text(before.get("config_fingerprint")) and before.get(
                "config_fingerprint"
            ) == after.get("config_fingerprint")
            same_scope = _scope_fingerprint(
                before.get("target_scope")
            ) is not None and _scope_fingerprint(
                before.get("target_scope")
            ) == _scope_fingerprint(after.get("target_scope"))
            if not (same_detector and same_config and same_scope):
                _append_unique(diffs["mismatched_detector_config_or_scope"], finding_id)

        before_obs = (
            set(_text_list(before.get("observed_finding_ids")) or [])
            if before
            else set()
        )
        after_obs = (
            set(_text_list(after.get("observed_finding_ids")) or []) if after else set()
        )
        declared_new = set(_text_list(delta.get("new_finding_ids")) or [])
        computed_new = (
            (after_obs - before_obs) if (after_obs or before_obs) else declared_new
        )
        for new_id in sorted(computed_new | declared_new):
            if not _finding_is_dispositioned(findings.get(new_id)):
                _append_unique(diffs["unresolved_new_after_scan_findings"], new_id)

    for finding_id, finding in findings.items():
        if finding.get("disposition") != "corrected" or not _is_text(
            finding.get("source_scanner_id")
        ):
            continue
        linked = False
        for remediation in remediations.values():
            named = _text_list(remediation.get("finding_ids")) or []
            if finding_id not in named:
                continue
            before = receipts.get(str(remediation.get("before_receipt_id", "")).strip())
            after = receipts.get(str(remediation.get("after_receipt_id", "")).strip())
            if before is not None and after is not None:
                linked = True
                break
        if not linked:
            _append_unique(
                diffs["corrected_scanner_findings_without_equivalent_rescan"],
                finding_id,
            )

    return fixer_identities


def _evaluate_verifiers(
    verifiers_raw: list[Any], fixer_identities: list[str], diffs: dict[str, list[str]]
) -> None:
    independent = False
    fixer_set = set(fixer_identities)
    for position, raw_verifier in enumerate(verifiers_raw):
        verifier = _require_object(raw_verifier, f"verifiers[{position}]")
        identity = verifier.get("identity")
        read_only = verifier.get("read_only")
        if not _is_text(identity) or not isinstance(read_only, bool):
            raise RecordError(
                f"verifiers[{position}] must include identity text and boolean read_only"
            )
        if identity.strip() not in fixer_set and read_only is True:
            independent = True
    if not independent:
        diffs["fixer_is_sole_verifier"].append("verifiers")


def _evaluate_schema_v2(
    record: dict[str, Any],
    findings: dict[str, dict[str, Any]],
    diffs: dict[str, list[str]],
) -> None:
    for name in V2_DIFF_NAMES:
        diffs[name] = []

    coverage = _require_object(
        record.get("deterministic_coverage"), "deterministic_coverage"
    )
    coverage_status = coverage.get("status")
    if not isinstance(coverage_status, str) or coverage_status not in COVERAGE_STATUSES:
        raise RecordError("deterministic_coverage.status must be complete or degraded")

    inventory = _index_records(
        _require_list(record, "scanner_inventory"), "scanner_inventory"
    )
    receipts = _index_records(
        _require_list(record, "scanner_receipts"), "scanner_receipts"
    )
    remediations = _index_records(
        _require_list(record, "remediation_receipts"), "remediation_receipts"
    )
    verifiers_raw = _require_list(record, "verifiers")

    receipts_by_scanner: dict[str, list[dict[str, Any]]] = {}
    for receipt in receipts.values():
        _record_receipt_shape(receipt, diffs)
        scanner_id = receipt.get("scanner_id")
        if _is_text(scanner_id):
            receipts_by_scanner.setdefault(scanner_id.strip(), []).append(receipt)

    _evaluate_scanner_inventory(inventory, receipts_by_scanner, coverage_status, diffs)
    fixer_identities = _evaluate_remediations(remediations, receipts, findings, diffs)
    if remediations:
        _evaluate_verifiers(verifiers_raw, fixer_identities, diffs)


def _profile_identity(profile: dict[str, Any]) -> dict[str, Any]:
    """Validate profile identity, distinguishing malformed from incomplete.

    Malformed or absent identity raises, because a diff list implies the gate
    understood the denominator. Incompleteness is returned to the caller as a
    closure failure instead, since there the denominator IS understood and what
    it reports is partial coverage.
    """
    version = profile.get("profile_version")
    if type(version) is not int or version != PROFILE_VERSION:
        raise RecordError(f"application_audit.profile_version must equal {PROFILE_VERSION}")

    for field in REQUIRED_IDENTITY_FIELDS:
        value = profile.get(field)
        if not _is_text(value):
            raise RecordError(f"application_audit.{field} must be a non-empty string")

    identity = _require_object(profile.get("target_identity"), "target_identity")
    kind = identity.get("kind")
    if kind not in ("immutable_checkout", "content_manifest"):
        raise RecordError(
            "target_identity.kind must be immutable_checkout or content_manifest"
        )
    return identity


def _identity_is_complete(identity: dict[str, Any]) -> bool:
    """An immutable checkout needs its identity; a manifest needs full coverage."""
    if identity.get("kind") == "immutable_checkout":
        return _is_text(identity.get("checkout_identity"))
    if not _is_digest(identity.get("manifest_digest")):
        return False
    covered = _text_list(identity.get("coverage")) or []
    return all(required in covered for required in REQUIRED_MANIFEST_COVERAGE)


def _is_digest(value: object) -> bool:
    return isinstance(value, str) and re.fullmatch(r"[0-9a-f]{64}", value) is not None


def profile_fingerprint(profile: dict[str, Any]) -> str:
    """Bind the declared identity without trusting a producer's fingerprint."""
    keys = [field for field in REQUIRED_IDENTITY_FIELDS if field != "run_fingerprint"]
    identity = {key: profile.get(key) for key in [*keys, "profile_version", "target_identity"]}
    return hashlib.sha256(json.dumps(identity, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def _evaluate_application_audit(
    profile: dict[str, Any], diffs: dict[str, list[str]],
    observed_manifests: tuple[dict[str, Any], dict[str, Any]] | None = None,
) -> str:
    """Populate the profile diffs and return the evaluator-owned health value.

    `claimed_health` is read only to detect a disagreement. It never influences
    the returned value, because a producer that could set its own health would
    make every other check here decorative.
    """
    for name in APPLICATION_AUDIT_DIFF_NAMES:
        diffs[name] = []

    identity = _profile_identity(profile)
    run_id = profile["run_id"].strip()

    if not _identity_is_complete(identity):
        diffs["application_audit_identity_incomplete"].append(run_id)
    for field in ("routing_manifest_digest", "run_fingerprint", "target_root_fingerprint", "scope_fingerprint"):
        if not _is_digest(profile.get(field)):
            diffs["application_audit_identity_incomplete"].append(field)
    if profile["run_fingerprint"] != profile_fingerprint(profile):
        diffs["contradictory_or_duplicate_receipts"].append("run_fingerprint")

    # --- stages -----------------------------------------------------------
    stages = _index_records(_require_list(profile, "stages"), "stages")
    if not stages:
        diffs["stages_without_terminal_receipt"].append("required_baseline")
    seen_stage_keys: dict[tuple[str, str], str] = {}
    required_failed = False
    self_attested_required_run = False
    non_run_applicable = False

    for stage_id, stage in stages.items():
        if stage.get("run_id") != run_id or stage.get("run_fingerprint") != profile["run_fingerprint"]:
            diffs["stages_without_terminal_receipt"].append(stage_id)
        if stage.get("kind") not in ("local", "network", "cloud", "model"):
            diffs["stages_without_terminal_receipt"].append(stage_id)
        state = stage.get("state")
        if not isinstance(state, str) or state not in RECEIPT_STATES:
            diffs["stages_without_terminal_receipt"].append(stage_id)
            continue

        # A stage identity may appear once. Two receipts for one stage are two
        # claims the record itself says are both true, so picking a winner would
        # be an arbitrary choice between them.
        if not _is_text(stage.get("stage_identity")) or type(stage.get("required")) is not bool:
            diffs["stages_without_terminal_receipt"].append(stage_id)
            continue
        key = (stage["stage_identity"], state)
        identity_key = (key[0], "")
        if identity_key in seen_stage_keys:
            diffs["contradictory_or_duplicate_receipts"].append(stage_id)
        else:
            seen_stage_keys[identity_key] = stage_id

        required = stage["required"]
        provenance = stage.get("provenance")
        if not isinstance(provenance, str) or provenance not in PROVENANCE_ASSURANCES:
            diffs["stages_without_terminal_receipt"].append(stage_id)

        if state == "FAILED":
            required_failed = True
        if state in NON_RUN_APPLICABLE_STATES and required:
            non_run_applicable = True
        # Every execution assertion arriving in a record is self-attested.
        # Producer-written content_observed never certifies process execution.
        if state == "RAN" and required:
            self_attested_required_run = True
        if state != "RAN" and not _is_text(stage.get("reason_code")):
            # A terminal state says what happened; the reason code says why, and
            # a non-RAN state with no reason is unactionable.
            diffs["stages_without_terminal_receipt"].append(stage_id)

    # --- execution boundary ----------------------------------------------
    boundary = _require_object(profile.get("execution_boundary"), "execution_boundary")
    if type(boundary.get("authorized")) is not bool:
        raise RecordError("execution_boundary.authorized must be boolean")
    for field in ("outbound_destinations", "transmitted_data_classes"):
        if _text_list(boundary.get(field)) is None:
            raise RecordError("execution boundary lists must contain text")
    for field in ("boundary_status", "credential_source", "credential_privilege"):
        if not _is_text(boundary.get(field)):
            raise RecordError("execution boundary identity is incomplete")
    authorized = boundary["authorized"]
    boundary_contradiction = False
    if not authorized:
        for stage_id, stage in stages.items():
            if stage.get("kind") in ("network", "cloud", "model") and stage.get("state") == "RAN":
                # Claiming an outbound stage ran with no authorization is
                # contradictory evidence, not a degrade.
                diffs["contradictory_or_duplicate_receipts"].append(stage_id)
                boundary_contradiction = True

    # --- surfaces ---------------------------------------------------------
    supported = _text_list(profile.get("supported_surfaces")) or []
    if not supported or len(set(supported)) != len(supported):
        diffs["surfaces_without_positive_or_negative_evidence"].append("surface_inventory")
    surface_receipts = _require_list(profile, "surface_receipts")
    reported: dict[str, str] = {}
    for entry in surface_receipts:
        receipt = _require_object(entry, "surface_receipts entry")
        if receipt.get("run_fingerprint") != profile["run_fingerprint"]:
            diffs["surfaces_without_positive_or_negative_evidence"].append("receipt_binding")
        surface = receipt.get("surface")
        result = receipt.get("result")
        if not _is_text(surface):
            diffs["surfaces_without_positive_or_negative_evidence"].append("invalid_surface")
            continue
        name = surface.strip()
        if result not in ("matched", "negative_checked") or name not in supported or not _is_digest(receipt.get("evidence_digest")):
            diffs["surfaces_without_positive_or_negative_evidence"].append(name)
            continue
        if name in reported:
            diffs["contradictory_or_duplicate_receipts"].append(name)
        reported[name] = result
    for surface in supported:
        if surface not in reported:
            # Silent omission. "We did not look" and "we looked and found
            # nothing" are different results and must stay distinguishable.
            diffs["surfaces_without_positive_or_negative_evidence"].append(surface)

    # --- graph ------------------------------------------------------------
    graph_quality_degraded = False
    graph = _index_records(_require_list(profile, "graph_receipts"), "graph_receipts")
    if not graph:
        diffs["graph_receipts_without_qualified_identity"].append("missing_graph_receipt")
    for entry in graph.values():
        receipt = _require_object(entry, "graph_receipts entry")
        receipt_id = receipt.get("id") if _is_text(receipt.get("id")) else "<unnamed>"
        if receipt.get("run_fingerprint") != profile["run_fingerprint"]:
            diffs["graph_receipts_without_qualified_identity"].append(receipt_id)
        quality = receipt.get("quality")
        if not isinstance(quality, str) or quality not in GRAPH_QUALITIES:
            diffs["graph_receipts_without_qualified_identity"].append(receipt_id)
            continue
        if quality != "complete":
            graph_quality_degraded = True
        availability = receipt.get("availability")
        if not isinstance(availability, str) or availability not in RECEIPT_STATES:
            diffs["graph_receipts_without_qualified_identity"].append(receipt_id)
        elif availability != "RAN":
            graph_quality_degraded = True
            if quality != "unknown" or not _is_text(receipt.get("reason_code")):
                diffs["graph_receipts_without_qualified_identity"].append(receipt_id)
        if availability == "RAN" and (receipt.get("qualified") is not True or not _is_text(receipt.get("symbol"))):
            diffs["graph_receipts_without_qualified_identity"].append(receipt_id)
        if not _is_text(receipt.get("query_provenance")):
            diffs["graph_receipts_without_qualified_identity"].append(receipt_id)

    # --- artifacts --------------------------------------------------------
    artifacts_all_observed = True
    artifacts = _index_records(_require_list(profile, "observed_artifacts"), "observed_artifacts")
    if not artifacts:
        diffs["artifacts_without_bound_digest"].append("missing_artifact")
    for entry in artifacts.values():
        artifact = _require_object(entry, "observed_artifacts entry")
        artifact_id = artifact.get("id") if _is_text(artifact.get("id")) else "<unnamed>"
        if not _is_digest(artifact.get("digest")):
            diffs["artifacts_without_bound_digest"].append(artifact_id)
        if artifact.get("run_id") != run_id:
            # Cross-run substitution: a digest from another run proves nothing
            # about this one.
            diffs["artifacts_without_bound_digest"].append(artifact_id)
        if artifact.get("run_fingerprint") != profile["run_fingerprint"]:
            diffs["artifacts_without_bound_digest"].append(artifact_id)
        stage_id = artifact.get("stage_id")
        if not isinstance(stage_id, str) or stage_id not in stages:
            diffs["artifacts_without_bound_digest"].append(artifact_id)
        if not isinstance(artifact.get("provenance"), str) or artifact["provenance"] not in PROVENANCE_ASSURANCES:
            diffs["artifacts_without_bound_digest"].append(artifact_id)
        # The record alone supplies no evaluator-owned content observation.
        artifacts_all_observed = False

    # --- mutable target ---------------------------------------------------
    out_of_scope_change = False
    if identity.get("kind") == "content_manifest":
        revalidation = _require_object(
            profile.get("target_revalidation"), "target_revalidation"
        )
        before = revalidation.get("before_digest")
        after = revalidation.get("after_digest")
        if (not _is_digest(before) or not _is_digest(after)
                or before != identity.get("manifest_digest")
                or type(revalidation.get("changed")) is not bool
                or revalidation["changed"] != (before != after)):
            diffs["mutable_target_change_unproven"].append(run_id)
        elif before != after:
            # A boolean supplied by the producer proves no outside-scope change.
            # Verified manifest observations are required before this may degrade.
            if _outside_change_proven(profile, observed_manifests):
                out_of_scope_change = True
            else:
                diffs["mutable_target_change_unproven"].append(run_id)

    # --- approval ---------------------------------------------------------
    approval = profile.get("approval_receipt")
    if approval is not None:
        # This evaluator is read-only and has no host-controlled approval channel.
        # Even origin=trusted_host inside a record is input-supplied evidence.
        diffs["approval_receipts_without_trusted_origin"].append(run_id)
        receipt = _require_object(approval, "approval_receipt")
        origin = receipt.get("origin")
        if origin != "trusted_host":
            # A record that supplies its own permission slip is describing an
            # attack, not a workflow.
            diffs["approval_receipts_without_trusted_origin"].append(run_id)
        else:
            required_bindings = (
                "run_id",
                "proposed_patch_digest",
                "permitted_paths",
                "approver_identity",
                "expiry",
                "nonce",
                "patcher_identity",
            )
            for binding in required_bindings:
                if receipt.get(binding) in (None, "", [], {}):
                    # Trusted origin is necessary but not sufficient: an
                    # approval for one change authorizes nothing else.
                    diffs["approval_receipts_without_trusted_origin"].append(run_id)
                    break
            if receipt.get("run_id") != run_id or bool(receipt.get("revoked")):
                diffs["approval_receipts_without_trusted_origin"].append(run_id)

    # --- health -----------------------------------------------------------
    if required_failed or boundary_contradiction or any(diffs[name] for name in APPLICATION_AUDIT_DIFF_NAMES):
        health = "failed"
    else:
        degraded = (
            self_attested_required_run
            or non_run_applicable
            or graph_quality_degraded
            or not artifacts_all_observed
            or out_of_scope_change
            or not authorized
            or bool(diffs["application_audit_identity_incomplete"])
            or any(diffs[name] for name in APPLICATION_AUDIT_DIFF_NAMES)
        )
        health = "degraded" if degraded else "complete"

    claimed = profile.get("claimed_health")
    if claimed is not None and (not isinstance(claimed, str) or claimed not in HEALTH_VALUES):
        raise RecordError("claimed_health has an unsupported value")
    if claimed is not None and claimed != health:
        diffs["provenance_insufficient_for_claimed_health"].append(
            f"{run_id}:claimed={claimed}:computed={health}"
        )

    for name in APPLICATION_AUDIT_DIFF_NAMES:
        diffs[name] = sorted(set(diffs[name]))
    return health


def _outside_change_proven(
    profile: dict[str, Any], observed: tuple[dict[str, Any], dict[str, Any]] | None,
) -> bool:
    """Compare caller-supplied full manifests, never record-directed files.

    Content observations establish byte relations only; they do not attest the
    host execution. An unknown metadata change fails conservatively.
    """
    if observed is None or len(observed) != 2:
        return False
    import hashlib

    import _target_manifest

    scope = _text_list(profile.get("scope_paths"))
    bound = _text_list(profile.get("bound_input_paths"))
    if not scope or bound is None:
        return False
    expected_scope = hashlib.sha256(json.dumps(sorted(scope), separators=(",", ":")).encode()).hexdigest()
    if profile["scope_fingerprint"] != expected_scope:
        return False
    try:
        for path in [*scope, *bound]:
            _target_manifest.canonical_path_identity(Path(path))
        before, after = observed
        revalidation = profile["target_revalidation"]
        if (before.get("declared_scope") != [] or after.get("declared_scope") != []
                or before.get("target_root_fingerprint") != profile["target_root_fingerprint"]
                or after.get("target_root_fingerprint") != profile["target_root_fingerprint"]
                or before.get("excluded_directory_names") != after.get("excluded_directory_names")
                or before.get("budgets") != after.get("budgets")
                or before.get("git_classification") != after.get("git_classification")):
            return False
        for manifest, field in ((before, "before_digest"), (after, "after_digest")):
            if (_target_manifest.manifest_digest(manifest) != revalidation[field]
                    or manifest.get("manifest_digest") != revalidation[field]):
                return False
        mappings = []
        for manifest in observed:
            entries = {}
            for entry in manifest["entries"]:
                name = entry["path"]["display"]
                identity = _target_manifest.canonical_path_identity(Path(name))
                if entry["path"] != identity or name in entries:
                    return False
                entries[name] = entry
            mappings.append(entries)
        changed = {name for name in set(mappings[0]) | set(mappings[1])
                   if mappings[0].get(name) != mappings[1].get(name)}
        return bool(changed) and all(
            not (name == prefix or name.startswith(prefix.rstrip("/") + "/"))
            for name in changed for prefix in [*scope, *bound]
        ) and revalidation.get("reason_code") == "OUT_OF_SCOPE_CHANGE_PROVEN"
    except (KeyError, TypeError, ValueError):
        return False


def evaluate_review_record(
    raw_record: object, *,
    observed_manifests: tuple[dict[str, Any], dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Evaluate records without publishing input-controlled profile identifiers."""
    is_profile = isinstance(raw_record, dict) and "application_audit" in raw_record
    try:
        result = _evaluate_review_record(raw_record, observed_manifests=observed_manifests)
    except (RecordError, TypeError, KeyError, ValueError) as exc:
        if is_profile:
            raise RecordError("application_audit_malformed") from exc
        raise
    if is_profile:
        for name, values in result["diffs"].items():
            result["diffs"][name] = sorted("sha256:" + hashlib.sha256(value.encode("utf-8")).hexdigest()
                                           for value in values)
    return result


def _evaluate_review_record(
    raw_record: object, *,
    observed_manifests: tuple[dict[str, Any], dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Return the deterministic closure diff for a validated review record."""
    record = _require_object(raw_record, "review record")
    schema_version = record.get("schema_version")
    if (
        isinstance(schema_version, bool)
        or schema_version not in SUPPORTED_SCHEMA_VERSIONS
    ):
        raise RecordError("schema_version must equal 1 or 2")

    components = _index_records(_require_list(record, "components"), "components")
    actions = _index_records(_require_list(record, "review_actions"), "review_actions")
    findings = _index_records(_require_list(record, "findings"), "findings")
    facts = _index_records(_require_list(record, "facts"), "facts")
    claims = _index_records(_require_list(record, "report_claims"), "report_claims")

    diffs: dict[str, list[str]] = {name: [] for name in DIFF_NAMES}

    for component_id, component in components.items():
        if not _component_is_resolved(component, actions):
            diffs[DIFF_NAMES[0]].append(component_id)

    for finding_id, finding in findings.items():
        disposition = finding.get("disposition")
        disposition_is_resolved = (
            isinstance(disposition, str) and disposition in DISPOSITIONS
        )
        if disposition == "needs-live-validation":
            disposition_is_resolved = _live_validation_is_explicit(finding)
        if not disposition_is_resolved:
            diffs[DIFF_NAMES[1]].append(finding_id)

        if disposition == "confirmed":
            evidence_ids = _text_list(finding.get("evidence_fact_ids"))
            if not evidence_ids or any(
                not _fact_is_supported(facts.get(fact_id)) for fact_id in evidence_ids
            ):
                diffs[DIFF_NAMES[2]].append(finding_id)

        if disposition == "rejected" and not _rejection_is_complete(finding):
            diffs[DIFF_NAMES[3]].append(finding_id)

    for claim_id, claim in claims.items():
        fact_ids = _text_list(claim.get("fact_ids"))
        if not fact_ids or any(
            not _fact_is_supported(facts.get(fact_id)) for fact_id in fact_ids
        ):
            diffs[DIFF_NAMES[4]].append(claim_id)

    if schema_version == SCHEMA_VERSION_V2:
        _evaluate_schema_v2(record, findings, diffs)

    computed_health: str | None = None
    profile = record.get("application_audit")
    if "application_audit" in record:
        if schema_version != SCHEMA_VERSION_V2:
            raise RecordError("application_audit requires schema_version 2")
        try:
            computed_health = _evaluate_application_audit(
                _require_object(profile, "application_audit"), diffs, observed_manifests
            )
        except (RecordError, TypeError, KeyError, ValueError) as exc:
            raise RecordError("application_audit_malformed") from exc

    for item_ids in diffs.values():
        item_ids.sort()
    failure_count = sum(len(item_ids) for item_ids in diffs.values())
    result: dict[str, Any] = {
        "status": "failure" if failure_count else "clean",
        "failure_count": failure_count,
        "diffs": diffs,
    }
    if computed_health is not None:
        # Present ONLY for a profile record. Adding this key unconditionally
        # would change the output of every existing schema-v1 and schema-v2
        # record, which the profile is required not to do.
        result["computed_health"] = computed_health
    return result


def _load_record(path: Path) -> object:
    """Read one record through the strict decoder.

    `json.loads` keeps the LAST of duplicate object members silently, so a
    record carrying two `computed_health` values would parse as whichever came
    second and destroy the evidence that both were claimed. The strict decoder
    rejects that, along with non-finite numbers, trailing data, and unbounded
    size, nesting, and collection width, before any semantic check runs.
    """
    try:
        return _strict_json.load_path(path)
    except _strict_json.StrictJSONError as exc:
        raise RecordError(f"review record rejected ({exc.code}): {exc}") from exc


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Fail when a security review has unresolved claim-to-evidence diffs."
    )
    parser.add_argument(
        "record", type=Path, help="path to the local review-record JSON"
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        result = evaluate_review_record(_load_record(args.record))
    except RecordError as exc:
        print(
            json.dumps({"status": "usage-error", "error": str(exc)}, sort_keys=True),
            file=sys.stderr,
        )
        return EXIT_USAGE_ERROR

    print(json.dumps(result, indent=2, sort_keys=True))
    if result["failure_count"]:
        return EXIT_CLOSURE_FAILURE
    return EXIT_CLEAN


if __name__ == "__main__":
    raise SystemExit(main())
