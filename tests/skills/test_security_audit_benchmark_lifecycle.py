"""Real local publication, scorer ownership, interruption, and ledger tampering."""

from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import shutil
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "catalog/skills/code-review/security-review/scripts"
sys.path.insert(0, str(SCRIPTS))
import _audit_envelope as audit
import _benchmark_corpus as corpus
import _benchmark_lifecycle as lifecycle
import _benchmark_protocol as protocol
import _benchmark_scoring as scoring


@pytest.fixture
def prepared(tmp_path, monkeypatch):
    tmp_path = lifecycle.filesystem_path(tmp_path)
    # Keep test copies small while exercising the real 32-file corpus, routing,
    # safe publication, and cleanup. Subject traversal has a separate real test.
    shutil.copytree(ROOT / lifecycle.SOURCE, tmp_path / lifecycle.SOURCE)
    for name in (lifecycle.ANSWERS, lifecycle.ROUTING):
        (tmp_path / name).parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / name, tmp_path / name)
    (tmp_path / "subject.txt").write_text("original")

    def subjects(root):
        return [
            {
                "path": "subject.txt",
                "digest": hashlib.sha256(
                    (root / "subject.txt").read_bytes()
                ).hexdigest(),
                "bytes": (root / "subject.txt").stat().st_size,
            }
        ]

    monkeypatch.setattr(lifecycle, "subject_manifest", subjects)
    context = {
        "host": "test",
        "platform": "test",
        "host_version": "test",
        "model": "test",
        "settings_digest": "a" * 64,
        "registration_digest": "b" * 64,
        "routing_digest": audit.digest(
            corpus.load(tmp_path, tmp_path / lifecycle.ROUTING)
        ),
        "timeout_seconds": 60,
        "retries": "none",
        "process_attestation": "none",
    }
    candidates, archive = tmp_path / "candidates", tmp_path / "answers-private"
    plan = lifecycle.prepare(tmp_path, candidates, archive, context)
    return tmp_path, candidates, archive, plan


def terminal(plan, index, state="UNAVAILABLE", code_search=None):
    declared = plan["attempts"][index]
    bind = {
        "candidate_id": plan["candidate_id"],
        "attempt_id": declared["id"],
        "mode": declared["mode"],
        "workers": declared["workers"],
        "context_digest": audit.digest(plan["context"]),
        **{
            k: plan[k]
            for k in (
                "source_digest",
                "answer_digest",
                "projection_digest",
                "map_digest",
            )
        },
        "revision": plan["projection_digest"],
        "root_fingerprint": audit.digest([index, "root"]),
        "scope_fingerprint": audit.digest([]),
        "content_manifest": audit.digest([index, "content"]),
        "index_digest": audit.digest([index, "index"])
        if (code_search or state) == "RAN"
        else None,
        "cache_fingerprint": audit.digest([index, "cache"]),
        "artifacts_fingerprint": audit.digest([index, "artifacts"]),
        "routing_digest": plan["context"]["routing_digest"],
    }
    receipt = {
        "started_at": f"2026-09-08T00:00:0{index * 2}Z",
        "finished_at": f"2026-09-08T00:00:0{index * 2 + 1}Z",
        "duration_ms": 1000,
        "binding_digest": audit.digest(bind),
        "context_digest": bind["context_digest"],
        "mode": declared["mode"],
        "workers": declared["workers"],
        "state": state,
        "code_search": code_search or state,
        "registration_digest": plan["context"]["registration_digest"],
        "process_attestation": "none",
    }
    receipt["producer_run_fingerprint"] = None
    return {
        "schema": protocol.VERSION,
        "candidate_id": plan["candidate_id"],
        "attempt_id": declared["id"],
        "mode": declared["mode"],
        "workers": declared["workers"],
        "state": state,
        "code_search": code_search or state,
        "binding": bind,
        "receipt": receipt,
        "producer_run_fingerprint": None,
        "envelope_digest": None,
        "sarif_digest": None,
        "declared_inputs_digest": audit.digest(
            {
                "projection_digest": plan["projection_digest"],
                "context_digest": bind["context_digest"],
                "attempt_id": declared["id"],
            }
        ),
        "cleanup": "complete",
        "original_source_digest": plan["source_digest"],
    }


def evidence(prepared, index=0):
    root, _, archive, plan = prepared
    answers = corpus.load(root, root / lifecycle.ANSWERS)
    mapping = corpus.load(root, archive / (plan["candidate_id"] + ".json"))
    term = terminal(plan, index, "RAN")
    envelope = json.loads(
        (
            ROOT / "tests/fixtures/security-audit/envelopes/degraded.expected.json"
        ).read_text()
    )
    host_template = next(r for r in envelope["receipts"] if r["type"] == "host")
    graph = copy.deepcopy(next(r for r in envelope["receipts"] if r["type"] == "graph"))
    graph.update(
        id=audit.opaque("graph"),
        state="RAN",
        index_digest=term["binding"]["index_digest"],
        quality="unknown",
        locations=[],
        result_count=0,
        ambiguity="none",
        operation="code_context",
    )
    host = []
    for owner in plan["required_owners"]:
        row = copy.deepcopy(host_template)
        row.update(
            id=audit.opaque(owner),
            owner_id=owner,
            state="RAN",
            required=True,
            artifact_ids=[],
            execution_context_digest=audit.digest(
                protocol.producer_context(plan["context"])
            ),
        )
        host.append(row)
    envelope.update(
        receipts=host + [graph],
        artifacts=[],
        findings=[],
        routing={
            "surface_receipts": plan["routing_expectations"],
            "required_stage_ids": plan["required_owners"],
        },
        remediation={
            "receipt_count": 0,
            "closure_state": "not-requested",
            "verifier_count": 0,
            "verifier_state": "not-requested",
        },
        graph_quality=["unknown"],
        reason_codes=["SELF_ATTESTED_HOST_EXECUTION"],
        input_run_fingerprint=audit.digest(term["binding"]),
        routing_manifest_digest=plan["context"]["routing_digest"],
    )
    bind = term["binding"]
    envelope["target"] = {
        "revision": bind["revision"],
        "root_fingerprint": bind["root_fingerprint"],
        "scope_fingerprint": bind["scope_fingerprint"],
        "content_manifest_before": bind["content_manifest"],
        "content_manifest_after": bind["content_manifest"],
        "change_reason": "UNCHANGED",
    }
    paths = {e["source_path"]: e["projected_path"] for e in mapping["entries"]}
    for seed in answers["seeds"]:
        path = paths[seed["path"]]
        finding = {
            "id": audit.opaque(seed["id"]),
            "rule_id": seed["vulnerability_kind"],
            "vulnerability_kind": seed["vulnerability_kind"],
            "language": seed["language"],
            "title": audit.KINDS[seed["vulnerability_kind"]],
            "severity": seed["severity"],
            "release_blocking": seed["release_blocking"],
            "confidence": 0.9,
            "disposition": "confirmed",
            "location": {"path": path, **seed["region"]},
            "evidence_receipt_ids": [graph["id"]],
            "properties": {},
        }
        if seed["source_to_sink"]:
            finding["source_to_sink"] = {}
            for endpoint, name in seed["source_to_sink"].items():
                symbol = audit.opaque(Path(path).stem + "." + name)
                finding["source_to_sink"][endpoint] = {
                    "symbol": symbol,
                    "receipt_ids": [graph["id"]],
                }
                graph["locations"].append(
                    {"path": path, "symbol": symbol, "start_line": 1, "end_line": 10}
                )
        envelope["findings"].append(finding)
    graph["result_count"] = 1
    return answers, mapping, plan, term, envelope


def reseal(term, envelope):
    envelope["disposition_counts"] = {
        d: sum(f["disposition"] == d for f in envelope["findings"])
        for d in audit.DISPOSITIONS
    }
    envelope["run_fingerprint"] = audit.digest(
        {k: v for k, v in envelope.items() if k != "run_fingerprint"}
    )
    sarif = scoring.sarif_module.emit(envelope, secrets=[])
    term["producer_run_fingerprint"] = envelope["input_run_fingerprint"]
    term["receipt"]["producer_run_fingerprint"] = envelope["input_run_fingerprint"]
    term["envelope_digest"], term["sarif_digest"] = (
        protocol.bytes_digest(envelope),
        protocol.bytes_digest(sarif),
    )
    return sarif


def scored(inputs):
    answers, mapping, plan, term, envelope = inputs
    sarif = reseal(term, envelope)
    return scoring.score(
        answers,
        mapping,
        plan,
        plan["candidate_inputs"]["subject_manifest_digest"],
        term,
        envelope,
        sarif,
    )


def complete(prepared):
    root, candidates, archive, plan = prepared
    for index in range(2):
        lifecycle.record(root, candidates, plan["candidate_id"], terminal(plan, index))
    lifecycle.score_candidate(root, candidates, archive, plan["candidate_id"])
    return lifecycle.verify(root, candidates, archive, plan["candidate_id"])


def test_prepare_reuses_one_projection(prepared):
    root, candidates, archive, plan = prepared
    assert lifecycle.prepare(root, candidates, archive, plan["context"]) == plan
    assert len(list(archive.iterdir())) == 1


def test_exact_two_outcomes_and_deterministic_report(prepared):
    root, candidates, archive, plan = prepared
    verified = complete(prepared)
    assert len(verified["entries"]) == 4
    assert {r["outcome"]["type"] for r in verified["outcomes"]} == {"not_scored"}
    lifecycle.render(
        root, candidates, archive, plan["candidate_id"], root / "report.md"
    )
    lifecycle.render(
        root, candidates, archive, plan["candidate_id"], root / "report.md"
    )
    assert (root / "report.md").read_bytes() == lifecycle.report(verified)
    data = (candidates / plan["candidate_id"] / "attempt-ledger.jsonl").read_bytes()
    assert data == b"".join(corpus.canonical(e) for e in verified["entries"])
    assert all(
        e["entry_hash"]
        == audit.digest({k: v for k, v in e.items() if k != "entry_hash"})
        for e in verified["entries"]
    )


def test_perfect_and_partial_scoring(prepared):
    inputs = evidence(prepared)
    result = scored(inputs)
    assert result["validity"] == "valid", result
    assert all(m["state"] == "met" for m in result["metrics"].values())
    assert "verdict" not in json.dumps(result)
    inputs[-1]["findings"] = inputs[-1]["findings"][:8]
    result = scored(inputs)
    assert result["metrics"]["seed_recall"]["numerator"] == 8
    assert result["metrics"]["seed_recall"]["denominator"] == 16
    assert result["metrics"]["seed_recall"]["state"] == "not_met"


def test_evaluated_outcomes_are_recomputed(prepared):
    root, candidates, archive, plan = prepared
    for index in range(2):
        inputs = evidence(prepared, index)
        term, envelope = inputs[-2:]
        sarif = reseal(term, envelope)
        lifecycle.record(root, candidates, plan["candidate_id"], term, envelope, sarif)
    lifecycle.score_candidate(root, candidates, archive, plan["candidate_id"])
    verified = lifecycle.verify(root, candidates, archive, plan["candidate_id"])
    assert all(row["outcome"]["validity"] == "valid" for row in verified["outcomes"])


@pytest.mark.parametrize(
    "case",
    [
        "locationless",
        "wrong_vulnerable",
        "nonoverlap",
        "benign_collision",
        "false_positive",
        "missing_stage",
        "empty",
    ],
)
def test_characterization_metrics_do_not_substitute_location_for_detection(
    prepared, case
):
    inputs = evidence(prepared)
    answers, mapping, plan, _term, envelope = inputs
    first = envelope["findings"][0]
    if case == "locationless":
        first["location"] = {"locationless": True}
    if case == "wrong_vulnerable":
        first["location"]["path"] = envelope["findings"][1]["location"]["path"]
    if case == "nonoverlap":
        first["location"].update(start_line=999, end_line=1000)
    if case in {"benign_collision", "false_positive"}:
        copy_finding = copy.deepcopy(first)
        copy_finding["id"] = audit.opaque("benign-alert")
        copy_finding["location"]["path"] = next(
            e["projected_path"]
            for e in mapping["entries"]
            if e["source_path"] == answers["seeds"][0]["benign_path"]
        )
        if case == "benign_collision":
            copy_finding["severity"] = "medium"
            copy_finding["release_blocking"] = False
        envelope["findings"].append(copy_finding)
    if case == "missing_stage":
        envelope["receipts"] = [
            r
            for r in envelope["receipts"]
            if r.get("owner_id") != plan["required_owners"][0]
        ]
        envelope["routing"]["required_stage_ids"] = plan["required_owners"][1:]
    if case == "empty":
        envelope["findings"] = []
    result = scored(inputs)
    assert result["validity"] == "valid", result
    if case in {"locationless", "wrong_vulnerable", "nonoverlap"}:
        assert result["metrics"]["seed_recall"]["numerator"] == 16
        assert result["metrics"]["location_accuracy"]["numerator"] == 15
    if case in {"benign_collision", "false_positive"}:
        assert result["metrics"]["seed_recall"]["numerator"] == 16
        assert result["metrics"]["benign_high_critical"]["numerator"] == (
            case == "false_positive"
        )
    if case == "missing_stage":
        assert result["metrics"]["required_stage_completeness"]["state"] == "not_met"
    if case == "empty":
        assert result["metrics"]["seed_recall"]["denominator"] == 16
        assert result["metrics"]["location_accuracy"]["state"] == "unscorable"
        assert result["metrics"]["closure_completeness"]["denominator"] == 1


@pytest.mark.parametrize(
    "case",
    [
        "duplicate_match",
        "unknown_path",
        "sarif",
        "binding",
        "subject",
        "map",
        "answer",
        "index",
        "context",
        "corrected",
        "duplicate_id",
        "invalid_disposition",
    ],
)
def test_invalid_attempts_are_scorer_owned_unscorable(prepared, case):
    inputs = evidence(prepared)
    answers, mapping, plan, term, envelope = inputs
    if case == "duplicate_match":
        finding = copy.deepcopy(envelope["findings"][0])
        finding["id"] = audit.opaque("duplicate")
        envelope["findings"].append(finding)
    if case == "unknown_path":
        envelope["findings"][0]["location"]["path"] = "unknown.py"
    if case == "corrected":
        envelope["findings"][0]["disposition"] = "corrected"
    sarif = reseal(term, envelope)
    subject = plan["candidate_inputs"]["subject_manifest_digest"]
    if case == "sarif":
        sarif["runs"][0]["results"].pop()
    if case == "binding":
        term["binding"]["root_fingerprint"] = "f" * 64
    if case == "subject":
        subject = "f" * 64
    if case == "map":
        mapping["projection_digest"] = "f" * 64
    if case == "answer":
        answers["seeds"].pop()
    if case == "index":
        term["binding"]["index_digest"] = "f" * 64
        term["receipt"]["binding_digest"] = audit.digest(term["binding"])
    if case == "context":
        plan["context"]["model"] = "changed"
    if case == "duplicate_id":
        envelope["findings"][1]["id"] = envelope["findings"][0]["id"]
    if case == "invalid_disposition":
        envelope["findings"][0]["disposition"] = "ignored"
    result = scoring.score(answers, mapping, plan, subject, term, envelope, sarif)
    assert result["validity"] == "unscorable"
    assert all(m["state"] == "unscorable" for m in result["metrics"].values())


@pytest.mark.parametrize(
    "point", ["terminal.json", "terminal-entry", "outcome.json", "outcome-entry"]
)
def test_interrupted_publication_recovery_is_exact(prepared, monkeypatch, point):
    root, candidates, archive, plan = prepared
    original = lifecycle.publish
    interrupted = False

    def publish(base, path, value):
        nonlocal interrupted
        match = path.name == point or (
            point.endswith("-entry")
            and value.get("type") == point.split("-")[0]
            and "entry_hash" in value
        )
        if match and not interrupted:
            interrupted = True
            original(base, path, value)
            raise OSError("injected after publication")
        original(base, path, value)

    monkeypatch.setattr(lifecycle, "publish", publish)
    if point.startswith("terminal"):
        with pytest.raises(OSError):
            lifecycle.record(root, candidates, plan["candidate_id"], terminal(plan, 0))
        lifecycle.record(root, candidates, plan["candidate_id"], terminal(plan, 0))
        lifecycle.record(root, candidates, plan["candidate_id"], terminal(plan, 1))
        lifecycle.score_candidate(root, candidates, archive, plan["candidate_id"])
    else:
        for i in range(2):
            lifecycle.record(root, candidates, plan["candidate_id"], terminal(plan, i))
        with pytest.raises(OSError):
            lifecycle.score_candidate(root, candidates, archive, plan["candidate_id"])
        lifecycle.score_candidate(root, candidates, archive, plan["candidate_id"])
    assert (
        interrupted
        and len(
            lifecycle.verify(root, candidates, archive, plan["candidate_id"])["entries"]
        )
        == 4
    )


@pytest.mark.parametrize(
    "case",
    [
        "outcome",
        "terminal",
        "entry",
        "fork",
        "missing",
        "extra",
        "map",
        "stale_subject",
        "jsonl",
    ],
)
def test_post_ledger_substitution_rejected(prepared, case):
    root, candidates, archive, plan = prepared
    complete(prepared)
    directory = candidates / plan["candidate_id"]
    first = directory / "attempts" / plan["attempts"][0]["id"]
    if case in {"outcome", "terminal"}:
        (first / (case + ".json")).write_text("{}")
    if case == "entry":
        next((directory / "ledger/entries").iterdir()).write_text("{}")
    if case == "fork":
        path = next(
            entry for entry in (directory / "ledger/entries").iterdir()
            if entry.name.startswith("0000-")
        )
        shutil.copyfile(path, path.with_name("0001" + path.name[4:]))
    if case == "missing":
        (first / "outcome.json").unlink()
    if case == "extra":
        (first / "raw.json").write_text("{}")
    if case == "map":
        (archive / (plan["candidate_id"] + ".json")).write_text("{}")
    if case == "stale_subject":
        (root / "subject.txt").write_text("changed")
    if case == "jsonl":
        (directory / "attempt-ledger.jsonl").write_text("forged")
    with pytest.raises((ValueError, OSError, lifecycle.safe.UnsafeArtifactError)):
        lifecycle.render(
            root, candidates, archive, plan["candidate_id"], root / "report.md"
        )


def test_order_and_not_scored_gate(prepared):
    root, candidates, archive, plan = prepared
    with pytest.raises(ValueError):
        lifecycle.record(root, candidates, plan["candidate_id"], terminal(plan, 1))
    with pytest.raises(ValueError):
        lifecycle.score_candidate(root, candidates, archive, plan["candidate_id"])
    with pytest.raises(ValueError):
        lifecycle.record(
            root, candidates, plan["candidate_id"], terminal(plan, 0, "RAN")
        )
    malformed = terminal(plan, 0)
    malformed["cleanup"] = "failed"
    with pytest.raises(ValueError):
        lifecycle.record(root, candidates, plan["candidate_id"], malformed)


def test_supersession_requires_changed_inputs(prepared):
    root, candidates, archive, plan = prepared
    with pytest.raises(ValueError):
        lifecycle.prepare(
            root,
            candidates,
            archive,
            plan["context"],
            supersedes=plan["candidate_id"],
            reason="SUBJECT_CHANGED",
        )
    (root / "subject.txt").write_text("changed")
    replacement = lifecycle.prepare(
        root,
        candidates,
        archive,
        plan["context"],
        supersedes=plan["candidate_id"],
        reason="SUBJECT_CHANGED",
    )
    assert replacement["candidate_id"] != plan["candidate_id"]
    assert (candidates / plan["candidate_id"] / "run-plan.json").exists()


def test_real_closure_producer_to_sarif_to_score(prepared):
    inputs = evidence(prepared)
    answers, mapping, plan, term, expected = inputs
    spec = importlib.util.spec_from_file_location(
        "benchmark_test_closure", SCRIPTS / "closure-gate.py"
    )
    gate = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(gate)
    raw = json.loads(
        (
            ROOT / "tests/fixtures/security-audit/application-audit-complete.json"
        ).read_text()
    )
    profile = raw["application_audit"]
    bind = term["binding"]
    profile.update(
        target_revision=bind["revision"],
        target_root_fingerprint=bind["root_fingerprint"],
        scope_fingerprint=bind["scope_fingerprint"],
        routing_manifest_digest=bind["routing_digest"],
        run_id=term["attempt_id"],
    )
    profile["target_identity"]["manifest_digest"] = bind["content_manifest"]
    profile["target_revalidation"] = {
        "before_digest": bind["content_manifest"],
        "after_digest": bind["content_manifest"],
        "changed": False,
    }
    manifest = corpus.load(prepared[0], prepared[0] / lifecycle.ROUTING)
    owner_names = {
        *manifest["fixed_stages"],
        *(r["owner"] for r in manifest["surfaces"]),
    }
    selected = sorted(
        o for o in owner_names if audit.opaque(o) in plan["required_owners"]
    )
    template = copy.deepcopy(profile["stages"][0])
    profile["stages"] = [
        {
            **copy.deepcopy(template),
            "id": "host-" + str(i),
            "stage_identity": name,
            "tool_identity": name,
            "execution_context": protocol.producer_context(plan["context"]),
        }
        for i, name in enumerate(selected)
    ]
    profile["required_stage_identities"] = selected
    surface_template = profile["surface_receipts"][0]
    by_id = {audit.opaque(s): s for s in protocol.SURFACES}
    profile["surface_receipts"] = [
        {
            **copy.deepcopy(surface_template),
            "surface": by_id[r["surface_id"]],
            "result": r["result"],
            "evidence_digest": r["evidence_digest"],
        }
        for r in plan["routing_expectations"]
    ]
    profile["supported_surfaces"] = list(protocol.SURFACES)
    graph = profile["graph_receipts"][0]
    normalized_graph = next(r for r in expected["receipts"] if r["type"] == "graph")
    for key in (
        "locations",
        "result_count",
        "operation",
        "quality",
        "ambiguity",
        "index_digest",
    ):
        graph[key] = normalized_graph[key]
    graph["query_provenance"] = "nexus-code-search/" + graph["operation"]
    raw_template = raw["findings"][0]
    raw["findings"] = []
    for i, finding in enumerate(expected["findings"]):
        row = {
            **copy.deepcopy(raw_template),
            **copy.deepcopy(finding),
            "id": "finding-" + str(i),
            "evidence_receipt_ids": [graph["id"]],
        }
        if "source_to_sink" in row:
            for endpoint in row["source_to_sink"].values():
                endpoint["receipt_ids"] = [graph["id"]]
        raw["findings"].append(row)
    for key in (
        "scanner_inventory",
        "scanner_receipts",
        "remediation_receipts",
        "verifiers",
        "report_claims",
    ):
        raw[key] = []
    profile["observed_artifacts"][0]["stage_id"] = profile["stages"][0]["id"]
    profile["run_fingerprint"] = gate.profile_fingerprint(profile)
    for key in ("stages", "surface_receipts", "graph_receipts", "observed_artifacts"):
        for row in profile[key]:
            row["run_fingerprint"] = profile["run_fingerprint"]
            if "run_id" in row:
                row["run_id"] = profile["run_id"]
            if key == "stages":
                row["binding"] = audit.binding(profile)
            if key == "graph_receipts":
                row.update({k: profile[k] for k in audit.BINDINGS})
    produced = gate.summarize_review_record(raw, secrets=[])
    frozen = corpus.canonical(produced)
    sarif = scoring.sarif_module.emit(produced, secrets=[])
    term["producer_run_fingerprint"] = produced["input_run_fingerprint"]
    term["receipt"]["producer_run_fingerprint"] = produced["input_run_fingerprint"]
    term["envelope_digest"], term["sarif_digest"] = (
        protocol.bytes_digest(produced),
        protocol.bytes_digest(sarif),
    )
    result = scoring.score(
        answers,
        mapping,
        plan,
        plan["candidate_inputs"]["subject_manifest_digest"],
        term,
        produced,
        sarif,
    )
    assert result["validity"] == "valid", result
    assert result["metrics"]["seed_recall"]["numerator"] == 16
    assert corpus.canonical(produced) == frozen
    assert produced["input_run_fingerprint"] != audit.digest(bind)


@pytest.mark.parametrize("case", ["sarif", "envelope", "language", "unknown_path"])
def test_invalid_evidence_remains_an_evaluated_outcome(prepared, case):
    root, candidates, archive, plan = prepared
    for index in range(2):
        inputs = evidence(prepared, index)
        term, envelope = inputs[-2:]
        if case == "language":
            envelope["findings"][0]["language"] = None
        if case == "unknown_path":
            envelope["findings"][0]["location"]["path"] = "unknown.py"
        sarif = reseal(term, envelope)
        if case == "sarif":
            sarif["runs"][0]["results"].pop()
        if case == "envelope":
            envelope["findings"][0]["disposition"] = "untrusted raw command"
        term["envelope_digest"], term["sarif_digest"] = (
            protocol.bytes_digest(envelope),
            protocol.bytes_digest(sarif),
        )
        lifecycle.record(root, candidates, plan["candidate_id"], term, envelope, sarif)
    lifecycle.score_candidate(root, candidates, archive, plan["candidate_id"])
    result = lifecycle.verify(root, candidates, archive, plan["candidate_id"])
    assert all(
        r["outcome"]["type"] == "evaluated" and r["score"]["validity"] == "unscorable"
        for r in result["outcomes"]
    )
    for path in (candidates / plan["candidate_id"]).rglob("*.json"):
        assert "untrusted raw command" not in path.read_text()


def test_strict_worker_types_and_cross_role_state(prepared):
    plan = copy.deepcopy(prepared[3])
    plan["protocol"]["sequential"] = True
    plan["attempts"][0]["workers"] = True
    plan["plan_digest"] = audit.digest(
        {k: v for k, v in plan.items() if k != "plan_digest"}
    )
    with pytest.raises(ValueError):
        protocol.validate_plan(plan)
    first, second = (terminal(prepared[3], i) for i in range(2))
    second["binding"]["root_fingerprint"] = first["binding"]["cache_fingerprint"]
    second["receipt"]["binding_digest"] = audit.digest(second["binding"])
    protocol.validate_terminal(prepared[3], second)
    with pytest.raises(ValueError):
        protocol.validate_pair(first, second)


def test_subject_includes_routing_host_contract():
    manifest = lifecycle.subject_manifest(ROOT)
    assert (
        "catalog/skills/workflow/agent-presets/references/security-audit-routing.md"
        in {e["path"] for e in manifest}
    )
    assert not any(
        "candidates/" in e["path"] or "answer-projection-map" in e["path"]
        for e in manifest
    )


def load_cli(name):
    spec = importlib.util.spec_from_file_location(
        name.replace("-", "_"), SCRIPTS / (name + ".py")
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_cli_lifecycle_and_score_boundaries(prepared, capsys):
    root, candidates, archive, plan = prepared
    manager = load_cli("manage-security-audit-benchmark")
    common = [
        "--root",
        str(root),
        "--candidates",
        str(candidates),
        "--answer-archive",
        str(archive),
    ]
    context = root / "context.json"
    context.write_bytes(corpus.canonical(plan["context"]))
    assert manager.main(["prepare-candidate", *common, "--context", str(context)]) == 0
    assert json.loads(capsys.readouterr().out)["candidate_id"] == plan["candidate_id"]
    for index in range(2):
        path = root / "terminal.json"
        path.write_bytes(corpus.canonical(terminal(plan, index)))
        assert (
            manager.main(
                [
                    "record-attempt",
                    *common,
                    "--candidate-id",
                    plan["candidate_id"],
                    "--terminal",
                    str(path),
                ]
            )
            == 0
        )
    for operation in ("score-candidate", "verify-candidate"):
        assert (
            manager.main([operation, *common, "--candidate-id", plan["candidate_id"]])
            == 0
        )
    assert (
        manager.main(
            [
                "render-report",
                *common,
                "--candidate-id",
                plan["candidate_id"],
                "--output",
                str(root / "report.md"),
            ]
        )
        == 0
    )
    assert (
        manager.main(["verify-candidate", *common, "--candidate-id", "../escape"]) == 2
    )
    capsys.readouterr()
    inputs = evidence(prepared)
    answers, mapping, plan, term, envelope = inputs
    sarif = reseal(term, envelope)
    paths = {}
    for name, value in zip(
        ("answers", "map", "plan", "terminal", "envelope", "sarif"),
        (answers, mapping, plan, term, envelope, sarif),
    ):
        path = root / ("score-" + name + ".json")
        path.write_bytes(corpus.canonical(value))
        paths[name] = path
    args = [
        "--root",
        str(root),
        "--subject-digest",
        plan["candidate_inputs"]["subject_manifest_digest"],
    ]
    args.extend(
        item for name, path in paths.items() for item in ("--" + name, str(path))
    )
    scorer = load_cli("score-security-audit")
    assert scorer.main(args) == 0
    assert json.loads(capsys.readouterr().out)["validity"] == "valid"
    paths["envelope"].write_text("{}")
    assert scorer.main(args) == 1
    assert json.loads(capsys.readouterr().out)["validity"] == "unscorable"
    paths["envelope"].write_text('{"bad":1,"bad":2}')
    assert scorer.main(args) == 2
    assert capsys.readouterr().out == ""
    rejected = manager.host_input(root, paths["envelope"], "envelope")
    assert isinstance(rejected, scoring.DecodeRejection)
    assert manager.host_input(root, None, "envelope") is None


@pytest.mark.parametrize("case", ["downgrade", "wrong_reason", "forbidden_not_scored"])
def test_rehashed_forged_outcome_still_fails_fresh_evaluator(prepared, case):
    root, candidates, archive, plan = prepared
    for index in range(2):
        inputs = evidence(prepared, index)
        term, envelope = inputs[-2:]
        if case == "wrong_reason":
            envelope["findings"][0]["language"] = None
        sarif = reseal(term, envelope)
        lifecycle.record(root, candidates, plan["candidate_id"], term, envelope, sarif)
    lifecycle.score_candidate(root, candidates, archive, plan["candidate_id"])
    directory = candidates / plan["candidate_id"]
    entries = lifecycle.ledger(root, directory, plan)
    base = directory / "attempts" / plan["attempts"][0]["id"]
    score = corpus.load(root, base / "score.json")
    outcome = corpus.load(root, base / "outcome.json")
    if case == "downgrade":
        score = scoring.unscorable("INVALID_OR_CROSS_BOUND_INPUT")
        outcome["validity"] = "unscorable"
    if case == "wrong_reason":
        score["reason_codes"] = ["REQUIRED_INDEX_UNAVAILABLE"]
    if case == "forbidden_not_scored":
        outcome["type"] = "not_scored"
        outcome["reason_code"] = "PRE_SCORING_UNAVAILABLE"
    outcome["input_output_digests"]["score"] = protocol.bytes_digest(score)
    (base / "score.json").write_bytes(corpus.canonical(score))
    (base / "outcome.json").write_bytes(corpus.canonical(outcome))
    entries[2]["payload_digests"] = {
        "score.json": protocol.bytes_digest(score),
        "outcome.json": protocol.bytes_digest(outcome),
    }
    for old_path in (directory / "ledger/entries").iterdir():
        old_path.unlink()
    previous = None
    for index, value in enumerate(entries):
        changed = lifecycle.entry(
            index, value["type"], value["id"], value["payload_digests"], plan, previous
        )
        (directory / "ledger/entries" / lifecycle.entry_name(changed)).write_bytes(
            corpus.canonical(changed)
        )
        previous = changed["entry_hash"]
    with pytest.raises(ValueError):
        lifecycle.verify(root, candidates, archive, plan["candidate_id"])


@pytest.mark.parametrize("name", ["raw-extra.json", "raw-extra.txt", "nested"])
def test_candidate_root_extras_fail_closed(prepared, name):
    root, candidates, archive, plan = prepared
    complete(prepared)
    path = candidates / plan["candidate_id"] / name
    if name == "nested":
        path.mkdir()
    else:
        path.write_text("untrusted")
    with pytest.raises(ValueError):
        lifecycle.verify(root, candidates, archive, plan["candidate_id"])


def test_characterization_integer_thresholds():
    assert scoring.metric(15, 16, 90)["state"] == "met"
    assert scoring.metric(14, 16, 90)["state"] == "not_met"
    assert scoring.metric(11, 12, 100)["state"] == "not_met"
    assert scoring.metric(0, 0, 100)["state"] == "unscorable"


def test_directory_creation_preserves_existing_parent_permissions(tmp_path, monkeypatch):
    parent = tmp_path / "existing"
    parent.mkdir()
    changed = []
    monkeypatch.setattr(lifecycle.safe, "_windows_owner_only", lambda path: changed.append(path))
    lifecycle.mkdir(tmp_path, parent / "new")
    assert parent not in changed and tmp_path not in changed
    lifecycle.mkdir(tmp_path, parent / "new")
    assert len(changed) <= 1


def test_caller_cannot_supply_evaluator_rejection(prepared):
    root, candidates, _archive, plan = prepared
    inputs = evidence(prepared)
    term, envelope = inputs[-2:]
    sarif = reseal(term, envelope)
    forged = {
        "schema": scoring.REJECTION_SCHEMA,
        "input_kind": "envelope",
        "input_digest": term["envelope_digest"],
        "reason_code": "NORMALIZED_ENVELOPE_REJECTED",
    }
    with pytest.raises(ValueError):
        lifecycle.record(root, candidates, plan["candidate_id"], term, forged, sarif)
    assert not lifecycle.ledger(root, candidates / plan["candidate_id"], plan)
    # Honest invalid JSON is a typed in-memory decoder result, not a JSON marker.
    invalid = scoring.DecodeRejection("envelope", "f" * 64)
    term["envelope_digest"] = "f" * 64
    lifecycle.record(root, candidates, plan["candidate_id"], term, invalid, sarif)
    assert len(lifecycle.ledger(root, candidates / plan["candidate_id"], plan)) == 1


@pytest.mark.parametrize(
    "mismatch", [None, "tool_id", "owner_id", "version_id", "config_digest", "verifier"]
)
def test_corrected_requires_equivalent_scanner_and_independent_verifier(
    prepared, mismatch
):
    inputs = evidence(prepared)
    envelope = inputs[-1]
    finding = envelope["findings"][0]
    template = copy.deepcopy(
        next(r for r in envelope["receipts"] if r["type"] == "host")
    )
    before = {
        **copy.deepcopy(template),
        "id": audit.opaque("before"),
        "type": "scanner",
        "owner_id": audit.opaque("scanner"),
        "tool_id": audit.opaque("scanner"),
    }
    after = {**copy.deepcopy(before), "id": audit.opaque("after")}
    if mismatch in {"tool_id", "owner_id", "version_id"}:
        after[mismatch] = audit.opaque("different")
    if mismatch == "config_digest":
        after[mismatch] = audit.digest("different")
    fix = {
        **copy.deepcopy(template),
        "id": audit.opaque("fix"),
        "type": "remediation",
        "before_receipt_id": before["id"],
        "after_receipt_id": after["id"],
        "finding_ids": [finding["id"]],
        "fixer_id": audit.opaque("fixer"),
    }
    verifier = {
        **copy.deepcopy(template),
        "id": audit.opaque("verifier"),
        "type": "verifier",
        "identity": audit.opaque("fixer" if mismatch == "verifier" else "independent"),
        "read_only": True,
    }
    envelope["receipts"].extend([before, after, fix, verifier])
    finding["evidence_receipt_ids"].append(before["id"])
    finding["disposition"] = "corrected"
    envelope["remediation"] = {
        "receipt_count": 1,
        "closure_state": "closed",
        "verifier_count": 1,
        "verifier_state": "self-attested",
    }
    result = scored(inputs)
    assert result["validity"] == ("valid" if mismatch is None else "unscorable"), result
