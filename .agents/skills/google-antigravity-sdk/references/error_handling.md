# Error Handling

An autonomous agent fails in characteristic ways. This document catalogs the failure modes and the standard recovery for each. The goal is an agent that fails safe and recoverably, not one that crashes the loop or silently does the wrong thing.

## Failure modes

### Missing or invalid API key

The SDK reads `GEMINI_API_KEY` at runtime. If it is absent or rejected, the agent cannot reach the backend. This is a fatal, fast failure: surface a clear message telling the user to set a valid key from the AI Studio key page, and exit. Do not retry an invalid key.

### Transient backend errors

Rate limits, timeouts, and 5xx responses from the backend are transient. The standard recovery is retry with exponential backoff and jitter, capped at a small number of attempts. Distinguish transient errors from fatal ones (an invalid key is not transient); retrying a fatal error wastes time and budget.

### Tool failures

A tool can fail for reasons unrelated to the model: an MCP server crashes, a custom tool raises, a file is missing. The SDK surfaces a tool failure back to the model as a tool error rather than crashing the loop, so the model can adapt (try a different approach, report the failure, or ask for input). Decide per tool whether a failure is recoverable (route back to the model) or fatal (abort the run).

### Policy denials

When the tool-call policy denies a call, that is not an error to crash on; it is information. The denial is reported back to the model, which can choose another path. Treat a denial as expected control flow. If an agent is denied repeatedly and cannot make progress, that is a sign the policy is too tight for the task or the persona is steering the model toward disallowed tools (see [safety_policies.md](safety_policies.md)).

### Structured-output parse failures

When a turn is constrained to a Pydantic schema and the model returns output that does not parse or is missing required fields, that is a recoverable error. The standard recovery is to route the parse error back to the model with a corrective instruction and retry once, then fail closed if it still does not conform. See [examples/structured_output.md](examples/structured_output.md).

## Recovery patterns

- **Retry with backoff** for transient backend errors only; cap attempts and add jitter.
- **Route back to the model** for tool failures and schema parse failures that the model can plausibly recover from.
- **Fail closed and report** for fatal errors (invalid key, repeated unrecoverable failures, budget exceeded).
- **Use `on_error` hooks** to centralize this logic rather than scattering try/except around every call. See [observability.md](observability.md) and [examples/hooks.md](examples/hooks.md).

## A note on cost during failures

Retry loops cost tokens. Pair any retry policy with the cost-cap hook pattern in [observability.md](observability.md) so a pathological retry storm cannot drain the budget. A hard cost cap that aborts the run is the backstop for every other failure mode.

## Related

- [safety_policies.md](safety_policies.md) -- policy denials as control flow.
- [observability.md](observability.md) -- `on_error` hooks and cost caps.
- [examples/hooks.md](examples/hooks.md) -- centralizing recovery in hooks.
- Back to the skill: [../SKILL.md](../SKILL.md).
