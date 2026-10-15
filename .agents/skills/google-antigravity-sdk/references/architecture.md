# Architecture: Agent / Conversation / Connection

The Google Antigravity SDK is organized in three layers. Understanding which layer owns what is the fastest way to know where a given concern (configuration, message state, transport) belongs. Most application code touches only the Agent layer; you reach into the lower layers when you customize transport or persist conversation state across runs.

## The three layers

### Agent (top layer)

The `Agent` is the entry point and the object your application holds. It owns:

- The agent configuration (`LocalAgentConfig`): which model to use, the system persona, the application data directory, and the connection strategy.
- The tool-call policy: the declarative allow / deny / ask rules evaluated before every tool call.
- The lifecycle hooks: callbacks fired around turns and tool calls.
- The async lifecycle: the agent is an async context manager, so resources (the connection, the local harness, MCP server subprocesses) are acquired on enter and released on exit.

The canonical shape is:

```python
async with Agent(config) as agent:
    reply = await agent.chat("Summarize the open issues in this repo.")
    print(reply.text)
```

Entering the context establishes the connection and starts any MCP servers; leaving it tears them down deterministically, even if the body raised.

### Conversation (middle layer)

A `Conversation` represents a single multi-turn session. It owns:

- The ordered message history (user, assistant, and tool messages).
- The current turn's inputs, including multimodal content (images, PDFs, audio, raw bytes).
- The structured-output contract for a turn, when the caller constrains output to a schema.

One agent can drive multiple conversations; each conversation is an independent thread of state. When you persist or restore agent state, the conversation history is the payload that matters.

### Connection (bottom layer)

The `Connection`, selected by a `ConnectionStrategy`, owns the transport to the Antigravity backend and the bridge to external tools:

- It maintains the channel to the backend that runs the agentic loop against the configured Gemini model.
- It bridges MCP servers over stdio and SSE so their tools appear in the agent's tool surface.
- It routes tool-call requests from the model out to the right tool (built-in, custom, or MCP) and routes results back.

Application code rarely instantiates a `Connection` directly; it selects a `ConnectionStrategy` in the config and lets the Agent layer manage the lifecycle.

## How a turn flows

A single `agent.chat(...)` call flows down and back up the three layers:

1. The Agent layer appends the user input (and any multimodal content) to the Conversation.
2. The Conversation hands the assembled turn to the Connection.
3. The Connection sends the turn to the backend, which runs the model. The model may request one or more tool calls.
4. For each requested tool call, the Agent layer evaluates the tool-call policy. If the policy denies, the call is blocked and the denial is surfaced back to the model. If it asks, the configured confirmation path runs. If it allows, the Connection dispatches the call.
5. Tool results return up through the Connection into the Conversation, and the model continues until it produces a final answer.
6. The final answer is appended to the Conversation and returned to the caller.

Lifecycle hooks fire at the boundaries of this flow (turn start/end, tool-call pre/post, on-error), which is what makes audit logging, retries, and cost caps possible without modifying the loop itself.

## Where state lives

- Configuration lives on the Agent and does not change during a run.
- Message history and turn inputs live on the Conversation; this is what you serialize to persist a session.
- Transport and tool connections live on the Connection and are recreated each time you re-enter the agent context.

## Related

- [agent_configuration.md](agent_configuration.md) -- the `LocalAgentConfig` fields the Agent layer owns.
- [safety_policies.md](safety_policies.md) -- the policy the Agent layer evaluates in step 4 above.
- [mcp_integration.md](mcp_integration.md) -- how the Connection layer bridges MCP tools.
- Back to the skill: [../SKILL.md](../SKILL.md).
