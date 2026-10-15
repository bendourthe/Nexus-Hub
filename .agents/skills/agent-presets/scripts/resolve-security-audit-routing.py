#!/usr/bin/env python3
"""Pure security-audit routing policy; input receipts never execute anything."""
from __future__ import annotations

import argparse
import fnmatch
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any

_HERE = Path(__file__).resolve().parent
sys.dont_write_bytecode = True
_PEERS = (_HERE.parents[2] / "code-review/security-review/scripts",
          _HERE.parents[1] / "security-review/scripts")
for _peer in _PEERS:
    if (_peer / "_strict_json.py").is_file():
        sys.path.insert(0, str(_peer))
        break
else:
    raise ImportError("required security-review bundle unavailable")

import _strict_json as strict
import _target_manifest as target_identity

SURFACES = {"application", "authentication", "api", "advanced-web", "dependency",
            "cryptography", "business-logic", "cloud-iac", "ai-agent"}
REASONS = {"INVENTORY_TRUNCATED", "UNSUPPORTED_FILETYPE", "UNCLASSIFIED_FILETYPE",
           "UNSAFE_ARTIFACT", "INVENTORY_CHANGED", "INVENTORY_INVALID", "UNSUPPORTED_SURFACE"}
_HEX = re.compile(r"^[0-9a-f]{64}$")
_NAME = re.compile(r"^[a-z][a-z0-9-]{0,95}$")


class RoutingError(ValueError):
    """A stable policy failure that never contains input text."""


def digest(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()).hexdigest()


def _require(condition: bool) -> None:
    if not condition:
        raise RoutingError("INVENTORY_INVALID")


def validate_manifest(value: Any) -> dict[str, Any]:
    """Validate policy data without importing code or consulting the target."""
    _require(isinstance(value, dict))
    _require(set(value) == {"schema_version", "concurrency_cap", "fixed_stages", "surfaces", "files", "budgets", "reason_codes"})
    _require(type(value["schema_version"]) is int and value["schema_version"] == 1)
    _require(type(value["concurrency_cap"]) is int and value["concurrency_cap"] == 4)
    _require(value["fixed_stages"] == ["security-review", "security-patch-advisor", "testing-review", "adversarial-verifier"])
    _require(set(value["reason_codes"]) == REASONS)
    _require(isinstance(value["surfaces"], list) and len(value["surfaces"]) == 9)
    ids, owners, priorities, predicates = set(), set(), set(), set()
    for surface in value["surfaces"]:
        _require(isinstance(surface, dict) and set(surface) == {"id", "owner", "priority", "predicates", "handoffs"})
        name, owner, priority = surface["id"], surface["owner"], surface["priority"]
        _require(isinstance(name, str))
        if name not in SURFACES:
            raise RoutingError("UNSUPPORTED_SURFACE")
        _require(name not in ids)
        _require(isinstance(owner, str) and bool(_NAME.fullmatch(owner)) and owner not in owners)
        _require(owner not in value["fixed_stages"][1:])
        _require(type(priority) is int and -1 <= priority <= 7 and priority not in priorities)
        ids.add(name)
        owners.add(owner)
        priorities.add(priority)
        _require(isinstance(surface["predicates"], list) and bool(surface["predicates"]))
        for predicate in surface["predicates"]:
            _require(isinstance(predicate, dict) and set(predicate) == {"id", "operation", "values"})
            _require(isinstance(predicate["id"], str) and bool(_NAME.fullmatch(predicate["id"])) and predicate["id"] not in predicates)
            predicates.add(predicate["id"])
            _require(predicate["operation"] in ("filename", "token", "source"))
            _require(isinstance(predicate["values"], list) and len(predicate["values"]) <= 64)
            _require(all(isinstance(item, str) and 0 < len(item) <= 80 for item in predicate["values"]))
            _require(bool(predicate["values"]) == (predicate["operation"] != "source"))
        _require(isinstance(surface["handoffs"], list))
        for handoff in surface["handoffs"]:
            _require(isinstance(handoff, dict) and set(handoff) == {"owner", "predicate", "gate"})
            _require(isinstance(handoff["owner"], str) and bool(_NAME.fullmatch(handoff["owner"])))
            _require(handoff["owner"] not in value["fixed_stages"])
            _require(handoff["predicate"] in {p["id"] for p in surface["predicates"]} or handoff["predicate"] is None)
            _require(handoff["gate"] in {"surviving-finding", "canonical-owner-confirms-domain", "narrower-evidence"})
    _require(ids == SURFACES and priorities == set(range(-1, 8)))
    baseline = next(item for item in value["surfaces"] if item["id"] == "application")
    _require(baseline["owner"] == "security-review" and baseline["priority"] == -1)
    files = value["files"]
    _require(isinstance(files, dict) and set(files) == {"read_extensions", "read_names", "credential_names", "source_extensions", "inert_assets", "ignored_directories"})
    for key, items in files.items():
        if key == "inert_assets":
            # No inert format parser is shipped in this version; nothing outside
            # the reading allowlist can silently disappear by extension/magic.
            _require(items == [])
        else:
            _require(isinstance(items, list) and bool(items) and all(isinstance(item, str) and 0 < len(item) < 100 for item in items))
    limits = {"depth": 32, "files": 100000, "file_bytes": 2097152, "total_bytes": 536870912, "seconds": 60}
    _require(isinstance(value["budgets"], dict) and set(value["budgets"]) == set(limits))
    _require(all(type(value["budgets"][k]) is int and 0 < value["budgets"][k] <= v for k, v in limits.items()))
    return value


def validate_inventory(manifest: dict[str, Any], inventory: Any) -> dict[str, Any]:
    """Require canonical observed receipts, exact denominators and a bound digest."""
    _require(isinstance(inventory, dict) and set(inventory) == {"schema_version", "manifest_digest", "root_fingerprint", "complete", "reason_codes", "counters", "checks", "inventory_digest"})
    _require(type(inventory["schema_version"]) is int and inventory["schema_version"] == 1)
    _require(inventory["manifest_digest"] == digest(manifest))
    _require(isinstance(inventory["root_fingerprint"], str) and bool(_HEX.fullmatch(inventory["root_fingerprint"])))
    _require(inventory["inventory_digest"] == digest({k: v for k, v in inventory.items() if k != "inventory_digest"}))
    _require(type(inventory["complete"]) is bool)
    reasons = inventory["reason_codes"]
    _require(isinstance(reasons, list) and all(isinstance(r, str) and r in REASONS for r in reasons) and len(set(reasons)) == len(reasons))
    _require(inventory["complete"] == (not reasons))
    counters = inventory["counters"]
    _require(isinstance(counters, dict) and set(counters) == {"files", "bytes", "existence_only"})
    _require(all(type(v) is int and v >= 0 for v in counters.values()))
    _require(counters["existence_only"] <= counters["files"])
    if inventory["complete"]:
        _require(counters["files"] <= manifest["budgets"]["files"] and counters["bytes"] <= manifest["budgets"]["total_bytes"])
    checks = inventory["checks"]
    _require(isinstance(checks, list) and len(checks) == len(SURFACES))
    seen = set()
    paths: dict[str, tuple[str, str, str | None]] = {}
    for check in checks:
        _require(isinstance(check, dict) and set(check) == {"surface", "result", "evidence"})
        surface = check["surface"]
        _require(isinstance(surface, str))
        if surface not in SURFACES:
            raise RoutingError("UNSUPPORTED_SURFACE")
        _require(surface not in seen)
        seen.add(surface)
        _require(check["result"] in {"MATCH", "NEGATIVE", "UNKNOWN"})
        evidence = check["evidence"]
        _require(isinstance(evidence, list))
        _require((check["result"] == "MATCH") == bool(evidence))
        if not evidence:
            _require(check["result"] == ("NEGATIVE" if inventory["complete"] else "UNKNOWN"))
        allowed = {p["id"]: p for s in manifest["surfaces"] if s["id"] == surface for p in s["predicates"]}
        receipts = set()
        for item in evidence:
            _require(isinstance(item, dict) and set(item) == {"path", "predicate", "line", "file_identity_digest", "content_digest", "existence_only"})
            _require(item["predicate"] in allowed)
            _require(isinstance(item["path"], dict) and isinstance(item["path"].get("display"), str))
            _require(item["path"] == target_identity.canonical_path_identity(Path(item["path"]["display"])))
            _require(isinstance(item["file_identity_digest"], str) and bool(_HEX.fullmatch(item["file_identity_digest"])))
            _require(type(item["existence_only"]) is bool)
            _require(type(item["line"]) is int and 0 <= item["line"] <= manifest["budgets"]["file_bytes"])
            _require((item["existence_only"] and item["content_digest"] is None and item["line"] == 0) or
                     (not item["existence_only"] and isinstance(item["content_digest"], str) and bool(_HEX.fullmatch(item["content_digest"]))))
            relative = Path(item["path"]["display"])
            credential = any(fnmatch.fnmatchcase(relative.name.lower(), pattern.lower()) for pattern in manifest["files"]["credential_names"])
            readable = relative.suffix.lower() in manifest["files"]["read_extensions"] or any(fnmatch.fnmatchcase(relative.name.lower(), pattern.lower()) for pattern in manifest["files"]["read_names"])
            _require(credential == item["existence_only"])
            _require(readable or credential)
            operation = allowed[item["predicate"]]["operation"]
            _require((operation == "token" and not credential and item["line"] > 0) or (operation != "token" and item["line"] == 0))
            if operation == "filename":
                _require(any(fnmatch.fnmatchcase(relative.name.lower(), pattern.lower()) for pattern in allowed[item["predicate"]]["values"]))
            key = digest(item)
            _require(key not in receipts)
            receipts.add(key)
            path_key = item["path"]["normalization_key"]
            identity = (item["path"]["display"], item["file_identity_digest"], item["content_digest"])
            _require(path_key not in paths or paths[path_key] == identity)
            paths[path_key] = identity
    _require(len(paths) <= counters["files"])
    return inventory


def resolve(manifest: Any, inventory: Any) -> dict[str, Any]:
    """Return a planned queue only; no filesystem, skill availability or outcomes."""
    try:
        policy = validate_manifest(manifest)
        observed = validate_inventory(policy, inventory)
    except RoutingError as exc:
        return {"status": "inventory-incomplete", "reason_codes": [str(exc)], "planned_queue": [], "handoff_candidates": [], "concurrency_cap": 4}
    except (TypeError, KeyError, ValueError, target_identity.TargetManifestError):
        return {"status": "inventory-incomplete", "reason_codes": ["INVENTORY_INVALID"], "planned_queue": [], "handoff_candidates": [], "concurrency_cap": 4}
    checks = {c["surface"]: c for c in observed["checks"]}
    planned, handoffs = [], []
    for surface in sorted(policy["surfaces"], key=lambda s: (s["priority"], s["owner"])):
        check = checks[surface["id"]]
        if surface["id"] != "application" and check["result"] != "MATCH":
            continue
        planned.append({"surface": surface["id"], "owner": surface["owner"], "evidence_digest": digest(check)})
        predicates = {e["predicate"] for e in check["evidence"]}
        for handoff in surface["handoffs"]:
            if handoff["predicate"] is None or handoff["predicate"] in predicates:
                handoffs.append({"parent": surface["owner"], **handoff})
    conditional = planned[1:]
    return {"status": "planned" if observed["complete"] else "inventory-incomplete",
            "reason_codes": observed["reason_codes"], "planned_queue": planned,
            "conditional_batches": [conditional[i:i + 4] for i in range(0, len(conditional), 4)],
            "handoff_candidates": handoffs, "concurrency_cap": 4,
            "uncovered_surfaces": sorted(key for key, check in checks.items() if check["result"] == "UNKNOWN"),
            "negative_surfaces": sorted(key for key, check in checks.items() if check["result"] == "NEGATIVE"),
            "inventory_digest": observed["inventory_digest"], "manifest_digest": digest(policy)}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("inventory", type=Path)
    args = parser.parse_args(argv)
    try:
        result = resolve(strict.load_path(args.manifest), strict.load_path(args.inventory))
    except (strict.StrictJSONError, OSError):
        result = {"status": "inventory-incomplete", "reason_codes": ["INVENTORY_INVALID"], "planned_queue": []}
    print(json.dumps(result, sort_keys=True))
    return 0 if result["status"] == "planned" else 1


if __name__ == "__main__":
    raise SystemExit(main())
