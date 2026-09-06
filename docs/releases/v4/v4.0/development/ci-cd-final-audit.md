# CI/CD Final Audit and Terminal Pipeline Comparison

**Project**: Nexus-Hub
**Phase**: 8 - Architecture refactor, known-gaps reconciliation, and CI/CD
**Date**: 2026-08-25
**Compared against**: [`ci-cd-lifecycle-contract.md`](ci-cd-lifecycle-contract.md), via the 23-field list in `catalog/skills/infrastructure/cicd-architect/references/repository-native-profiles.md`
**Mode**: `[[cicd-architect]]` existing-pipeline comparison

This is the terminal reconciliation the lifecycle requires of every plan's final phase, run against Nexus-Hub's own pipeline. It is also the first real exercise of the comparison downstream plans will use, so the shape here is the shape those get.

## 1. Ownership map after the refactor

Who owns what, once. Every other surface cross-links rather than restating.

| Concern | Owner | Everyone else |
|---|---|---|
| CI/CD lifecycle policy | `catalog/skills/infrastructure/cicd-architect/SKILL.md` | `cd-pipeline-generator` and `cicd-integration` declare conformance in their bodies |
| Provider event models | `cicd-architect/references/provider-event-models.md` | cited by basename from the skill body |
| Profile and report schemas | `cicd-architect/references/repository-native-profiles.md` | cited by basename from the skill body |
| Required-check topology | `docs/policy/required-checks.json` + `scripts/check_required_check_coverage.py` | the contract cites them; `cicd-architect` Step 5 summarizes and links |
| Plan-phase lifecycle | `implementation-plan` (generation) + `implement-phase` (execution) | `/plan` and `/implement` state the guarantee only |
| Final-phase template | `implementation-plan/references/mandatory-final-phase.md` | the skill body keeps the rule and points at it |
| Commit atomicity | `code-commit-workflow` | `implement-phase` step 8.9 cross-links |
| Branch model and publication timing | `git-branching-workflow` | the contract cites it |
| Release ordering | `catalog/commands/update.md` + `version-upgrade` Step 0 | `implement-phase` 9C-9E hands off |
| Executable validation | `scripts/ci/profiles.py` | the Makefile and `.github/workflows/` each delegate in one line |
| External repository settings | [`github-ci-settings-runbook.md`](github-ci-settings-runbook.md) | nothing mutates them |

## 2. Architecture refactor findings

### Structure detectors

| Detector | Result |
|---|---|
| Orphaned bundle files | none (`validate_skills.py --bundles-only`, 0 errors) |
| Duplicated command lists | none remaining. `ci.yml` re-declared the validator sequence as 31 steps and now calls one profile |
| Stale CI examples in the catalog | none. `cicd-integration`'s worked example triggered on push AND pull_request; corrected in Phase 2 |
| Obsolete workflow fragments | none. No workflow was left gated on an event it can no longer receive (see the `nexus-memory` finding below) |
| Files deleted this branch | 0 |
| Files added this branch | 33 |
| Empty directories | 8, all pre-existing and out of scope |

### The empty directories, deliberately not touched

`.antigravitycli`, `.claude/worktrees`, `docs/v3/v3.17/development/history`, `docs/v3/v3.18/development`, `docs/v3/v3.19/development`, and three under `extensions/nexus-code-search/benchmarks/.work`.

None was created by this plan. Git does not track empty directories, so none is in the diff, and the two under `.claude/` and `.work/` are gitignored runtime artifacts. The three under `docs/v3/` are residue from prior archival passes and belong to a `[[docs-layout-refactor]]` run, not to this one. Cleaning them here would be exactly the adjacent-code cleanup the boundaries rule forbids.

### The near-miss worth recording

Removing the `push` trigger from the extension workflows left `nexus-memory.yml`'s three-OS locking matrix conditioned on `github.event_name == 'push'`, which can never be true again. Left alone, that matrix would have silently stopped running, and a skipped job reports Success.

That is the fail-open shape this entire release exists to remove, and it was one line away from being introduced BY the fix for it. It is caught, re-gated to the pull request, and recorded here because the general lesson is not about that job: removing a trigger requires auditing every `if:` that referenced it.

## 3. Terminal pipeline comparison

Provider DETECTED: GitHub Actions (`.github/workflows/`, 11 files, 26 jobs).

PASS requires observable evidence per field. A green run is not evidence: a pipeline that checks nothing is green for the wrong reason.

| # | Field | Verdict | Evidence |
|---|---|---|---|
| 1 | Provider detected | PASS | GitHub Actions, 11 workflow files |
| 2 | Profiles exist | PASS | `fast`, `full`, `platform`, `report`, `release` in `scripts/ci/profiles.py`; each resolves via `--list`; `tests/ci` asserts the roster is exactly these five |
| 3 | No duplicated validator | PASS | `test_ci_does_not_re_declare_the_validator_list` fails on any `run: python scripts/<name>.py` in `ci.yml`. Zero matches |
| 4 | Feature-push runs nothing | PASS | no workflow has an unfiltered `push:`; the only branch-filtered push is `post-merge.yml` on `main`/`develop`, and the only tag push is `release.yml` |
| 5 | Integration gate is complete | PASS | `ci.yml` on `pull_request` into `main`/`develop` plus `merge_group`, running validate, shellcheck, tests, tests-windows, bootstrap (ubuntu + macOS), bootstrap-windows, install-smoke (3 OS), installer-smoke (3 OS) |
| 6 | No duplicate post-merge suite | PASS | `ci.yml` has no `push` trigger. `test_no_validation_workflow_pairs_a_pull_request_with_the_same_branch_push` holds repo-wide, with a documented exemption for per-job `github.event_name` separation |
| 7 | Post-merge is minimal | PASS | `post-merge.yml` runs the `fast` profile and a provenance report. Asserted: `--profile full` and `--profile platform` are absent |
| 8 | Release is separate | PASS | `release.yml` on `tags: ['v*']` and dispatch, running `--profile release` only. Asserted: no `pytest`, no `full`, no `platform` |
| 9 | Aggregate required check | PASS | one `ci-required` job, `if: always()`, allowlist verdict (`success` or `skipped`), vacuous-pass guard, pure-bash evaluation |
| 10 | No per-leg required context | PASS | no context in `docs/policy/required-checks.json` contains a parenthesis |
| 11 | Scoping is job-level | PASS | `ci.yml` triggers carry no `paths`/`paths-ignore`; the `changes` job classifies and jobs gate on `if:`. `check_required_check_coverage.py` reports 10 contexts across 2 branches, all produced unconditionally |
| 12 | Runner selection | PASS | GitHub-hosted only; no `self-hosted` in any `runs-on:` |
| 13 | Expensive legs pre-merge | PASS | Windows and macOS legs moved from `push` to `pull_request` in Phase 7 |
| 14 | Immutable references | PASS | every `uses:` across 11 workflows is a 40-character SHA with a version comment; asserted per workflow |
| 15 | Least-privilege permissions | PASS | all 11 declare a workflow-level block; `codeql.yml` was the last without one |
| 16 | Caching | PASS | pip caches keyed to `.pre-commit-config.yaml` and `extensions/*/pyproject.toml`; deliberately absent from the bootstrap and smoke jobs, which test a cold install |
| 17 | Concurrency | PASS | `cancel-in-progress: true` on validation; `false` on `release.yml` and `post-merge.yml`, asserted both ways |
| 18 | Untrusted forks | PASS | no `pull_request_target`, no self-hosted runner, no secret consumption in any validation workflow |
| 19 | Reports produced | PASS | `summary.md`, `summary.json`, per-group JUnit, `metadata/environment.json`, all verified by hand after a real `fast` run |
| 20 | Reports published | **PARTIAL** | the summary reaches `$GITHUB_STEP_SUMMARY` with `if: always()` in all three lifecycle workflows. Artifact UPLOAD is deferred as DF-1 |
| 21 | Deployment boundary | PASS (N/A) | Nexus-Hub deploys nothing. `cd-pipeline-generator` carries the rule for repositories that do |
| 22 | Failure recovery | PASS | documented in the contract section 11 and in runbook 9F; a local reproduction is required before any re-run, asserted by `test_a_red_check_reopens_the_phase_and_requires_a_local_reproduction` |
| 23 | External settings | PASS | [`github-ci-settings-runbook.md`](github-ci-settings-runbook.md), 8 sections plus a verification checklist. Nothing mutated automatically |

### Verdict

**22 PASS, 1 PARTIAL, 0 FAIL.**

The one PARTIAL is field 20, recorded as known gap DF-1 with an owner and a next step. Its cause is worth stating rather than hiding: uploading requires `actions/upload-artifact`, every third-party action here is pinned to a full commit SHA, and that SHA must be FETCHED from the vendor rather than recalled. Nexus-Hub has already shipped one companion file that was fabricated rather than found (the v3.15.0 `.kimi/agent.yaml`) and had to drop it. A plausible-looking SHA would break every run at once; a floating `@v4` tag would violate the pinning rule the same phase asserts.

What ships instead satisfies the human-readable half of the contract on every result, including a failure, and uses no action at all.

## 4. What this comparison could NOT establish

Stated explicitly, because a comparison that lists only what it proved reads as a comparison that proved everything.

- **The new topology has not run against real GitHub.** Every assertion above is static: YAML parsing, trigger inspection, contract tests. Nothing has observed GitHub running `ci.yml` on a pull request, `post-merge.yml` on a merge, or `release.yml` on a tag, nor confirmed that the five required contexts still resolve. Recorded as WN-1. The plan's own publication is the first real-world test.
- **The `full` profile has not completed end to end on this host.** Every constituent group is verified individually (1825 tests in `tests/skills` plus `tests/validators`, 85 in `tests/ci`, 97 in `tests/workflows`, the whole validator chain via `make validate`), but not the single aggregated invocation and its cross-group exit status. Recorded as DF-2.
- **Actual minute savings are projected, not measured.** The direction is certain (one comprehensive run instead of two, and no third on the tag), but the figure depends on the live per-unit runner price, which must be read from the billing page rather than assumed from a remembered multiplier. Runbook section 6 covers it.

## 5. Cost model, before and after

| Event | Before | After |
|---|---|---|
| Ordinary feature-branch push | nothing | nothing |
| Integration pull request | Linux-only for most jobs | full three-OS coverage |
| Push to `develop` or `main` | the complete suite WITH the expensive matrix legs | one Linux `fast` profile plus a provenance report |
| `v*` tag | the complete suite again | the `release` profile only |
| Per multi-phase plan | one full pipeline run per phase, if the author took the offered push | one, at the final phase |

The last row is the largest change and appears in no workflow file. It is the lifecycle default that Phases 3 and 4 removed.

## 6. Evidence commands

```text
python scripts/ci/run.py --profile fast --reports-dir reports        PASS  12/12, 8.0s
python scripts/ci/run.py --profile release --reports-dir reports     PASS  3/3, 5.9s
python scripts/validate_workflow_security.py                         PASS  11 workflows
python scripts/check_required_check_coverage.py                      PASS  10 contexts, 2 branches
python scripts/check_base_template_parity.py                         PASS
python scripts/validate_doc_budgets.py                               PASS
python scripts/check_registry_entries.py --check --strict            PASS
python scripts/check_agentskills_conformance.py                      PASS  325 skills
python scripts/run_trigger_evals.py --gate                           PASS  0 routing failures
python scripts/validate_skills.py --bundles-only                     PASS  0 errors
python scripts/validate_decision_records.py                          PASS  23 records
python -m pytest tests/ci -q                                          85 passed
python -m pytest tests/workflows -q                                   97 passed, 13 skipped
python -m pytest tests/validators/test_ci_workflow_contract.py -q      49 passed
python -m pytest tests/skills tests/validators -q                   1825 passed, 2 skipped
```
