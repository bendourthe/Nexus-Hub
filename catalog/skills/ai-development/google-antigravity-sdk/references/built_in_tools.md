# Built-in Tools

Before adding custom tools or MCP servers, know what the agent can already do. The SDK ships a built-in tool surface that the model can invoke during a turn. This document describes the categories and how the default policy gates them.

## Tool categories

The built-in surface typically covers:

- **Command execution** -- running a shell command in the agent's environment. This is the highest-risk built-in and is denied by the default policy.
- **Filesystem access** -- reading and writing files within the agent's working area. Reads are low risk; writes mutate state and should be gated.
- **Workspace navigation** -- listing directories and inspecting the project structure.

The exact tool names and signatures are part of the SDK surface for the version you install; verify them against your installed version rather than assuming, since this is alpha software.

## How the default policy gates them

The default policy (`confirm_run_command()`, see [safety_policies.md](safety_policies.md)) denies `run_command` and allows the rest. So out of the box:

- The agent can read and navigate files.
- The agent cannot run shell commands until you widen the policy.

This is a deliberate safe default. When you do need command execution, add a specific allow (ideally with a predicate that constrains the command), rather than switching to `allow_all()`.

## Built-in vs. custom vs. MCP tools

The model sees a single merged tool surface; it does not distinguish where a tool came from. The three sources are:

- **Built-in** -- shipped with the SDK (this document).
- **Custom** -- tools you register from your own functions; see [examples/custom_tool.md](examples/custom_tool.md).
- **MCP** -- tools bridged from MCP servers; see [mcp_integration.md](mcp_integration.md).

All three are gated by the same tool-call policy, so reason about every tool, regardless of source, before allowing it.

## Choosing what to expose

Expose the minimum tool set the task needs. A research agent that only reads should not have command execution or write access in its policy at all. A narrower tool surface reduces both the attack surface and the rate at which a confused model attempts something disallowed. Pair the tool set with a precise persona ([agent_configuration.md](agent_configuration.md)) so the model's intent matches the tools you granted.

## Related

- [safety_policies.md](safety_policies.md) -- the policy that gates every built-in tool.
- [agent_configuration.md](agent_configuration.md) -- the persona that steers tool use.
- [examples/custom_tool.md](examples/custom_tool.md) -- adding a tool beyond the built-ins.
- [mcp_integration.md](mcp_integration.md) -- bridging external tools via MCP.
- Back to the skill: [../SKILL.md](../SKILL.md).
