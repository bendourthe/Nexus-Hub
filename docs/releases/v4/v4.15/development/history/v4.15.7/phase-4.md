# CI Speed Phase 4

**Version**: v4.15.7
**Phase**: 4, Pre-push Gate and Setup Fixes (partial: sensitive files are outside the admitted claims)
**Started**: 2026-11-15T14:12:58-08:00
**Ended**: 2026-11-15T14:37:28-08:00 (work complete; the local commit follows immediately)
**Base**: `40f9b0b1c90ee48d2f2fc679b3bfd228ed2d4d74`

## Outcome

T015 (documentation) and T016 (policy amendment and decision record) are written; T015 stays unticked because the AGENTS.md correction is a coordinator write. T014, T017 and T018 need `.pre-commit-config.yaml`, `.github/workflows/post-merge.yml` and `.github/workflows/ci.yml`, which this run did not admit for writing. Their exact diffs and tests are in the sensitive deltas file (S2, S3), and T014's design was proven in a scratch clone. Those three tasks stay unticked.

## Task status

| Task | State | Evidence |
|---|---|---|
| T014 pre-push stage | Not applied, unticked | Scratch proof below; diff and tests in sensitive deltas S2. |
| T015 documentation | Written, unticked | `CONTRIBUTING.md` "Optional Pre-push Gate": install command, measured per-host time, agent-shell timeout, `--no-verify`, `core.hooksPath` caveat, trust boundary, scope. The AGENTS.md correction is proposed in coordinator delta D4; the task closes only after the coordinator applies and verifies it. |
| T016 policy and decision | Done, ticked | `docs/policy/ci-cd-lifecycle-contract.md` section 4.1 and the amended post-merge wording (state diagram, event table), the mirrored row in `cicd-architect/SKILL.md`, and `docs/decisions/proposed/tooling/2026-11-06-develop-scoped-cache-seeding.md` with alternatives (no seeding, dispatch-only, seed from the pull request, seed on main), acceptance criteria and risks. `validate_decision_records.py` reports 120 records OK; `tests/skills/test_cicd_lifecycle_contract.py` 73 passed. |
| T017 seed job and blobless checkout | Not applied, unticked | Diff and tests in sensitive deltas S3. |
| T018 verify and commit | Commit made; verification of the applied setup pending, unticked | Needs S2 and S3 applied; see the scratch proof for the gate itself. |

## Scratch proof of the pre-push gate (T014 and the Verification Expectation, partially)

Run in a clone under the scratch lanes folder (`git clone -c core.longpaths=true --local`), with pre-commit 4.7.0 in a throwaway venv, never against the real remote or the real worktree. The clone's `.pre-commit-config.yaml` got the proposed change; `data/skills.json` got the coordinator's D1 edit in the clone only, so the registry check could pass.

| Step | Observed |
|---|---|
| `pre-commit validate-config` | Valid. |
| Plan's design only (`default_stages: [pre-commit]`) | `pre-commit run --hook-stage pre-push` still ran `trim trailing whitespace` and `fix end of files`: the hooks' own manifest in `pre-commit-hooks` v4.5.0 declares `stages: [commit, push, manual]`, which beats `default_stages`. The plan's failure-mode claim ("keeps every existing hook out of the push stage") does not hold. |
| Plus an explicit `stages: [pre-commit]` on each remote hook (`trailing-whitespace`, `end-of-file-fixer`, `check-yaml`, `check-json`, `mixed-line-ending`, `shellcheck`) | Only `Fast validation profile (pre-push)` runs at pre-push. |
| Control (clean tree) | `Fast validation profile (pre-push)....Passed`, 29 s. |
| A committed Markdown file containing U+202E | `pre-commit hook-impl --hook-type=pre-push` (the exact entry point the installed hook calls) exits 1 after 22 s, prints `Fast validation profile (pre-push).....Failed`, and names `[FAIL] validate_unicode_safety` with `docs\zz-scratch-violation.md:3:8: unsafe Unicode U+202E`. No commit-stage hook output appears. (`check_commit_attribution` also failed in the scratch clone, where history carried a scratch identity; irrelevant to the proof.) |
| `pre-commit install --hook-type pre-push` | Refused while git `core.hooksPath` is set ("hint: `git config --unset-all core.hooksPath`"). I did not work around it: the real `git push` refusal was therefore not exercised, only the hook entry point that git would call. |
| No network or `gh` call in the fast profile | A scan of the 14 scripts the fast profile runs found no network import; `scripts/check_required_check_coverage.py` calls `gh` only behind `--sync`, which the profile does not pass. |

## Verification

| Check | Result | Meaning |
|---|---|---|
| `python scripts/validate_decision_records.py` | 120 decision record(s) OK | The new record has the required sections. |
| `python -m pytest tests/skills/test_cicd_lifecycle_contract.py` | 73 passed | The contract amendment keeps the non-negotiable statements. |
| `python scripts/check_docs_conventions.py`, `validate_unicode_safety.py`, `validate_no_personal_paths.py` on the changed documents | Clean | Hygiene holds. |
| `python scripts/ci/run.py --profile fast` | 17 passed, 1 failed in 141.7 s | The one failure is `check_registry_entries`, awaiting the coordinator's `data/skills.json` delta D1. |
| `nexus-hub attribution check` | VERIFIED | Run before the commit. |

## CI Impact

No pipeline file changed. The intended impact, recorded for the terminal reconciliation: one post-merge job on `develop`, one checkout filter on the `changes` job, one opt-in local pre-push stage, no new required context and no new dependency.

## Plan delta

Disposition: Wrong assumption, non-blocking. Evidence: the plan's T014 relies on `default_stages: [pre-commit]` to keep existing hooks out of the push stage; the scratch run shows remote hooks keep their manifest stages, so each needs an explicit pin. A second plan assumption also failed in practice: `pre-commit install` refuses where `core.hooksPath` is set, so the opt-in does not work for such users. Consequence for remaining phases: Phase 5's CI reconciliation (T023) must carry the pinned-hooks form of the diff, T015's documentation already states the fallback, and T014, T017, T018 remain open until the pipeline-file permission exists.

## Deferred Final Validation

The full profile still runs once in 9B (T027). T018 additionally needs S2 and S3 applied before it can be ticked.

## Open Work

- Coordinator: apply D1, D4, D5 (coordinator deltas) and, with the typed permission, S1 to S3 (sensitive deltas).
