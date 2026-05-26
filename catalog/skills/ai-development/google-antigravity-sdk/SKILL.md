---
name: google-antigravity-sdk
description: Design, implement, and debug autonomous AI agents using the Google Antigravity SDK -- the async agent loop, declarative tool-call policies, lifecycle hooks, MCP integration, multimodal ingestion, triggers, subagents, and Pydantic structured output. Make sure to use this skill whenever the user mentions the Google Antigravity SDK, AGY SDK, antigravity SDK, a Gemini agent loop, an antigravity agent, LocalAgentConfig, Conversation, or ConnectionStrategy, even if they do not say the word "agent" explicitly. SKIP, do NOT use for, a standalone Gemini API client with no agent loop (use multi-provider-ai or claude-api instead), one-off Gemini text-completion calls, or Antigravity CLI install / configuration work (that is owned by the Antigravity20Integration installer path, not this skill).
summary_l0: "Build autonomous AI agents with the Google Antigravity SDK -- async agent loop, hooks, policies, MCP"
overview_l1: "Use this skill to build autonomous agents on the Google Antigravity backend (Gemini models) with the Python Antigravity SDK. It covers the SDK's three-layer architecture (Agent owns the lifecycle and configuration, Conversation manages turn state and message history, Connection handles the backend transport and MCP bridging), its async-first API (async with Agent(config) as agent), and the operational surface around it: a declarative tool-call policy system with deterministic priority resolution and fail-closed predicates, lifecycle hooks for pre/post turn and pre/post tool execution and error recovery, MCP integration over stdio and SSE transports, multimodal input ingestion (images, PDFs, audio, in-memory bytes), background-task triggers, subagent spawning, and Pydantic-schema structured output. The expected output is working SDK agent code plus the configuration, policy, and observability scaffolding to run it safely. Trigger phrases: Google Antigravity SDK, AGY SDK, antigravity agent, Gemini agent loop, LocalAgentConfig, Conversation, ConnectionStrategy."
---

# Google Antigravity SDK

Patterns for building autonomous AI agents with the Google Antigravity SDK, the official Python client for the Antigravity backend (Gemini models). The skill covers the full operational stack: the async agent lifecycle, configuration, the declarative tool-call policy system, lifecycle hooks, MCP integration, multimodal ingestion, triggers, subagents, and structured output. It teaches you to install the SDK in your own project (`pip install google-antigravity`) and wire it up correctly; Nexus-Hub does not run the SDK or ship its runtime.

## When to Use This Skill

Use this skill for:

- Building an autonomous agent on the Antigravity backend with the async `Agent` / `Conversation` / `Connection` loop.
- Configuring an agent: model selection, system persona, application data directory, `LocalAgentConfig`, `ConnectionStrategy`.
- Authoring a declarative tool-call policy (allow / deny / ask) with predicate functions and understanding the resolution order.
- Adding lifecycle hooks (pre/post turn, pre/post tool execution, on-error) for audit logging, retries, persona shifts, or cost caps.
- Connecting MCP servers to an agent over stdio or SSE.
- Feeding multimodal inputs (images, PDFs, audio, raw bytes) into an agent turn.
- Scheduling background triggers, spawning subagents, or constraining output to a Pydantic schema.

**Trigger phrases**: "Google Antigravity SDK", "AGY SDK", "antigravity SDK", "Gemini agent loop", "antigravity agent", "LocalAgentConfig", "Conversation", "ConnectionStrategy".

**When NOT to use this skill**:

- **Standalone Gemini API client with no agent loop** -- if the user only wants to call a Gemini model for a completion or chat turn without the agent lifecycle, policies, or tools, use `multi-provider-ai` (provider routing) or `claude-api` (Anthropic-side equivalents) instead.
- **One-off Gemini text-completion calls** -- a single prompt-in / text-out call does not need the agent runtime; do not pull in the SDK for it.
- **Antigravity CLI install or configuration** -- installing the Antigravity CLI, writing its instruction files, or wiring its workflows is owned by the `Antigravity20Integration` installer path (`scripts/lib/integrations/antigravity.py`), not by this skill.

## Installation & Setup

Install the SDK into the user's own project:

```bash
pip install google-antigravity
```

Set the Gemini API key the SDK reads at runtime. Obtain a key from the Google AI Studio key page (https://aistudio.google.com/app/api-keys):

```bash
export GEMINI_API_KEY="your-key-here"
```

The SDK reaches the Gemini API at the user's runtime when their agent runs. Nexus-Hub never executes the SDK and never transmits anything; this skill teaches the user to install and configure it in their own project. The key is never stored by Nexus-Hub.

See [references/agent_configuration.md](references/agent_configuration.md) for the full configuration surface and [references/error_handling.md](references/error_handling.md) for the failure modes a missing or invalid key produces.

## Architecture

The SDK is organized in three layers. Most agent code touches only the `Agent` layer; the lower layers matter when you customize transport or persist conversation state.

| Layer | Responsibility | Key types |
|---|---|---|
| Agent | Top-level entry point. Owns the agent configuration, the tool-call policy, the lifecycle hooks, and the async context-manager lifecycle (`async with Agent(config) as agent`). | `Agent`, `LocalAgentConfig` |
| Conversation | Manages turn state and message history within a session, accepts multimodal inputs, and carries the structured-output contract for a turn. | `Conversation` |
| Connection | Establishes and maintains the transport to the Antigravity backend, bridges MCP servers (stdio + SSE), and routes tool calls. | `ConnectionStrategy` |

The full layer walkthrough, including how a turn flows down through the layers and back, is in [references/architecture.md](references/architecture.md).

## Instructions

Read the reference doc that matches the task, then the matching example for a concrete walkthrough. Every file below is part of this skill's bundle.

### Reference docs (concepts)

| Topic | Reference | Read when |
|---|---|---|
| Three-layer model, turn flow | [references/architecture.md](references/architecture.md) | You need the mental model before writing any agent code. |
| Model, persona, data dir, `LocalAgentConfig` | [references/agent_configuration.md](references/agent_configuration.md) | Configuring an agent or overriding defaults. |
| Connecting MCP servers (stdio + SSE) | [references/mcp_integration.md](references/mcp_integration.md) | Giving an agent access to external tools. |
| Declarative policy + resolution order | [references/safety_policies.md](references/safety_policies.md) | Controlling which tool calls are allowed, denied, or confirmed. |
| Failure modes and recovery | [references/error_handling.md](references/error_handling.md) | Handling transient errors, invalid keys, or tool failures. |
| Token usage and tracing hooks | [references/observability.md](references/observability.md) | Adding cost attribution or audit logging. |
| The agent's built-in tool surface | [references/built_in_tools.md](references/built_in_tools.md) | Knowing what the agent can do before you add custom tools. |

### Example walkthroughs (concrete)

| Goal | Example | 
|---|---|
| Minimal agent loop | [references/examples/hello_world.md](references/examples/hello_world.md) |
| Register a custom tool | [references/examples/custom_tool.md](references/examples/custom_tool.md) |
| Set the agent persona | [references/examples/persona_config.md](references/examples/persona_config.md) |
| Send images / PDFs / audio | [references/examples/multimodal.md](references/examples/multimodal.md) |
| Spawn and orchestrate subagents | [references/examples/subagents.md](references/examples/subagents.md) |
| Connect MCP tools | [references/examples/mcp_tools.md](references/examples/mcp_tools.md) |
| Push messages on an interval | [references/examples/periodic_trigger.md](references/examples/periodic_trigger.md) |
| Add lifecycle hooks | [references/examples/hooks.md](references/examples/hooks.md) |
| Persist conversation state | [references/examples/persistence.md](references/examples/persistence.md) |
| Override the data directory | [references/examples/app_data_dir_override.md](references/examples/app_data_dir_override.md) |
| Constrain output to a schema | [references/examples/structured_output.md](references/examples/structured_output.md) |
| Bundle agent skills | [references/examples/agent_skills.md](references/examples/agent_skills.md) |

### Standard build sequence

1. Install the SDK and set `GEMINI_API_KEY` (see Installation & Setup above).
2. Read [references/architecture.md](references/architecture.md) for the three-layer model.
3. Configure the agent per [references/agent_configuration.md](references/agent_configuration.md); start from [references/examples/hello_world.md](references/examples/hello_world.md).
4. Define a tool-call policy per [references/safety_policies.md](references/safety_policies.md) before granting any tool that mutates state. Start denying `run_command` and widen deliberately.
5. Add only the tools the agent needs: built-ins ([references/built_in_tools.md](references/built_in_tools.md)), custom tools ([references/examples/custom_tool.md](references/examples/custom_tool.md)), or MCP servers ([references/mcp_integration.md](references/mcp_integration.md)).
6. Add hooks for observability and cost control ([references/observability.md](references/observability.md), [references/examples/hooks.md](references/examples/hooks.md)).
7. Layer advanced capabilities as needed: multimodal, triggers, subagents, structured output.

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "The user just wants a Gemini call, I will skip the agent loop." | If there are no tools, no policy, and no multi-turn state, that is correct -- use `multi-provider-ai` instead. But the moment a tool can run a command or mutate a file, the policy layer in [references/safety_policies.md](references/safety_policies.md) is the difference between a safe agent and one that runs `rm -rf` because a predicate raised an exception and was treated as allow. Do not hand-roll an agent loop to dodge this skill. |
| "This agent is internal, I do not need a tool-call policy." | The SDK default policy denies `run_command` for a reason: an agent with an open `run_command` and a confused model is a remote code execution path. The resolution order (Specific Deny > Specific Ask > Specific Allow > Wildcard Deny > Wildcard Ask > Wildcard Allow) and fail-closed predicates exist so an internal agent fails safe, not open. |
| "Hooks are optional polish, I will add them later." | Without `on_tool_call_pre` / `on_turn_end` hooks you have no audit trail and no cost cap. An autonomous loop with no cost cap can drain an API budget in one runaway session. Wire the observability hooks ([references/observability.md](references/observability.md)) on the first iteration, not the last. |
| "I will copy the SDK example code verbatim from the upstream repo." | Match the documented async API surface (`async with Agent(config) as agent`, `agent.chat(...)`), but verify against the SDK version you installed -- this is alpha software and the surface can shift between releases. Pin the SDK version in your project. |

## Verification

- [ ] The skill installs via the standard Nexus-Hub installer and lands at `catalog/skills/ai-development/google-antigravity-sdk/` in the target tree.
- [ ] Every reference and example link in the routing tables above resolves to a file that exists under `references/` or `references/examples/`.
- [ ] `python scripts/validate_skills.py --bundles-only` reports zero orphan-bundle warnings for this skill folder.
- [ ] A manual trigger test confirms the three SKIP cases (standalone Gemini call, one-off completion, Antigravity CLI install) are routed away from this skill.
- [ ] The agent code a user writes from this skill sets `GEMINI_API_KEY` from their own environment and never hardcodes a key.
- [ ] The agent defines a tool-call policy before granting any state-mutating tool.

## Related Skills

- `claude-agent-sdk` -- the Anthropic-side equivalent (Claude Agent SDK in TypeScript); use it when building on Claude instead of Gemini.
- `mcp-builder` -- build the MCP servers an Antigravity agent consumes (this skill covers the consumer side; `mcp-builder` covers the author side).
- `ai-development/ai-agent-development` -- general agent architecture patterns (planning loops, memory) independent of any one SDK; the canonical home for the agent lifecycle-hook pattern ([references/lifecycle-hooks.md](../ai-agent-development/references/lifecycle-hooks.md)) and the multimodal-ingestion pattern ([references/multimodal-ingestion.md](../ai-agent-development/references/multimodal-ingestion.md)) this skill implements.
- `security/authentication-patterns` -- declarative tool-call authorization patterns; the canonical home for the policy resolution-order doctrine ([references/agent-policy-resolution.md](../../security/authentication-patterns/references/agent-policy-resolution.md)) that this skill's [safety_policies.md](references/safety_policies.md) implements concretely.
- `multi-provider-ai` -- provider routing for standalone model calls without an agent loop (one of the SKIP destinations above).
