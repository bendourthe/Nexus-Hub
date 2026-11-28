# Testing an Instruction File Before You Edit It

Summary: how to test a behavioral edit to any instruction file (CLAUDE.md, AGENTS.md, a rules file, a platform template) before the edit lands. It specializes four owners and restates none of them. Read it when you are about to change what an instruction file tells an agent to do.

## Who Owns What

Link to the owner, do not restate its rule.

| Concern | Owner |
|---|---|
| Write the failing baseline first and stop when nothing fails | `create-custom-command/references/tdd-for-skills.md` |
| Trial execution, isolation, the canary, repeats, receipts, and the spending cap | the shared evaluator `scripts/evaluate_harness_pairings.py`, contract in `guides/reference/HARNESS_PAIRING_EVALUATION.md` |
| The grader, the aggregator, and locked regression sets | `skill-eval-loop` (this skill) |
| pass@k and unstable trials | `ai-output-evaluation` |

Judge-style assertions are graded by this skill's grader over the final text and the tool-call path that the evaluator retains. The evaluator calls no judge.

## What Instruction Files Add

An instruction file has no trigger, so the skill procedure does not fit it directly. Add these rules on top of the owners above.

1. The instruction file or one named section is the artifact under test. The two arms differ only in that text.
2. Each case set has at least three positive cases, two negative cases, and one keep-working case. A positive case should fail on the current text. A negative case is one where the rule must not fire. A keep-working case checks that an existing behavior still holds after the edit.
3. The isolation canary runs first, as the evaluator's canary workload. It asks the session to quote a marker sentence that exists only in the operator's installed instruction file. Pass means the session cannot. A failed canary makes every trial `not-run`.
4. Each case runs 5 times. The case passes when at least 4 of 5 runs pass.
5. A gain or a loss counts only when the pass count moves by 2 or more. The classes are gain, loss, no change, unstable, and not run. A case that falls between the pass and fail thresholds is unstable. It does not block, and it appears in the table.
6. Case files are committed before the first baseline run. One sharpening is allowed per set. Record its reason and keep the original case.
7. Any loss blocks the edit until it is explained. A set with no failing positive case at baseline does not justify an edit; stop that edit.
8. Record the output tokens per arm and the input tokens the instruction file adds.
9. A stated spending cap stops the run. Every remaining case is `not-run`, and nothing is retried.

## Procedure

1. Write the case set from the sources of the rule, not from the rule text you expect to write.
2. Commit the case files and their evaluator manifest.
3. Run the canary, then run the baseline arm on the current text.
4. Stop if no positive case fails. Otherwise make the edit.
5. Run the same manifest again on the edited text, with the same model and repeats.
6. Report a per-case table with the class of each case. Never report an aggregate pass rate alone.

## Cases

- Assertions are narrow pass or fail questions with a threshold, such as "at most one nominalized action in the summary". Do not write per-sentence absolutes.
- A case that depends on tool use is also judged on the tool-call path, not only the final text. A case file may carry a fixture workspace that the evaluator materializes per trial.
- Grade prose-quality assertions with a cold reader: a judge session given the whole final text and no transcript or earlier version. A phrase list is not a cold reader.
- A false-positive control, a text the maintainer wrote that must draw zero findings, is one of the negative cases for any prose rule.

## Limits

A small case set does not show a population-level improvement. A passing run supports only the cases recorded. Do not claim a quality gain beyond them.

## Expressing a Case Set as an Evaluator Manifest

Each case file keeps `case_kind` and `instruction_section` as case-file fields, and the evaluator does not read them. The mapping, with the field definitions in `schemas.md`:

- One pairing per arm, where the instruction path or text variant is the only difference. Both arms pin the same model.
- `repeats` is 5. The workload holds the prompt and the canary; the workload folder is hashed as the contract describes.
- Per-case grading happens after the run, from the retained final text and tool-call path.

## Related

- `references/schemas.md` documents the two optional case fields.
- `references/cli-adapter.md` covers runner isolation for skill evals. Instruction-file runs use the shared evaluator instead.
