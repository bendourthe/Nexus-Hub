# Agent Configuration

The agent is configured with a `LocalAgentConfig` object passed to `Agent(config)`. This document covers the configuration surface and the defaults that apply when a field is omitted.

## LocalAgentConfig fields

The configuration carries, at minimum:

- The model identifier.
- The system persona (the agent's standing instructions).
- The application data directory.
- The connection strategy.
- Optionally: the tool-call policy, the lifecycle hooks, and the set of registered tools (these can also be attached to the agent after construction).

```python
from google.antigravity import Agent, LocalAgentConfig

config = LocalAgentConfig(
    model="gemini-3.5-flash",
    system="You are a careful repository assistant. Prefer reading over writing.",
)

async with Agent(config) as agent:
    ...
```

## Default model

The Google Antigravity SDK's default model is `gemini-3.5-flash`. If you do not set `model` on the config, the agent runs against `gemini-3.5-flash`. Set it explicitly when you need a different Gemini model tier; pin the value in your project so a backend default change does not silently move your agent to a different model.

## System persona

The `system` field is the agent's standing instruction set. Keep it narrow and specific: state the agent's scope, the tools it should prefer, the output format it should produce, and the constraints it must not cross. A precise persona materially reduces the rate at which the model attempts disallowed tool calls. See [examples/persona_config.md](examples/persona_config.md) for a worked persona.

## Application Data Directory Override

The agent persists working artifacts (session brain state, cached context) under an application data directory. The default location is `~/.gemini/antigravity/brain/`. Override it when you need per-project isolation, an ephemeral directory for tests, or a path on a faster disk:

```python
config = LocalAgentConfig(
    model="gemini-3.5-flash",
    app_data_dir="/srv/agents/project-x/brain",
)
```

When the override points at a directory that does not exist, the SDK creates it. Use a dedicated directory per logical agent so two agents do not share brain state. See [examples/app_data_dir_override.md](examples/app_data_dir_override.md) for the full pattern and [examples/persistence.md](examples/persistence.md) for how the directory relates to conversation persistence.

## Connection strategy

The `ConnectionStrategy` selects how the agent reaches the backend and how it bridges tools. The default strategy runs the local harness that hosts the agentic loop and the MCP bridge. You set the strategy on the config; the Agent layer manages its lifecycle inside the async context manager (see [architecture.md](architecture.md)).

## Defaults summary

| Field | Default when omitted |
|---|---|
| `model` | `gemini-3.5-flash` |
| `app_data_dir` | `~/.gemini/antigravity/brain/` |
| tool-call policy | deny `run_command`, allow other tools (see [safety_policies.md](safety_policies.md)) |
| connection strategy | local harness with MCP bridge |

## Related

- [architecture.md](architecture.md) -- where configuration sits in the three-layer model.
- [safety_policies.md](safety_policies.md) -- the default policy and how to change it.
- [examples/hello_world.md](examples/hello_world.md) -- the minimal config in context.
- Back to the skill: [../SKILL.md](../SKILL.md).
