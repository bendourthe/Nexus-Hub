# Session history - v4.13.0 Phase 5: Context fact freshness and revalidation

**Date**: 2026-09-15
**Plan**: [v4.13.0-adoption-evidence-driven-agent-improvement](../../plans/v4.13.0-adoption-evidence-driven-agent-improvement.md)
**Phase**: 5 of 7 (candidate A5)
**Branch**: `feat/v4.13.0-evidence-driven-agent-improvement`

## What was implemented

| Task | Artifact | Outcome |
|---|---|---|
| T017 | `context-pack-builder/SKILL.md` | Optional, prose-first freshness procedure: four things to record, four dispositions, volatile-versus-stable test, five rules |
| T018 | `tests/fixtures/agent-improvement/context-freshness.json` | Six-scenario matrix evaluated against a fixed clock and target identity |
| T019 | `context-engineering/SKILL.md` | Decision-scoped revalidation handoff with three boundaries |
| T020 | `test_evidence_driven_improvement.py` | Extended to 137 tests |

## Test results

```
$ python -m pytest -q tests/skills/test_evidence_driven_improvement.py --no-cov
137 passed in 0.81s
```

No troubleshooting iterations were needed in this phase.

## Design note: what makes a fact stale

The procedure deliberately does not key staleness on age. Two fields in the existing pack format look like they answer currency and do not: `created` records when a fact was written, and `confidence` records how settled it was across observations. Neither says whether the world changed.

The test used instead is whether the world the fact describes can change without anyone editing the pack. A documented architectural decision cannot; a check result, deployment state, or version reading can. The fixture makes that concrete by giving the **stable** fact an **older** timestamp than the stale one, so a rule keyed on age would get both wrong.

## Plan delta

**Disposition: No delta.**

**Evidence considered**: sub-task 5.1 requires preferring prose annotations over new fields and adding no required schema version or memory-store migration. The existing `Optional: Typed Fact Entries` section already carries `created`, `confidence` and `source`, so the freshness procedure was written to annotate those in place rather than extend the shape; a test asserts the text still says no schema version is required and that existing packs stay readable.

Sub-task 5.3's constraint that the future Redis session is "not a prerequisite or a presumed source of implementation details" required no action: nothing in the handoff references a session store, and the revalidation habit sits at the assembly boundary rather than in any reader.

**Consequence for remaining phases**: none for Phase 6, which is deferred. Phase 7 reconciles the evidence set.

## Deviations

None. All four sub-tasks stayed in their stated scope.

## Next steps

Phase 6 is deferred as UNMEASURED (DF-1, QG-1): the plan's entry prerequisite is unsatisfied because no available execution path both enforces an aggregate spend ceiling and observes organic skill selection. Phase 7 has not been run; this session stops at the Phase 5 boundary per the agreed scope.
