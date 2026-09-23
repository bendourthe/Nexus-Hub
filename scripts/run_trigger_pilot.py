#!/usr/bin/env python3
"""Run the v4.13.0 Phase 6 trigger pilot against a real agent CLI.

The plan held Phase 6 because no execution path supplied five controls at once:
two model tiers, observed skill selection, bounded subprocess time, an
ENFORCEABLE AGGREGATE spend ceiling, and the T022 isolation controls. The two
repository scripts named in the plan supply none of them -- `run_trigger_evals`
is model-free, and `optimize_skill_description` forces the skill with `--skill`
(which destroys the very thing the pilot measures) and has no timeout or cost
accounting.

This runner supplies all five by wrapping the CLI's own structured output:

* `--model` selects the tier; the `init` event echoes what actually resolved.
* The `init` event enumerates loaded skills, and a skill invocation appears as a
  tool call in the stream, so ORGANIC selection is observable. Nothing forces a
  skill to load.
* `subprocess(timeout=)` bounds wall time; `--max-budget-usd` bounds one call.
* `result.total_cost_usd` is summed against a running ceiling, and the runner
  refuses to START a call once the projected total would exceed it. That is the
  aggregate control the plan required and no existing tool provided.
* `--setting-sources`, `--add-dir` and `--strict-mcp-config` isolate the run.

Every cap is fail-closed: the runner stops and records a partial, honest result
rather than continuing past a limit. A call whose selection evidence is missing
is recorded as evidence-missing, never as a non-selection, because "the skill
did not load" and "we could not see whether it loaded" are different findings
and only one of them is a measurement.

Usage::

    python scripts/run_trigger_pilot.py --protocol <dir> --out <results.json>
    python scripts/run_trigger_pilot.py ... --calibrate 4   # slice first

Exit codes: 0 completed (possibly partial, recorded as such), 2 refused to start.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import random
import re
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass, field, asdict
from pathlib import Path

# Frozen caps. These mirror the protocol document; the runner does not invent them.
MAX_CALLS = 96
MAX_SPEND_USD = 35.00
PER_CALL_BUDGET_USD = 0.50
PER_CALL_TIMEOUT_S = 180
TOTAL_WALL_S = 120 * 60
SEED = 4131

FIXTURE_MARKER = ".nexus-pilot-fixture"

MODELS = {"fast": "claude-haiku-4-5-20251001", "strong": "claude-opus-5"}

SKILLS = {
    "plan-before-code": "workflow/plan-before-code",
    "html-output-conventions": "developer-experience/html-output-conventions",
    "skill-description-authoring": "developer-experience/skill-description-authoring",
    "context-engineering": "ai-development/context-engineering",
}


@dataclass
class CallResult:
    """One invocation. Absent evidence is recorded, never inferred."""

    skill: str
    prompt_id: str
    prompt_class: str
    variant: str
    model_tier: str
    model_id: str = ""
    selected: bool | None = None  # None => evidence missing, NOT a non-selection
    tools_used: list[str] = field(default_factory=list)
    skill_selectors: list[dict[str, str]] = field(default_factory=list)
    skills_available: int | None = None
    num_turns: int | None = None
    cost_usd: float = 0.0
    duration_ms: int | None = None
    status: str = "pending"
    note: str = ""
    corpus_hashes: dict = field(default_factory=dict)


def parse_stream(raw: str, skill: str) -> dict:
    """Read the structured stream. Returns what was OBSERVED, not what is assumed."""
    out: dict = {
        "selected": None,
        "tools_used": [],
        "skill_selectors": [],
        "skills_available": None,
        "num_turns": None,
        "cost_usd": 0.0,
        "duration_ms": None,
        "model_id": "",
        "saw_result": False,
        "clean_result": False,
    }
    for line in raw.splitlines():
        line = line.strip()
        if not line.startswith("{"):
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue

        if event.get("subtype") == "init":
            out["model_id"] = event.get("model", "")
            skills = event.get("skills")
            if isinstance(skills, list):
                out["skills_available"] = len(skills)

        # A skill invocation is a tool call; this is the organic-selection signal.
        if event.get("type") == "assistant":
            for block in (event.get("message", {}) or {}).get("content", []) or []:
                if isinstance(block, dict) and block.get("type") == "tool_use":
                    name = block.get("name", "")
                    out["tools_used"].append(name)
                    if name == "Skill":
                        selectors = _skill_selectors(block.get("input", {}))
                        out["skill_selectors"].append(selectors)
                        if skill in selectors.values():
                            out["selected"] = True

        if event.get("type") == "result":
            out["saw_result"] = True
            out["clean_result"] = not event.get("is_error") and not str(
                event.get("subtype", "")
            ).startswith("error")
            out["num_turns"] = event.get("num_turns")
            try:
                out["cost_usd"] = float(event.get("total_cost_usd"))
            except (TypeError, ValueError):
                # Unknown cost is charged at the worst case, never at zero: a
                # ledger that under-counts spend permits more of it.
                out["cost_usd"] = PER_CALL_BUDGET_USD
                out["note"] = "cost not reported; charged at the per-call budget"
            out["duration_ms"] = event.get("duration_ms")

    # Only a CLEANLY completed run licenses "the skill was not selected". A run
    # the per-call budget truncated never got the chance to invoke the skill, so
    # it is evidence-missing, not a measured non-selection.
    if out["selected"] is None and out["saw_result"] and out["clean_result"]:
        out["selected"] = False
    return out


def _skill_selectors(tool_input: object) -> dict[str, str]:
    """Retain only bounded skill names, never other tool arguments.

    The first scorer matched a substring across the full input and counted a
    different skill's prompt mention as selection. This record is enough to
    re-score each future row without retaining that prompt or other payload.
    """
    if not isinstance(tool_input, dict):
        return {}
    selectors = {}
    for key in ("command", "skill", "name"):
        if key not in tool_input:
            continue
        value = tool_input[key]
        normalized = value.strip().lstrip("/") if isinstance(value, str) else ""
        selectors[key] = (
            normalized
            if len(normalized) <= 64 and re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", normalized)
            else "<invalid>"
        )
    return selectors


def stage_variant(variant: str, fixture: Path, repo: Path, variant_b: dict) -> dict[str, str]:
    """Write the four sampled skills into the fixture's PROJECT skills directory.

    This is what makes the experiment an experiment. Both arms must differ only
    in the instruction bundle, so each call stages its own corpus: variant A is
    the skill verbatim, variant B replaces only its `description:` line. Running
    both arms against one unchanged corpus would compare A with A and produce a
    confident null result that measured nothing.

    Project skills are used (not the user's installed copy) so the corpus under
    test is the fixture's, and the user's own catalog cannot leak into a result.
    """
    skills_root = fixture / ".claude" / "skills"
    if skills_root.exists():
        # Only ever remove a directory this runner created. `--fixture .` inside
        # a real project would otherwise delete that project's skills.
        if not (fixture / FIXTURE_MARKER).is_file():
            raise SystemExit(
                f"refusing to clear {skills_root}: {fixture} carries no "
                f"{FIXTURE_MARKER} marker, so it is not a runner-owned fixture"
            )
        shutil.rmtree(skills_root)
    hashes: dict[str, str] = {}
    for name, rel in SKILLS.items():
        source = (repo / "catalog" / "skills" / rel / "SKILL.md").read_text(encoding="utf-8")
        if variant == "B":
            replacement = variant_b["descriptions"][name].replace("\\", "\\\\")
            source, substitutions = re.subn(
                r"^description:.*$",
                "description: " + replacement,
                source,
                count=1,
                flags=re.M,
            )
            # A silent no-op here is the worst failure this runner has: both arms
            # would be identical and the null result would measure nothing while
            # looking exactly like a real one.
            if substitutions != 1:
                raise SystemExit(
                    f"variant B staging failed for {name}: matched "
                    f"{substitutions} description lines, expected exactly 1"
                )
        dest = skills_root / name
        dest.mkdir(parents=True, exist_ok=True)
        (dest / "SKILL.md").write_text(source, encoding="utf-8")
        hashes[name] = hashlib.sha256(source.encode("utf-8")).hexdigest()[:16]
    return hashes


def build_command(prompt: str, model: str, fixture: Path) -> list[str]:
    """Isolated, budgeted, observable. Nothing here forces a skill to load.

    `--setting-sources project` makes the fixture's staged corpus the one under
    test and keeps the user's installed catalog out of the measurement.
    """
    return [
        "claude",
        "-p",
        prompt,
        "--model",
        model,
        "--output-format",
        "stream-json",
        "--verbose",
        "--max-budget-usd",
        str(PER_CALL_BUDGET_USD),
        "--setting-sources",
        "project",
        "--strict-mcp-config",
        "--add-dir",
        str(fixture),
    ]


class Ledger:
    """The aggregate spend control the plan required.

    Refuses to START a call whose worst case would breach the ceiling, rather
    than discovering the breach afterwards. That asymmetry is the point: a
    ceiling checked only after spending is a report, not a control.
    """

    def __init__(self, ceiling: float, max_calls: int, wall_s: int) -> None:
        self.ceiling = ceiling
        self.max_calls = max_calls
        self.wall_s = wall_s
        self.spent = 0.0
        self.calls = 0
        self.started = time.monotonic()

    def may_start(self) -> tuple[bool, str]:
        if self.calls >= self.max_calls:
            return False, f"call cap reached ({self.max_calls})"
        if time.monotonic() - self.started > self.wall_s:
            return False, f"wall-clock cap reached ({self.wall_s}s)"
        if self.spent + PER_CALL_BUDGET_USD > self.ceiling:
            return False, (
                f"spend ceiling would be breached: spent {self.spent:.4f} "
                f"+ worst case {PER_CALL_BUDGET_USD:.2f} > {self.ceiling:.2f}"
            )
        return True, ""

    def record(self, cost: float) -> None:
        self.spent += cost
        self.calls += 1


def run_call(item: dict, fixture: Path, ledger: Ledger, repo: Path, variant_b: dict) -> CallResult:
    model_id = MODELS[item["model_tier"]]
    result = CallResult(
        skill=item["skill"],
        prompt_id=item["prompt_id"],
        prompt_class=item["prompt_class"],
        variant=item["variant"],
        model_tier=item["model_tier"],
        model_id=model_id,
    )
    result.corpus_hashes = stage_variant(item["variant"], fixture, repo, variant_b)
    cmd = build_command(item["prompt"], model_id, fixture)
    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=PER_CALL_TIMEOUT_S,
            check=False,
            cwd=str(fixture),
        )
    except subprocess.TimeoutExpired as exc:
        result.status = "timeout"
        # A timed-out call still spent money. Recording 0.0 would let the
        # aggregate ceiling permit more than it believes it has allowed, so the
        # cost is read from whatever the stream managed to emit and otherwise
        # charged at the per-call worst case.
        partial = exc.stdout or ""
        if isinstance(partial, bytes):
            partial = partial.decode("utf-8", errors="replace")
        observed = parse_stream(partial, item["skill"])
        result.cost_usd = observed["cost_usd"] or PER_CALL_BUDGET_USD
        result.tools_used = observed["tools_used"]
        result.skill_selectors = observed["skill_selectors"]
        result.note = (
            f"exceeded {PER_CALL_TIMEOUT_S}s; charged {result.cost_usd:.4f} "
            "(observed, else the per-call budget). Selection is unknown."
        )
        return result

    parsed = parse_stream(proc.stdout, item["skill"])
    result.selected = parsed["selected"]
    result.tools_used = parsed["tools_used"]
    result.skill_selectors = parsed["skill_selectors"]
    result.skills_available = parsed["skills_available"]
    result.num_turns = parsed["num_turns"]
    result.cost_usd = parsed["cost_usd"]
    result.duration_ms = parsed["duration_ms"]
    result.model_id = parsed["model_id"] or model_id

    if not parsed["saw_result"]:
        result.status = "evidence-missing"
        result.note = "no result event; selection is unknown, not negative"
    else:
        result.status = "ok"
    return result


def load_matrix(protocol_dir: Path) -> list[dict]:
    path = protocol_dir / "pilot-prompts.json"
    if not path.is_file():
        raise SystemExit(f"missing frozen prompt set: {path}")
    prompts = json.loads(path.read_text(encoding="utf-8"))["prompts"]
    matrix = [
        {**p, "variant": v, "model_tier": t}
        for p in prompts
        for v in ("A", "B")
        for t in ("fast", "strong")
    ]
    random.Random(SEED).shuffle(matrix)  # seeded: order recorded, not incidental
    return matrix


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--protocol", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--fixture", type=Path, default=Path("./.pilot-fixture"))
    ap.add_argument("--calibrate", type=int, default=0, help="run only N calls")
    ap.add_argument("--ceiling", type=float, default=MAX_SPEND_USD)
    args = ap.parse_args(argv)

    if not shutil.which("claude"):
        print("error: the claude CLI is not on PATH; refusing to start", file=sys.stderr)
        return 2

    # The frozen ceiling is a cap, not a default. argparse accepts any float, so
    # without this an operator could raise the "frozen" limit from the command
    # line, and a non-finite value would disable the spend check entirely:
    # every comparison against nan is False, so the branch simply never fires.
    if not math.isfinite(args.ceiling) or args.ceiling <= 0:
        print(
            f"error: --ceiling must be a positive finite number, got {args.ceiling!r}",
            file=sys.stderr,
        )
        return 2
    ceiling = min(args.ceiling, MAX_SPEND_USD)
    if ceiling < args.ceiling:
        print(
            f"note: --ceiling {args.ceiling:.2f} exceeds the frozen "
            f"{MAX_SPEND_USD:.2f} cap; using {ceiling:.2f}",
            file=sys.stderr,
        )

    fixture = args.fixture.resolve()
    fixture.mkdir(parents=True, exist_ok=True)
    # Mark the fixture as runner-owned so staging may clear it later.
    (fixture / FIXTURE_MARKER).write_text(
        "Created by scripts/run_trigger_pilot.py. Safe to delete.\n", encoding="utf-8"
    )

    repo = Path(__file__).resolve().parents[1]
    variant_b = json.loads((args.protocol / "pilot-variant-b.json").read_text(encoding="utf-8"))
    matrix = load_matrix(args.protocol)
    if args.calibrate:
        matrix = matrix[: args.calibrate]

    ledger = Ledger(ceiling, MAX_CALLS, TOTAL_WALL_S)
    results: list[CallResult] = []
    stopped = ""

    for item in matrix:
        ok, why = ledger.may_start()
        if not ok:
            stopped = why
            break
        r = run_call(item, fixture, ledger, repo, variant_b)
        ledger.record(r.cost_usd)
        results.append(r)
        print(
            f"  [{ledger.calls:2d}] {r.skill[:24]:24s} {r.variant} {r.model_tier:6s} "
            f"selected={r.selected} ${r.cost_usd:.4f} ({r.status})",
            flush=True,
        )

    payload = {
        "seed": SEED,
        "ceiling_usd": ceiling,
        "calls_made": ledger.calls,
        "calls_planned": len(matrix),
        "total_spend_usd": round(ledger.spent, 4),
        "stopped_early": stopped,
        "complete": not stopped and ledger.calls == len(matrix),
        "results": [asdict(r) for r in results],
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    print(f"\ncalls: {ledger.calls}/{len(matrix)}   spend: ${ledger.spent:.4f}")
    if stopped:
        print(f"STOPPED EARLY: {stopped}")
        print("Result is PARTIAL. Per the protocol this is UNMEASURED, not a finding.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
