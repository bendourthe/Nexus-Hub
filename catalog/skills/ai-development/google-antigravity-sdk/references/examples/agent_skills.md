# Example: Agent Skills

The SDK can load bundled "skills" -- packaged instructions and resources that extend what an agent knows how to do, in the same Agent Skill format Nexus-Hub uses. This lets you give an agent a curated capability without bloating its system persona.

## Code

```python
import asyncio
from google.antigravity import Agent, LocalAgentConfig


async def main() -> None:
    config = LocalAgentConfig(
        model="gemini-3.5-flash",
        skills=["./skills/invoice-review", "./skills/release-notes"],
    )
    async with Agent(config) as agent:
        print((await agent.chat("Review the attached invoice for anomalies.")).text)


if __name__ == "__main__":
    asyncio.run(main())
```

## What to notice

- A skill is a folder with an instruction file plus optional bundled references and assets. The agent loads the skill's guidance when the task matches, rather than carrying it in the persona at all times.
- This is progressive disclosure for the agent you are building, the same three-tier loading idea Nexus-Hub applies to its own catalog skills.
- Keep each skill narrow and give it a precise trigger description, exactly as Nexus-Hub does, so the agent loads the right one at the right time.

## Relationship to Nexus-Hub

Nexus-Hub is itself a catalog of Agent Skills distributed to AI assistants. This example is the mirror image: loading skills into an agent you build with the SDK. The format and the loading discipline are the same; only the consumer differs.

## Related

- [../architecture.md](../architecture.md) -- where skills sit relative to the agent config.
- [persona_config.md](persona_config.md) -- the persona that a loaded skill complements.
- Back to the skill: [../../SKILL.md](../../SKILL.md).
