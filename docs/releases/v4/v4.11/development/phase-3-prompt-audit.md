# Phase 3 evidence - Bounded prompt audit

Evidence for Phase 3 (T007-T009) of the [v4.11.0 adoption plan](../plans/v4.11.0-adoption-cache-and-diagram-quality.md). Checks both synthetic audits against D3, records which requirements and proving commands survived each one, states the cross-owner contracts that were preserved, and marks the behavioural evidence this phase explicitly does not produce.

## T007 - The audit procedure

One reference was added, `catalog/skills/ai-development/prompt-engineering/references/prompt-audit.md`, linked from a new short section in that skill's `SKILL.md`. The count matches the plan's ceiling of at most one new prompt-audit reference.

Structure: declare the task and intended outputs; identify each instruction's origin and owner against a six-row table; review all six adopted categories recording a decision per instruction rather than per category; propose the narrowest edit; account for every instruction as kept, merged, or removed; run the retained acceptance checks.

Preserved by default, as required: user requirements, trust and security boundaries, hard budgets, and observable proof requirements. The procedure states that emphasis words such as "must", "always" and "never" are never treated as evidence that an instruction is dispensable, on the grounds that emphasis usually records someone having previously watched the rule get ignored.

Currency-dependent categories (scaffolds, stale examples, retired settings) route to `[[model-prompting-research]]`. An unavailable source leaves the finding **unresolved**; the procedure explicitly forbids guessing that a setting is retired.

The excluded list is stated in the reference itself: no bulk prompt rewrite, no automatic model tuning, no private session-log collection, no central prompt registry.

## T008 - The two synthetic audits checked against D3

D3 requires that a bounded audit produces a before/after decision record while preserving user requirements, trust boundaries, hard budgets, and required proof, and that synthetic demonstrations are explicitly labelled.

### Case A - valid merge

Six instructions in, two out. Every instruction appears in the decision table.

| Retained requirement | Survived as |
|---|---|
| The stated task ("summarize the changes") | Kept verbatim |
| The proving command | **Kept verbatim**: `git log --oneline v1.2..v1.3` with the confirmation clause |

Four self-check repetitions were merged into the single proving command that already existed. Nothing that produced observable output was removed. This is the case the plan required: a repeated self-check ritual merged while retaining a proving command.

### Case B - refused removal

Four instructions in, four out. The proposed edit is refused rather than narrowed.

| Retained requirement | Survived as |
|---|---|
| Source screening before substantive reading | **Refused removal**; trust boundary |
| Fetched instruction-like text treated as quoted task data | **Refused removal**; trust boundary |

The decision table records a reason per refusal rather than a smaller prompt, and states that a security instruction reads as boilerplate precisely when it is working. This is the case the plan required: a prompt where removing a security or source-origin instruction would be invalid.

### Category coverage

Cases A and B exercise categories 1 (redundant verification) and 2 (emphasis). A compact table supplies one short example each for categories 3, 4, 5 and 6 with a per-instruction decision and its expected output, including one escalation (a contradiction that cannot be resolved inside the audit) and one unresolved finding (a retired setting whose source cannot be fetched). All six categories therefore carry a worked decision.

### Labelling

Both cases are labelled synthetic in the reference. The closing section states that an audit does not demonstrate improved agent behaviour, task completion, or lower cost, and that word counts and lexical checks are not evidence of agent behaviour.

## Cross-owner contracts preserved

- **`[[verification-before-completion]]`**: no rule owned by that skill was changed. The reference distinguishes a redundant in-turn self-re-check (category 1, mergeable) from evidence for a claim made to a human (preserved by default), and Case A demonstrates the distinction rather than asserting it.
- **v4.9 WN-2**: the gap's status is unchanged. The reference explains why the vendor claim and the catalog skill are not the same rule, and states that reconciling them would be a decision record rather than a prompting edit. No edit to `docs/releases/v4/v4.9/known-gaps.md` was made.
- **Source screening and prompt-injection defence**: reinforced by Case B rather than restated as a new rule; the owning skills keep the rule.
- **Hard budgets**: listed in the origin table with the budget owner named as the only party who may remove one.

## T009 - Checks run

```text
$ python scripts/validate_skills.py --bundles-only
Scanned 336 skills under catalog\skills (bundle audit)
RESULT: PASS (0 errors, 64 warnings)

$ python -m pytest tests/skills/test_cache_share_example.py -q
..................
18 passed in 0.59s

$ python scripts/ci/run.py --profile fast
PASS: 13 passed, 0 failed, 0 skipped, 0 advisory in 68.5s
```

The bundle audit is the meaningful check for this phase: it fails on a bundled reference that no `SKILL.md` links. Its pass proves the new reference is reachable rather than orphaned. The 64 warnings are pre-existing and none names the prompt-engineering skill. The cache regression was re-run to confirm Phase 1 and 2 work in the sibling reference is undisturbed.

## Evidence explicitly NOT exercised

This phase changes no runtime behaviour and claims none. The following are marked not exercised because this phase does not change or claim them:

- **Live skill selection**: no evidence that the new reference is loaded, or loaded at the right time, by any agent.
- **Runtime budget behaviour**: no measurement of tokens, calls, or wall-clock for an audited prompt.
- **Savings**: no measurement that an audited prompt costs less or performs better.

Each of those requires a qualified live runner with a bounded budget, which the separate v4.11 evaluation plan owns. No lexical or word-count check in this phase should be read as a proxy for any of them.

## CI impact

One linked reference and one new `SKILL.md` section. No new executable surface, dependency, schema, environment variable, test path, or artifact. Covered by the existing bundle audit and Markdown hygiene groups. Nothing carried forward to the Phase 6 reconciliation.
