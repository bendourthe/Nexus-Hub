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

## Best Practices

- **Use fresh sessions** for each model role to avoid context contamination from previous phases
- **Never skip the review phase** even when the plan looks obvious; independent review catches blind spots consistently
- **Keep artifacts machine-readable** with consistent Markdown structure so each model can parse them reliably
- **Assign roles based on actual experience**, not assumptions; test which models work best for your specific stack
- **Time-box each phase** to prevent runaway token consumption (e.g., 30 min planning, 15 min review, 2 hr implementation, 15 min verification)
- **Log all model outputs** so you can audit which model contributed what and improve role assignments over time
- **Start simple** with two models (planner + reviewer) before scaling to a full four-model workflow
- **Use the same prompt format** across models for consistency; the artifact templates above help with this

## Related Skills

- `plan-before-code` - Detailed planning methodology used in Phase 1
- `workflow-orchestrator` - General workflow orchestration patterns
- `task-coordinator` - Breaking down tasks across phases
- `quality-gate-definitions` - Reusable gate criteria referenced in Step 4

---

**Version**: 1.0.0
**Last Updated**: March 2026
**Based on**: Multi-model orchestration patterns, cross-validation workflows
