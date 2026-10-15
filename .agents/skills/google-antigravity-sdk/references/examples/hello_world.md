# Example: Hello World

The minimal Antigravity agent: configure, enter the async context, send one turn, print the reply.

## Prerequisites

- `pip install google-antigravity`
- `GEMINI_API_KEY` set in the environment (see the skill's Installation & Setup section).

## Code

```python
import asyncio
from google.antigravity import Agent, LocalAgentConfig


async def main() -> None:
    config = LocalAgentConfig(
        model="gemini-3.5-flash",
        system="You are a concise assistant. Answer in one sentence.",
    )

    async with Agent(config) as agent:
        reply = await agent.chat("What is the capital of France?")
        print(reply.text)


if __name__ == "__main__":
    asyncio.run(main())
```

## What to notice

- `model` is set explicitly even though `gemini-3.5-flash` is the default; pinning it keeps the agent stable across backend changes.
- `async with Agent(config) as agent` acquires the connection on enter and releases it on exit, so there is no manual teardown.
- This agent has no custom tools and runs under the default policy (deny `run_command`, allow the rest), so it is safe to run as-is.

## Next steps

- Give the agent a sharper identity: [persona_config.md](persona_config.md).
- Let it call your own functions: [custom_tool.md](custom_tool.md).
- Understand the layers behind `async with Agent`: [../architecture.md](../architecture.md).

## Related

- [../agent_configuration.md](../agent_configuration.md) -- the config fields used here.
- Back to the skill: [../../SKILL.md](../../SKILL.md).
