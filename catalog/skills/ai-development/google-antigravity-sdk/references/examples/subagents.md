# Example: Subagents

A main agent can spawn and orchestrate child agents in-process. Use this for tight-latency delegation where the child shares the parent's process and you want a single owner of the lifecycle.

## Code

```python
import asyncio
from google.antigravity import Agent, LocalAgentConfig


async def main() -> None:
    researcher_cfg = LocalAgentConfig(
        model="gemini-3.5-flash",
        system="You gather facts and return them as a short bulleted list. You do not write prose.",
    )
    writer_cfg = LocalAgentConfig(
        model="gemini-3.5-flash",
        system="You turn bulleted findings into a one-paragraph summary.",
    )

    async with Agent(researcher_cfg) as researcher, Agent(writer_cfg) as writer:
        findings = await researcher.chat("List three facts about the Antigravity backend.")
        summary = await writer.chat(["Summarize these findings:", findings.text])
        print(summary.text)


if __name__ == "__main__":
    asyncio.run(main())
```

## What to notice

- Each subagent is a full `Agent` with its own config, persona, and policy. Give each the narrowest persona and tool set its role needs.
- Nesting `async with` blocks ties every subagent's lifecycle to the enclosing scope; all connections are torn down on exit.
- This is in-process spawning. For process-level isolation, per-agent provider routing, or durable multi-agent workflows, use the orchestration skills instead.

## In-process vs. process-level

- **In-process (this example)**: low latency, shared process, simplest to reason about. Best for short delegations.
- **Process-level**: stronger isolation, independent failure domains, per-agent routing. Covered by `orchestration/multi-agent-coordinator`, `temporal-orchestration`, and `cross-model-orchestrator`.

## Related

- The `orchestration/multi-agent-coordinator` skill's `sdk-subagents.md` reference -- when to pick each shape.
- Back to the skill: [../../SKILL.md](../../SKILL.md).
