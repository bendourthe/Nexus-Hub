#!/usr/bin/env python3
"""Iteratively optimize a Nexus-Hub skill's `description` frontmatter field.

The optimizer evaluates the current description on a 60/40 train-test split
of an eval set, asks the chosen CLI to PROPOSE 3 candidate rewrites based on
which train queries failed, evaluates each candidate on train AND held-out
test, and selects the winner by held-out test score (NOT train) - the rule
that prevents overfitting to the candidate-generation prompt.

Schema and rationale: catalog/skills/workflow/skill-eval-loop/references/
description-optimizer.md

CLI dispatch follows the v1.1.3 four-hook precedent: a single dispatcher
file with a hard `assert cli in {claude, gemini, codex, opencode}` and per-CLI
branches that only invoke their matching CLI binary. The parity invariant is
enforced by catalog/hooks/tests/test_eval_loop.py::TestEvalLoopCLIAdapter.

Usage:
    python scripts/optimize_skill_description.py \\
        --skill catalog/skills/workflow/skill-eval-loop/SKILL.md \\
        --evals my-skill-workspace/evals/evals.json \\
        --cli claude \\
        --max-iterations 5 \\
        --workspace my-skill-workspace

    python scripts/optimize_skill_description.py \\
        --skill catalog/skills/workflow/skill-eval-loop/SKILL.md \\
        --evals my-skill-workspace/evals/evals.json \\
        --cli claude \\
        --dry-run

    python scripts/optimize_skill_description.py \\
        --evals my-skill-workspace/evals/evals.json \\
        --cli claude \\
        --run-raw-memory \\
        --iteration-dir my-skill-workspace/iteration-1

`--dry-run` prints the train/test split, the baseline description, and the
candidate-generation prompt template, then exits 0 without invoking any CLI.
The pytest at catalog/hooks/tests/test_eval_loop.py::TestOptimizerDryRun
asserts the dry-run output schema.

Trigger-testing techniques (v2.3.0 / Phase 4):
    `--model <name>` runs the trigger-rate estimation against a faster / cheaper
    model (e.g. `--model haiku`) to surface descriptions that only trigger on
    stronger models (a per-eval `model` field in evals.json overrides it).
    `detect_premature_action()` flags a with_skill run that invoked another tool
    before loading the Skill, and `evaluate_multi_turn()` replays an ordered
    `turns` list and asserts the skill triggers at the designated turn. These
    reuse the same CLI dispatcher (no new outbound calls, no new dependency) and
    are documented at catalog/skills/workflow/skill-eval-loop/references/
    trigger-testing.md.
"""

from __future__ import annotations

import argparse
import json
import random
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


_SUPPORTED_CLIS = ("claude", "gemini", "codex", "opencode")
_DEFAULT_SEED = 42
_DEFAULT_TRAIN_FRACTION = 0.6


# ── Skill / eval loading ──────────────────────────────────────────────────────


def load_evals(evals_path: Path) -> list[dict[str, Any]]:
    raw = json.loads(evals_path.read_text(encoding="utf-8"))
    if isinstance(raw, dict) and "evals" in raw:
        raw = raw["evals"]
    if not isinstance(raw, list):
        raise ValueError(f"{evals_path}: expected a list of eval entries or {{'evals': [...]}}")
    return raw


def parse_skill_description(skill_md_path: Path) -> str:
    """Extract the `description` field from a SKILL.md frontmatter block."""
    text = skill_md_path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        raise ValueError(f"{skill_md_path}: no YAML frontmatter")
    end = text.find("\n---", 3)
    if end == -1:
        raise ValueError(f"{skill_md_path}: unterminated YAML frontmatter")
    fm = text[3:end]
    match = re.search(r"^description:\s*(.+?)(?=\n[a-zA-Z_]+:|$)", fm, re.DOTALL | re.MULTILINE)
    if not match:
        raise ValueError(f"{skill_md_path}: no `description:` field in frontmatter")
    return match.group(1).strip()


# ── Train/test split ──────────────────────────────────────────────────────────


def split_train_test(
    evals: list[dict[str, Any]],
    train_fraction: float = _DEFAULT_TRAIN_FRACTION,
    seed: int = _DEFAULT_SEED,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Deterministic split. Returns (train, test). For N<5 the split is
    bounds-checked so test always has at least 1 entry and train has at
    least 1 entry."""
    rng = random.Random(seed)
    pool = list(evals)
    rng.shuffle(pool)
    n_train = max(1, min(len(pool) - 1, int(round(len(pool) * train_fraction))))
    train = pool[:n_train]
    test = pool[n_train:]
    return train, test


# ── CLI dispatch (parity-tested) ──────────────────────────────────────────────


def build_cli_command(
    cli: str, prompt: str, skill_path: Path | None, model: str | None = None
) -> list[str]:
    """Construct the argv for `cli`, optionally loading a skill and pinning a model.

    Each branch references ONLY its matching CLI binary. Command construction is
    split out from `invoke_cli` so the cheap-model flag threading (T015) and the
    no-cross-CLI-bleed parity invariant are both testable without spawning a
    subprocess. The parity test in
    catalog/hooks/tests/test_eval_loop.py::TestEvalLoopCLIAdapter inspects this
    function's `if cli == "X":` branches and asserts no other CLI binary appears
    in any of them.
    """
    assert cli in _SUPPORTED_CLIS, f"unsupported cli: {cli}"

    if cli == "claude":
        cmd = ["claude", "-p", prompt]
        if skill_path is not None:
            cmd.extend(["--skill", str(skill_path)])
        if model:
            cmd.extend(["--model", model])
        return cmd
    if cli == "gemini":
        cmd = ["gemini", "--workflow", prompt]
        if skill_path is not None:
            cmd.extend(["--skill-file", str(skill_path)])
        if model:
            cmd.extend(["--model", model])
        return cmd
    if cli == "codex":
        cmd = ["codex", "exec", prompt]
        if skill_path is not None:
            cmd.extend(["--prompt", str(skill_path)])
        if model:
            cmd.extend(["--model", model])
        return cmd
    if cli == "opencode":
        cmd = ["opencode", "run", prompt]
        if skill_path is not None:
            cmd.extend(["--skill", str(skill_path)])
        if model:
            cmd.extend(["--model", model])
        return cmd
    raise AssertionError(f"unreachable: cli={cli}")


def invoke_cli(
    cli: str, prompt: str, skill_path: Path | None, model: str | None = None
) -> dict[str, Any]:
    """Run `cli` with the given prompt and (optionally) skill + model loaded."""
    return _run_subprocess(build_cli_command(cli, prompt, skill_path, model))


def _run_subprocess(cmd: list[str]) -> dict[str, Any]:
    started = datetime.now(timezone.utc)
    proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    finished = datetime.now(timezone.utc)
    return {
        "stdout": proc.stdout,
        "stderr": proc.stderr,
        "exit_code": proc.returncode,
        "duration_ms": int((finished - started).total_seconds() * 1000),
        "started_at": started.isoformat().replace("+00:00", "Z"),
        "finished_at": finished.isoformat().replace("+00:00", "Z"),
    }


def resolve_raw_memory_path(evals_path: Path, eval_entry: dict[str, Any]) -> Path | None:
    """Resolve a readable raw-memory source relative to the eval-set file."""
    declared = eval_entry.get("raw_memory")
    if not isinstance(declared, str) or not declared.strip():
        return None
    candidate = evals_path.parent / declared
    return candidate if candidate.is_file() else None


def build_raw_memory_prompt(eval_entry: dict[str, Any], raw_memory: str) -> str:
    """Append prior notes verbatim to the eval query without a skill overlay."""
    query = eval_entry.get("query")
    if not isinstance(query, str) or not query:
        turns = eval_entry.get("turns")
        if not isinstance(turns, list) or not turns or not all(isinstance(turn, str) for turn in turns):
            raise ValueError(f"{eval_entry.get('id', '<unknown>')}: expected a query or string turns")
        query = "\n\n".join(turns)
    return f"{query}\n\nPrior notes follow verbatim:\n{raw_memory}"


def run_raw_memory_condition(
    cli: str,
    evals_path: Path,
    eval_entry: dict[str, Any],
    iteration_dir: Path,
    model: str | None = None,
) -> Path | None:
    """Run one declared raw-memory arm and write response-compatible artifacts."""
    source = resolve_raw_memory_path(evals_path, eval_entry)
    if source is None:
        return None

    eval_id = eval_entry.get("id")
    if not isinstance(eval_id, str) or not eval_id:
        raise ValueError("raw-memory eval entry requires a non-empty id")

    try:
        raw_memory = source.read_text(encoding="utf-8")
    except (OSError, UnicodeError):
        return None
    prompt = build_raw_memory_prompt(eval_entry, raw_memory)
    selected_model = eval_entry.get("model") or model
    result = invoke_cli(cli, prompt, None, selected_model)

    outputs_dir = iteration_dir / eval_id / "raw_memory" / "outputs"
    outputs_dir.mkdir(parents=True, exist_ok=True)
    response = str(result.get("stdout", ""))
    (outputs_dir / "response.txt").write_text(response, encoding="utf-8")
    metadata = {
        "cli": cli,
        "skill_loaded": False,
        "memory_injected": True,
        "started_at": result.get("started_at"),
        "finished_at": result.get("finished_at"),
        "duration_ms": result.get("duration_ms", 0),
        "total_tokens": round((len(prompt) + len(response)) / 4),
        "tokens_estimated": True,
        "exit_code": result.get("exit_code", 1),
    }
    (outputs_dir / "run_metadata.json").write_text(
        json.dumps(metadata, indent=2) + "\n", encoding="utf-8"
    )
    return outputs_dir.parent


def run_declared_raw_memory_evals(
    cli: str,
    evals_path: Path,
    evals: list[dict[str, Any]],
    iteration_dir: Path,
    model: str | None = None,
) -> dict[str, Any]:
    """Run every readable optional arm and report skipped entries as not_run."""
    report: dict[str, Any] = {"mode": "raw-memory", "run": [], "not_run": []}
    for eval_entry in evals:
        eval_id = str(eval_entry.get("id", "<unknown>"))
        run_dir = run_raw_memory_condition(cli, evals_path, eval_entry, iteration_dir, model)
        if run_dir is None:
            report["not_run"].append(eval_id)
            continue
        metadata = json.loads((run_dir / "outputs" / "run_metadata.json").read_text(encoding="utf-8"))
        report["run"].append({"id": eval_id, "run_dir": str(run_dir), "exit_code": metadata["exit_code"]})
    return report


# ── Trigger detection ─────────────────────────────────────────────────────────


def estimate_trigger_rate(
    cli: str,
    skill_path: Path,
    description_under_test: str,
    queries: list[dict[str, Any]],
    repeats: int,
    model: str | None = None,
) -> float:
    """Run each `query` `repeats` times and compute the trigger rate.

    A run "triggers" when the response contains markers indicating the skill
    body was loaded (a heuristic: presence of any unique phrase from the
    description, or - more reliably - a CLI-reported skill-loaded flag if
    the CLI surfaces one).

    For an honest evaluation, the description-under-test is temporarily
    swapped into the SKILL.md, the trigger rate is measured, and the
    original description is restored afterward. The optimizer's caller is
    responsible for not running multiple optimizations in parallel against
    the same SKILL.md.
    """
    if not queries:
        return 0.0

    original_text = skill_path.read_text(encoding="utf-8")
    try:
        _swap_description(skill_path, description_under_test)
        successes = 0
        total = 0
        for q in queries:
            should_trigger = bool(q.get("should_trigger", True))
            q_model = q.get("model") or model
            for _ in range(repeats):
                result = invoke_cli(cli, q["query"], skill_path, q_model)
                triggered = _detect_trigger(result["stdout"], description_under_test)
                # An eval is a "success" when triggered matches should_trigger.
                if triggered == should_trigger:
                    successes += 1
                total += 1
        return successes / total if total else 0.0
    finally:
        skill_path.write_text(original_text, encoding="utf-8")


def _swap_description(skill_path: Path, new_description: str) -> None:
    text = skill_path.read_text(encoding="utf-8")
    end = text.find("\n---", 3)
    if end == -1:
        raise ValueError(f"{skill_path}: unterminated frontmatter, refusing to overwrite")
    fm = text[3:end]
    new_fm = re.sub(
        r"^description:\s*.+?(?=\n[a-zA-Z_]+:|$)",
        f"description: {new_description}",
        fm,
        count=1,
        flags=re.DOTALL | re.MULTILINE,
    )
    if new_fm == fm:
        raise ValueError(f"{skill_path}: failed to replace description in frontmatter")
    skill_path.write_text("---" + new_fm + text[end:], encoding="utf-8")


def _detect_trigger(stdout: str, description: str) -> bool:
    """Heuristic: triggered if the response mentions any verbatim trigger phrase.

    Real CLIs will eventually surface a structured `skill_loaded` flag; until
    then this heuristic is the best portable signal. Tests should override
    this function via monkeypatch when invoking the optimizer in dry-run.
    """
    lowered = stdout.lower()
    # Pull short phrases (<= 6 words) out of the description as proxies.
    candidates = re.findall(r"[a-z][a-z\- ]{4,40}", description.lower())
    return any(c.strip() in lowered for c in candidates if len(c.strip()) >= 8)


# ── Premature-action detection (T014) ─────────────────────────────────────────


# Tools allowed before the first Skill invocation in a with_skill run. `Skill`
# IS the skill load; `TodoWrite` is planning scaffolding, not real work. Any
# other tool used before the skill loads is "premature action": the agent
# started working before it loaded the skill it was supposed to use.
_PREMATURE_ACTION_ALLOWLIST = ("Skill", "TodoWrite")


def extract_tool_invocations(stream_text: str) -> list[str]:
    """Return the ordered list of tool-use names from a CLI stream-json transcript.

    Accepts the newline-delimited JSON that the CLIs emit under their
    stream/transcript output mode (the superpowers harness greps the same
    stream for `"name":"Skill"`). Each `{"type": "tool_use", "name": ...}` block,
    however deeply nested inside an assistant message, contributes its `name` in
    document order. Tolerates a single JSON document spanning the whole text and
    skips any non-JSON line rather than raising.
    """
    names: list[str] = []

    def walk(obj: Any) -> None:
        if isinstance(obj, dict):
            if obj.get("type") == "tool_use" and isinstance(obj.get("name"), str):
                names.append(obj["name"])
            for value in obj.values():
                walk(value)
        elif isinstance(obj, list):
            for item in obj:
                walk(item)

    for line in stream_text.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            walk(json.loads(line))
        except json.JSONDecodeError:
            continue
    if not names:
        # Fall back to parsing the whole text as one JSON document (an array
        # of events rather than newline-delimited objects).
        try:
            walk(json.loads(stream_text))
        except json.JSONDecodeError:
            pass
    return names


def detect_premature_action(tool_stream: str | list[str]) -> bool:
    """Flag a with_skill run that acted before loading the skill.

    `tool_stream` is either a raw stream-json transcript or an already-extracted
    ordered list of tool names. Returns True when a non-allowlisted tool is
    invoked before the first `Skill` invocation - including the case where the
    skill never loads at all but the agent still used a real tool.
    """
    invocations = (
        extract_tool_invocations(tool_stream)
        if isinstance(tool_stream, str)
        else list(tool_stream)
    )
    for name in invocations:
        if name == "Skill":
            return False
        if name not in _PREMATURE_ACTION_ALLOWLIST:
            return True
    return False


# ── Multi-turn trigger testing (T015) ─────────────────────────────────────────


def is_multi_turn(eval_entry: dict[str, Any]) -> bool:
    """True when an eval entry drives a multi-turn flow (a non-empty `turns` list)."""
    turns = eval_entry.get("turns")
    return isinstance(turns, list) and len(turns) > 0


def first_trigger_turn(per_turn_triggers: list[bool]) -> int | None:
    """Return the 1-based index of the first turn that triggered, or None."""
    for idx, triggered in enumerate(per_turn_triggers, start=1):
        if triggered:
            return idx
    return None


def multi_turn_passes(per_turn_triggers: list[bool], expected_turn: int) -> bool:
    """A multi-turn eval passes when the FIRST trigger lands on `expected_turn`.

    Triggering earlier than expected (the description over-triggers on setup
    turns) and never triggering both count as failures - the designated turn is
    where the skill is supposed to fire, no sooner and no later.
    """
    return first_trigger_turn(per_turn_triggers) == expected_turn


def evaluate_multi_turn(
    cli: str,
    skill_path: Path,
    eval_entry: dict[str, Any],
    repeats: int,
    model: str | None = None,
) -> dict[str, Any]:
    """Replay an eval's ordered `turns` and report whether it triggers on time.

    Each turn is run `repeats` times; a turn counts as triggered when the
    majority of its repeats trigger (the same >= 0.5 rule the optimizer uses).
    The designated turn comes from the entry's `trigger_turn` (1-based; defaults
    to the last turn, matching the superpowers `run-haiku-test` 5-turn flow that
    asserts a turn-5 trigger). Reuses the standard dispatcher - no new outbound
    path.
    """
    turns = eval_entry.get("turns") or []
    expected_turn = int(eval_entry.get("trigger_turn", len(turns)))
    q_model = eval_entry.get("model") or model

    per_turn_triggers: list[bool] = []
    for turn_prompt in turns:
        hits = 0
        for _ in range(repeats):
            result = invoke_cli(cli, turn_prompt, skill_path, q_model)
            if _detect_trigger(result["stdout"], eval_entry.get("query", turn_prompt)):
                hits += 1
        per_turn_triggers.append(repeats > 0 and hits / repeats >= 0.5)

    return {
        "eval_id": eval_entry.get("id"),
        "expected_turn": expected_turn,
        "per_turn_triggers": per_turn_triggers,
        "first_trigger_turn": first_trigger_turn(per_turn_triggers),
        "passed": multi_turn_passes(per_turn_triggers, expected_turn),
    }


# ── Candidate generation ──────────────────────────────────────────────────────


_CANDIDATE_PROMPT_TEMPLATE = """\
You are rewriting the `description` field of a Nexus-Hub skill so it triggers
more reliably on the skill's intended use cases without over-triggering on
look-alike intents.

Current description:
<<<
{description}
>>>

Train queries that the description CURRENTLY HANDLES CORRECTLY:
{train_passes}

Train queries that the description CURRENTLY MISHANDLES:
{train_failures}

Rules:
- The rewrite MUST follow the AGENTS.md "pushy description" rule: lead with
  the action, list trigger phrases verbatim, cover synonyms, end with a
  `SKIP:` clause for look-alike intents.
- Do NOT lengthen the description past 350 words.
- Do NOT introduce vendor-specific names, brands, or platform identifiers.
- Output exactly 3 candidate rewrites as a JSON array of strings, no prose.
"""


def generate_candidates(
    cli: str,
    description: str,
    train_passes: list[str],
    train_failures: list[str],
) -> list[str]:
    """Ask the CLI to propose 3 candidate descriptions. Falls back to [description] on parse failure."""
    prompt = _CANDIDATE_PROMPT_TEMPLATE.format(
        description=description,
        train_passes="\n".join(f"- {q}" for q in train_passes) or "- (none)",
        train_failures="\n".join(f"- {q}" for q in train_failures) or "- (none)",
    )
    result = invoke_cli(cli, prompt, skill_path=None)
    try:
        candidates = json.loads(result["stdout"])
        if not isinstance(candidates, list):
            return [description]
        return [c for c in candidates if isinstance(c, str)][:3] or [description]
    except json.JSONDecodeError:
        return [description]


# ── Selection rule ────────────────────────────────────────────────────────────


def select_best(baseline: dict[str, Any], candidates: list[dict[str, Any]]) -> dict[str, Any]:
    """Pick the entry with the highest test_trigger_rate; tie-break on
    train_trigger_rate then on description length (shorter wins)."""
    pool = [baseline, *candidates]

    def key(c: dict[str, Any]) -> tuple[float, float, int]:
        return (
            c.get("test_trigger_rate", 0.0),
            c.get("train_trigger_rate", 0.0),
            -len(c.get("description", "")),
        )

    return max(pool, key=key)


# ── Iteration loop ────────────────────────────────────────────────────────────


def run_iteration(
    cli: str,
    skill_path: Path,
    train: list[dict[str, Any]],
    test: list[dict[str, Any]],
    description: str,
    repeats: int,
    model: str | None = None,
) -> dict[str, Any]:
    """Run one optimizer iteration. Returns the iteration record."""
    baseline_train = estimate_trigger_rate(cli, skill_path, description, train, repeats, model)
    baseline_test = estimate_trigger_rate(cli, skill_path, description, test, repeats, model)

    train_passes = [
        q["query"] for q in train if _passes(cli, skill_path, description, q, repeats, model)
    ]
    train_failures = [q["query"] for q in train if q["query"] not in train_passes]

    candidate_strs = generate_candidates(cli, description, train_passes, train_failures)
    candidates = []
    for cand in candidate_strs:
        candidates.append(
            {
                "description": cand,
                "train_trigger_rate": estimate_trigger_rate(
                    cli, skill_path, cand, train, repeats, model
                ),
                "test_trigger_rate": estimate_trigger_rate(
                    cli, skill_path, cand, test, repeats, model
                ),
            }
        )

    baseline_record = {
        "description": description,
        "train_trigger_rate": baseline_train,
        "test_trigger_rate": baseline_test,
    }
    best = select_best(baseline_record, candidates)

    return {
        "skill_path": str(skill_path),
        "split": {
            "train_ids": [q["id"] for q in train],
            "test_ids": [q["id"] for q in test],
        },
        "baseline": baseline_record,
        "candidates": candidates,
        "best_description": best["description"],
        "selection_metric": "test_trigger_rate",
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    }


def _passes(
    cli: str,
    skill_path: Path,
    description: str,
    query: dict[str, Any],
    repeats: int,
    model: str | None = None,
) -> bool:
    rate = estimate_trigger_rate(cli, skill_path, description, [query], repeats, model)
    return rate >= 0.5


# ── Dry-run mode ──────────────────────────────────────────────────────────────


def render_dry_run(
    skill_path: Path,
    evals_path: Path,
    train: list[dict[str, Any]],
    test: list[dict[str, Any]],
    description: str,
    cli: str,
    max_iterations: int,
    seed: int,
    model: str | None = None,
) -> dict[str, Any]:
    """Build the dry-run report without invoking any CLI."""
    return {
        "mode": "dry-run",
        "cli": cli,
        "model": model,
        "max_iterations": max_iterations,
        "seed": seed,
        "skill_path": str(skill_path),
        "evals_path": str(evals_path),
        "baseline_description": description,
        "split": {
            "train_ids": [q["id"] for q in train],
            "test_ids": [q["id"] for q in test],
        },
        "n_train": len(train),
        "n_test": len(test),
        "low_confidence": len(train) + len(test) < 8,
        "candidate_generation_prompt_template_preview": _CANDIDATE_PROMPT_TEMPLATE.format(
            description=description,
            train_passes="<train passes inserted at runtime>",
            train_failures="<train failures inserted at runtime>",
        ),
        "selection_metric": "test_trigger_rate",
    }


# ── Entry point ───────────────────────────────────────────────────────────────


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    parser.add_argument("--skill", type=Path, default=None, help="Path to the SKILL.md")
    parser.add_argument("--evals", type=Path, required=True, help="Path to evals.json")
    parser.add_argument(
        "--cli",
        choices=_SUPPORTED_CLIS,
        required=True,
        help="Which AI CLI to dispatch to",
    )
    parser.add_argument("--workspace", type=Path, default=Path("."), help="Where to write optimizer/iteration-N.json")
    parser.add_argument("--max-iterations", type=int, default=5)
    parser.add_argument("--repeats", type=int, default=3, help="Trigger-rate samples per query (default 3)")
    parser.add_argument("--seed", type=int, default=_DEFAULT_SEED)
    parser.add_argument("--train-fraction", type=float, default=_DEFAULT_TRAIN_FRACTION)
    parser.add_argument(
        "--model",
        default=None,
        help="Run trigger-rate estimation against this (e.g. cheaper/faster) model; "
        "a per-eval `model` field overrides it. Default: the CLI's default model.",
    )
    parser.add_argument("--dry-run", action="store_true", help="Print plan and exit; no CLI calls")
    parser.add_argument(
        "--run-raw-memory",
        action="store_true",
        help="Run readable eval-entry raw_memory arms through the existing dispatcher",
    )
    parser.add_argument(
        "--iteration-dir",
        type=Path,
        default=None,
        help="Iteration directory for --run-raw-memory response artifacts",
    )
    args = parser.parse_args()

    if not args.evals.exists():
        print(f"Error: evals not found: {args.evals}", file=sys.stderr)
        return 1

    evals = load_evals(args.evals)

    if args.run_raw_memory:
        if args.dry_run or args.iteration_dir is None:
            print("Error: --run-raw-memory requires --iteration-dir and cannot be combined with --dry-run", file=sys.stderr)
            return 1
        report = run_declared_raw_memory_evals(
            args.cli, args.evals, evals, args.iteration_dir, args.model
        )
        print(json.dumps(report, indent=2))
        return 0 if all(item["exit_code"] == 0 for item in report["run"]) else 1

    if args.skill is None or not args.skill.exists():
        print(f"Error: skill not found: {args.skill}", file=sys.stderr)
        return 1

    description = parse_skill_description(args.skill)
    train, test = split_train_test(evals, args.train_fraction, args.seed)

    if args.dry_run:
        report = render_dry_run(
            skill_path=args.skill,
            evals_path=args.evals,
            train=train,
            test=test,
            description=description,
            cli=args.cli,
            max_iterations=args.max_iterations,
            seed=args.seed,
            model=args.model,
        )
        print(json.dumps(report, indent=2))
        return 0

    optimizer_dir = args.workspace / "optimizer"
    optimizer_dir.mkdir(parents=True, exist_ok=True)

    current_description = description
    last_test_score = -1.0
    flat_count = 0
    final_record: dict[str, Any] | None = None

    for n in range(1, args.max_iterations + 1):
        record = run_iteration(
            cli=args.cli,
            skill_path=args.skill,
            train=train,
            test=test,
            description=current_description,
            repeats=args.repeats,
            model=args.model,
        )
        record["iteration"] = n
        out_path = optimizer_dir / f"iteration-{n}.json"
        out_path.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
        print(f"Iteration {n}: best test_trigger_rate = "
              f"{select_best(record['baseline'], record['candidates'])['test_trigger_rate']:.3f}")

        best = select_best(record["baseline"], record["candidates"])
        current_description = best["description"]
        final_record = record

        if best["test_trigger_rate"] <= last_test_score:
            flat_count += 1
            if flat_count >= 2:
                print(f"Stopping: {flat_count} consecutive iterations without improvement.")
                break
        else:
            flat_count = 0
        last_test_score = best["test_trigger_rate"]
        if last_test_score >= 1.0:
            print("Stopping: held-out test score reached 1.0.")
            break

    if final_record is not None:
        final_path = optimizer_dir / "final.json"
        final_path.write_text(json.dumps(final_record, indent=2) + "\n", encoding="utf-8")
        print(f"Final: {final_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
