#!/usr/bin/env python3
"""Serialize one validated application-audit envelope without source reads."""

from __future__ import annotations

import json
import sys
from urllib.parse import quote

import _audit_envelope as contract
import _normalized_audit
import _strict_json

LEVELS = {
    "critical": "error",
    "high": "error",
    "medium": "warning",
    "low": "note",
    "info": "note",
}


def emit(envelope: dict, secrets: list[str] | None = None) -> dict:
    """Preserve evaluator-owned values; emit only active alerts."""
    secrets = contract.environment_secrets() if secrets is None else secrets
    _normalized_audit.validate(envelope, secrets)
    active = sorted(
        (
            f
            for f in envelope["findings"]
            if f["disposition"] in {"confirmed", "needs-live-validation"}
        ),
        key=lambda f: (f["rule_id"], f["id"]),
    )
    rules = {
        f["rule_id"]: {"id": f["rule_id"], "shortDescription": {"text": f["title"]}}
        for f in active
    }
    rule_ids = sorted(rules)
    rule_indices = {key: i for i, key in enumerate(rule_ids)}
    results = []
    for finding in active:
        result = {
            "ruleId": finding["rule_id"],
            "ruleIndex": rule_indices[finding["rule_id"]],
            "level": LEVELS[finding["severity"]],
            "message": {"text": finding["title"]},
            "partialFingerprints": {"applicationFinding/v1": finding["id"]},
            "properties": {
                k: finding[k]
                for k in (
                    "severity",
                    "release_blocking",
                    "confidence",
                    "disposition",
                    "language",
                    "evidence_receipt_ids",
                )
            },
        }
        if "source_to_sink" in finding:
            result["properties"]["source_to_sink"] = finding["source_to_sink"]
        loc = finding["location"]
        if not loc.get("locationless"):
            result["locations"] = [
                {
                    "physicalLocation": {
                        "artifactLocation": {
                            "uri": "/".join(
                                quote(part, safe="") for part in loc["path"].split("/")
                            )
                        },
                        "region": {
                            "startLine": loc["start_line"],
                            "endLine": loc["end_line"],
                        },
                    }
                }
            ]
        results.append(result)
    properties = {k: v for k, v in envelope.items() if k != "findings"}
    properties["finding_ledger"] = [
        {k: f[k] for k in ("id", "rule_id", "disposition", "evidence_receipt_ids")}
        for f in sorted(envelope["findings"], key=lambda f: f["id"])
    ]
    output = {
        "version": "2.1.0",
        "$schema": "https://docs.oasis-open.org/sarif/sarif/v2.1.0/os/schemas/sarif-schema-2.1.0.json",
        "runs": [
            {
                "tool": {
                    "driver": {
                        "name": "nexus-application-security",
                        "rules": [rules[k] for k in rule_ids],
                    }
                },
                "results": results,
                "properties": properties,
            }
        ],
    }
    _normalized_audit.strings(output, secrets, max_length=12288)
    return output


def main() -> int:
    try:
        envelope = _strict_json.loads(sys.stdin.buffer.read(_strict_json.MAX_BYTES + 1))
        output = emit(envelope)
        encoded = json.dumps(output, indent=2, sort_keys=True, allow_nan=False) + "\n"
    except (ValueError, TypeError, KeyError, AttributeError, OSError):
        print('{"error":"application_sarif_invalid"}', file=sys.stderr)
        return 2
    sys.stdout.write(encoded)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
