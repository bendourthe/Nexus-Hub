# Agent Lifecycle Hooks

Lifecycle hooks fire at the boundaries of an agent's turn-and-tool loop. They are how you add cross-cutting behavior (audit logging, retries, persona shifts, cost caps, structured error recovery) without editing the loop itself.

## Two hook layers, do not confuse them

There are two distinct hook layers in play when you build an agent with an AI assistant:

- **AI-assistant runtime hooks** (the harness side). These govern the assistant that is building your agent: `PreToolUse`, `PostToolUse`, `Stop`, `SessionStart`, configured in `catalog/hooks/settings.json`. They fire around the assistant's own tool calls, not your agent's.
- **Agent-being-built lifecycle hooks** (the SDK side, this document's subject). These fire inside the agent your code creates, around its turns and its tool calls.

This reference is about the second layer. Mixing the two is a common source of confusion: a cost cap on your agent's turns belongs in the SDK lifecycle hook, not in a harness `PreToolUse` hook.

## The five events

### on_turn_start

Fires before the agent processes a turn. The natural place to enforce a hard cost cap: check accumulated spend and raise to abort before the next expensive turn begins. Also useful for injecting per-turn context or rotating a persona based on conversation state.

### on_turn_end

Fires after a turn completes. Carries token usage for the turn, which is the basis for cost accounting. Accumulate input and output tokens here, convert to an approximate cost with the current per-token rate, and attribute spend to the agent id. This is the passive half of the cost-cap pair whose active half lives in `on_turn_start`.

### on_tool_call_pre

Fires before each tool call, carrying the tool name, arguments, and the policy decision. This is the audit trail: emit one structured record per call so you can later answer "what did this agent try to do, and was it allowed". It is also where a retry-with-backoff wrapper can short-circuit a call that recently failed.

### on_tool_call_post

Fires after each tool call, carrying the result and duration. Use it for latency profiling and for retry-with-backoff on transient tool failures: classify the failure, and if it is transient (timeout, rate limit, 5xx), schedule a bounded retry rather than surfacing the error immediately.

### on_error

Fires on any failure in the loop. Centralize recovery here rather than scattering try/except around every call. The standard branches: route a recoverable tool failure or schema parse error back to the model with a corrective message; fail closed and report for fatal errors (invalid credentials, repeated unrecoverable failures, budget exceeded). Structured error recovery, where a tool failure becomes a corrective system message that lets the model adapt, lives here.

## Use cases mapped to events

- **Audit logging** -- `on_tool_call_pre` (decision + args) and `on_turn_end` (token usage), emitted as structured JSON.
- **Retry with backoff** -- `on_tool_call_post` (classify and retry transient failures) and `on_error`.
- **Dynamic persona shift** -- `on_turn_start` (adjust standing instructions mid-conversation based on state).
- **Hard cost cap** -- `on_turn_start` (check) + `on_turn_end` (accumulate); raise to abort.
- **Structured error recovery** -- `on_error` (route the failure back to the model as a corrective message).

## Related

- [google-antigravity-sdk hooks example](../../google-antigravity-sdk/references/examples/hooks.md) -- a concrete five-event hook implementation with an audit log and cost cap.
- [google-antigravity-sdk observability.md](../../google-antigravity-sdk/references/observability.md) -- what to capture in each hook and why.
- [ai-billing-safeguards SKILL.md](../../ai-billing-safeguards/SKILL.md) -- the cost-cap layer the `on_turn_start` / `on_turn_end` pair enforces.
- [observability-setup SKILL.md](../../../infrastructure/observability-setup/SKILL.md) -- structured logging and tracing sinks for the audit records.
- [ai-agent-development SKILL.md](../SKILL.md) -- the parent skill (guardrails and observability sections).
