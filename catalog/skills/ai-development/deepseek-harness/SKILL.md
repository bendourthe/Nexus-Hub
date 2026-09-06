---
name: deepseek-harness
description: Build, extend, and operate coding agents on DeepSeek Harness (dsh), the MIT-licensed TypeScript agent runtime from DeepSeek AI where everything is a Cordis plugin. Make sure to use this skill whenever the user mentions "deepseek harness", "dsh", "deepseek agent framework", "dsh profile", "dsh bundle", "dsh headless", "cordis plugin agent", a dsh patch layer, a dsh plugin tree, or dump-config, and whenever they ask how to register a tool on ctx.tools, an LLM adapter on ctx.llm, a sandbox backend on ctx.sandbox, or an MCP server into dsh, how to inspect what a dsh profile or bundle composes, why a dsh patch layer is not taking effect, or how to run dsh headless for one-shot runs, even when they do not name the framework explicitly. SKIP, do NOT use for, any other vendor's agent runtime or harness, each of which has its own dedicated skill; calling the DeepSeek model API directly with no harness involved (that is provider routing); or runtime-agnostic agent-architecture questions where no framework has been chosen yet.
summary_l0: "Build agents on DeepSeek Harness with Cordis plugin composition, profiles, and capability seams"
overview_l1: "DeepSeek Harness (dsh) is an MIT-licensed TypeScript agent runtime from DeepSeek AI, built on the Cordis plugin/DI layer, in developer preview with compatibility-breaking changes expected. Its organizing idea is that everything is a plugin: the model adapter, the tool registry, the session log, and the agent loop itself are all replaceable from configuration, with no privileged core to patch. This skill covers install and quickstart, the profile-and-bundle composition model inspected with --dump-config, the step/turn agent-loop vocabulary and its one inbox, the ctx.tools / ctx.llm / ctx.sandbox capability seams, fail-closed sandbox modes, the MCP client bridge and its server-qualified tool names, headless and ACP and JSON-RPC entry modes, the Python SDK, and skills discovery. Use it to extend dsh correctly rather than patching around it."
---

# DeepSeek Harness (dsh)

DeepSeek Harness is an open-source agent harness from DeepSeek AI, licensed MIT and distributed as `@deepseek-ai/dsh`. It is powered by [Cordis](https://github.com/cordiverse/cordis), a plugin/DI layer in which plugins contribute services, typed events, and reversible effects to a shared context.

The framework's whole design follows from one sentence in its architecture doc: **there is no privileged core to patch**. You extend dsh by mounting a plugin beside the others, never by forking a center. Two consequences drive almost every instruction below: registrations are *effects* that unwind when their plugin unloads, and anything the model can see must be reconstructable from the session log.

> **Developer preview.** dsh is iterating rapidly and its own README states that there will be compatibility-breaking changes. Pin a version, read the changelog before upgrading, and verify any API shape in the installed version rather than assuming this skill's vocabulary is current.

## When to Use This Skill

Use it when:

- Building a coding agent, automation, or IDE integration on top of dsh.
- Adding a capability to a dsh deployment: a tool, an LLM provider adapter, a shell or filesystem or sandbox backend, a human command, background jobs, or a Chat node.
- Composing or debugging a dsh profile: which bundles stack, which patch layer won, why a plugin row is or is not present.
- Wiring external MCP servers into a dsh agent, or driving dsh from Python, ACP, or a headless one-shot run.
- Deciding *where* a new behavior belongs, which is the question dsh's extension-point map exists to answer.

**When NOT to use this skill:**

- **Calling the DeepSeek API directly** with no harness involved. That is a provider-routing question: use `multi-provider-ai`.
- **Claude-native agents** on the Claude Agent SDK: use `claude-agent-sdk`.
- **Google Antigravity** agents: use `google-antigravity-sdk`.
- **Runtime-agnostic agent architecture** (what a planning loop is, how memory should work, when to use multi-agent): use `ai-agent-development`. Come back here once the runtime is chosen.
- **Building an MCP server** rather than consuming one from dsh: use `mcp-builder`.

## Instructions

### 1. Install and run

Install Node.js, then start the Web UI, which serves at `http://127.0.0.1:3080` by default:

```sh
npx @deepseek-ai/dsh web
```

For a one-shot, non-interactive run with no server and no listening port:

```sh
dsh --profile headless "summarize the failing tests in this repo"
```

To work from a checkout instead:

```sh
git clone https://github.com/deepseek-ai/deepseek-harness.git
cd deepseek-harness
pnpm install
pnpm run build
pnpm dsh web
```

The Harness home resolves to `$DSH_HOME`, falling back to `~/.dsh`. Profiles live under `$DSH_HOME/profiles/<name>`.

### 2. Understand profile and bundle composition

A running `dsh` is a plugin tree composed at boot from ordered layers. Two nouns carry the model:

- A **profile** is a named composition stored in the Harness home. It is a directory holding a `package.json` whose `dsh.profile.bundles` field lists, in order, the bundles it stacks, plus any out-of-tree plugin `dependencies` and the user's own `cordis.patch.yml`. `web` and `headless` ship as auto-initializing templates.
- A **bundle** is a distribution format for Cordis config rows and the code they mount. An npm package declares itself one with `"dsh": { "bundle": { "patch": "./cordis.patch.yml" } }`.

The shipped bundles layer like this:

| Bundle | Adds |
|---|---|
| `dsh-base` | First layer of every profile: model adapters, tools, persistence, sandbox and approval policy, settings, credentials, telemetry |
| `dsh-web-app` | The browser application |
| `dsh-headless` | A one-shot runner with no server at all |

Layers apply to an empty entry list in a fixed order: each bundle in the profile's listed order, then the profile's `cordis.patch.yml`, then the home-level one, then any `--patch` overlay. A patch targets a row **by id** and replaces that row's whole config, or inserts new rows.

Never guess what booted. Print the actual tree:

```sh
dsh --profile web --dump-config
```

Any row it prints can be replaced by a patch of your own. Because composition, flag derivation, and config dumps all run through the same `applyEntryPatches` path, the dump cannot drift from what actually boots. Treat a surprising `--dump-config` as the truth and your mental model as the bug.

### 3. Learn the agent-loop vocabulary

Two words carry precise meanings, and using them loosely is the most common source of confusion when reading dsh code:

- A **step** is one model request plus the tools it calls.
- A **turn** is zero or more steps. It opens before its first input is claimed and closes once nothing is owed.

The flow, condensed from the architecture doc:

```text
turn/start
  claim next-step input plus one queued message
  assemble prompt sections + tool schemas
  -> agent/pre-step                   reject | enter(messages)
     step/start
     append entered messages as user/message
     derive model history from the log
     agent/request -> llm/stream -> assistant/chunk* -> assistant/message
     tool/call* -> tools/pre-execute -> tools/execute -> tools/post-execute -> tool/result*
     step/end
  -> agent/turn-stopping
turn/end
```

Three rules follow:

1. **`turn/*`, `step/*`, `user/message`, `assistant/*`, and `tool/*` are durable session events.** The rest are live extension points.
2. **`agent/pre-step`, `agent/request`, `llm/stream`, and the three `tools/*` events are waterfalls** whose listeners must call `next()` to delegate. `agent/turn-stopping` is serial and has no `next()`. Forgetting `next()` in a waterfall silently halts the chain.
3. **A rejected or empty first claim still closes a durable turn that spent no step**, so the log records the attempt rather than losing it.

Input reaches the driver through **one inbox**. The unified `send` method exposes target and wakeup routing directly; the three named methods are fixed-preset aliases over it:

| Method | Meaning |
|---|---|
| `followup(message)` | Ordinary queued user input |
| `steer(message)` | Steering for the nearest step; an idle driver starts a turn. A rejected step leaves steering parked in the inbox until the next wake |
| `inject(message)` | Model-facing context that waits in the inbox until another message wakes the driver; it lands in the next admitted request |

`followup()` returns no handle. Its `MessageId` identifies durable inbox insertion, claim, and discard facts, not a later assistant output or turn ending. Do not treat it as a completion token.

**Model-visible means logged.** Anything reaching a model request must be reconstructable from the session log, and a runtime invariant asserts it. This is why adding a new model-visible input requires a new session event: extend `SessionEventMap` and render from the log. Smuggling context in by any other route is the one shortcut the runtime will actively catch.

### 4. Work with capability seams

A **seam** is a swappable capability with three roles: a *Service Definition* declaring the interface, a *Service Provider* implementing it, and a *Consumer* using it (commonly a model-facing tool). A package may combine roles, but one role alone is not a seam. Adding a capability means designing all three.

Core packages and their context keys:

| Package | Owns | `ctx` key |
|---|---|---|
| `core/session` | Append-only `SessionEvent` log and in-memory store | `ctx.sessions` |
| `core/system-prompt` | Prompt-section and tool-schema assembly | `ctx.systemPrompt` |
| `core/tools` | Scoped tool registry and guarded execution pipeline | `ctx.tools` |
| `core/agent` | The `Agent` interface, live registry, `agent/*` events | `ctx.agents` |
| `core/agent-loop` | Default driver implementing that interface | `ctx.agentLoop` |
| `llm/llm` | Message and stream vocabulary plus the adapter seam | `ctx.llm` |

Seams are why one provider swap changes the whole product: filesystem and subprocess providers share one execution world, so pointing them at a remote sandbox moves Bash, PTY, and LSP with them, with no provider forks.

For LLM providers, two adapters ship and both register on `ctx.llm`: `llm-deepseek` (direct DeepSeek) and `llm-pi-ai` (multi-provider via pi-ai). `llm-retry` (provider-scoped retry, listening on `agent/request-error`) and `token-meter` (replay-aware measurement) stay separate consumers rather than being folded into adapters.

Use this map to place new behavior. Attaching it anywhere else is the mistake the map exists to prevent:

| Goal | Mechanism |
|---|---|
| Add a model provider | Register its adapter on `ctx.llm` |
| Add a model-facing capability | Register on `ctx.tools`; its schema joins prompt assembly |
| Add shell execution | Register a `ctx.shell` backend; the local one spawns through `ctx.subprocess` |
| Add a human command | Register on `ctx.commands`; it dispatches without a model turn |
| Add background work | Register on `ctx.jobs`; `job_*` tools collect or stop it |
| Add filesystem access or policy | Register a `ctx.fs` provider or listen to `fs/*` events |
| Confine spawned processes | Use a `ctx.sandbox` backend; consumers wrap argv before spawning |
| Intercept a request, tool, or turn | Use its `agent/*` or `tools/*` event |
| Add model-facing context | Call `agent.inject()` |
| Add durable session state | Extend `SessionEventMap`; render and replay from the log |
| Scope a registration to one agent | Use that agent's `agent.ctx` |

### 5. Respect the fail-closed sandbox

`SandboxMode` governs **filesystem effects only**. Network and process visibility are outside this vocabulary, so do not reach for it as a network control.

| Mode | Effect |
|---|---|
| `read-only` | Backend denies writes; POSIX runners additionally grant the `/dev/null` sink their shells require |
| `workspace-write` | Permits writes under the workspace root and the backend's promised temp area |
| `danger-full-access` | Bypasses confinement entirely |

Only the first two can be sent to a provider. A `danger-full-access` consumer spawns its original argv and does not call `ctx.sandbox` at all.

`ctx.sandbox.confine(argv, policy)` returns a `ConfinedArgv` or throws `SandboxUnavailableError` with code `SANDBOX_UNAVAILABLE` when no usable backend exists. **Silent unconfined passthrough is never legal for a confined policy.** If you write a consumer, its failure path is to fail closed, never to shrug and spawn unwrapped.

Normal tool calls derive `workspaceRoot` from the calling session's immutable cwd. The root is canonicalized with filesystem semantics before lexical normalization, so a cwd containing `symlink/..` identifies the directory where a spawned process actually runs rather than where the path string suggests.

### 6. Bridge MCP servers

`mcp-client` connects to external MCP servers and registers their tools on `ctx.tools` under server-qualified names:

```text
mcp__<serverName>__<rawName>
```

The model sees `mcp__github__create_issue`, `mcp__web__search`, and so on, which is the same shape Claude Code and Codex use. Every MCP tool therefore has two names: the raw MCP name sent on the wire in `tools/call`, and the public registered name.

Public names are normalized to the DeepSeek function-name contract (64 characters, `[A-Za-z0-9_-]`). When replacement or truncation changes a name, a deterministic 12-hex-character hash of `(serverName, rawName)` is appended, so distinct tools never collapse into one name. Names are pure functions of `(serverName, rawName)`: connection order, re-syncs, and other servers never rename a tool. HMR hot-swaps a server on entry edit (disconnect plus reconnect, no process restart), and an unchanged `serverName` reproduces identical tool names.

Credentials come from the environment by reference rather than being inlined:

```yaml
env:
  GITHUB_TOKEN: !!js process.env.GITHUB_TOKEN
```

The stdio bridge merges a server's declared `env` on top of a **scrubbed** ambient environment, so a child MCP server does not inherit the parent's whole credential set by accident. Declare exactly the variables a server needs.

### 7. Choose an entry mode

| Mode | Use for |
|---|---|
| Web UI (`dsh web`) | Interactive human use; served at `127.0.0.1:3080` by default |
| Headless (`dsh --profile headless "task"`) | One-shot automation. No listening port. Writes the last non-empty assistant text to stdout and exits 0 on a completed final `turn/end`, else 1; a terminal `error` reason writes code and message to stderr, and successful runs keep stderr empty |
| ACP | Exposing harness agents to programmatic clients over the Agent Client Protocol. An interoperability transport, not a presentation layer |
| Python SDK | Driving dsh as a subprocess over newline-delimited JSON-RPC on stdio |

Headless has two limits worth knowing before you design around it: it accepts **one submitted task only** with no interactive follow-up surface, and `ctx.appExit` is launcher-owned, so booting the headless profile outside the `dsh` launcher fails loud at activation until the host provides the exit request.

For Python, install `deepseek-harness-sdk` (module `deepseek_harness`), which offers a high-level turns API plus a lower-level JSON-RPC client. It starts the matching bundled runtime (`deepseek-harness-runtime-bin`) unless the caller selects an explicit channel. Note the asymmetry: the client supplies default configuration, but the runtime itself always requires an explicit configuration.

### 8. Ship skills to a dsh agent

dsh discovers Markdown skills from ranked roots, lowest rank first:

| Rank | Source | Root |
|---|---|---|
| 100 | `project-dsh` | `<projectRoot>/.dsh/skills` |
| 200 | `project-agents` | `<projectRoot>/.agents/skills` |
| 300 | `custom` | `Config.customSkillDirs` |
| 400 | `user-dsh` | `<dshHome>/skills` |
| 500 | `user-agents` | `<agentsHome>/skills` |
| 600 | `bundled` | `Config.bundledSkillDir` when configured |

The project root is the nearest ancestor containing `.git`, falling back to the current cwd. Skill names are kebab-case (`^[a-z0-9]+(?:-[a-z0-9]+)*$`). The local provider accepts directory bundles (`<name>/SKILL.md`) and flat Markdown files (`<name>.md`).

Nested recursive discovery is **not supported**. A skill nested one level deeper than the provider expects is silently invisible, which is the single most common reason a skill "isn't loading".

Skills carry two independent invocation controls normalized into positive booleans on `SkillInvocationPolicy`, and the model session catalog renders only model-invocable `name` and `description`, never the body or the absolute file path.

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "I'll just patch the agent loop directly, it's faster than finding the right event." | There is no privileged core to patch, and a fork does not unwind. Registrations are effects that unload with their plugin; a direct edit leaks state across reload and HMR, and the next upgrade silently drops your change. Use the extension-point map in step 4. |
| "I'll pass this extra context straight into the model request instead of adding a session event." | A runtime invariant asserts that everything model-visible is reconstructable from the log. Your context vanishes on fork, resume, and replay, and the invariant will flag it. Extend `SessionEventMap` and render from the log. |
| "The sandbox has no backend here, so I'll spawn the argv unwrapped and log a warning." | Silent unconfined passthrough is never legal for a confined policy. `confine()` throwing `SANDBOX_UNAVAILABLE` is the contract working; degrading to unconfined turns a fail-closed guarantee into a fail-open one on exactly the machines where confinement was unavailable. |
| "I read the bundle's cordis.patch.yml, so I know what's running." | Four layers stack after it: later bundles, the profile patch, the home patch, and any `--patch` overlay, each able to replace a row's whole config by id. Only `--dump-config` shows what your machine boots. |
| "My listener didn't need to call next(), the chain still worked in my test." | `agent/pre-step`, `agent/request`, `llm/stream`, and the three `tools/*` events are waterfalls. Skipping `next()` halts delegation, so every downstream listener stops running. It "works" until a second plugin registers on the same event. |
| "I'll set read-only mode to stop the agent from reaching the network." | `SandboxMode` governs filesystem effects only; network and process visibility are explicitly outside the vocabulary. A `read-only` process can still open sockets. |
| "followup() returned a MessageId, so I can await that to know the turn finished." | That id identifies durable inbox insertion, claim, and discard facts, not assistant output or turn ending. Observe agent status or `whenIdle()` instead. |
| "My skill is in .agents/skills/team/reviewer/SKILL.md and it isn't loading, must be a bug." | Nested recursive discovery is not supported. The provider accepts `<name>/SKILL.md` or `<name>.md` at the root, one level only. |
| "It's a developer preview, so the API shape I remember is close enough." | The project's own README warns of compatibility-breaking changes. Verify against the installed version; a skill or doc is a starting point, not the contract. |

## Verification

- [ ] `npx @deepseek-ai/dsh web` starts and the UI is reachable at `http://127.0.0.1:3080` (or the configured address).
- [ ] `dsh --profile <name> --dump-config` prints the plugin tree, and every row you expect to have added or patched appears in it with the expected config.
- [ ] For a new capability, all three seam roles exist: a Service Definition, a Service Provider, and at least one Consumer.
- [ ] A sandbox probe reports a usable runner rather than `SANDBOX_UNAVAILABLE`, and any consumer you wrote fails closed when it does not.
- [ ] Every MCP server you configured appears with tools named `mcp__<serverName>__<rawName>`, and each server's `env` declares exactly the variables it needs (no inline credential literals).
- [ ] Any new model-visible input is backed by a `SessionEventMap` entry and survives a session reload or fork.
- [ ] Every waterfall listener you registered calls `next()`.
- [ ] `dsh --profile headless "<task>"` exits 0 with the final assistant text on stdout and empty stderr.
- [ ] Each skill you shipped resolves at a supported discovery root, one level deep, with a kebab-case name.

## Related Skills

- `claude-agent-sdk` - the equivalent skill for Claude-native agents; use it instead when the runtime is Anthropic's SDK.
- `google-antigravity-sdk` - the equivalent for Google Antigravity; same relationship.
- `ai-agent-development` - runtime-agnostic agent architecture (tool use, memory, planning loops); read it before choosing dsh, this skill after.
- `mcp-builder` - use when *building* the MCP server that step 6 consumes.
- `multi-provider-ai` - provider routing across Anthropic, Bedrock, Vertex, and OpenRouter; the right skill when there is no harness in the picture.
