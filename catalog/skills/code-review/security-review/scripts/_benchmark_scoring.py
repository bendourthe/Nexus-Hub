"""Pure deterministic scoring of normalized evidence, with no release verdict."""

from __future__ import annotations

import importlib.util
from dataclasses import dataclass
from pathlib import Path

import _audit_envelope as audit
import _benchmark_corpus as corpus
import _benchmark_protocol as protocol
import _normalized_audit as normalized

_spec = importlib.util.spec_from_file_location(
    "benchmark_sarif", Path(__file__).with_name("emit-sarif.py")
)
sarif_module = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(sarif_module)
TARGETS = {
    "seed_recall": 90,
    "blocking_recall": 100,
    "location_accuracy": 90,
    "blocking_location_accuracy": 100,
    "routing_coverage": 100,
    "required_stage_completeness": 100,
    "closure_completeness": 100,
    "artifact_consistency": 100,
    "benign_high_critical": 0,
}
VERSION = "nexus.application-audit-score/v1"
REJECTION_SCHEMA = "nexus.application-audit-rejected-input/v1"
REJECTIONS = {
    "NORMALIZED_ENVELOPE_REJECTED",
    "SARIF_DIVERGENCE",
    "STRICT_JSON_REJECTED",
    "UNVALIDATED_SARIF",
}


@dataclass(frozen=True)
class DecodeRejection:
    """In-memory decoder result; a caller JSON object cannot construct this."""

    input_kind: str
    input_digest: str


def supplied_digest(value: object, kind: str) -> str:
    if isinstance(value, DecodeRejection):
        protocol.require(
            value.input_kind == kind and audit.is_digest(value.input_digest)
        )
        return value.input_digest
    return protocol.bytes_digest(value)


def rejected(value: object, kind: str) -> bool:
    if not isinstance(value, dict) or value.get("schema") != REJECTION_SCHEMA:
        return False
    protocol.fields(value, "schema input_kind input_digest reason_code")
    protocol.require(
        value["input_kind"] == kind
        and audit.is_digest(value["input_digest"])
        and value["reason_code"] in REJECTIONS
    )
    protocol.require(
        value["reason_code"]
        in (
            {"NORMALIZED_ENVELOPE_REJECTED", "STRICT_JSON_REJECTED"}
            if kind == "envelope"
            else {"SARIF_DIVERGENCE", "STRICT_JSON_REJECTED", "UNVALIDATED_SARIF"}
        )
    )
    return True


def input_digest(value: object, kind: str) -> str:
    return (
        value["input_digest"] if rejected(value, kind) else protocol.bytes_digest(value)
    )


def rejection(value: object, kind: str, reason: str) -> dict:
    return {
        "schema": REJECTION_SCHEMA,
        "input_kind": kind,
        "input_digest": supplied_digest(value, kind),
        "reason_code": reason,
    }


def admit(envelope: dict, sarif: dict) -> tuple[dict, dict]:
    """Retain allowlisted normalized bytes or only a digest-bound rejection.

    Invalid raw values never enter the evidence tree. The rejection preserves
    input identity for deterministic invalidity replay, not the raw preimage.
    """
    if isinstance(envelope, DecodeRejection):
        return rejection(envelope, "envelope", "STRICT_JSON_REJECTED"), rejection(
            sarif, "sarif", "UNVALIDATED_SARIF"
        )
    try:
        normalized.validate(envelope)
    except (ValueError, TypeError, KeyError, IndexError, AttributeError):
        return rejection(
            envelope, "envelope", "NORMALIZED_ENVELOPE_REJECTED"
        ), rejection(sarif, "sarif", "UNVALIDATED_SARIF")
    if isinstance(sarif, DecodeRejection):
        return envelope, rejection(sarif, "sarif", "STRICT_JSON_REJECTED")
    if sarif != sarif_module.emit(envelope):
        return envelope, rejection(sarif, "sarif", "SARIF_DIVERGENCE")
    return envelope, sarif


def metric(
    numerator: int, denominator: int, target: int, *, maximum: bool = False
) -> dict:
    percent = numerator * 100 / denominator if denominator else None
    met = (
        numerator <= target
        if maximum
        else denominator > 0 and numerator * 100 >= target * denominator
    )
    return {
        "numerator": numerator,
        "denominator": denominator,
        "percent": percent,
        "target": target,
        "comparison": "maximum_count" if maximum else "minimum_percent",
        "state": "unscorable" if not denominator else "met" if met else "not_met",
    }


def unscorable(reason: str) -> dict:
    return {
        "schema": VERSION,
        "validity": "unscorable",
        "reason_codes": [reason],
        "metrics": {
            name: {"state": "unscorable", "target": target}
            for name, target in TARGETS.items()
        },
        "limitations": protocol.LIMITATIONS,
    }


def translated_paths(value: object, mapping: dict) -> None:
    """Every envelope path, including graph locations, must be a declared input."""
    if isinstance(value, dict):
        for key, child in value.items():
            if key == "path":
                protocol.require(
                    isinstance(child, str) and child in mapping,
                    "UNKNOWN_PROJECTED_PATH",
                )
            else:
                translated_paths(child, mapping)
    elif isinstance(value, list):
        for child in value:
            translated_paths(child, mapping)


def corrected(finding: dict, envelope: dict, receipts: dict) -> None:
    protocol.require(
        envelope["remediation"]["closure_state"] == "closed",
        "CORRECTED_CLOSURE_INVALID",
    )
    fixes = [
        r
        for r in receipts.values()
        if r["type"] == "remediation" and finding["id"] in r["finding_ids"]
    ]
    protocol.require(
        len(fixes) == 1 and fixes[0]["state"] == "RAN", "CORRECTED_CLOSURE_INVALID"
    )
    fix = fixes[0]
    before, after = (
        receipts[fix[k]] for k in ("before_receipt_id", "after_receipt_id")
    )
    protocol.require(
        before["type"] == after["type"] == "scanner"
        and before["state"] == after["state"] == "RAN"
        and all(
            before[k] == after[k]
            for k in ("tool_id", "owner_id", "version_id", "config_digest")
        )
        and before["id"] in finding["evidence_receipt_ids"],
        "CORRECTED_CLOSURE_INVALID",
    )
    protocol.require(
        any(
            r["type"] == "verifier"
            and r["state"] == "RAN"
            and r["read_only"]
            and r["identity"] != fix["fixer_id"]
            for r in receipts.values()
        ),
        "CORRECTED_CLOSURE_INVALID",
    )


def score(
    answers: dict,
    mapping: dict,
    plan: dict,
    subject_digest: str,
    terminal: dict,
    envelope: dict,
    sarif: dict,
    *,
    admitted: bool = False,
) -> dict:
    """Return valid metrics or an evaluator-derived invalidity, never accept metrics."""
    try:
        protocol.validate_plan(plan)
        corpus.validate_answers(answers)
        corpus.validate_map(mapping, answers, plan["candidate_id"])
        bind = protocol.validate_terminal(plan, terminal)
        protocol.require(
            subject_digest == plan["candidate_inputs"]["subject_manifest_digest"]
        )
        protocol.require(
            all(
                plan[k] == mapping[k]
                for k in (
                    "source_digest",
                    "answer_digest",
                    "projection_digest",
                    "map_digest",
                )
            )
        )
        for value, kind in ((envelope, "envelope"), (sarif, "sarif")):
            protocol.require(
                (
                    input_digest(value, kind)
                    if admitted
                    else protocol.bytes_digest(value)
                )
                == terminal[kind + "_digest"]
            )
            if admitted and rejected(value, kind):
                return unscorable(value["reason_code"])
        normalized.validate(envelope)
        protocol.require(sarif == sarif_module.emit(envelope), "SARIF_DIVERGENCE")
        protocol.require(
            terminal["state"] == "RAN" and terminal["code_search"] == "RAN",
            "REQUIRED_INDEX_UNAVAILABLE",
        )
        protocol.require(
            terminal["envelope_digest"] == protocol.bytes_digest(envelope)
            and terminal["sarif_digest"] == protocol.bytes_digest(sarif)
        )
        protocol.require(
            envelope["evaluation_scope"] == "host-audit"
            and envelope["input_run_fingerprint"]
            == terminal["producer_run_fingerprint"]
        )
        protocol.require(envelope["routing_manifest_digest"] == bind["routing_digest"])
        target = envelope["target"]
        protocol.require(
            target
            == {
                "revision": bind["revision"],
                "root_fingerprint": bind["root_fingerprint"],
                "scope_fingerprint": bind["scope_fingerprint"],
                "content_manifest_before": bind["content_manifest"],
                "content_manifest_after": bind["content_manifest"],
                "change_reason": "UNCHANGED",
            }
        )
        receipts = {r["id"]: r for r in envelope["receipts"]}
        protocol.require(
            all(
                r["execution_context_digest"]
                == audit.digest(protocol.producer_context(plan["context"]))
                for r in receipts.values()
                if r["type"] == "host"
            )
        )
        graph_receipts = [r for r in receipts.values() if r["type"] == "graph"]
        protocol.require(
            bool(graph_receipts) and any(r["state"] == "RAN" for r in graph_receipts),
            "REQUIRED_INDEX_UNAVAILABLE",
        )
        protocol.require(
            all(
                r["index_digest"] == bind["index_digest"]
                for r in graph_receipts
                if r["state"] == "RAN"
            )
        )
        paths = {e["projected_path"]: e for e in mapping["entries"]}
        translated_paths(envelope, paths)
        # Qualified symbols identify a module in the projection, without choosing
        # the expected vulnerable module. Location is evaluated only afterwards.
        symbols = {
            audit.opaque(Path(path).stem + "." + name): (path, name)
            for path in paths
            for name in ("receive", "handle")
        }
        eligible, benign_active = [], []
        for finding in envelope["findings"]:
            protocol.require(
                finding["language"] in {"python", "typescript"},
                "INVALID_BENCHMARK_LANGUAGE",
            )
            location = finding["location"]
            identity = paths.get(location.get("path"))
            if finding["disposition"] == "rejected":
                continue
            if finding["disposition"] == "corrected":
                corrected(finding, envelope, receipts)
            else:
                protocol.require(
                    any(
                        receipts[r]["state"] == "RAN"
                        for r in finding["evidence_receipt_ids"]
                    ),
                    "INCOMPLETE_FINDING",
                )
            if identity is not None and identity["role"] == "benign":
                if finding["disposition"] != "corrected" and finding["severity"] in {
                    "critical",
                    "high",
                }:
                    benign_active.append(finding)
                continue
            eligible.append(finding)
        matched, located, blocking_matched, blocking_located = 0, 0, 0, 0
        assigned = set()
        for seed in sorted(answers["seeds"], key=lambda s: s["id"]):
            candidates = []
            for finding in eligible:
                if (finding["vulnerability_kind"], finding["language"]) != (
                    seed["vulnerability_kind"],
                    seed["language"],
                ):
                    continue
                if seed["source_to_sink"] is not None:
                    chain = finding.get("source_to_sink")
                    if chain is None:
                        continue
                    source, sink = (
                        symbols.get(chain[k]["symbol"]) for k in ("source", "sink")
                    )
                    if (
                        source is None
                        or sink is None
                        or source[1] != "receive"
                        or sink[1] != "handle"
                        or source[0] != sink[0]
                        or paths[source[0]]["role"] == "benign"
                    ):
                        continue
                candidates.append(finding)
            protocol.require(len(candidates) <= 1, "AMBIGUOUS_OR_DUPLICATE_MATCH")
            if not candidates:
                continue
            finding = candidates[0]
            protocol.require(
                finding["id"] not in assigned, "AMBIGUOUS_OR_DUPLICATE_MATCH"
            )
            assigned.add(finding["id"])
            matched += 1
            blocking_matched += seed["release_blocking"]
            loc = finding["location"]
            identity = paths.get(loc.get("path"))
            correct_location = (
                identity is not None
                and identity["source_path"] == seed["path"]
                and loc["start_line"] <= seed["region"]["end_line"]
                and loc["end_line"] >= seed["region"]["start_line"]
            )
            located += bool(correct_location)
            blocking_located += bool(correct_location) and seed["release_blocking"]
        owners = plan["required_owners"]
        host = [r for r in receipts.values() if r["type"] == "host"]
        owner_count = sum(
            sum(
                r["owner_id"] == owner
                and r["required"]
                and r["state"] in protocol.TERMINAL
                for r in host
            )
            == 1
            for owner in owners
        )
        protocol.require(
            len({r["owner_id"] for r in host}) == len(host), "DUPLICATE_OWNER"
        )
        protocol.require(
            all(r["owner_id"] in owners for r in host if r["required"]),
            "UNDECLARED_REQUIRED_OWNER",
        )
        actual_surfaces = {
            r["surface_id"]: r for r in envelope["routing"]["surface_receipts"]
        }
        surface_count = sum(
            actual_surfaces.get(row["surface_id"]) == row
            for row in plan["routing_expectations"]
        )
        finalization = int(
            owner_count == len(owners)
            and envelope["remediation"]["closure_state"] != "failed"
        )
        count = len(envelope["findings"])
        metrics = {
            "seed_recall": metric(matched, 16, 90),
            "blocking_recall": metric(
                blocking_matched,
                sum(s["release_blocking"] for s in answers["seeds"]),
                100,
            ),
            "location_accuracy": metric(located, matched, 90),
            "blocking_location_accuracy": metric(
                blocking_located, blocking_matched, 100
            ),
            "routing_coverage": metric(
                surface_count + owner_count, 9 + len(owners), 100
            ),
            "required_stage_completeness": metric(owner_count, len(owners), 100),
            "closure_completeness": metric(count + finalization, count + 1, 100),
            "artifact_consistency": metric(
                len(protocol.RELATIONS), len(protocol.RELATIONS), 100
            ),
            "benign_high_critical": metric(len(benign_active), 16, 0, maximum=True),
        }
        return {
            "schema": VERSION,
            "validity": "valid",
            "reason_codes": [],
            "candidate_id": plan["candidate_id"],
            "attempt_id": terminal["attempt_id"],
            "mode": terminal["mode"],
            "workers": terminal["workers"],
            "metrics": metrics,
            "bindings": {
                "plan_digest": plan["plan_digest"],
                "terminal_digest": protocol.bytes_digest(terminal),
                "host_receipt_digest": audit.digest(terminal["receipt"]),
                "envelope_fingerprint": envelope["run_fingerprint"],
                "sarif_digest": protocol.bytes_digest(sarif),
                "subject_digest": subject_digest,
            },
            "computed_health": envelope["computed_health"],
            "graph_quality": envelope["graph_quality"],
            "code_search": terminal["code_search"],
            "limitations": protocol.LIMITATIONS,
        }
    except (ValueError, TypeError, KeyError, IndexError, AttributeError) as exc:
        known = {
            "SARIF_DIVERGENCE",
            "UNKNOWN_PROJECTED_PATH",
            "CORRECTED_CLOSURE_INVALID",
            "INCOMPLETE_FINDING",
            "AMBIGUOUS_OR_DUPLICATE_MATCH",
            "DUPLICATE_OWNER",
            "UNDECLARED_REQUIRED_OWNER",
            "REQUIRED_INDEX_UNAVAILABLE",
            "INVALID_BENCHMARK_LANGUAGE",
        }
        return unscorable(
            str(exc) if str(exc) in known else "INVALID_OR_CROSS_BOUND_INPUT"
        )
