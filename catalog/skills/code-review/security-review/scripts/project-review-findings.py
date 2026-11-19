#!/usr/bin/env python3
"""Project one validated application-audit envelope into generic review findings.

Reads the envelope on stdin and the independently supplied expected review
context from --expected-context. Opens no source or artifact path, runs no
command, and never recomputes health. See references/generic-review-projection.md.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import _audit_envelope as contract
import _normalized_audit
import _strict_json

SCHEMA = "nexus.generic-review-projection/v1"
SEVERITY = {"critical": "P0", "high": "P1", "medium": "P2", "low": "P3", "info": "P3"}
REVIEW_STATE = {
    "confirmed": "confirmed",
    "needs-live-validation": "pending",
    "corrected": "corrected",
    "rejected": "rejected",
}
UNAVAILABLE = (
    "proof_class",
    "reproducer",
    "environment",
    "duplicate_links",
    "expected_observed",
)
CONTEXT_REQUIRED = (
    "revision",
    "root_fingerprint",
    "scope_fingerprint",
    "input_run_fingerprint",
)
CONTEXT_OPTIONAL = ("run_id", "run_fingerprint", "routing_manifest_digest")


class ContextMismatch(ValueError):
    """The envelope belongs to a different review than the caller expects."""


def check_context(context: object) -> dict:
    """Validate the caller-supplied context shape; never derive it from input."""
    _normalized_audit.fields(context, " ".join(CONTEXT_REQUIRED), " ".join(CONTEXT_OPTIONAL))
    _normalized_audit.require(
        isinstance(context["revision"], str)
        and re.fullmatch(r"(?:[0-9a-f]{40}|[0-9a-f]{64})", context["revision"]) is not None
    )
    for key in CONTEXT_REQUIRED[1:] + ("run_fingerprint", "routing_manifest_digest"):
        if key in context:
            _normalized_audit.require(contract.is_digest(context[key]))
    if "run_id" in context:
        _normalized_audit.require(contract.is_opaque(context["run_id"]))
    return context


def submitted_bindings(envelope: dict) -> dict:
    target = envelope["target"]
    return {
        "revision": target["revision"],
        "root_fingerprint": target["root_fingerprint"],
        "scope_fingerprint": target["scope_fingerprint"],
        "input_run_fingerprint": envelope["input_run_fingerprint"],
        "run_id": envelope["run_id"],
        "run_fingerprint": envelope["run_fingerprint"],
        "routing_manifest_digest": envelope["routing_manifest_digest"],
    }


def bind(envelope: dict, context: dict | None) -> dict:
    """Compare every supplied binding; one miss refuses the whole projection."""
    submitted = submitted_bindings(envelope)
    if context is None:
        return {"state": "unbound", "checked": [], "submitted": submitted}
    for key, expected in context.items():
        if submitted[key] != expected:
            raise ContextMismatch(key)
    return {"state": "bound", "checked": sorted(context), "submitted": submitted}


def project_finding(finding: dict) -> dict:
    location = finding["location"]
    locationless = bool(location.get("locationless"))
    severity = SEVERITY[finding["severity"]]
    if finding["release_blocking"] and severity not in {"P0", "P1"}:
        severity = "P1"  # a release-blocking alert is never hidden below P1
    confidence = finding["confidence"]
    result = {
        "id": finding["id"],
        "fingerprint_key": "security:" + finding["id"],
        "persona": "security",
        "title": finding["title"],
        "severity": severity,
        "source_severity": finding["severity"],
        "release_blocking": finding["release_blocking"],
        "file": None if locationless else location["path"],
        "line": None if locationless else location["start_line"],
        "locationless": locationless,
        "source_confidence": confidence,
        "confidence_band": max(25, int(confidence * 4) * 25) if confidence < 1 else 100,
        "review_state": REVIEW_STATE[finding["disposition"]],
        "source_disposition": finding["disposition"],
        "requires_verification": finding["disposition"] == "needs-live-validation",
        "security": {
            "rule_id": finding["rule_id"],
            "vulnerability_kind": finding["vulnerability_kind"],
            "language": finding["language"],
            "evidence_receipt_ids": list(finding["evidence_receipt_ids"]),
            "unavailable": list(UNAVAILABLE),
        },
    }
    if not locationless:
        result["end_line"] = location["end_line"]
    if "source_to_sink" in finding:
        result["security"]["source_to_sink"] = finding["source_to_sink"]
    return result


def project(
    envelope: dict, context: dict | None = None, secrets: list[str] | None = None
) -> dict:
    secrets = contract.environment_secrets() if secrets is None else secrets
    _normalized_audit.validate(envelope, secrets)
    binding = bind(envelope, check_context(context) if context is not None else None)
    bound = binding["state"] == "bound"
    health = envelope["computed_health"]
    output = {
        "schema": SCHEMA,
        "schema_version": 1,
        "binding": binding,
        "claims": {
            "current_target_confirmation": bound,
            "complete_review": bound and health == "complete",
        },
        "source": {
            "schema": envelope["schema"],
            "computed_health": health,
            "evaluation_scope": envelope["evaluation_scope"],
            "evaluator": envelope["evaluator"],
            "provenance": envelope["provenance"],
            "reason_codes": envelope["reason_codes"],
            "graph_quality": envelope["graph_quality"],
            "remediation": envelope["remediation"],
            "routing": envelope["routing"],
            "disposition_counts": envelope["disposition_counts"],
            "target": envelope["target"],
        },
        "findings": [
            project_finding(f) for f in sorted(envelope["findings"], key=lambda f: f["id"])
        ],
    }
    _normalized_audit.strings(output, secrets, max_length=12288)
    return output


def parse_args(argv: list[str]) -> Path | None:
    if not argv:
        return None
    if len(argv) != 2 or argv[0] != "--expected-context":
        raise ValueError("usage")
    return Path(argv[1])


def main(argv: list[str] | None = None) -> int:
    try:
        context_path = parse_args(sys.argv[1:] if argv is None else argv)
        envelope = _strict_json.loads(sys.stdin.buffer.read(_strict_json.MAX_BYTES + 1))
        context = None if context_path is None else _strict_json.load_path(context_path)
        encoded = json.dumps(project(envelope, context), indent=2, sort_keys=True, allow_nan=False) + "\n"
    except ContextMismatch:
        print('{"error":"review_projection_context_mismatch"}', file=sys.stderr)
        return 2
    except (ValueError, TypeError, KeyError, AttributeError, OSError):
        print('{"error":"review_projection_invalid"}', file=sys.stderr)
        return 2
    sys.stdout.write(encoded)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
