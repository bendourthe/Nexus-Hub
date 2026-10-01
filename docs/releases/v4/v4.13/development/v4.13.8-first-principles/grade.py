"""Grade the v4.13.8 first-principles pilot runs and recompute the per-arm rates (T323).

Scaffolding, never shipped. The grader sees only (prompt_id, final answer text): the arm label
is removed before grading and re-attached only to aggregate. No LLM grader. An errored or
empty run is a non-pass, never dropped.

Usage:
    python grade.py          # prints per-run verdicts, the per-prompt table, and per-arm rates
"""
from __future__ import annotations

import json
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
EVALS = HERE / "evals" / "bug-localization.json"
RUNS = HERE / "runs"
ARMS = ("baseline", "first-principles", "control")
_LINE = re.compile(r"^\s*ROOT CAUSE:\s*(.+?)\s*$", re.MULTILINE)


def normalize(name: str) -> str:
    return name.strip().strip("`*").replace("()", "").rstrip(".").strip("`*").strip().lower()


def grade(prompt_id: str, answer: str | None, references: dict[str, str]) -> dict:
    """Blind grade: both assertions must hold for a pass."""
    matches = _LINE.findall(answer or "")
    present = bool(matches)
    named = normalize(matches[-1]) if present else None
    equals = present and named == references[prompt_id].lower()
    return {"root_cause_line_present": present, "named": named,
            "root_cause_equals": equals, "pass": present and equals}


def main() -> int:
    data = json.loads(EVALS.read_text(encoding="utf-8"))
    refs = {p["id"]: p["reference_root_cause"] for p in data["prompts"]}
    table: dict[str, dict[str, str]] = {pid: {} for pid in refs}
    for path in sorted(RUNS.glob("*.json")):
        run = json.loads(path.read_text(encoding="utf-8"))
        answer = None if run["errored"] else (run["cli_output"] or {}).get("result")
        verdict = grade(run["prompt_id"], answer, refs)  # arm label not passed in
        table[run["prompt_id"]][run["arm"]] = "pass" if verdict["pass"] else "fail"
        print(f"{run['cell']}: named={verdict['named']} pass={verdict['pass']}")
    print("\n| Prompt | " + " | ".join(ARMS) + " |")
    print("|---|" + "---|" * len(ARMS))
    for pid in refs:
        print(f"| {pid} | " + " | ".join(table[pid].get(a, "not run") for a in ARMS) + " |")
    print()
    for arm in ARMS:
        ran = [t[arm] for t in table.values() if arm in t]
        passed = sum(1 for v in ran if v == "pass")
        print(f"{arm}: {passed}/{len(ran)} run, {len(refs) - len(ran)} not run")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
