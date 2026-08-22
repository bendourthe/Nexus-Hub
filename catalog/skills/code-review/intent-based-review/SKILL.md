---
name: intent-based-review
description: Review AI-generated code by verifying acceptance criteria pass/fail status rather than reading implementation line-by-line. Triggers detailed code inspection only for failed criteria. Use when reviewing AI-generated PRs at scale, when acceptance criteria are well-defined, or when review volume exceeds human capacity.
summary_l0: "Review AI-generated code by verifying acceptance criteria instead of line-by-line inspection"
overview_l1: "This skill reviews code changes by verifying that acceptance criteria are met rather than inspecting every line of implementation, designed for AI-generated code at scale where volume exceeds human cognitive capacity for line-by-line review. Use it when reviewing AI-generated code with well-defined acceptance criteria, when PR volume exceeds team capacity, when changes were produced by structured workflows (research-plan-implement) with specifications, when shifting review effort from implementation correctness to requirements fulfillment, or when reviewing multi-model orchestration output. Key capabilities include acceptance criteria extraction from specifications, automated pass/fail verification, selective deep-dive triggering only for failed criteria, requirement-to-implementation traceability, and structured review reports with evidence. The expected output is a criteria-based review report showing pass/fail status per criterion with detailed inspection findings only for failures. Trigger phrases: intent-based review, acceptance criteria review, AI code review, verify acceptance criteria, criteria-based review, requirement verification."
---

# Intent-Based Code Review

Review code changes by verifying that acceptance criteria are met, rather than inspecting every line of implementation. This approach is designed for AI-generated code at scale, where the volume and velocity of changes exceed human cognitive capacity for line-by-line review. Detailed code inspection is triggered only when acceptance criteria fail, focusing human attention where it matters most.

## When to Use This Skill

Use this skill when:

- Reviewing AI-generated code where acceptance criteria are well-defined
- PR volume exceeds the team's capacity for line-by-line review
- The change was produced by a structured workflow (e.g., research-plan-implement) with a REQUEST.md or specification
- You want to shift review effort from "Did the agent write it correctly?" to "Does it meet the requirements?"
- You are reviewing changes produced by a multi-model orchestration workflow

Do NOT use this skill when:

- The code is human-authored and benefits from mentoring-style review
- No acceptance criteria exist (use `requirement-enhancer` first to generate them)
- The change touches security-critical code (auth, crypto, payment) without dedicated security review
- The change is a novel architectural decision that requires design review

**Trigger phrases**: "intent-based review", "acceptance criteria review", "review AI-generated code", "review by intent", "criteria-based review", "outcome review", "skip line-by-line review"

## What This Skill Does

This skill provides an alternative review methodology:

- **Criteria Extraction**: Identifies acceptance criteria from REQUEST.md, user stories, or specification documents
- **Test Mapping**: Maps each criterion to one or more test results that verify it
- **Outcome Verification**: Checks whether each criterion passes based on test results, linter output, and type checker output
- **Gap Detection**: Identifies criteria without corresponding tests (coverage gaps)
- **Selective Deep Dive**: Triggers line-by-line review only for criteria that fail or lack test coverage
- **Review Report**: Produces a structured INTENT-REVIEW.md artifact

## Capturing Intent as the Review Oracle

The whole method depends on a faithful statement of intent, because intent is the oracle every finding is judged against. Intent is what the user set out to accomplish (the goal or request behind the work, in the user's own terms), not a description of the diff or a list of the files that changed. A reviewer handed only the diff cannot tell a deliberate choice from an accident, and the intent statement is what supplies that missing knowledge.

Capture the nuance the diff alone does not reveal:

- The user's actual goal, stated as an outcome rather than as a file list.
- The specific decisions and tradeoffs made along the way (what was chosen, and what it was chosen over).
- Any constraints or approaches the user deliberately ruled in or ruled out.
- Anything the user explicitly asked for that would otherwise look surprising in the diff (a deletion, an added guard, an unusual dependency).

Err on the side of completeness, not brevity: a few sentences to a short paragraph is normal. A thin one-line intent is the classic failure mode, because it makes the review flag things the user already chose on purpose, producing false escalations under the finding-action taxonomy below. A rich intent is exactly what lets the reviewer drop a finding into the mechanical-fix bucket instead of the escalate bucket.

Prefer intent known directly from the live conversation over intent reconstructed after the fact from session transcripts. Live intent is faster to obtain and less error-prone, so when the agent already knows the goal from the working session it should pass that along rather than mine logs to rediscover it. Reconstruction is a fallback for when the original context is gone, not the default. See [[verification-before-completion]] for proving the change against that intent.

## Classifying Findings by Action

Severity tells you how bad a finding is. It does not tell you who gets to decide what happens next. Classify every review finding by the action it implies, in three buckets:

- **Mechanical-fix**: an objective, low-risk defect (an ignored error return, a missing null check, a clear correctness, reliability, or security bug). The right fix is not in dispute, so the agent may resolve it on its own judgment.
- **Escalate-to-human**: a finding that challenges the user's deliberate intent or changes product behavior. It argues that an intentional addition, removal, or guard should be undone, or it questions a deliberate design or product choice. This is a decision only the user can make.
- **Informational**: a note that needs no fix (a heads-up, a future consideration, a context comment).

Hold the boundary between the first two buckets sharply. Routine correctness, reliability, and security fixes stay in the mechanical-fix bucket even when the smallest correct fix reintroduces a little previously-deleted logic. The escalate bucket is reserved for findings that genuinely contest intent or product behavior, not for any change that merely touches deleted code. Reintroducing one guard clause to fix a real crash is mechanical; arguing that an entire feature the user deliberately removed should come back is an escalation.

This classification is what makes intent-based review actionable. A reviewer that cannot tell a deliberate decision from a mistake fails in one of two directions: it rubber-stamps real defects (treating a bug as an intentional choice), or it flags the user's own choices (treating intent as a bug). The escalate bucket is handled by the escalation discipline in [[receiving-code-review]].

## Instructions

### Step 1: Locate Acceptance Criteria

Find the acceptance criteria for the change being reviewed. Check these sources in order:

1. `REQUEST.md` or `rpi/{feature-slug}/REQUEST.md` (from research-plan-implement workflow)
2. The PR description or linked issue
3. A specification document referenced in the commit message
4. The `PLAN.md` artifact (from cross-model-orchestrator workflow)

If no acceptance criteria exist, stop and use the `requirement-enhancer` skill to generate them before proceeding.

**Extract each criterion as a testable statement:**

```markdown
## Acceptance Criteria

| # | Criterion | Source |
|---|-----------|--------|
| AC-1 | [Specific, testable statement] | [REQUEST.md line N / PR description / etc.] |
| AC-2 | [Specific, testable statement] | [source] |
| AC-3 | [Specific, testable statement] | [source] |
```

### Step 2: Map Criteria to Verification Evidence

For each criterion, identify the verification evidence that confirms it. Evidence sources include:

| Evidence Type | How to Collect | Pass Condition |
|--------------|----------------|----------------|
| **Unit test** | `pytest` / `npm test` / `cargo test` | Relevant test(s) pass |
| **Integration test** | Test suite with integration tag | Relevant test(s) pass |
| **Type checker** | `mypy` / `tsc --noEmit` / `cargo check` | No type errors in changed files |
| **Linter** | `ruff check` / `eslint` / `clippy` | No errors in changed files |
| **Build** | `npm run build` / `cargo build` | Build succeeds |
| **Manual verification** | Run the application and test the feature | Feature works as described |

**Mapping template:**

```markdown
## Criteria-to-Evidence Map

| # | Criterion | Evidence | Result |
|---|-----------|----------|--------|
| AC-1 | [statement] | test_feature_x passes; type check clean | PASS / FAIL / NO EVIDENCE |
| AC-2 | [statement] | test_edge_case_y passes | PASS / FAIL / NO EVIDENCE |
| AC-3 | [statement] | Manual: endpoint returns 200 with valid payload | PASS / FAIL / NO EVIDENCE |
```

### Step 3: Run Automated Verification

Execute the automated checks and record results:

```bash
# Run the full test suite
pytest --tb=short -q          # Python
npm test                       # JavaScript
cargo test                     # Rust
dotnet test                    # C#
go test ./...                  # Go

# Run type checking
mypy .                         # Python
npx tsc --noEmit               # TypeScript
cargo check                    # Rust

# Run linting
ruff check .                   # Python
eslint src/                    # JavaScript
cargo clippy                   # Rust
```

Record the results against each criterion in the mapping table.

### Step 4: Classify Review Outcome

Based on the evidence, classify each criterion:

| Classification | Meaning | Action |
|---------------|---------|--------|
| **PASS** | Criterion has passing test(s) and no type/lint errors | No further review needed for this criterion |
| **FAIL** | Test(s) fail or type/lint errors exist | Trigger line-by-line review of the relevant code |
| **NO EVIDENCE** | No test covers this criterion | Write a test or perform manual verification |
| **PARTIAL** | Some evidence exists but coverage is incomplete | Review the gap; decide if additional testing is needed |

### Step 5: Selective Deep Dive

For any criterion classified as FAIL, NO EVIDENCE, or PARTIAL:

1. Identify the specific files and functions related to that criterion
2. Read only those files (not the entire diff)
3. Determine the root cause of the failure or gap
4. Request fixes or additional tests as needed

For criteria classified as PASS, **do not review the implementation** unless you have a specific reason to doubt the test quality.

### Step 6: Check for Untracked Side Effects

Even with all criteria passing, verify that the change does not introduce untracked side effects:

1. **Dependency changes**: Check if `package.json`, `requirements.txt`, `go.mod`, or similar files were modified. New dependencies require justification.
2. **Configuration changes**: Check for modifications to CI/CD, Dockerfiles, environment variables, or infrastructure config.
3. **Scope creep**: Compare the set of changed files to the files listed in PLAN.md. Flag any files changed that were not planned.
4. **Security-sensitive paths**: If the change touches auth, crypto, payment, or user data handling, escalate to the `security-review` skill regardless of criteria status.

### Step 7: Produce the Review Report

Generate INTENT-REVIEW.md as the review artifact:

```markdown
# Intent-Based Review Report

**Change**: [PR title or feature description]
**Reviewer**: [model or human name]
**Date**: [timestamp]
**Criteria Source**: [REQUEST.md / PR description / etc.]

## Criteria Verification Summary

| # | Criterion | Evidence | Result |
|---|-----------|----------|--------|
| AC-1 | [statement] | [test names / commands] | PASS |
| AC-2 | [statement] | [test names / commands] | PASS |
| AC-3 | [statement] | [evidence] | FAIL |

## Overall Result

- **Criteria Passing**: X / Y
- **Criteria Failing**: Z / Y
- **Criteria Without Evidence**: W / Y

## Deep Dive Findings

### AC-3: [Failed criterion]
**Root Cause**: [explanation]
**Affected Files**: [file list]
**Recommendation**: [fix description]

## Side Effect Check

| Check | Status | Notes |
|-------|--------|-------|
| No unplanned dependency changes | PASS/FAIL | [details] |
| No unplanned config changes | PASS/FAIL | [details] |
| No scope creep beyond plan | PASS/FAIL | [details] |
| No security-sensitive changes | PASS/ESCALATE | [details] |

## Verdict

**APPROVE** / **REQUEST CHANGES** / **ESCALATE**

**Rationale**: [1-2 sentences]
```

## When to Escalate to Full Code Review

Switch to the traditional `full-code-review` workflow (or individual review skills like `code-quality`, `security-review`, `performance-review`) when:

- More than 30% of criteria fail or lack evidence
- The change introduces a new architectural pattern not covered by existing tests
- Security-sensitive code is modified
- The acceptance criteria themselves are ambiguous or incomplete
- You observe suspicious patterns in the side effect check (unexplained file changes, new dependencies without justification)

## Best Practices

- **Write acceptance criteria before implementation**: the intent-based review only works when criteria exist upfront; use `requirement-enhancer` if they are missing
- **Trust passing tests**: if the test suite is well-maintained and criteria map to specific tests, a passing test is strong evidence; do not second-guess it without cause
- **Invest in test quality, not review time**: the long-term return on intent-based review comes from improving test coverage and acceptance criteria quality, not from adding more review steps
- **Combine with adversarial verification**: for high-stakes changes, pair this skill with the `adversarial-verifier` skill to have a breaker agent stress-test the implementation
- **Track criteria-to-test ratios**: if you consistently find criteria without evidence (NO EVIDENCE), the team needs better test generation practices
- **Use for AI-generated code, not human code**: human-authored code benefits from mentoring, knowledge sharing, and design discussion that intent-based review deliberately skips

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "Line-by-line review is more thorough than intent-based review" | Line-by-line review of AI-generated code is slower and still misses behavioral correctness -- reviewers can read syntactically clean code and miss that it satisfies none of the acceptance criteria, as seen in many AI-assisted PR audits. |
| "We don't write acceptance criteria because requirements are in the tickets" | Tickets describe what was requested, not what was accepted; without explicit acceptance criteria, any implementation can be argued to be correct, making review a matter of opinion rather than evidence. |
| "If tests pass, there's nothing more to check" | Tests pass against themselves; if tests were written to match a wrong implementation rather than the original requirement, intent-based review is the only layer that catches the mismatch between requirement and test intent. |
| "This skill only applies to AI-generated code" | Intent-based review applies whenever code is reviewed against requirements; it is most valuable for AI-generated code because AI output is fluent and syntactically clean, making line-by-line review less discriminating. |
| "NO EVIDENCE status just means the test suite is incomplete" | NO EVIDENCE is a flag that triggers investigation, not an automatic failure; but consistently accepting NO EVIDENCE results normalizes shipping untested requirements -- the gap accumulates until a critical acceptance criterion has no coverage. |

## Verification

- [ ] REQUEST.md or equivalent file exists with explicit, testable acceptance criteria for every deliverable
- [ ] Every acceptance criterion is mapped to at least one test, code section, or documented rationale (no unreviewed NO EVIDENCE items)
- [ ] All mapped tests pass: `pytest -q` / `npm test` / equivalent exits with code 0
- [ ] PARTIAL EVIDENCE items have a documented risk assessment and explicit owner sign-off
- [ ] Final verdict (APPROVED / APPROVED WITH CONDITIONS / REJECTED) is recorded with supporting evidence
- [ ] Any REJECTED items have a specific gap description that can be used to generate a targeted fix

## Related Skills

- [[requirement-enhancer]] -- generate acceptance criteria when none exist before this review runs
- [[quality-gate-definitions]] -- reusable gate criteria for workflow transitions
- [[cross-model-orchestrator]] -- multi-model workflow that produces artifacts reviewable with this skill
- [[research-plan-implement]] -- workflow that produces the REQUEST.md this skill consumes
- [[adversarial-verifier]] -- stress-test implementations that pass intent-based review
- [[traceability-matrix-generator]] -- map requirements to tests systematically

---

**Version**: 1.0.0
**Last Updated**: March 2026
**Based on**: Intent-based review patterns, acceptance criteria verification, Swiss Cheese verification model
