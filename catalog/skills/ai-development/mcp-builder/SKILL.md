---
name: mcp-builder
description: "Build a local MCP (Model Context Protocol) server in Python (FastMCP) or TypeScript / Node (the official MCP SDK) - tool definitions, structured output, auth, transports, and registration into Claude Code, Cursor, Codex, Gemini, and OpenCode. Use whenever the user wants to \"build an MCP\", \"write an MCP server\", \"expose tools to the agent\", \"wrap an API as an MCP\", \"create a custom MCP\", \"MCP tool\", \"MCP transport\", \"register an MCP\", or asks how to integrate a service the agent can call as a tool. Bundles cross-platform scaffolding scripts (init-mcp-fastmcp.{sh,ps1} and init-mcp-ts.{sh,ps1}) so Windows / macOS / Linux all reach the same starter. SKIP: capabilities the agent's LLM can already do (use a skill instead - per the AGENTS.md MCP Registry Policy decision tree); third-party search-as-service / embeddings-as-service / scraping-as-service wrappers (categorically rejected by policy); user wants to CONSUME an existing MCP (this skill is for BUILDING one - to consume, edit settings.json directly)."
summary_l0: "Build local MCP servers (FastMCP Python or MCP SDK Node/TS) with cross-platform scaffolding scripts"
overview_l1: "This skill walks the agent through building a local MCP server in either Python (FastMCP) or Node / TypeScript (the official MCP SDK), then registering it across all five Nexus-Hub-supported AI CLIs (Claude Code, Cursor, Codex, Gemini, OpenCode). The skill enforces the AGENTS.md MCP Registry Policy decision tree before building - many capabilities should be a skill (LLM-native), not an MCP. When an MCP is the right shape, the bundled scaffolding scripts (init-mcp-fastmcp.{sh,ps1} for Python, init-mcp-ts.{sh,ps1} for Node / TS) generate a one-tool hello-world server in under 30 seconds, with tool definitions, structured output, auth stubs, and transport configuration ready to extend. Reference docs (references/fastmcp.md, references/ts-sdk.md) cover the deeper API surface. Trigger phrases: build an MCP, MCP server, FastMCP, MCP SDK, MCP tool, expose tools to the agent, wrap an API as an MCP, custom MCP, MCP transport, register an MCP, model context protocol, hello-world MCP."
---

# MCP Builder

Build a local MCP server in Python (FastMCP) or Node / TypeScript (the official MCP SDK), then register it across all five Nexus-Hub-supported AI CLIs. The skill is opinionated about WHAT to build before HOW: many requests for "an MCP that does X" are better served by a skill (LLM-native, zero infrastructure) per the AGENTS.md MCP Registry Policy. When an MCP is the right shape, the bundled scaffolding scripts get a working server up in under 30 seconds.

## When to Use This Skill

Use this skill when:

- The user wants to expose a deterministic capability the LLM cannot reliably do on its own (a database query, a filesystem operation, a service-account API call, a calculation that needs exact numerics)
- The capability is local or runs against a service the user already owns (their database, their cluster, their git repo)
- The capability returns structured data the agent will reason over (typed records, schemas, IDs)
- A skill alone is insufficient because the operation needs deterministic execution outside the LLM (e.g., "run this SQL query against my Postgres", "list pending pull requests on my repo", "publish a message to my Pub/Sub topic")
- The user wants the same capability available across multiple AI CLIs (Claude Code, Cursor, Codex, Gemini, OpenCode) - a single MCP server registers in all five

**Trigger phrases**: "build an MCP", "MCP server", "FastMCP", "MCP SDK", "MCP tool", "expose tools to the agent", "wrap an API as an MCP", "custom MCP", "MCP transport", "register an MCP", "model context protocol", "hello-world MCP", "spin up a tool server".

**When NOT to use** (apply the [AGENTS.md MCP Registry Policy](../../../../AGENTS.md#mcp-registry-policy) decision tree before building):

- The capability can be achieved by instructing the LLM directly (write code, generate text, explain a concept, summarize a doc) - ship a SKILL, not an MCP. See `workflow/create-skill-or-command`.
- The capability is search-as-service, embeddings-as-service, scraping-as-service, or generation-as-service - categorically rejected by policy regardless of vendor.
- The user wants to CONSUME an existing third-party MCP - that is a settings.json edit, not a build task. Cross-link `catalog/mcp-configs/mcp-servers.json` for the curated registry.
- The third party is the data destination but reverse-engineering is viable - prefer building a local internal MCP (per the policy) over wrapping the third party's hosted service.
- Hooks are sufficient (one-shot lifecycle event with no return value) - use a hook, not an MCP. See `catalog/hooks/`.
- A simple shell script invoked by the user is sufficient (not by the agent autonomously) - use a script, not an MCP.

If unsure whether the capability needs an MCP or a skill, walk the AGENTS.md decision tree explicitly with the user before scaffolding. The wrong shape costs more than the build.

## When to Build vs. Skill vs. Hook (Quick Compare)

| Shape | Use when | Cost | Cross-CLI reach |
|---|---|---|---|
| Skill | Capability is achievable by instructing the LLM (writing, reasoning, generating, explaining) | Lowest - just SKILL.md + frontmatter | All 5 CLIs via the recursive-copy installer |
| Hook | One-shot lifecycle event (PreToolUse, PostToolUse, SessionStart) with no return value the agent uses downstream | Low - one shell or Python script | Claude / Codex / Gemini / OpenCode (parity scripts); other CLIs case-by-case |
| MCP | Deterministic capability returning structured data the LLM cannot reliably do (database query, exact API call, file ops, owned-service integration) | Highest - server process, transport, schemas, registration in settings.json across 5 CLIs | All 5 CLIs once registered |

The MCP shape is the most expensive of the three. Make sure the capability actually needs deterministic execution before paying for it.

## The Two Stacks

| Layer | Python (FastMCP) | Node / TypeScript (MCP SDK) |
|---|---|---|
| Package | `mcp[cli]` (PyPI) | `@modelcontextprotocol/sdk` (npm) |
| Min runtime | Python 3.10+ | Node 20+ |
| Transport | stdio (default) / HTTP / SSE | stdio (default) / HTTP / SSE |
| Tool definition | `@mcp.tool()` decorator on a function with type-annotated parameters | `server.tool(name, schema, handler)` with a Zod schema |
| Structured output | Native via Pydantic models | Native via Zod schemas |
| Local dev | `mcp dev <module>` for inspector | `npm run dev` (custom) + `mcp inspector` separately |
| Auth | Custom middleware on the FastMCP app | Custom middleware on the SDK server |
| Best for | Data-science / Python-heavy services, ML pipelines, scientific tooling | Frontend / Node-heavy services, npm-only environments, TypeScript-typed clients |

Pick by the language the underlying service is already written in. If both are equally viable, FastMCP wins on speed-to-running-server (decorator-based, fewer files); the TypeScript SDK wins on type-safety-end-to-end if the consumer is already a TS app.

## Instructions

### Step 0 - Decide if an MCP is the right shape

Before scaffolding, walk the [AGENTS.md MCP Registry Policy](../../../../AGENTS.md#mcp-registry-policy) decision tree with the user:

1. Is this capability local-only (their own DB, their own files, their own service)? Proceed.
2. Can the LLM do this directly via a skill? If yes, ship a skill instead.
3. Can the third party's logic be reverse-engineered locally? If yes, build a local internal MCP, not a vendor wrapper.
4. Is this a trusted-vendor wrapper for a service the user already pays for? Proceed with caution - justify per the 3-condition test.
5. Is this search / embeddings / scraping / generation as service? Drop categorically.

Only proceed past step 0 if the user confirms the capability needs deterministic execution outside the LLM AND the policy allows it.

### Step 1 - Pick the stack

Ask the user (one consolidated turn):

1. Python or Node / TypeScript? (Default: match the underlying service's language; fall back to Python if neither.)
2. What is the tool's name and what does it return? (e.g., "name: query_postgres, returns: array of {row_id, value}".)
3. What transport? (stdio is the default and almost always correct for local servers; HTTP/SSE only when the server runs on a different host.)
4. Where will the server run? (Local-only is the default and simplest; remote requires more thought about auth.)

Record the answers - they shape the scaffold flags.

### Step 2 - Scaffold the server

Run the bundled init script for the chosen stack:

```bash
# Python (FastMCP) - macOS / Linux
bash ~/.nexus-hub/skills/ai-development/mcp-builder/scripts/init-mcp-fastmcp.sh <server-name>

# Node / TS (MCP SDK) - macOS / Linux
bash ~/.nexus-hub/skills/ai-development/mcp-builder/scripts/init-mcp-ts.sh <server-name>
```

```powershell
# Python (FastMCP) - Windows
& "$HOME\.nexus-hub\skills\ai-development\mcp-builder\scripts\init-mcp-fastmcp.ps1" -ServerName <server-name>

# Node / TS (MCP SDK) - Windows
& "$HOME\.nexus-hub\skills\ai-development\mcp-builder\scripts\init-mcp-ts.ps1" -ServerName <server-name>
```

The Python script: (a) verifies Python 3.10+; (b) creates a venv; (c) installs `mcp[cli]`; (d) writes `<name>/server.py` with one example `@mcp.tool()` and a `__main__` block running stdio transport; (e) writes a minimal `pyproject.toml`; (f) prints next-step commands.

The TypeScript script: (a) verifies Node 20+; (b) runs `npm init -y`; (c) installs `@modelcontextprotocol/sdk` and `zod`; (d) writes `<name>/src/server.ts` with one example tool and stdio transport; (e) configures `package.json` with a `dev` script; (f) prints next-step commands.

### Step 3 - Define your tool(s)

Edit the scaffolded server. Each tool needs:

- **Name** - kebab-case verb-object (`query-postgres`, `list-pull-requests`); never just a noun.
- **Description** - what it does, when the agent should invoke it, what it returns. The agent reads this to decide when to call - same pushy-description rule that applies to skills.
- **Input schema** - typed parameters with descriptions. FastMCP uses Pydantic / annotations; TS SDK uses Zod.
- **Output schema** - structured data, not free-form strings. The agent reasons better over `{rows: [{id, name}]}` than over a single string `"id=1 name=foo, id=2 name=bar"`.
- **Error handling** - return an error code/message in a structured shape, not as a thrown exception that crashes the transport. The MCP protocol distinguishes tool errors from server errors.

Reference docs: deeper FastMCP API at [references/fastmcp.md](references/fastmcp.md); deeper TS SDK API at [references/ts-sdk.md](references/ts-sdk.md).

### Step 4 - Test locally

Python: `mcp dev server.py` opens the MCP Inspector at `http://localhost:5173`. The inspector lists tools, lets the user invoke each with sample input, and shows the structured output.

TypeScript: run `npm run dev` to start the server in stdio mode, then in a separate terminal run `npx @modelcontextprotocol/inspector node ./build/server.js`. Same inspector UI.

Verify before claiming success: the inspector lists all your tools; each invokes without errors on the sample input; the output schema matches the declared types.

### Step 5 - Add auth (when needed)

Local stdio servers usually do not need auth - the server runs as the user, with the user's permissions. Add auth when:

- The server runs over HTTP / SSE (remote transport)
- The server holds credentials for an external service and you want to scope which agent sessions can use it
- Multi-tenancy is a requirement (multiple users hit the same server)

Both stacks support custom middleware on the transport layer. The simplest pattern: a bearer token in the `Authorization` header, validated against an env var (`MCP_AUTH_TOKEN`). For OAuth or more complex flows, consult the upstream protocol docs - the bundled scaffold does not lock you into a specific auth pattern.

### Step 6 - Register the MCP across all five CLIs

Once the server runs locally, register it in each AI CLI's settings. The path varies by CLI:

| CLI | Settings file | Section |
|---|---|---|
| Claude Code | `~/.claude/settings.json` | `mcpServers.<name>` |
| Cursor | `~/.cursor/mcp.json` (or per-project `.cursor/mcp.json`) | `mcpServers.<name>` |
| Codex | `~/.codex/config.json` | `mcpServers.<name>` |
| Gemini / Antigravity | `~/.gemini/mcp.json` | `mcpServers.<name>` |
| OpenCode | `~/.config/opencode/mcp.json` | `mcpServers.<name>` |

The entry shape is the same across all five (the MCP protocol is the contract):

```json
{
  "mcpServers": {
    "<server-name>": {
      "command": "python",
      "args": ["/abs/path/to/server.py"],
      "env": {
        "MCP_AUTH_TOKEN": "..."
      }
    }
  }
}
```

For Node / TS:

```json
{
  "mcpServers": {
    "<server-name>": {
      "command": "node",
      "args": ["/abs/path/to/build/server.js"]
    }
  }
}
```

If your server is intended for the curated Nexus-Hub registry (`catalog/mcp-configs/mcp-servers.json`), follow the AGENTS.md MCP Registry Policy: the `_comment` field MUST answer the five-question audit, and the `docs/policy/mcp-reverse-engineering-matrix.md` MUST get a row classifying the bucket. Do NOT add to the registry without walking the policy.

### Step 7 - Verify cross-CLI

Open each registered CLI in turn (or at least the user's primary plus one other) and verify:

- The CLI lists the MCP's tools in its tool inventory (Claude Code: `/mcp`; Cursor: status bar; Codex / Gemini / OpenCode: per their docs).
- The agent can invoke the tool with sample input.
- The agent receives the structured output and reasons over it correctly.

If a CLI doesn't list the MCP, the most common cause is a typo in the absolute path or a missing executable bit on the server script (Linux / macOS).

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "I'll wrap the third-party search API as an MCP - users want it" | Search-as-service is categorically rejected by the AGENTS.md MCP Registry Policy. Build a local internal MCP that does keyword + AST chunking against the user's own filesystem, OR ship a skill that uses the agent's web-fetch directly. The vendor wrapper is the easy answer; the policy says no for good reasons (data flow surface, lock-in, retraction risk). |
| "An MCP is overkill - I'll just put this in a skill" | A skill is the right answer ONLY if the LLM can do the capability reliably. A SQL query, a deterministic API call, a file-system operation - those need an MCP because the LLM cannot guarantee correct execution. Walk the decision tree before defaulting either way. |
| "I'll use FastMCP because Python is easier" | FastMCP is great for Python services; it is the wrong shape if the underlying service is a TypeScript app and you'd be calling out from Python to a TS process. Pick by the underlying service's language, not by personal preference. |
| "I'll skip Step 0 - the user already said they want an MCP" | The user says they want an MCP because that is the term they have heard. The policy decision tree exists to catch the case where they actually want a skill, a hook, or to consume an existing MCP. Spend 60 seconds on Step 0 before paying for the build. |
| "I'll use HTTP transport from the start - it's more flexible" | Stdio is the default for a reason: it is the simplest transport, requires no port management, and works in every CLI without extra config. HTTP / SSE is correct ONLY when the server runs on a different host from the agent. Default to stdio; promote later if needed. |
| "Auth is too complex - I'll skip it for v1" | Skip auth ONLY when the server is local-stdio and the operations are read-only against the user's own data. The moment the server can WRITE (mutate state, send messages, post API calls) or runs over HTTP, auth is mandatory; deferring it means shipping an unauthenticated mutation surface. |
| "I'll register the MCP only in the user's primary CLI - they don't use the others" | One of the design points of MCP is cross-CLI reach. Registering in only one CLI is fine for the user's session today, but limits the MCP's value as the user adds CLIs. The five settings.json edits are templates; ship them all. |
| "Tool descriptions should be terse - the agent will figure it out" | Tool descriptions follow the same pushy-description rule as skill descriptions: the agent under-triggers tool calls when the description is too narrow. List trigger phrases, list when NOT to call, give an example invocation. The 60 extra words pay for themselves the first time the agent skips a relevant call under a terse description. |

## Verification

Binary checklist - each item must describe an observable artifact or state.

- [ ] AGENTS.md MCP Registry Policy decision tree was walked with the user before scaffolding (recorded in chat or session-history).
- [ ] The chosen scaffolding script ran and produced a `<server-name>/` directory with `server.py` (FastMCP) or `src/server.ts` (TS SDK), a runnable manifest (`pyproject.toml` / `package.json`), and the chosen transport configured.
- [ ] At least one tool is defined with a kebab-case name, an input schema, an output schema, and a non-trivial description.
- [ ] The MCP Inspector (`mcp dev` or `mcp inspector`) lists the tools, accepts sample input, and returns structured output without transport errors.
- [ ] The server's settings.json entry has been written for at least the user's primary CLI; the user has been told the same shape applies to all five (paths documented in Step 6).
- [ ] No vendor-specific search / embeddings / scraping / generation calls in the implementation (verify against the AGENTS.md hard-no list).
- [ ] If submitting to `catalog/mcp-configs/mcp-servers.json`, the five-question audit comment is filled and the reverse-engineering matrix has a corresponding row.
- [ ] Tool descriptions follow the pushy-description rule (list trigger phrases, list when NOT to call, include `SKIP:` clause for ambiguous cases).
- [ ] Cross-platform: both `init-mcp-fastmcp.{sh,ps1}` and `init-mcp-ts.{sh,ps1}` exist as siblings and produce equivalent scaffolds on their respective host shells.

"The MCP works on my machine" is not a valid verification criterion. The verification is: did the inspector confirm tools are listed, did sample input return structured output, and was Step 0 walked before the build?

## Bundled Resources

The skill ships four scaffolding scripts (FastMCP and TS SDK, each with bash + PowerShell siblings) and two reference docs.

- `scripts/init-mcp-fastmcp.sh` - bash script for macOS / Linux. Scaffolds a FastMCP Python server with one example tool. Set executable on installer copy.
- `scripts/init-mcp-fastmcp.ps1` - PowerShell sibling. Same scaffold, Windows shell.
- `scripts/init-mcp-ts.sh` - bash script for macOS / Linux. Scaffolds a Node / TypeScript MCP SDK server with one example tool.
- `scripts/init-mcp-ts.ps1` - PowerShell sibling. Same scaffold, Windows shell.
- `references/fastmcp.md` - deeper FastMCP API surface: tool definitions, structured output, transports, auth, testing patterns, common pitfalls.
- `references/ts-sdk.md` - deeper TS SDK API surface: same topics for the Node / TypeScript stack.

The `.sh` and `.ps1` siblings are kept parallel per the v1.1.3 four-hook precedent: every bundled `.sh` has a `.ps1` sibling, both produce the same output, neither references the other. Cross-platform parity is enforced by the recursive-copy logic in `scripts/installer.{sh,ps1}` (Phase 3 of the v1.1.5 plan).

## Related Skills

- [[tool-design]] -- upstream skill for designing tool / API schemas the agent consumes well; apply BEFORE scaffolding the MCP so the tool surface is well-shaped.
- [[ai-agent-development]] -- broader agent architecture context (tool use patterns, planning loops); consumes MCPs as one tool source.
- [[claude-agent-sdk]] -- Claude Agent SDK integration; consumes MCPs registered in `~/.claude/settings.json`.
- [[api-design]] -- REST / gRPC / GraphQL design; relevant when wrapping an existing API as an MCP and you need the underlying API to be well-shaped first.
- [[python-expert]] -- production Python patterns for the FastMCP path.
- [[typescript-expert]] -- production TypeScript patterns for the SDK path.
