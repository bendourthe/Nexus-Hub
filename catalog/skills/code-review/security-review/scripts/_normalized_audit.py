"""Strict, read-free schema validation shared by normalized audit consumers."""

from __future__ import annotations

import math
import re
import unicodedata
from pathlib import Path, PureWindowsPath

import _audit_envelope as contract
import _graph_receipt as graph


def require(condition: bool) -> None:
    if not condition:
        raise ValueError("NORMALIZED_AUDIT_INVALID")


def fields(value: object, required: str, optional: str = "") -> None:
    require(isinstance(value, dict))
    require(
        set(required.split()) <= set(value) <= set((required + " " + optional).split())
    )


def choice(value: object, choices: str) -> None:
    require(isinstance(value, str) and value in choices.split())


def strings(value: object, secrets: list[str], max_length: int = 1024) -> None:
    """Bounded decoder owns recursion limits; check every string, including keys."""
    if isinstance(value, str):
        require(len(value) <= max_length and contract.redacted(value, secrets) == value)
        require(all(unicodedata.category(c) not in {"Cc", "Cf", "Cs"} for c in value))
    elif isinstance(value, dict):
        for key, item in value.items():
            strings(key, secrets, max_length)
            strings(item, secrets, max_length)
    elif isinstance(value, list):
        for item in value:
            strings(item, secrets, max_length)
    else:
        require(value is None or type(value) in {int, float, bool})
        if type(value) is float:
            require(math.isfinite(value))


def ids(items: object) -> dict:
    result = contract.index(items)
    require(all(contract.is_opaque(key) for key in result))
    return result


def refs(value: object, bank: dict, *, nonempty: bool = False) -> None:
    require(isinstance(value, list) and (bool(value) or not nonempty))
    require(
        all(isinstance(v, str) and v in bank for v in value)
        and len(set(value)) == len(value)
    )


def path(value: object, seen: dict, secrets: list[str]) -> str:
    require(isinstance(value, str) and 0 < len(value) <= 1024 and "%" not in value)
    require(unicodedata.normalize("NFC", value) == value)
    require(not any(PureWindowsPath(part).is_reserved() for part in value.split("/")))
    contract.safe_path(value, secrets)
    key = contract.canonical_path_identity(Path(value))["normalization_key"]
    require(key not in seen or seen[key] == value)
    seen[key] = value
    return value


def location(value: object, seen: dict, secrets: list[str]) -> None:
    require(isinstance(value, dict))
    if set(value) == {"locationless"}:
        require(value["locationless"] is True)
    else:
        fields(value, "path start_line end_line")
        path(value["path"], seen, secrets)
        require(
            type(value["start_line"]) is int
            and type(value["end_line"]) is int
            and 1 <= value["start_line"] <= value["end_line"] <= 10000000
        )


def validate(value: dict, secrets: list[str] | None = None) -> dict:
    """Validate the unsigned envelope's integrity, never recompute its health."""
    secrets = contract.environment_secrets() if secrets is None else secrets
    strings(value, secrets)
    fields(
        value,
        "schema schema_version decoder evaluation_scope target routing_manifest_digest input_run_fingerprint run_id computed_health provenance receipts artifacts findings disposition_counts graph_quality remediation reason_codes evaluator routing run_fingerprint",
    )
    require(
        value["schema"] == contract.SCHEMA
        and type(value["schema_version"]) is int
        and value["schema_version"] == 1
        and value["decoder"] == contract.DECODER
    )
    require(
        value["run_fingerprint"]
        == contract.digest({k: v for k, v in value.items() if k != "run_fingerprint"})
    )
    require(contract.is_opaque(value["run_id"]))
    require(
        all(
            contract.is_digest(value[k])
            for k in (
                "run_fingerprint",
                "input_run_fingerprint",
                "routing_manifest_digest",
            )
        )
    )
    choice(value["computed_health"], "complete degraded failed")
    choice(value["evaluation_scope"], "host-audit deterministic-local")
    target = value["target"]
    fields(
        target,
        "revision root_fingerprint scope_fingerprint content_manifest_before content_manifest_after change_reason",
    )
    require(
        isinstance(target["revision"], str)
        and re.fullmatch(r"(?:[0-9a-f]{40}|[0-9a-f]{64})", target["revision"])
        is not None
    )
    require(
        all(
            contract.is_digest(target[k])
            for k in (
                "root_fingerprint",
                "scope_fingerprint",
                "content_manifest_before",
                "content_manifest_after",
            )
        )
    )
    choice(target["change_reason"], "UNCHANGED OUT_OF_SCOPE_CHANGE_PROVEN")
    require(
        value["provenance"]
        == {
            "execution": "self_attested",
            "limitations": [
                "PROCESS_NOT_ATTESTED",
                "HOST_SETTINGS_SELF_ATTESTED",
                "RETRIES_NOT_ATTESTED",
                "ANSWER_ACCESS_NOT_ATTESTED",
            ],
        }
    )
    require(
        value["evaluator"]
        == {"id": "closure-gate", "state": "complete", "provenance": "content_observed"}
    )
    artifacts, receipts, findings = (
        ids(value["artifacts"]),
        ids(value["receipts"]),
        ids(value["findings"]),
    )
    require(
        len(set(artifacts) | set(receipts) | set(findings))
        == len(artifacts) + len(receipts) + len(findings)
    )
    for item in artifacts.values():
        fields(item, "id digest stage_id provenance")
        require(
            contract.is_digest(item["digest"]) and contract.is_opaque(item["stage_id"])
        )
        require(
            item["stage_id"] in receipts
            or value["evaluation_scope"] == "deterministic-local"
            and item["stage_id"] == contract.opaque("closure-gate/evaluate")
        )
        choice(item["provenance"], "content_observed self_attested")
    seen = {}
    for receipt in receipts.values():
        choice(receipt.get("type"), "host scanner graph remediation verifier")
        choice(receipt.get("state"), "RAN NOT_APPLICABLE UNAVAILABLE FAILED DECLINED")
        require(
            receipt.get("provenance") == "self_attested"
            and contract.is_digest(receipt.get("source_digest"))
        )
        common = "id type state provenance source_digest"
        if receipt["type"] == "graph":
            fields(
                receipt,
                common
                + " operation symbol parameters_digest result_digest index_digest duration_ms ambiguity truncated quality locations result_count fallback reason_code",
            )
            identity = {
                "run_fingerprint": value["input_run_fingerprint"],
                "target_root_fingerprint": target["root_fingerprint"],
                "scope_fingerprint": target["scope_fingerprint"],
                "routing_manifest_digest": value["routing_manifest_digest"],
                "target_revision": target["revision"],
            }
            raw = {k: v for k, v in receipt.items() if k not in common.split()}
            raw.update(
                identity,
                id="normalized",
                availability=receipt["state"],
                qualified=True,
                query_provenance="nexus-code-search/" + receipt["operation"],
            )
            graph.validate(raw, identity)
            for loc in receipt["locations"]:
                path(loc["path"], seen, secrets)
        else:
            extra = (
                "before_receipt_id after_receipt_id finding_ids fixer_id"
                if receipt["type"] == "remediation"
                else "identity read_only"
                if receipt["type"] == "verifier"
                else ""
            )
            fields(
                receipt,
                common
                + " started_at finished_at duration_ms owner_id tool_id version_id config_digest reason_code artifact_ids required execution_context_digest qualified_symbols "
                + extra,
            )
            contract.clock_fields(receipt)
            require(
                all(
                    contract.is_opaque(receipt[k])
                    for k in ("owner_id", "tool_id", "version_id")
                )
            )
            require(
                all(
                    contract.is_digest(receipt[k])
                    for k in ("config_digest", "execution_context_digest")
                )
            )
            require(
                re.fullmatch(r"REASON_[0-9a-f]{24}", receipt["reason_code"]) is not None
                and type(receipt["required"]) is bool
            )
            refs(receipt["artifact_ids"], artifacts)
            require(
                isinstance(receipt["qualified_symbols"], list)
                and all(contract.is_opaque(s) for s in receipt["qualified_symbols"])
            )
            require(receipt["type"] == "scanner" or not receipt["qualified_symbols"])
            if receipt["type"] == "remediation":
                refs(
                    [receipt["before_receipt_id"], receipt["after_receipt_id"]],
                    receipts,
                    nonempty=True,
                )
                refs(receipt["finding_ids"], findings, nonempty=True)
                require(contract.is_opaque(receipt["fixer_id"]))
            if receipt["type"] == "verifier":
                require(
                    contract.is_opaque(receipt["identity"])
                    and type(receipt["read_only"]) is bool
                )
    rules = {}
    for finding in findings.values():
        fields(
            finding,
            "id rule_id vulnerability_kind language title severity release_blocking confidence disposition location evidence_receipt_ids properties",
            "source_to_sink",
        )
        rule = finding["rule_id"]
        require(
            isinstance(rule, str)
            and (
                rule in contract.KINDS
                or re.fullmatch(r"custom:[0-9a-f]{64}", rule) is not None
            )
        )
        require(
            finding["vulnerability_kind"] == rule
            and finding["title"]
            == contract.KINDS.get(rule, "Application security finding")
        )
        require(rule not in rules or rules[rule] == finding["title"])
        rules[rule] = finding["title"]
        require(
            finding["language"] is None
            or finding["language"] in {"python", "typescript", "javascript", "other"}
        )
        choice(finding["severity"], "critical high medium low info")
        require(
            type(finding["release_blocking"]) is bool
            and (
                finding["severity"] not in {"critical", "high"}
                or finding["release_blocking"]
            )
        )
        require(
            type(finding["confidence"]) in {int, float}
            and 0 <= finding["confidence"] <= 1
        )
        choice(
            finding["disposition"], "confirmed needs-live-validation corrected rejected"
        )
        require(finding["properties"] == {})
        location(finding["location"], seen, secrets)
        refs(finding["evidence_receipt_ids"], receipts, nonempty=True)
        if "source_to_sink" in finding:
            fields(finding["source_to_sink"], "source sink")
            for endpoint in finding["source_to_sink"].values():
                fields(endpoint, "symbol receipt_ids")
                require(contract.is_opaque(endpoint["symbol"]))
                refs(endpoint["receipt_ids"], receipts, nonempty=True)
                for ref in endpoint["receipt_ids"]:
                    receipt = receipts[ref]
                    require(
                        ref in finding["evidence_receipt_ids"]
                        and receipt["state"] == "RAN"
                        and receipt["type"] in {"graph", "scanner"}
                    )
                    symbols = (
                        [loc["symbol"] for loc in receipt["locations"]]
                        if receipt["type"] == "graph"
                        else receipt["qualified_symbols"]
                    )
                    require(endpoint["symbol"] in symbols)
    require(
        value["disposition_counts"]
        == {
            d: sum(f["disposition"] == d for f in findings.values())
            for d in contract.DISPOSITIONS
        }
    )
    require(all(type(n) is int for n in value["disposition_counts"].values()))
    require(
        value["graph_quality"]
        == sorted({r["quality"] for r in receipts.values() if r["type"] == "graph"})
    )
    fields(
        value["remediation"],
        "receipt_count closure_state verifier_count verifier_state",
    )
    for field, kind in (
        ("receipt_count", "remediation"),
        ("verifier_count", "verifier"),
    ):
        require(
            type(value["remediation"][field]) is int
            and value["remediation"][field]
            == sum(r["type"] == kind for r in receipts.values())
        )
    choice(value["remediation"]["closure_state"], "failed closed not-requested")
    choice(value["remediation"]["verifier_state"], "self-attested not-requested")
    require(
        isinstance(value["reason_codes"], list)
        and all(
            isinstance(s, str) and re.fullmatch(r"[A-Za-z_]{1,128}", s)
            for s in value["reason_codes"]
        )
    )
    fields(value["routing"], "surface_receipts required_stage_ids")
    require(isinstance(value["routing"]["surface_receipts"], list))
    surfaces = []
    for surface in value["routing"]["surface_receipts"]:
        fields(surface, "surface_id result evidence_digest")
        require(
            contract.is_opaque(surface["surface_id"])
            and contract.is_digest(surface["evidence_digest"])
        )
        choice(surface["result"], "matched negative_checked")
        surfaces.append(surface["surface_id"])
    require(len(set(surfaces)) == len(surfaces))
    require(
        value["routing"]["required_stage_ids"]
        == sorted(
            r["owner_id"]
            for r in receipts.values()
            if r["type"] == "host" and r["required"]
        )
    )
    return value
