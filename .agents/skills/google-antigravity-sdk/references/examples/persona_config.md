# Example: Persona Configuration

A precise system persona is the cheapest, highest-leverage control you have over an agent. It sets scope, preferred tools, output format, and hard constraints, which reduces the rate at which the model attempts disallowed actions.

## Code

```python
import asyncio
from google.antigravity import Agent, LocalAgentConfig

PERSONA = """You are a repository review assistant.

SCOPE: You read code and summarize findings. You do not modify files or run commands.

TOOLS: Prefer read_file and list_directory. Never request run_command.

OUTPUT: Return findings as a short bulleted list, most important first.

CONSTRAINTS:
1. Only read files under the current repository.
2. If asked to change code, explain the change but do not apply it.
3. Flag anything you are unsure about rather than guessing.
"""


async def main() -> None:
    config = LocalAgentConfig(model="gemini-3.5-flash", system=PERSONA)
    async with Agent(config) as agent:
        reply = await agent.chat("Review error handling in src/server.py.")
        print(reply.text)


if __name__ == "__main__":
    asyncio.run(main())
```

## What to notice

- The persona follows a repeatable shape: Identity, Scope, Tools, Output, Constraints. This shape is easy for the model to honor and easy for you to audit.
- The persona and the tool-call policy reinforce each other. The persona says "never request run_command"; the default policy denies it anyway. Belt and suspenders.
- Keep the persona narrow. A general-purpose persona produces a general-purpose (and less reliable) agent.

## Related

- [../agent_configuration.md](../agent_configuration.md) -- the `system` field.
- [../safety_policies.md](../safety_policies.md) -- the policy that backs the persona.
- Back to the skill: [../../SKILL.md](../../SKILL.md).
