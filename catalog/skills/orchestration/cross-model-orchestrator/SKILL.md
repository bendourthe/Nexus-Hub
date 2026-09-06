---
name: cross-model-orchestrator
description: Orchestrate multiple AI coding assistants (Claude Code, Codex CLI, Gemini CLI, Copilot) in coordinated workflows with QA gates between models. Use when you want to leverage different model strengths for planning, implementation, review, and verification phases.
summary_l0: "Orchestrate multiple AI assistants in coordinated workflows with cross-model QA gates"
overview_l1: "This skill orchestrates multiple AI coding assistants (Claude Code, Codex CLI, Gemini CLI, Copilot) in coordinated workflows with QA gates between models. Use it when leveraging different model strengths for planning, implementation, review, and verification phases, when cross-model verification improves confidence, or when specific models excel at different task types. Key capabilities include model strength mapping (which model for which phase), cross-model workflow design, QA gate enforcement between model transitions, output format normalization across models, handoff protocol design, model-specific prompt adaptation, and cost optimization across providers. The expected output is a coordinated multi-model workflow with phase assignments, QA gates, and handoff protocols. Trigger phrases: cross-model, multi-model, orchestrate models, Claude and Codex, model strengths, cross-model review, multi-assistant, model coordination."
---

# Cross-Model Orchestrator

Specialized expertise in coordinating multiple AI coding assistants across a single development workflow. By assigning distinct roles to different models and enforcing quality gates between handoffs, you get stronger outcomes than any single model can deliver alone.

## When to Use This Skill

Use this skill for:

- Complex feature implementations where planning, coding, and review benefit from different model strengths
- High-stakes changes (security, data pipelines, infrastructure) that warrant independent verification
- Situations where one model's plan should be stress-tested by a second model before execution
- Large refactoring efforts that benefit from parallel review perspectives
- Any workflow where you want to reduce single-model blind spots

**Trigger phrases**: "cross-model workflow", "multi-model orchestration", "use different models", "model handoff", "independent verification", "cross-check with another model", "model disagreement"

## What This Skill Does

Provides cross-model orchestration capabilities including:

- **Role Assignment**: Mapping model strengths to workflow phases (planner, implementer, reviewer, verifier)
- **Artifact Handoff**: Structuring intermediate outputs so they transfer cleanly between models
- **QA Gates**: Enforcing GO/NO-GO criteria at each model transition
- **Disagreement Resolution**: Handling conflicts when models produce different recommendations
- **Workflow Templates**: Ready-to-use multi-model patterns for common development tasks

## Instructions

### Step 1: Define Model Roles

Assign each model a role based on its strengths. Use the decision matrix below as a starting point, then adjust based on your subscription access and experience.

**Model Strength Decision Matrix**:

| Capability | Claude Opus | Claude Sonnet | Codex CLI | Gemini CLI | Copilot |
|------------|-------------|---------------|-----------|------------|---------|
| Deep reasoning and planning | Strong | Moderate | Moderate | Strong | Moderate |
| Large codebase navigation | Strong | Strong | Strong | Strong | Strong |
| Code generation speed | Moderate | Fast | Fast | Fast | Fast |
| Security analysis | Strong | Moderate | Moderate | Moderate | Moderate |
| Test generation | Strong | Strong | Strong | Strong | Strong |
| Refactoring precision | Strong | Strong | Moderate | Strong | Strong |
| Long-context synthesis | Strong | Moderate | Moderate | Strong | Moderate |
| Cost efficiency | Low | High | High | High | High |

**Role Assignment Template**:

```
Planner:     [Model best at reasoning and architecture]
Implementer: [Model best at code generation for your stack]
Reviewer:    [Different model for independent perspective]
Verifier:    [Third model or same as planner for final check]
Breaker:     [Model with strong security/edge-case reasoning for adversarial testing]
```

**Example Assignment**:

```
Planner:     Claude Opus (deep reasoning, plan mode)
Reviewer:    Codex CLI (independent codebase review)
Implementer: Claude Sonnet (fast, cost-effective generation)
Verifier:    Gemini CLI (independent final verification)
Breaker:     Claude Opus (adversarial testing, see adversarial-verifier skill)
```

> **Note**: The Breaker role is optional and recommended for high-stakes changes (security, payments, data integrity). It uses the `adversarial-verifier` skill to actively try to break the implementation after verification passes. See the `adversarial-verifier` skill for detailed instructions on running the breaker phase.

### Step 2: Set Up Cross-Model Workflow

Execute the workflow in four sequential phases. Each phase produces artifacts that feed into the next.

```
┌──────────────────────────────────────────────────────────────────────┐
│                    CROSS-MODEL WORKFLOW                               │
│                                                                      │
│  Phase 1: PLANNING        Phase 2: QA REVIEW                        │
│  ┌───────────────────┐    ┌───────────────────┐                      │
│  │ Model A (Planner) │───>│ Model B (Reviewer) │                     │
│  │                   │    │                    │                      │
│  │ - Explore codebase│    │ - Review plan      │                     │
│  │ - Draft plan      │    │ - Check feasibility│                     │
│  │ - Identify risks  │    │ - Flag gaps        │                     │
│  └───────────────────┘    └────────┬───────────┘                     │
│           │                        │                                 │
│      [PLAN.md]              [REVIEW.md]                              │
│                                    │                                 │
│                             ┌──────▼──────┐                          │
│                             │  QA Gate 1  │                          │
│                             │  GO/NO-GO   │                          │
│                             └──────┬──────┘                          │
│                                    │                                 │
│  Phase 3: IMPLEMENTATION   Phase 4: VERIFICATION                    │
│  ┌───────────────────┐    ┌───────────────────┐                      │
│  │ Model C (Builder) │───>│ Model D (Verifier) │                     │
│  │                   │    │                    │                      │
│  │ - Execute plan    │    │ - Verify vs plan   │                     │
│  │ - Run tests       │    │ - Check coverage   │                     │
│  │ - Track progress  │    │ - Confirm quality  │                     │
│  └───────────────────┘    └───────────────────┘                      │
│           │                        │                                 │
│      [code + tests]         [VERIFY.md]                              │
│                                    │                                 │
│                             ┌──────▼──────┐                          │
│                             │  QA Gate 2  │                          │
│                             │  GO/NO-GO   │                          │
│                             └─────────────┘                          │
└──────────────────────────────────────────────────────────────────────┘
```

**Phase 1: Planning Phase**

Use your strongest reasoning model in plan/exploration mode.

1. Start a session with the planner model
2. Provide the feature request or task description
3. Instruct the model to explore the codebase without writing code
4. Request a structured plan saved to `PLAN.md` with these sections:
   - Goal and acceptance criteria
   - Files to modify (with rationale)
   - Implementation steps (ordered)
   - Testing strategy
   - Risk assessment

**Phase 2: QA Review Phase**

Switch to a different model to review the plan independently.

1. Open a fresh session with the reviewer model
2. Provide the original task description and `PLAN.md`
3. Ask the reviewer to:
   - Read the same codebase files referenced in the plan
   - Identify any gaps, risks, or incorrect assumptions
   - Check that the plan is consistent with existing patterns
   - Produce `REVIEW.md` with findings and a GO/NO-GO recommendation

**Phase 3: Implementation Phase**

Start a clean session with the implementer model.

1. Provide the approved `PLAN.md` and any revisions from `REVIEW.md`
2. Instruct the model to implement phase-by-phase
3. After each phase, run tests and confirm they pass before continuing
4. Track deviations from the plan in `PROGRESS.md`

**Phase 4: Verification Phase**

Use a different model (or the original planner) for independent verification.

1. Provide the original `PLAN.md`, the final code changes, and test results
2. Ask the verifier to:
   - Confirm every acceptance criterion is met
   - Run a fresh test pass
   - Check for missed edge cases
   - Produce `VERIFY.md` with GO/NO-GO for merge

### Step 3: Configure Communication Between Models

Models cannot share sessions, so all handoffs happen through files. Structure your artifacts for clean transfer.

**Required Artifact Files**:

| Artifact | Producer | Consumer | Purpose |
|----------|----------|----------|---------|
| `PLAN.md` | Planner | Reviewer, Implementer | Implementation blueprint |
| `REVIEW.md` | Reviewer | Planner (if NO-GO), Implementer | Feedback and corrections |
| `PROGRESS.md` | Implementer | Verifier | Deviation log and status |
| `VERIFY.md` | Verifier | Human (final decision) | Verification results |

**Artifact Format Template**:

```markdown
# [Artifact Name]
**Task**: [one-line description]
**Model**: [which model produced this]
**Date**: [timestamp]

## Summary
[2-3 sentence overview]

## Details
[structured content]

## Decision
**Recommendation**: GO / NO-GO
**Rationale**: [why]
**Conditions**: [any conditions on the recommendation]
```

**Tip**: Store all artifacts in a dedicated folder (e.g., `rpi/{feature-slug}/`) so every model session can find them easily.

### Handoff Egress Hygiene

Step 3 hands files to a second model, so the handoff is where egress discipline belongs. When the receiving model runs behind an external CLI or API, every artifact you pass it (the `PLAN.md`, the `REVIEW.md`, the `PROGRESS.md`, and any source file the plan cites) leaves your machine. Treat each handoff as a content-egress boundary governed by the MCP Registry Policy in `AGENTS.md`, and apply the same care you would give any outbound call. See [[agent-access-policy]] for the broader access posture this fits into.

- **Redact before the first send.** Substitute the contents of files matching a default deny-glob set with a visible marker such as `[redacted:<relative-path>]` instead of sending the raw bytes. The default set is `.env`, `.env.*`, `secrets/**`, `**/*.key`, plus any secret paths specific to your project. The marker keeps the artifact's structure legible to the reviewer while withholding the secret itself.

- **Get explicit first-send consent.** The first time a given destination model receives project content, state in one place WHAT will be sent (the artifact list), WHICH model or CLI receives it, and WHICH redaction globs are applied, then require an explicit confirmation before the content goes out. Record that consent (the destination, the list of artifacts sent, and the redaction globs applied) so later sends to the same destination in the same session do not re-prompt.

- **A fully-local reviewer needs no consent.** When the second model is served locally on the operator's own machine, the handoff never leaves the host, so the egress gate does not apply. Reserve the consent step for any destination that reaches an external service.

### Step 4: Quality Gates Between Models

Every model transition must pass through a quality gate. Do not proceed to the next phase if the gate fails.

**Gate 1: Plan Review Gate (between Phase 1 and Phase 3)**

| Criterion | Type | Check Method |
|-----------|------|-------------|
| All acceptance criteria are testable | Required | Manual review |
| No contradictions with existing architecture | Required | Reviewer model |
| Risk mitigations identified for each risk | Required | Reviewer model |
| Implementation steps are ordered correctly | Required | Reviewer model |
| Testing strategy covers acceptance criteria | Optional | Reviewer model |

**Gate 2: Verification Gate (between Phase 3 and merge)**

| Criterion | Type | Check Method |
|-----------|------|-------------|
| All tests pass | Required | Automated (`npm test`, `pytest`, etc.) |
| Every acceptance criterion has a corresponding test or manual check | Required | Verifier model |
| No untracked deviations from plan | Required | Compare `PROGRESS.md` to `PLAN.md` |
| Code compiles and lints cleanly | Required | Automated |
| No new security vulnerabilities introduced | Optional | Verifier model or scanner |

**Gate Actions**:

- **GO**: Proceed to next phase
- **NO-GO (fixable)**: Return to previous phase with specific feedback, then re-run gate
- **NO-GO (blocking)**: Escalate to human for decision

**Reviewer vs. judge**

Distinguish the two roles a second model can play at a gate:

- A **reviewer** produces non-binding notes: observations, adversarial critique, tone. It is for brainstorming and stress-testing and cannot honestly certify a binary outcome.
- A **judge** returns a structured, parseable verdict: a pass-or-revise decision, the blocking issues, and a confidence value.

Only a judge or a human may be the deciding source for a gate whose policy is "revise until clean", because a notes-only reviewer cannot honestly certify "clean" -- treating reviewer notes as a blocking clean verdict is fake precision. This is the same anti-self-deception discipline as the self-review entry in the Common Rationalizations table (a model reviewing its own work re-confirms its own assumptions), applied to the gate's deciding source rather than to who writes the code. Prefer a judge or a human for any gate that blocks progress; reserve a reviewer for gates where a forced pass/fail would itself be false precision. See [[quality-gate-definitions]] and [[adversarial-verifier]].

### Step 5: Handle Disagreements Between Models

When the reviewer or verifier disagrees with the planner or implementer, follow this resolution protocol.

**Disagreement Categories**:

1. **Factual disagreement** (e.g., "this API does not exist"): Verify by reading the actual source code. The model that is correct wins.
2. **Approach disagreement** (e.g., "strategy pattern vs. if-else"): Document both approaches with pros and cons. Let the human decide or default to the approach that is more consistent with the existing codebase.
3. **Risk assessment disagreement** (e.g., "this is safe" vs. "this is risky"): Err on the side of caution. If either model flags a risk, treat it as real until proven otherwise.
4. **Scope disagreement** (e.g., "we should also refactor X"): Stick to the original scope. Log the suggestion for a follow-up task.

**Resolution Template**:

```markdown
## Disagreement Log

### Issue: [description]
**Model A says**: [position]
**Model B says**: [position]
**Evidence**: [what the code actually shows]
**Resolution**: [which approach and why]
**Resolved by**: [human / evidence / codebase convention]
```

## Cross-Model Review Loop (loop-until-clean recipe)

A concrete, runnable specialization of the workflow above for the most common cross-model case: drive a SECOND model as a review pass over a change, then fix its findings and re-review until the change is clean. It adapts the shape of a mature review loop (scope -> review -> structured findings -> fix -> re-review) while staying strictly vendor-neutral.

**Vendor-neutrality rule.** The reviewing model is whatever the operator has configured - any second CLI or model they already run (Codex, Gemini, a local model, a separate Claude session). NEVER hardcode a specific vendor's CLI. Per the AGENTS.md MCP Registry Policy hard-no on generation-as-service, this recipe adopts the loop's SHAPE, not a lock-in to any one review tool: invoke whatever the operator names (for example via a `NEXUS_REVIEW_CLI` environment variable), never a fixed binary.

### The loop

1. **Resolve scope.** Decide what the reviewer sees: a PR diff (`git diff <base>...HEAD`), the diff against a base branch, or the uncommitted working tree (`git diff` / `git diff --staged`). Capture it once so every iteration reviews the same defined surface.

2. **Launch the review on a DIFFERENT model.** Run the configured review model over the scope as a background subagent in a fresh session (the independence rule from Best Practices), so the model that implemented the change is not the one reviewing it. The reviewing model / CLI is whatever the operator configured, never hardcoded. Apply the [Handoff Egress Hygiene](#handoff-egress-hygiene) gate when that model reaches an external service.

3. **Parse to a findings schema.** Normalize the raw review into structured findings so the loop can act on them deterministically:

    | Field | Meaning |
    |---|---|
    | `id` | stable identifier for the finding (used to detect recurrence across iterations) |
    | `severity` | critical / high / medium / low |
    | `category` | correctness / security / performance / style / test-gap / ... |
    | `location` | `file:line` |
    | `effort` | rough fix size (S / M / L) |
    | `status` | open / fixed / wont-fix / do-not-refix |

4. **HITL gate on the finding set.** Present the parsed findings and let the human choose the disposition BEFORE any code changes: fix all, criticals-only, or report-only. A report-only run stops here with the findings written out. This is the human-in-the-loop control point; it is not optional. A notes-only reviewer cannot certify "clean" on its own (see the reviewer-vs-judge distinction in Step 4).

5. **Atomic per-finding fix-verify-commit.** For each finding to be fixed, one at a time: apply the fix, run the project's lint / type-check / tests, and commit ONLY if they pass; if they fail, roll the change back so the tree stays clean and mark the finding `open` with a note. One finding per commit keeps history bisectable and stops a failed fix from poisoning the next. This is the [[verification-before-completion]] gate applied per finding.

6. **Re-review with safety limits.** Re-run steps 1-5 on the updated scope until the reviewer returns zero open findings, bounded by explicit limits so the loop always terminates:

    - **Max 3 iterations.** Stop after the third and report whatever remains.
    - **Recurrence -> do-not-refix.** A finding whose `id` reappears across two iterations (the fix did not satisfy the reviewer, or the reviewer is oscillating) is marked `do-not-refix`, skipped for the rest of the loop, and surfaced for a human. This prevents an infinite fix-review-refix cycle.

7. **Final report.** Emit a summary: findings found, fixed (with commit SHAs), wont-fix / do-not-refix (with reasons), and the iteration count. If findings remain after the iteration cap, say so plainly - a loop that hit its limit is not a clean result.

### Invocation

The recipe drives whatever review tool the operator configures. Point it at the review CLI via an environment variable rather than a hardcoded binary, and pass the program plus discrete arguments (never an interpolated shell string), matching the project Bash security rules:

```
# The operator chooses which reviewer to use; the recipe never hardcodes one.
export NEXUS_REVIEW_CLI="<your review model CLI>"
git diff "origin/main...HEAD" | "$NEXUS_REVIEW_CLI" review --format json
```

Run this in a fresh session (Step 2's independence rule), parse the output into the findings schema (Step 3), and drive the loop. For a richer multi-persona review pass instead of a single reviewer, use [[multi-agent-code-review]]; to have the reviewer actively try to BREAK the change rather than critique it, add the breaker phase from [[adversarial-verifier]]; to act on the findings without reflexive agreement, follow [[receiving-code-review]]. If you ship a wrapper script for this loop, keep it under the skill's `scripts/` bundle, cross-platform, and calling the operator's configured CLI (never a fixed vendor); this repo documents the invocation inline rather than bundling one.

## Best Practices

- **Use fresh sessions** for each model role to avoid context contamination from previous phases
- **Never skip the review phase** even when the plan looks obvious; independent review catches blind spots consistently
- **Keep artifacts machine-readable** with consistent Markdown structure so each model can parse them reliably
- **Assign roles based on actual experience**, not assumptions; test which models work best for your specific stack
- **Time-box each phase** to prevent runaway token consumption (e.g., 30 min planning, 15 min review, 2 hr implementation, 15 min verification)
- **Log all model outputs** so you can audit which model contributed what and improve role assignments over time
- **Start simple** with two models (planner + reviewer) before scaling to a full four-model workflow
- **Use the same prompt format** across models for consistency; the artifact templates above help with this
- **Invoke models and checks as argument arrays**, never interpolated shell strings: pass the program plus discrete arguments with an explicit per-call timeout. This is injection-resistant by construction and matches the project Bash security rules, which require building commands as arrays and never interpolating input into a command string

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "One capable model can plan, code, and review the change itself." | A model reviewing its own work re-confirms its own assumptions; the blind spot that produced the bug also hides it during self-review. The cross-model gate exists so a second model with different training catches what the first cannot see. |
| "The plan is obvious, so I will let the implementer skip the review handoff." | "Obvious" plans are where unverified assumptions hide. Skipping the independent review phase is the single most common way a cross-model workflow degrades into an expensive single-model workflow. |
| "I will reuse the same session across roles to save setup time." | Carrying the planner's context into the reviewer role contaminates the review with the planner's framing. Fresh sessions per role are what make the second opinion genuinely independent. |
| "I will just script the review loop against the one CLI I have." | Hardcoding a single vendor's review CLI turns a model-agnostic recipe into lock-in and violates the MCP Registry Policy's generation-as-service hard-no. Drive whatever reviewer the operator configured via an env var; the loop's value is its shape, not the tool. |

## Verification

- [ ] Each workflow phase has an assigned model and a documented rationale for the assignment
- [ ] A QA gate with explicit GO/NO-GO criteria sits at every model transition
- [ ] Intermediate artifacts are machine-readable Markdown that the next model can parse
- [ ] Each model role ran in a fresh session (no context carried across phases)
- [ ] Model disagreements were logged and resolved before proceeding

## Related Skills

- [[plan-before-code]] - Detailed planning methodology used in Phase 1
- [[workflow-orchestrator]] - General workflow orchestration patterns
- [[task-coordinator]] - Breaking down tasks across phases
- [[quality-gate-definitions]] - Reusable gate criteria referenced in Step 4
- [[multi-agent-code-review]] - a richer multi-persona review pass to run as the reviewer in the review loop
- [[adversarial-verifier]] - the breaker phase: have the reviewer try to break the change, not just critique it
- [[receiving-code-review]] - act on the review loop's findings without reflexive agreement
- [[verification-before-completion]] - the per-finding fix-verify gate the review loop's Step 5 applies

---

**Version**: 1.0.0
**Last Updated**: March 2026
**Based on**: Multi-model orchestration patterns, cross-validation workflows
