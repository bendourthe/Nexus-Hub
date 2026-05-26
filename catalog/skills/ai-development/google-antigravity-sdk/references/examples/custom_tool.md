# Example: Custom Tool

Register one of your own functions as a tool the agent can call. The model decides when to invoke it; the tool-call policy decides whether it is allowed.

## Code

```python
import asyncio
from google.antigravity import Agent, LocalAgentConfig, tool


@tool
def get_weather(city: str) -> str:
    """Return the current weather for a city. Use when the user asks about weather."""
    # Your real implementation would call a weather API here.
    return f"It is 18C and clear in {city}."


async def main() -> None:
    config = LocalAgentConfig(
        model="gemini-3.5-flash",
        system="You are a travel assistant. Use tools to answer factual questions.",
        tools=[get_weather],
    )

    async with Agent(config) as agent:
        reply = await agent.chat("Should I bring a coat to Paris today?")
        print(reply.text)


if __name__ == "__main__":
    asyncio.run(main())
```

## What to notice

- The tool's docstring is part of its contract: it tells the model what the tool does and when to use it. Write it as carefully as the system persona.
- Type-annotate every parameter; the SDK derives the tool's input schema from the annotations.
- A read-only tool like this is safe under any policy. A tool that mutates state must be reasoned about against the policy before you allow it (see [../safety_policies.md](../safety_policies.md)).

## Next steps

- Gate a state-mutating tool: [../safety_policies.md](../safety_policies.md).
- Bring in tools from an external server instead of writing them: [mcp_tools.md](mcp_tools.md).

## Related

- [../built_in_tools.md](../built_in_tools.md) -- the tools the agent already has.
- Back to the skill: [../../SKILL.md](../../SKILL.md).
