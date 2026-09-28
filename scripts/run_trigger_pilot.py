#!/usr/bin/env python3
"""Run the v4.13.0 Phase 6 trigger pilot against a real agent CLI.

The plan held Phase 6 because no execution path supplied five controls at once:
two model tiers, observed skill selection, bounded subprocess time, an
aggregate spend control, and the T022 isolation controls. The two
repository scripts named in the plan supply none of them -- `run_trigger_evals`
is model-free, and `optimize_skill_description` forces the skill with `--skill`
(which destroys the very thing the pilot measures) and has no timeout or cost
accounting.

This runner supplies the measurement controls by wrapping the CLI's structured output:

* `--model` selects the tier; the `init` event echoes what actually resolved.
* The `init` event enumerates loaded skills, and a skill invocation appears as a
  tool call in the stream, so ORGANIC selection is observable. Nothing forces a
  skill to load.
* `subprocess(timeout=)` bounds wall time; `--max-budget-usd` requests a per-call
  limit, but observed costs exceeded it in the second pilot.
* `result.total_cost_usd` is summed against a running ceiling, and the runner
  refuses to start another call after an observed overrun. This is not a hard
  aggregate ceiling until a provider-enforced or proven per-call bound exists.
* `--setting-sources`, `--add-dir` and `--strict-mcp-config` isolate the run.

The runner records an in-flight receipt before each call and stops after an
observed limit breach. A call whose selection evidence is missing
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
import os
import random
import re
import shutil
import subprocess
import sys
import tempfile
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path

# Frozen limits. The spend amount is a target until per-call enforcement is proven.
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
                cost = float(event.get("total_cost_usd"))
                if not math.isfinite(cost) or cost < 0:
                    raise ValueError("cost must be finite and nonnegative")
                out["cost_usd"] = cost
            except (TypeError, ValueError):
                # Unknown cost is charged at the reservation, never at zero.
                # This may still under-count an overrun, so it is not a hard cap.
                out["cost_usd"] = PER_CALL_BUDGET_USD
                out["note"] = "cost not reported; charged at the per-call budget"
            out["duration_ms"] = event.get("duration_ms")

    if not out["saw_result"]:
        out["cost_usd"] = PER_CALL_BUDGET_USD
        out["note"] = "result and cost not reported; charged at the per-call budget"

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
    """The aggregate pre-call reservation, conditional on a real per-call bound.

    Refuses to START a call whose reserved amount would breach the ceiling,
    rather than discovering the breach afterwards. The CLI's observed overrun means
    this reservation is not presently a hard ceiling.
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
                f"spend ceiling reservation would exceed target: spent {self.spent:.4f} "
                f"+ reservation {PER_CALL_BUDGET_USD:.2f} > {self.ceiling:.2f}"
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
        # charged at the per-call reservation, which may be below actual spend.
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
        result.note = "no result event; selection is unknown; cost charged at the per-call budget"
    else:
        result.status = "ok"
        result.note = parsed.get("note", "")
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


def write_receipt(path: Path, payload: dict) -> None:
    """Replace the on-disk result after each state change, never mid-write."""
    staged = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", newline="\n", prefix=path.name + ".",
            suffix=".tmp", dir=path.parent, delete=False,
        ) as stream:
            staged = Path(stream.name)
            json.dump(payload, stream, indent=2)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(staged, path)
    finally:
        if staged is not None:
            staged.unlink(missing_ok=True)


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

    # The frozen spend target is an upper configuration limit. argparse accepts
    # any float, so without this an operator could raise it from the command
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
            f"{MAX_SPEND_USD:.2f} configured maximum; using {ceiling:.2f}",
            file=sys.stderr,
        )

    if os.path.lexists(args.out):
        print(f"error: result receipt already exists: {args.out}", file=sys.stderr)
        return 2

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

    args.out.parent.mkdir(parents=True, exist_ok=True)

    def save_receipt(inflight: dict | None = None) -> None:
        write_receipt(args.out, {
            "seed": SEED,
            "ceiling_usd": ceiling,
            "calls_made": ledger.calls,
            "calls_planned": len(matrix),
            "total_spend_usd": round(ledger.spent, 4),
            "stopped_early": stopped,
            "complete": not stopped and inflight is None and ledger.calls == len(matrix),
            "inflight": inflight,
            "results": [asdict(r) for r in results],
        })

    save_receipt()

    for item in matrix:
        ok, why = ledger.may_start()
        if not ok:
            stopped = why
            break
        save_receipt({
            "call_number": ledger.calls + 1,
            "skill": item["skill"],
            "prompt_id": item["prompt_id"],
            "variant": item["variant"],
            "model_tier": item["model_tier"],
            "reserved_usd": PER_CALL_BUDGET_USD,
        })
        r = run_call(item, fixture, ledger, repo, variant_b)
        ledger.record(r.cost_usd)
        results.append(r)
        if r.cost_usd > PER_CALL_BUDGET_USD:
            stopped = (
                f"per-call budget exceeded: observed {r.cost_usd:.4f} "
                f"> reserved {PER_CALL_BUDGET_USD:.2f}"
            )
        save_receipt()
        print(
            f"  [{ledger.calls:2d}] {r.skill[:24]:24s} {r.variant} {r.model_tier:6s} "
            f"selected={r.selected} ${r.cost_usd:.4f} ({r.status})",
            flush=True,
        )
        if stopped:
            break

    save_receipt()

    print(f"\ncalls: {ledger.calls}/{len(matrix)}   spend: ${ledger.spent:.4f}")
    if stopped:
        print(f"STOPPED EARLY: {stopped}")
        print("Result is PARTIAL. Per the protocol this is UNMEASURED, not a finding.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
