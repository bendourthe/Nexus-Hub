# Example: Periodic Trigger

A trigger pushes a message into the agent on an interval or in response to an external event, without a human typing a turn. Use it for background monitoring or scheduled check-ins.

## Code

```python
import asyncio
from google.antigravity import Agent, LocalAgentConfig
from google.antigravity.triggers import every


async def main() -> None:
    config = LocalAgentConfig(
        model="gemini-3.5-flash",
        system="You monitor a build queue and report only when something needs attention.",
    )

    async with Agent(config) as agent:

        async def check_queue():
            reply = await agent.chat("Check the build queue. Report only failures.")
            if reply.text.strip():
                print(reply.text)

        # Fire every 60 seconds.
        await every(60, check_queue)


if __name__ == "__main__":
    asyncio.run(main())
```

## What to notice

- A time-based trigger fires a callback on an interval; an event-based trigger fires on an external signal (a filesystem change, a queue message, a webhook).
- Triggers run inside the agent's async context, so the connection and tools stay live between firings.
- This is the agent-being-built layer. It is distinct from the Claude Code harness's `/loop` (which paces the assistant itself) and `/schedule` (which schedules remote agents), though the mental model is similar.

## Cost note

A trigger that fires often is a recurring cost. Pair it with the cost-cap hook ([hooks.md](hooks.md)) so an interval that is too tight cannot drain the budget unnoticed.

## Related

- The `workflow` `/loop` and `/schedule` skills' `sdk-triggers.md` reference -- the prior-art framing.
- Back to the skill: [../../SKILL.md](../../SKILL.md).
