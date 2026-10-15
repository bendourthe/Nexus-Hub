# Description optimizer (A7)

`scripts/optimize_skill_description.py` is a specialized form of the eval loop that targets only the skill's `description` frontmatter field. It exists because the description controls **whether the skill loads at all** - and a skill whose body is great but whose description does not trigger reliably looks identical to a missing skill in the user's session.

## Why a separate optimizer (vs the main loop)

The main loop iterates on the entire skill: description, body, instructions, rationalizations, references, scripts. The description optimizer iterates on a single frontmatter line. This focus matters because:

1. The description is high-leverage: a wrong description hides the entire body. A wrong instructions step hides one step.
2. The description is short: candidate generation is cheap (3 candidates per iteration cost ~3-5K tokens, vs 20-50K tokens to re-run a full body iteration).
3. The description is testable on a small eval set because trigger / no-trigger is binary. Small is not the same as precise, though: 8 to 12 evals are enough to catch a description that clearly fails, but a 40% test split of them is 3 to 5 queries, whose score moves in steps of 20 to 33 points. Treat a score from a set that size as a coarse signal, not a measured rate.

## Splits and the `reported_optimistic` label

The optimizer chooses between two split modes with `--split` (default `auto`).

**Two-way (the legacy 60/40 split).** Train is what the candidate-generation prompt SEES; the remaining 40% is the test split, which both selects `best_description` and produces the reported `test_trigger_rate`. Selecting on a split never shown to candidate generation still prevents the main failure: a description that memorizes the train queries verbatim and does not transfer. But because the winner is the candidate that scored best on that same split, its score is biased upward: on new queries it will usually do somewhat worse. The output therefore carries `reported_optimistic: true`, and that score must not be described as held-out.

**Three-way (train / validation / test).** `--split auto` uses it only when the set has 24 or more entries AND every split can hold at least 2 entries of each `should_trigger` class; below that the test split would be too small for its score to mean anything, so the two-way split is kept and labelled. Train takes its `--train-fraction` (default 0.6) of each class, and validation and test divide the rest evenly. Validation selects; the test split is scored exactly once, after the loop, for the final description and for the original, so its score is a real held-out figure and `reported_optimistic` is `false`. Equivalent queries are grouped before assignment so one group never spans two splits: an explicit `group` field wins (any non-empty value, compared as text), otherwise the text normalized for case, whitespace, and punctuation, taken from the query or a multi-turn entry's joined turns, so a one-turn entry and a query with the same text share a group. Because an explicit `group` overrides text matching, once one variant of a prompt carries a `group`, give every variant that same `group`. An entry with no `should_trigger` counts as a positive, the same default the scorer uses. When a set of 24 or more entries still falls back, the optimizer prints the reason on stderr. The two-way split stays ungrouped, so its old partitions are unchanged.

Every catalog eval set today has fewer than 24 entries, so every run is two-way and labelled. `--split two-way` forces the legacy split on a large set.

Both modes are deterministic: the script seeds Python's `random` with a fixed seed (default `42`, configurable via `--seed`) so re-runs produce the same partition. This lets the user re-run the optimizer with hyperparameter changes (more iterations, different `--max-candidates`) without the partition shifting underneath them.

For eval sets smaller than N=8, the optimizer warns and recommends growing the eval set first. At N=5, a 60/40 split yields 3 train + 2 test - too thin for stable selection. The optimizer still runs in that case but flags the result with `low_confidence: true`.

## Iteration structure

```
<workspace>/optimizer/
├── iteration-1.json
├── iteration-2.json
├── ...
└── final.json   # copy of the last iteration; in three-way mode it also carries the one-time test scores
```

Each `iteration-N.json` (schema at `references/schemas.md`) contains:

- `split` - the partition: `train_ids` and `test_ids`, plus `validation_ids` in three-way mode
- `baseline` - the description being iterated FROM, plus its train score and its selection-split score
- `candidates` - the 3 candidate rewrites generated this iteration, each with the same two scores
- `best_description` - the candidate (or the baseline, if no candidate beat it) with the best selection-split score
- `selection_metric` - `test_trigger_rate` in two-way mode, `validation_trigger_rate` in three-way mode
- `split_mode`, `selection_split`, `reported_split`, `reported_optimistic` - which mode ran, which entry ids chose the winner, which produced the reported score, and whether that score is biased upward

Across iterations, the baseline of iteration `N+1` is the `best_description` from iteration `N`. The optimizer terminates when:

- `--max-iterations` is reached (default 5), OR
- two consecutive iterations show no improvement in the selection-split score (early-stop), OR
- the selection-split score reaches 1.0 (more iterations can only overfit).

In three-way mode the iterations never read the test split. After the loop, `final.json` gains `test_trigger_rate` (the final description) and `original_test_trigger_rate` (the description the run started from), each scored once.

## Candidate generation prompt

The optimizer asks the chosen CLI to rewrite the description by sending a prompt of roughly this shape (the actual text lives inline in `optimize_skill_description.py` and is editable):

```
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
- Output exactly 3 candidate rewrites as a JSON array of strings.

Output:
```

The 3 candidates are then evaluated on train and on the selection split. The CLI's response is parsed with `json.loads`; if parsing fails, the optimizer logs the raw response under `<workspace>/optimizer/iteration-N-raw.txt` and falls back to a single-candidate iteration (the original description) so the loop does not crash.

## Selection rule

The selection rule, where `metric` is the run's `selection_metric`:

```python
def select_best(baseline: dict, candidates: list[dict], metric: str) -> dict:
    pool = [baseline, *candidates]
    return max(pool, key=lambda c: c[metric])
```

Ties on the selection score are broken by `train_trigger_rate` (the more general description wins among equally-effective candidates). Ties on both are broken by description length (shorter wins - shorter descriptions cost fewer always-loaded Tier 1 tokens per the AGENTS.md three-tier loading model).

This selection rule is what prevents the train-overfitting failure mode. Without it, the optimizer's `best_description` would drift toward a 300-word run-on sentence that memorizes the train phrasing.

## `--dry-run` mode

`scripts/optimize_skill_description.py --dry-run` does not call the CLI. Instead it prints what it would evaluate (the split mode and partition, the baseline description, the candidate-generation prompt template) and exits 0. The pytest test at `catalog/hooks/tests/test_eval_loop.py::TestOptimizerDryRun` runs this mode against a fixture eval set and asserts the train/test split is correct and the output JSON has the right shape.

## CLI parity

The optimizer reuses the same dispatcher as the main loop (single file, `--cli` flag, no cross-CLI fallback). The parity test in `test_eval_loop.py::TestEvalLoopCLIAdapter` is parametrized over (script, cli), so adding the optimizer to the dispatcher set does not require a separate test class.
