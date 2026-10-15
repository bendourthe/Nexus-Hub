# Example: Persistence

A conversation's message history is the state worth persisting. Save it to resume a session later, across process restarts.

## Code

```python
import asyncio
import json
from pathlib import Path
from google.antigravity import Agent, LocalAgentConfig, Conversation

STATE = Path("session-state.json")


async def main() -> None:
    config = LocalAgentConfig(model="gemini-3.5-flash")

    async with Agent(config) as agent:
        # Restore prior history if it exists.
        if STATE.exists():
            conversation = Conversation.from_dict(json.loads(STATE.read_text()))
        else:
            conversation = Conversation()

        reply = await agent.chat("What did we decide last time?", conversation=conversation)
        print(reply.text)

        # Persist the updated history.
        STATE.write_text(json.dumps(conversation.to_dict()))


if __name__ == "__main__":
    asyncio.run(main())
```

## What to notice

- The `Conversation` carries the message history; serializing it (and restoring it) is what resumes a session. The `Connection` is recreated each run, so it is not part of the saved state.
- One agent can drive several conversations; persist each under its own key if you run more than one.
- The agent's working artifacts (brain state, caches) live under the application data directory, which is a separate concern from conversation history (see [app_data_dir_override.md](app_data_dir_override.md)).

## Related

- [../architecture.md](../architecture.md) -- the Conversation layer and where state lives.
- [app_data_dir_override.md](app_data_dir_override.md) -- the on-disk working directory.
- Back to the skill: [../../SKILL.md](../../SKILL.md).
