# External Integrations and MCPs

Model Context Protocol (MCP) integrations for Nexus-Hub skills and workflows.

---

## Policy Compliance Notice

Integrations documented here are **governed by the MCP Registry Policy** in [AGENTS.md](../../AGENTS.md) and classified in [docs/policy/mcp-reverse-engineering-matrix.md](../../docs/policy/mcp-reverse-engineering-matrix.md). This guide lists only servers that satisfy the policy's decision tree:

1. Local-only (internal or zero-outbound Anthropic-official)
2. LLM-native skill (no MCP needed)
3. Reverse-engineered internal MCP under `extensions/`
4. Trusted vendor wrapper where the vendor is the intrinsic data destination AND the capability cannot be reverse-engineered AND the feature is extremely worth it
5. Otherwise: drop

Third-party search-as-service, embeddings-as-service, scraping-as-service, and generation-as-service MCPs are **hard-no** under the policy. Previously-common servers like context7, exa, firecrawl, magic-ui, claude-context, tavily, and hosted LLM proxies (OpenAI / Anthropic / etc. via MCP) are NOT shipped in `catalog/mcp-configs/mcp-servers.json` and NOT documented below. See [MCP_DEVELOPMENT_SERVERS.md](../../guides/MCP_DEVELOPMENT_SERVERS.md) "Reverse-engineered replacements" for the Nexus-Hub equivalents.

---

## What are MCPs?

Model Context Protocol (MCP) is Anthropic's standard for connecting Claude to external tools, services, and data sources. An MCP server runs as a local subprocess; the agent calls its exposed tools via stdio. The server may be purely local (no network) or wrap an outbound API. Under the policy, outbound-calling MCPs are acceptable only when the vendor is the intrinsic data destination (your own GitHub repo, your own database, your own Railway project).

---

## MCP Configuration

MCPs are configured in `.mcp.json` at your project root or `~/.claude/.mcp.json` for user-scope. The canonical registry Nexus-Hub ships is `catalog/mcp-configs/mcp-servers.json`; copy the entries you need. See [MCP_DEVELOPMENT_SERVERS.md](../../guides/MCP_DEVELOPMENT_SERVERS.md) for recommendation ordering by workflow stage.

```json
{
  "mcpServers": {
    "server-name": {
      "command": "command-to-run",
      "args": ["arg1", "arg2"],
      "env": { "API_KEY": "${ENV_VAR_NAME}" }
    }
  }
}
```

---

## Nexus-Hub Internal MCPs

Three servers shipped in this repo. All pure-local, zero outbound calls, zero API keys.

| Server | Purpose | Install | Tool surface |
|---|---|---|---|
| `nexus-skill-server` | Skill catalog retrieval | `pip install -e extensions/nexus-skill-server` | `search_skills`, `get_skill`, `list_categories`, `list_bundles`, `get_bundle` |
| `nexus-code-search` | Local keyword code search with incremental indexing (v1.0.0 keyword-only; dense/hybrid planned for v1.1.0) | `pip install -e extensions/nexus-code-search` | `index_codebase`, `search_code`, `clear_index`, `get_indexing_status` |
| `nexus-web-fetch` | Single-URL HTTPS fetch + readability extraction (SSRF-guarded) | `pip install -e extensions/nexus-web-fetch` | `fetch_url(url, render_js=False, extract_mode="readability")` |

All three are installed by the Nexus-Hub installer under `~/.nexus-hub/`. Their registry entries in `catalog/mcp-configs/mcp-servers.json` carry the full 5-question audit.

---

## Anthropic-Official Local MCPs

| Server | Purpose | Outbound calls |
|---|---|---|
| `filesystem` | Scoped file read/write | None |
| `memory` | Persistent entity / fact store | None |
| `sequential-thinking` | Step-by-step reasoning scaffold | None |
| `sqlite` | Query a SQLite database file | None |

See `catalog/mcp-configs/mcp-servers.json` for the config snippets.

---

## Vendor-Intrinsic Wrappers (Your-Own-Account)

Acceptable **only if you are already a customer of the vendor**. The vendor is the intrinsic data destination. Each entry in `catalog/mcp-configs/mcp-servers.json` carries the 5-question audit in its `_comment`.

### GitHub

```json
{
  "mcpServers": {
    "github": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": { "GITHUB_PERSONAL_ACCESS_TOKEN": "${GITHUB_TOKEN}" }
    }
  }
}
```

Setup:
1. Generate a GitHub Personal Access Token at Settings > Developer settings > Personal access tokens. Minimum scopes: `repo`, `read:org`, `read:user`.
2. Export `GITHUB_TOKEN=<token>` in your shell profile or `.env`.

### PostgreSQL (your own database)

```json
{
  "mcpServers": {
    "postgres": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-postgres", "${DATABASE_URL}"]
    }
  }
}
```

### Supabase, Railway, Vercel, Cloudflare

See `catalog/mcp-configs/mcp-servers.json` for ready-to-use snippets with the 5-question audit in each `_comment` field. All require a user-supplied API token set as an environment variable.

---

## Security Best Practices

### Never commit secrets

Use `${ENV_VAR}` references in `.mcp.json`; never hardcode tokens. Set values in your shell profile or a `.env` file that is in `.gitignore`.

```json
{
  "mcpServers": {
    "github": {
      "env": { "GITHUB_PERSONAL_ACCESS_TOKEN": "${GITHUB_TOKEN}" }
    }
  }
}
```

```bash
# Linux / macOS
export GITHUB_TOKEN="ghp_abc123..."

# Windows PowerShell
$env:GITHUB_TOKEN="ghp_abc123..."
```

### Rotate keys regularly

- Rotate API keys every 90 days.
- Use short-lived tokens where possible.
- Revoke unused keys immediately.

### Gitignore

Add to `.gitignore`:

```
.mcp.json
.env
*.secrets
credentials.json
```

---

## Troubleshooting

### MCP not found

```
Cannot find module '@modelcontextprotocol/server-github'
```

Use `npx -y <package>` in the args (as in every snippet above) so the package auto-installs on first run. Alternatively `npm install -g <package>`.

### Authentication failed (401 / 403)

- Verify the API key is correct.
- Confirm the key has the required scopes.
- Confirm the key hasn't expired.
- Test the credential directly against the vendor API with `curl`.

### Connection timeout

- Check network connectivity.
- Verify the service URL.
- Check firewall and proxy settings.

### Rate limiting (429)

- Reduce call frequency.
- Cache within your workflow.
- Use authenticated requests where possible (higher limits).

---

## Custom MCPs

To build a new MCP server for Nexus-Hub:

1. Walk the MCP Registry Policy decision tree in [AGENTS.md](../../AGENTS.md). Prefer local-only or skill-native before reaching for external wrappers.
2. If building a new local-only MCP, mirror the layout of `extensions/nexus-skill-server/` or `extensions/nexus-code-search/`.
3. Add a row to `docs/policy/mcp-reverse-engineering-matrix.md` before opening the PR.
4. Update `catalog/mcp-configs/mcp-servers.json` with a `_comment` that answers the 5-question audit.
5. Register the package in both installer scripts per the `AGENTS.md` Installer-Aware Changes section.

External references:
- [Anthropic MCP Documentation](https://docs.anthropic.com/en/docs/agents-and-tools/mcp)
- [MCP SDK](https://github.com/modelcontextprotocol)

---

*Part of Nexus-Hub (v1.0.0 origin; rebranded at v2.0.0). Governed by the MCP Registry Policy in `AGENTS.md`.*
