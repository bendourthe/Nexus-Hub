# Eval-loop JSON schemas

Every JSON artifact produced by the skill-eval-loop has a stable schema so the aggregator, the viewer, and the optimizer can all read each other's output. This file is the canonical reference; SKILL.md links here whenever a schema is named.

## `evals/evals.json`

A list of eval entries. Each entry:

```json
{
  "id": "eval-001",
  "query": "User-facing prompt that the CLI receives verbatim",
  "should_trigger": true,
  "assertions": [
    {"text": "Output references at least one Stage 1 question"},
    {"text": "Output does not exceed 250 lines"}
  ],
  "tags": ["happy-path", "trigger-positive"],
  "raw_memory": "raw_memory.md"
}
```

Fields:

- `id` (string, required) - kebab-case identifier; used as the directory name under `iteration-N/`.
- `query` (string, required for single-turn evals) - the prompt text passed to the CLI. Should be realistic, not contrived. Optional when `turns` is present.
- `should_trigger` (bool, required) - whether the skill is expected to trigger on this query. The optimizer uses this for its trigger-rate metric.
- `assertions` (array of `{text, ...}` objects, required) - each `text` is human-readable; the grader sub-agent evaluates each one against the run's `response.txt` and records `passed` + `evidence`.
- `tags` (array of strings, optional) - free-form labels for filtering in the viewer. Common tags: `happy-path`, `edge-case`, `trigger-positive`, `trigger-negative`, `regression`.
- `turns` (array of strings, optional) - an ordered list of conversation turns for a multi-turn trigger test. When present, `evaluate_multi_turn()` replays the turns in order and asserts the skill triggers at the designated turn (the deep-in-conversation failure mode). See `references/trigger-testing.md`.
- `trigger_turn` (number, optional) - the 1-based turn index at which the skill is expected to FIRST trigger in a multi-turn flow. Defaults to the last turn. Triggering earlier or never both fail the multi-turn assertion.
- `model` (string, optional) - run THIS eval against a specific (typically cheaper/faster) model to surface descriptions that only trigger on stronger models. Overrides the harness-level `--model` flag for this entry. See `references/trigger-testing.md`.
- `raw_memory` (string, optional) - path, relative to `evals.json`, to raw logs or notes containing the same prior experience distilled into the target skill. When present and readable, `python scripts/optimize_skill_description.py --evals <evals.json> --cli <cli> --run-raw-memory --iteration-dir <iteration-N>` creates `raw_memory/` through the existing dispatcher and injects the file verbatim after the unchanged query. When absent or unreadable, the runner does not invent a substitute and the benchmark records `raw_memory: "not_run"`.

Both `turns`/`trigger_turn` and `model` are opt-in: a plain single-turn eval omits them and is unaffected.

## `iteration-N/eval-XXX/{with_skill,without_skill,raw_memory}/outputs/run_metadata.json`

Captured per-run metadata:

```json
{
  "cli": "claude",
  "skill_loaded": true,
  "started_at": "2026-05-08T12:34:56Z",
  "finished_at": "2026-05-08T12:35:14Z",
  "duration_ms": 18221,
  "total_tokens": 4127,
  "tokens_estimated": false,
  "exit_code": 0
}
```

Fields:

- `cli` (string, required) - one of `claude` / `gemini` / `codex` / `opencode`. Must match across paired runs in the same eval.
- `skill_loaded` (bool, required) - `true` for `with_skill/`; `false` for `without_skill/` and `raw_memory/`. The aggregator uses this to compute the with-vs-without delta without filename inference.
- `memory_injected` (bool, required for `raw_memory/`) - `true` confirms that the eval's declared raw-memory file was appended verbatim to the prompt. Omit it for the two standard arms.
- `duration_ms`, `total_tokens` (number, required) - if the CLI does not report tokens directly, estimate via `len(prompt + response) / 4` and set `tokens_estimated: true`.
- `exit_code` (number, required) - `0` for success; the aggregator marks a non-zero raw-memory run invalid and excludes it from aggregate metrics.

## `iteration-N/eval-XXX/{with_skill,without_skill,raw_memory}/grading.json`

Produced by the grader sub-agent per the prompt in `agents/grader.md`:

```json
{
  "eval_id": "eval-001",
  "skill_loaded": true,
  "graded_at": "2026-05-08T12:35:30Z",
  "premature_action": false,
  "assertions": [
    {
      "text": "Output references at least one Stage 1 question",
      "passed": true,
      "evidence": "Line 12: 'who is the audience and what do they already know'"
    },
    {
      "text": "Output does not exceed 250 lines",
      "passed": false,
      "evidence": "Output is 287 lines (exceeds cap by 37)"
    }
  ],
  "pass_rate": 0.5
}
```

The aggregator depends on the exact field names `text`, `passed`, `evidence`. The grader sub-agent prompt enforces this contract.

`premature_action` (bool, optional) is the trigger-discipline flag for a `with_skill` run: `true` when the agent invoked a tool other than `Skill` / `TodoWrite` before the first `Skill` invocation (it started working before loading the skill). The grader computes it from the run's tool stream via the rule in `optimize_skill_description.detect_premature_action`; the aggregator surfaces it per-eval in `benchmark.json`. It defaults to `false` for the `without_skill` baseline (no skill to load) and for runs that predate the field.

## `iteration-N/benchmark.json`

Produced by `scripts/aggregate_benchmark.py`:

```json
{
  "iteration": 1,
  "n_evals": 5,
  "generated_at": "2026-05-08T12:40:00Z",
  "by_eval": {
    "eval-001": {
      "with_skill": {"pass_rate": 0.8, "duration_ms_mean": 18000, "duration_ms_stddev": 1200, "tokens_mean": 4100, "tokens_stddev": 250, "premature_action": false},
      "without_skill": {"pass_rate": 0.2, "duration_ms_mean": 9500, "duration_ms_stddev": 800, "tokens_mean": 2200, "tokens_stddev": 150, "premature_action": false},
      "delta": {"pass_rate": 0.6, "duration_ms": 8500, "tokens": 1900},
      "premature_action": false,
      "raw_memory": "not_run"
    }
  },
  "overall": {
    "with_skill_pass_rate": 0.74,
    "without_skill_pass_rate": 0.31,
    "pass_rate_delta": 0.43,
    "with_skill_duration_ms_mean": 18000,
    "without_skill_duration_ms_mean": 9500,
    "with_skill_tokens_mean": 4100,
    "without_skill_tokens_mean": 2200,
    "raw_memory": "not_run"
  }
}
```

When an eval contains a contract-valid completed `raw_memory/` directory, its `raw_memory` value is the same metrics object as the other run conditions plus `status: "run"`. Validity requires parseable metadata and grading, `skill_loaded: false`, `memory_injected: true`, numeric timing and token fields, `exit_code: 0`, a numeric grading pass rate, and one CLI identity shared by all three conditions. A present but invalid arm records `status: "invalid"` with an `errors` list and never enters aggregate metrics.

When at least one eval has a valid arm, `overall.raw_memory` is an object with `status: "run"` or `status: "partial"`, `n_evals`, `pass_rate`, `duration_ms_mean`, and `tokens_mean`; `partial` also lists `invalid_evals`. If directories exist but none are valid, the overall object has `status: "invalid"`, `n_evals: 0`, and `invalid_evals`. When no optional directory exists, both per-eval and overall values are the literal string `"not_run"`. Existing with-vs-without deltas never include the optional arm.

`benchmark.md` is the same data as a Markdown table for human review; the analyzer sub-agent reads `benchmark.json` (the structured form) for its non-discriminating-assertion detection.

## `iteration-N/feedback.json`

Produced by the viewer when the user clicks "Submit All Reviews":

```json
{
  "iteration": 1,
  "submitted_at": "2026-05-08T13:00:00Z",
  "reviews": {
    "eval-001": {
      "verdict": "looks-right",
      "notes": "with_skill output cited the right Stage 1 question; baseline did not."
    },
    "eval-002": {
      "verdict": "wrong-direction",
      "notes": "Output passed assertions but missed the user's actual ask - assertions are too loose."
    },
    "eval-003": {
      "verdict": "ambiguous",
      "notes": "Both runs are mediocre; rewrite the eval prompt."
    }
  }
}
```

`verdict` is exactly one of `looks-right` / `wrong-direction` / `ambiguous`. The improvement-heuristics step at `references/improvement-heuristics.md` keys off these values.

## Optimizer result schema

Produced by `scripts/optimize_skill_description.py` at `<workspace>/optimizer/iteration-N.json`:

```json
{
  "iteration": 1,
  "skill_path": "catalog/skills/workflow/skill-eval-loop/SKILL.md",
  "split": {"train_ids": ["eval-001", "eval-002", "eval-003"], "test_ids": ["eval-004", "eval-005"]},
  "baseline": {
    "description": "Drive a structured evaluation iteration loop ...",
    "train_trigger_rate": 0.67,
    "test_trigger_rate": 0.50
  },
  "candidates": [
    {
      "description": "Drive a structured evaluation iteration loop. Trigger phrases: ...",
      "train_trigger_rate": 0.83,
      "test_trigger_rate": 0.75
    }
  ],
  "best_description": "Drive a structured evaluation iteration loop. Trigger phrases: ...",
  "selection_metric": "test_trigger_rate"
}
```

The `best_description` is selected by `test_trigger_rate` (held-out test), never by `train_trigger_rate`. The full optimizer reasoning is at `references/description-optimizer.md`.

## Interoperable behavioral-eval schema (interop)

For interoperability with external skill-eval tooling, the eval set can be exported to and imported from a portable behavioral-eval schema:

```json
{
  "skill_name": "my-skill",
  "evals": [
    {
      "id": "eval-001",
      "prompt": "User-facing prompt (maps to the internal `query`)",
      "expected_output": "optional golden output; empty for assertion-only evals",
      "expectations": ["Output references at least one Stage 1 question", "Output does not exceed 250 lines"]
    }
  ]
}
```

Field mapping to the internal `evals.json` above:

- internal `query` <-> interop `prompt`
- internal `assertions[].text` <-> interop `expectations[]` (flattened to plain strings)
- interop `expected_output` has no internal equivalent (the internal format is assertion-based, not golden-output-based); it is preserved verbatim across a round-trip.

**Decision (align vs adapter)**: the internal format is the source of truth and an ADAPTER is shipped, rather than natively adopting the interoperable schema. Rationale: the internal format is a strict superset - it carries `should_trigger` (the optimizer's trigger-rate metric), `turns` / `trigger_turn` (multi-turn triggering), `model` (cheap-model fragility), and `tags`, none of which the interoperable schema can express. Adopting the interoperable schema natively would drop those capabilities and force a rewrite of the grader / aggregator / optimizer / viewer; a converter keeps every capability and changes nothing in the grading path (behavior preserved by construction).

**Lossless round-trip**: the converter (`scripts/skill_eval_convert.py`) stashes every internal-only field (and any assertion keys beyond `text`) under an `x_nexus` extension key on each interop eval. External tools ignore the unknown key; the converter reads it back, so both directions are lossless:

- `internal -> interop -> internal == internal`
- `interop -> internal -> interop == interop`

Usage:

```bash
python scripts/skill_eval_convert.py --to-interop evals.json --skill-name my-skill -o interop.json
python scripts/skill_eval_convert.py --to-internal interop.json -o evals.json
```

The converter is stdlib-only (no third-party import, no outbound call, no new dependency) and is installer-distributed to `~/.nexus-hub/scripts/` alongside the other eval-loop scripts.
