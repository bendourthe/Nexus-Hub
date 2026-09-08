"""Score explicit, physically contained normalized audit inputs without execution."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import _benchmark_corpus as corpus
import _benchmark_protocol as protocol
from _benchmark_scoring import score
from _safe_artifact import UnsafeArtifactError
from _strict_json import StrictJSONError


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", required=True, type=Path)
    for name in ("answers", "map", "plan", "terminal", "envelope", "sarif"):
        parser.add_argument("--" + name, required=True, type=Path)
    parser.add_argument("--subject-digest", required=True)
    args = parser.parse_args(argv)
    try:
        values = {
            name: protocol.read_input(args.root, getattr(args, name))
            for name in ("answers", "map", "plan", "terminal", "envelope", "sarif")
        }
        result = score(
            values["answers"],
            values["map"],
            values["plan"],
            args.subject_digest,
            values["terminal"],
            values["envelope"],
            values["sarif"],
        )
    except (ValueError, TypeError, OSError, UnsafeArtifactError, StrictJSONError):
        print("BENCHMARK_INPUT_REJECTED", file=sys.stderr)
        return 2
    sys.stdout.buffer.write(corpus.canonical(result))
    return 0 if result["validity"] == "valid" else 1


if __name__ == "__main__":
    raise SystemExit(main())
