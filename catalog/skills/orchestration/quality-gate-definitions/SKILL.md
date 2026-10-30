---
name: quality-gate-definitions
description: Reusable GO/NO-GO quality gate definitions for multi-phase workflows. Provides predefined gate types, criteria templates, and behavior configuration for planning, implementation, testing, security, and deployment checkpoints.
summary_l0: "Define reusable GO/NO-GO quality gates for multi-phase workflow checkpoints"
overview_l1: "This skill provides reusable GO/NO-GO quality gate definitions for multi-phase workflows, including predefined gate types, criteria templates, and behavior configuration. Use it when establishing checkpoints between planning, implementation, testing, security, and deployment phases, enforcing quality standards before phase transitions, or designing automated quality enforcement. Key capabilities include predefined gate type selection (planning, implementation, testing, security, deployment), criteria template customization, pass/fail threshold configuration, automated gate evaluation, manual override policies, gate failure remediation guidance, and integration with workflow orchestration. The expected output is configured quality gate definitions with criteria, thresholds, and enforcement behavior for each workflow phase. Trigger phrases: quality gate, GO/NO-GO, checkpoint, gate criteria, phase gate, deployment gate, quality checkpoint, workflow gate."
---

# Quality Gate Definitions

A library of reusable quality gate definitions that can be plugged into any multi-phase workflow. Each gate defines required and optional criteria, automatic and manual checks, and configurable behavior for every outcome, with templates for tracking results. Use these gates as building blocks rather than reinventing checkpoint criteria for every workflow.

## When to Use This Skill

Use this skill for:

- Setting up quality checkpoints in multi-phase development workflows
- Defining GO/NO-GO criteria before implementation, testing, or deployment
- Standardizing quality expectations, or configuring automated checks, at phase transitions

**Trigger phrases**: "quality gate", "GO/NO-GO criteria", "gate check", "phase transition criteria", "checkpoint definition", "approval criteria", "gate library", "pass/fail criteria"

## Instructions

### Step 1: Select Gate Type

Choose the appropriate gate type based on where the checkpoint falls in your workflow.

**Gate Type Reference**:

| Gate Type | Placed Between | Primary Purpose |
|-----------|---------------|-----------------|
| Planning Gate | Research and Implementation | Ensure the plan is sound before writing code |
| Implementation Gate | Implementation phases | Verify each phase is complete before starting the next |
| Testing Gate | Implementation and Review | Confirm adequate test coverage and all tests pass |
| Security Gate | Testing and Deployment | Verify no vulnerabilities are introduced |
| Deployment Gate | Staging and Production | Final confirmation before production release |

**Decision Guide**: If your workflow has N phases, you need at most N-1 gates (one between each pair of phases). Start with the highest-risk transition and add gates incrementally. Not every transition needs a formal gate; use judgment.

### Step 2: Define Gate Criteria

For each gate, specify four categories of criteria.

**Criteria Categories**:

| Category | Description | Example |
|----------|-------------|---------|
| **Required** | Must pass for GO. No exceptions. | "All unit tests pass" |
| **Optional** | Should pass. NO-GO only if multiple fail. | "Code coverage above 90%" |
| **Automatic** | Verified by a tool or command. No human needed. | `npm test` exit code 0 |
| **Manual** | Requires human judgment or review. | "Architecture approach is appropriate" |

**Criteria Definition Template**:

```markdown
## Gate: {Gate Name}

### Required Criteria (all must pass)
| # | Criterion | Check Type | How to Verify |
|---|-----------|-----------|---------------|
| R1 | [criterion] | Auto/Manual | [command or process] |
| R2 | [criterion] | Auto/Manual | [command or process] |

### Optional Criteria (aim for all, tolerate 1-2 failures)
| # | Criterion | Check Type | How to Verify |
|---|-----------|-----------|---------------|
| O1 | [criterion] | Auto/Manual | [command or process] |
| O2 | [criterion] | Auto/Manual | [command or process] |
```

**Safety-critical guards gate on `pass^k`.** For any criterion that guards a safety-critical behavior (a hook that must block a destructive command, a redaction that must fire, an allowlist that must reject), the gate reports GO only on a `pass^k` result over the k recorded trials, per the definition owned by `[[ai-output-evaluation]]`; a single green run is a `pass@1` sample, not evidence the guard holds. Nexus-Hub's own hook guards are exactly this class. Record the k trial results with the gate outcome; do not restate the metric definitions here.

### Step 3: Configure Gate Behavior

Define what happens when a gate passes, fails, or partially passes.

**Behavior Options**:

| Outcome | Action | Description |
|---------|--------|-------------|
| **PASS** | Proceed | All required criteria met. Move to next phase. |
| **FAIL (fixable)** | Retry | One or more required criteria failed but can be fixed. Return to current phase, fix, and re-run gate. |
| **FAIL (blocking)** | Stop | A required criterion failed and cannot be fixed within current scope. Escalate to human decision-maker. |
| **UNGATED** | Stop and explain | The gate could not judge the work, so it has no verdict. Never proceeds as PASS. Follow "After UNGATED or exhausted FAIL". |
| **PARTIAL** | Conditional proceed | All required criteria met but one or more optional criteria failed or were not measured. Proceed with documented exceptions. |

**Precedence.** The gate takes the highest outcome among its criteria: FAIL (blocking) > FAIL (fixable) > UNGATED > PARTIAL > PASS. List every criterion behind the outcome, not only the one that decided it.

**UNGATED.** A gate is UNGATED when any of these holds for a required criterion: the gate has no required criteria; an automatic criterion has no measured value or a zero denominator; a manual criterion has no recorded judgment (an approver and a date); a `pass^k` criterion has fewer than k recorded trials; or its check could not run. An unmeasured optional criterion yields PARTIAL, not UNGATED. UNGATED never proceeds as PASS, because a gate that measured nothing says nothing.

**Reason categories.** Record why as one fixed category, never as raw error text (it can carry paths, hostnames, or tokens): `no-criteria`, `not-measured`, `zero-denominator`, `no-judgment`, `too-few-trials`, `tool-missing`, or `timeout`. A tool permanently unavailable within the current scope is FAIL (blocking), not UNGATED, only when the gate definition says the tool must exist.

**Regression.** If an earlier run of the same gate measured a required criterion and this run did not, report that beside the outcome as a regression.

**Worked example: a manual criterion.** The `plan-approved` gate has four required manual criteria, each needing a recorded judgment. All four carrying an approver and a date (for example, "R1: A. Rivera, 2026-10-14") gives PASS. R4 left blank gives UNGATED (`no-judgment`). R4 recorded as rejected gives FAIL (fixable).

**Behavior Configuration Template**:

```markdown
### Gate Behavior: {Gate Name}

**On PASS**:
- Log gate result to {artifact file}
- Announce "Gate {name} PASSED" with summary
- Proceed to Phase {N+1}

**On FAIL (fixable)**:
- Log failure details to {artifact file}
- Return to Phase {N} with specific feedback:
  - Which criteria failed
  - What needs to change
- Re-run gate after fixes (max {N} retries)
- When the retries are used up, follow "After UNGATED or exhausted FAIL"

**On FAIL (blocking)**:
- Log failure details to {artifact file}
- Stop workflow
- Escalate to {human / team lead / architect}
- Do not proceed until blocker is resolved

**On PARTIAL**:
- Log which optional criteria failed or were not measured
- Document accepted risk in {artifact file}
- Proceed with acknowledgment

**On UNGATED**:
- Log the outcome, the reason category for each criterion behind it, and any regression to {artifact file}
- Do not announce a pass and do not proceed to Phase {N+1}
- Follow "After UNGATED or exhausted FAIL"
```

### After UNGATED or exhausted FAIL

An UNGATED outcome, or a FAIL whose retries are used up, stops the workflow and goes through this one flow. The agent never loops silently and never gives up silently.

**Interactive run.** Show the user a message of at most five lines, in plain words with no jargon:

```text
Gate {name} could not be judged.
What: {the criterion that could not be judged}
Why: {the reason in plain words, not raw error text}
To fix: {what would make it judgeable}
Choose: "try again" or "record as a known gap"
```

- **Retries.** "Try again" allows at most two further attempts. After two further failed attempts, the agent records the known gap itself through `[[known-gaps-tracker]]` as a `QG` item, with why it failed and what would resolve it.
- **Who accepts.** Only the user accepts a known gap interactively, and the gap names who accepted it. A gap recorded at the retry limit names that reason instead.

**Unattended run.** With no user to ask, record the known gap immediately, with the same explanation, naming "unattended run" as the reason.

**Missing evidence.** Report a gate input that could not be produced under `[[verification-before-completion]]`, never as approval. `/implement`'s troubleshooting loop hands off to this section instead of defining a retry flow of its own.

### Step 4: Implement Gate Checks

Use the predefined gate library below. Copy the relevant gate template into your workflow and customize the thresholds.

**Gate Library**:

#### Gate: code-compiles

```markdown
## Gate: code-compiles
**Type**: Implementation Gate
**Automation**: Fully automatic

### Required Criteria
| # | Criterion | Command |
|---|-----------|---------|
| R1 | Source compiles without errors | `npm run build` / `cargo build` / `go build ./...` |
| R2 | No type errors | `npx tsc --noEmit` / `mypy .` / `cargo check` |

### On Fail
Return to implementation phase. Compile errors must be fixed before proceeding.
```

#### Gate: lint-passes

```markdown
## Gate: lint-passes
**Type**: Implementation Gate
**Automation**: Fully automatic

### Required Criteria
| # | Criterion | Command |
|---|-----------|---------|
| R1 | Linter reports zero errors | `npm run lint` / `ruff check .` / `cargo clippy` |

### Optional Criteria
| # | Criterion | Command |
|---|-----------|---------|
| O1 | Linter reports zero warnings | Same command, check warning count |

### On Fail
Auto-fix where possible (`--fix` flag). Manual fix for remaining issues.
```

#### Gate: tests-pass

```markdown
## Gate: tests-pass
**Type**: Testing Gate
**Automation**: Fully automatic

### Required Criteria
| # | Criterion | Command |
|---|-----------|---------|
| R1 | All existing tests pass | `npm test` / `pytest` / `cargo test` |
| R2 | All new tests pass | Same command (new tests included in suite) |
| R3 | No test regressions | Compare test count: current >= previous |

### Optional Criteria
| # | Criterion | Command |
|---|-----------|---------|
| O1 | No flaky tests detected | Run test suite twice, compare results |

### On Fail
Fix failing tests or the code that caused them. Do not skip or disable tests to pass the gate.
```

#### Gate: coverage-threshold

```markdown
## Gate: coverage-threshold
**Type**: Testing Gate
**Automation**: Fully automatic

### Required Criteria
| # | Criterion | Command |
|---|-----------|---------|
| R1 | Overall coverage >= {threshold}% | `pytest --cov` / `npx jest --coverage` |
| R2 | New code coverage >= 80% | Coverage diff report |

### Optional Criteria
| # | Criterion | Command |
|---|-----------|---------|
| O1 | No files below 50% coverage | Coverage per-file report |
| O2 | Branch coverage >= {threshold}% | Coverage report with branch analysis |

### On Fail
Add tests for uncovered code paths. Focus on new code first, then existing gaps.
```

#### Gate: no-security-vulns

```markdown
## Gate: no-security-vulns
**Type**: Security Gate
**Automation**: Mostly automatic

### Required Criteria
| # | Criterion | Command |
|---|-----------|---------|
| R1 | No critical/high dependency vulnerabilities | `npm audit` / `pip audit` / `cargo audit` |
| R2 | No hardcoded secrets in diff | Secret scanning tool or manual grep |
| R3 | No new SQL injection vectors | Manual review of database queries |

### Optional Criteria
| # | Criterion | Command |
|---|-----------|---------|
| O1 | No medium dependency vulnerabilities | Same audit command |
| O2 | Security-sensitive changes reviewed by second person | Manual |

### On Fail
Critical and high vulnerabilities are blocking. Update dependencies or refactor code. Medium vulnerabilities are tracked but not blocking.
```

#### Gate: rendered-artifact-verified

```markdown
## Gate: rendered-artifact-verified
**Type**: Implementation Gate
**Automation**: Fully automatic, except the final criterion

### Required Criteria
| # | Criterion | Check |
|---|-----------|-------|
| R1 | Renders with zero page errors | `measure_handbook.py` reports no pageerror entries |
| R2 | Geometric audit returns zero findings | `geometric_audit.py <file>` exits 0 |
| R3 | Nothing overflows its designed container | `slide-overflow` and `clipped-text` silent |
| R4 | Every figure and table reference resolves | `clone-reference-escapes-slide` silent |
| R5 | Line endings unchanged from baseline | each changed file against its committed blob |
| R6 | The unmeasurable decisions are recorded | `check_attestation.py <record>` exits 0 |
| R7 | The edited region was captured and inspected | a capture clipped to the region, under 1500px longest edge |

### On Fail
Return to the generation step. A rendered artifact that has not been rendered
and looked at is not verified, whatever its source says.
```

R5 exists because a whitespace pass once silently rewrote eight files of a
byte-frozen qualification corpus, invalidating the manifest that made the
benchmark meaningful. R7 is the only criterion a machine cannot fully settle,
and it is the one the source project's failures traced to most often.

Owners: `[[document-to-interactive-html]]` for R1 to R4 and R6,
`catalog/rules/html/visual-self-verification.md` for R7.

#### Gate: docs-complete

```markdown
## Gate: docs-complete
**Type**: Deployment Gate
**Automation**: Partially automatic

### Required Criteria
| # | Criterion | Check |
|---|-----------|-------|
| R1 | Public API changes have updated docs | Manual review of changed exports |
| R2 | Breaking changes documented in changelog | `grep "BREAKING" CHANGELOG.md` |

### Optional Criteria
| # | Criterion | Check |
|---|-----------|-------|
| O1 | Inline code comments for complex logic | Manual review |
| O2 | README updated if user-facing behavior changed | Manual review |

### On Fail
Add missing documentation before deployment. Prioritize public API docs and breaking change notes.
```

#### Gate: plan-approved

```markdown
## Gate: plan-approved
**Type**: Planning Gate
**Automation**: Manual (human judgment)

### Required Criteria
| # | Criterion | Check |
|---|-----------|-------|
| R1 | Plan addresses all acceptance criteria | Compare plan to request |
| R2 | Implementation phases are ordered and non-overlapping | Review phase list |
| R3 | Testing strategy covers every acceptance criterion | Cross-reference |
| R4 | Risk mitigations are specific and actionable | Review risk table |

### Optional Criteria
| # | Criterion | Check |
|---|-----------|-------|
| O1 | Effort estimate provided for each phase | Review estimates |
| O2 | Rollback strategy documented | Review plan |

### On Fail
Return to planning phase with specific feedback on what needs revision.
```

#### Gate: performance-budget

```markdown
## Gate: performance-budget
**Type**: Deployment Gate
**Automation**: Fully automatic

### Required Criteria
| # | Criterion | Command |
|---|-----------|---------|
| R1 | Response time p95 <= {threshold}ms | Load test or benchmark |
| R2 | Memory usage <= {threshold}MB | Profiler output |
| R3 | Bundle size increase <= {threshold}KB | `du -b dist/` or bundler stats |

### Optional Criteria
| # | Criterion | Command |
|---|-----------|---------|
| O1 | No performance regression vs. baseline | Benchmark comparison |
| O2 | Startup time <= {threshold}ms | Profiler output |

### On Fail
Profile and optimize. If the budget cannot be met, escalate for budget revision with justification.
```

#### Gate: merge-ready

```markdown
## Gate: merge-ready
**Type**: Deployment Gate (final gate before merge)
**Automation**: Mostly automatic (the collaborator-rule criteria are policy/manual)

### Required Criteria
| # | Criterion | How to Verify |
|---|-----------|---------------|
| R1 | CI is green on the current head | `gh pr checks` / the status-check rollup for the head commit |
| R2 | Cross-model / multi-agent review is clean, or every finding is addressed | reviewDecision APPROVED + zero unresolved threads (see multi-agent-code-review, cross-model-orchestrator) |
| R3 | The PR is one concern wide | Diff scope matches a single stated intent (no drive-by changes) |
| R4 | An issue is linked, or partiality is stated | `Fixes #N` / `Closes #N` in the body, or an explicit "partial: ..." note |
| R5 | Evidence discipline satisfied | Every gate above verified against LIVE current-head GitHub state, not local history (see verification-before-completion) |
| R6 | Project review trapdoors checked | The project's recurring-blocker list was applied (see review-trapdoors) |

### Optional Criteria (configurable collaborator rules; see the merge-readiness-contract style guide)
| # | Criterion | How to Verify |
|---|-----------|---------------|
| O1 | No self-merge (a second person approves) | Reviewer is not the author, unless the bus-factor escape hatch applies |
| O2 | Diff within the net-lines / one-concern ceiling | Diff stat under the project's configured cap |

### On Fail
Any required criterion failing blocks the merge. Fix the cause (green CI, address findings, split the PR, link the issue) and re-run. The collaborator rules are policy, not code: configure them per the style guide.
```

### Step 5: Track Gate Results

Record every gate run so a reader can recompute its verdict from the record and git alone. Every rerun is a new record and never overwrites an earlier one. Each record stores:

- The gate name, the definition's repository path and the commit SHA the run ran against, and the sha256 of the definition's canonical form.
- Per criterion: the measured value (a number or a boolean, nothing else), the threshold, the comparison, the producing command with the sha256 of its output, and the outcome.
- Any other input as a hash per `[[egress-redaction]]`, never raw and never as a length.

**Canonical form** (defined only here). The definition block runs from its `## Gate:` heading to the next heading of equal or higher level, or to the end of the enclosing code fence or file. Use LF line endings, strip trailing whitespace from every line, drop trailing blank lines, end with one LF, encode as UTF-8 without BOM, and hash with sha256. The digest detects drift; fetch the old definition from git by path and SHA, never from the working tree.

**Recompute.** Compare each measured value with its threshold using the stated comparison (`<=`, `>=`, `<`, `>`, `==`, `!=`). A missing measured value or threshold is `not measured` and is never inferred. Then apply the Step 3 precedence. Whether a FAIL is fixable or blocking is a recorded judgment, not recomputed.

**Limits.** The record proves internal consistency, not that the measured values were honest, which is why each value cites its producing command and an output hash. A definition SHA that git can no longer reach is reported as "definition unavailable", never replaced with the current definition. Flag a run whose definition changed in the same change set (`changed-in-run: yes`). When one gate and commit have two records, keep both in order; the later stands only if it states why (`stands-because`). Tool-call decision records belong to `ai-agent-development/references/decision-policy-harness.md`.

**Gate Result Reporting Template**:

```markdown
# Gate Results: {Workflow Name}

## Summary
| Gate | Result | Date | Attempts |
|------|--------|------|----------|
| lint-passes | PARTIAL | [date] | 2 |
| coverage-threshold | UNGATED (not-measured) | [date] | 1 |

## Exceptions Log
| Gate | Criterion | Accepted Risk | Approved By |
|------|-----------|---------------|-------------|
| lint-passes | O1 (zero warnings) | 2 cosmetic warnings | [name] |
```

**Worked examples** (the sha256 on the second line is the published digest of that gate's block above; the commit SHA and output hashes are illustrative):

```gate-record
gate: lint-passes | run: 1 | date: 2026-10-14T10:02:00Z
definition: catalog/skills/orchestration/quality-gate-definitions/SKILL.md@0123456789abcdef0123456789abcdef01234567 | sha256: d5cb9b64a68fc5b83e4397d770aaa37f6a893110823b87b70a196a81f0f0ec62 | changed-in-run: no
R1 | required | 3 | <= | 0 | ruff check . | sha256:e464090ceb8960eb0e45db18e47ee013a509bc25e24da1a77328521e63b09250 | not met
outcome: FAIL (fixable)
```

```gate-record
gate: lint-passes | run: 2 | date: 2026-10-14T10:20:00Z
definition: catalog/skills/orchestration/quality-gate-definitions/SKILL.md@0123456789abcdef0123456789abcdef01234567 | sha256: d5cb9b64a68fc5b83e4397d770aaa37f6a893110823b87b70a196a81f0f0ec62 | changed-in-run: no
R1 | required | 0 | <= | 0 | ruff check . | sha256:943b39331457bfaab35f842e1bbd41582f29bd19feeff0f951a514606fcfb88a | met
O1 | optional | 2 | <= | 0 | ruff check . | sha256:943b39331457bfaab35f842e1bbd41582f29bd19feeff0f951a514606fcfb88a | not met
stands-because: errors fixed; 2 cosmetic warnings accepted
outcome: PARTIAL
```

```gate-record
gate: coverage-threshold | run: 1 | date: 2026-10-14T10:40:00Z
definition: catalog/skills/orchestration/quality-gate-definitions/SKILL.md@0123456789abcdef0123456789abcdef01234567 | sha256: 6939c92715671a57f191b48055268d348acb9f013f1a633e9f5b852c9c53f8ad | changed-in-run: no
R1 | required | - | >= | 80 | pytest --cov | sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855 | not measured
R2 | required | 91 | >= | 80 | coverage diff | sha256:632ab7c6afadacdbb30c307a97e4220f3c3a1a161c293584dd2e815064633daa | met
outcome: UNGATED (not-measured: R1)
```

## Merge-Readiness Contract

The `merge-ready` gate above is a COMPOSITE, machine-checkable contract: a change is mergeable only when its required criteria all hold, so "ready to merge" becomes a checklist backed by evidence. It composes disciplines already in the catalog. The CI and review gates (tests-pass, lint-passes, coverage-threshold, no-security-vulns above) supply R1-R2. The evidence discipline in [[verification-before-completion]] supplies R5: each gate is verified against the PR's live current-head state (the status rollup, the latest review submissions, `mergeable`), never a stale top-level comment or a remembered green check. The project's review trapdoors ([[review-trapdoors]]) supply R6: the curated recurring-blocker list is applied before the change is called mergeable. The collaborator rules (O1/O2) are deliberately CONFIGURABLE convention, not mandate: a solo maintainer cannot honor a no-self-merge rule, and a hotfix may need a time-boxed self-merge escape hatch. The options (no-self-merge by default, a net-lines / one-concern ceiling, a bus-factor self-merge escape hatch) are documented in the [merge-readiness-contract style guide](../../../style-guides/merge-readiness-contract.md) (installed at `~/.nexus-hub/style-guides/merge-readiness-contract.md`); a project adopts the subset that fits its team size and risk. See [[git-branching-workflow]] for how the merge fits the branching model, [[pr-description-writer]] for the issue-linkage and one-concern hygiene the contract checks, and [[shipping-and-launch]] for the release step the contract gates.

## Best Practices

- **Start with fewer gates** and add more as your workflow matures; over-gating slows velocity without proportional quality gains
- **Automate every criterion that can be automated**, and keep each check fast (under 5 minutes) to avoid workflow stalls
- **Set thresholds based on your project's current state**, not ideals; a project at 60% coverage should not gate at 90% overnight, and review them quarterly
- **Never disable a required criterion to pass a gate**; if a criterion is consistently blocking, either fix the underlying issue or reclassify it as optional with documented rationale
- **Use the PARTIAL outcome** judiciously, and share gate results with the team so everyone can see the quality bar and its trend

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "This criterion is blocking the gate, so I will disable it just this once." | A required criterion disabled "just once" is the exact path by which untested or insecure code reaches the next phase. If a criterion blocks consistently, fix the underlying issue or reclassify it as optional with documented rationale -- never silently waive it. |
| "More gates with stricter thresholds means higher quality." | Over-gating slows velocity without proportional quality gains, and a 90% coverage gate on a 60%-coverage project just gets routinely overridden until the gate means nothing. Set thresholds against the project's current state. |
| "The tool timed out, so it is UNGATED and I can move on." | A timeout reports UNGATED (`timeout`) and then goes through "After UNGATED or exhausted FAIL": the user is asked, or the gap is recorded. It never silently proceeds, because UNGATED is not a quiet PASS. |
| "I will eyeball whether the gate passed instead of defining explicit criteria." | A gate without explicit, mostly-automated criteria is a subjective judgment dressed up as a checkpoint. Two reviewers will pass and fail the same change, and the audit trail records nothing useful. |

## Verification

- [ ] Each gate has explicitly listed required and optional criteria
- [ ] Every criterion that can be automated is automated (manual checks are the exception)
- [ ] Pass / fail / partial behavior is defined for each gate
- [ ] Thresholds are set against the project's current state, not an aspirational ideal
- [ ] Gate outcomes are recorded in the result-tracking template for the audit trail
- [ ] Every logged result is one of PASS, PARTIAL, UNGATED, FAIL (fixable), or FAIL (blocking), and none is PASS without evidence for each required criterion

## Related Skills

- [[functional-verification]] - owns the procedure that produces functional evidence; this skill defines the criterion, threshold, and GO/NO-GO outcome that consume it.
- [[workflow-orchestrator]] - Orchestrating multi-phase workflows that use these gates
- [[task-coordinator]] - Coordinating tasks within gated phases
- [[plan-before-code]] - Planning phase that feeds into the plan-approved gate
- [[cross-model-orchestrator]] - Multi-model workflows that use gates at model transitions
- [[research-plan-implement]] - RPI workflow that uses gates between research, plan, and implement phases
- [[verification-before-completion]] - supplies the merge-readiness contract's evidence discipline (verify each gate against live current-head state) and owns how missing evidence is reported
- [[known-gaps-tracker]] - records the `QG` gap that "After UNGATED or exhausted FAIL" ends in
- [[egress-redaction]] - owns the hash rule for any gate-record input that is not a number or a boolean
- [[review-trapdoors]] - the project-specific recurring-blocker check the merge-readiness contract requires
- [[multi-agent-code-review]] - the review pass whose clean result the merge-readiness contract composes
- [[shipping-and-launch]] - the release step the merge-readiness contract gates
- [[git-branching-workflow]] - how the gated merge fits the project's branching model
- [[pr-description-writer]] - the issue-linkage and one-concern PR hygiene the contract checks

---

**Version**: 1.0.0
**Last Updated**: March 2026
**Based on**: Quality gate patterns, CI/CD pipeline best practices, multi-phase workflow management
