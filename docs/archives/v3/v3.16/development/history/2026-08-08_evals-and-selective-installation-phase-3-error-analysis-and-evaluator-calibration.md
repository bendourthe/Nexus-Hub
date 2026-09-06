# Session History - v3.16.1 Phase 3: Error analysis and evaluator calibration

**Date**: 2026-08-08
**Plan**: [docs/releases/v3/v3.16/plans/v3.16.1-evals-and-selective-installation.md](../../plans/v3.16.1-evals-and-selective-installation.md)
**Phase**: 3 of 8 (not the final phase; no release-readiness workflow ran)
**Branch**: `feat/v3.16.1-evals-and-selective-installation`
**Outcome**: Complete. All quality gates passed; no new known gaps.

## Goal

Turn evaluation failures and judge quality into measurable, reproducible workflows owned by `ai-output-evaluation`, filling two reference targets that Phase 1's contract and Phase 2's routing table already point at.

## Sub-tasks completed

### 3.1 - Trace-centered error analysis (T014)

Created `references/error-analysis.md` (147 lines, cold-readable). Five steps: deliberate trace sampling with a table of what each sampling method can and cannot support; a non-overlapping taxonomy where every category carries definition, inclusion criteria, and exclusion criteria; quantification by count, share, severity, and tractability; root-cause hypotheses that must state their own refuting evidence; and promotion of confirmed patterns into minimized `regression_case` artifacts.

### 3.2 - Evaluator validation and calibration (T015)

Created `references/evaluator-validation.md` (146 lines). Train / development / held-out separation with `holdout_touched_count` as the leakage signal; blind annotation, double-labeling, and adjudication as the ground-truth discipline; the confusion matrix with precision, recall (TPR), and specificity (TNR); a fully computed worked example; a Wilson interval on the recall figure; the prevalence effect; threshold tuning restricted to development data; an advisory-versus-gate table; recalibration triggers; and a seven-row failure-mode table.

### 3.3 - Parent-skill integration (T016)

Added an "Evaluating Output vs Validating the Evaluator" section to `ai-output-evaluation/SKILL.md` with a routing table linking both references by basename and restating the two load-bearing rules inline. Added three Common Rationalizations and three Verification items, including the two the plan requires: a release-gating evaluator must have held-out evidence and a documented disagreement review. Added three Related Skills. Nothing was removed; the body went 305 -> 330 lines, inside the 500-line norm.

### 3.4 / 3.5 - Tests and stabilization (T017, T018)

Extended `tests/skills/test_evaluation_methodology.py` from 74 to 114 assertions.

## Decisions made

- **Exclusion criteria are mandatory per taxonomy category, not optional polish.** A category with a definition but no boundary drifts into its neighbors, two reviewers file the same trace differently, and every frequency count silently stops meaning anything. The worked pair in the reference (`unsupported_claim` versus `retrieval_miss`) also encodes the retrieval-before-generation order from Phase 1, so a retrieval failure can never be filed as a hallucination.
- **Single-label by earliest cause is the default convention.** When retrieval misses and the model then invents an answer, the category is `retrieval_miss`. Fixing the earliest link in the chain is what prevents the downstream failure, so single-label counts point at the work rather than double-counting one root cause.
- **The prevalence effect got a worked example rather than a warning.** Holding recall and specificity fixed and moving only the failure rate from 30 percent to 5 percent drops precision from 0.60 to 0.16. Stated as a caution it reads as a footnote; shown as arithmetic it explains why a judge that validated well gets ignored within a week of deployment. The 0.156 figure is asserted by a test for exactly that reason.
- **`holdout_touched_count` is the honesty mechanism, not bookkeeping.** Nothing prevents re-evaluating against the held-out split; what the field does is make the number of times visible, so a reader can discount a figure produced after ten tuning rounds. The test asserts the field exists because it is the kind of thing an editor removes as clutter.
- **Verification distinguishes advisory from gating evaluators.** The plan asked for held-out evidence and documented disagreement review on a release-gating evaluator specifically. Applying those requirements to every evaluator would make advisory scoring impractically expensive and push teams to skip evaluation entirely; the cost belongs where the consequence is.

## Troubleshooting trail

- **The session had moved to `develop`, and Phase 3 nearly got built on the wrong tree.** At phase start the working tree was on `develop` (tip `6e345e19`), not the feature branch. Every Phase 1 and 2 artifact was absent from disk: the audit skill, the RAG reference, the artifact contract, and both test modules. The commits were safe on `feat/v3.16.1-evals-and-selective-installation` (`db62248b`, `11c956dc`), but building here would have produced two references pointing at a contract that does not exist on this branch, and T017 would have had no test file to extend. Stopped and asked rather than proceeding; switched back on the user's instruction and verified all five artifacts present and the tree clean before writing anything. Worth recording because the failure mode is silent: every individual file operation would have succeeded.
- **A heredoc append failed on shell quoting.** Appending the Phase 3 tests via `cat >> file <<'PY'` hit an unmatched-quote parse error. Switched to an anchored edit on the file's final assertion, which is also safer: it fails loudly if the anchor has moved, where a blind append does not.

## Verification

- `python -m pytest -q tests/skills/test_evaluation_methodology.py` - 114 passed (74 before this phase, +40)
- `python -m pytest -q tests/skills tests/validators` - 978 passed, 3 skipped
- `python scripts/validate_skills.py --bundles-only` - PASS, 0 errors, 0 warnings across 271 skills (both new references correctly seen as referenced, not orphaned)
- `python scripts/validate_skills.py --quality` - PASS, 0 errors, 6 pre-existing warnings, none on `ai-output-evaluation`
- `python scripts/run_trigger_evals.py --gate` - PASS, 0 un-allowlisted collisions, 0 routing failures
- `python scripts/scan_skill_security.py catalog/skills/developer-experience/ai-output-evaluation --fail-on high` - 4 files scanned, 0 findings
- `python scripts/validate_unicode_safety.py` - 0 errors, no findings in either new file
- `check_version_sync`, `check_base_template_parity`, `verify_platform_contracts`, `check_platform_contract_freshness`, `scan_supply_chain_iocs`, `validate_no_personal_paths` - all PASS
- `git diff --check` - clean

## CI impact

None. Both references live under `catalog/skills/`, which the workflow's `paths` filter includes, and `tests/skills` already runs as its own CI step, so the 40 new assertions are covered with no workflow edit. This phase is deliberately outside QG-1's scope, which concerns only the `docs/**` exclusion affecting the artifact-contract assertions.

## Files changed

| File | Change |
|---|---|
| `catalog/skills/developer-experience/ai-output-evaluation/references/error-analysis.md` | new |
| `catalog/skills/developer-experience/ai-output-evaluation/references/evaluator-validation.md` | new |
| `catalog/skills/developer-experience/ai-output-evaluation/SKILL.md` | routing section, 3 rationalizations, 3 verification items, 3 related skills |
| `tests/skills/test_evaluation_methodology.py` | +40 assertions |
| `docs/v3/v3.16/known-gaps.md` | Phase 3 no-new-gaps record |
| `docs/DEVLOG.md`, `docs/todos.md` | Phase 3 entry and tracker |

## Next steps

Phase 4 completes the skill-native track: `references/synthetic-data.md` and `references/review-interface.md` under the same parent skill, plus a directive-density check in `skill-stocktake`. After that, Phase 5 switches domains entirely to the selective-installation contract, where NI-1's four bundle references (repaired in Phase 2) and the dependency-closure rules become load-bearing.
