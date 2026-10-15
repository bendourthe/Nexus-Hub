"""Manage an observational benchmark ledger without launching any audit tools."""

from __future__ import annotations

import argparse
import hashlib
import sys
from pathlib import Path

import _benchmark_corpus as corpus
import _benchmark_lifecycle as lifecycle
import _safe_artifact as safe
import _strict_json as strict


def host_input(root: Path, path: Path, kind: str) -> dict | None:
    if path is None:
        return None
    payload = safe.open_contained_bytes(root, path, strict.MAX_BYTES)
    try:
        return strict.loads(payload)
    except strict.StrictJSONError:
        return lifecycle.scoring.DecodeRejection(
            kind, hashlib.sha256(payload).hexdigest()
        )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "operation",
        choices=(
            "prepare-candidate",
            "record-attempt",
            "score-candidate",
            "verify-candidate",
            "render-report",
        ),
    )
    parser.add_argument("--root", required=True, type=Path)
    parser.add_argument("--candidates", required=True, type=Path)
    parser.add_argument("--answer-archive", required=True, type=Path)
    parser.add_argument("--candidate-id")
    parser.add_argument("--supersedes")
    parser.add_argument("--change-reason", default="INITIAL")
    for name in ("context", "terminal", "envelope", "sarif", "output"):
        parser.add_argument(
            "--" + name, type=lambda value: lifecycle.filesystem_path(Path(value))
        )
    args = parser.parse_args(argv)
    try:
        root = lifecycle.filesystem_path(args.root)
        candidates = safe.assert_no_reparse_in_chain(
            root, lifecycle.filesystem_path(args.candidates)
        )
        archive = safe.assert_no_reparse_in_chain(
            root, lifecycle.filesystem_path(args.answer_archive)
        )
        if args.operation == "prepare-candidate":
            plan = lifecycle.prepare(
                root,
                candidates,
                archive,
                corpus.load(root, args.context),
                supersedes=args.supersedes,
                reason=args.change_reason,
            )
            result = {
                "candidate_id": plan["candidate_id"],
                "plan_digest": plan["plan_digest"],
                "state": "prepared",
            }
        elif args.operation == "record-attempt":
            lifecycle.record(
                root,
                candidates,
                args.candidate_id,
                corpus.load(root, args.terminal),
                host_input(root, args.envelope, "envelope"),
                host_input(root, args.sarif, "sarif"),
            )
            result = {"candidate_id": args.candidate_id, "state": "terminal_recorded"}
        elif args.operation == "score-candidate":
            lifecycle.score_candidate(root, candidates, archive, args.candidate_id)
            result = {"candidate_id": args.candidate_id, "state": "outcomes_recorded"}
        elif args.operation == "verify-candidate":
            lifecycle.verify(root, candidates, archive, args.candidate_id)
            result = {
                "candidate_id": args.candidate_id,
                "state": "verified",
                "entries": 4,
            }
        else:
            lifecycle.render(root, candidates, archive, args.candidate_id, args.output)
            result = {"candidate_id": args.candidate_id, "state": "rendered"}
    except (
        ValueError,
        TypeError,
        KeyError,
        AttributeError,
        OSError,
        safe.UnsafeArtifactError,
        strict.StrictJSONError,
    ):
        print("BENCHMARK_LIFECYCLE_REJECTED", file=sys.stderr)
        return 2
    sys.stdout.buffer.write(corpus.canonical(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
