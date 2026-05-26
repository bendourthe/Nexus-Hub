# Agent Tool-Call Policy Resolution

Declarative tool-call authorization for an AI agent you are building, as distinct from the runtime authorization of the AI assistant doing the building. When an agent can invoke tools (run commands, write files, call APIs), each call must be authorized. The mature pattern is a declarative policy: a set of rules that each match some set of tool calls and return `allow`, `deny`, or `ask` (request confirmation). This is the agent-being-built layer, separate from the assistant-runtime hook policies documented in `catalog/hooks/settings.json` (PreToolUse / PostToolUse / Stop), which govern the harness, not the agent your code creates.

## Resolution priority order

When more than one rule matches a single tool call, the decision is resolved by a fixed priority, highest to lowest. This determinism is the point: the outcome must never depend on rule declaration order.

1. **Specific Deny** -- a deny rule naming a specific tool. Wins over everything; the surest way to forbid one tool.
2. **Specific Ask** -- an ask rule naming a specific tool. Forces confirmation even when a broader allow exists.
3. **Specific Allow** -- an allow rule naming a specific tool. Grants one tool without opening others.
4. **Wildcard Deny** -- a deny matching all tools (or a glob). The baseline "deny everything" guard.
5. **Wildcard Ask** -- an ask matching all tools. "Confirm everything not specifically allowed."
6. **Wildcard Allow** -- the broadest allow, lowest priority. Anything not otherwise decided is permitted.

The practical rule: a specific rule always beats a wildcard, and within the same specificity, deny beats ask beats allow. To carve one tool out of a broad allow, add a specific deny for it; it wins.

## Predicate evaluation (fail closed)

A rule may carry a predicate: a function that inspects the call's arguments and decides whether the rule applies (for example, allow `write_file` only under a workspace path). The critical semantic is **fail closed**: if a predicate raises an exception during evaluation, the policy treats the rule as matching rather than skipping it. A predicate bug therefore errs toward the more restrictive outcome and can never silently widen access. Write predicates defensively, but rely on fail-closed as the backstop.

## Convenience presets

Common postures are worth naming as presets, then layering specific rules on top:

- `allow_all()` -- permit every tool. Only for fully sandboxed, throwaway environments.
- `deny_all()` -- deny every tool. A locked-down baseline you open one specific allow at a time.
- `confirm_run_command()` -- deny command execution, allow everything else. A sensible default for most agents.
- `workspace_only(workspaces)` -- a predicate-backed preset that restricts file-touching tools to given workspace paths.

The recommended posture for any agent that can mutate state: start from `deny_all()` or `confirm_run_command()` and add a specific allow only for each tool you have reasoned about. Treat external (MCP) tools that write or call out exactly like command execution.

## Where this applies

This pattern belongs anywhere a Nexus-Hub skill teaches building an agent with tool access:

- `ai-development/ai-agent-development` -- the general agent-architecture skill (guardrails section).
- `ai-development/claude-agent-sdk` -- the Anthropic-side SDK build skill.
- `ai-development/google-antigravity-sdk` -- the Google-side SDK build skill (the concrete reference implementation of this exact resolution order).
- Any future SDK-build skill that grants an agent tools.

## Related

- [google-antigravity-sdk safety_policies.md](../../../ai-development/google-antigravity-sdk/references/safety_policies.md) -- the concrete reference implementation of this resolution order and the fail-closed predicate semantics.
- [google-antigravity-sdk SKILL.md](../../../ai-development/google-antigravity-sdk/SKILL.md) -- the skill that ships the worked policy examples.
- [authentication-patterns SKILL.md](../SKILL.md) -- the parent skill (human / service authorization; this reference extends it to agent tool-call authorization).
