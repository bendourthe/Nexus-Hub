# Session history - v4.13.0 Phase 1: Evaluation foundation and judge sensitivity

**Date**: 2026-09-15
**Plan**: [v4.13.0-adoption-evidence-driven-agent-improvement](../../plans/v4.13.0-adoption-evidence-driven-agent-improvement.md)
**Phase**: 1 of 7 (candidate A1)
**Branch**: `feat/v4.13.0-evidence-driven-agent-improvement`

## What was implemented

| Task | Artifact | Outcome |
|---|---|---|
| T001 | `tests/fixtures/agent-improvement/judge-sensitivity.json` | Frozen synthetic fixture: 8 cases, 4 criteria, disjoint train/development/held-out split, 2 declared negative controls |
| T002 | `catalog/skills/developer-experience/ai-output-evaluation/references/evaluator-validation.md` | Added Step 6 (controlled degradation, per-criterion direction, multi-criterion and inconclusive handling, optional backtesting), 5 failure-mode rows, 9 verification items |
| T003 | `catalog/skills/ai-development/eval-pipeline-audit/SKILL.md` | Sensitivity evidence folded into existing concern 4; routing row added; ten-concern inventory and three-recommendation cap preserved |
| T004 | `tests/skills/test_evidence_driven_improvement.py` | 29 tests, including an executable sensitivity harness with two failing negative controls |

## Test results

```
$ python -m pytest -q tests/skills/test_evaluation_methodology.py tests/skills/test_evidence_driven_improvement.py --no-cov
184 passed in 0.35s

$ python scripts/validate_skills.py --bundles-only
RESULT: PASS (0 errors, 66 warnings)
```

The fast repository profile reports 14 passed / 1 failed. The single failure is `check_commit_attribution` over pre-existing history; the branch carried zero commits when it was observed. Recorded as WN-1.

## Entry-prerequisite decision

The plan's fail-closed entry gate was evaluated by read-only inspection before any catalog edit. Two of five required controls are absent, so Phase 6 is deferred as UNMEASURED (DF-1, QG-1). The maintainer authorized proceeding with Phases 1-5 on that basis. No model was invoked and no money was spent in this phase.

## Plan delta

**Disposition: Incomplete** (non-blocking).

**Observed evidence**: the plan's entry prerequisite treats the required T022 isolation controls as capability the repository must establish, and names only two repository scripts as candidate paths. Inspection of the installed hosts found that several of those controls already exist natively in the `claude` CLI: `--setting-sources` restricts user/project/local instruction discovery, `--add-dir` scopes filesystem access, `--strict-mcp-config` suppresses all non-declared MCP servers, and `--max-budget-usd` bounds a single invocation. `codex` additionally exposes `--sandbox`. The plan did not account for these.

**Why this does not change the gate**: the two decisive gaps are untouched by that finding. There is still no aggregate spend accounting across the pilot's up-to-96 invocations, and still no path that observes *organic* skill selection, because the only skill-loading mechanism available forces the skill with `--skill <path>`. The gate therefore holds and Phase 6 remains deferred.

**Consequence for remaining phases**: Phases 2 through 5 are unaffected; none of them invokes a model. The consequence is for the eventual Phase 6 scoping decision, which is narrower than the plan assumed: the separately scoped work needs aggregate cost accounting and a selection-observation mechanism, and does **not** need to build an isolation stack, because the host already supplies one. That should be stated when DF-1 is scoped, so the adapter is not over-built.

## Deviations

None. All four sub-tasks were implemented in their stated scope.

## Next steps

Phase 2: private agent traces and observable evidence (T005-T008).
