# Observability

An autonomous agent is opaque unless you instrument it. The SDK's lifecycle hooks are the instrumentation surface: they fire around turns and tool calls and carry the data you need for token accounting, cost attribution, audit logging, and tracing. This document covers what to capture and how.

## What to capture

- **Token usage per turn** -- input and output token counts, available at turn end. This is the basis for cost attribution.
- **Tool calls** -- which tool, with what arguments, and the policy decision. This is the audit trail.
- **Latency** -- wall-clock duration per turn and per tool call, for performance profiling.
- **Errors** -- every failure, classified (transient, fatal, denial, parse failure). See [error_handling.md](error_handling.md).

## Hooks as the instrumentation surface

Attach hooks to the agent and let them emit structured records. The relevant events:

- `on_turn_start` / `on_turn_end` -- bracket a turn; `on_turn_end` carries token usage and duration.
- `on_tool_call_pre` / `on_tool_call_post` -- bracket each tool call; `pre` carries the tool name, arguments, and policy decision; `post` carries the result and duration.
- `on_error` -- fires on any failure; carries the error and context.

Emit one structured (JSON) record per event to a log sink. Structured logs are queryable; plain text is not. See [examples/hooks.md](examples/hooks.md) for a worked audit-logging hook.

## Token accounting and cost attribution

Read input and output token counts in `on_turn_end` and accumulate them per agent (and per conversation if you run several). Convert tokens to an approximate cost with the current per-token rates for the model in use. Attribute cost to the agent id so a multi-agent system shows where spend goes.

## Cost-cap pattern

Token accounting alone is passive. To make it active, check the accumulated cost in `on_turn_start` and abort the run when it crosses a hard limit:

```python
def make_cost_cap(limit_usd: float):
    spent = {"usd": 0.0}

    def on_turn_start(ctx):
        if spent["usd"] >= limit_usd:
            raise BudgetExceeded(spent["usd"], limit_usd)

    def on_turn_end(ctx):
        spent["usd"] += estimate_cost(ctx.input_tokens, ctx.output_tokens)

    return on_turn_start, on_turn_end
```

A hard cost cap that raises and aborts is the backstop behind every retry and recovery path. Wire it on the first iteration of any autonomous agent, not the last. The `ai-billing-safeguards` skill covers comprehensive cap strategies.

## Tracing

For multi-agent or multi-turn debugging, include a correlation id (agent id + conversation id + turn index) in every record so a single session can be reconstructed from the log. Forward the records to whatever tracing backend the project already uses; the `observability-setup` skill covers the sink side (structured logging, metrics, tracing).

## Related

- [error_handling.md](error_handling.md) -- the `on_error` hook and failure classification.
- [examples/hooks.md](examples/hooks.md) -- a concrete audit-logging and cost-cap hook.
- The `ai-billing-safeguards` skill -- hard spending caps for autonomous agents.
- The `observability-setup` skill -- structured logging, metrics, and tracing sinks.
- Back to the skill: [../SKILL.md](../SKILL.md).
