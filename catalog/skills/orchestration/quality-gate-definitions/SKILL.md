---
name: quality-gate-definitions
description: Reusable GO/NO-GO quality gate definitions for multi-phase workflows. Provides predefined gate types, criteria templates, and behavior configuration for planning, implementation, testing, security, and deployment checkpoints.
summary_l0: "Define reusable GO/NO-GO quality gates for multi-phase workflow checkpoints"
overview_l1: "This skill provides reusable GO/NO-GO quality gate definitions for multi-phase workflows, including predefined gate types, criteria templates, and behavior configuration. Use it when establishing checkpoints between planning, implementation, testing, security, and deployment phases, enforcing quality standards before phase transitions, or designing automated quality enforcement. Key capabilities include predefined gate type selection (planning, implementation, testing, security, deployment), criteria template customization, pass/fail threshold configuration, automated gate evaluation, manual override policies, gate failure remediation guidance, and integration with workflow orchestration. The expected output is configured quality gate definitions with criteria, thresholds, and enforcement behavior for each workflow phase. Trigger phrases: quality gate, GO/NO-GO, checkpoint, gate criteria, phase gate, deployment gate, quality checkpoint, workflow gate."
---

# Quality Gate Definitions

A library of reusable quality gate definitions that can be plugged into any multi-phase workflow. Each gate defines required and optional criteria, automatic and manual checks, and configurable pass/fail behavior. Use these gates as building blocks rather than reinventing checkpoint criteria for every workflow.

## When to Use This Skill

Use this skill for:

- Setting up quality checkpoints in multi-phase development workflows
- Defining GO/NO-GO criteria before implementation, testing, or deployment
- Standardizing quality expectations across team members and projects
- Configuring automated checks that run at phase transitions
- Any workflow where you need explicit approval criteria between phases

**Trigger phrases**: "quality gate", "GO/NO-GO criteria", "gate check", "phase transition criteria", "checkpoint definition", "approval criteria", "gate library", "pass/fail criteria"

## What This Skill Does

Provides quality gate capabilities including:

- **Gate Type Selection**: Choosing the right gate type for each workflow transition
- **Criteria Definition**: Specifying required, optional, automatic, and manual checks
- **Behavior Configuration**: Defining what happens on pass, fail, or partial pass
- **Gate Templates**: Ready-to-use checklists for common gate types
- **Result Tracking**: Reporting templates for gate outcomes and audit trails

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
| **PARTIAL** | Conditional proceed | All required criteria met but one or more optional criteria failed. Proceed with documented exceptions. |

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

**On FAIL (blocking)**:
- Log failure details to {artifact file}
- Stop workflow
- Escalate to {human / team lead / architect}
- Do not proceed until blocker is resolved

**On PARTIAL**:
- Log which optional criteria failed
- Document accepted risk in {artifact file}
- Proceed with acknowledgment
```

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

Record every gate execution for auditability. This is especially valuable for teams and for post-mortems.

**Gate Result Reporting Template**:

```markdown
# Gate Results: {Workflow Name}

## Summary
| Gate | Result | Date | Attempts |
|------|--------|------|----------|
| plan-approved | PASS | [date] | 1 |
| code-compiles | PASS | [date] | 1 |
| lint-passes | PARTIAL | [date] | 2 |
| tests-pass | PASS | [date] | 1 |
| coverage-threshold | PASS | [date] | 1 |
| no-security-vulns | PASS | [date] | 1 |
| performance-budget | N/A | [date] | - |

## Detailed Results

### Gate: lint-passes (Attempt 1 - FAIL)
**Date**: [timestamp]
**Failed Criteria**:
- R1: 3 lint errors in `src/processor.ts`
**Action Taken**: Auto-fixed 2 errors, manually fixed 1

### Gate: lint-passes (Attempt 2 - PARTIAL)
**Date**: [timestamp]
**Passed Required**: All
**Failed Optional**:
- O1: 2 warnings remaining (cosmetic, documented)
**Decision**: Proceed with documented exceptions

## Exceptions Log
| Gate | Criterion | Accepted Risk | Approved By |
|------|-----------|---------------|-------------|
| lint-passes | O1 (zero warnings) | 2 cosmetic warnings | [name] |
```

## Merge-Readiness Contract

The `merge-ready` gate above is a named, machine-checkable contract: a change is mergeable only when its required criteria all hold. Unlike the single-purpose gates (tests, lint, coverage), it is a COMPOSITE that binds the others plus PR hygiene into one verifiable statement, so "ready to merge" stops being a feeling and becomes a checklist backed by evidence.

The contract composes disciplines already in the catalog:

- **CI + review gates** (tests-pass, lint-passes, coverage-threshold, no-security-vulns above) supply R1-R2.
- **The evidence discipline** in [[verification-before-completion]] supplies R5: each gate is verified against the PR's live current-head state (the status rollup, the latest review submissions, `mergeable`), never a stale top-level comment or a remembered green check. A usage-limit or missing-review result is MISSING EVIDENCE, not approval.
- **The project's review trapdoors** ([[review-trapdoors]]) supply R6: the curated recurring-blocker list is applied before the change is called mergeable.

The collaborator rules (O1/O2) are deliberately CONFIGURABLE convention, not mandate: a solo maintainer cannot honor a no-self-merge rule, and a hotfix may need a time-boxed self-merge escape hatch. The options (no-self-merge by default, a net-lines / one-concern ceiling, a bus-factor self-merge escape hatch) are documented in the [merge-readiness-contract style guide](../../../style-guides/merge-readiness-contract.md) (installed at `~/.nexus-hub/style-guides/merge-readiness-contract.md`); a project adopts the subset that fits its team size and risk. See [[git-branching-workflow]] for how the merge fits the branching model, [[pr-description-writer]] for the issue-linkage and one-concern hygiene the contract checks, and [[shipping-and-launch]] for the release step the contract gates.

## Best Practices

- **Start with fewer gates** and add more as your workflow matures; over-gating slows velocity without proportional quality gains
- **Automate every criterion that can be automated** to reduce human bottlenecks and inconsistency
- **Set thresholds based on your project's current state**, not ideals; a project at 60% coverage should not gate at 90% overnight
- **Review gate definitions quarterly** and adjust thresholds as the project improves
- **Never disable a required criterion to pass a gate**; if a criterion is consistently blocking, either fix the underlying issue or reclassify it as optional with documented rationale
- **Keep gate checks fast** (under 5 minutes each) to avoid workflow stalls
- **Use the PARTIAL outcome** judiciously; it should be the exception, not the norm
- **Share gate results** with the team so everyone knows the quality bar and can see trends over time

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "This criterion is blocking the gate, so I will disable it just this once." | A required criterion disabled "just once" is the exact path by which untested or insecure code reaches the next phase. If a criterion blocks consistently, fix the underlying issue or reclassify it as optional with documented rationale -- never silently waive it. |
| "More gates with stricter thresholds means higher quality." | Over-gating slows velocity without proportional quality gains, and a 90% coverage gate on a 60%-coverage project just gets routinely overridden until the gate means nothing. Set thresholds against the project's current state. |
| "I will eyeball whether the gate passed instead of defining explicit criteria." | A gate without explicit, mostly-automated criteria is a subjective judgement dressed up as a checkpoint. Two reviewers will pass and fail the same change, and the audit trail records nothing useful. |

## Verification

- [ ] Each gate has explicitly listed required and optional criteria
- [ ] Every criterion that can be automated is automated (manual checks are the exception)
- [ ] Pass / fail / partial behavior is defined for each gate
- [ ] Thresholds are set against the project's current state, not an aspirational ideal
- [ ] Gate outcomes are recorded in the result-tracking template for the audit trail

## Related Skills

- [[functional-verification]] - owns the procedure that produces functional evidence; this skill defines the criterion, threshold, and GO/NO-GO outcome that consume it.
- [[workflow-orchestrator]] - Orchestrating multi-phase workflows that use these gates
- [[task-coordinator]] - Coordinating tasks within gated phases
- [[plan-before-code]] - Planning phase that feeds into the plan-approved gate
- [[cross-model-orchestrator]] - Multi-model workflows that use gates at model transitions
- [[research-plan-implement]] - RPI workflow that uses gates between research, plan, and implement phases
- [[verification-before-completion]] - supplies the merge-readiness contract's evidence discipline (verify each gate against live current-head state)
- [[review-trapdoors]] - the project-specific recurring-blocker check the merge-readiness contract requires
- [[multi-agent-code-review]] - the review pass whose clean result the merge-readiness contract composes
- [[shipping-and-launch]] - the release step the merge-readiness contract gates
- [[git-branching-workflow]] - how the gated merge fits the project's branching model
- [[pr-description-writer]] - the issue-linkage and one-concern PR hygiene the contract checks

---

**Version**: 1.0.0
**Last Updated**: March 2026
**Based on**: Quality gate patterns, CI/CD pipeline best practices, multi-phase workflow management
