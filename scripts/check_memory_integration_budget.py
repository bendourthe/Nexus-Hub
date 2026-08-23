#!/usr/bin/env python3
"""Fail when the always-loaded memory integration prose exceeds its token budget.

The memory capability needs a block of instructions that every session loads
(read memory at startup; record entries while working). That block is paid on
every platform, forever, so it has a hard token ceiling declared in
``docs/policy/memory-substrate-contract.md``. This guard measures the block
and exits non-zero when it is over budget.

Token counting follows the ``nexus-context-compressor`` precedent: prefer
``tiktoken`` when it is already available locally, and degrade to a
deterministic stdlib estimate otherwise. The guard never requires a network
call and never downloads a vocab.

Repo-internal maintainer tooling: no ``.ps1`` sibling, no installer copy
step. Listed in ``DEV_ONLY_SCRIPTS`` in
``catalog/hooks/tests/test_installer_smoke.py``.

Usage:
    python scripts/check_memory_integration_budget.py
    python scripts/check_memory_integration_budget.py --path FILE --budget N
    python scripts/check_memory_integration_budget.py --text FILE

Exit codes:
    0 - the measured block is within the budget
    1 - the block is over budget, missing, or the budget is invalid
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

DEFAULT_PATH = "docs/policy/memory-integration-prose.md"
DEFAULT_BUDGET = 500

# Deterministic stdlib fallback: word runs and standalone punctuation.
# Same shape as extensions/nexus-context-compressor/src/nexus_context_compressor/tokens.py
# so the two cannot disagree on what "a token" is when tiktoken is absent.
_FALLBACK_TOKEN_RE = re.compile(r"\w+|[^\w\s]")


def estimate_tokens(text: str) -> int:
    """Deterministic, dependency-free token estimate."""
    if not text:
        return 0
    return len(_FALLBACK_TOKEN_RE.findall(text))


def count_tokens(text: str) -> tuple[int, str]:
    """Return (count, mode) preferring local tiktoken, else the stdlib estimate.

    A missing or unloadable tiktoken install is not an error. The function
    never opens a network connection.
    """
    if not text:
        return 0, "empty"
    try:
        import tiktoken
    except ImportError:
        return estimate_tokens(text), "stdlib"
    try:
        encoding = tiktoken.get_encoding("cl100k_base")
    except Exception:
        return estimate_tokens(text), "stdlib"
    return len(encoding.encode(text)), "tiktoken"


def check(path: Path, budget: int) -> list[str]:
    """Return a list of failure strings; empty means the file is in budget."""
    failures: list[str] = []
    if budget < 1:
        failures.append(f"BAD  budget must be a positive integer, got {budget}")
        return failures
    if not path.is_file():
        failures.append(f"MISS {path.as_posix()}: integration prose file not found")
        return failures
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        failures.append(f"MISS {path.as_posix()}: {exc}")
        return failures
    count, mode = count_tokens(text)
    if count > budget:
        failures.append(
            f"OVER {path.as_posix()}: {count} tokens ({mode}) exceeds budget {budget}"
        )
    return failures


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--root", default=".", help="Repository root.")
    parser.add_argument(
        "--path",
        default=DEFAULT_PATH,
        help=f"Repo-relative path of the integration prose (default {DEFAULT_PATH}).",
    )
    parser.add_argument(
        "--budget",
        type=int,
        default=DEFAULT_BUDGET,
        help=f"Token ceiling (default {DEFAULT_BUDGET}).",
    )
    parser.add_argument(
        "--text",
        default=None,
        help="Optional override file to measure instead of --path (for tests).",
    )
    args = parser.parse_args(argv)

    root = Path(args.root).resolve()
    relative = args.text if args.text is not None else args.path
    target = Path(relative)
    if not target.is_absolute():
        target = root / relative

    failures = check(target, args.budget)
    if failures:
        for line in failures:
            print(line, file=sys.stderr)
        return 1

    count, mode = count_tokens(target.read_text(encoding="utf-8"))
    print(f"OK   {target.as_posix()}: {count} tokens ({mode}) / {args.budget}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
