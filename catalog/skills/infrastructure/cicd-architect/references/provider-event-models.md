# Provider Event Models

Per-provider mapping of the canonical lifecycle to real trigger syntax, plus the limits of merge-only enforcement on each. Read cold; each section stands alone.

The canonical lifecycle this maps is defined in `SKILL.md` Step 1 and Step 4. In short: ordinary feature-branch pushes run nothing, the integration pull request runs the complete gate against the merge result, the protected-branch merge runs only minimal post-merge work, and the release event runs only the release profile.

## The event classes

Every trigger in any provider falls into exactly one of six classes.

| Class | Purpose | Cost posture |
|---|---|---|
| `feature-push` | nothing | must not trigger validation |
| `integration` | the one comprehensive gate, against the merge result | the expensive one; spend here |
| `merge-queue` | the same gate, against the queued merge result | same as `integration` |
| `post-merge` | smoke, publication, provenance on the protected integration branch | must be minimal |
| `release` | package, sign, publish from a tag or approved dispatch | bounded, never cancelled |
| `schedule` | drift against the outside world | the only legitimate re-run of a proven tree |

## GitHub Actions

### Trigger mapping

| Class | Trigger |
|---|---|
| `integration` | `pull_request: branches: [main, develop]` |
| `merge-queue` | `merge_group:` |
| `post-merge` | `push: branches: [main, develop]` in a separate, minimal workflow |
| `release` | `push: tags: ['v*']` or `release: types: [published]`, plus `workflow_dispatch` |
| `schedule` | `schedule: - cron: ...` |
| `feature-push` | no trigger at all |

### Merge-only enforcement

`push` carries no evidence of a merge. It becomes merge-only when branch protection on that branch rejects direct pushes and requires a pull request. Without that setting a `push`-triggered "post-merge" workflow fires on any developer push, and the post-merge assumptions (the tree was reviewed, the gate was green) are false. State the dependency in a comment on every `push`-filtered workflow.

`merge_group` is the strongest available signal, because it only exists inside a merge queue. Where the repository has a merge queue, gate the comprehensive suite on `pull_request` OR `merge_group` and treat `push` as post-merge only.

### Traps specific to this provider

- **Workflow-level `paths:` plus a required check.** The workflow does not start, so its check stays Pending forever and the branch cannot merge without an administrator bypass. Filter with a job-level `if:` instead: a skipped job reports Success.
- **Per-matrix-leg required contexts.** A job-level `if:` is evaluated before matrix expansion, so a skipped matrix job publishes only its bare job name. Require an aggregate context.
- **`needs:` alone fails open.** A job whose dependency failed is skipped, and a skipped required check reports Success. Gate with `if: ${{ !cancelled() && needs.<detector>.outputs.<flag> != 'false' }}`; both halves are load-bearing.
- **`pull_request_target`.** Runs with the base repository's secrets against fork code. Do not use it in a validation workflow.
- **Concurrency and releases.** `cancel-in-progress: true` is correct for pull-request validation and wrong for a release or deployment. Use a separate group per class.

### Runners

`ubuntu-*` is the baseline rate. `windows-*` and `macos-*` bill at higher multiples, historically about two and about ten. Treat those as the current price ratio rather than a constant: derive the weight from the live per-unit price when the number matters.

Self-hosted runners on a public repository must never execute fork pull requests. Restrict with repository settings plus a `runs-on` label that fork runs cannot reach.

## GitLab CI

### Trigger mapping

| Class | Rule |
|---|---|
| `integration` | `rules: - if: $CI_PIPELINE_SOURCE == "merge_request_event"` |
| `merge-queue` | merge trains: `$CI_MERGE_REQUEST_EVENT_TYPE == "merge_train"` |
| `post-merge` | `rules: - if: $CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH` in a minimal job set |
| `release` | `rules: - if: $CI_COMMIT_TAG` |
| `schedule` | `rules: - if: $CI_PIPELINE_SOURCE == "schedule"` |
| `feature-push` | no rule matches |

### Notes

- Merge request pipelines run against the source branch by default; **merged results pipelines** run against the merge result and are the correct choice for the `integration` class. Enable them explicitly.
- Protected branches plus "merge request required" give the same merge-only property as GitHub branch protection.
- There is no aggregate-check concept: GitLab gates on the pipeline's overall status, which already behaves like an aggregate. The equivalent trap is a job with `allow_failure: true` that a reader assumes is blocking.
- `workflow: rules:` at the top of the file is the provider's supported way to prevent duplicate pipelines (the classic branch-pipeline plus merge-request-pipeline double run). Set it deliberately; the double run is this provider's version of the same cost defect.

## Jenkins

### Trigger mapping

| Class | Mechanism |
|---|---|
| `integration` | multibranch pipeline, `CHANGE_ID` present (a pull request build) |
| `merge-queue` | not natively supported; approximate with a queue job |
| `post-merge` | branch build where `BRANCH_NAME` matches the protected branch |
| `release` | tag build, or a parameterized job requiring an approver |
| `schedule` | `triggers { cron(...) }` |
| `feature-push` | exclude with a branch-source filter |

### Notes

- Jenkins has no native concept of a required status check. The gate lives in the forge (GitHub, GitLab, Bitbucket) via a status-publishing plugin, so the aggregate rule applies at the forge, not in the `Jenkinsfile`.
- Agents are self-hosted by definition. The public-repository rule therefore applies in full: never build untrusted fork code on a persistent agent with credentials or state.
- A shared library is the natural home for the thin trigger layer. Keep the profile calls in the repository, not in the shared library, or every repository's validation becomes invisible from its own checkout.

## CircleCI, Azure Pipelines, Buildkite, Woodpecker, Drone

These differ in syntax, not in shape. Map each to the six classes and check three things:

1. Can the provider trigger on the merge result rather than the branch tip? If not, record it as a known gap: the gate proves less than it appears to.
2. Does the provider expose a single overall status the forge can require? If it exposes per-job statuses, require the aggregate only.
3. Does the provider let a filtered-out pipeline leave a required status unresolved? If yes, filter inside the pipeline, not at the trigger.

## Generic webhook runners

A repository whose CI is a webhook into a bespoke runner has none of the above guarantees. The minimum conforming shape:

- The runner invokes the repository's profiles and nothing else.
- It publishes exactly one status back to the forge.
- It refuses to run for a fork or an unknown sender.
- It reports a status on failure, including its own crash, so a dead runner is not indistinguishable from a passing one.

## Recording a provider gap

Where a provider cannot express a required property, record it rather than accepting it silently:

```text
Field: integration runs against the merge result
Provider: <name>
State: NOT SUPPORTED
Consequence: the gate proves the branch tip, not the post-merge tree
Mitigation: require an up-to-date branch before merge
Recorded as: <version> known gap DF-<n>
```

A silently accepted gap becomes an assumed guarantee within one release cycle.
