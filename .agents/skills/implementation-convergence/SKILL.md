---
name: implementation-convergence
description: Assess the present implementation against a plan's stated intent AFTER an implementation pass, classify every gap with traceability, and append the remaining work as new tasks - never rewriting history, and guaranteeing a byte-for-byte no-op when the code already satisfies the plan. Make sure to use this whenever the user says "converge the code with the plan", "what's left unbuilt from the plan", "did the implementation drift from the spec", "assess the code against the plan and append the remaining work", "post-implementation gap check", or wants to know whether an implementation actually delivered its plan before review or release. SKIP, do NOT use for - artifact-vs-artifact consistency analysis before or during implementation (use cross-artifact-analyzer); the per-version deferral ledger (use known-gaps-tracker); verifying a single change end-to-end (use verification-before-completion).
summary_l0: "Assess code against a plan post-implementation, classify gaps, and append remaining work as new tasks"
overview_l1: "This skill runs a convergence pass after an implementation over an existing plan or task file: it treats the plan, spec, and tasks (and the project constitution when present) as the sole source of intent, inventories every requirement, acceptance criterion, plan decision, and task under a stable key, maps the code scope the artifacts name, and classifies each gap as missing, partial, contradicts, or unrequested with a CRITICAL/HIGH/MEDIUM/LOW severity. It is a present-state assessment, not a diff tool - no git history or branch comparison. Its only write is append-only: a single new Phase N: Convergence section of strict-format T### task lines, each traced to its source-ref and gap type, never rewriting, renumbering, reordering, or deleting an existing task. When nothing remains it leaves the task file byte-for-byte unchanged and reports converged. Trigger phrases: converge the code with the plan, what's left unbuilt, did the implementation drift from the spec, post-implementation gap check."
---

# Implementation Convergence

Assess what was actually built against what a plan said to build, then append the remaining work as new tasks without ever rewriting the ledger. A convergence pass runs after an implementation and answers one question with traceable evidence: does the present code satisfy the plan's stated intent, and if not, exactly what is left? It is the post-implementation, code-vs-artifact counterpart to the pre-implementation, artifact-vs-artifact `[[cross-artifact-analyzer]]`.

## When to Use This Skill

Use this skill when you need to:

- Converge the current code with the plan after an implementation pass ("what's left unbuilt from the plan").
- Decide whether an implementation drifted from the spec before you open review or cut a release.
- Turn a post-implementation gap assessment into concrete, tracked follow-up tasks the team can pick up.
- Produce a traceable, cite-by-ID gap report where every finding points back to the requirement, criterion, or task it came from.

**When NOT to use this skill:**

- You want artifact-vs-artifact consistency (spec vs plan vs tasks) BEFORE or DURING implementation - use `[[cross-artifact-analyzer]]` (read-only, no code involved).
- You want the per-version deferral ledger of known gaps, warnings, and deferred items - use `[[known-gaps-tracker]]`; this skill feeds that ledger, it does not replace it.
- You want to verify that a single change actually works end-to-end - use `[[verification-before-completion]]`.
- There is no plan or task artifact to converge against - there is no intent to measure the code against, so stop.

**Trigger phrases**: "converge the code with the plan", "what's left unbuilt from the plan", "did the implementation drift from the spec", "assess the code against the plan and append the remaining work", "post-implementation gap check".

## Instructions

The convergence contract has eight parts. Present the findings summary (part 7) before making the single permitted write (part 5).

### 1. Scope and timing

Run this ONLY after an implementation pass over an existing plan or task file. The plan, spec, and tasks artifacts are the sole source of intent; when a project constitution exists (`docs/<version>/constitution.md` or `CONSTITUTION.md`), its MUST principles are governing constraints layered on top. This is a present-state assessment of the code as it stands now - not a diff tool. Do not compare git history or branches; assess whether the current tree satisfies the stated intent.

### 2. Build the intent inventory

Give every unit of intent a stable key so findings are cite-able and stable across reruns:

- Functional requirements (`FR-003`), success criteria (`SC-002`), user-story acceptance criteria (`US1/AC2`), task ids (`T042`), and plan-phase touch-points (`Phase 3 / sub-task 3.2`).
- Build a code-scope map bounded to the files and modules the artifacts name. Do NOT infer scope beyond what the artifacts define - unrequested code is a finding (part 3), not an expansion of scope.

### 3. Classify each gap (four-type taxonomy)

Every finding is exactly one of:

- **missing** - required work is absent from the code.
- **partial** - present but incomplete against its stated criterion.
- **contradicts** - code conflicts with stated intent or a constitution MUST.
- **unrequested** - work present in the code that no artifact called for; surfaced for review, never auto-deleted.

### 4. Assign severity

- **CRITICAL** - a constitution-MUST violation, or a missing/contradicting gap that blocks a P1 story's baseline.
- **HIGH** - a gap on a core requirement.
- **MEDIUM** - a secondary-requirement partial, or an unclear unrequested addition.
- **LOW** - polish.

### 5. The append-only write contract

The ONLY permitted write is appending a single new `## Phase N: Convergence` section to the task file, where `N` is the highest existing phase number plus one. In that section:

- Emit one task line per actionable finding, using the next available `T###` ids (highest existing id + 1, continuing upward).
- Order the lines CRITICAL and HIGH first.
- Trace each line to its source-ref and tag it with its gap type, in the description.
- Each line MUST conform to the strict task-line contract used by `[[implementation-plan]]` and consumed by `[[tasks-to-issues]]`: `- [ ] T### [P?] [US?] <description>` (the optional `[P]` parallel marker precedes the optional `[US#]` story label).

Never rewrite, renumber, reorder, or delete an existing task line - including tasks from a prior convergence phase. Convergence is strictly additive; the ledger is append-only so it stays a faithful, re-runnable record.

Example appended section:

```markdown
## Phase 7: Convergence

- [ ] T081 [US1] missing (FR-003): enforce the rate-limit header on the auth endpoint; no limiter present in auth/middleware
- [ ] T082 partial (SC-002): retry path covers 5xx but not timeouts; SC-002 requires both
```

### 6. The converged no-op guarantee

When no actionable finding remains, leave the task file **byte-for-byte unchanged** - do not append an empty `## Phase N: Convergence` header. Report `converged` with the summary counts (0 missing / 0 partial / 0 contradicts, and any accepted unrequested items). A clean convergence produces no diff, so "no change" is itself the signal.

### 7. Present the findings summary before writing

Before any write, present an in-session findings table so the human sees the assessment and can veto the append:

| id | gap type | severity | source-ref | evidence | remaining work |
|---|---|---|---|---|---|

Only after presenting it do you make the single append (part 5) or confirm the no-op (part 6).

### 8. Hand off

- On **tasks-appended**: recommend `/implement` to complete the new convergence phase.
- On **converged**: recommend proceeding to review or release.
- Feed any deferred or won't-fix findings to `[[known-gaps-tracker]]` rather than leaving them only in the summary.

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "The plan is basically done, I'll just tidy the task file while I'm here - renumber and reorder it." | Renumbering or reordering corrupts the ledger: `[[tasks-to-issues]]` and prior convergence phases reference tasks by id, so a renumber breaks every downstream reference. The write contract is append-only for exactly this reason. |
| "Nothing is left, so I'll append a `## Phase N: Convergence` header noting it's converged." | An empty header is a diff, and a diff implies work landed. The no-op guarantee is byte-for-byte: a converged tree leaves the file untouched so "no change" stays a meaningful signal. |
| "This is really a diff between what I coded and the plan, so I'll git-diff the branch." | Convergence is a present-state assessment against stated intent, not a VCS diff. The code may satisfy the plan through work on another branch or a refactor with no matching commit; assess the tree as it stands, keyed to the artifacts. |
| "I found extra code that isn't in the plan - I'll delete it to converge." | `unrequested` findings are surfaced for human review, never auto-deleted. The plan may be stale, or the code may be load-bearing; deletion is a decision for the maintainer, not the convergence pass. |
| "This overlaps with the analyze scope, so I'll just run cross-artifact-analyzer." | That skill is read-only and operates on artifacts before code exists. Convergence is the post-implementation pass that measures code against intent and appends the remaining work. Different timing, different input, different output. |

## Verification

- [ ] The pass ran only after an implementation over an existing plan/task file; the plan/spec/tasks (and constitution if present) were the sole source of intent.
- [ ] Every finding carries a stable source-ref key, one of the four gap types, and a severity.
- [ ] The only write was a single appended `## Phase N: Convergence` section (N = highest existing + 1); no existing task line was rewritten, renumbered, reordered, or deleted.
- [ ] Every appended task line matches the strict `- [ ] T### [P?] [US?] <description>` contract with CRITICAL/HIGH first and a source-ref + gap type in the description.
- [ ] On a converged result, the task file is byte-for-byte unchanged (no empty header) and the report states `converged` with summary counts.
- [ ] The in-session findings table was presented before any write.
- [ ] `unrequested` findings were surfaced for review, not auto-deleted.

## Related Skills

- [[cross-artifact-analyzer]] - the read-only, pre/during-implementation, artifact-vs-artifact counterpart; convergence is its post-implementation, code-vs-artifact mirror.
- [[known-gaps-tracker]] - the per-version deferral ledger this skill feeds (deferred or won't-fix findings) but does not replace.
- [[verification-before-completion]] - verifies a single change end-to-end; convergence assesses a whole implementation against the plan.
- [[tasks-to-issues]] - consumes the appended strict-format `T###` lines to file linked issues.
- [[implementation-plan]] - produces the plan and the strict task-line format this skill appends to.

---

**Version**: 1.0.0
**Last Updated**: July 2026
**Based on**: Post-implementation code-vs-intent convergence, append-only task-ledger, and source-ref traceability patterns
