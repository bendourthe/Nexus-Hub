"""Exclusive local evidence ledger; caller execution claims remain self-attested."""

from __future__ import annotations

import importlib.util
import os
import re
from pathlib import Path

import _audit_envelope as audit
import _benchmark_corpus as corpus
import _benchmark_protocol as protocol
import _benchmark_scoring as scoring
import _safe_artifact as safe

HERE = Path(__file__).resolve().parent
SOURCE = "tests/fixtures/security-audit-appsec/source"
ANSWERS = "tests/fixtures/security-audit-appsec/answers/manifest.json"
ROUTING = "catalog/skills/workflow/agent-presets/references/security-audit-routing.json"
SUBJECT_TREES = (
    "catalog/skills/code-review/security-review",
    "extensions/nexus-code-search/src",
)
SUBJECT_FILES = (
    "docs/releases/v4/v4.9/development/repro/record-benchmark-unavailability.py",
    ROUTING,
    "catalog/skills/workflow/agent-presets/references/security-audit-routing.md",
    "catalog/skills/workflow/agent-presets/scripts/resolve-security-audit-routing.py",
    "catalog/skills/workflow/agent-presets/SKILL.md",
    "extensions/nexus-code-search/pyproject.toml",
    ANSWERS,
)
_spec = importlib.util.spec_from_file_location(
    "benchmark_inventory", HERE / "collect-security-audit-inventory.py"
)
inventory = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(inventory)


def filesystem_path(path: Path) -> Path:
    """The declared hash-named ledger exceeds legacy Windows MAX_PATH."""
    return corpus.filesystem_path(path)


def subject_manifest(root: Path) -> list[dict]:
    """Fixed admission roots prevent a caller from dropping a scoring input."""
    files = set(SUBJECT_FILES)
    for relative in (*SUBJECT_TREES, SOURCE):
        base = safe.assert_no_reparse_in_chain(root, root / relative)
        with safe._directory_guard(base):
            for directory, names, leaves in os.walk(base, followlinks=False):
                parent = Path(directory)
                safe.assert_no_reparse_in_chain(root, parent)
                names[:] = [n for n in names if n != "__pycache__"]
                for name in names:
                    safe.assert_no_reparse_in_chain(root, parent / name)
                for name in leaves:
                    if not name.endswith(".pyc"):
                        files.add((parent / name).relative_to(root).as_posix())
    result = []
    for relative in sorted(files):
        digest, count = safe.digest_contained_file(root, root / relative)
        result.append({"path": relative, "digest": digest, "bytes": count})
    return result


def mkdir(root: Path, path: Path) -> None:
    """Create only named descendants through validated parent handles."""
    path = safe.assert_no_reparse_in_chain(root, path)
    if path == root or path.exists():
        protocol.require(path.is_dir())
        return
    mkdir(root, path.parent)
    with safe._directory_guard(path.parent) as descriptor:
        try:
            if descriptor is None:
                path.mkdir(mode=0o700)
            else:
                os.mkdir(path.name, mode=0o700, dir_fd=descriptor)
        except FileExistsError:
            # Another creator won; validate it without changing its permissions.
            safe.assert_no_reparse_in_chain(root, path)
            protocol.require(path.is_dir())
            return
        safe.assert_no_reparse_in_chain(root, path)
        protocol.require(path.is_dir())
        if os.name == "nt":
            safe._windows_owner_only(path)
    safe.sync_contained_directory(root, path.parent)


def publish(root: Path, path: Path, value: object) -> None:
    """Idempotent only for exact expected canonical bytes; never overwrite."""
    payload = corpus.canonical(value)
    try:
        safe.atomic_publish_bytes(root, path, payload)
    except FileExistsError:
        protocol.require(
            safe.open_contained_bytes(root, path) == payload,
            "IMMUTABLE_ARTIFACT_CONFLICT",
        )
        safe.sync_contained_directory(root, path.parent)


def route_projection(source: Path, manifest: dict) -> tuple[list[dict], list[str]]:
    observed = inventory.collect(source, manifest)
    result = inventory.policy.resolve(manifest, observed)
    protocol.require(result["status"] == "planned", "INVENTORY_INCOMPLETE")
    # The physical receipt remains local. Its benchmark projection omits inode
    # identity so equivalent copies have the same logical routing evidence.
    checks = [
        {
            **c,
            "evidence": [
                {k: v for k, v in e.items() if k != "file_identity_digest"}
                for e in c["evidence"]
            ],
        }
        for c in observed["checks"]
    ]
    rows = [
        {
            "surface_id": audit.opaque(c["surface"]),
            "result": "matched" if c["result"] == "MATCH" else "negative_checked",
            "evidence_digest": audit.digest(c),
        }
        for c in checks
    ]
    owners = sorted(
        {audit.opaque(o) for o in manifest["fixed_stages"]}
        | {audit.opaque(row["owner"]) for row in result["planned_queue"]}
    )
    return sorted(rows, key=lambda r: r["surface_id"]), owners


def prepare(
    root: Path,
    candidates: Path,
    answer_archive: Path,
    snapshot: dict,
    *,
    supersedes: str | None = None,
    reason: str = "INITIAL",
) -> dict:
    """Freeze identity first, then exactly one map, then the predeclared run plan."""
    root, candidates, answer_archive = map(
        filesystem_path, (root, candidates, answer_archive)
    )
    candidates = safe.assert_no_reparse_in_chain(root, candidates)
    answer_archive = safe.assert_no_reparse_in_chain(root, answer_archive)
    protocol.require(
        candidates != answer_archive
        and candidates not in answer_archive.parents
        and answer_archive not in candidates.parents
    )
    subject = subject_manifest(root)
    inputs = protocol.candidate_inputs(audit.digest(subject), snapshot)
    candidate_id = audit.digest(inputs)
    answers = corpus.load(root, root / ANSWERS)
    corpus.snapshot(root / SOURCE, answers)
    routing = corpus.load(root, root / ROUTING)
    protocol.require(snapshot["routing_digest"] == audit.digest(routing))
    mkdir(root, candidates)
    mkdir(root, answer_archive)
    existing = {p.name for p in candidates.iterdir()}
    protocol.require(
        all(audit.is_digest(name) for name in existing), "UNKNOWN_CANDIDATE"
    )
    protocol.require(
        not existing or candidate_id in existing or supersedes is not None,
        "SUPERSESSION_REASON_REQUIRED",
    )
    directory = candidates / candidate_id
    mkdir(root, directory)
    map_path = answer_archive / (candidate_id + ".json")
    if map_path.exists():
        mapping = corpus.load(root, map_path)
        corpus.validate_map(mapping, answers, candidate_id)
    else:
        mapping = corpus.create_map(answers, candidate_id)
        publish(root, map_path, mapping)
    with corpus.projection(root / SOURCE, answers, candidate_id, mapping) as projected:
        rows, owners = route_projection(projected.source_root, routing)
    if supersedes is not None:
        protocol.require(audit.is_digest(supersedes) and supersedes != candidate_id)
        previous = corpus.load(root, candidates / supersedes / "run-plan.json")
        protocol.validate_plan(previous)
        field = {
            "SUBJECT_CHANGED": "subject_manifest_digest",
            "CONTEXT_CHANGED": "execution_context_snapshot_digest",
            "PROTOCOL_CHANGED": "protocol_map_digest",
        }.get(reason)
        protocol.require(
            field is not None and previous["candidate_inputs"][field] != inputs[field]
        )
    else:
        protocol.require(reason == "INITIAL")
    plan = {
        "schema": protocol.VERSION,
        "candidate_id": candidate_id,
        "candidate_inputs": inputs,
        "subject_manifest": subject,
        "context": snapshot,
        "protocol": protocol.PROTOCOL,
        "attempts": protocol.attempts(candidate_id),
        "source_digest": mapping["source_digest"],
        "answer_digest": mapping["answer_digest"],
        "projection_digest": mapping["projection_digest"],
        "map_digest": mapping["map_digest"],
        "routing_expectations": rows,
        "required_owners": owners,
        "supersedes": supersedes,
        "change_reason": reason,
    }
    plan["plan_digest"] = audit.digest(plan)
    protocol.validate_plan(plan)
    publish(root, directory / "run-plan.json", plan)
    mkdir(root, directory / "ledger/entries")
    mkdir(root, directory / "attempts")
    return plan


def load_candidate(
    root: Path, candidates: Path, candidate_id: str
) -> tuple[Path, dict]:
    protocol.require(audit.is_digest(candidate_id))
    directory = safe.assert_no_reparse_in_chain(root, candidates / candidate_id)
    plan = corpus.load(root, directory / "run-plan.json")
    protocol.validate_plan(plan)
    protocol.require(plan["candidate_id"] == candidate_id)
    protocol.require(
        subject_manifest(root) == plan["subject_manifest"], "STALE_SUBJECT"
    )
    return directory, plan


def entry(
    sequence: int,
    kind: str,
    attempt_id: str,
    payloads: dict,
    plan: dict,
    previous: str | None,
) -> dict:
    preimage = {
        "sequence": sequence,
        "type": kind,
        "id": attempt_id,
        "payload_digests": payloads,
        "plan_digest": plan["plan_digest"],
        "prior_entry_hash": previous,
    }
    return {**preimage, "entry_hash": audit.digest(preimage)}


def entry_name(value: dict) -> str:
    return f"{value['sequence']:04d}-{value['type']}-{value['id']}-{value['entry_hash']}.json"


def ledger(root: Path, directory: Path, plan: dict) -> list[dict]:
    base = directory / "ledger/entries"
    safe.assert_no_reparse_in_chain(root, base)
    result = []
    for path in sorted(base.iterdir()):
        protocol.require(
            re.fullmatch(
                r"000[0-3]-(terminal|outcome)-[0-9a-f]{64}-[0-9a-f]{64}\.json",
                path.name,
            )
            is not None,
            "UNKNOWN_LEDGER_ENTRY",
        )
        value = corpus.load(root, path)
        protocol.fields(
            value,
            "sequence type id payload_digests plan_digest prior_entry_hash entry_hash",
        )
        index = len(result)
        protocol.require(
            index < 4 and value["sequence"] == index and type(value["sequence"]) is int,
            "LEDGER_SEQUENCE_INVALID",
        )
        kind = "terminal" if index < 2 else "outcome"
        attempt_id = plan["attempts"][index % 2]["id"]
        expected = entry(
            index,
            kind,
            attempt_id,
            value["payload_digests"],
            plan,
            result[-1]["entry_hash"] if result else None,
        )
        protocol.require(
            value == expected and path.name == entry_name(expected),
            "LEDGER_HASH_INVALID",
        )
        protocol.require(
            isinstance(value["payload_digests"], dict)
            and bool(value["payload_digests"])
        )
        for name, digest in value["payload_digests"].items():
            protocol.require(
                name
                in {
                    "terminal.json",
                    "envelope.json",
                    "sarif.json",
                    "outcome.json",
                    "score.json",
                }
                and audit.is_digest(digest)
            )
            protocol.require(
                safe.digest_contained_file(
                    root, directory / "attempts" / attempt_id / name
                )[0]
                == digest,
                "LEDGER_ARTIFACT_SUBSTITUTION",
            )
        result.append(value)
    return result


def append_entry(
    root: Path,
    directory: Path,
    plan: dict,
    sequence: int,
    kind: str,
    attempt_id: str,
    artifacts: dict,
) -> None:
    entries = ledger(root, directory, plan)
    protocol.require(len(entries) >= sequence, "MISSING_PRIOR_ENTRY")
    prior = entries[sequence - 1]["entry_hash"] if sequence else None
    value = entry(
        sequence,
        kind,
        attempt_id,
        {name: protocol.bytes_digest(obj) for name, obj in artifacts.items()},
        plan,
        prior,
    )
    if len(entries) > sequence:
        protocol.require(entries[sequence] == value, "IMMUTABLE_ENTRY_CONFLICT")
    publish(root, directory / "ledger/entries" / entry_name(value), value)


def record(
    root: Path,
    candidates: Path,
    candidate_id: str,
    terminal: dict,
    envelope: dict | None = None,
    sarif: dict | None = None,
) -> None:
    root, candidates = map(filesystem_path, (root, candidates))
    directory, plan = load_candidate(root, candidates, candidate_id)
    protocol.validate_terminal(plan, terminal)
    protocol.require((envelope is None) == (sarif is None))
    protocol.require((terminal["envelope_digest"] is None) == (envelope is None))
    artifacts = {"terminal.json": terminal}
    if envelope is not None:
        protocol.require(
            scoring.supplied_digest(envelope, "envelope") == terminal["envelope_digest"]
            and scoring.supplied_digest(sarif, "sarif") == terminal["sarif_digest"]
        )
        admitted_envelope, admitted_sarif = scoring.admit(envelope, sarif)
        artifacts.update(
            {"envelope.json": admitted_envelope, "sarif.json": admitted_sarif}
        )
    entries = ledger(root, directory, plan)
    index = protocol.ORDER.index(terminal["mode"])
    protocol.require(len(entries) >= index, "ATTEMPT_ORDER_INVALID")
    if index:
        first = corpus.load(
            root, directory / "attempts" / plan["attempts"][0]["id"] / "terminal.json"
        )
        protocol.validate_pair(first, terminal)
    base = directory / "attempts" / terminal["attempt_id"]
    mkdir(root, base)
    for name, value in artifacts.items():
        publish(root, base / name, value)
    append_entry(
        root, directory, plan, index, "terminal", terminal["attempt_id"], artifacts
    )


def computed_outcome(
    root: Path,
    directory: Path,
    plan: dict,
    answers: dict,
    mapping: dict,
    declared: dict,
) -> dict:
    base = directory / "attempts" / declared["id"]
    terminal = corpus.load(root, base / "terminal.json")
    protocol.validate_terminal(plan, terminal)
    protocol.require(terminal["attempt_id"] == declared["id"])
    evaluator_digest = audit.digest(
        [
            e
            for e in plan["subject_manifest"]
            if e["path"].startswith(
                "catalog/skills/code-review/security-review/scripts/"
            )
        ]
    )
    common = {
        "schema": protocol.VERSION,
        "candidate_id": plan["candidate_id"],
        "attempt_id": declared["id"],
        "terminal_digest": protocol.bytes_digest(terminal),
        "evaluator_version": protocol.VERSION,
        "evaluator_code_digest": evaluator_digest,
    }
    if terminal["envelope_digest"] is None:
        protocol.require(terminal["state"] in {"FAILED", "UNAVAILABLE", "DECLINED"})
        protocol.require(
            not (base / "envelope.json").exists()
            and not (base / "sarif.json").exists()
            and not (base / "score.json").exists(),
            "FORBIDDEN_NOT_SCORED",
        )
        return {
            "outcome.json": {
                **common,
                "type": "not_scored",
                "reason_code": "PRE_SCORING_" + terminal["state"],
                "state": terminal["state"],
                "artifact_digests": {"terminal.json": protocol.bytes_digest(terminal)},
                "limitations": protocol.LIMITATIONS,
            }
        }
    envelope, sarif = (
        corpus.load(root, base / name) for name in ("envelope.json", "sarif.json")
    )
    result = scoring.score(
        answers,
        mapping,
        plan,
        plan["candidate_inputs"]["subject_manifest_digest"],
        terminal,
        envelope,
        sarif,
        admitted=True,
    )
    bindings = {
        "answers": protocol.bytes_digest(answers),
        "map": protocol.bytes_digest(mapping),
        "plan": protocol.bytes_digest(plan),
        "subject": plan["candidate_inputs"]["subject_manifest_digest"],
        "terminal": protocol.bytes_digest(terminal),
        "envelope": protocol.bytes_digest(envelope),
        "sarif": protocol.bytes_digest(sarif),
        "score": protocol.bytes_digest(result),
    }
    return {
        "score.json": result,
        "outcome.json": {
            **common,
            "type": "evaluated",
            "validity": result["validity"],
            "scorer_version": scoring.VERSION,
            "input_output_digests": bindings,
            "limitations": protocol.LIMITATIONS,
        },
    }


def scoring_inputs(
    root: Path, directory: Path, plan: dict, answer_archive: Path
) -> tuple[dict, dict, list[dict]]:
    entries = ledger(root, directory, plan)
    protocol.require(len(entries) >= 2, "BOTH_TERMINALS_REQUIRED")
    terminals = [
        corpus.load(root, directory / "attempts" / a["id"] / "terminal.json")
        for a in plan["attempts"]
    ]
    for terminal in terminals:
        protocol.validate_terminal(plan, terminal)
    protocol.validate_pair(*terminals)
    answers = corpus.load(root, root / ANSWERS)
    mapping = corpus.load(root, answer_archive / (plan["candidate_id"] + ".json"))
    corpus.validate_map(mapping, answers, plan["candidate_id"])
    protocol.require(
        all(
            mapping[k] == plan[k]
            for k in (
                "source_digest",
                "answer_digest",
                "projection_digest",
                "map_digest",
            )
        )
    )
    return answers, mapping, entries


def score_candidate(
    root: Path, candidates: Path, answer_archive: Path, candidate_id: str
) -> None:
    root, candidates, answer_archive = map(
        filesystem_path, (root, candidates, answer_archive)
    )
    directory, plan = load_candidate(root, candidates, candidate_id)
    answers, mapping, _ = scoring_inputs(root, directory, plan, answer_archive)
    for index, declared in enumerate(plan["attempts"]):
        artifacts = computed_outcome(root, directory, plan, answers, mapping, declared)
        for name, value in artifacts.items():
            publish(root, directory / "attempts" / declared["id"] / name, value)
        append_entry(
            root, directory, plan, index + 2, "outcome", declared["id"], artifacts
        )


def verify(
    root: Path, candidates: Path, answer_archive: Path, candidate_id: str
) -> dict:
    root, candidates, answer_archive = map(
        filesystem_path, (root, candidates, answer_archive)
    )
    directory, plan = load_candidate(root, candidates, candidate_id)
    protocol.require(
        {p.name for p in directory.iterdir()}
        in (
            {"run-plan.json", "ledger", "attempts"},
            {"run-plan.json", "ledger", "attempts", "attempt-ledger.jsonl"},
        ),
        "UNTRACKED_CANDIDATE_ARTIFACT",
    )
    protocol.require(
        {p.name for p in (directory / "ledger").iterdir()} == {"entries"},
        "UNTRACKED_LEDGER_ARTIFACT",
    )
    answers, mapping, entries = scoring_inputs(root, directory, plan, answer_archive)
    protocol.require(len(entries) == 4, "INCOMPLETE_LEDGER")
    if (directory / "attempt-ledger.jsonl").exists():
        protocol.require(
            safe.open_contained_bytes(root, directory / "attempt-ledger.jsonl")
            == b"".join(corpus.canonical(e) for e in entries),
            "DERIVED_ARTIFACT_CONFLICT",
        )
    outcomes = []
    for index, declared in enumerate(plan["attempts"]):
        base = directory / "attempts" / declared["id"]
        terminal = corpus.load(root, base / "terminal.json")
        terminal_names = {"terminal.json"} | (
            {"envelope.json", "sarif.json"}
            if terminal["envelope_digest"] is not None
            else set()
        )
        protocol.require(set(entries[index]["payload_digests"]) == terminal_names)
        expected = computed_outcome(root, directory, plan, answers, mapping, declared)
        protocol.require(
            entries[index + 2]["payload_digests"]
            == {name: protocol.bytes_digest(obj) for name, obj in expected.items()},
            "OUTCOME_SUBSTITUTION",
        )
        protocol.require(
            {p.name for p in base.iterdir()} == terminal_names | set(expected),
            "UNTRACKED_ATTEMPT_ARTIFACT",
        )
        for name, value in expected.items():
            protocol.require(
                safe.open_contained_bytes(root, base / name) == corpus.canonical(value),
                "OUTCOME_SUBSTITUTION",
            )
        outcomes.append(
            {
                "attempt": declared,
                "outcome": expected["outcome.json"],
                "score": expected.get("score.json"),
                "terminal": terminal,
            }
        )
    protocol.require(
        {p.name for p in (directory / "attempts").iterdir()}
        == {a["id"] for a in plan["attempts"]}
    )
    # All tracked artifacts are typed objects. The answer archive is deliberately
    # separate and is never an artifact admitted into a declared host attempt.
    for path in directory.rglob("*.json"):
        payload = safe.open_contained_bytes(root, path)
        protocol.require(
            answers["answer_canary"].encode() not in payload, "ANSWER_CANARY_EXPOSED"
        )
    return {
        "plan": plan,
        "entries": entries,
        "outcomes": outcomes,
        "limitations": protocol.LIMITATIONS,
    }


def report(verified: dict) -> bytes:
    plan = verified["plan"]
    lines = [
        "# Application audit benchmark",
        "",
        "Two predeclared observational attempts. Execution is self-attested; local artifact bytes and ledger consistency are verified. No process attestation or external anchor exists. Omitted host launches and answer access outside declared inputs cannot be discovered.",
        "",
        f"Candidate: `{plan['candidate_id']}`.",
        "",
        f"Plan digest: `{plan['plan_digest']}`. Subject digest: `{plan['candidate_inputs']['subject_manifest_digest']}`.",
        "",
        "| Attempt | Workers | Outcome | Code search |",
        "| --- | --- | --- | --- |",
    ]
    for row in verified["outcomes"]:
        outcome = row["outcome"]
        state = outcome.get("reason_code", outcome.get("validity"))
        lines.append(
            f"| {row['attempt']['mode']} | {row['attempt']['workers']} | {state} | {row['terminal']['code_search']} |"
        )
    lines.extend(
        [
            "",
            "## Characterization targets",
            "",
            "| Attempt | Target | Observed | State |",
            "| --- | --- | --- | --- |",
        ]
    )
    for row in verified["outcomes"]:
        result = row["score"]
        for name, target in scoring.TARGETS.items():
            value = result["metrics"][name] if result else {"state": "unscorable"}
            observed = str(value.get("numerator", "unavailable")) + (
                "/" + str(value["denominator"]) if "denominator" in value else ""
            )
            lines.append(
                f"| {row['attempt']['mode']} | {name} ({target}) | {observed} | {value['state']} |"
            )
    lines.extend(
        [
            "",
            "## Evidence and limits",
            "",
            f"The local ledger contains exactly two terminal entries and two evaluator-owned outcomes. Its final hash is `{verified['entries'][-1]['entry_hash']}`. Each outcome is recomputed before rendering; attempt-ledger.jsonl is only a derived projection.",
            "",
            "Both attempts declare separate source, cache, artifact, and index state. Owned temporary roots are cleaned and original source digests are unchanged. The frozen answer map remains only in the separate local answer archive for future verification; it is excluded from declared host inputs and tracked host artifacts. The corpus is inert syntax and was never executed. Structural remediation is not functional preservation. Characterization misses and unavailable outcomes are informational and do not establish application safety.",
            "",
        ]
    )
    return "\n".join(lines).encode("ascii")


def render(
    root: Path,
    candidates: Path,
    answer_archive: Path,
    candidate_id: str,
    destination: Path,
) -> None:
    root, candidates, answer_archive, destination = map(
        filesystem_path, (root, candidates, answer_archive, destination)
    )
    verified = verify(root, candidates, answer_archive, candidate_id)
    directory = candidates / candidate_id
    payload = b"".join(corpus.canonical(e) for e in verified["entries"])
    for path, content in (
        (directory / "attempt-ledger.jsonl", payload),
        (destination, report(verified)),
    ):
        try:
            safe.atomic_publish_bytes(root, path, content)
        except FileExistsError:
            protocol.require(
                safe.open_contained_bytes(root, path) == content,
                "DERIVED_ARTIFACT_CONFLICT",
            )
            safe.sync_contained_directory(root, path.parent)
