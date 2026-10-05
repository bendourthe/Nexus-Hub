# Decision: Optimizer selection and reporting split

Status: proposed - label the two-way optimizer score as optimistic and add a grouped three-way split for eval sets of 24 or more entries

## Problem

`scripts/optimize_skill_description.py` splits an eval set 60/40. It selects `best_description` by the test-split score and then reports that same score as the result. A score used to pick the winner is biased upward, because the winner is by construction the candidate that did best on those queries, so the reported number overstates how the description will do on new queries. The skill-eval-loop docs called that split "held-out", which made the overstatement look like a measurement.

Changing only the split does not fix this on its own. On 2026-09-30 the catalog held 88 `trigger-cases.json` sets of 2 to 12 entries and one optimizer-format `evals.json` of 3 entries. A three-way split of a 12-entry set leaves a test split of about 3 queries, whose score can only be 0, 1/3, 2/3, or 1.

## Proposal

1. **Two-way mode stays the default for small sets and says what it is.** Every existing output key keeps its exact value and meaning. The output gains `split_mode: "two-way"`, `selection_split` and `reported_split` (both equal to `split.test_ids`), and `reported_optimistic: true`.
2. **Three-way mode runs only when it can produce a meaningful score:** 24 or more entries, with at least 2 entries of each `should_trigger` class in each of train, validation, and test. `--split auto` (the default) chooses it when eligible; `--split two-way` forces the legacy split.
3. **In three-way mode,** iterations score train and validation only. Validation selects (`selection_metric: "validation_trigger_rate"`) and drives early stop, the plateau rule, and the perfect-score stop. The test split is scored exactly once after the loop, for the final description and for the original, and the results are recorded in `final.json` as `test_trigger_rate` and `original_test_trigger_rate`. `reported_optimistic` is `false`.
4. **Split integrity.** Three-way mode groups entries before assignment, so one group never spans two splits. The key is an explicit `group` field when present; otherwise the query text normalized for case, whitespace, and punctuation; for a multi-turn entry, its turns joined and normalized. It stratifies by class. Train takes `--train-fraction` (default 0.6) of each class, and validation and test divide the rest evenly. The same `--seed` (default 42) makes it deterministic.

**Compatibility contract.** A consumer that reads `selection_metric`, `split.train_ids`, `split.test_ids`, `baseline.test_trigger_rate`, or `candidates[].test_trigger_rate` from a two-way run sees no change. Three-way mode changes the meaning of `selection_metric` and drops the per-iteration test score, and a consumer distinguishes the two modes by `split_mode`. Because no catalog set reaches 24 entries, no existing run changes mode. The key table lives in `catalog/skills/workflow/skill-eval-loop/references/schemas.md`.

A status of `proposed` satisfies the v4.13.8 plan. Moving this record to `implemented` waits until a three-way run has been exercised on a real 24+ entry set.

## Alternatives considered

- **Always three-way, rejecting sets below the minimum.** Rejected: every catalog set is below 24, so the optimizer would stop working for every current user in exchange for a guarantee nobody could use yet. Labelling the small-set result keeps the tool usable and honest.
- **A 12-entry minimum for three-way mode.** Rejected: a 12-entry set gives a test split of about 3 queries, whose score can move only in thirds. That split would claim to be held-out while being too coarse to compare two descriptions, which is worse than an openly optimistic score.
- **Keep two-way and disclose the bias only in prose.** Rejected: prose does not travel with the number. A `final.json` copied into a report or a PR loses the surrounding doc, and the machine-readable `reported_optimistic` field is what lets a reader or a later check tell the two kinds of score apart.
- **Cross-validation over repeated splits.** Rejected for now: it multiplies the number of provider calls by the fold count on a tool where every evaluation is a paid CLI run, and it still needs a final untouched split to report an unbiased number. It stays a possible later addition for large sets.

## Acceptance criteria

- `catalog/hooks/tests/test_eval_loop.py::TestOptimizerSplit` passes. It covers split sizes and the class minimum, determinism, no group spanning two splits, the `reported_optimistic` label, validation-only selection under a stub scorer, the test split scored once for the final description and once for the original, and unchanged old keys in two-way mode.
- A dry run on a 24-entry balanced set reports `split_mode: three-way`, `selection_metric: validation_trigger_rate`, and `reported_optimistic: false`. A dry run on any catalog set reports `two-way` and `true`.
- The skill-eval-loop docs no longer call the two-way selection split "held-out".

## Risks

- **A consumer that assumes `test_trigger_rate` exists on every iteration** breaks on a three-way run. This is mitigated by `split_mode` and by the fact that no current set triggers three-way mode, but a future large set would expose it.
- **Grouping by normalized text** catches case, spacing, and punctuation variants but not paraphrases. Two paraphrases of one intent can still land in different splits unless the author sets `group`.
- **The 24-entry threshold is a judgement,** chosen so that each test class holds at least 2 entries and the test split is about 6. A different minimum may prove better once real large sets exist.
