# Mandatory Final Phase Template

The verbatim block `[[implementation-plan]]` emits as the last `## Phase N` of every generated plan, plus the rules that govern it. Kept here rather than in the skill body because it is a template a reader copies once at generation time, not guidance the agent needs loaded on every trigger.

The one-line rule the body states, and this file expands: every plan ends with a fail-closed last phase, and it is the ONLY phase permitted to push, open a pull request, or start remote CI.

#### Mandatory Final Phase (every plan)

Every generated plan MUST end with a fail-closed last phase dedicated to architecture refactor, known-gaps reconciliation, living-docs architecture, git-tree hygiene, terminal CI/CD reconciliation, the Tier 3 deep pass via `[[functional-verification]]`, independent Goal-vs-codebase review, last-phase-only human testing, full-suite local stabilization, and the plan's single publication and integration. This is also the ONLY phase permitted to push, open a pull request, or start remote CI. The heading is never enough: each duty writes a named section in `<version_dir>/development/last-phase-evidence.md`. An empty finding is allowed only when the scan output is quoted. A duty is omitted only by recording a known-gap (`QG` or `DF`) with Source phase, Plan reference, Reason, and Suggested next step. Automated tests still end every earlier phase; human/manual testing suggestions are forbidden until this last phase. Emit the block verbatim as the last `## Phase N`:

```markdown
## Phase N: Architecture Refactor, Known-Gaps Reconciliation, and CI/CD

**Goal**: Leave the project well-organized, its known gaps reconciled, its living docs architecture current, its complete artifact set exercised through the Tier 3 deep pass, and its pipeline reconciled against the canonical contract, with independent evidence that the plan Goal landed, then publish and integrate the completed branch.
**Prerequisites**: All prior phases.
**Stability Gate**: `<version_dir>/development/last-phase-evidence.md` exists with one quoted section per duty below, including `## Tier 3 deep pass`. A missing Goal, a Goal-review miss without a recorded known-gap, or a missing evidence section blocks `/update release`.
**Verification Expectation**: Run `[[functional-verification]]`'s Tier 3 procedure from `references/deep-pass.md` against every artifact produced by the plan and observe either a clean terminal result or a bounded result whose remaining findings are recorded as owned known gaps; quote that result under `## Tier 3 deep pass`.
**Recommended model tier**: frontier
**Recommended effort level**: max
**Rationale**: Repo-wide refactor, Tier 3 artifact exercise, Goal-vs-codebase review, known-gap reconciliation, and release gating carry high context volume and blast radius.

### Sub-tasks

#### N.1 - Architecture refactor
**Objective**: Refactor toward a well-organized, intuitive layout and quote the scan.
**Prompt**:
> Identify deprecated/obsolete files, empty directories, redundant files/dirs, and overcomplicated structure, then refactor toward a clean, intuitive layout via [[project-refactor]] and [[docs-layout-refactor]] (propose-then-apply, with confirmation; repair every reference for anything that moves). Write the detector output into `<version_dir>/development/last-phase-evidence.md` under `## Architecture refactor`. An empty finding is allowed only when the scan output is quoted.

#### N.2 - Known-gaps reconciliation
**Objective**: Reconcile this version and every other still-open known-gaps file.
**Prompt**:
> Via [[known-gaps-tracker]], reconcile this version's known gaps AND every other `docs/**/known-gaps.md` whose Status is in-progress or whose Open Items remain. Glob both canonical (`docs/releases/v<MAJOR>/v<MAJOR>.<MINOR>/known-gaps.md`) and legacy layouts. If a file is unreachable, record the glob result and continue with what was found. Write the disposition into the evidence file under `## Known-gaps reconciliation`.

#### N.3 - Living docs architecture
**Objective**: Prove handbooks, decisions, and generated HTML match the required living tree.
**Prompt**:
> Check `docs/handbooks/` (markdown source of truth, generated `html/`, one atlas walkthrough, technical companions for key components), `docs/decisions/`, and living `docs/README.md` / `docs/DEVLOG.md` / `docs/todos.md`. Self-gated: never invent `docs/testing/` or `docs/validation/`. Markdown wins if HTML disagrees; regenerate or fail the check. Quote the check in the evidence file under `## Living docs architecture`. Details live in [[docs-layout-refactor]].

#### N.4 - Git-tree hygiene
**Objective**: Report branch and repository-settings hygiene without deleting anything.
**Prompt**:
> Run `python scripts/check_release_preconditions.py --branches --repo-settings`. Quote the output in the evidence file under `## Git-tree hygiene`. Report only; never delete branches.

#### N.5 - Terminal CI/CD reconciliation
**Objective**: The repository's pipeline is compared field by field against the canonical contract, and every difference is either applied with approval or recorded as a known gap.
**Prompt**:
> Invoke [[cicd-architect]] in existing-pipeline comparison mode and run its six steps in order: DETECT the active CI provider (recording "none detected" rather than assuming one); COMPARE the existing pipeline against every field of the canonical contract - repository-native profiles, event separation, runner selection, the always-resolving aggregate required check, permissions, immutable action or plugin references, caching, concurrency, path scoping, artifact retention, structured reports, deployment boundaries, and failure recovery; PROPOSE each difference with its cost, its risk, and the smallest change that closes it; obtain explicit APPROVAL per change (silence is not approval); APPLY the approved changes and re-run the local gate; and RECORD every declined or environment-only difference as a known gap with an owner and a next step via [[known-gaps-tracker]]. The comparison concludes PASS only when every required field has observable evidence; a green pipeline run is not evidence, because a pipeline that checks nothing is green for the wrong reason. If this repository ships more than one installer, run or add a declarative cross-installer parity gate covering distributed artifacts, supported platforms, named capability counterparts, and external-tool fallbacks, then execute the real installers on their target operating systems with identical postconditions. Cross-link [[platform-contract-verification]] so discovery and delivery are checked in the same pass. If the repository ships zero or one installer, record a silent no-op and continue. Quote the per-field comparison result in the evidence file under `## CI/CD coverage`.

#### N.6 - Tier 3 deep pass
**Objective**: Exercise every artifact the complete plan produced and record the bounded terminal result.
**Prompt**:
> Invoke [[functional-verification]] and follow its Tier 3 runbook at `references/deep-pass.md` against every artifact this plan produced. Do not copy or improvise that procedure here: use its blast-radius decision, delegated owners, plan audits, and global iteration budget exactly as written. Quote the terminal result in `<version_dir>/development/last-phase-evidence.md` under `## Tier 3 deep pass`. A clean result states what ran and what was observed; any finding left when the budget ends is recorded through [[known-gaps-tracker]] with an owner and a next step.

#### N.7 - Independent Goal-vs-codebase review
**Objective**: Prove the plan Goal landed in the codebase, not that checkboxes were ticked.
**Prompt**:
> Re-read the plan header Goal and the Goals First / Definition of Done. Inspect the codebase as if this agent had not implemented the phases. Write `## Goal-vs-codebase review` in `<version_dir>/development/last-phase-evidence.md` listing: the plan Goal restated; the code/docs artifacts that satisfy it; and any gap. A missing or malformed Goal is a fail-closed finding that names the missing Goal. Completing every prior-phase sub-task is not evidence the Goal landed. A miss is a blocking finding or a new known-gap, not a pass.

#### N.8 - Human/manual testing suggestions (last phase only)
**Objective**: Ask a human to exercise only what automated tests cannot cover, now that the feature is complete.
**Prompt**:
> Emit human/manual testing suggestions for user-facing workflows, external integrations, and environment-specific cases that automated tests cannot cover. Do not invent a fake walkthrough. This duty exists only on the last phase.

#### N.9 - Testing and Stabilization
**Objective**: Prove the refactor preserved behavior and the complete LOCAL gate is green before anything is published.
**Prompt**:
> Run the full local validation/test suite, confirm the refactor changed no behavior, and iterate until clean. This gate is local by construction: it must pass before the branch is published, so it cannot depend on a remote run. Quote the suite in the evidence file under `## Full-suite testing and stabilization`. Generate a session-history entry for this phase.

#### N.10 - Publication and integration
**Objective**: Publish the completed branch once, validate the merge result remotely, and hand a green integration to the release flow.
**Prompt**:
> Create the final local commit for this phase. Then present the resolved branching model, remote, branch name, and pull-request target, and obtain EXPLICIT approval before the plan's first branch push. Push once, open the integration pull request against the integration branch, and report the exact required checks expected. Wait until every required check reaches a terminal state. A red check REOPENS this phase: classify the failure, reproduce it locally, apply the narrow fix, re-run the local gate, update known gaps and session history, then amend the final commit or add one narrowly scoped stabilization commit and push again with approval. Never re-run a red check without a local reproduction; a re-run without one is a guess. Merge only after every required check is green and the user approves. Confirm the post-merge workflow performed only its intended smoke, publication, or provenance work and did not rerun the complete suite. Only then hand off to `/update release`, which owns the version bump, changelog, tag, push, and GitHub Release behind its own confirmation gates. Quote the required-check results in the evidence file under `## Publication and integration`.
```
