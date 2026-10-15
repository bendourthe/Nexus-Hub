# Required Status Checks and Conditional Execution

Read this before combining a required status check with any form of conditional execution. It is the long form of the rule stated in Pattern 2 of `SKILL.md`.

## The rule

**A required status check MUST be produced by a job whose workflow triggers unconditionally. Filter at the JOB level with `if:`, never at the workflow level with `paths:`.**

## Why, in the vendor's own words

> "If a workflow is skipped due to path filtering, branch filtering or a commit message, then checks associated with that workflow will remain in a **Pending** state." ... "If a **job** within a workflow is skipped due to a conditional, it will report its status as **Success**."
>
> -- [GitHub Docs: Troubleshooting required status checks](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/defining-the-mergeability-of-pull-requests/troubleshooting-required-status-checks), fetched 2026-08-19

So the two forms of filtering are opposites, not variants:

| Where the filter lives | A change the filter excludes |
|---|---|
| Workflow trigger (`on: ... paths:`) | Workflow never starts. Check stays **Pending forever**. The pull request can never merge. |
| Job condition (`if:`) | Job is skipped. Check reports **Success**. The pull request merges. |

Both save the same Actions minutes. Only one of them lets the branch merge.

## The failure this produces

A required check that can never report does not look broken. It looks pending, which reads as "still running". The pull request is simply unmergeable, and the only way through is an administrator bypass. That is the real damage: bypassing becomes routine, and a gate that is routinely bypassed is not protecting anything, including the cases where it mattered.

It compounds when filters point in different directions. One workflow excluding `docs/**` and another including only `docs/**` produce a required-check set that **no pull request shape can satisfy**: a docs-only change misses the first, a code-only change misses the second.

## The fix

Move the filter from the trigger to the job.

```yaml
on:
  push:
    branches: [main]
  pull_request:
    branches: [main]          # no `paths:` here

jobs:
  changes:                     # cheap detector, always runs
    runs-on: ubuntu-latest
    outputs:
      code: ${{ steps.filter.outputs.code }}
    steps:
      - uses: actions/checkout@<sha>
        with: { fetch-depth: 0 }
      - id: filter
        run: |
          # Classify the diff; default to "run everything" on any error.
          echo "code=true" >> "$GITHUB_OUTPUT"

  expensive-job:
    needs: changes
    if: ${{ !cancelled() && needs.changes.outputs.code != 'false' }}
    runs-on: ubuntu-latest
    steps:
      - run: echo work
```

## Three traps in that fix

**1. Fail closed, because the failure mode inverted.** Under a trigger filter, a misclassification left the check Pending: loud and unmergeable. With a job condition it *skips* a job, and a skipped job reports Success: silent. So the detector must default to "run", and must never exit non-zero.

**2. `needs:` alone fails open.** GitHub skips a job whose dependency **failed**, and a skipped required check reports Success. So a broken detector would wave everything through. Both halves of the condition above are load-bearing: `!cancelled()` overrides the skip-on-failed-dependency rule, and `!= 'false'` treats the empty output of a failed job as "run".

**3. A skipped MATRIX job does not publish its per-leg names.** The `if:` is evaluated **before** matrix expansion, so a skipped matrix job emits ONE check run named after the bare job (`installer-smoke`), never `installer-smoke (ubuntu-latest)`. If branch protection requires the per-leg contexts, they never come into existence and you are back to Pending forever.

For a matrix job, require a single **aggregate** context instead:

```yaml
  ci-required:
    needs: [changes, expensive-job, matrix-job]
    if: always()               # must report even when a dependency failed
    runs-on: ubuntu-latest
    steps:
      - env:
          R_expensive: ${{ needs.expensive-job.result }}
          R_matrix: ${{ needs.matrix-job.result }}
        run: |
          set -uo pipefail
          for var in $(env | sed -n 's/^\(R_[A-Za-z0-9_]*\)=.*/\1/p'); do
            eval "result=\${${var}-}"
            case "${result}" in
              success|skipped) ;;   # skipped is the detector working
              *) echo "FAIL: ${var#R_}=${result:-<empty>}"; exit 1 ;;
            esac
          done
```

Make that verdict an **allowlist** (`success` or `skipped` pass) rather than a denylist on `failure`/`cancelled`, so a result value the platform has not used before fails closed. The canonical one-liner `contains(needs.*.result, 'failure')` is shorter but can only express a denylist.

## How to verify it, not assume it

A green configuration review does not prove the platform behaves as documented. Open a real pull request that touches **only** paths every filter excludes, and confirm each required context reports and the pull request reaches a mergeable state with no administrator bypass. Then open the mirror-image pull request. If a required check is missing from either, list the raw check runs for the head commit rather than reading the summary UI, which renders a bare job name and a per-leg name identically at a glance.
