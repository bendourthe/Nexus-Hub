# MCP TypeScript SDK Reference

Deeper API surface for `@modelcontextprotocol/sdk`, the official Node / TypeScript SDK for the Model Context Protocol. Loaded on demand by `mcp-builder/SKILL.md`.

## Install

```bash
npm install @modelcontextprotocol/sdk zod
```

`zod` is not strictly required, but the SDK uses it for input schema validation in the recommended pattern. Use Zod over hand-written `JSONSchema` objects - the type inference is the value.

Minimum runtime: Node 20+. ESM-only.

## Minimal server

```typescript
// src/server.ts
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { z } from "zod";

const server = new McpServer({
  name: "example-server",
  version: "0.1.0",
});

server.tool(
  "add",
  {
    a: z.number().describe("First addend"),
    b: z.number().describe("Second addend"),
  },
  async ({ a, b }) => ({
    content: [{ type: "text", text: String(a + b) }],
  }),
);

const transport = new StdioServerTransport();
await server.connect(transport);
```

Run: `npx tsx src/server.ts` (silent stdio loop, ESM-native via tsx).

Inspect: `npx @modelcontextprotocol/inspector npx tsx src/server.ts` (opens the inspector at http://localhost:5173).

## Tool definitions

Three positional arguments: name, input schema (Zod), handler function.

```typescript
import { z } from "zod";

const QueryResult = z.object({
  rows: z.array(z.record(z.unknown())),
  rowCount: z.number().describe("Number of rows returned"),
});

server.tool(
  "query-postgres",
  {
    sql: z.string().describe("Read-only SQL query to execute"),
    maxRows: z.number().int().positive().default(100).describe("Row cap"),
  },
  async ({ sql, maxRows }) => {
    // ... implementation
    const rows: unknown[] = [];
    return {
      content: [
        {
          type: "text",
          text: JSON.stringify({ rows, rowCount: rows.length }),
        },
      ],
      structuredContent: { rows, rowCount: rows.length },
    };
  },
);
```

Key points:

1. **Tool name uses kebab-case**. `query-postgres`, not `queryPostgres`. The agent reads names directly.
2. **Zod schemas drive input validation AND inference**. The handler's destructured args are typed automatically.
3. **Return both `content` (string-flavored) and `structuredContent` (typed)**. `content` is the legacy field; `structuredContent` is the typed form modern clients prefer. Ship both for compatibility.
4. **`.describe()` on each Zod field surfaces in the inspector**. Treat parameter descriptions as agent-facing prose - apply pushy-description rules.
5. **Async handlers are required**. Return a `Promise`; the SDK awaits it.

## Transports

| Transport | When to use | Module |
|---|---|---|
| stdio | Default. Local server invoked by an MCP client. | `StdioServerTransport` from `@modelcontextprotocol/sdk/server/stdio.js`. |
| HTTP | Remote server, multiple clients. | `StreamableHTTPServerTransport` from `@modelcontextprotocol/sdk/server/streamableHttp.js`. |
| SSE | Streaming server-sent events to a browser client. | Use the HTTP transport with SSE support; SSE-specific helper available in newer SDK versions. |

Stdio is the default. Promote to HTTP only when remote.

## Auth (HTTP only)

```typescript
import express from "express";
import { StreamableHTTPServerTransport } from "@modelcontextprotocol/sdk/server/streamableHttp.js";

const app = express();
const expectedToken = process.env.MCP_AUTH_TOKEN;

app.use((req, res, next) => {
  if (req.headers.authorization !== `Bearer ${expectedToken}`) {
    res.status(401).json({ error: "invalid token" });
    return;
  }
  next();
});

const transport = new StreamableHTTPServerTransport({ /* options */ });
// ... mount transport on the express app and start
```

## Resources and prompts

```typescript
server.resource(
  "schema://postgres/{table}",
  async ({ table }) => ({
    contents: [{ uri: `schema://postgres/${table}`, text: "... DDL ..." }],
  }),
);

server.prompt(
  "review-query",
  { sql: z.string() },
  ({ sql }) => ({
    messages: [
      {
        role: "user",
        content: { type: "text", text: `Review this SQL:\n\n${sql}` },
      },
    ],
  }),
);
```

Resources and prompts are optional. Most MCPs ship tools only.

## Testing patterns

| Pattern | When | How |
|---|---|---|
| Inspector smoke test | Every commit | `npx @modelcontextprotocol/inspector npx tsx src/server.ts`; verify each tool. |
| Unit tests for handler logic | Non-trivial tools | Vitest; extract the handler as a named function; test it directly without the SDK. |
| Zod schema regression | Before publishing | Snapshot-test the schemas via `zod-to-json-schema` to catch accidental shape changes. |
| Integration over stdio | Pre-release | Use `Client` from `@modelcontextprotocol/sdk/client/index.js` with `StdioClientTransport` to spawn the server. |

## Common pitfalls

| Pitfall | Fix |
|---|---|
| ESM/CJS interop errors at runtime | The SDK is ESM-only. Set `"type": "module"` in `package.json` and use `.js` import extensions in TS source. |
| Handler throws → transport closes | Catch errors and return `{ content: [{ type: "text", text: "..." }], isError: true }`. Never leak exceptions to the transport. |
| Tool description is one sentence | Apply the pushy-description rule. Tool description goes in `.describe()` on the Zod schema or as a third field on `server.tool()` (newer SDK signature). |
| `tsx` not found in production | Use `tsc` to compile to `dist/` and ship `dist/server.js`; reference that path in settings.json. |
| Inspector won't connect | Confirm the server runs cleanly via `npx tsx src/server.ts` first; fix any startup errors before launching the inspector. |
| Settings.json path is `~/...` | Must be absolute. `node ~/server.js` doesn't expand `~` in `args`. |

## Going beyond the scaffold

The `init-mcp-ts.{sh,ps1}` script ships a one-tool hello-world. Extending past that:

1. **Multiple tools**: call `server.tool(...)` repeatedly. Group definitions by domain in separate files; import into `server.ts`.
2. **Configuration**: load secrets from `process.env` at startup; never hardcode. Use `zod` to validate the env shape.
3. **Logging**: use a logger that writes to a file (not stderr - conflicts with stdio transport). Pino or winston with a file transport.
4. **Build**: configure `tsc` with `"module": "ESNext"`, `"target": "ES2022"`, `"moduleResolution": "Bundler"` (or `"node16"`).
5. **Distribution**: publish as an npm package with `"bin"` so users can `npx <package-name>`.
