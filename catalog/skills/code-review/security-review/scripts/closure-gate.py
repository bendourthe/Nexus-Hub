#!/usr/bin/env python3
"""Fail a security review whose claims do not resolve to recorded evidence."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

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


def evaluate_review_record(raw_record: object) -> dict[str, Any]:
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

    for item_ids in diffs.values():
        item_ids.sort()
    failure_count = sum(len(item_ids) for item_ids in diffs.values())
    return {
        "status": "failure" if failure_count else "clean",
        "failure_count": failure_count,
        "diffs": diffs,
    }


def _load_record(path: Path) -> object:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise RecordError(f"cannot read review record: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise RecordError(f"review record is not valid JSON: {exc}") from exc


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
