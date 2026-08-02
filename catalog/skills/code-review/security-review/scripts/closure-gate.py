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
DISPOSITIONS = {
    "confirmed",
    "needs-live-validation",
    "corrected",
    "rejected",
}
REJECTION_RESULTS = {"observed-blocked", "observed-safe", "not-applicable"}
DIFF_NAMES = (
    "components_without_review_action_or_caveat",
    "findings_without_terminal_or_pending_disposition",
    "confirmed_findings_without_supporting_evidence",
    "rejected_findings_without_complete_rejection_record",
    "report_claims_without_matching_facts",
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


def evaluate_review_record(raw_record: object) -> dict[str, Any]:
    """Return the deterministic closure diff for a validated review record."""
    record = _require_object(raw_record, "review record")
    schema_version = record.get("schema_version")
    if isinstance(schema_version, bool) or schema_version != SCHEMA_VERSION:
        raise RecordError(f"schema_version must equal {SCHEMA_VERSION}")

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
