# Decision: A required status check must be produced by an unconditionally-triggered workflow

Status: implemented - path scoping moved from workflow triggers to job-level `if:`, `ci.yml`'s nine per-job contexts collapsed into one `ci-required` aggregate, and a validator now fails when a required check comes from a filtered workflow

## Problem

Shipping v3.17.5 on 2026-08-19 required merging pull requests that could not satisfy their own required status checks. GitHub treats a missing check and a skipped check as opposites:

> "If a workflow is skipped due to path filtering, branch filtering or a commit message, then checks associated with that workflow will remain in a **Pending** state." ... "If a **job** within a workflow is skipped due to a conditional, it will report its status as **Success**."
>
> -- [GitHub Docs: Troubleshooting required status checks](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/defining-the-mergeability-of-pull-requests/troubleshooting-required-status-checks), fetched 2026-08-19

An untriggered workflow leaves its check Pending forever; a job skipped by an `if:` reports Success. So workflow-level `paths:` filtering and a job-level `if:` look like the same Actions-minute optimization and behave in opposite ways.

The required-check set was **structurally unsatisfiable in both directions**. `ci.yml` excluded `docs/**`, so nine of its contexts never reported on a docs-only pull request. `doc-colocation.yml` included ONLY `docs/**` and `catalog/skills/**`, so `colocation` never reported on a code-only pull request. No pull request shape satisfied all ten.

### Evidence

Every pull request merged into a protected branch on 2026-08-19, with the required contexts that never came into existence on its head commit. Derived from the check-runs API against the ten contexts required at the time, not from recollection:

| PR | Base | Shape | Files | Required contexts never reported |
|---|---|---|---|---|
| [#50](https://github.com/bendourthe/Nexus-Hub/pull/50) | develop | zero-file back-merge | 0 | 9 (all of `ci.yml` plus `colocation`) |
| [#51](https://github.com/bendourthe/Nexus-Hub/pull/51) | develop | docs-only | 1 | 8 (all of `ci.yml`) |
| [#52](https://github.com/bendourthe/Nexus-Hub/pull/52) | develop | code-only | 2 | 1 (`colocation`) |
| [#53](https://github.com/bendourthe/Nexus-Hub/pull/53) | develop | docs-only | 1 | 8 (all of `ci.yml`) |
| [#54](https://github.com/bendourthe/Nexus-Hub/pull/54) | develop | docs-only | 8 | 8 (all of `ci.yml`) |
| [#55](https://github.com/bendourthe/Nexus-Hub/pull/55) | develop | zero-file back-merge | 0 | 9 (all of `ci.yml` plus `colocation`) |

**Six pull requests, not seven.** The v3.17.6 plan and the session notes both state seven administrator bypasses. Six is what the check-run evidence supports across every pull request merged that day, and the seventh is not reconstructible: it was most likely a second bypass action on one of these six (a re-run after a push), or a miscount in the moment. The verified figure is recorded here in preference to the remembered one.

Two entries are worth reading closely. **#52 is the code-only direction**, missing only `colocation`, which proves the set was unsatisfiable in both directions rather than merely hostile to docs. And **#50 and #55 are zero-file back-merges**: a pull request that changes no files can never match any path filter, so a path-filtered required check is unsatisfiable there by construction. That case needs an administrator merge legitimately, and no amount of filter tuning fixes it.

## Decision

A required status check MUST be produced by a job whose workflow triggers unconditionally on a pull request into the protected branch. Path scoping belongs at the JOB level, expressed with `if:`, never at the workflow level with `paths:` or `paths-ignore:`.

The rule is enforced and satisfied by four things:

1. **`scripts/check_required_check_coverage.py`** resolves every context declared in `docs/policy/required-checks.json` to its producing job and fails when that job's workflow is path- or branch-filtered. It reports `UNPRODUCED`, `CONDITIONAL`, and `BAD` separately because the remedies differ, and runs in `make validate` and in CI's existing `validate` job (not a new job, which would need its own required context).
2. **`ci.yml` and `doc-colocation.yml` trigger unconditionally.** `ci.yml` gained a cheap `changes` detector job and gates its four expensive jobs with `if:`. `doc-colocation.yml` has no detector at all: the check measures 0.1 billed minutes and a detector costs 0.2, so gating it would spend minutes to save none. Both follow the shape `presentify-extractor.yml` had used correctly since v3.12.0.
3. **One aggregate required context replaces `ci.yml`'s nine.** A job-level `if:` is evaluated BEFORE matrix expansion, so a skipped matrix job publishes only its bare job name and never `job (leg)`. Requiring `installer-smoke (ubuntu-latest)` therefore reproduced the original defect in a new form. `ci-required` (`if: always()`, depending on all nine other jobs, allowlist verdict) is required instead, so per-leg names are no longer load-bearing.
4. **`tests/workflows/test_workflow_policy_repo_wide.py` derives the rule from the manifest.** It asserts that a required-check-producing workflow carries no event-level path filter, with the producing set read from `docs/policy/required-checks.json`, so declaring a new required context enforces the rule on its workflow with no second edit.

The two guards approach from opposite ends: the validator works manifest-to-workflow, the policy test works workflow-to-manifest. Both were negative-controlled together, and reintroducing a `paths:` filter on `ci.yml` fails each of them.

## Alternatives considered

- **Move filtering to a job-level `if:` and require the per-leg matrix contexts.** This is the alternative that won for the non-matrix jobs, and it FAILED for the matrix ones. Kept here because it looks complete and is not: the docs-only proof pull request ([#57](https://github.com/bendourthe/Nexus-Hub/pull/57)) reached `BLOCKED` under exactly this design, which is what forced the aggregate.
- **Un-gate the three matrix jobs so they always publish their leg names.** Correct, and rejected on measured cost: roughly 6.3 billed minutes on every docs-only pull request, dominated by the 10x macOS leg, against 1.38 measured for the aggregate. It also leaves per-leg names load-bearing.
- **Remove the offending checks from the required set entirely.** Rejected: it weakens the gate rather than fixing it. This was the interim action actually taken for `build-and-test` on 2026-08-19, which is precisely why it is recorded as a stopgap and not a decision.
- **Add inverse-path no-op workflows that emit the same check names.** Rejected; frozen separately in `docs/decisions/rejected/tooling/2026-08-19-inverse-path-no-op-workflows.md` because it is the plausible-looking answer a future proposer reaches for first.
- **Adopt merge queues.** Rejected: heavy platform machinery for what is a configuration bug, and it would not fix the zero-file back-merge case either.
- **Accept routine administrator bypassing.** Rejected, and named explicitly because it is the status quo this decision replaces. It is not a neutral default: a gate that is routinely bypassed stops being read as a gate, so the bypass habit spends the protection on the cases where it did not matter and has none left for the cases where it does.
- **Keep `validate` and `shellcheck` out of the required set now that `ci-required` covers them.** Rejected: the aggregate is a single point of failure, and both of those jobs are ungated and always run, so requiring them costs nothing and still gates a pull request if the aggregate's own verdict were ever wrong.

## Consequences

- **Docs-only pull requests now run cheap jobs where they previously ran none.** Measured at 1.38 billed minutes (`changes` 0.12, `validate` 0.63, `shellcheck` 0.30, `ci-required` 0.05, `colocation` 0.10). The previous cost was zero minutes and an unmergeable branch.
- **Failure modes inverted, from loud to silent.** Under a trigger filter, a misclassification left a check Pending: obvious and blocking. Under a job condition it skips a job, and a skipped job reports Success. Everything downstream is therefore written fail-closed: the detector defaults to "run" and cannot exit non-zero, every gate is `!cancelled() && ... != 'false'` (both halves needed, because GitHub skips a job whose dependency failed), and the aggregate uses an allowlist verdict so a result value the platform has not used yet fails closed.
- **The aggregate concentrates risk.** One context now stands between a broken build and a green merge for nine jobs. Mitigated by 12 tests covering its three silent-failure modes, an allowlist rather than denylist verdict, and the two redundant always-running required checks above. Tracked as `NI-1` in the v3.17.6 known gaps.
- **The required-check names in `docs/policy/required-checks.json` are load-bearing and must stay in step with actual protection.** Renaming a job silently drops its gate. `check_required_check_coverage.py` catches an `UNPRODUCED` context, and `--sync` prints live protection state via the operator's own `gh` without ever writing.
- **A zero-file pull request still needs an administrator merge.** Nothing here fixes that, and nothing should: with no changed files there is no diff for any detector to classify. Such a merge is legitimate rather than a shortcut, and conflating it with the bypasses above is what made the original problem look larger and vaguer than it was.
- **The rule is now taught, not just enforced.** `catalog/skills/infrastructure/cicd-architect/` carried the antipattern: it recommended workflow-level `paths:` in one section and required a status check in another, without connecting them. Both are corrected, with the long form in that skill's `references/required-status-checks.md`.
