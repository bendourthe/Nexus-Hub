"""Record two declared unavailable-tool attempts without launching source or hosts."""

from __future__ import annotations

import argparse
import hashlib
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[6]
sys.path.insert(0, str(ROOT / "catalog/skills/code-review/security-review/scripts"))
import _audit_envelope as audit
import _benchmark_corpus as corpus
import _benchmark_lifecycle as lifecycle
import _benchmark_protocol as protocol
import _safe_artifact as safe
import _target_manifest as target


def now() -> datetime:
    return datetime.now(timezone.utc).replace(microsecond=0)


def run(
    root: Path,
    context_path: Path,
    registration_path: Path,
    supersedes: str | None = None,
) -> dict:
    root, context_path, registration_path = map(
        corpus.filesystem_path, (root, context_path, registration_path)
    )
    observed_registration = corpus.load(root, registration_path)
    protocol.require(
        observed_registration
        == {"registered_code_search_tools": [], "state": "UNAVAILABLE"}
    )
    snapshot = corpus.load(root, context_path)
    protocol.require(
        snapshot["registration_digest"] == audit.digest(observed_registration)
    )
    candidates = (
        root / "docs/releases/v4/v4.9/development/security-audit-benchmark/candidates"
    )
    archive = root / ".nexus/security-audit-answers"
    plan = lifecycle.prepare(
        root,
        candidates,
        archive,
        snapshot,
        supersedes=supersedes,
        reason="SUBJECT_CHANGED" if supersedes else "INITIAL",
    )
    directory = candidates / plan["candidate_id"]
    answers = corpus.load(root, root / lifecycle.ANSWERS)
    mapping = corpus.load(root, archive / (plan["candidate_id"] + ".json"))
    routing = corpus.load(root, root / lifecycle.ROUTING)
    for index, declared in enumerate(plan["attempts"]):
        entries = lifecycle.ledger(root, directory, plan)
        if len(entries) > index:
            continue
        terminal_path = directory / "attempts" / declared["id"] / "terminal.json"
        if terminal_path.exists():
            # Recover a fully published terminal without repeating observation.
            lifecycle.record(
                root, candidates, plan["candidate_id"], corpus.load(root, terminal_path)
            )
            continue
        started = now()
        with corpus.projection(
            root / lifecycle.SOURCE, answers, plan["candidate_id"], mapping
        ) as projected:
            source = projected.source_root
            cache, artifacts, index_root = (
                source.parent / name for name in ("cache", "artifacts", "index")
            )
            for path in (cache, artifacts, index_root):
                path.mkdir(mode=0o700)
            before = target.build_target_manifest(source)
            rows, owners = lifecycle.route_projection(source, routing)
            protocol.require(
                rows == plan["routing_expectations"]
                and owners == plan["required_owners"]
            )
            after = target.build_target_manifest(source)
            protocol.require(before == after)
            bind = {
                "candidate_id": plan["candidate_id"],
                "attempt_id": declared["id"],
                "mode": declared["mode"],
                "workers": declared["workers"],
                "context_digest": audit.digest(snapshot),
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
                "root_fingerprint": before["target_root_fingerprint"],
                "scope_fingerprint": audit.digest([]),
                "content_manifest": before["manifest_digest"],
                "index_digest": None,
                "cache_fingerprint": hashlib.sha256(str(cache).encode()).hexdigest(),
                "artifacts_fingerprint": hashlib.sha256(
                    str(artifacts).encode()
                ).hexdigest(),
                "routing_digest": snapshot["routing_digest"],
            }
        protocol.require(not source.parent.exists())
        finished = now()
        receipt = {
            "started_at": started.isoformat().replace("+00:00", "Z"),
            "finished_at": finished.isoformat().replace("+00:00", "Z"),
            "duration_ms": int((finished - started).total_seconds() * 1000),
            "binding_digest": audit.digest(bind),
            "context_digest": bind["context_digest"],
            "mode": declared["mode"],
            "workers": declared["workers"],
            "state": "UNAVAILABLE",
            "code_search": "UNAVAILABLE",
            "registration_digest": snapshot["registration_digest"],
            "process_attestation": "none",
            "producer_run_fingerprint": None,
        }
        terminal = {
            "schema": protocol.VERSION,
            "candidate_id": plan["candidate_id"],
            "attempt_id": declared["id"],
            "mode": declared["mode"],
            "workers": declared["workers"],
            "state": "UNAVAILABLE",
            "code_search": "UNAVAILABLE",
            "binding": bind,
            "receipt": receipt,
            "envelope_digest": None,
            "sarif_digest": None,
            "producer_run_fingerprint": None,
            "declared_inputs_digest": audit.digest(
                {
                    "projection_digest": plan["projection_digest"],
                    "context_digest": bind["context_digest"],
                    "attempt_id": declared["id"],
                }
            ),
            "cleanup": "complete",
            "original_source_digest": audit.digest(
                corpus.snapshot(root / lifecycle.SOURCE, answers)
            ),
        }
        lifecycle.record(root, candidates, plan["candidate_id"], terminal)
    lifecycle.score_candidate(root, candidates, archive, plan["candidate_id"])
    verified = lifecycle.verify(root, candidates, archive, plan["candidate_id"])
    report_path = root / "docs/releases/v4/v4.9/development/security-audit-benchmark.md"
    lifecycle.render(root, candidates, archive, plan["candidate_id"], report_path)
    return {
        "candidate_id": plan["candidate_id"],
        "entries": len(verified["entries"]),
        "outcomes": [r["outcome"]["reason_code"] for r in verified["outcomes"]],
        "cleanup": "complete",
        "original_source_unchanged": True,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--context", type=Path, required=True)
    parser.add_argument("--registration", type=Path, required=True)
    parser.add_argument("--supersedes")
    args = parser.parse_args(argv)
    try:
        result = run(args.root, args.context, args.registration, args.supersedes)
    except (ValueError, TypeError, OSError, safe.UnsafeArtifactError):
        print("BENCHMARK_OBSERVATION_REJECTED", file=sys.stderr)
        return 2
    sys.stdout.buffer.write(corpus.canonical(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
