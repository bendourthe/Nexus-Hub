# SDK Subagents (in-process spawning, as prior art)

An agent SDK can spawn and orchestrate subagents in-process: one main agent process owns the lifecycle of child agents through a Python API, sharing the process and (optionally) context with them. This is a different shape from the process-level multi-agent coordination this skill, `temporal-orchestration`, and `cross-model-orchestrator` cover, and knowing the distinction is what lets you pick the right one.

## In-process vs. process-level

- **In-process spawning (the SDK pattern)** -- the main agent constructs child agents as objects in the same process and drives them directly. Lowest latency, easy to share context, simplest to reason about. The tradeoff: child failures share the parent's failure domain, and every child runs in the same process with the same provider configuration.
- **Process-level coordination (this skill and friends)** -- each agent runs as its own process (or worker, or remote task), coordinated over a queue, a workflow engine, or an orchestration protocol. Stronger isolation, independent failure domains, and per-agent provider routing, at the cost of more moving parts and higher latency.

## When each applies

- Reach for **in-process** subagents when delegations are short, latency matters, and the children benefit from shared context (for example, a main agent fanning out a few quick research subtasks and merging the results).
- Reach for **process-level** coordination when you need isolation (a failing agent must not take down the others), per-agent provider routing, durability across crashes, or horizontal scale. `temporal-orchestration` adds durable replay; `cross-model-orchestrator` adds cross-model QA gates.

The two compose: a process-level orchestrator can run agents that themselves spawn in-process subagents.

## Related

- [google-antigravity-sdk subagents example](../../../ai-development/google-antigravity-sdk/references/examples/subagents.md) -- the concrete reference implementation of in-process subagent spawning.
