#!/usr/bin/env python3
"""Qualify an ephemeral source-only projection; never execute its source files."""

import argparse
import json
import sys
from pathlib import Path

import _benchmark_corpus as corpus


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--answers", type=Path, required=True)
    parser.add_argument("--candidate-id", required=True)
    args = parser.parse_args()
    try:
        root = args.root.absolute()
        source = corpus.safe.assert_no_reparse_in_chain(root, args.source)
        answers = corpus.load(root, args.answers)
        with corpus.projection(source, answers, args.candidate_id) as result:
            roots = (result.source_root.parent, result.answer_root)
            output = {
                "projection_digest": result.mapping["projection_digest"],
                "map_digest": result.mapping["map_digest"],
                "source_digest": result.mapping["source_digest"],
                "file_count": len(result.public_manifest),
                "answer_excluded_from_declared_inputs": True,
                "process_attestation": "none",
            }
        corpus.require(not any(path.exists() for path in roots))
        output["cleanup"] = "complete"
    except (ValueError, TypeError, KeyError, OSError):
        print('{"error":"benchmark_projection_invalid"}', file=sys.stderr)
        return 2
    print(json.dumps(output, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
