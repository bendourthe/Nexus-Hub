# MCP Integration (consumer side)

This document covers how an Antigravity agent **consumes** MCP servers as tool providers. It is the consumer side; if you need to **author** an MCP server, use the `mcp-builder` skill instead.

The SDK bridges MCP servers through the Connection layer so their tools appear in the agent's tool surface alongside built-in and custom tools. Two transports are supported: stdio and SSE.

## stdio transport

A stdio MCP server is launched as a subprocess; the agent communicates with it over the process's standard input and output. This is the right choice for local tools (filesystem access, a local database, a project-specific script). Declare it with the stdio server type:

```python
from google.antigravity.mcp import McpStdioServer

filesystem = McpStdioServer(
    name="filesystem",
    command="npx",
    args=["-y", "@modelcontextprotocol/server-filesystem", "/workspace"],
)
```

The agent starts the subprocess when it enters its async context and terminates it on exit, so MCP server lifetimes are tied to the agent lifetime.

## SSE transport

An SSE (server-sent events) MCP server is reached over HTTP. Use it for a remote or already-running MCP service that you connect to by URL rather than launching as a subprocess. The agent opens the event stream on context enter and closes it on exit.

Choose stdio for tools you launch locally; choose SSE for tools that run as a separate, network-reachable service.

## Registering servers with an agent

Attach the MCP servers to the agent configuration (or to the agent after construction). On context enter, the Connection layer starts or connects each server, discovers its tools, and merges them into the tool surface the model sees:

```python
config = LocalAgentConfig(
    model="gemini-3.5-flash",
    mcp_servers=[filesystem],
)

async with Agent(config) as agent:
    reply = await agent.chat("List the markdown files under /workspace/docs.")
```

See [examples/mcp_tools.md](examples/mcp_tools.md) for an end-to-end walkthrough.

## Tool namespacing and policy

MCP tools are subject to the same tool-call policy as built-in and custom tools. When two servers expose a tool with the same name, namespace them (by server name) so policy rules can target a specific tool unambiguously. Treat any MCP tool that can mutate state (write files, run commands, call external APIs) the same way you treat `run_command`: deny or ask by default, and widen the policy only for the specific tool you intend to allow. See [safety_policies.md](safety_policies.md).

## Failure handling

If an MCP server fails to start (bad command, missing binary) or disconnects mid-session, the agent surfaces the failure as a tool error rather than crashing the loop. Decide per tool whether a failure should be retried, routed back to the model as a recoverable error, or treated as fatal. See [error_handling.md](error_handling.md).

## Related

- [architecture.md](architecture.md) -- the Connection layer that owns the MCP bridge.
- [safety_policies.md](safety_policies.md) -- gating MCP tool calls.
- [examples/mcp_tools.md](examples/mcp_tools.md) -- connecting an MCP server step by step.
- `mcp-builder` skill -- authoring the MCP servers consumed here.
- Back to the skill: [../SKILL.md](../SKILL.md).
