---
name: plan-review
description: Review a plan, spec, or requirements document with a panel of parallel persona lenses (coherence, feasibility, product, design, security, scope-guardian, adversarial) BEFORE any code is written, returning a severity-tagged findings table and a coverage note. Make sure to use this skill whenever the user says "review my plan", "review this spec", "review the requirements", "review the design doc", "critique this proposal", "red-team this plan", or wants a multi-perspective read of a plan / spec / PRD before implementation starts. SKIP, do NOT use for, reviewing code or a diff (use multi-agent-code-review), a single-agent cross-artifact consistency check across spec/plan/tasks in a feature directory (use cross-artifact-analyzer or analyze-spec), or generating the plan itself (use generate-plan).
summary_l0: "Review a plan or requirements doc with parallel persona lenses before coding"
overview_l1: "Reviews a single plan, spec, or requirements document through parallel persona lenses before implementation begins, so design and scope problems are caught while they are cheap to fix. It dispatches lens agents - coherence, feasibility, product, design, security, scope-guardian, and adversarial - over the document, each returning structured findings, then aggregates them into one severity-tagged table plus a coverage note stating which lenses ran and what each examined. It is read-only: it never edits the plan. The lenses reuse the same confidence anchors as the code-review pipeline, and security / adversarial reuse the existing reviewer agents. Use it after a plan is drafted and before coding starts. It complements the single-agent cross-artifact-analyzer and analyze-spec by adding independent, parallel viewpoints rather than one consistency pass. Trigger phrases: review my plan, review this spec, review the requirements, red-team this plan, critique this proposal."
---

# Plan Review

Review a plan, spec, or requirements document the way a strong design review would: several reviewers, each with a different stake (does it hang together? can we build it? does it serve the user? is the design sound? is it secure? is it in scope? how does it break?), reading the same document in parallel and pooling their findings. Catching a contradiction, an infeasible sequence, or a missing cut-line at the plan stage is an order of magnitude cheaper than catching it after the code is written.

This is the document-stage sibling of [[multi-agent-code-review]]. It is **read-only**: it produces findings about the plan and never modifies it.

## When to Use This Skill

Use when:

- A plan, spec, PRD, or design doc is drafted and you want a multi-perspective critique *before* implementation.
- The user asks to "review my plan", "review the spec", "review the requirements", "critique this proposal", or "red-team this plan".
- A plan is about to gate a phase of work and you want independent lenses on it.

**When NOT to use:**

- Reviewing code, a diff, or a PR - use [[multi-agent-code-review]].
- A single-agent consistency / coverage / ambiguity check across a *set* of artifacts (spec.md + plan.md + tasks.md) in a feature directory - use [[cross-artifact-analyzer]] or `/spec analyze`. Those answer "do these artifacts agree and cover each other?"; this answers "from seven independent viewpoints, what is wrong with this one plan?".
- Generating or drafting the plan in the first place - use `/plan`.

### Persona-fanout vs the single-agent analyzers

Reach for **plan-review** when you want *diverse, independent viewpoints* on one document - the product lens and the feasibility lens disagree productively, and that tension is the value. Reach for **cross-artifact-analyzer** / **analyze-spec** when you want *one analyst* to check that a feature's spec, plan, and tasks are mutually consistent and fully covered. They answer different questions; they compose well (run analyze-spec for coverage, plan-review for critique).

## Lenses

Each lens maps to an agent. Reuse where one already exists; the rest are the dedicated plan-lens agents.

| Lens | Agent | Always-on? | Asks |
|---|---|---|---|
| coherence | `coherence-reviewer` | yes | Is it consistent, complete, unambiguous? |
| feasibility | `feasibility-reviewer` | yes | Can we build it, in this order, with these assumptions? |
| product | `product-lens-reviewer` | yes | Does it solve the real problem, with a success metric? |
| design | `design-lens-reviewer` | conditional (technical plan) | Are the boundaries / data model / structure sound? |
| scope-guardian | `scope-guardian-reviewer` | yes | Is it bounded, sequenced, with cut-lines? |
| security | `security-reviewer` (reused) | conditional | Does the plan handle auth / data / trust correctly by design? |
| adversarial | `adversarial-reviewer` (reused) | conditional | How does the described system break under hostile use? |

Select the conditionals by document content: `design` when the plan proposes architecture / data models; `security` when it touches auth, user data, payments, or external trust; `adversarial` when it exposes a surface a hostile user reaches.

### Lifecycle checks (always-on, feasibility lens)

A multi-phase plan carries a lifecycle whose violations are cheap to spot and expensive to discover later, so the `feasibility` lens checks five of them on every plan. These are DETECTION rules. The policy itself is owned by `[[cicd-architect]]`; do not restate it here, and cite it in the suggested fix so the reader has one place to go.

| Signal | Why it is a finding | Severity floor |
|---|---|---|
| a per-phase push (any non-final phase that pushes, opens a pull request, or starts remote CI) | bills a full pipeline run per phase to validate work the plan itself says is incomplete | P1 |
| a missing local phase commit (a phase with no commit at its boundary) | leaves the plan unrevertible at phase granularity, so a bad phase can only be undone by hand | P2 |
| remote CI before the terminal phase | same cost as a per-phase push, and it usually appears as a stray "verify in CI" step rather than an explicit push | P1 |
| a missing terminal pipeline comparison (no final-phase reconciliation against the canonical contract) | the plan can complete while the pipeline it shipped has never been checked against anything | P1 |
| release before green integration (a release step not gated on a merged, green integration result) | ships from an unvalidated tree | P0 |

A plan that legitimately makes CI/CD a mid-plan deliverable is not a finding, provided it says so; check for the statement before reporting.

## Instructions

### 1. Resolve the document and intent

Identify the target doc (the user names it, or detect the active plan under `docs/**/plans/`). Read it once yourself to extract its stated goal, the problem it claims to solve, and its phase structure. If a project constitution or STRATEGY anchor exists, note it - `product-lens` and `scope-guardian` judge against it.

### 2. Select lenses

Always-on: coherence, feasibility, product, scope-guardian. Add design / security / adversarial per the table above. Record which lenses ran and which were skipped - the coverage note depends on it.

### 3. Dispatch lenses in parallel

Dispatch the selected lens agents over the same document, each receiving the doc path and the extracted intent. Respect the harness active-subagent limit (queue and retry on backpressure; never drop a lens). Each returns a JSON array of findings (title, severity P0-P3, location, confidence anchor, persona, suggested_fix) per the [confidence-anchored-scoring](../code-quality/references/confidence-anchored-scoring.md) field contract. Lenses are read-only.

### 4. Merge and gate

Apply the [confidence-anchored-scoring](../code-quality/references/confidence-anchored-scoring.md) discipline, same fixed order as the code pipeline: fingerprint dedup (the doc path + section bucket + normalized title), cross-lens promotion when two lenses agree, then the late confidence gate (suppress < anchor 75, except a P0 at 50+). Plan review is typically run for a human, so skip mode-aware demotion unless explicitly headless.

### 5. Emit the findings table + coverage note

Produce a single severity-tagged table, ranked P0 -> P3 then by confidence:

```markdown
| Severity | Lens | Location | Finding | Confidence | Suggested fix |
|---|---|---|---|---|---|
| P0 | feasibility | Phase 2, ln 140 | Phase 2 depends on the index built in Phase 4 | 75 | Reorder or stub the index for Phase 2 |
```

Follow it with a **coverage note**: which lenses ran, which were skipped and why, and any section of the plan no lens examined. Then a one-line verdict: `READY` / `REVISE` / `BLOCK` with the count of P0/P1 findings. Keep suppressed (sub-gate) findings in an appendix; never delete them. Do not edit the plan - findings only.

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "The plan reads fine to me, a review is overhead" | The author is the worst judge of their own plan's gaps - they fill ambiguity with intent the reader does not have. Independent lenses surface the contradiction the author reads past every time. |
| "Just have one reviewer read it" | One reviewer blends lenses and anchors on whatever they noticed first. The product lens and the feasibility lens find different failures; collapsing them to one pass loses the one you needed. |
| "Skip plan review, we'll catch it in code review" | A design or sequencing error caught at code review costs the whole implementation that built on it. The entire point of reviewing the plan is that the plan is still cheap to change. |
| "Edit the plan inline while reviewing to save a round-trip" | This skill is read-only by contract. Editing as you review entangles critique with authorship and hides what was wrong from the author. Emit findings; let the author revise. |
| "Run every lens on every doc for completeness" | A security lens on a pure-refactor plan, or a design lens on a copy-change spec, invents findings to look useful. Select by content and record the skips so coverage is auditable. |

## Verification

- [ ] The target document was identified and its goal / problem / phase structure extracted before dispatch.
- [ ] Lens selection is recorded, including which conditional lenses were skipped and why.
- [ ] Each dispatched lens returned findings in the confidence-anchored field shape (or an explicit empty array).
- [ ] The merge ran dedup -> promotion -> gate (gate last); suppressed findings are kept in an appendix.
- [ ] Output is a single severity-tagged table plus a coverage note plus a READY / REVISE / BLOCK verdict.
- [ ] The plan document itself was NOT modified (read-only contract honored).
- [ ] No outbound network call or new credential was introduced.

## Related Skills

- [[cicd-architect]] - owns the plan-lifecycle and CI/CD policy this skill's lifecycle checks DETECT violations of; it states the rule, this skill finds the breach.
- [[multi-agent-code-review]] - the same persona-fanout idea applied to a code diff after implementation.
- [[cross-artifact-analyzer]] - single-agent cross-artifact consistency / coverage / constitution-alignment across a feature directory; use for "do these artifacts agree?".
- `/spec analyze` - single-agent spec/plan/tasks consistency and ambiguity analysis; complements this skill's parallel critique.
- `/plan` - authors the plan this skill reviews; run plan-review on its output before implementing.
- [[code-quality]] - owns the [confidence-anchored-scoring](../code-quality/references/confidence-anchored-scoring.md) reference both review pipelines share.
