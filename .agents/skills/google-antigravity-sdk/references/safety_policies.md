# Safety Policies (declarative tool-call authorization)

The SDK gates every tool call through a declarative policy. A policy is a set of rules, each of which matches some set of tool calls and returns one of three decisions: `allow`, `deny`, or `ask` (request user confirmation). This is authorization for the agent you are building, distinct from the runtime hook policies of the AI assistant that builds it.

## The three decisions

- **allow** -- the tool call proceeds without confirmation.
- **deny** -- the tool call is blocked and the denial is reported back to the model, which can adapt.
- **ask** -- the configured confirmation path runs (for example, prompting a human) before the call proceeds.

A rule can match by tool name (a specific rule) or by wildcard (all tools, or a glob). A rule can also carry a predicate function that inspects the call's arguments and decides whether the rule applies.

## Resolution priority order

When more than one rule matches a tool call, the decision is resolved by a fixed priority, from highest to lowest:

1. **Specific Deny** -- a named-tool deny wins over everything.
2. **Specific Ask** -- a named-tool ask wins over any allow and over wildcard rules.
3. **Specific Allow** -- a named-tool allow wins over wildcard rules.
4. **Wildcard Deny** -- a deny that matches all tools.
5. **Wildcard Ask** -- an ask that matches all tools.
6. **Wildcard Allow** -- the broadest allow, lowest priority.

The practical consequence: a specific rule always beats a wildcard, and within the same specificity, deny beats ask beats allow. To carve a single tool out of a broad allow, add a specific deny for it; it will win.

## Predicate evaluation (fail closed)

A rule's predicate is a function that receives the tool call and returns whether the rule matches. Predicates let you allow a tool only for safe arguments (for example, allow `write_file` only under a workspace path). The critical semantic: if a predicate raises an exception during evaluation, the policy fails closed and treats the rule as matching. A predicate error never accidentally widens access; it errs toward the more restrictive outcome. Write predicates defensively, but know that a bug in one cannot silently open a tool.

## Default Behavior

The SDK's default policy is `confirm_run_command()`: it denies `run_command` and allows all other tools. This means an agent created with no explicit policy cannot run arbitrary shell commands, but can use its other tools. Start from this default and widen deliberately. Do not replace it with `allow_all()` to "make things work" during development; that removes the one guard standing between a confused model and arbitrary command execution.

## Convenience presets

The SDK ships presets for common postures. Use them as starting points, then layer specific rules on top:

- `allow_all()` -- allow every tool. Appropriate only for fully sandboxed, throwaway environments.
- `deny_all()` -- deny every tool. A locked-down baseline you open up one specific allow at a time.
- `confirm_run_command()` -- the default: deny `run_command`, allow the rest.
- `workspace_only(workspaces)` -- restrict file-touching tools to the given workspace paths (a predicate-backed preset).

## Recommended posture

For any agent that can mutate state, start from `deny_all()` or `confirm_run_command()` and add a specific allow only for each tool you have reasoned about. Treat MCP tools that write files or call external APIs exactly like `run_command`. See [examples/hooks.md](examples/hooks.md) for combining policy with an `on_tool_call_pre` hook for audit logging of every decision.

## Related

- [architecture.md](architecture.md) -- the Agent layer evaluates the policy during a turn.
- [mcp_integration.md](mcp_integration.md) -- MCP tools are gated by the same policy.
- [error_handling.md](error_handling.md) -- how a denial surfaces to the model.
- The `security/authentication-patterns` skill -- the resolution-order pattern as general doctrine.
- Back to the skill: [../SKILL.md](../SKILL.md).
