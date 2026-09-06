# Trigger-testing techniques

The optimizer (`scripts/optimize_skill_description.py`) measures whether a skill's `description` triggers on a single prompt. That catches the most common failure (a description too narrow to fire at all) but misses three others that only show up under more realistic conditions: the agent that acts before loading the skill, the skill that triggers on a cold prompt but not deep in a conversation, and the description that triggers on a strong model but not a cheaper one. This reference documents the three techniques that cover those gaps, what each one catches, how to author an eval that exercises it, and how to read the resulting output fields.

These techniques are reverse-engineered (form, not verbatim) from the superpowers trigger harness (`tests/skill-triggering/run-test.sh`, `tests/explicit-skill-requests/run-test.sh`, and `run-haiku-test.sh`); see the legacy migration-source path `docs/archive/v2/v2.3/comparison-superpowers.md` Section 8 for provenance. They reuse the same CLI dispatcher as the rest of the loop: no new outbound calls, no new dependency, no new credential.

## 1. Premature-action detection

**What it catches.** A `with_skill` run where the agent starts doing real work (editing files, running commands, searching) BEFORE it loads the skill it was supposed to use. The skill may eventually load, but by then the agent has already committed to an approach the skill was meant to shape. A skill that "triggers" on this measure can still be losing in practice because it triggers too late.

**How it works.** The CLI stream-json transcript records each tool invocation in order. `detect_premature_action()` walks that ordered list of tool names and applies one rule: the first `Skill` invocation clears the run; any non-allowlisted tool seen before it sets the flag. `Skill` (the skill load itself) and `TodoWrite` (planning scaffolding, not real work) are the only tools allowed before the skill loads. A run where the skill never loads but a real tool ran also flags as premature.

**How to author the eval.** No new eval field is needed. Capture the run's stream-json transcript to `<run>/outputs/stream.jsonl` (the runner's stream/transcript output mode - the same stream the superpowers harness greps for `"name":"Skill"`). The grader reads it and records `premature_action` in `grading.json`; the aggregator surfaces it per-eval in `benchmark.json`.

**How to read the output.** Two places:

- `grading.json` -> `premature_action` (per run; meaningful only for `with_skill`).
- `benchmark.json` -> `by_eval.<id>.premature_action` (lifted from the `with_skill` run) and `by_eval.<id>.with_skill.premature_action`.

A `true` here means: even if the pass-rate looks fine, fix the description so the skill loads FIRST. The usual cause is a description that reads as optional ("you may want to...") rather than a gate ("before doing X, load this skill").

## 2. Multi-turn conversation triggering

**What it catches.** A skill that triggers on a direct cold prompt ("review this code") but fails to trigger when the same intent arrives at the end of a multi-turn flow ("let's brainstorm a feature" -> "draft a plan" -> "now implement step 1"). The deep-in-conversation case is where many discipline skills are actually needed, and it is exactly where a description tuned only against single prompts tends to miss.

**How it works.** `evaluate_multi_turn()` replays the eval's ordered `turns` list, running each turn through the dispatcher with the skill loaded, and records whether the skill triggered on each turn. `multi_turn_passes()` then asserts the FIRST trigger lands on the designated `trigger_turn` (1-based; defaults to the last turn). Triggering earlier than expected (the description over-fires on setup turns) and never triggering both count as failures.

**How to author the eval.** Add `turns` and `trigger_turn` to the eval entry:

```json
{
  "id": "eval-010",
  "turns": [
    "Let's brainstorm a logging feature for the API.",
    "Good. Now draft an implementation plan for it.",
    "Plan looks right - go ahead and implement step 1."
  ],
  "trigger_turn": 3,
  "should_trigger": true,
  "assertions": [
    {"text": "Output loads the spec/design gate before writing code"}
  ]
}
```

`turns` replaces the single `query`; `trigger_turn` is where the skill is expected to first fire (here, the implementation turn, not the brainstorm turn). Both fields are optional - a plain single-turn eval omits them and is unaffected.

**How to read the output.** `evaluate_multi_turn()` returns:

- `per_turn_triggers` - a bool per turn, in order.
- `first_trigger_turn` - the 1-based index of the first trigger, or `null`.
- `passed` - whether `first_trigger_turn == expected_turn`.

If `first_trigger_turn` is earlier than expected, tighten the `SKIP:` clause so setup turns do not fire it. If it is `null` (never triggered), the description is missing the deep-in-conversation phrasing; add the verbatim phrases a user would actually type at the implementation turn.

## 3. Cheap-model fragility test

**What it catches.** A description that triggers reliably on a strong model but not on a cheaper/faster one. Stronger models infer intent from a terse description; cheaper models need the trigger phrases spelled out. A skill that only triggers on the strong model silently fails for every user running a faster model.

**How it works.** The harness-level `--model <name>` flag (e.g. `--model haiku`) threads through `build_cli_command()` into every per-CLI invocation, so trigger-rate estimation runs against that model. A per-eval `model` field overrides the flag for a single entry. Run the same eval set twice - once on the default model, once with `--model <cheaper>` - and compare trigger rates. A description whose trigger rate drops on the cheaper model is fragile.

**How to author the eval.** Either pass `--model` to the whole run:

```bash
python scripts/optimize_skill_description.py \
    --skill catalog/skills/<cat>/<name>/SKILL.md \
    --evals <workspace>/evals/evals.json \
    --cli claude \
    --model haiku \
    --dry-run
```

or pin a single eval to a model with the optional `model` field:

```json
{
  "id": "eval-011",
  "query": "score this skill against my test prompts",
  "should_trigger": true,
  "model": "haiku",
  "assertions": [{"text": "Skill triggers on the cheaper model"}]
}
```

**How to read the output.** The dry-run report echoes the resolved `model` (so you can confirm the flag took effect without spending a call). After a real run, compare `test_trigger_rate` across the default-model and cheap-model iteration records: a meaningful drop on the cheaper model means the description leans on inference the cheaper model does not do - add verbatim trigger phrases per `references/improvement-heuristics.md` until the cheap-model rate recovers.

## When to use each

- Run premature-action detection on every discipline / gate skill (verification, design-approval, root-cause): for those, loading FIRST is the whole point.
- Run multi-turn triggering on any skill whose real use arrives mid-workflow rather than as a cold opening prompt.
- Run the cheap-model test before shipping any skill to users who may not be on the strongest model - it is the cheapest insurance against silent non-triggering in the field.

All three are opt-in and additive: a single-turn, default-model eval set keeps working exactly as before. See `references/schemas.md` for the exact `evals.json`, `grading.json`, and `benchmark.json` field definitions.
