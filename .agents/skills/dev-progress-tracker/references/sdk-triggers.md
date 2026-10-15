# SDK Triggers (prior art for /loop and /schedule)

Background-task triggers in agent SDKs are a runtime-layer cousin of Nexus-Hub's `/loop` and `/schedule` workflows. A trigger is a background task that pushes a message into a running agent without a human typing a turn: it fires on a schedule or in response to an external event, and the agent reacts. This reference records the pattern as prior art so the mental model is documented alongside the workflow tools that share it.

## Two trigger shapes

- **Time-based** -- a callback fires on a fixed interval (an `every(60, callback)` style periodic trigger). Use it for polling, heartbeat checks, and scheduled summaries.
- **Event-based** -- a callback fires when an external signal arrives: a filesystem watcher detecting a changed file, a message landing on a queue, or an inbound webhook. Use it for reactive monitoring where the cadence is driven by the world, not a clock.

Both shapes run inside the agent's own runtime, so the connection and tools stay live between firings.

## Why this is prior art for /loop and /schedule

The Claude Code harness has two surfaces with the same mental model but a different runtime layer:

- `/loop` paces the **assistant itself** on a recurring interval (re-invoking the agent loop).
- `/schedule` creates **cron-scheduled remote agents** that run on a server-side schedule.

The SDK trigger pattern is the agent-being-built equivalent: the agent your code creates schedules its own background tasks. Same idea (work that fires without a human prompt), different layer (inside the agent vs. around the assistant). Reading the SDK pattern clarifies what `/loop` and `/schedule` are doing one level up, and vice versa. Pair any frequently-firing trigger with a hard cost cap so an interval that is too tight cannot drain a budget unnoticed.

## Related

- [google-antigravity-sdk periodic_trigger example](../../../ai-development/google-antigravity-sdk/references/examples/periodic_trigger.md) -- the concrete reference implementation of a time-based trigger inside an agent.
