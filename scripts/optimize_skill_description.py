#!/usr/bin/env python3
"""Iteratively optimize a DevAI-Hub skill's `description` frontmatter field.

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

`--dry-run` prints the train/test split, the baseline description, and the
candidate-generation prompt template, then exits 0 without invoking any CLI.
The pytest at catalog/hooks/tests/test_eval_loop.py::TestOptimizerDryRun
asserts the dry-run output schema.
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


def invoke_cli(cli: str, prompt: str, skill_path: Path | None) -> dict[str, Any]:
    """Run `cli` with the given prompt and (optionally) skill loaded.

    Each branch invokes ONLY its matching CLI binary. The parity test in
    catalog/hooks/tests/test_eval_loop.py::TestEvalLoopCLIAdapter inspects
    this function's source and asserts no other CLI binary appears in any
    `if cli == "X":` branch.
    """
    assert cli in _SUPPORTED_CLIS, f"unsupported cli: {cli}"

    if cli == "claude":
        cmd = ["claude", "-p", prompt]
        if skill_path is not None:
            cmd.extend(["--skill", str(skill_path)])
        return _run_subprocess(cmd)
    if cli == "gemini":
        cmd = ["gemini", "--workflow", prompt]
        if skill_path is not None:
            cmd.extend(["--skill-file", str(skill_path)])
        return _run_subprocess(cmd)
    if cli == "codex":
        cmd = ["codex", "exec", prompt]
        if skill_path is not None:
            cmd.extend(["--prompt", str(skill_path)])
        return _run_subprocess(cmd)
    if cli == "opencode":
        cmd = ["opencode", "run", prompt]
        if skill_path is not None:
            cmd.extend(["--skill", str(skill_path)])
        return _run_subprocess(cmd)
    raise AssertionError(f"unreachable: cli={cli}")


def _run_subprocess(cmd: list[str]) -> dict[str, Any]:
    started = datetime.now(timezone.utc)
    proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    finished = datetime.now(timezone.utc)
    return {
        "stdout": proc.stdout,
        "stderr": proc.stderr,
        "exit_code": proc.returncode,
        "duration_ms": int((finished - started).total_seconds() * 1000),
    }


# ── Trigger detection ─────────────────────────────────────────────────────────


def estimate_trigger_rate(
    cli: str,
    skill_path: Path,
    description_under_test: str,
    queries: list[dict[str, Any]],
    repeats: int,
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
            for _ in range(repeats):
                result = invoke_cli(cli, q["query"], skill_path)
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


# ── Candidate generation ──────────────────────────────────────────────────────


_CANDIDATE_PROMPT_TEMPLATE = """\
You are rewriting the `description` field of a DevAI-Hub skill so it triggers
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
) -> dict[str, Any]:
    """Run one optimizer iteration. Returns the iteration record."""
    baseline_train = estimate_trigger_rate(cli, skill_path, description, train, repeats)
    baseline_test = estimate_trigger_rate(cli, skill_path, description, test, repeats)

    train_passes = [q["query"] for q in train if _passes(cli, skill_path, description, q, repeats)]
    train_failures = [q["query"] for q in train if q["query"] not in train_passes]

    candidate_strs = generate_candidates(cli, description, train_passes, train_failures)
    candidates = []
    for cand in candidate_strs:
        candidates.append(
            {
                "description": cand,
                "train_trigger_rate": estimate_trigger_rate(cli, skill_path, cand, train, repeats),
                "test_trigger_rate": estimate_trigger_rate(cli, skill_path, cand, test, repeats),
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
    cli: str, skill_path: Path, description: str, query: dict[str, Any], repeats: int
) -> bool:
    rate = estimate_trigger_rate(cli, skill_path, description, [query], repeats)
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
) -> dict[str, Any]:
    """Build the dry-run report without invoking any CLI."""
    return {
        "mode": "dry-run",
        "cli": cli,
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
    parser.add_argument("--skill", type=Path, required=True, help="Path to the SKILL.md")
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
    parser.add_argument("--dry-run", action="store_true", help="Print plan and exit; no CLI calls")
    args = parser.parse_args()

    if not args.skill.exists():
        print(f"Error: skill not found: {args.skill}", file=sys.stderr)
        return 1
    if not args.evals.exists():
        print(f"Error: evals not found: {args.evals}", file=sys.stderr)
        return 1

    description = parse_skill_description(args.skill)
    evals = load_evals(args.evals)
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
