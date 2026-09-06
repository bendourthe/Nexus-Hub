# Source Analysis: Nexus-Hub vs. "Claude Code Dynamic Workflows" + "Subagents vs. Agent Teams"

**Version**: v3.0.0 (planning; current released version is v2.4.0)
**Generated**: 2026-06-02
**Analyzer**: Claude Code -- compare-project command
**External Source**: `Downloads/Claude Code Dynamic Workflows.pdf` + `Downloads/Claude Subagents vs. Agent Teams, explained.pdf`
**Source Type**: Web Article (two related articles analyzed together)

## Section 1: Executive Summary

This report analyzes two related explainer articles on Claude Code's multi-agent primitives: a piece on the new **Dynamic Workflows** feature (Claude writes a JavaScript orchestration script that fans work across up to 16 concurrent / 1,000 total subagents, keeping intermediates out of the context window) and a companion piece contrasting **subagents** (parallelism through isolation, fire-and-forget) with **agent teams** (long-running peers that communicate and share a task list). Twelve actionable insights were extracted. Nexus-Hub already covers most of the orchestration *theory* (it ships `multi-agent-coordinator`, `multi-agent-code-review`, `competitive-generation`, `adversarial-verifier`, `task-coordinator`, `temporal-orchestration`, and per-role model tiering added in v2.4.0), so the net-new surface is small: one decision-guide skill that includes the new Dynamic Workflows primitive, optional "fan-out" guidance baked into the consolidated `/review` and `/test` commands, and a few enrichments to existing skills. The overall recommendation is **selective adoption** -- every insight is `skill-native` (catalog content), nothing requires code, and nothing introduces an outbound call or dependency. These insights primarily shape *how the v3.0.0 consolidated commands are authored* (when they should suggest fanning out) rather than adding standalone artifacts.

## Section 2: Source Overview

- **Article A -- "Claude Code Dynamic Workflows, explained!"**. Topic: the Dynamic Workflows feature shipped alongside Opus 4.8. Key thesis: orchestration logic should move *out of the LLM's context window and into executable code* -- Claude writes a JS script that the runtime executes, fanning out to tens-to-hundreds of parallel subagents, storing every intermediate result in script variables and returning only the verified converged answer. Positioned "above" subagents and agent teams. Notes it is a research-preview feature (Max/Team/Enterprise), token-heavy, with an `ultracode` effort setting that lets Claude auto-trigger workflows at `xhigh` reasoning.
- **Article B -- "Claude Subagents vs. Agent Teams, explained" (Akshay Pachaar, X thread)**. Topic: choosing the right multi-agent paradigm. Key thesis: the right question is not "should I use multiple agents?" but "what kind of coordination does this task actually need?" Subagents = parallelism + context compression, isolated, fire-and-forget, parent is sole coordinator. Agent teams = persistent peers with direct messaging and a shared `blockedBy` task list. Closes with first-principles design guidance (decompose by context, not by role), the five orchestration patterns, the three failure modes, and "start with a single agent; add complexity only where a measured problem demands it."

## Section 3: Key Insights Extracted

1. **(A) Orchestration-as-code**: move the plan out of the context window into an executable JS script; the script *is* the plan. Intermediates live in script variables, not the conversation.
2. **(A) Massive bounded fan-out**: up to 16 concurrent and 1,000 total subagents per workflow, versus a "handful" for subagents and "messy past 5" for agent teams.
3. **(A) Adversarial convergence**: agents attack a problem from independent angles, other agents try to refute the findings, and the system iterates until answers converge.
4. **(A) Durable / crash-safe execution**: progress saves continuously; interrupted jobs resume where they left off (agent teams die with the session).
5. **(A) Autonomous decomposition + auto-trigger**: Claude decides how to split work, how many agents to spawn, and how to verify; an `auto`/`ultracode` mode lets Claude decide *when* a workflow is warranted vs. a simpler approach.
6. **(A) Scope-first token discipline**: calibrate on a single folder before going full-scale because workflows burn far more tokens; review the execution plan on first trigger; enterprise has workflows off by default.
7. **(A) Canonical use case**: "audit every endpoint under `src/routes/` for missing auth checks and report what you find without changing any code" -- read-only, embarrassingly-parallel, large-surface audit.
8. **(B) Subagents = compression, not just parallelism**: the point is distilling vast exploration into a clean signal without polluting the parent's context; subagents cannot spawn subagents or talk to each other (a feature, not a limitation -- predictable information flow).
9. **(B) The `description` field is the routing signal**: the parent routes to a subagent based on its `description`; keep it specific.
10. **(B) Context-centric decomposition**: split work by *context boundaries*, not by role. Role-splitting (planner/implementer/tester) creates a telephone game that degrades quality at every handoff. An agent implementing a feature should also write that feature's tests (it already has the context).
11. **(B) The five orchestration patterns**: prompt chaining, routing (cheap model for easy, capable model for hard), parallelization (voting / sectioning), orchestrator-worker (the dominant pattern), evaluator-optimizer (generate-then-critique loop).
12. **(B) Three failure modes + when not to go multi-agent**: vague task descriptions cause duplicated work; verification agents declare victory without verifying (give concrete "run the full suite, do not mark complete until each passes" instructions); token costs compound (tier models, add budget controls). Start with one well-prompted agent; for coding specifically, parallel agents writing code make incompatible assumptions -- use subagents to *explore and answer questions*, not to write code alongside the main agent.

## Section 4: Relevance Analysis

| # | Insight | Status | Evidence / Notes |
|---|---------|--------|------------------|
| 1 | Orchestration-as-code | Not Applicable (platform feature) | Dynamic Workflows is an Anthropic runtime feature, not something a catalog "implements". Nexus-Hub can only *teach when to reach for it* and *author commands that suggest it*. |
| 2 | Bounded fan-out 16/1000 | Partially Implemented | `[[multi-agent-coordinator]]` and `[[competitive-generation]]` describe bounded parallel dispatch; they predate the Dynamic Workflows primitive and its specific limits. Gap: no skill names the new primitive or its 16/1000 envelope. |
| 3 | Adversarial convergence | Already Implemented | `[[adversarial-verifier]]` and v2.4.0's `multi-agent-code-review` "independent validation pass" + cross-reviewer promotion already encode refute-until-converge. |
| 4 | Durable / crash-safe | Already Implemented | v2.4.0 added crash-safe persistence discipline to `[[skill-eval-loop]]` (write-then-verify, re-read at phase boundaries, append-only log, per-experiment recovery markers). The principle is captured; it can be cross-linked from a new decision guide. |
| 5 | Autonomous decomposition + auto-trigger | Partially Implemented | `[[task-coordinator]]` / `[[workflow-orchestrator]]` cover decomposition. Gap: no guidance on the `ultracode`/auto-trigger decision (when to let Claude pick a workflow vs. a single agent). |
| 6 | Scope-first token discipline | Partially Implemented | `[[context-compression]]`, `[[prompt-token-optimization]]`, and the `ai-billing-safeguards` skill cover budget control. Gap: the specific "calibrate on one folder, review the plan on first trigger" workflow guidance is not stated. |
| 7 | Canonical audit use case | Missing (as command behavior) | This is exactly the consolidated `/review` (scope=security/full) and `/test` (large-surface generation) use case in v3.0.0. The opportunity is to author those command bodies to *offer* a fan-out path for large read-only audits. |
| 8 | Subagents = compression | Already Implemented | `[[context-manager]]`, `[[context-compression]]`, `[[multi-agent-coordinator]]` all frame subagents as context-protection/compression. |
| 9 | `description` is the routing signal | Already Implemented | This is the entire premise of Nexus-Hub's "pushy description" / combat-undertriggering guidance in `AGENTS.md` and `[[create-custom-command]]`, and of the 23 reviewer agents' `description` fields. |
| 10 | Context-centric decomposition | Partially Implemented | `[[component-boundary-identifier]]` and `[[multi-agent-coordinator]]` touch coupling/cohesion. Gap: the crisp "split by context not role; the implementer writes the tests" rule is not stated as a first-class principle in the orchestration skills. |
| 11 | Five orchestration patterns | Partially Implemented | The patterns are scattered across `[[multi-agent-coordinator]]`, `[[competitive-generation]]` (voting), `[[cross-model-orchestrator]]` (routing), `[[adversarial-verifier]]` (evaluator-optimizer). Gap: no single skill enumerates all five as a named catalog. |
| 12 | Failure modes + when-not-to | Partially Implemented | v2.4.0's `multi-agent-code-review` and `[[multi-agent-coordinator]]` cover model tiering and the verification-victory trap. Gap: the "start with one agent; don't parallelize code-writing" warning is not consolidated into a single decision gate. |

## Section 5: Adoption Plan (preliminary)

| Tier | What | Source insight | Target | Effort | Risk |
|------|------|----------------|--------|--------|------|
| P1 | New skill `agent-orchestration-primitives` -- a decision guide that names all four primitives (single agent / subagents / agent teams / Dynamic Workflows), their envelopes (16/1000), and a "start single, escalate on a measured problem" gate. Pulls together insights 1-12. | A1-A6, B8-B12 | `catalog/skills/orchestration/agent-orchestration-primitives/SKILL.md` (+ `references/five-patterns.md`) | Medium | Low |
| P2 | Author the consolidated `/review` and `/test` command bodies to *offer a fan-out path* for large read-only audits / large test-generation surfaces (the "audit every endpoint" pattern), gated on scope size and explicit user confirmation, with the scope-first token warning. | A2, A6, A7 | `catalog/commands/review.md`, `catalog/commands/test.md` (v3.0.0 consolidation) | Low | Low |
| P2 | Enrich `[[multi-agent-coordinator]]` with the context-centric-decomposition principle (split by context not role; implementer writes the tests) and the five-pattern catalog cross-link. | B10, B11 | `catalog/skills/orchestration/multi-agent-coordinator/SKILL.md` | Low | Low |
| P3 | Add a "when NOT to go multi-agent" + "don't parallelize code-writing" gate to `[[multi-agent-coordinator]]` and cross-link from `[[verification-before-completion]]`. | B12 | same | Low | Low |

## Section 6: Security and Reverse-Engineering Assessment (MANDATORY)

Every insight in this report is conceptual guidance or catalog content. None introduces a runtime dependency, an outbound call, a credential, or a third-party data processor. Evaluated against the `AGENTS.md` MCP Registry Policy decision tree:

| # | Insight | RE Classification | Internal deliverable | Risk tier | Rationale |
|---|---------|-------------------|----------------------|-----------|-----------|
| 1 | Orchestration-as-code | skill-native | Decision-guide skill (teach the primitive) | None | Platform feature; Nexus-Hub ships guidance only. No code, no outbound. |
| 2-6 | Fan-out / convergence / durability / auto-trigger / token discipline | skill-native | Skill body + cross-links to existing skills | None | All achievable by instructing the agent's own LLM (Policy tier 2). |
| 7 | Canonical audit use case | skill-native | Command-body guidance in `/review`, `/test` | None | Markdown command content; no new processor. |
| 8-12 | Subagent/team design principles | skill-native | Skill enrichments | None | Pure catalog content; no outbound, no credential. |

**MCP Registry Policy outcome**: all twelve insights are **tier 2 (LLM-native skill)** -- ship as catalog content, never as an MCP or external integration. No `vendor-intrinsic` items. No `drop-outright` items. There is nothing in these two articles that even tempts an external wrapper.

## Section 7: Implementation Sequence

Because every item is `skill-native`, sequencing follows dependency, not RE-bucket ordering:

1. Author `agent-orchestration-primitives` (the decision guide) first -- it is the anchor the command-body guidance and skill enrichments cross-link to.
2. Enrich `multi-agent-coordinator` (context-centric decomposition, five-pattern catalog, when-not-to gate) -- depends on the new skill existing for cross-links.
3. Bake the fan-out guidance into the consolidated `/review` and `/test` command bodies -- this happens naturally *inside* the v3.0.0 command-consolidation phases (those commands are being written anyway), so it adds near-zero marginal effort.

In the v3.0.0 plan these items are folded into the command-consolidation phases and a small orchestration-skills phase rather than standing alone.

## Section 8: Risks and Considerations

- **Risk of over-promising a preview feature**: Dynamic Workflows is a research-preview, plan-gated feature. The decision-guide skill must frame it as "if available in your harness" and never assume it is present. Mitigation: the skill teaches the *decision*, and the command bodies *offer* fan-out only as an optional path with explicit confirmation.
- **Risk of token blowups**: the canonical use case (fan-out audits) is token-heavy. The command-body guidance must carry the scope-first warning (calibrate on one folder, review the plan, confirm before full-scale). Mitigation: cross-link `ai-billing-safeguards` and `prompt-token-optimization`.
- **Risk of redundancy**: Nexus-Hub already has eight-plus orchestration skills. The new skill must be a *decision guide / index*, not a re-statement -- it should cross-link existing skills rather than duplicate them. Mitigation: keep it under the 500-line norm; push the five-pattern detail into a `references/` file.

### Items explicitly NOT recommended for adoption (security / policy reasons)

- **None.** No insight in these two articles implies an outbound call, a new dependency, a credential, or a third-party data processor, so there is no `drop-outright` item to record. (Contrast with the SkillSpector report, whose OSV.dev lookup is the only item in this v3.0.0 cycle that touches the network.)
