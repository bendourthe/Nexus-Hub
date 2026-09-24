# GitHub settings read-back for v4.3 WN-2

This frozen follow-up records the GitHub repository settings that can be read with the current account credential on 2026-09-24. It supports the [v4.3 known-gaps ledger](../../../../releases/v4/v4.3/known-gaps.md) and does not change any repository setting or close its remaining billing gate.

## Read-only results

| Requested value | Observed result | Boundary |
|---|---|---|
| Default artifact and log retention | `days=90`, `maximum_allowed_days=90` from `GET repos/bendourthe/Nexus-Hub/actions/permissions/artifact-and-log-retention` | Repository-level read-back, not an assertion that every workflow uses the default; jobs may specify a shorter artifact expiry. |
| Merge-queue state | `Repository.mergeQueue(branch:"develop")=null` and `Repository.mergeQueue(branch:"main")=null`; `main` is the default branch. The REST repository-rulesets list contained zero entries. | No queue object was returned for either named branch at this read-back. Classic branch protection remains a separate control, not proof of a queue. |
| Per-runner-class billing minutes | Not read. `GET users/bendourthe/settings/billing/usage` returned HTTP 404 and an explicit message that the current credential needs the `user` scope. | No runner-minute or cost value is inferred from workflow run durations, and no OAuth scope was added. |

The relevant GitHub contracts are the [repository artifact-retention endpoint](https://docs.github.com/en/rest/actions/permissions#get-artifact-and-log-retention-settings-for-a-repository), [GraphQL repository merge-queue field](https://docs.github.com/en/graphql/reference/repos#repository), and [user billing usage endpoint](https://docs.github.com/en/rest/billing/usage#get-billing-usage-report-for-a-user). The billing endpoint also requires access to GitHub's enhanced billing platform, so a token-scope change alone is not guaranteed to return a report.

## Reproduction and next gate

The successful read-only calls used `gh api repos/bendourthe/Nexus-Hub/actions/permissions/artifact-and-log-retention` and a GraphQL `repository` query with separate `develop` and `main` string variables passed to `mergeQueue(branch:)`. The failed billing call used `gh api users/bendourthe/settings/billing/usage` with the existing credential. No token, billing payload, or account-private page was retained here.

The remaining gate is an account-owner read of runner-class Actions minutes, either in GitHub's billing UI or through an explicitly authorized credential with the required billing read access. Record the period and the runner-class values before closing WN-2; leave it open if the account cannot expose that data.
