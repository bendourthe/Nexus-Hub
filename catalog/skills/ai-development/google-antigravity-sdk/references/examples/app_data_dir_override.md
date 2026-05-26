# Example: Application Data Directory Override

The agent persists working artifacts (brain state, cached context) under an application data directory. The default is `~/.gemini/antigravity/brain/`. Override it for per-project isolation, ephemeral test runs, or a faster disk.

## Code

```python
import asyncio
import tempfile
from google.antigravity import Agent, LocalAgentConfig


async def main() -> None:
    # Per-project isolation: a dedicated brain directory for this agent.
    config = LocalAgentConfig(
        model="gemini-3.5-flash",
        app_data_dir="/srv/agents/project-x/brain",
    )
    async with Agent(config) as agent:
        print((await agent.chat("Resume where we left off.")).text)


async def ephemeral() -> None:
    # Ephemeral: a throwaway directory for a test that should leave no state behind.
    with tempfile.TemporaryDirectory() as tmp:
        config = LocalAgentConfig(model="gemini-3.5-flash", app_data_dir=tmp)
        async with Agent(config) as agent:
            print((await agent.chat("One-shot question.")).text)


if __name__ == "__main__":
    asyncio.run(main())
```

## What to notice

- When the override path does not exist, the SDK creates it.
- Use a dedicated directory per logical agent so two agents do not share brain state and corrupt each other's context.
- For tests, an ephemeral temp directory keeps runs isolated and reproducible.
- This is separate from conversation persistence (the message history you serialize yourself); see [persistence.md](persistence.md).

## Related

- [../agent_configuration.md](../agent_configuration.md) -- the "Application Data Directory Override" section.
- [persistence.md](persistence.md) -- saving conversation history.
- Back to the skill: [../../SKILL.md](../../SKILL.md).
