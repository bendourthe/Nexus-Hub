# Description optimizer (A7)

`scripts/optimize_skill_description.py` is a specialized form of the eval loop that targets only the skill's `description` frontmatter field. It exists because the description controls **whether the skill loads at all** - and a skill whose body is great but whose description does not trigger reliably looks identical to a missing skill in the user's session.

## Why a separate optimizer (vs the main loop)

The main loop iterates on the entire skill: description, body, instructions, rationalizations, references, scripts. The description optimizer iterates on a single frontmatter line. This focus matters because:

1. The description is high-leverage: a wrong description hides the entire body. A wrong instructions step hides one step.
2. The description is short: candidate generation is cheap (3 candidates per iteration cost ~3-5K tokens, vs 20-50K tokens to re-run a full body iteration).
3. The description is testable on a tiny eval set: trigger / no-trigger is binary, so 8-12 evals cover the trigger surface with reasonable statistical power.

## 60/40 train-test split

The optimizer splits the user's `evals.json` 60% train / 40% held-out test. Train is what the candidate-generation prompt SEES; test is reserved for `best_description` selection.

Why? Without a held-out split, the optimizer would pick the description that wins on the prompts the candidate-generation step saw. That description tends to be longer and more verbose - it memorizes the train queries verbatim. Across the held-out test, that same description performs no better than a shorter, more general one because the train-specific phrasing does not transfer.

The split is deterministic: the script seeds Python's `random` with a fixed seed (default `42`, configurable via `--seed`) so re-runs produce the same train/test partition. This lets the user re-run the optimizer with hyperparameter changes (more iterations, different `--max-candidates`) without the partition shifting underneath them.

For eval sets smaller than N=8, the optimizer warns and recommends growing the eval set first. At N=5, a 60/40 split yields 3 train + 2 test - too thin for stable selection. The optimizer still runs in that case but flags the result with `low_confidence: true`.

## Iteration structure

```
<workspace>/optimizer/
├── iteration-1.json
├── iteration-2.json
├── ...
└── final.json   # symlink or copy of the iteration with the best held-out test score
```

Each `iteration-N.json` (schema at `references/schemas.md`) contains:

- `split` - the train/test partition
- `baseline` - the description being iterated FROM, plus its train and test trigger rates
- `candidates` - the 3 candidate rewrites generated this iteration, each with train and test trigger rates
- `best_description` - the candidate (or the baseline, if no candidate beat it) selected by held-out test score
- `selection_metric` - always `test_trigger_rate`; surfaced as a field so the schema is self-describing

Across iterations, the baseline of iteration `N+1` is the `best_description` from iteration `N`. The optimizer terminates when:

- `--max-iterations` is reached (default 5), OR
- two consecutive iterations show no improvement in held-out test score (early-stop), OR
- `test_trigger_rate` reaches 1.0 (perfect score on held-out test - more iterations can only overfit).

## Candidate generation prompt

The optimizer asks the chosen CLI to rewrite the description by sending a prompt of roughly this shape (the actual text lives inline in `optimize_skill_description.py` and is editable):

```
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
- Output exactly 3 candidate rewrites as a JSON array of strings.

Output:
```

The 3 candidates are then evaluated on train AND test. The CLI's response is parsed with `json.loads`; if parsing fails, the optimizer logs the raw response under `<workspace>/optimizer/iteration-N-raw.txt` and falls back to a single-candidate iteration (the original description) so the loop does not crash.

## Held-out test selection

The selection rule is:

```python
def select_best(baseline: dict, candidates: list[dict]) -> dict:
    pool = [baseline, *candidates]
    return max(pool, key=lambda c: c["test_trigger_rate"])
```

Ties on `test_trigger_rate` are broken by `train_trigger_rate` (the more general description wins among equally-effective candidates on test). Ties on both are broken by description length (shorter wins - shorter descriptions cost fewer always-loaded Tier 1 tokens per the AGENTS.md three-tier loading model).

This selection rule is what prevents the train-overfitting failure mode. Without it, the optimizer's `best_description` would drift toward a 300-word run-on sentence that memorizes the train phrasing.

## `--dry-run` mode

`scripts/optimize_skill_description.py --dry-run` does not call the CLI. Instead it prints what it would evaluate (the train/test split, the baseline description, the candidate-generation prompt template) and exits 0. The pytest test at `catalog/hooks/tests/test_eval_loop.py::TestOptimizerDryRun` runs this mode against a fixture eval set and asserts the train/test split is correct and the output JSON has the right shape.

## CLI parity

The optimizer reuses the same dispatcher as the main loop (single file, `--cli` flag, no cross-CLI fallback). The parity test in `test_eval_loop.py::TestEvalLoopCLIAdapter` is parametrized over (script, cli), so adding the optimizer to the dispatcher set does not require a separate test class.
