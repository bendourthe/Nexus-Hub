# Phase 1 Evidence -- Evaluation foundation and judge sensitivity

**Plan**: [v4.13.0-adoption-evidence-driven-agent-improvement](../plans/v4.13.0-adoption-evidence-driven-agent-improvement.md)
**Candidate**: A1
**Phase**: 1 of 7
**Implementation branch**: `feat/v4.13.0-evidence-driven-agent-improvement`
**Branched from**: `develop` at `d231323c`

This file records what was actually run and observed for Phase 1. Synthetic fixtures here prove wiring and direction only. They are not evidence of production model quality and no live model was invoked in this phase.

## Implementation entry prerequisite

The plan holds implementation at a fail-closed gate until a qualified native execution path is established by read-only inspection. That inspection was performed before any catalog edit. The gate is **NOT SATISFIED**, and the maintainer authorized proceeding with Phases 1-5 only, deferring the Phase 6 pilot as UNMEASURED.

### Inspected executables

| Executable | Version | Present |
|---|---|---|
| `claude` | 2.1.156 (Claude Code) | yes |
| `codex` | codex-cli 0.136.0 | yes |
| `gemini` | not on PATH | no |
| `opencode` | not on PATH | no |
| `python` | 3.12.10 | yes |

No provider credential was set in the environment at inspection time: `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, `GOOGLE_API_KEY`, and `GEMINI_API_KEY` were all unset.

### Capability findings against the five required controls

| Required control | Disposition | Observed evidence |
|---|---|---|
| Two accessible model tiers | LIKELY AVAILABLE, unproven | `claude --model` accepts a model for the session; two CLI families are installed. Account-level reachability of two distinct tiers was not exercised, because exercising it spends money. |
| Isolation controls per T022 | AVAILABLE, better than the plan recorded | `claude` exposes `--setting-sources` (restricting user/project/local discovery), `--add-dir` (fixture-scoped tool access), and `--strict-mcp-config` (ignoring all non-declared MCP servers). `codex` exposes `--sandbox`. |
| Bounded subprocess time | MISSING | `scripts/optimize_skill_description.py::_run_subprocess` calls `subprocess.run(cmd, capture_output=True, text=True, check=False)` with no `timeout=` argument. |
| Enforceable aggregate spend accounting | MISSING | `claude --max-budget-usd` bounds a single invocation only. The protocol requires one aggregate ceiling across up to 96 invocations. No component in this repository sums per-call cost against a running total. |
| Observed skill-selection and pause records | MISSING | `scripts/run_trigger_evals.py` is self-described as a "deterministic, model-free gate". `scripts/optimize_skill_description.py` passes `--skill <path>`, which explicitly loads the skill under test and therefore cannot observe whether the agent would have selected it unprompted. |

### Conclusion

Two of the five controls are missing, and both gaps are closed only by writing new accounting and observation code. The plan places that outside its own scope: "Building an adapter or changing the two-model/cost/evidence contract requires a separately scoped decision; it is outside this plan."

The named missing capability is therefore: **an execution path that both enforces an aggregate spend ceiling across the pilot and records organic skill selection rather than forced skill loading.**

Phase 6 is consequently deferred and will be recorded UNMEASURED. Phases 1-5 require no model invocation and proceed under the maintainer's explicit authorization.

## Baseline before Phase 1 edits

```
$ python -m pytest -q tests/skills/test_evaluation_methodology.py --no-cov
155 passed in 0.29s
```

## Artifacts added in this phase

| Path | Kind | SHA-256 |
|---|---|---|
| `tests/fixtures/agent-improvement/judge-sensitivity.json` | frozen synthetic fixture | `3f4e61923b182475be0cab089461ea343c98aa715bd523847d1a181cab52ebbb` |

## Frozen criteria and split

Criteria and split membership were fixed in the fixture before any scoring logic was written, per the plan requirement to freeze before scoring.

- **Criteria**: `execution_evidence`, `claim_support`, `boundary_adherence`, `style_quality`.
- **Split**: train `ME-001, UC-001, CR-001`; development `UC-002, HS-001`; held-out `ME-002, CR-002, HS-002`. Membership is disjoint and verified programmatically.
- **`holdout_touched_count`**: 0.
- **Chance-corrected agreement**: optional, and only where the label type supports it. No universal numeric kappa threshold is set, and an undefined denominator is reported as undefined rather than defaulted.

## Required case coverage

| Required case | Family | Case IDs |
|---|---|---|
| Missing execution | `missing_execution` | ME-001, ME-002 |
| Unsupported factual output | `unsupported_claim` | UC-001, UC-002 |
| Correct refusal | `correct_refusal` | CR-001, CR-002 |
| Unrelated harmless style change | `harmless_style_change` | HS-001, HS-002 |

## Limitations

- Every pair in the fixture is hand-authored. No real trace, session, or model output is stored.
- A passing fixture proves the recipe is wired and the expected directions are stated. It does not prove any judge is calibrated, and it is not a measured LLM result.
- Historical online win/loss data does not exist for this repository, so the optional backtesting path is recorded as unavailable rather than simulated.

## Verification run

```
$ python -m pytest -q tests/skills/test_evaluation_methodology.py tests/skills/test_evidence_driven_improvement.py --no-cov
184 passed in 0.35s

$ python scripts/validate_skills.py --bundles-only
Scanned 337 skills under catalog\skills (bundle audit)
RESULT: PASS (0 errors, 66 warnings)

$ python scripts/ci/run.py --profile fast --quiet
FAIL: 14 passed, 1 failed, 0 skipped, 0 advisory in 78.7s
```

Strict ASCII check over the three changed Markdown files reported 0 non-ASCII lines.

The single fast-profile failure is `check_commit_attribution`, reporting 3186 findings across 3377 scanned commits. The branch carried zero commits at observation time, so the condition is entirely pre-existing and is recorded as WN-1 rather than treated as a Phase 1 regression.

### Negative controls observed failing

The plan requires that controls fail when the guarded behavior is removed. Two are executable rather than declarative:

| Control | Behavior | Result |
|---|---|---|
| `constant_scorer` | returns an identical score for every input | separates no degraded pair, as required |
| `style_reactive_scorer` | moves substantive criteria with wording | drifts on the wording-only control pairs, as required |

A third, `test_correct_refusal_case_would_catch_an_inverted_judge`, asserts the refusing answer outscores the complying one on `boundary_adherence`, so a helpfulness-biased judge would be caught rather than rewarded.

## CI impact record (Phase 1)

Recorded against `[[cicd-architect]]`. No pipeline file was changed; CI/CD is not this phase's deliverable.

| Dimension | This phase | Covered by existing profiles |
|---|---|---|
| New commands | none | n/a |
| New dependencies | none (standard library and existing pytest only) | yes |
| New environment variables | none | n/a |
| New test paths | `tests/skills/test_evidence_driven_improvement.py` | yes -- the existing `tests/skills/` selection collects it automatically |
| New fixtures | `tests/fixtures/agent-improvement/` | yes -- read by the test module, no separate registration |
| New artifacts | none published by CI | n/a |

No uncovered item was found, so nothing from this phase is carried into the terminal reconciliation.

## Phase 1 gate

| Gate element | Result |
|---|---|
| Test failures | 0 |
| Lint errors | 0 new |
| Build | n/a (no build step; catalog and test changes only) |
| Functional smoke | fixture exercised through the executable harness; negative controls observed failing |
| Feature matches expected behavior | yes -- degraded pairs separate, wording-only controls hold steady |

**Verdict: GO.**
