# GitHub Settings Runbook (external, manual)

**Project**: Nexus-Hub
**Introduced**: v4.0.0
**Contract**: [`ci-cd-lifecycle-contract.md`](ci-cd-lifecycle-contract.md) section 9

Everything the pipeline files cannot enforce. Configure and verify each item by hand.

Nexus-Hub does not mutate any of this automatically, and the reason is worth stating once rather than repeating per item: the installer holds no credentials, and acquiring any would breach the zero-outbound policy. A tool that silently changed a repository's branch protection would also be a tool that could silently weaken it.

Contains no credentials. Every command below runs with the reader's own authenticated `gh`.

## Why these settings are load-bearing, not hygiene

A `push` event carries no evidence that an update came from a reviewed merge. `post-merge.yml` and the comment on every branch-filtered trigger say "a merge or a release operation happened", and that sentence is TRUE ONLY IF the branch rejects direct pushes.

Without the protection below, the same workflow fires on any developer push to `develop`, and every post-merge assumption (the tree was reviewed, the gate was green, the pull request validated the merge result) is false while the pipeline still reports green. That is the worst available failure: not a red check, but a green one that means nothing.

## 1. Protected branches

Both `main` and `develop`, identically.

| Setting | Value | Why |
|---|---|---|
| Require a pull request before merging | on | this is what makes a `push` to the branch mean "a merge landed" |
| Require status checks to pass | on | see section 2 |
| Require branches to be up to date (`strict`) | on | so the checks ran against a tree that includes the current base |
| Block force pushes | on | a force push to a protected branch rewrites what everyone else already validated |
| Block deletions | on | |
| Do not allow bypassing the above | on, where the team can live with it | routine bypassing erodes the gate for the cases that matter; see the note below |

### On administrator bypass

Nexus-Hub shipped v3.17.5 through six administrator bypasses in one day. Not one was a judgement call: every one was forced by a required check that could never report, because its workflow was path-filtered. The lesson recorded in `docs/decisions/implemented/tooling/2026-08-19-required-checks-must-be-unconditionally-produced.md` is that a bypass used routinely stops being an escape hatch and becomes the merge procedure.

So the setting matters less than the question behind it: if bypass is being used more than about once a release, the gate is wrong, not the person bypassing it.

Verify:

```bash
gh api repos/bendourthe/Nexus-Hub/branches/main/protection
gh api repos/bendourthe/Nexus-Hub/branches/develop/protection
```

## 2. Required status checks

The declared set lives in [`docs/policy/required-checks.json`](../../../../policy/required-checks.json) and is enforced against the workflows by `scripts/check_required_check_coverage.py` in `make validate` and in CI.

Current contexts on both branches:

| Context | Produced by | Why it is required |
|---|---|---|
| `validate` | `ci.yml` | always runs, can never be skipped |
| `shellcheck` | `ci.yml` | always runs, can never be skipped |
| `ci-required` | `ci.yml` | the aggregate over every other job |
| `colocation` | `doc-colocation.yml` | comparison and plan co-location |
| `verify` | `presentify-extractor.yml` | extractor fixture verification |

Three rules, each learned from a shipped defect:

1. **Never require a per-matrix-leg context.** A job-level `if:` is evaluated BEFORE matrix expansion, so a skipped matrix job publishes only its bare job name. `installer-smoke (ubuntu-latest)` and its siblings never come into existence and sit Pending forever.
2. **Never path-filter a workflow that produces a required check.** GitHub leaves the absent context Pending; the identical scoping as a job-level `if:` reports Success.
3. **`validate` and `shellcheck` are deliberately redundant with the aggregate.** Both always run and can never be skipped, so they cost nothing and still gate a pull request if the aggregate itself were ever wrong.

Refresh the manifest from the live state (prints, never writes):

```bash
python scripts/check_required_check_coverage.py --sync
```

## 3. Merge queue

Optional. `ci.yml` declares `merge_group:`, so enabling the queue is a settings change with no workflow edit.

When enabled, the queue validates the QUEUED merge result, which is a stronger signal than a pull request's synthetic merge because it accounts for everything ahead of it in the queue. Point the queue at the same required contexts as section 2.

The REST rulesets and classic branch-protection responses do not prove whether a merge queue is enabled. Confirm the setting in the GitHub UI under Settings, Rules, Rulesets, and record the observation in release evidence.

## 4. Fork pull requests

| Setting | Value | Why |
|---|---|---|
| Require approval for first-time contributors | on | a fork pull request runs workflow code from an untrusted branch |
| Send secrets to workflows from fork pull requests | off | this is the default; do not change it |
| Self-hosted runners | not used | see section 5 |

Nexus-Hub uses no `pull_request_target` anywhere, which is the trigger that would run fork code with the base repository's secrets. `scripts/validate_workflow_security.py` fails on `pull_request_target` combined with a checkout of the pull-request head.

## 5. Runners

Nexus-Hub is a public repository and uses only GitHub-hosted runners. There is nothing to configure, and one rule to keep: **a persistent self-hosted runner must never execute untrusted public-fork code.** `validate_workflow_security.py` fails a `runs-on:` naming a self-hosted runner in a workflow reachable from `pull_request`.

For a PRIVATE repository adopting this contract, self-hosted runners are permitted when hosted-minute cost is material, subject to ephemeral or reset-per-job isolation, no ambient credentials, and no shared mutable state between jobs.

## 6. Billing review

No GitHub endpoint reports drawdown against the included allowance directly, so this is a periodic manual read rather than a monitor. The v3.18.2 decision to withdraw the GitHub Usage Monitor records why: the reconstruction needs repository visibility AT THE TIME OF USE, which no API reports.

```bash
gh api /repos/bendourthe/Nexus-Hub/actions/cache/usage
```

Then read Settings, Billing, and check per-runner-class minutes.

**Derive runner weights from the live per-unit price, never from a remembered multiplier.** The familiar 1x / 2x / 10x figures were the pre-2026 price RATIOS, and GitHub's 2026-01-01 price cut silently made them 1x / 1.67x / 10.33x. Any table written before that date was already wrong.

### What v4.0.0 changed, so you know what to expect

| Event | Before | After |
|---|---|---|
| Integration pull request | Linux only for most jobs | full three-OS coverage |
| Push to `develop` or `main` | the complete suite, WITH the expensive matrix legs | one Linux fast profile plus a provenance report |
| `v*` tag | the complete suite again | the release profile only |
| Ordinary feature-branch push | nothing | nothing |

The expensive legs moved from after the merge to before it. Total spend per change should fall (one comprehensive run instead of two, and no third on the tag), and the spend that remains happens where it can still prevent a bad merge.

The other half of the saving is behavioral and does not appear in any setting: under the v4.0.0 lifecycle a multi-phase plan pushes ONCE, at its final phase, instead of once per phase.

## 7. Artifact retention

Confirm the repository default in Settings, Actions, General, Artifact and log retention. The REST settings queried during the v4.3.0 audit did not expose that value, so this runbook does not infer it from a platform default.

`cursor-usage-monitor.yml` uploads its built VSIX and sets `retention-days: 7` explicitly; a later job downloads the same artifact. Any additional upload must also set an explicit retention. `validate_workflow_security.py` fails an `upload-artifact` step with no `retention-days`, so this cannot be forgotten silently.

## 8. Dated live-settings evidence

The v4.3.0 final-phase audit observed the following read-only state on 2026-08-30. This snapshot is evidence for that audit, not a substitute for rechecking settings after a later change.

| Surface | Observed state | Verification boundary |
|---|---|---|
| Repository | public; default branch `main`; delete branches on merge enabled | repository API |
| Actions policy | Actions enabled; all actions allowed | Actions permissions API |
| Workflow token | default permission `read`; pull-request approval disabled | workflow-permissions API |
| `main` protection | pull requests required; strict status checks; administrator enforcement; force pushes and deletion blocked; conversation resolution required | classic branch-protection API |
| `develop` protection | same controls as `main` | classic branch-protection API |
| Required contexts | `validate`, `shellcheck`, `colocation`, `verify`, `ci-required` on both protected branches | classic branch-protection API |
| Rulesets | no repository rulesets returned | rulesets API; this does not prove merge-queue state |
| Actions caches | 3,726,625,920 bytes across 71 active caches | cache-usage API |
| Artifact default retention | not observed | confirm in Settings, Actions, General |
| Merge queue | not observed | confirm in Settings, Rules, Rulesets |

## 9. Verification checklist

Run through this after any change to branch protection or to the workflow topology.

- [ ] `gh api repos/<owner>/<repo>/branches/main/protection` shows a required pull request, required status checks, `strict: true`, and force pushes blocked
- [ ] The same for `develop`
- [ ] `python scripts/check_required_check_coverage.py` exits 0
- [ ] `python scripts/check_required_check_coverage.py --sync` output matches `docs/policy/required-checks.json`
- [ ] No required context contains a parenthesis (a matrix leg name)
- [ ] Open a docs-only pull request and confirm every required context REPORTS (success or skipped), none stays Pending
- [ ] Merge it and confirm `post-merge.yml` ran and `ci.yml` did NOT
- [ ] Confirm no workflow run was triggered by an ordinary feature-branch push
- [ ] After a release tag, confirm `release.yml` ran and `ci.yml` did NOT
- [ ] Read the billing page and record per-runner-class minutes for the period
- [ ] Confirm the default artifact retention in Settings, Actions, General
- [ ] Confirm merge-queue state in Settings, Rules, Rulesets
- [ ] Every `upload-artifact` step sets an explicit `retention-days`
