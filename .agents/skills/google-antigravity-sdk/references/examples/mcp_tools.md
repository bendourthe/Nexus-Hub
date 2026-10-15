# Example: MCP Tools

Connect an MCP server to an agent so its tools join the agent's tool surface. This example uses a stdio server launched as a subprocess.

## Code

```python
import asyncio
from google.antigravity import Agent, LocalAgentConfig
from google.antigravity.mcp import McpStdioServer


async def main() -> None:
    filesystem = McpStdioServer(
        name="filesystem",
        command="npx",
        args=["-y", "@modelcontextprotocol/server-filesystem", "/workspace"],
    )

    config = LocalAgentConfig(
        model="gemini-3.5-flash",
        system="You answer questions about files under /workspace. Read only; never write.",
        mcp_servers=[filesystem],
    )

    async with Agent(config) as agent:
        reply = await agent.chat("How many markdown files are under /workspace/docs?")
        print(reply.text)


if __name__ == "__main__":
    asyncio.run(main())
```

## What to notice

- The stdio server is launched on context enter and terminated on exit; its lifetime equals the agent's.
- The MCP server's tools are gated by the same policy as built-in and custom tools. This filesystem server can write; if you only want reads, deny its write tool in the policy.
- For a remote, already-running MCP service, use the SSE transport instead of stdio (see [../mcp_integration.md](../mcp_integration.md)).

## Related

- [../mcp_integration.md](../mcp_integration.md) -- stdio vs. SSE and registration details.
- [../safety_policies.md](../safety_policies.md) -- gating MCP tool calls.
- The `mcp-builder` skill -- authoring your own MCP server.
- Back to the skill: [../../SKILL.md](../../SKILL.md).
