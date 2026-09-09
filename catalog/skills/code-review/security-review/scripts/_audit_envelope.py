"""Pure normalization of validated application-audit records; no target reads."""
from __future__ import annotations

import hashlib
import json
import math
import os
import re
from datetime import datetime
from pathlib import Path

from _graph_receipt import BINDINGS, is_digest
from _graph_receipt import validate as validate_graph
from _target_manifest import canonical_path_identity

SCHEMA = "nexus.application-audit-envelope/v1"
DECODER = "nexus.strict-json/v1"
KINDS = {"sql-injection": "SQL injection", "os-command-injection": "OS command injection", "path-traversal": "Path traversal", "ssrf": "Server-side request forgery", "unsafe-deserialization": "Unsafe deserialization", "broken-object-authorization": "Broken object-level authorization", "insecure-session-cookie": "Insecure session cookie", "verbose-error-disclosure": "Verbose error disclosure"}
DISPOSITIONS = {"confirmed", "needs-live-validation", "corrected", "rejected"}
STATES = {"RAN", "NOT_APPLICABLE", "UNAVAILABLE", "FAILED", "DECLINED"}
SECRET_HINTS = ("TOKEN", "SECRET", "PASSWORD", "PASSWD", "APIKEY", "API_KEY", "CREDENTIAL")
INLINE_SECRET = re.compile(r"\b(?:gh[pousr]_[A-Za-z0-9]{16,}|sk-[A-Za-z0-9]{20,}|xox[baprs]-[A-Za-z0-9-]{10,})")


class EnvelopeError(ValueError):
    """Stable error code only; input-derived strings never enter diagnostics."""


def require(condition: bool, code: str = "AUDIT_ENVELOPE_INVALID") -> None:
    if not condition:
        raise EnvelopeError(code)


def digest(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def opaque(value: object) -> str:
    return "sha256:" + digest(value)


def is_opaque(value: object) -> bool:
    return isinstance(value, str) and value.startswith("sha256:") and is_digest(value[7:])


def redacted(text: str, secrets: list[str]) -> str:
    """Same longest-first value/token semantics as CI reporting, no CI import."""
    for value in sorted((v for v in secrets if v), key=len, reverse=True):
        text = text.replace(value, "[REDACTED]")
    return INLINE_SECRET.sub("[REDACTED]", text)


def environment_secrets() -> list[str]:
    return [v for k, v in os.environ.items() if len(v) >= 8 and any(h in k.upper() for h in SECRET_HINTS)]


def safe_path(value: object, secrets: list[str]) -> str:
    require(isinstance(value, str) and bool(value) and "\\" not in value)
    require(redacted(value, secrets) == value, "AUDIT_SENSITIVE_PATH")
    require(canonical_path_identity(Path(value))["display"] == value)
    require(not any(part in {".", ".."} for part in value.split("/")))
    return value


def text(value: object) -> str:
    require(isinstance(value, str) and 0 < len(value) <= 1024)
    return value


def index(items: object) -> dict:
    require(isinstance(items, list))
    result = {}
    for item in items:
        require(isinstance(item, dict))
        key = text(item.get("id"))
        require(key not in result, "AUDIT_DUPLICATE_ID")
        result[key] = item
    return result


def clock_fields(item: dict) -> dict:
    start, end = item.get("started_at"), item.get("finished_at")
    pattern = r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?Z"
    require(isinstance(start, str) and re.fullmatch(pattern, start) is not None)
    require(isinstance(end, str) and re.fullmatch(pattern, end) is not None)
    elapsed = (datetime.fromisoformat(end.replace("Z", "+00:00")) - datetime.fromisoformat(start.replace("Z", "+00:00"))).total_seconds() * 1000
    duration = item.get("duration_ms")
    require(type(duration) is int and 0 <= duration <= 86400000 and elapsed >= 0 and abs(elapsed - duration) < 1, "AUDIT_CLOCK_CONFLICT")
    return {"started_at": start, "finished_at": end, "duration_ms": duration}


def binding(profile: dict) -> dict:
    require(isinstance(profile, dict) and isinstance(profile.get("target_identity"), dict))
    result = {k: profile[k] for k in BINDINGS}
    result["target_manifest_digest"] = profile["target_identity"].get("manifest_digest", profile["target_identity"].get("checkout_identity"))
    require(is_digest(result["target_manifest_digest"]))
    require(isinstance(result["target_revision"], str) and re.fullmatch(r"(?:[0-9a-f]{40}|[0-9a-f]{64})", result["target_revision"]) is not None)
    return result


def validate_metadata(record: dict) -> dict:
    """Summary inputs must carry complete, cross-bound host metadata."""
    profile = record["application_audit"]
    expected = binding(profile)
    stages = index(profile["stages"])
    require(all(type(s.get("required")) is bool for s in stages.values()))
    artifacts = index(profile["observed_artifacts"])
    scanners = index(record["scanner_receipts"])
    graphs = index(profile["graph_receipts"])
    remediations = index(record["remediation_receipts"])
    verifiers = index(record["verifiers"])
    banks = (stages, scanners, graphs, artifacts, remediations, verifiers)
    require(len(set().union(*banks)) == sum(map(len, banks)), "AUDIT_DUPLICATE_ID")
    required = profile.get("required_stage_identities")
    require(isinstance(required, list) and all(isinstance(x, str) and x for x in required) and len(set(required)) == len(required))
    actual = {s.get("stage_identity") for s in stages.values() if s.get("required") is True}
    require(actual == set(required), "AUDIT_REQUIRED_STAGE_MISSING")
    for stage in [*stages.values(), *remediations.values(), *verifiers.values()]:
        require(stage.get("binding") == expected, "AUDIT_BINDING_MISMATCH")
        text(stage.get("tool_identity")); text(stage.get("tool_version")); text(stage.get("reason_code"))
        require(is_digest(stage.get("config_digest")))
        require(stage.get("state") in STATES)
        clock_fields(stage)
        refs = stage.get("artifact_ids")
        require(isinstance(refs, list) and len(set(refs)) == len(refs) and all(a in artifacts for a in refs))
        context = stage.get("execution_context")
        require(isinstance(context, dict) and set(context) == {"host_identity", "model_identity", "settings_digest", "boundary_status"})
        text(context["host_identity"]); text(context["model_identity"]); text(context["boundary_status"])
        require(is_digest(context["settings_digest"]))
    for scanner in scanners.values():
        require(isinstance(scanner.get("state"), str) and scanner["state"] in STATES)
        require(scanner.get("binding") == expected, "AUDIT_BINDING_MISMATCH")
        text(scanner.get("tool_version")); text(scanner.get("reason_code"))
        require(is_digest(scanner.get("config_digest")))
        if scanner.get("state") == "RAN":
            require(isinstance(scanner.get("target_scope"), dict))
            require(scanner.get("scanner_version") == scanner["tool_version"])
            require(scanner["config_digest"] == digest(scanner.get("config_fingerprint")))
            require(scanner.get("target_scope", {}).get("fingerprint") == profile["scope_fingerprint"], "AUDIT_BINDING_MISMATCH")
        clock_fields(scanner)
        require(isinstance(scanner.get("artifact_ids"), list) and all(a in artifacts for a in scanner["artifact_ids"]))
        require(isinstance(scanner.get("qualified_symbols", []), list) and all(is_opaque(s) for s in scanner.get("qualified_symbols", [])))
    for verifier in verifiers.values():
        text(verifier.get("identity"))
        require(type(verifier.get("read_only")) is bool)
    for graph in graphs.values():
        validate_graph(graph, profile)
    for artifact in artifacts.values():
        require(artifact.get("run_id") == profile["run_id"] and artifact.get("run_fingerprint") == profile["run_fingerprint"], "AUDIT_BINDING_MISMATCH")
        require(is_digest(artifact.get("digest")))
    for receipt in profile["surface_receipts"]:
        require(isinstance(receipt, dict))
        text(receipt.get("surface"))
        require(isinstance(receipt.get("result"), str) and receipt["result"] in {"matched", "negative_checked"})
        require(is_digest(receipt.get("evidence_digest")))
    return {**stages, **scanners, **graphs, **remediations, **verifiers}


def normalize_findings(record: dict, receipts: dict, secrets: list[str]) -> list:
    result = []
    path_keys = {}
    profile = record["application_audit"]
    qualified_ids = set(index(profile["graph_receipts"])) | set(index(record["scanner_receipts"]))
    for finding in index(record["findings"]).values():
        kind = finding.get("vulnerability_kind")
        if kind not in KINDS:
            rule = text(finding.get("rule_id"))
            require(re.fullmatch(r"[A-Za-z][A-Za-z0-9_.-]*:[A-Za-z0-9_.-]+", rule) is not None)
            kind = "custom:" + digest(rule)
        language = finding.get("language")
        require(language in {"python", "typescript", "javascript", "other", None})
        if profile.get("benchmark_scored") is True:
            require(language in {"python", "typescript"})
        severity = finding.get("severity")
        require(severity in {"critical", "high", "medium", "low", "info"})
        blocking = finding.get("release_blocking")
        require(type(blocking) is bool and (severity not in {"critical", "high"} or blocking))
        confidence = finding.get("confidence")
        require(type(confidence) in (int, float) and math.isfinite(confidence) and 0 <= confidence <= 1)
        disposition = finding.get("disposition")
        require(disposition in DISPOSITIONS)
        evidence = finding.get("evidence_receipt_ids")
        require(isinstance(evidence, list) and bool(evidence) and all(isinstance(e, str) and e in receipts for e in evidence) and len(set(evidence)) == len(evidence), "AUDIT_UNBOUND_FINDING")
        location = finding.get("location")
        require(isinstance(location, dict))
        if set(location) == {"locationless"}:
            require(location["locationless"] is True)
            normalized_location = {"locationless": True}
        else:
            require(set(location) == {"path", "start_line", "end_line"})
            path = safe_path(location["path"], secrets)
            start, end = location["start_line"], location["end_line"]
            require(type(start) is int and type(end) is int and 1 <= start <= end <= 10000000)
            key = canonical_path_identity(Path(path))["normalization_key"]
            require(key not in path_keys or path_keys[key] == path, "AUDIT_PATH_COLLISION")
            path_keys[key] = path
            normalized_location = {"path": path, "start_line": start, "end_line": end}
        normalized = {"id": opaque(finding["id"]), "rule_id": kind, "vulnerability_kind": kind, "language": language, "title": KINDS.get(kind, "Application security finding"), "severity": severity, "release_blocking": blocking, "confidence": confidence, "disposition": disposition, "location": normalized_location, "evidence_receipt_ids": sorted(opaque(e) for e in evidence), "properties": {}}
        if "source_to_sink" in finding:
            chain = finding["source_to_sink"]
            require(isinstance(chain, dict) and set(chain) == {"source", "sink"}, "AUDIT_UNBOUND_FLOW")
            normalized_chain = {}
            for endpoint, value in chain.items():
                require(isinstance(value, dict) and set(value) == {"symbol", "receipt_ids"} and is_opaque(value["symbol"]), "AUDIT_UNBOUND_FLOW")
                refs = value["receipt_ids"]
                require(isinstance(refs, list) and bool(refs) and len(set(refs)) == len(refs))
                for ref in refs:
                    require(ref in qualified_ids and ref in evidence, "AUDIT_UNBOUND_FLOW")
                    receipt = receipts[ref]
                    require(receipt.get("availability", receipt.get("state")) == "RAN", "AUDIT_UNBOUND_FLOW")
                    symbols = [v["symbol"] for v in receipt["locations"]] if ref in index(profile["graph_receipts"]) else receipt.get("qualified_symbols", [])
                    require(value["symbol"] in symbols, "AUDIT_UNBOUND_FLOW")
                normalized_chain[endpoint] = {"symbol": value["symbol"], "receipt_ids": sorted(opaque(ref) for ref in refs)}
            normalized["source_to_sink"] = normalized_chain
        if disposition == "corrected":
            matching = [m for m in record["remediation_receipts"] if finding["id"] in m.get("finding_ids", [])]
            require(bool(matching), "AUDIT_UNBOUND_CORRECTION")
            require(all(m.get("state") == "RAN" for m in matching), "AUDIT_UNBOUND_CORRECTION")
            fixers = {m["fixer_identity"].strip() for m in record["remediation_receipts"]}
            require(any(v["state"] == "RAN" and v["read_only"] is True and v["identity"].strip() not in fixers for v in record["verifiers"]), "AUDIT_UNBOUND_CORRECTION")
            for m in matching:
                before = receipts.get(m.get("before_receipt_id"), {})
                after = receipts.get(m.get("after_receipt_id"), {})
                require(before.get("state") == after.get("state") == "RAN", "AUDIT_UNBOUND_CORRECTION")
                require(before.get("tool_version") == after.get("tool_version"), "AUDIT_UNBOUND_CORRECTION")
                require(finding["id"] in before.get("observed_finding_ids", []) and finding["id"] not in after.get("observed_finding_ids", []), "AUDIT_UNBOUND_CORRECTION")
        result.append(normalized)
    return sorted(result, key=lambda f: f["id"])


def normalize(record: dict, evaluation: dict, observed: dict[str, str], secrets: list[str] | None = None) -> dict:
    """Build the sole downstream envelope from closure-owned health."""
    secrets = environment_secrets() if secrets is None else secrets
    profile = record["application_audit"]
    receipts = validate_metadata(record)
    normalized = []
    types = {r["id"]: kind for kind, bank in (("graph", profile["graph_receipts"]), ("scanner", record["scanner_receipts"]), ("host", profile["stages"]), ("remediation", record["remediation_receipts"]), ("verifier", record["verifiers"])) for r in bank}
    for receipt in sorted(receipts.values(), key=lambda r: r["id"]):
        graph = types[receipt["id"]] == "graph"
        item = {"id": opaque(receipt["id"]), "type": types[receipt["id"]], "state": receipt.get("availability") if graph else receipt.get("state"), "provenance": "self_attested", "source_digest": digest(receipt)}
        if graph:
            item.update({k: receipt[k] for k in ("operation", "symbol", "parameters_digest", "result_digest", "index_digest", "duration_ms", "ambiguity", "truncated", "quality", "locations", "result_count", "fallback", "reason_code")})
            for loc in item["locations"]:
                safe_path(loc["path"], secrets)
        else:
            item.update(clock_fields(receipt))
            item.update(owner_id=opaque(receipt.get("stage_identity", receipt.get("scanner_id", receipt.get("tool_identity")))), tool_id=opaque(receipt.get("tool_identity", receipt.get("scanner_id"))), version_id=opaque(receipt["tool_version"]), config_digest=receipt["config_digest"], reason_code="REASON_" + digest(receipt["reason_code"])[:24], artifact_ids=sorted(opaque(a) for a in receipt["artifact_ids"]), required=receipt["required"] if item["type"] == "host" else True, execution_context_digest=digest(receipt.get("execution_context", {})), qualified_symbols=receipt.get("qualified_symbols", []) if item["type"] == "scanner" else [])
            if item["type"] == "remediation":
                item.update(before_receipt_id=opaque(receipt["before_receipt_id"]), after_receipt_id=opaque(receipt["after_receipt_id"]), finding_ids=sorted(opaque(f) for f in receipt["finding_ids"]), fixer_id=opaque(receipt["fixer_identity"]))
            if item["type"] == "verifier":
                item.update(identity=opaque(receipt["identity"]), read_only=receipt["read_only"])
        normalized.append(item)
    artifacts = [{"id": opaque(a["id"]), "digest": a["digest"], "stage_id": opaque(a["stage_id"]), "provenance": "content_observed" if observed.get(a["id"]) == a["digest"] else "self_attested"} for a in profile["observed_artifacts"]]
    findings = normalize_findings(record, receipts, secrets)
    identity = binding(profile)
    revalidation = profile.get("target_revalidation", {}) if profile["target_identity"]["kind"] == "content_manifest" else {}
    envelope = {"schema": SCHEMA, "schema_version": 1, "decoder": DECODER, "evaluation_scope": profile.get("evaluation_scope", "host-audit"), "target": {"revision": profile["target_revision"], "root_fingerprint": profile["target_root_fingerprint"], "scope_fingerprint": profile["scope_fingerprint"], "content_manifest_before": identity["target_manifest_digest"], "content_manifest_after": revalidation.get("after_digest", identity["target_manifest_digest"]), "change_reason": "OUT_OF_SCOPE_CHANGE_PROVEN" if revalidation.get("changed") else "UNCHANGED"}, "routing_manifest_digest": profile["routing_manifest_digest"], "input_run_fingerprint": profile["run_fingerprint"], "run_id": opaque(profile["run_id"]), "computed_health": evaluation["computed_health"], "provenance": {"execution": "self_attested", "limitations": ["PROCESS_NOT_ATTESTED", "HOST_SETTINGS_SELF_ATTESTED", "RETRIES_NOT_ATTESTED", "ANSWER_ACCESS_NOT_ATTESTED"]}, "receipts": sorted(normalized, key=lambda r: r["id"]), "artifacts": sorted(artifacts, key=lambda a: a["id"]), "findings": findings, "disposition_counts": {d: sum(f["disposition"] == d for f in findings) for d in sorted(DISPOSITIONS)}, "graph_quality": sorted({g["quality"] for g in profile["graph_receipts"]}), "remediation": {"receipt_count": len(record["remediation_receipts"]), "closure_state": "failed" if any(evaluation["diffs"].get(k) for k in ("corrected_scanner_findings_without_equivalent_rescan", "mismatched_detector_config_or_scope", "unresolved_new_after_scan_findings", "fixer_is_sole_verifier")) else "closed" if record["remediation_receipts"] else "not-requested", "verifier_count": len(record["verifiers"]), "verifier_state": "self-attested" if record["verifiers"] else "not-requested"}, "reason_codes": sorted(k for k, v in evaluation["diffs"].items() if v)}
    envelope["evaluator"] = {"id": "closure-gate", "state": "complete", "provenance": "content_observed"}
    envelope["routing"] = {"surface_receipts": sorted(({"surface_id": opaque(r["surface"]), "result": r["result"], "evidence_digest": r["evidence_digest"]} for r in profile["surface_receipts"]), key=lambda r: r["surface_id"]), "required_stage_ids": sorted(opaque(s) for s in profile["required_stage_identities"])}
    reasons = set(envelope["reason_codes"])
    if normalized:
        reasons.add("SELF_ATTESTED_HOST_EXECUTION")
    if any(a["provenance"] != "content_observed" for a in artifacts):
        reasons.add("ARTIFACT_CONTENT_NOT_OBSERVED")
    if any(q != "complete" for q in envelope["graph_quality"]):
        reasons.add("GRAPH_QUALITY_DEGRADED")
    if revalidation.get("changed"):
        reasons.add("TARGET_OUTSIDE_SCOPE_CHANGED")
    for receipt in normalized:
        if receipt["state"] != "RAN":
            reasons.add("RECEIPT_" + receipt["state"])
    envelope["reason_codes"] = sorted(reasons)
    envelope["run_fingerprint"] = digest(envelope)
    # Values with no diagnostic role were projected to digests or fixed enums.
    # Reject surviving sensitive path/token text rather than alter its identity.
    encoded = json.dumps(envelope, sort_keys=True, ensure_ascii=True)
    require(redacted(encoded, secrets) == encoded, "AUDIT_OUTPUT_REDACTION_FAILED")
    return envelope
