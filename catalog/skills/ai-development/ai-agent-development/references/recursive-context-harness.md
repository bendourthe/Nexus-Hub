# Recursive Context Harness

A harness pattern for agents that treat context as a program value, not as a transcript the model must reread. Use this file when designing or reviewing an agent runtime. It is not a Nexus-Hub skill rewrite and it does not ship a kernel. Link it from [[ai-agent-development]]; load it only when the architecture question is "should context live in the prompt or in a program?"

## The pattern

Three moves, always together:

1. **Context as a variable.** The working set (files, traces, tables, prior results) lives in a persistent kernel as ordinary program state. The model does not receive the whole blob on every turn.
2. **Tool use as code over that variable.** Reads, filters, joins, and writes are expressed as code the kernel runs against the variable. The model authors or selects the code; the kernel returns a handle, a summary, or a slice, not the raw corpus.
3. **Recursive delegation as async calls.** A sub-computation is an async function over the same variable (or a derived view). It returns a handle. The parent steers by that handle instead of pasting the child's transcript back into the parent's prompt.

The kernel is the durable process. The model is invoked for decisions the kernel cannot make. This is the same "LLM as the dynamic step, code as the loop" split [[loop-engineering]] already teaches for control loops, applied to context itself.

## When to consider it

Consider this pattern when:

- The working set is larger than a useful prompt and is structured (trees, logs, tables), so [[prompt-token-optimization]]'s functions-over-data principle is already the right instinct.
- Sub-computations must be addressable later (the persistent-id rule in [[multi-agent-coordinator]]), not respawned cold.
- You are building an agent product with a local kernel, not authoring a catalog skill.

Do not reach for it when:

- The job is a one-shot coding session in Claude Code, Cursor, or Codex. Those hosts already own context; Nexus-Hub does not add a kernel.
- You only needed a summary skill, a compressor, or a grep. Use [[context-optimization]] and functions-over-data instead.
- The design would upload the working set to a third-party "context service." That is out of scope under the MCP Registry Policy.

## What this catalog already covers

| Concern | Owner |
|---|---|
| Compute over data instead of reading it | [[prompt-token-optimization]] (functions-over-data) |
| Compress tool output at the boundary | [[context-optimization]] |
| Parent / sibling / child messaging and persistent subagent ids | [[multi-agent-coordinator]] |
| Iteration caps, idempotent gates, reward hacking | [[loop-engineering]] |
| Planning-loop implementation sketches | [step-4-implement-planning-and-reasoning-loops.md](step-4-implement-planning-and-reasoning-loops.md) |
| Multi-agent topologies | [step-5-orchestrate-multi-agent-systems.md](step-5-orchestrate-multi-agent-systems.md) |

This reference names the combined harness shape. It does not duplicate those owners' rules. If a delegate skill is unavailable, mark that portion not covered.

## Authoring notes

- Keep the kernel local. A remote kernel that holds source and prompts is a new egress surface.
- Handles must be stable ids, like instinct `id` values in [[continuous-learning]]: rollback and steering target the id, not a rewritten blob.
- Recursion needs the same simultaneous caps as any loop (iteration, token or cost, wall-clock). An unbounded recursive call is loopmaxxing with a stack.
