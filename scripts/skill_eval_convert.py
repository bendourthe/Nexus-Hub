#!/usr/bin/env python3
"""Bidirectional converter between the eval-loop's internal evals.json format and
the interoperable behavioral-eval schema, for interop with external skill-eval
tooling.

The skill-eval-loop keeps a RICH internal eval format (see
catalog/skills/workflow/skill-eval-loop/references/schemas.md): a bare JSON list
of entries, each `{id, query, should_trigger, assertions:[{text}], tags?, turns?,
trigger_turn?, model?}`. That format carries trigger-discipline, multi-turn, and
per-eval-model signals the interoperable schema has no field for, so it stays the
source of truth. This converter maps it to and from the interoperable
behavioral-eval schema:

    {"skill_name": "<name>", "evals": [{"id", "prompt", "expected_output", "expectations": [str, ...]}]}

Field mapping:
    internal.query          <-> interop.prompt
    internal.assertions[].text <-> interop.expectations[]   (flattened to strings)
    (no internal equivalent) <-> interop.expected_output    (golden output; preserved verbatim)

Every internal field the interoperable schema cannot express (should_trigger,
tags, turns, trigger_turn, model, and any assertion keys beyond `text`) is stashed
under an `x_nexus` extension key on each interop eval. External tools ignore the
unknown key; this converter reads it back, so BOTH round-trips are lossless:

    internal -> interop -> internal  == internal
    interop  -> internal -> interop  == interop

Stdlib only (json, argparse, sys, pathlib); no third-party imports, no outbound
call, no new dependency. Cross-platform single .py (no .ps1 sibling needed),
matching the sibling eval scripts skill_eval_viewer.py / aggregate_benchmark.py /
optimize_skill_description.py.

Usage:
    python scripts/skill_eval_convert.py --to-interop evals.json --skill-name my-skill -o interop.json
    python scripts/skill_eval_convert.py --to-internal interop.json -o evals.json
    python scripts/skill_eval_convert.py --to-interop evals.json      # prints to stdout
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Extension namespace: where internal-only fields ride inside an interop eval so
# a round-trip loses nothing. Named generically; not tied to any external tool.
NEXUS_EXT_KEY = "x_nexus"

# Internal-entry keys that map to a dedicated interop field (so they are NOT
# duplicated into the extension namespace).
_MAPPED_INTERNAL_KEYS = frozenset({"id", "query", "assertions", "expected_output"})


def _assertions_to_expectations(assertions: list[dict]) -> list[str]:
    return [str(a.get("text", "")) for a in assertions]


def internal_entry_to_interop(entry: dict) -> dict:
    """Map one internal eval entry to one interoperable eval object (lossless)."""
    assertions = entry.get("assertions", []) or []
    out: dict = {
        "id": entry.get("id", ""),
        "prompt": entry.get("query", ""),
        "expected_output": entry.get("expected_output", ""),
        "expectations": _assertions_to_expectations(assertions),
    }
    # Stash every internal-only field (should_trigger, tags, turns, trigger_turn,
    # model, ...) under the extension namespace.
    ext = {k: v for k, v in entry.items() if k not in _MAPPED_INTERNAL_KEYS}
    # If any assertion carries keys beyond `text`, the flattened `expectations`
    # would lose them; stash the full assertion objects so import restores them.
    if any(set(a.keys()) - {"text"} for a in assertions):
        ext["assertions"] = assertions
    if ext:
        out[NEXUS_EXT_KEY] = ext
    return out


def interop_entry_to_internal(evalobj: dict) -> dict:
    """Map one interoperable eval object back to one internal eval entry (lossless)."""
    ext = dict(evalobj.get(NEXUS_EXT_KEY, {}))
    if "assertions" in ext:
        assertions = ext.pop("assertions")
    else:
        assertions = [{"text": t} for t in evalobj.get("expectations", [])]
    entry: dict = {
        "id": evalobj.get("id", ""),
        "query": evalobj.get("prompt", ""),
        "assertions": assertions,
    }
    # Restore internal-only fields (should_trigger, tags, turns, trigger_turn, ...).
    for key, value in ext.items():
        entry[key] = value
    # Preserve a golden expected_output only when the interop file carried one, so
    # an interop -> internal -> interop round-trip is lossless. Internal evals
    # authored in-repo never set it.
    expected_output = evalobj.get("expected_output", "")
    if expected_output:
        entry["expected_output"] = expected_output
    return entry


def internal_to_interop(evals_list: list, skill_name: str = "") -> dict:
    """Convert a bare internal evals list to the interoperable schema object."""
    if not isinstance(evals_list, list):
        raise ValueError("internal evals.json must be a JSON list of eval entries")
    return {
        "skill_name": skill_name,
        "evals": [internal_entry_to_interop(e) for e in evals_list],
    }


def interop_to_internal(interop_obj: dict) -> tuple[str, list]:
    """Convert an interoperable schema object to (skill_name, internal evals list)."""
    if not isinstance(interop_obj, dict) or "evals" not in interop_obj:
        raise ValueError(
            "interoperable evals must be a JSON object with a top-level 'evals' array"
        )
    skill_name = str(interop_obj.get("skill_name", ""))
    internal = [interop_entry_to_internal(e) for e in interop_obj["evals"]]
    return skill_name, internal


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(
        description="Convert eval-loop evals.json to/from the interoperable "
                    "behavioral-eval schema",
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--to-interop",
        type=Path,
        metavar="EVALS_JSON",
        help="Convert an internal evals.json (bare list) to the interoperable schema",
    )
    group.add_argument(
        "--to-internal",
        type=Path,
        metavar="INTEROP_JSON",
        help="Convert an interoperable-schema file to an internal evals.json (bare list)",
    )
    parser.add_argument(
        "--skill-name",
        default="",
        help="skill_name to stamp on the interoperable output (--to-interop only)",
    )
    parser.add_argument(
        "-o", "--out",
        type=Path,
        default=None,
        help="Write the result here (default: stdout)",
    )
    args = parser.parse_args()

    src = args.to_interop or args.to_internal
    try:
        data = json.loads(src.read_text(encoding="utf-8"))
    except OSError as exc:
        print(f"ERROR: cannot read {src}: {exc}", file=sys.stderr)
        return 1
    except ValueError as exc:
        print(f"ERROR: {src} is not valid JSON: {exc}", file=sys.stderr)
        return 1

    try:
        if args.to_interop is not None:
            result: object = internal_to_interop(data, args.skill_name)
        else:
            skill_name, internal = interop_to_internal(data)
            if skill_name:
                print(f"skill_name: {skill_name}", file=sys.stderr)
            result = internal
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    rendered = json.dumps(result, indent=2, ensure_ascii=False) + "\n"
    if args.out is not None:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(rendered, encoding="utf-8")
        print(f"Wrote {args.out}", file=sys.stderr)
    else:
        sys.stdout.write(rendered)
    return 0


if __name__ == "__main__":
    sys.exit(main())
