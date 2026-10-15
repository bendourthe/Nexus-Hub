"""Pure metadata projection and validation for existing public graph responses."""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

from _target_manifest import canonical_path_identity

OPERATIONS = frozenset({"code_node", "code_callers", "code_callees", "code_impact", "code_context", "code_explore"})
REASONS = frozenset({"GRAPH_RETURNED", "GRAPH_NO_RESULT", "GRAPH_UNAVAILABLE", "GRAPH_FAILED", "GRAPH_TIMEOUT", "GRAPH_NOT_APPLICABLE", "GRAPH_PARTIAL", "GRAPH_AMBIGUOUS", "GRAPH_UNKNOWN", "GRAPH_DECLINED"})
BINDINGS = ("run_fingerprint", "target_root_fingerprint", "scope_fingerprint", "routing_manifest_digest", "target_revision")
FIELDS = frozenset({"id", "availability", "quality", "qualified", "symbol", "query_provenance", "operation", "parameters_digest", "result_digest", "index_digest", "duration_ms", "ambiguity", "truncated", "locations", "result_count", "reason_code", "fallback", *BINDINGS})


def digest(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def is_digest(value: object) -> bool:
    return isinstance(value, str) and re.fullmatch(r"[0-9a-f]{64}", value) is not None


def symbol_id(qualified_name: str) -> str:
    """Opaque qualified identity; source-controlled symbol text never emits."""
    return "sha256:" + digest(qualified_name)


def validate(receipt: dict, identity: dict) -> None:
    """Reject invalid metadata and mismatched bindings without echoing values."""
    def require(ok: bool) -> None:
        if not ok:
            raise ValueError("GRAPH_RECEIPT_INVALID")

    require(isinstance(receipt, dict) and set(receipt) == FIELDS)
    require(isinstance(receipt["id"], str) and re.fullmatch(r"[A-Za-z0-9_-]{1,80}", receipt["id"]) is not None)
    require(all(receipt[k] == identity.get(k) for k in BINDINGS))
    require(all(is_digest(receipt[k]) for k in BINDINGS if k != "target_revision"))
    require(isinstance(receipt["target_revision"], str) and re.fullmatch(r"[0-9a-f]{40,64}", receipt["target_revision"]) is not None)
    require(isinstance(receipt["operation"], str) and receipt["operation"] in OPERATIONS)
    require(receipt["query_provenance"] == "nexus-code-search/" + receipt["operation"])
    require(is_digest(receipt["parameters_digest"]))
    require(receipt["index_digest"] is None or is_digest(receipt["index_digest"]))
    require(receipt["result_digest"] is None or is_digest(receipt["result_digest"]))
    require(type(receipt["duration_ms"]) is int and 0 <= receipt["duration_ms"] <= 60000)
    require(type(receipt["result_count"]) is int and 0 <= receipt["result_count"] <= 100000)
    require(type(receipt["truncated"]) is bool and type(receipt["qualified"]) is bool)
    require(isinstance(receipt["symbol"], str) and receipt["symbol"].startswith("sha256:") and is_digest(receipt["symbol"][7:]))
    require(isinstance(receipt["availability"], str) and receipt["availability"] in {"RAN", "NOT_APPLICABLE", "UNAVAILABLE", "FAILED", "DECLINED"})
    require(isinstance(receipt["quality"], str) and receipt["quality"] in {"complete", "partial", "ambiguous", "unknown"})
    require(isinstance(receipt["ambiguity"], str) and receipt["ambiguity"] in {"none", "multiple", "unknown"})
    require(isinstance(receipt["reason_code"], str) and receipt["reason_code"] in REASONS)
    require(isinstance(receipt["fallback"], str) and receipt["fallback"] in {"none", "direct-corpus"})
    if receipt["availability"] == "RAN":
        require(receipt["qualified"] and is_digest(receipt["result_digest"]))
        require(receipt["result_count"] != 0 or not receipt["locations"])
        require(receipt["reason_code"] in {"GRAPH_RETURNED", "GRAPH_NO_RESULT", "GRAPH_PARTIAL", "GRAPH_AMBIGUOUS", "GRAPH_UNKNOWN"})
        if receipt["result_count"] > 1:
            require(receipt["ambiguity"] == "multiple")
        if receipt["ambiguity"] == "multiple":
            require(receipt["quality"] in {"ambiguous", "partial"})
        if receipt["quality"] == "ambiguous":
            require(receipt["ambiguity"] == "multiple" and receipt["reason_code"] == "GRAPH_AMBIGUOUS")
        if receipt["truncated"]:
            require(receipt["quality"] == "partial" and receipt["reason_code"] == "GRAPH_PARTIAL")
        if receipt["result_count"] == 0 and not receipt["truncated"]:
            require(receipt["reason_code"] == "GRAPH_NO_RESULT" and receipt["quality"] == "unknown")
        if receipt["reason_code"] == "GRAPH_NO_RESULT":
            require(receipt["result_count"] == 0)
        if receipt["reason_code"] == "GRAPH_PARTIAL":
            require(receipt["quality"] == "partial")
        if receipt["reason_code"] == "GRAPH_AMBIGUOUS":
            require(receipt["quality"] == "ambiguous")
        if receipt["reason_code"] == "GRAPH_UNKNOWN":
            require(receipt["quality"] == "unknown")
    else:
        require(receipt["quality"] == "unknown" and receipt["result_digest"] is None and not receipt["locations"] and receipt["result_count"] == 0)
        expected = {"NOT_APPLICABLE": {"GRAPH_NOT_APPLICABLE"}, "UNAVAILABLE": {"GRAPH_UNAVAILABLE", "GRAPH_TIMEOUT"}, "FAILED": {"GRAPH_FAILED"}, "DECLINED": {"GRAPH_DECLINED"}}
        require(receipt["reason_code"] in expected[receipt["availability"]])
    if receipt["quality"] == "complete":
        require(not receipt["truncated"] and receipt["ambiguity"] == "none" and receipt["fallback"] == "none" and is_digest(receipt["index_digest"]))
    require(isinstance(receipt["locations"], list) and len(receipt["locations"]) <= 100)
    seen = set()
    for loc in receipt["locations"]:
        require(isinstance(loc, dict) and set(loc) == {"path", "symbol", "start_line", "end_line"})
        require(isinstance(loc["path"], str) and "\\" not in loc["path"])
        require(canonical_path_identity(Path(loc["path"]))["display"] == loc["path"])
        require(isinstance(loc["symbol"], str) and loc["symbol"].startswith("sha256:") and is_digest(loc["symbol"][7:]))
        require(type(loc["start_line"]) is int and type(loc["end_line"]) is int and 1 <= loc["start_line"] <= loc["end_line"] <= 10000000)
        key = (loc["path"], loc["symbol"], loc["start_line"], loc["end_line"])
        require(key not in seen)
        seen.add(key)


def project(raw: dict, *, operation: str, qualified_symbol: str, parameters: dict, identity: dict, receipt_id: str, duration_ms: int, index_digest: str | None = None, limit: int = 100) -> dict:
    """Project a bounded caller-observed result; never claim graph freshness."""
    if not isinstance(raw, dict) or operation not in OPERATIONS or type(limit) is not int or not 1 <= limit <= 100 or not isinstance(qualified_symbol, str) or not qualified_symbol.strip():
        raise ValueError("GRAPH_RECEIPT_INVALID")
    result = {k: identity[k] for k in BINDINGS}
    result.update(id=receipt_id, operation=operation, query_provenance="nexus-code-search/" + operation, availability="RAN", quality="unknown", qualified=True, symbol=symbol_id(qualified_symbol), parameters_digest=digest(parameters), result_digest=digest(raw), index_digest=index_digest, duration_ms=duration_ms, ambiguity="none", truncated=False, locations=[], result_count=0, reason_code="GRAPH_UNKNOWN", fallback="none")
    if raw.get("error"):
        result.update(availability="FAILED", quality="unknown", result_digest=None, reason_code="GRAPH_FAILED")
        validate(result, identity)
        return result
    matches = raw.get("matches", 0)
    count = len(matches) if isinstance(matches, list) else matches
    if type(count) is not int or not 0 <= count <= 100000:
        raise ValueError("GRAPH_RECEIPT_INVALID")
    result["result_count"] = count
    if count > 1:
        result.update(ambiguity="multiple", quality="ambiguous", reason_code="GRAPH_AMBIGUOUS")
    elif count == 0:
        result["reason_code"] = "GRAPH_NO_RESULT"
    stack = [(raw, 0)]
    seen = set()
    visited = 0
    while stack:
        item, depth = stack.pop()
        visited += 1
        if visited > 10000 or depth > 32:
            result["truncated"] = True
            break
        if isinstance(item, dict):
            if "qualified_name" in item and "file_path" in item:
                path = item["file_path"]
                if not isinstance(path, str) or "\\" in path or not isinstance(item["qualified_name"], str):
                    raise ValueError("GRAPH_RECEIPT_INVALID")
                canonical_path_identity(Path(path))
                loc = {"path": path, "symbol": symbol_id(item["qualified_name"]), "start_line": item.get("start_line"), "end_line": item.get("end_line")}
                key = digest(loc)
                if key not in seen:
                    seen.add(key)
                    if len(result["locations"]) < limit:
                        result["locations"].append(loc)
                    else:
                        result["truncated"] = True
            # Descend through structural graph containers only. Scalar source
            # fields and arbitrary nested properties are never projected.
            stack.extend((v, depth + 1) for k, v in item.items() if k in {"matches", "results", "node", "target", "caller", "callee", "callers", "callees", "siblings", "impact"} and isinstance(v, (list, dict)))
        elif isinstance(item, list):
            stack.extend((v, depth + 1) for v in item[:10001])
            if len(item) > 10001:
                result["truncated"] = True
    if result["truncated"]:
        result.update(quality="partial", reason_code="GRAPH_PARTIAL")
    result["locations"].sort(key=lambda v: (v["path"], v["symbol"], v["start_line"]))
    validate(result, identity)
    return result
