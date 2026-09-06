---
name: cicd-architect
description: The canonical, provider-neutral CI/CD lifecycle policy - repository-native fast/full/platform/report/release profiles, event separation, runner selection, stable aggregate required checks, structured reports, and existing-pipeline migration. Use whenever the user mentions CI/CD, a build pipeline, GitHub Actions, GitLab CI, Jenkins, a workflow file, required status checks, action minutes, or runner cost, or says any of "optimize CI cost", "our CI is too expensive", "make pipelines run only at the end of a plan", "move CI logic into repository scripts", "why does our CI pipeline run the whole suite twice", "our pipeline duplicates itself", or "our required check is stuck pending". Also the terminal pipeline reconciliation step in a plan's final phase. SKIP - deployment stages (use cd-pipeline-generator), wiring a test suite and its quality gates (use cicd-integration), post-release verification (use shipping-and-launch), and the release commit/tag/publish flow (use /update release).
summary_l0: "Own the canonical CI/CD lifecycle: repository-native profiles, event separation, and pipeline migration"
overview_l1: "The single authoritative CI/CD policy in this catalog. It defines one provider-neutral lifecycle - local phase work and local phase commits, then a single final-phase branch publication, then one comprehensive pull-request gate against the integration merge result, then minimal protected-branch post-merge work, then release - and one execution architecture: definitive validation logic lives in the repository as five named profiles (fast, full, platform, report, release) that a developer can run with no CI provider present, while the pipeline file stays a thin trigger and reporting layer. It also owns runner selection for public and private repositories, the always-resolving aggregate required check, structured reporting (summary, JUnit, coverage, SARIF, environment metadata), least-privilege and immutable-reference security controls, cost controls (caching, concurrency, change scoping), and the six-step existing-pipeline comparison that every plan's final phase runs. GitHub Actions is the primary worked example, not a dependency. Trigger phrases: CI/CD pipeline, optimize CI cost, why does CI run twice, required check stuck pending, migrate our CI, audit our pipeline, action minutes, runner cost."
---

# CI/CD Architect

The canonical CI/CD lifecycle policy for this catalog. Every other CI/CD skill conforms to this one instead of defining its own triggers, profiles, or reporting.

Two ideas carry the whole skill:

1. **Definitive validation logic lives in the repository, not in the pipeline file.** Five named profiles run identically on a developer machine and on a runner. The pipeline is a trigger and a reporting surface.
2. **Remote CI runs once per unit of completed work, against the merge result.** Not once per phase, not again on the merge commit.

## When to Use This Skill

- Setting up CI/CD for a repository that has none.
- Auditing or migrating an existing pipeline, on any provider.
- A pipeline is expensive, slow, or duplicating itself, and it is not obvious why.
- A required status check is stuck Pending and the branch cannot merge.
- Deciding between hosted and self-hosted runners.
- Running the terminal pipeline reconciliation in the final phase of a multi-phase plan. This is the mandatory call site: `[[implementation-plan]]` generates it and `[[implement-phase]]` executes it.

### When NOT to use this skill

- Writing the deployment stages, promotion order, or rollback mechanics: `[[cd-pipeline-generator]]`.
- Wiring a test suite, coverage thresholds, and quality gates into a pipeline: `[[cicd-integration]]`.
- Verifying a production launch after the release shipped: `[[shipping-and-launch]]`.
- Cutting the release itself (version, changelog, tag, publish): `/update release`.

## What This Skill Owns

| Concern | Owned here | Owned elsewhere |
|---|---|---|
| Lifecycle order (phase commit, publication, integration, release) | yes | phase execution: `[[implement-phase]]` |
| The five repository-native profiles | yes | - |
| Trigger and event separation | yes | - |
| Runner selection and cost controls | yes | - |
| Aggregate required check topology | yes | - |
| Structured report schema | yes | test-specific report content: `[[cicd-integration]]` |
| Security controls on the pipeline itself | yes | application security: `[[security-review]]` |
| Existing-pipeline comparison and migration | yes | - |
| Deployment stages, environments, rollback | no | `[[cd-pipeline-generator]]` |
| Test selection, coverage thresholds | no | `[[cicd-integration]]` |
| Branch model resolution | no | `[[git-branching-workflow]]` |

## Instructions

### Step 1: Resolve the lifecycle

Before touching a pipeline file, establish where this work sits in the lifecycle. The canonical order never varies:

```text
local phase work -> local phase gate -> local phase commit   (repeat per phase, NO PUSH)
  -> terminal pipeline reconciliation (final phase only)
  -> complete local gate -> final phase commit
  -> ONE branch publication -> integration pull request
  -> required checks against the MERGE RESULT
  -> merge to the protected integration branch
  -> minimal post-merge work
  -> release
```

Three rules follow, and they are the ones most often broken:

- **A non-final phase never pushes.** It commits locally and stops. Seven pipeline runs on incomplete work cost seven times as much as one run on complete work and produce worse signal, because a red check on known-incomplete work teaches the author to ignore red checks.
- **A pipeline file changes only when the pipeline is the current phase's explicit deliverable.** Otherwise the phase records its CI impact in prose and changes nothing.
- **A push event cannot prove a merge.** Merge-only semantics come from branch protection, which is an external repository setting. A branch-filtered `push` workflow means "merge or release" only in a repository that rejects direct pushes to that branch. Say so explicitly whenever you write one.

### Step 2: Detect the provider

Never assume. Look for, in order:

| Provider | Evidence |
|---|---|
| GitHub Actions | `.github/workflows/*.yml` |
| GitLab CI | `.gitlab-ci.yml` |
| Jenkins | `Jenkinsfile` |
| CircleCI | `.circleci/config.yml` |
| Azure Pipelines | `azure-pipelines.yml` |
| Buildkite | `.buildkite/pipeline.yml` |
| Woodpecker / Drone | `.woodpecker.yml`, `.drone.yml` |
| none | none of the above |

Record "none detected" as a finding rather than defaulting to GitHub Actions. A repository with no pipeline gets the profiles first and a trigger layer second; that order matters, because the profiles are what make the trigger layer thin.

Per-provider event mapping, merge-request semantics, merge queues, and the limits of merge-only enforcement on each: [`references/provider-event-models.md`](references/provider-event-models.md).

### Step 3: Build or verify the five repository-native profiles

Every repository gets exactly these five. Do not rename them and do not add a sixth without recording the decision.

| Profile | Answers | Duration | Runs on |
|---|---|---|---|
| `fast` | Would this fail the cheapest checks? | seconds to ~2 min | developer machine, pre-commit, first CI job |
| `full` | Is this correct on this host? | minutes | developer machine, integration pull request |
| `platform` | Does this behave the same on every supported OS and shell? | minutes per host | integration pull request matrix |
| `report` | What is the evidence? | seconds | after any profile |
| `release` | Is this packageable and publishable? | minutes | release tag or explicit dispatch |

Requirements for each:

- One documented command, no CI-provider environment variables required.
- Reuses the repository's existing validators and test commands. A profile that reimplements a validator has created a second source of truth, which is the defect it exists to prevent.
- Fails fast within a group, aggregates a correct exit status across groups.
- Concise output by default; credentials redacted.
- `platform` makes host differences explicit and testable, never implicit.

Profile inputs and outputs, the report directory schema, retention, pinning, comparison fields, and failure recovery: [`references/repository-native-profiles.md`](references/repository-native-profiles.md).

### Step 4: Separate the events

This is where most pipeline cost hides. Map every trigger to exactly one class.

| Event | Runs | Never runs |
|---|---|---|
| Ordinary feature-branch push | nothing | any validation workflow |
| Integration pull request into a protected branch | `fast`, `full`, `platform`, `report` | deployment, publication |
| Merge queue entry, where supported | the same gate as the pull request | deployment |
| Protected integration branch update (a merge) | concise smoke, docs publication, provenance | the complete validation suite |
| Protected release branch update or release tag | `release` | the complete validation suite |
| Schedule | drift detection that depends on the outside world | anything reproducible from the tree alone |

The rule underneath: **a suite that already proved the merge result must not run again on the merge commit.** A pull request is validated against the synthetic merge, so the merge commit is the same tree. Running it twice buys nothing and is billed twice.

Two consequences people get wrong:

- **A workflow that fires on both `pull_request` into `develop` and `push` to `develop` is running twice.** Under a pull-request-only merge policy those are the same tree. Drop the push trigger and give the merge event its own minimal workflow.
- **Expensive platform proof belongs BEFORE the merge, not after.** Gating a Windows or macOS leg to `push` does not save the minutes; it spends them at the moment they can no longer prevent a bad merge. If a leg is worth running at all, run it on the pull request. If it is not, delete it.

Scheduled work is the one legitimate re-run: it tests the tree against a world that has changed (new advisories, upstream deprecations, vendor documentation drift).

### Step 5: Make the required check stable

A required status check MUST be produced by a job whose workflow triggers unconditionally.

- Filter at the JOB level with a condition. Never at the workflow level with a path or branch filter.
- Expose exactly one aggregate required context per validation workflow.
- The aggregate runs unconditionally so a failed or skipped dependency cannot leave it unreported.
- Its verdict is an allowlist over dependency results, so an unfamiliar result value fails closed.
- Never require a per-matrix-leg context. A job condition is evaluated before matrix expansion, so a skipped matrix job publishes only its bare job name and every per-leg context sits Pending forever.

Both halves of the dependency guard are load-bearing: a "not cancelled" clause overrides the platform's skip-on-failed-dependency rule, and comparing against the literal string treats a missing output as "run".

Full rationale, the vendor quotation, the fail-closed detector, and the aggregate-job pattern: [`references/required-status-checks.md`](references/required-status-checks.md).

### Step 6: Choose runners

| Repository | Default | Allowed alternative | Hard limit |
|---|---|---|---|
| Public | provider-hosted standard runners | none | a persistent self-hosted runner MUST NOT execute untrusted fork code |
| Private | provider-hosted standard runners | isolated self-hosted runners when hosted-minute cost is material | ephemeral or reset-per-job, no ambient credentials, no shared mutable state |

Cost scoping for expensive host classes (commonly around twice the Linux rate for Windows and around ten times for macOS) is a job-level condition, never a workflow filter. Derive those weights from the provider's live per-unit price rather than hardcoding a ratio; published multipliers have turned out to be price ratios that then changed.

### Step 7: Produce structured reports

From the same local execution a developer can reproduce:

- `reports/summary.md`: overall status, per-group pass/fail/skip counts, coverage, security findings, platform results, duration, tool versions, artifact paths.
- JUnit XML per test group.
- Coverage output in the runner's native machine-readable format, where the runner supports it.
- SARIF, or a SARIF index, for static-analysis and security steps that emit it.
- `reports/metadata/environment.json`: host, OS, shell, interpreter and tool versions, profile, start and end timestamps.

And in the pipeline:

- Append the summary to the provider's native run-summary surface on every result.
- Upload detailed reports unconditionally, with a short explicit retention period.
- Never require an external reporting service.

A failing command must still produce a readable summary and valid partial metadata. A run that fails and reports nothing is indistinguishable from a run that never started.

### Step 8: Apply the security and cost controls

| Control | Requirement |
|---|---|
| Third-party actions and plugins | immutable reference (a full commit SHA for GitHub Actions) with a readable version comment |
| Permissions | explicit and least-privilege at workflow or job scope; never inherited silently |
| Caching | keyed to lockfiles or manifests; never contains credentials or mutable state; deliberately absent from jobs that test a cold install |
| Concurrency | cancel superseded pull-request validation; never cancel an in-flight release or deployment |
| Untrusted forks | no secret exposure, no privileged trigger variants, no self-hosted execution |
| Change scoping | a cheap detector job whose classification fails CLOSED, consumed by job-level conditions |

### Step 9: Run the existing-pipeline comparison

This is the terminal duty in every plan's final phase, and the entry point when a user asks to audit or migrate a pipeline. Six steps, in order.

1. **Detect** the provider (Step 2). Record "none detected" rather than assuming.
2. **Compare** the existing pipeline against every field in Steps 3 through 8: profiles, events, runner selection, required aggregate, permissions, pinning, caching, concurrency, path scoping, artifact retention, reports, deployment boundaries, failure recovery.
3. **Propose** each difference with its cost, its risk, and the smallest change that closes it.
4. **Approve.** Obtain explicit approval per change. Silence is not approval.
5. **Apply** approved changes in the current phase, then re-run the local gate.
6. **Record** every declined or environment-only difference as a known gap with an owner and a next step. Cross-link `[[known-gaps-tracker]]`.

The comparison concludes PASS only when every required field has observable evidence. "Looks fine" is not evidence, and neither is a green run: a green run on a pipeline that never checks a thing is green for the wrong reason.

The comparison field list and its output shape: [`references/repository-native-profiles.md`](references/repository-native-profiles.md).

### Step 10: Document what the pipeline cannot enforce

Some of this contract lives in repository settings, not in files. Write it down; never mutate it automatically.

- Protected integration branch and protected release branch, both rejecting direct pushes.
- Pull request required before merge, with the aggregate check required.
- Administrator bypass disabled where the project's risk tolerance allows.
- Merge queue enabled where supported, with the same gate.
- Public-fork workflow restrictions and fork secret exposure rules.
- Self-hosted runner isolation for private repositories.
- Artifact retention period.
- Billing usage review per repository and runner class.

## Common Patterns

### Pattern 1: The thin trigger layer

The pipeline file declares triggers, permissions, concurrency, a change-scope detector, a matrix, and calls to profiles. It contains no validator list. If someone deletes the pipeline file, every check still runs locally; if someone deletes the profiles, the pipeline has nothing to call. That asymmetry is the point.

### Pattern 2: Cost scoping that still reports

Put the scoping in a cheap detector job whose classification fails closed, output a single boolean, and consume it from every gated job's condition. The detector must be unable to exit non-zero, because under a workflow-level filter a detection mistake was loud (Pending forever) and under a job-level condition it is silent (skipped reports Success).

### Pattern 3: Migration from an existing pipeline

Do not rewrite in place. Add the profiles first and prove they reproduce the existing pipeline's result locally. Then replace the pipeline's inline command lists with profile calls one job at a time. Then separate the events. Then delete what is now duplicated. Each step is independently revertible; a wholesale rewrite is not.

### Pattern 4: Reusable pipeline definitions

Where a provider supports callable or included pipeline definitions, use them for the trigger layer only. A reusable definition that carries a validator list has moved the duplication rather than removed it.

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "Path filters save minutes, so filter at the workflow level" | That makes every required check the workflow produces unsatisfiable: the platform leaves it Pending forever on an excluded change, so the only way to merge is an administrator bypass, and routine bypassing erodes the gate for the cases that matter. A job-level condition saves the same minutes and reports Success. Nexus-Hub shipped one release through six administrator bypasses for exactly this. |
| "Running the suite again after merge is a safety net" | The pull request already validated the merge result. The merge commit is that same tree, so the second run cannot discover anything the first did not, and it is billed at full price. If you distrust the pull-request gate, fix the gate. |
| "We gate the expensive OS legs to push, so PRs stay cheap" | The minutes are spent either way. Gating to push spends them after the change is already on a shared branch, where a failure is an incident instead of a review comment. Either the leg is worth running before merge or it should be deleted. |
| "Pushing every phase keeps CI green" | It keeps CI RUNNING. Seven of eight runs validate work the author already knows is incomplete, which is how a team learns to merge past red checks. One run on complete work is both cheaper and a stronger signal. |
| "Duplicating the command list in YAML is clearer than a script" | Two lists drift, and the drift is silent. This repository lost a security validator from CI for weeks because a duplicated key overwrote it, while the local list still ran it. One list, called from both places. |
| "We will add reports later" | Without machine-readable output the only way to read a result is to scroll a log, so nobody reads failures they did not cause. The report is what makes a red run actionable by someone other than its author. |
| "Self-hosted runners are cheaper, so use them everywhere" | On a public repository a persistent self-hosted runner executes untrusted fork code on a machine with state. That is a remote code execution surface, not a cost optimization. Private repositories, ephemeral runners, no ambient credentials. |
| "Floating action tags get security fixes automatically" | They also get supply-chain compromises automatically. A moved tag is an unreviewed code change with your credentials. Pin the SHA and update deliberately. |
| "The pipeline is green, so it conforms" | Green proves the checks that ran passed. It says nothing about the checks that were skipped, never written, or silently dropped. Step 9 requires observable evidence per field, which is a different question. |

## Verification

- [ ] The active CI provider is named, or "none detected" is recorded
- [ ] All five profiles exist and each runs to completion from one documented command with no CI-provider environment variables set
- [ ] No profile reimplements a validator the repository already owns: each profile step maps to an existing repository command
- [ ] No validation workflow fires on both a pull request into a protected branch and a push to that same branch
- [ ] Every expensive-host leg runs on the integration pull request, not only after merge
- [ ] Exactly one aggregate required context exists per validation workflow; it runs unconditionally and its verdict is an allowlist
- [ ] No per-matrix-leg name appears in the required-check list
- [ ] Open a pull request touching only paths the change detector excludes and confirm every required context reports rather than staying Pending
- [ ] Every third-party action or plugin reference is an immutable identifier with a version comment
- [ ] Every workflow declares explicit least-privilege permissions
- [ ] A deliberately failed profile run still produces `reports/summary.md` and valid `reports/metadata/environment.json`
- [ ] The run summary and uploaded artifacts appear on a failing run, with an explicit retention period set
- [ ] Step 9 was run and every field concluded with observable evidence, or the difference is recorded as a known gap with an owner and a next step
- [ ] The external repository settings of Step 10 are documented in a runbook, and nothing mutated them automatically

## Related Skills

- [[cd-pipeline-generator]] -- generates the deployment stages that consume this lifecycle's validated release artifact
- [[cicd-integration]] -- wires test suites, coverage, and quality gates into these profiles
- [[implementation-plan]] -- generates the phase lifecycle and the mandatory terminal reconciliation that calls Step 9
- [[implement-phase]] -- executes local phase commits, the single publication, and the integration gate
- [[git-branching-workflow]] -- resolves the branch model this lifecycle publishes into
- [[known-gaps-tracker]] -- records declined pipeline differences and environment-only limitations from Step 9
- [[kubernetes-expert]] -- Kubernetes deployment targets
- [[terraform-specialist]] -- infrastructure provisioning in pipelines
- [[security-review]] -- application security assessment, distinct from pipeline security
- [[test-structure]] -- test automation strategy behind the profiles
