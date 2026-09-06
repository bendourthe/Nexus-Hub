# CI/CD Lifecycle Contract (canonical, provider-neutral)

**Project**: Nexus-Hub
**Status**: normative
**Introduced**: v4.0.0
**Owning skill**: `catalog/skills/infrastructure/cicd-architect/SKILL.md`
**Plan**: [`docs/releases/v4/v4.0/plans/v4.0.0-cost-effective-ci-cd.md`](../plans/v4.0.0-cost-effective-ci-cd.md)

This document is the single normative definition of how plan-driven work moves from a local edit to a published release, and of what a repository's continuous integration and delivery pipeline must look like to support that movement cheaply and safely. It is provider-neutral: GitHub Actions is the reference implementation and the primary worked example, not a dependency.

Every statement marked MUST is testable. `tests/skills/test_cicd_lifecycle_contract.py` encodes the non-negotiable ones.

## 1. Why this contract exists

Two independent defaults were costing money and confidence.

The first is per-phase remote execution. When every plan phase ends with an offer to push, a multi-phase plan starts a full remote pipeline once per phase. Seven of those eight runs validate incomplete work, and the eighth validates the same tree the seventh already covered. The cost is real (hosted minutes are billed per run, with Windows at roughly double and macOS at roughly ten times the Linux rate) and the signal is worse than a single terminal run, because a red check on incomplete work teaches the author to ignore red checks.

The second is per-phase pipeline authorship. When every phase is told to "create, update, and optimize CI/CD", each phase invents a slightly different topology. The result is pipeline configuration that duplicates repository commands, drifts from what a developer can run locally, and cannot be reproduced off the CI provider.

This contract replaces both defaults with one lifecycle and one repository-native execution engine.

## 2. Lifecycle state machine

The canonical order is fixed. A conforming harness MUST NOT offer a transition that skips a state.

```text
  local phase work
        |
        v
  local phase gate  (lint, tests, coverage, docs, session history)
        |
        v
  local phase commit                     <-- repeats, once per phase
        |
        |  non-final phase: return to local phase work. NO PUSH.
        |
        v  (final phase only)
  terminal pipeline reconciliation       <-- compare, propose, approve, apply
        |
        v
  complete local gate
        |
        v
  final phase commit
        |
        v
  single branch publication (push)       <-- the plan's FIRST remote event
        |
        v
  integration pull request
        |
        v
  required checks against the MERGE RESULT
        |
        |  red: reopen the final phase, fix locally, amend or add one
        |       narrowly scoped stabilization commit, push again
        |
        v  green
  merge to the protected integration branch
        |
        v
  minimal post-merge work                <-- smoke, publish, provenance only
        |
        v
  /update release                        <-- version, changelog, tag, publish
```

### 2.1 Phase states (MUST)

- Every phase MUST end with a local quality gate and exactly one local commit that is scoped to that phase.
- A non-final phase MUST NOT push, open a pull request, or start remote CI. `Commit`, `Amend`, and `Stop` are the only completion choices offered.
- A non-final phase MUST record its CI impact against this contract without executing remote CI. The record is a statement, not a run.
- A phase MAY change pipeline source files only when the pipeline is that phase's explicit deliverable. Changing them still does not authorize a push.

### 2.2 Terminal states (MUST)

- The final phase MUST run the pipeline reconciliation described in section 7 before publication.
- The final phase MUST complete the full local gate before the final commit.
- The plan MUST publish its branch exactly once under normal conditions, with explicit user approval.
- Remote validation MUST run against the integration merge result (a pull request's synthetic merge), not against the branch tip in isolation.
- A red required check MUST reopen the final phase. The fix is reproduced locally, re-gated locally, and only then amended into the final commit or added as one narrowly scoped stabilization commit.
- `/update release` MUST NOT begin until the integration result is green and merged.

### 2.3 What a push event cannot prove

A version control push event carries no evidence that the update came from a reviewed merge. Merge-only semantics are therefore an EXTERNAL repository-settings contract, not something a pipeline file can assert. A conforming repository MUST protect its integration and release branches so that direct pushes are rejected; only then does a branch-filtered push workflow reliably represent a merge or a release operation. Section 9 lists the settings.

## 3. Repository-native profiles

Definitive validation logic MUST live in the repository, callable without any CI provider present. The pipeline file is a trigger and a reporting surface.

Five profiles are canonical. A repository MAY add none, and MUST NOT rename these.

| Profile | Question it answers | Typical duration | Where it runs |
|---|---|---|---|
| `fast` | Would this change fail the cheapest checks? | seconds to about 2 minutes | developer machine, pre-commit, first CI job |
| `full` | Is this change correct on this host? | minutes | developer machine, integration pull request |
| `platform` | Does this change behave the same on every supported operating system and shell? | minutes per host | integration pull request matrix |
| `report` | What is the human-readable and machine-readable evidence? | seconds | after any profile |
| `release` | Is this tree packageable and publishable? | minutes | release tag or explicit dispatch |

Requirements:

- Each profile MUST be invocable by one documented command with no CI-provider environment variables set.
- A profile MUST reuse the repository's existing validators and test commands rather than reimplementing them.
- Profiles MUST fail fast within a group and MUST aggregate a correct overall exit status across groups.
- Profile output MUST be concise by default and MUST redact credentials.
- `platform` MUST make host differences explicit and testable rather than implicit. For Nexus-Hub that means Linux, macOS, Windows PowerShell 5.1, and PowerShell 7.

## 4. Event separation

| Event | Runs | Never runs |
|---|---|---|
| Ordinary feature-branch push | nothing | any validation workflow |
| Integration pull request into a protected branch | `fast`, then `full`, then `platform`, then `report` | deployment, publication |
| Merge queue entry, where supported | the same gate as the pull request | deployment |
| Protected integration branch update (a merge) | concise smoke, docs publication, provenance | the complete validation suite |
| Protected release branch update or release tag | `release` | the complete validation suite |
| Schedule | drift detection that depends on the outside world | anything reproducible from the tree alone |

The rule behind the table: a suite that already proved the merge result MUST NOT run again on the merge commit. The merge result and the merge commit are the same tree. Rerunning it buys nothing and is billed twice.

Scheduled work is the one exception, because a scheduled run tests the tree against a world that has changed since the merge (new advisories, upstream deprecations, vendor documentation drift).

## 5. Required checks and the stable aggregate

- A repository MUST expose exactly one aggregate required check per validation workflow.
- The aggregate job MUST run unconditionally (`if: always()` or the provider's equivalent) so a failed or skipped dependency cannot leave it unreported.
- The aggregate's verdict MUST be an allowlist over dependency results, so an unfamiliar result value fails closed.
- Cost scoping MUST be expressed as a job-level condition, never as a workflow-level path or branch filter, because an untriggered workflow leaves its required check pending forever while a skipped job reports success.
- A matrix leg's per-leg check name MUST NOT be a required context. A job-level condition is evaluated before matrix expansion, so a skipped matrix job publishes only its bare job name.

## 6. Reporting

Every terminal run MUST produce, from the same local execution that a developer can reproduce:

- `reports/summary.md`: overall status, per-group pass/fail/skip counts, coverage, security findings, platform results, duration, tool versions, artifact paths.
- JUnit XML per test group, for provider-native test rendering.
- Coverage output in the runner's native machine-readable format when the runner supports it.
- A SARIF file or SARIF index for static-analysis and security steps that emit it.
- `reports/metadata/environment.json`: host, operating system, shell, interpreter versions, tool versions, profile, start and end timestamps.

Requirements:

- A failing command MUST still produce a readable summary and valid partial metadata.
- Report content MUST be deterministic given the same inputs, ASCII-safe, and free of credentials.
- The provider MUST publish the summary to its native run summary surface and upload detailed reports unconditionally (`if: always()`), with a short explicit retention period.
- No external reporting service may be required.

## 7. Existing-pipeline reconciliation

The final phase of every plan MUST run this procedure. It is a comparison, not a rewrite.

1. Detect. Identify the active CI provider from the repository (workflow directories, pipeline manifests, service configuration). Record "none detected" rather than assuming one.
2. Compare. Evaluate the existing pipeline against every field in this contract: profiles, events, runner selection, required aggregate, permissions, dependency and action pinning, caching, concurrency, path scoping, artifact retention, reports, deployment boundaries, failure recovery.
3. Propose. Present each difference with its cost, its risk, and the smallest change that closes it.
4. Approve. Obtain explicit approval per change. Silence is not approval.
5. Apply. Make the approved changes in the current phase and re-run the local gate.
6. Record. Write every declined or environment-only difference into the version's known-gaps file with an owner and a next step.

The comparison concludes PASS only when every required field has observable evidence. "Looks fine" is not evidence.

## 8. Runner selection

- A public repository defaults to the provider's standard hosted runners. Persistent self-hosted runners MUST NOT execute untrusted public-fork code.
- A private repository MAY select isolated self-hosted runners when hosted-minute cost is material, subject to ephemeral or reset-per-job isolation, no ambient credentials, and no shared mutable state between jobs.
- Expensive host legs (for Nexus-Hub, macOS at roughly ten times and Windows at roughly twice the Linux rate) MUST be scoped to the events that actually need real-platform proof, and the scoping MUST be a job-level condition.

## 9. External settings contract

These cannot be asserted from a pipeline file and MUST be configured and verified manually:

- Protected integration branch and protected release branch, both rejecting direct pushes.
- Pull request required before merge, with the aggregate check required.
- Administrator bypass disabled where the project's risk tolerance allows.
- Merge queue enabled where the provider supports it, with the same gate.
- Public-fork workflow restrictions, and secret exposure rules for fork pull requests.
- Self-hosted runner isolation for private repositories.
- Artifact retention period.
- Billing usage review per repository and runner class.

These items are documented in [`github-ci-settings-runbook.md`](github-ci-settings-runbook.md). The harness MUST NOT mutate them automatically.

## 10. Security controls

- Every third-party pipeline action or plugin MUST be referenced by an immutable identifier (a full commit SHA for GitHub Actions) with a readable version comment.
- Permissions MUST be least-privilege and explicit at workflow or job scope. The default MUST NOT be inherited silently.
- Caches MUST be keyed to lockfiles or manifests and MUST NOT contain credentials or mutable state.
- Concurrency groups MUST cancel superseded pull-request validation and MUST NOT cancel in-flight release or deployment operations.
- Secrets MUST NOT be exposed to workflows triggered by untrusted forks.

## 11. Failure recovery

| Failure | Response |
|---|---|
| Local phase gate red | Fix in the phase. No commit until green. |
| Terminal local gate red | Fix in the final phase. No push until green. |
| Required check red after publication | Classify, reproduce locally, fix, re-gate locally, amend or add one stabilization commit, push again with approval. |
| Post-merge smoke red | Treat as an incident on the integration branch. Do not start `/update release`. |
| Release step red | Stop. Do not tag or publish. Return to the integration branch. |

At no point does a red remote check authorize a blind re-run. A re-run without a local reproduction is a guess.

## 12. Providers other than GitHub Actions

A conforming implementation on another provider MUST preserve the profile boundary (definitive logic in the repository), the event separation of section 4, a single always-resolving aggregate gate, the reporting schema of section 6, and the external-settings contract of section 9. It MAY differ in trigger syntax, in matrix expression, and in how the aggregate is expressed.

Where a provider cannot express a required property, the gap MUST be recorded as a known gap rather than silently accepted. `catalog/skills/infrastructure/cicd-architect/references/provider-event-models.md` carries the per-provider mapping.

## 13. Non-negotiable statements

These are the assertions the contract test encodes.

1. The five profiles are named `fast`, `full`, `platform`, `report`, and `release`.
2. Non-final plan phases are commit-only and do not push.
3. The final phase owns branch publication and pull-request integration.
4. Terminal pipeline reconciliation is mandatory and is delegated to `cicd-architect`.
5. Release work starts only after the integration result is green.
6. The canonical instruction templates carry the shared lifecycle rule.
7. A validation workflow exposes exactly one always-resolving aggregate required check.
