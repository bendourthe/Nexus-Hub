# Session History - v3.16.1 Phase 4: Synthetic data, human review, and skill quality

**Date**: 2026-08-08
**Plan**: [docs/releases/v3/v3.16/plans/v3.16.1-evals-and-selective-installation.md](../../plans/v3.16.1-evals-and-selective-installation.md)
**Phase**: 4 of 8 (not the final phase; no release-readiness workflow ran)
**Branch**: `feat/v3.16.1-evals-and-selective-installation`
**Outcome**: Complete. All quality gates passed; no new known gaps. Closes the skill-native adoption track (A1-A7).

## Goal

Complete the evaluation lifecycle with coverage-driven synthetic cases, a disciplined human-review contract, and a directive-density quality signal for skill authoring - the last work before the plan switches domains to selective installation.

## Sub-tasks completed

### 4.1 - Controlled synthetic evaluation data (T019)

Created `references/synthetic-data.md` (135 lines). Seven steps: declare dimensions and allowed values; record constraints with their reasons; choose a coverage target from a cost table; generate in batches against named cells; filter for duplicates, source leakage, difficulty, and a human spot check; recompute achieved coverage and report the uncovered cells; keep synthetic cases out of the held-out split.

### 4.2 - Human review interface contract (T020)

Created `references/review-interface.md` (121 lines). Defines the annotation schema, what blindness actually requires (four specific things the interface must hide), randomized ordering from a recorded seed, keyboard-first and accessible controls, confidence and abstention as first-class fields, adjudication with a `taxonomy_change_required` flag, append-only history, local autosave and resume, and deterministic export with no implicit upload.

### 4.3 - Directive-density review (T021)

Added step 4b to `skill-stocktake`: sample each substantial section (cap 8 per skill) and ask one binary question - does it yield an observable action, decision rule, artifact, gate, or verification condition? Report directive/expository counts and name the expository sections. Explicitly advisory, with four non-goals and two new Common Rationalizations rows.

### 4.4 / 4.5 - Integration, tests, stabilization (T022, T023, T024)

Linked both references from the parent skill's routing table, added two inline rules, two rationalizations, and two verification items. Extended `test_evaluation_methodology.py` from 114 to 155 assertions and added `test_skill_stocktake_directive_density.py` with 22.

## Decisions made

- **The directive-density check is a binary per-section question, never a ratio.** The obvious implementation - count imperative verbs, flag a low ratio - would flag the "Reality" column of every Common Rationalizations table in the catalog, which is explanatory by design and is the most valuable prose in the schema. A ratio is also tunable, so prose gets optimized toward it. The binary question leaves no number to game, and the non-goals name the exact content the signal must never argue for deleting.
- **The stocktake test ships a reference implementation of the rule, honestly labeled.** The check is agent-executed prose, so nothing runs it. But a signal set that matches everything is worse than no signal, because it produces a reassuring report while catching nothing. `classify_section` in the test encodes the five signals and proves on fixtures that they separate explanation-only prose from prose that changes behavior. The module docstring states plainly that this is test-only and not what the agent executes.
- **The near-boundary fixtures are the ones that matter.** The fixture set deliberately includes a Common Rationalizations table entry (mostly prose, names a gate) and a decision-rule-only section with no command at all. Both must classify as directive. A fixture set of obvious extremes would pass under a rule that is actually broken.
- **Unanswerable queries are a declared dimension value, not an afterthought.** Unbounded generation almost never produces them, because the generating model is looking at the corpus and writing questions it can answer. A system's behavior on unanswerable queries is usually its worst and its least tested, and declaring dimensions first is the mechanism that surfaces it.
- **Coverage is recomputed after generation, not inferred from the target.** Declaring a pairwise target and generating against it does not mean the target was hit. The reference requires reporting achieved coverage and naming the uncovered cells, which then become the next batch's plan. Without this step the whole method is setup with no payoff.
- **The review-interface reference prescribes no framework.** It defines observable completion checks so any stack satisfies it, including a terminal prompt loop. A test asserts no framework is named, because the natural drift is toward a worked example in one library that readers then treat as a requirement.

## Troubleshooting trail

- **Nothing failed.** All 22 stocktake assertions and all 41 new methodology assertions passed on first run, and the full suite was green without a troubleshooting iteration. Recorded because a phase with a clean run and a phase whose failures went unrecorded look identical otherwise.
- **Branch state was verified before any write**, following the Phase 3 incident: confirmed `feat/v3.16.1-evals-and-selective-installation` at `c19865c2` with all five Phase 1-3 artifacts present on disk and a clean tree.

## A1-A7 completion check

The plan's 4.5 asks for confirmation that every A1-A7 comparison item has an implemented owner and that no seven-skill duplicate structure was introduced. Verified against the comparison's own declared target column rather than asserted:

| Item | Declared target | Status |
|---|---|---|
| A1 RAG evaluation metrics | `rag-implementation/references/evaluation.md` | Present (Phase 1) |
| A2 Evaluation-pipeline audit | `catalog/skills/ai-development/eval-pipeline-audit/` | Present (Phase 2) |
| A3 Trace-centered error analysis | `ai-output-evaluation/references/error-analysis.md` | Present (Phase 3) |
| A4 Evaluator validation | `ai-output-evaluation/references/evaluator-validation.md` | Present (Phase 3) |
| A5 Synthetic evaluation data | `ai-output-evaluation/references/synthetic-data.md` | Present (Phase 4) |
| A6 Review-interface contract | `ai-output-evaluation/references/review-interface.md` | Present (Phase 4) |
| A7 Directive-density check | heuristic in `skill-stocktake` | Present (Phase 4) |
| A8 Selective installation | installers, runner, tests, docs | Phases 5-7, not started |

Structure check: one new skill was created across the whole track (`eval-pipeline-audit`), plus five Tier-3 references under two existing owner skills. The seven-skill verbatim import the plan's Out of Scope section forbids did not happen.

## Verification

- `python -m pytest -q tests/skills/test_evaluation_methodology.py` - 155 passed (114 before this phase, +41)
- `python -m pytest -q tests/skills/test_skill_stocktake_directive_density.py` - 22 passed
- `python -m pytest -q tests/skills tests/validators` - 1041 passed, 3 skipped
- `python scripts/validate_skills.py --bundles-only` - PASS, 0 errors, 0 warnings across 271 skills (all four `ai-output-evaluation` references correctly seen as linked)
- `python scripts/validate_skills.py --quality` - PASS, 0 errors, 6 pre-existing warnings, none on either changed skill
- `python scripts/run_trigger_evals.py --gate` - PASS, 0 un-allowlisted collisions, 0 routing failures
- `python scripts/scan_skill_security.py` over both changed skills - 7 files scanned, 0 findings
- `python scripts/validate_unicode_safety.py` - 0 errors, no findings in new or changed files
- `check_version_sync`, `check_base_template_parity`, `verify_platform_contracts`, `check_platform_contract_freshness`, `scan_supply_chain_iocs`, `validate_no_personal_paths` - all PASS
- `git diff --check` - clean
- Sizes within norms: `ai-output-evaluation` 338 lines, `skill-stocktake` 175, references 121-147

## CI impact

None. All changed files live under `catalog/skills/` and `tests/skills/`, both of which the workflow's `paths` filter includes, and `tests/skills` already runs as its own CI step. The new test module is picked up automatically because CI invokes the directory, not individual files.

## Files changed

| File | Change |
|---|---|
| `catalog/skills/developer-experience/ai-output-evaluation/references/synthetic-data.md` | new |
| `catalog/skills/developer-experience/ai-output-evaluation/references/review-interface.md` | new |
| `catalog/skills/workflow/skill-stocktake/SKILL.md` | step 4b, 2 rationalizations, 2 verification items |
| `catalog/skills/developer-experience/ai-output-evaluation/SKILL.md` | 2 routing rows, 2 inline rules, 2 rationalizations, 2 verification items |
| `tests/skills/test_evaluation_methodology.py` | +41 assertions |
| `tests/skills/test_skill_stocktake_directive_density.py` | new, 22 assertions |
| `docs/v3/v3.16/known-gaps.md` | Phase 4 no-new-gaps record |
| `docs/DEVLOG.md`, `docs/todos.md` | Phase 4 entry and tracker |

## Next steps

Phase 5 switches domains entirely: audit every install path, write the normative selection contract, build the shared fixture matrix, and implement the pure Python resolver. It is the first phase of this plan to touch runtime code rather than documentation, and the plan rates it strong-tier / high-effort with a large downstream blast radius. NI-1's four repaired bundle references and the dependency-closure rules become load-bearing there.
