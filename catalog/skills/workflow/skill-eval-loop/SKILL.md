---
name: skill-eval-loop
description: Drive a structured evaluation iteration loop for any Nexus-Hub skill - capture user intent, write test prompts, run the skill against a baseline (no-skill) control, grade outputs against assertions, aggregate to a benchmark, view in a browser, collect feedback, and improve the skill across iterations until pass-rate stabilizes. Use whenever the user wants to evaluate a skill, benchmark a skill, A/B test a skill, optimize a skill description, run an eval set, score a skill against test prompts, iterate on a skill, or "make this skill actually work" - even if they don't say the word "eval". Use when locking a regression set, setting per-slice eval floors, refusing to lower a threshold to hide a regression, or versioning an eval corpus. Covers workspace layout, eval-prompt authoring, with-skill / without-skill paired runs, grading via assertions, browser-based human review, feedback capture, and the description-optimizer integration. SKIP one-off prompt tests with no comparison, ad-hoc skill drafting that does not need iteration, or simple unit-test runs against deterministic code. Version-bound documentation uses docs/releases/v<MAJOR>/v<MAJOR>.<MINOR>/; closed snapshots use docs/archives/.
summary_l0: "Iterate on skills and place promoted evaluation records canonically"
overview_l1: "This skill drives a closed-loop evaluation workflow for any Nexus-Hub skill. Each iteration writes 2-3 realistic test prompts to evals/evals.json, spawns paired runs (with-skill vs baseline), captures outputs + tokens + duration, grades each output against per-eval assertions, and aggregates a benchmark. A browser viewer presents the runs side-by-side and collects structured feedback. The next iteration consumes the feedback, applies improvement heuristics (pushy descriptions, explain-the-why, repeated-work elimination), and re-runs - producing a measurable pass-rate trajectory rather than a vibes-based revision history. The loop is CLI-agnostic by design: a single dispatcher routes to claude / gemini / codex / opencode with a parity invariant enforced by pytest. Trigger phrases: evaluate a skill, benchmark a skill, A/B test a skill, optimize a skill description, run eval set, score a skill, iterate on a skill, skill regression, prompt eval, with-skill vs without-skill, eval harness, eval workspace, paired runs, eval iteration. Version-bound documentation uses docs/releases/v<MAJOR>/v<MAJOR>.<MINOR>/; closed snapshots use docs/archives/."
---

# Skill Evaluation Iteration Loop

A closed-loop workflow for evolving any Nexus-Hub skill from "draft I think is good" to "skill that measurably outperforms baseline on a stable held-out test set". Each iteration produces a workspace under `<skill-name>-workspace/iteration-N/` with paired runs, assertion-graded outputs, an aggregated `benchmark.json`, and a browser-reviewable viewer. Feedback flows into iteration `N+1` as structured input, not a memory-of-the-conversation. The loop terminates when pass-rate is stable, not when the agent feels done.

Eval workspaces remain local working data. When a release adopts an evaluation report as governed evidence, place that promoted record under `docs/releases/v<MAJOR>/v<MAJOR>.<MINOR>/`; closed snapshots use `docs/archives/`.

## When to Use This Skill

Use this skill when the user wants to:

- Evaluate or benchmark an existing skill (whether their own or a catalog skill)
- A/B test a new skill against a baseline that has no skill loaded
- Optimize a skill's description so it triggers reliably without over-triggering
- Iterate on a skill across multiple rounds with measurable pass-rate deltas
- Set up a regression eval set so future skill edits do not silently regress earlier wins
- Compare two candidate descriptions, instructions blocks, or rationalizations tables on the same prompts
- Score a skill's effective trigger rate on a held-out test set the agent has not seen during authoring

**Trigger phrases**: "evaluate a skill", "benchmark a skill", "A/B test a skill", "optimize a skill description", "run an eval set", "score a skill against test prompts", "iterate on a skill", "skill regression", "with-skill vs without-skill", "eval harness", "eval workspace", "paired runs", "eval iteration", "make this skill actually work".

**When NOT to use**:

- One-off prompt tests with no comparison (use the agent directly)
- Ad-hoc skill drafting that does not yet have stable test prompts (use `workflow/create-custom-command` or AGENTS.md "Adding a New Skill" first)
- Unit-test runs against deterministic code (use the language's native test runner via `tests-generation/unit-tests`)
- Live A/B testing in production (this is offline / batch-mode evaluation, not online traffic splitting)
- Vendor-specific eval suites that ship their own runner (the loop is for the Nexus-Hub catalog; do not rebuild HuggingFace `lm-eval-harness` here)

If the user has not yet stabilized 2-3 test prompts and the skill is still in initial drafting, run `create-custom-command` or the AGENTS.md authoring guide first; this skill is the iteration phase, not the cold-start phase.

## Instructions

The loop has 10 steps per iteration. Steps 1-2 happen ONCE (or at most when the eval set itself needs to grow); steps 3-10 repeat per iteration.

### One-time setup (steps 1-2)

#### 1. Capture user intent and target skill

Ask the user, in one consolidated turn (batch, not ping-pong):

1. Which skill is being iterated on? Provide the path: `catalog/skills/<category>/<name>/SKILL.md`.
2. What is the user's success criterion? (Examples: "trigger rate >= 80% on the test set"; "with-skill output passes all 5 assertions on every eval"; "tokens reduced by 30% vs baseline at equal pass-rate".)
3. What CLI is the user running on? Must be one of `claude` / `gemini` / `codex` / `opencode` (per the v1.1.3 four-hook precedent - no cross-CLI fallback).
4. Where should the workspace live? Default `<skill-name>-workspace/` at the repo root.

Record the answers in the workspace's `intent.md` so iteration `N+1` can re-anchor to the same target without re-asking.

#### 2. Write the eval set

Create `<workspace>/evals/evals.json`. Each entry has:

```json
{
  "id": "eval-001",
  "query": "User-side prompt that should (or should not) trigger the skill",
  "should_trigger": true,
  "assertions": [
    {"text": "Output cites at least one trigger phrase from the skill description"},
    {"text": "Output does not produce more than 200 lines of code"}
  ],
  "tags": ["happy-path", "trigger-positive"]
}
```

Aim for **2-3 prompts initially** (1 trigger-positive, 1 trigger-negative for skip-clause coverage, 1 ambiguous). Grow to 8-15 across iterations. Do NOT write 50 prompts up-front - pass-rate at N=3 with deliberate prompts beats N=50 with shallow ones. The schema is documented at `references/schemas.md`.

### Per-iteration loop (steps 3-10)

#### 3. Spawn paired runs and an optional raw-memory arm

For each `eval-XXX` in `evals.json`, spawn the two standard runs in the same iteration directory:

```
<workspace>/iteration-N/eval-001/
├── with_skill/
│   └── outputs/
│       ├── response.txt
│       └── run_metadata.json   # tokens, duration_ms, exit_code
└── without_skill/
    └── outputs/
        ├── response.txt
        └── run_metadata.json
```

Both runs must use the same CLI (the one declared in step 1). The "with_skill" run loads the target skill via the CLI's skill-loading mechanism (Claude Code: `--skill <path>`; Gemini: `--workflow`; Codex: `--prompt`; OpenCode: `--skill` - the dispatcher in `references/cli-adapter.md` documents per-CLI invocations). The "without_skill" run is the same prompt with no skill. Run them **in parallel within the same turn** when the harness supports it; serial is acceptable when it does not.

When the eval entry declares a readable `raw_memory` path, create `raw_memory/` beside those two directories and run a third condition through the same dispatcher, CLI, model, settings, and eval query. Do not load the target skill in this condition; append the declared file verbatim as prior notes and record `skill_loaded: false` plus `memory_injected: true`. The notes must contain the same prior experience distilled into SKILL.md, not a newly authored substitute.

Run every readable optional arm through the existing dispatcher after the paired response runs exist:

```bash
python scripts/optimize_skill_description.py --evals <workspace>/evals/evals.json --cli <cli> --run-raw-memory --iteration-dir <workspace>/iteration-N
```

This mode resolves each source relative to `evals.json`, preserves the eval query, appends the source text verbatim, and writes `response.txt` plus `run_metadata.json`. It does not grade the response; step 5 sends all present conditions through the same assertion grader.

If the field is absent or its file cannot be read, do not create `raw_memory/`, do not call another model or hosted judge to reconstruct it, and continue with the standard pair. The aggregator records `raw_memory: "not_run"`. This arm exists to test whether distillation adds value beyond supplying raw experience; the reported 6.06 percentage-point finding motivated the comparison but is not a pass threshold.

#### 4. Capture timing and tokens

`run_metadata.json` MUST include `total_tokens` and `duration_ms` per run. Without these the analyzer cannot detect time/token regressions. If the CLI does not report tokens directly, estimate via `len(prompt + response) / 4` and mark `tokens_estimated: true`.

#### 5. Grade against assertions

For each run, invoke the **grader sub-agent** (`agents/grader.md`) with: the eval's assertions, the run's `outputs/response.txt`, and the run's metadata. The grader writes `<run>/grading.json`:

```json
{
  "assertions": [
    {"text": "Output cites at least one trigger phrase", "passed": true, "evidence": "Line 4: 'co-author'"},
    {"text": "Output does not exceed 200 lines", "passed": false, "evidence": "Output is 247 lines"}
  ],
  "pass_rate": 0.5
}
```

Field names are exact (`text`, `passed`, `evidence`) - the aggregator depends on them.

#### 6. Aggregate to benchmark

Run `scripts/aggregate_benchmark.py <workspace>/iteration-N/`. This produces:

- `benchmark.json` - per-eval `pass_rate`, `time_ms_mean`, `time_ms_stddev`, `tokens_mean`, `tokens_stddev`, plus `with_skill_vs_baseline_delta` for each metric
- `benchmark.md` - the same data formatted as a Markdown table for human review

Schema documented at `references/schemas.md`.

#### 7. Launch viewer

Run `scripts/skill_eval_viewer.py <workspace>/iteration-N/` (server mode, default) OR `scripts/skill_eval_viewer.py <workspace>/iteration-N/ --static review.html` (static mode for headless / CI environments). The viewer renders two tabs:

- **Outputs**: per-eval, with_skill vs without_skill side-by-side plus raw_memory when present, with assertion-grading badges and a free-form feedback textarea.
- **Benchmark**: the `benchmark.json` table plus a "Submit All Reviews" button that writes `<workspace>/iteration-N/feedback.json`.

In server mode the viewer opens `http://localhost:<port>` automatically. In static mode the user clicks "Submit All Reviews" and the JS writes a downloadable `feedback.json` Blob.

#### 8. Read user feedback

The user reviews each eval's outputs in the viewer, marks each as `looks-right` / `wrong-direction` / `ambiguous`, and adds free-form notes. The aggregated `feedback.json` is the structured input for step 9.

#### 9. Apply improvement heuristics

Read `feedback.json`, then apply the heuristics from `references/improvement-heuristics.md`:

- **Pushy descriptions**: if a `should_trigger: true` eval failed because the skill did not trigger, the description was probably too narrow. Apply A14's rule (verbatim trigger phrases + explicit `SKIP:` clause).
- **Explain the why**: if outputs technically passed assertions but the user marked them `wrong-direction`, the instructions were probably mechanical. Add a "why" rationale before each step.
- **Repeated work elimination**: if the analyzer reports high time/token variance, the skill is probably doing the same lookup twice. Bundle a deterministic step into a `scripts/<step>.py` tier-3 resource (per A13 / A17).
- **Negative-space coverage**: if a `should_trigger: false` eval triggered anyway, expand the `SKIP:` clause.
- **Assertion calibration**: if every assertion passes on every run with no discrimination, the assertions are too loose; replace at least one with a sharper invariant.

Document the changes in a one-line `iteration-N/decisions.md` so iteration `N+2` can read what changed.

#### 10. Re-run and check stop condition

Spawn iteration `N+1` (steps 3-8 again). The loop terminates when:

- **Pass-rate stabilizes** for two consecutive iterations on the held-out portion of the eval set (the optimizer's 40% test split, or a manually-marked subset).
- **OR** the user explicitly accepts the current state (the "good enough" call).
- **OR** pass-rate regresses for two consecutive iterations - in that case roll back to the last winning iteration and adjust the eval set itself (the prompts may have drifted off-target).

Do NOT run more than 5 iterations without a measurable pass-rate trajectory. If pass-rate is flat across 3 iterations, the bottleneck is the assertions or the eval set, not the skill - go fix those first.

## Persistence discipline (crash-safe long runs)

An eval loop can run for many iterations across hours, and a long run is exactly the situation where context compaction, a crashed CLI, or a killed shell silently discards in-memory state. The defense is to treat the filesystem - not the conversation - as the source of truth for every measured result. The cost is one extra read per write; the payoff is that any interruption resumes from the last completed experiment instead of restarting the loop and re-spending tokens.

Apply these rules whenever a run spans more than a couple of evals or more than one iteration:

- **Write each result immediately.** The moment an experiment is measured (a graded run, an optimizer candidate score, an aggregated benchmark) write it to its own file under the iteration directory before starting the next experiment. Never hold a batch of results in memory to flush at the end - a crash before the flush loses the whole batch.
- **Verify the write by reading it back.** After writing `grading.json` / `benchmark.json` / an optimizer result, immediately re-read and parse the file. A write that produced truncated or invalid JSON is worse than no write, because on resume it looks like completed progress. Treat a failed read-back as a failed experiment and retry the write before moving on.
- **Re-read state at every phase boundary.** Do not trust in-memory state across a phase transition (iteration N -> N+1, or step 9 -> step 10). At each boundary re-read the completed results from disk and rebuild the working set from those files. This makes the loop correct whether it is running fresh or resuming after compaction dropped the earlier turns from context.
- **Keep the log append-only.** Maintain a single append-only progress log (e.g. `<workspace>/run-log.jsonl`) with one line per completed experiment. Never rewrite or truncate it - appending survives an interrupt mid-loop, whereas a rewrite can corrupt the whole history.
- **Write a per-experiment crash-recovery marker.** Before starting an experiment write a `started` marker; on completion write a `done` marker. On resume, any experiment with a `started` marker but no `done` marker is the one that was interrupted - rerun exactly that one and continue. A minimal marker:

    ```json
    {"experiment": "iteration-3/eval-002/with_skill", "status": "done", "result_file": "grading.json"}
    ```

On resume, the procedure is: re-read the markers, find the first `started`-without-`done` experiment (or the first never-started one), and continue from there. Completed experiments are never recomputed - their result files are authoritative. This is what lets a 5-iteration optimizer run survive a mid-run crash without re-spending tokens on the iterations it already finished.

## Reproducible receipts

No headline number ships without a reproducible receipt. A pass rate, a win rate, or an assertion-pass count is a claim, and a claim is only as strong as the artifact a reader can recompute it from. Tie every reported metric to three things:

- **A committed artifact.** The number must be backed by a file committed alongside the report (here the iteration's `benchmark.json`, plus the per-run `grading.json` files it aggregates, under the workspace output directory) from which the metric recomputes exactly. A percentage with no committed source file is a vibe, not a result.
- **A single recompute step.** There must be one documented command that regenerates the headline from that artifact, so a reader can verify it without rebuilding the run. Here that step is `scripts/aggregate_benchmark.py <workspace>/iteration-N/`, which recomputes `benchmark.json` from the graded runs. State the exact step next to the number.
- **A confidence interval, or an honest label.** Every rate carries an interval (for a pass@1 rate, a Wilson score interval is a sound default), so "80%" is reported as "80% (95% CI 55-93%, n=10)" rather than a bare point estimate. When the sample is too small for a meaningful interval, label the number preliminary and unproven instead of publishing a bare percentage. A small-N number stated without that caveat is the exact failure mode this rule exists to prevent.

- **Repeated trials report `pass@k` or `pass^k`, never a single pass or fail.** `[[ai-output-evaluation]]` owns the definitions and the counting rules (errored trials count as non-passes; a retry is not an independent trial); this loop runs the k trials, records each result individually in the per-run `grading.json` files, and reports the figure with k stated, so `pass@3` is written as three recorded results and an aggregate, not as one green mark.

This strengthens the benchmark flow above (steps 6-8): the aggregated `benchmark.json` is the receipt, the aggregator is the recompute step, and the interval is what keeps a two-iteration pass-rate comparison honest rather than a coin flip dressed as progress. The same receipt-and-interval discipline, applied to general output scoring, lives in `[[ai-output-evaluation]]`.

## Description optimizer (A7)

The description-optimizer is a specialized form of the loop that targets only the skill's `description` frontmatter field. Run `scripts/optimize_skill_description.py --skill <path> --evals <evals.json> --cli <name>`. The optimizer:

1. Splits the eval set 60% train / 40% held-out test.
2. Evaluates the current description on each train query 3 times (for stable trigger rate).
3. Asks the chosen CLI to PROPOSE 3 candidate description rewrites based on which train queries failed.
4. Evaluates each candidate on train AND held-out test.
5. Iterates up to `--max-iterations` (default 5).
6. Emits a JSON result with `best_description` selected by **held-out test score** (not train) - this is what prevents overfitting to the prompts the agent saw during candidate generation.

Full schema and worked example at `references/description-optimizer.md`. The optimizer reuses the same CLI dispatcher as the main loop (no cross-CLI fallback; parity-test enforced).

## Trigger-testing techniques

Single-prompt trigger rate catches the most common failure (a description too narrow to fire) but misses three others. The harness adds techniques for each, all reusing the same CLI dispatcher (no new outbound calls, no new dependency):

- **Premature-action detection** - flags a `with_skill` run that invoked a real tool before loading the skill (it started working before loading the gate it was meant to use). Computed by `detect_premature_action()` from the run's tool stream, recorded as `premature_action` in `grading.json`, and surfaced per-eval in `benchmark.json`.
- **Multi-turn triggering** - replays an ordered `turns` list and asserts the skill triggers at the designated `trigger_turn`, catching skills that fire on a cold prompt but not deep in a brainstorm -> plan -> execute flow.
- **Cheap-model fragility** - re-runs the eval against a faster/cheaper model via `--model <name>` (or a per-eval `model` field) to surface descriptions that only trigger on stronger models.

Use premature-action detection on discipline/gate skills, multi-turn on skills whose real use arrives mid-workflow, and the cheap-model test before shipping to users not on the strongest model. Full guidance - what each catches, how to author the eval, how to read the output fields - is at `references/trigger-testing.md`. The `turns`, `trigger_turn`, and `model` eval fields are documented in `references/schemas.md` and are opt-in (single-turn, default-model evals are unaffected).

## Adversarial Eval Battery Design

Paired runs and trigger assertions measure marginal value and routing, but they do not prove the executor resists a tempting shortcut. Add an adversarial battery when the skill claims a discipline, gate, or security property.

Apply these rules:

- **Score axes separately.** Define one axis per claimed behavior and report each result. Do not score "find exactly the planted item": a realistic fixture may contain incidental valid findings, and penalizing those findings trains under-reporting. Score whether the planted discipline held while preserving extra valid results.
- **Give every axis an objective trap.** State the tempting shortcut that constitutes failure, the disciplined behavior that passes, and the artifact comparison that detects the violation. A trap whose verdict depends on whether the report "sounds rigorous" is not an eval.
- **Split the battery into two tiers.** Deterministic axes use no model, are true regression tests, and run on every relevant change. Live-model axes execute the skill against seeded fixtures. One seed is a smoke test, not a benchmark; run multiple seeds and report the exact count.
- **Keep ground truth judge-only.** Store expected results separately from the executor-visible fixture and never place the expected-results file in the executor's context. Exposure turns the eval into answer copying.
- **Randomize each fixture seed.** Vary names, layout, and the path to the planted item while holding the tested invariant constant. A fixed corpus measures recall of that corpus rather than application of the method.
- **Judge artifacts, not self-reports.** Derive the verdict from produced files, execution receipts, and a working-tree diff. The executor's prose claim that it ran a check or preserved a boundary is never the evidence for that claim.

For each axis, record `axis`, `tier`, `trap`, `pass_condition`, `artifact_check`, and `seed`. Keep the judge-only expected result outside the executor-visible fixture. The benchmark reports per-axis results and the number of seeds run, while incidental valid findings remain visible as additional observations rather than false-positive penalties.

## Behavioral-eval schema interop (A4)

The eval set can be exported to and imported from a portable, interoperable behavioral-eval schema so Nexus-Hub's evals interoperate with external skill-eval tooling. The internal `evals.json` stays the source of truth (it carries `should_trigger`, `turns`, `trigger_turn`, `model`, and `tags` that the interoperable schema cannot express); a bidirectional converter handles interop rather than a native re-alignment, so no eval-loop capability is lost and the grading path is unchanged. Run:

```bash
python scripts/skill_eval_convert.py --to-interop evals.json --skill-name <skill> -o interop.json
python scripts/skill_eval_convert.py --to-internal interop.json -o evals.json
```

The converter stashes internal-only fields under an `x_nexus` extension key so both round-trips are lossless. The interoperable schema, the field mapping, and the align-vs-adapter decision are documented at `references/schemas.md`.

## CLI-agnostic adapter

The loop must work on whichever AI CLI the user has installed. The design follows the v1.1.3 four-hook precedent (`catalog/hooks/{claude,gemini,codex,opencode}-diff-review.sh`):

- **Single dispatcher file** (`scripts/skill_eval_viewer.py`, `scripts/aggregate_benchmark.py`, `scripts/optimize_skill_description.py`) with a hard `assert cli in {"claude", "gemini", "codex", "opencode"}` and a per-CLI dispatch branch.
- **No cross-CLI fallback**: each `if cli == "X":` branch invokes ONLY the matching CLI binary - never falls through to a different CLI.
- **Parity invariant enforced by pytest**: `catalog/hooks/tests/test_eval_loop.py::TestEvalLoopCLIAdapter` reads each script's source and asserts that for every `if cli == "X":` branch, no other CLI binary appears in subprocess calls within that branch.

This is option B from the design space (single dispatcher with `--cli` flag) over option A (four parallel scripts). Option B wins on code-duplication grounds; option A's redundancy was justified for shell hooks where the entire script is 80 lines but is overkill for ~300-line Python utilities. Full design rationale at `references/cli-adapter.md`.

## Locked regression sets, per-slice floors, and threshold governance

Eval numbers that can be quietly lowered are not a gate. Three rules, all load-bearing:

1. **Locked, versioned regression set.** The eval corpus is append-only at the example level: you may add a prompt, you may not silently rewrite or delete one that already shipped. The corpus itself carries a version integer. "Did we regress vs corpus v1?" must be answerable from git history plus that version field. A wholesale rewrite of the set is a new corpus version, recorded in the same change that swaps the fixtures.

2. **Per-slice hard floors.** An aggregate pass-rate that holds while one slice collapses is a hidden regression. Every named slice (a fixture, a tag, a skill, a language) has its own floor. A release that keeps the mean green but drops one slice below its floor fails the gate. Worked instance: `extensions/nexus-context-compressor/evals/` stores per-fixture `min_char_reduction` floors in `baseline.json` and `evals/runner.py` fails `--check` when any slice misses.

3. **No lowering thresholds to hide a miss.** Lowering a floor requires its own PR (or a dedicated commit) whose body shows the historical series and names the behavior change that justifies the new number. You do not get to lower a threshold in the same change that would otherwise fail. `--update-baseline` is for raising floors after a real improvement, or for recording a new corpus version, not for making a red gate green.

A compressor eval that only checks mean character reduction is the exact failure these rules exist to prevent: one fixture can stop compressing while the other three still carry the average.

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "I can just eyeball the skill output - no need for paired runs" | Eyeballing N=1 is how you ship a skill that wins on the prompt you authored against and fails on every prompt that drifts an inch. Paired runs against an explicit baseline measure the skill's MARGINAL value, not its absolute value. |
| "Two prompts is enough - I'll get to N=10 later" | If "later" is a separate session, the prompts authored later will be biased by the failures you saw in iteration 1. Three deliberate prompts (1 positive, 1 negative, 1 ambiguous) authored ONCE survive the iteration loop; prompts authored after iteration 3 leak the iteration-3 outputs into the eval set and become a vibes-confirmation. |
| "Tokens and duration don't matter for a skill - it's just guidance" | Skills that 3x token consumption for a 5% pass-rate gain ship and then quietly degrade everyone's session economics. The aggregator surfaces the trade-off so the user makes an informed call instead of an unmeasured one. |
| "Held-out test split is overkill for a 10-prompt eval set" | The optimizer specifically uses held-out test for `best_description` selection because train-only optimization will pick a description that is verbose enough to memorize the train queries verbatim and lose generalizability. Even at N=10, a 60/40 split prevents that overfitting failure mode. |
| "I'll grade the outputs myself - I don't need a grader sub-agent" | Manual grading drifts across an iteration loop: the grader (the user, mid-iteration) starts seeing what they want to see. The grader sub-agent reads the assertion text and the output cold, every time, and writes structured `evidence` per assertion. The user then reviews the grader's calls in the viewer - that is two passes, not one. |
| "I'll run with-skill and look at it, then later run baseline if needed" | "Later" never happens. The iteration directory is structured to hold both runs from the start because the marginal-value question is the only one that matters for skill iteration. A with-skill-only run is a demo, not an eval. |
| "The planted finding is the answer key, so extra findings should lose points" | Penalizing incidental valid findings teaches the executor to suppress discoveries that were not in the seed manifest. Score the planted discipline on its own axis and retain extra valid results as observations. |
| "The four-CLI parity test is bureaucracy" | The test exists because the v1.1.3 four-hook precedent was reverse-engineered from a real bug (a hook fell through to a different CLI when its primary was missing, silently doing the wrong thing). The parity test is a regression guard for that bug class - it costs ~50 lines of pytest and prevents a class of failure that is invisible in production. |
| "I'll run iterations until I feel good about the skill" | The stop condition is data-driven: pass-rate stable across two consecutive iterations on held-out test. "Feel good" is what produced the original draft you are now iterating on. |
| "The aggregate still passes, so one weak slice is noise" | A slice floor exists so a release cannot hide a collapsed fixture behind a healthy mean. Fail the gate; do not average the miss away. |
| "I'll lower the threshold in the same PR so CI goes green" | Lowering a floor to hide a regression is the regression. It needs its own change with a historical comparison. |

## Verification

Binary checklist - each item must describe an observable artifact or state.

- [ ] `<workspace>/intent.md` exists and answers all four step-1 questions (target skill path, success criterion, CLI, workspace path).
- [ ] `<workspace>/evals/evals.json` parses as valid JSON and has at least 2 entries with non-empty `query`, `should_trigger`, and `assertions` fields.
- [ ] At least one iteration directory exists at `<workspace>/iteration-N/` for `N >= 1`.
- [ ] Every `<workspace>/iteration-N/eval-XXX/` directory contains BOTH `with_skill/` and `without_skill/` subdirectories; `raw_memory/` exists only for an eval with a readable declared source.
- [ ] Every `with_skill/outputs/run_metadata.json` and `without_skill/outputs/run_metadata.json` parses and contains `total_tokens` and `duration_ms` (estimated values OK if `tokens_estimated: true` is set).
- [ ] Every present `raw_memory/outputs/run_metadata.json` parses, contains `total_tokens`, `duration_ms`, and `exit_code: 0`, records `skill_loaded: false` plus `memory_injected: true`, and names the same CLI as both paired runs.
- [ ] Every present `raw_memory/` has a completed `grading.json`; incomplete or failed artifacts appear as `status: "invalid"` and do not enter aggregate metrics.
- [ ] `benchmark.json` records `raw_memory: "not_run"` when no optional source exists and aggregates only contract-valid third-arm runs when it does.
- [ ] Every run directory has a `grading.json` produced by the grader sub-agent with the exact field names `text`, `passed`, `evidence`.
- [ ] `<workspace>/iteration-N/benchmark.json` and `benchmark.md` exist and parse cleanly.
- [ ] The viewer can be launched in either server mode (`scripts/skill_eval_viewer.py <iter>`) or static mode (`--static <path>`), and the static-mode HTML opens without errors in a browser.
- [ ] `<workspace>/iteration-N/feedback.json` exists after a viewer review pass.
- [ ] If the optimizer was run, `<workspace>/optimizer/iteration-N.json` exists with a `best_description` field selected by held-out test score (NOT train score).
- [ ] For a multi-iteration run, an append-only `<workspace>/run-log.jsonl` exists and every completed experiment has a crash-recovery marker with `status: done`; a simulated resume recomputes no already-`done` experiment.
- [ ] Every adversarial axis records a tempting shortcut, disciplined pass condition, and objective artifact comparison; no verdict depends on the executor's prose claim.
- [ ] Deterministic adversarial axes run without a model on every relevant change, while live-model results report the exact seed count and do not label one seed a benchmark.
- [ ] Judge-only expected results were absent from the executor-visible fixture, and fixture names, layout, and planted-item paths vary across seeds.
- [ ] Incidental valid findings are retained as observations rather than penalized for differing from the planted item.
- [ ] `catalog/hooks/tests/test_eval_loop.py::TestEvalLoopCLIAdapter` passes (no cross-CLI bleed in any dispatcher script).
- [ ] The eval corpus records a version, and new examples were appended rather than rewritten in place.
- [ ] Every named slice has a floor, and a seeded one-slice miss fails the gate while the aggregate still looks healthy.
- [ ] No threshold was lowered in the same change that would have failed the previous floor.

"The skill seems better now" is not a valid verification criterion. Pass-rate must be measured numerically and compared across at least 2 consecutive iterations.

## Reference files

- `references/schemas.md` - JSON schemas for `evals.json`, `run_metadata.json`, `grading.json`, `benchmark.json`, `feedback.json`, and the optimizer result schema.
- `references/improvement-heuristics.md` - the five improvement heuristics applied at step 9 (pushy descriptions, explain-the-why, repeated-work elimination, negative-space coverage, assertion calibration), each with a worked example.
- `references/cli-adapter.md` - the option-A vs option-B design rationale, the per-CLI invocation patterns for `claude` / `gemini` / `codex` / `opencode`, and the parity-test specification.
- `references/description-optimizer.md` - the 60/40 train-test split rationale, the candidate-generation prompt template, and the held-out-test selection rule for `best_description`.
- `references/trigger-testing.md` - the three trigger-testing techniques (premature-action detection, multi-turn conversation triggering, cheap-model fragility), what each catches, how to author an eval that exercises it, and how to read the new output fields.

## Bundled sub-agent prompts

These are tier-3 resources - the agent loads them only when invoking the corresponding sub-agent during the loop.

- `agents/grader.md` - evaluates assertions against a run's outputs and writes `grading.json` with `text` / `passed` / `evidence` fields.
- `agents/comparator.md` - blind A/B comparison between two outputs without knowing which is the with-skill run, then returns a structured verdict.
- `agents/analyzer.md` - reads `benchmark.json` and surfaces non-discriminating assertions, high-variance evals, and time/token trade-offs.

## Related Skills

- [[ai-output-evaluation]] -- upstream evaluation methodology (rubrics, LLM-as-judge, bias mitigation); this skill operationalizes that methodology specifically for the Nexus-Hub skill catalog.
- [[create-custom-command]] and AGENTS.md "Adding a New Skill" - the cold-start phase that produces the draft this skill iterates on. Its bundled `references/tdd-for-skills.md`, `references/pressure-testing.md`, and `references/persuasion-principles.md` are the test-first authoring methodology that pairs with this empirical loop: TDD-for-skills mines rationalizations from a baseline run during authoring, and this loop uses the same baseline as its marginal-value control during iteration.
- [[code-coverage]] -- covers test coverage for code, not skills; complementary, not redundant.
- [[multi-agent-coordinator]] -- relevant when paired runs spawn parallel sub-agents (grader + comparator + analyzer); this skill calls each sub-agent in serial within an iteration but the multi-agent coordinator covers the parallel case.
- [[prompt-engineering]] -- the upstream skill for designing the prompts that go INTO `evals.json`; use it before running the loop, not during.
- [[known-gaps-tracker]] -- record open eval-set drift, optimizer hyperparameter choices, and any deferred test-prompt expansion under `docs/<version>/known-gaps.md`.
