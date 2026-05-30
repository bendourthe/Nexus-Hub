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
  "tags": ["happy-path", "trigger-positive"]
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

Both `turns`/`trigger_turn` and `model` are opt-in: a plain single-turn eval omits them and is unaffected.

## `iteration-N/eval-XXX/{with_skill,without_skill}/outputs/run_metadata.json`

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
- `skill_loaded` (bool, required) - `true` for `with_skill/`, `false` for `without_skill/`. The aggregator uses this to compute the with-vs-without delta without filename inference.
- `duration_ms`, `total_tokens` (number, required) - if the CLI does not report tokens directly, estimate via `len(prompt + response) / 4` and set `tokens_estimated: true`.
- `exit_code` (number, required) - `0` for success; the aggregator excludes non-zero runs from the pass-rate denominator.

## `iteration-N/eval-XXX/{with_skill,without_skill}/grading.json`

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
      "premature_action": false
    }
  },
  "overall": {
    "with_skill_pass_rate": 0.74,
    "without_skill_pass_rate": 0.31,
    "pass_rate_delta": 0.43,
    "with_skill_duration_ms_mean": 18000,
    "without_skill_duration_ms_mean": 9500,
    "with_skill_tokens_mean": 4100,
    "without_skill_tokens_mean": 2200
  }
}
```

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
