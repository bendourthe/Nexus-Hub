"""Frozen two-attempt protocol and strictly typed self-attested bindings."""

from __future__ import annotations

import hashlib
import re
from datetime import datetime
from pathlib import Path

import _audit_envelope as audit
import _benchmark_corpus as corpus
import _normalized_audit as normalized

PROTOCOL = {"sequential": 1, "concurrent-four": 4}
ORDER = tuple(PROTOCOL)
VERSION = "nexus.application-audit-benchmark/v1"
SURFACES = (
    "application",
    "authentication",
    "api",
    "advanced-web",
    "dependency",
    "cryptography",
    "business-logic",
    "cloud-iac",
    "ai-agent",
)
TERMINAL = {"RAN", "FAILED", "UNAVAILABLE", "DECLINED"}
LIMITATIONS = [
    "SELF_ATTESTED_EXECUTION",
    "CONTENT_OBSERVED_ONLY",
    "PROCESS_NOT_ATTESTED",
    "ANSWER_ACCESS_NOT_ATTESTED",
    "NO_EXTERNAL_ANCHOR",
    "OMITTED_LAUNCHES_NOT_DISCOVERABLE",
]
RELATIONS = (
    "subject",
    "context",
    "protocol",
    "candidate",
    "attempt",
    "mode",
    "workers",
    "source",
    "answers",
    "projection",
    "map",
    "revision",
    "root",
    "scope",
    "content",
    "index",
    "routing",
    "host_receipt",
    "envelope",
    "sarif",
)


def require(ok: bool, reason: str = "BENCHMARK_BINDING_INVALID") -> None:
    if not ok:
        raise ValueError(reason)


def fields(value: object, names: str) -> None:
    require(isinstance(value, dict) and set(value) == set(names.split()))


def bytes_digest(value: object) -> str:
    return hashlib.sha256(corpus.canonical(value)).hexdigest()


def context(value: dict) -> None:
    fields(
        value,
        "host platform host_version model settings_digest registration_digest routing_digest timeout_seconds retries process_attestation",
    )
    for key in ("host", "platform", "host_version", "model"):
        require(
            isinstance(value[key], str)
            and re.fullmatch(r"[A-Za-z0-9_. -]{1,80}", value[key]) is not None
        )
    for key in ("settings_digest", "registration_digest", "routing_digest"):
        require(audit.is_digest(value[key]))
    require(
        type(value["timeout_seconds"]) is int and 1 <= value["timeout_seconds"] <= 86400
    )
    require(value["retries"] == "none" and value["process_attestation"] == "none")
    normalized.strings(value, audit.environment_secrets())


def candidate_inputs(subject_digest: str, snapshot: dict) -> dict:
    require(audit.is_digest(subject_digest))
    context(snapshot)
    return {
        "subject_manifest_digest": subject_digest,
        "execution_context_snapshot_digest": audit.digest(snapshot),
        "protocol_map_digest": audit.digest(PROTOCOL),
    }


def attempts(candidate_id: str) -> list[dict]:
    return [
        {
            "id": audit.digest({"candidate_id": candidate_id, "mode": mode}),
            "mode": mode,
            "workers": PROTOCOL[mode],
        }
        for mode in ORDER
    ]


def producer_context(snapshot: dict) -> dict:
    """Use the existing envelope producer's four-field context contract."""
    return {
        "host_identity": snapshot["host"]
        + "/"
        + snapshot["platform"]
        + "/"
        + snapshot["host_version"],
        "model_identity": snapshot["model"],
        "settings_digest": snapshot["settings_digest"],
        "boundary_status": "self-attested-no-process-attestation",
    }


def validate_plan(plan: dict) -> None:
    fields(
        plan,
        "schema candidate_id candidate_inputs subject_manifest context protocol attempts source_digest answer_digest projection_digest map_digest routing_expectations required_owners supersedes change_reason plan_digest",
    )
    require(plan["schema"] == VERSION and plan["protocol"] == PROTOCOL)
    require(all(type(v) is int for v in plan["protocol"].values()))
    require(
        isinstance(plan["subject_manifest"], list) and bool(plan["subject_manifest"])
    )
    seen = set()
    for entry in plan["subject_manifest"]:
        fields(entry, "path digest bytes")
        normalized.path(entry["path"], {}, [])
        require(
            entry["path"] not in seen
            and audit.is_digest(entry["digest"])
            and type(entry["bytes"]) is int
            and entry["bytes"] > 0
        )
        seen.add(entry["path"])
    require(
        plan["subject_manifest"]
        == sorted(plan["subject_manifest"], key=lambda e: e["path"])
    )
    require(
        plan["candidate_inputs"]
        == candidate_inputs(audit.digest(plan["subject_manifest"]), plan["context"])
    )
    require(plan["candidate_id"] == audit.digest(plan["candidate_inputs"]))
    require(plan["attempts"] == attempts(plan["candidate_id"]))
    require(all(type(a["workers"]) is int for a in plan["attempts"]))
    for key in (
        "source_digest",
        "answer_digest",
        "projection_digest",
        "map_digest",
        "plan_digest",
    ):
        require(audit.is_digest(plan[key]))
    require(
        plan["plan_digest"]
        == audit.digest({k: v for k, v in plan.items() if k != "plan_digest"})
    )
    require(plan["supersedes"] is None or audit.is_digest(plan["supersedes"]))
    require(
        plan["change_reason"]
        in {"INITIAL", "SUBJECT_CHANGED", "CONTEXT_CHANGED", "PROTOCOL_CHANGED"}
    )
    require((plan["supersedes"] is None) == (plan["change_reason"] == "INITIAL"))
    require(
        isinstance(plan["required_owners"], list)
        and bool(plan["required_owners"])
        and plan["required_owners"] == sorted(set(plan["required_owners"]))
    )
    require(all(audit.is_opaque(o) for o in plan["required_owners"]))
    expectations = plan["routing_expectations"]
    require(isinstance(expectations, list) and len(expectations) == 9)
    require(
        {r["surface_id"] for r in expectations} == {audit.opaque(s) for s in SURFACES}
    )
    for row in expectations:
        fields(row, "surface_id result evidence_digest")
        require(
            row["result"] in {"matched", "negative_checked"}
            and audit.is_digest(row["evidence_digest"])
        )


def attempt(plan: dict, attempt_id: str) -> dict:
    validate_plan(plan)
    rows = [a for a in plan["attempts"] if a["id"] == attempt_id]
    require(len(rows) == 1)
    return rows[0]


def validate_terminal(plan: dict, terminal: dict) -> dict:
    fields(
        terminal,
        "schema candidate_id attempt_id mode workers state code_search binding receipt envelope_digest sarif_digest producer_run_fingerprint declared_inputs_digest cleanup original_source_digest",
    )
    require(
        terminal["schema"] == VERSION
        and terminal["candidate_id"] == plan["candidate_id"]
    )
    declared = attempt(plan, terminal["attempt_id"])
    require(
        terminal["mode"] == declared["mode"]
        and type(terminal["workers"]) is int
        and terminal["workers"] == declared["workers"]
    )
    require(terminal["state"] in TERMINAL and terminal["code_search"] in TERMINAL)
    require(
        terminal["cleanup"] == "complete"
        and terminal["original_source_digest"] == plan["source_digest"]
    )
    bind = terminal["binding"]
    fields(
        bind,
        "candidate_id attempt_id mode workers context_digest source_digest answer_digest projection_digest map_digest revision root_fingerprint scope_fingerprint content_manifest index_digest cache_fingerprint artifacts_fingerprint routing_digest",
    )
    for key in ("candidate_id", "attempt_id", "mode", "workers"):
        require(bind[key] == terminal[key])
    require(type(bind["workers"]) is int)
    for key in ("source_digest", "answer_digest", "projection_digest", "map_digest"):
        require(bind[key] == plan[key])
    require(bind["context_digest"] == audit.digest(plan["context"]))
    require(bind["routing_digest"] == plan["context"]["routing_digest"])
    require(bind["revision"] == plan["projection_digest"])
    require(bind["scope_fingerprint"] == audit.digest([]))
    for key in (
        "root_fingerprint",
        "content_manifest",
        "cache_fingerprint",
        "artifacts_fingerprint",
    ):
        require(audit.is_digest(bind[key]))
    require(
        len(
            {
                bind[k]
                for k in (
                    "root_fingerprint",
                    "cache_fingerprint",
                    "artifacts_fingerprint",
                )
            }
        )
        == 3
    )
    require(
        audit.is_digest(bind["index_digest"])
        if terminal["code_search"] == "RAN"
        else bind["index_digest"] is None
    )
    receipt = terminal["receipt"]
    fields(
        receipt,
        "started_at finished_at duration_ms binding_digest context_digest mode workers state code_search registration_digest process_attestation producer_run_fingerprint",
    )
    audit.clock_fields(receipt)
    require(
        receipt["binding_digest"] == audit.digest(bind)
        and receipt["context_digest"] == bind["context_digest"]
    )
    for key in ("mode", "workers", "state", "code_search"):
        require(receipt[key] == terminal[key])
    require(
        type(receipt["workers"]) is int
        and receipt["producer_run_fingerprint"] == terminal["producer_run_fingerprint"]
    )
    require(
        receipt["registration_digest"] == plan["context"]["registration_digest"]
        and receipt["process_attestation"] == "none"
    )
    require(
        terminal["declared_inputs_digest"]
        == audit.digest(
            {
                "projection_digest": plan["projection_digest"],
                "context_digest": bind["context_digest"],
                "attempt_id": terminal["attempt_id"],
            }
        )
    )
    pair = (terminal["envelope_digest"], terminal["sarif_digest"])
    require(
        all(audit.is_digest(v) for v in pair)
        or (pair == (None, None) and terminal["state"] != "RAN")
    )
    require(
        audit.is_digest(terminal["producer_run_fingerprint"])
        if pair[0] is not None
        else terminal["producer_run_fingerprint"] is None
    )
    normalized.strings(terminal, audit.environment_secrets())
    return bind


def validate_pair(first: dict, second: dict) -> None:
    keys = ("root_fingerprint", "cache_fingerprint", "artifacts_fingerprint")
    require(
        {first["binding"][k] for k in keys}.isdisjoint(
            {second["binding"][k] for k in keys}
        ),
        "SHARED_ATTEMPT_STATE",
    )
    require(
        datetime.fromisoformat(first["receipt"]["finished_at"].replace("Z", "+00:00"))
        <= datetime.fromisoformat(
            second["receipt"]["started_at"].replace("Z", "+00:00")
        )
    )


def read_input(root: Path, path: Path) -> dict:
    return corpus.load(root, path)
