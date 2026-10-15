# Example: Lifecycle Hooks

Hooks fire around turns and tool calls. They are how you add audit logging, retries, persona shifts, and cost caps without modifying the agent loop.

## Code

```python
import asyncio
import json
from google.antigravity import Agent, LocalAgentConfig


def make_hooks(log_path: str, cost_limit_usd: float):
    spent = {"usd": 0.0}

    def on_turn_start(ctx):
        if spent["usd"] >= cost_limit_usd:
            raise RuntimeError(f"Cost cap hit: ${spent['usd']:.4f} >= ${cost_limit_usd:.2f}")

    def on_tool_call_pre(ctx):
        with open(log_path, "a", encoding="utf-8") as fh:
            fh.write(json.dumps({"tool": ctx.tool_name, "decision": ctx.decision}) + "\n")

    def on_turn_end(ctx):
        spent["usd"] += estimate_cost(ctx.input_tokens, ctx.output_tokens)

    def on_error(ctx):
        with open(log_path, "a", encoding="utf-8") as fh:
            fh.write(json.dumps({"error": str(ctx.error)}) + "\n")

    return {
        "on_turn_start": on_turn_start,
        "on_tool_call_pre": on_tool_call_pre,
        "on_turn_end": on_turn_end,
        "on_error": on_error,
    }


def estimate_cost(input_tokens: int, output_tokens: int) -> float:
    # Replace with the current per-token rate for your model.
    return (input_tokens + output_tokens) / 1_000_000 * 0.5


async def main() -> None:
    config = LocalAgentConfig(
        model="gemini-3.5-flash",
        hooks=make_hooks("agent-audit.jsonl", cost_limit_usd=1.00),
    )
    async with Agent(config) as agent:
        print((await agent.chat("Summarize today's open pull requests.")).text)


if __name__ == "__main__":
    asyncio.run(main())
```

## The five events

- `on_turn_start` -- before a turn; the place to enforce a cost cap.
- `on_turn_end` -- after a turn; carries token usage for accounting.
- `on_tool_call_pre` -- before a tool call; carries the tool name and policy decision (the audit trail).
- `on_tool_call_post` -- after a tool call; carries the result and duration.
- `on_error` -- on any failure; centralize recovery and logging here.

## What to notice

- The cost cap raises in `on_turn_start`, which aborts the run cleanly before the next expensive turn.
- Audit records are structured JSON, one per line, so they are queryable.
- Hooks keep cross-cutting concerns out of the agent's business logic.

## Related

- [../observability.md](../observability.md) -- what to capture and why.
- [../error_handling.md](../error_handling.md) -- the recovery logic `on_error` centralizes.
- The `ai-agent-development` skill's `lifecycle-hooks.md` reference -- the pattern in general terms.
- Back to the skill: [../../SKILL.md](../../SKILL.md).
