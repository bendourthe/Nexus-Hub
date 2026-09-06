---
name: ai-agent-development
description: AI agent architecture and development patterns including tool use, memory systems, planning loops, and multi-agent orchestration. Use when building AI agents, designing tool interfaces, or implementing agent evaluation.
summary_l0: "Build AI agents with tool use, memory, planning loops, and multi-agent orchestration"
overview_l1: "This skill provides comprehensive architecture and implementation guidance for building AI agents that reason, plan, use tools, and collaborate. Use it when designing agent architectures (ReAct, plan-and-execute, reflection), implementing tool-use patterns with function calling or MCP, building memory systems (short-term, long-term, episodic, semantic), creating planning and reasoning loops, orchestrating multi-agent systems, or adding guardrails and evaluation. Key capabilities include architecture pattern selection, tool integration schemas, memory system design, planning loop implementation, multi-agent topologies (supervisor, peer-to-peer, pipeline), guardrail enforcement, trajectory-based evaluation, and observability instrumentation. The expected output is production-grade agent code with structured logging, error handling, and cost tracking. Trigger phrases: build an agent, agent architecture, tool use, function calling, agent memory, planning loop, multi-agent, agent orchestration, agent evaluation, agent guardrails, ReAct pattern, MCP server."
---

# AI Agent Development

Comprehensive patterns and implementation guidance for building AI agents that reason, plan, use tools, and collaborate. Covers the full spectrum from single-agent architectures to multi-agent orchestration, with production-grade error handling, observability, and evaluation.

> **Effort-level note**: when agents run inside loops or parallel fan-out, default the `effortLevel` to `high`, not `max`. Iterative and concurrent runs compound effort-level cost without matching quality gains. See the **Effort-Level Strategy** section of [prompt-engineering/SKILL.md](../prompt-engineering/SKILL.md) for the decision table. A full Opus 4.7 Anti-Patterns table for agent workloads is maintained alongside this skill.

## When to Use This Skill

Use this skill for:

- Designing agent architectures (ReAct, plan-and-execute, reflection)
- Implementing tool-use patterns with function calling or MCP
- Building memory systems (short-term, long-term, episodic, semantic)
- Creating planning and reasoning loops
- Orchestrating multi-agent systems
- Adding guardrails and safety layers to agents
- Evaluating and testing agent behavior
- Instrumenting agents for observability

**Trigger phrases**: "build an agent", "agent architecture", "tool use", "function calling", "agent memory", "planning loop", "multi-agent", "agent orchestration", "agent evaluation", "agent guardrails", "ReAct pattern", "MCP server"

## What This Skill Does

Provides agent development expertise including:

- **Architecture Patterns**: ReAct, plan-and-execute, reflection, and hybrid approaches
- **Tool Integration**: Function calling schemas, MCP servers, tool selection logic
- **Memory Systems**: Working memory, long-term stores, episodic recall, semantic search
- **Planning Loops**: Goal decomposition, step execution, replanning on failure
- **Recursive context harness**: When the working set should live as a kernel variable rather than a reread transcript; see [references/recursive-context-harness.md](references/recursive-context-harness.md)
- **Multi-Agent Orchestration**: Supervisor, peer-to-peer, and pipeline topologies
- **Guardrails**: Input validation, output filtering, budget limits, human-in-the-loop
- **Evaluation**: Task completion metrics, trajectory analysis, regression testing
- **Observability**: Structured logging, trace propagation, cost tracking

## Instructions

### Step 1: Choose an Agent Architecture

Full walkthrough: [step-1-choose-an-agent-architecture.md](references/step-1-choose-an-agent-architecture.md) (load this step when you reach it).

### Step 2: Implement Tool Integration

Full walkthrough: [step-2-implement-tool-integration.md](references/step-2-implement-tool-integration.md) (load this step when you reach it).

### Step 3: Build Memory Systems

Full walkthrough: [step-3-build-memory-systems.md](references/step-3-build-memory-systems.md) (load this step when you reach it).

### Step 4: Implement Planning and Reasoning Loops

Full walkthrough: [step-4-implement-planning-and-reasoning-loops.md](references/step-4-implement-planning-and-reasoning-loops.md) (load this step when you reach it).

### Step 5: Orchestrate Multi-Agent Systems

Full walkthrough: [step-5-orchestrate-multi-agent-systems.md](references/step-5-orchestrate-multi-agent-systems.md) (load this step when you reach it).

### Step 6: Add Guardrails and Safety

Full walkthrough: [step-6-add-guardrails-and-safety.md](references/step-6-add-guardrails-and-safety.md) (load this step when you reach it).

### Step 7: Evaluate and Test Agents

Full walkthrough: [step-7-evaluate-and-test-agents.md](references/step-7-evaluate-and-test-agents.md) (load this step when you reach it).

### Step 8: Instrument for Observability

Full walkthrough: [step-8-instrument-for-observability.md](references/step-8-instrument-for-observability.md) (load this step when you reach it).

## Best Practices

- **Start simple**: Begin with a ReAct loop; add complexity only when needed
- **Fail loudly**: Agents that silently fail are harder to debug than agents that error clearly
- **Limit tool count**: Keep active tools to 10-20 for reliable selection (see `tool-design` skill)
- **Budget turns**: Set explicit turn limits to prevent runaway agent loops
- **Log everything**: Structured logs with trace IDs make debugging multi-step agents tractable
- **Test trajectories, not just outputs**: Verify the agent took the right path, not just that it arrived at a plausible answer
- **Use cheaper models for planning**: Planning steps need reasoning; execution steps often need tool use. Route accordingly
- **Keep memory lean**: Summarize aggressively; stale context degrades quality faster than missing context
- **Add guardrails early**: Safety checks are easier to add during development than to retrofit
- **Version your prompts**: System prompts are code; treat them with the same versioning discipline

## Common Patterns

Detailed guidance lives in [common-patterns.md](references/common-patterns.md) (load on demand).

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "We don't need turn limits -- the agent will stop when it's done" | Agents in infinite loops or with misconfigured tools have run for hours and incurred thousands of dollars in API costs before operators noticed; hard turn and cost limits are non-negotiable safety mechanisms, not optional guardrails. |
| "Guardrails slow down the agent and hurt task performance" | Guardrails that reject invalid tool calls prevent irreversible side effects (deleting production data, sending emails to real users) that no subsequent action can undo; the performance cost of validation is orders of magnitude cheaper than remediation. |
| "We'll add observability after we validate the agent works" | Agent failures in production are non-deterministic and context-dependent; without structured logs and trace IDs from the first deployment, diagnosing why the agent chose an unexpected action path is practically impossible. |
| "A single monolithic agent is simpler than multi-agent orchestration" | A single agent with 50+ tools saturates the context window with tool descriptions, degrading routing accuracy; multi-agent systems with 5-10 focused tools per agent consistently outperform monolithic agents on complex tasks. |
| "Memory is optional for agents that run on short tasks" | Short-task agents that interact with the same user across sessions without memory force users to re-explain context every time; compounding user friction is the primary reason real-world agent adoption stalls. |
| "We'll handle planning failures by restarting the agent" | Restart without replanning repeats the same failure; agents need explicit failure detection and a replanning step that incorporates the failure as new context, not a blind retry of the same plan. |

## Anti-Patterns (Opus 4.7)

Three anti-patterns that specifically hurt Opus 4.7 agent workloads. These are distinct from the Common Rationalizations above: they are patterns that feel correct and used to be correct for Opus 4.6, but compound cost without matching quality gains on 4.7.

| Anti-pattern | Why it feels right | Why it's wrong in Opus 4.7 | What to do instead |
|---|---|---|---|
| Fixed thinking budgets (`max_thinking_tokens=20000`) | Predictable cost per turn; easy to reason about. | Opus 4.7 scales thinking adaptively per turn. A fixed budget truncates reasoning on hard turns and wastes budget on easy ones. | Omit `max_thinking_tokens`; set `effortLevel` instead. Drop one tier (e.g., `xhigh` -> `high`) for cost control. |
| Excessive tool-calling as "thorough investigation" | "The agent looked at everything, so the answer is well-grounded." | Opus 4.7 prefers reasoning; too many tool calls burn tokens without adding signal and can crowd out the actual problem solving. | Reason first; invoke tools only when external state is needed. Explicit tool-invocation prompts beat implicit "check everything." |
| `max` effort level on extended runs (loop-operator, temporal workflows, multi-iteration agents) | "Best results always." | `max` compounds per iteration - 20 loop turns at `max` can 2-3x cost vs `xhigh` with no observable quality win on routine subtasks. | Default `xhigh` for runs; reserve `max` for single hard one-shot analyses. For parallel fan-out, de-escalate to `high`. |

Cross-links:
- Full decision guidance: [prompt-engineering - Effort-Level Strategy](../prompt-engineering/SKILL.md) and the [Opus 4.7 Practices](../prompt-engineering/SKILL.md#opus-47-practices) section.
- Output-side token optimization (distinct from tool-call frequency): [prompt-token-optimization](../../orchestration/prompt-token-optimization/SKILL.md).

## Verification

- [ ] Turn limit and cost limit are configured and enforced: agent stops and reports status when limits are reached
- [ ] Input guardrail validates all tool call arguments before execution; invalid inputs are rejected with an error, not silently corrected
- [ ] Structured logs with trace IDs exist for every agent run, covering tool calls, tool results, and planning decisions
- [ ] Evaluation suite runs on at least three scenarios: happy path, tool failure, and ambiguous input
- [ ] Memory layer (if applicable) persists and retrieves context across sessions: verified by running the same query in two separate sessions
- [ ] Replanning logic is triggered on tool failure: confirmed by injecting a tool error and observing the agent adjusts its plan

## References

- [references/lifecycle-hooks.md](references/lifecycle-hooks.md) - The agent-being-built lifecycle hook pattern (on_turn_start / on_turn_end / on_tool_call_pre / on_tool_call_post / on_error) for audit logging, retries, persona shifts, cost caps, and structured error recovery. Distinct from AI-assistant runtime hooks.
- [references/multimodal-ingestion.md](references/multimodal-ingestion.md) - Agent multimodal input patterns: the two ingestion shapes (in-memory bytes vs. filesystem path), supported media families, and mixed prompt lists. Agent input, as distinct from output evaluation.
- [references/sdk-structured-output.md](references/sdk-structured-output.md) - Constraining agent output to a Pydantic schema (the response-contract pattern), its failure modes, and the retry-then-fail-closed recovery. Output constraint, as distinct from output evaluation.
- [references/recursive-context-harness.md](references/recursive-context-harness.md) - Recursive context-harness pattern: context as a program variable in a persistent kernel, tool use as code over that variable, recursive delegation as async calls returning handles. When to consider it versus a catalog skill or a one-shot host session. Load on demand; do not inline it into this body.

## Related Skills

- [[tool-design]] -- designing tools and APIs for agent consumption
- [[prompt-engineering]] -- crafting effective system prompts for agents
- [[rag-implementation]] -- building retrieval systems agents can query
- [[context-manager]] -- managing context budgets in long agent sessions
- [[ai-agent-governance]] -- compliance and governance for AI agent deployments

---

**Version**: 1.0.0
**Last Updated**: March 2026

### Iterative Refinement Strategy
This skill is optimized for an iterative approach:
1. **Execute**: Perform the core steps defined above.
2. **Review**: Critically analyze the output (coverage, quality, completeness).
3. **Refine**: If targets aren't met, repeat the specific implementation steps with improved context.
4. **Loop**: Continue until the definition of done is satisfied.
