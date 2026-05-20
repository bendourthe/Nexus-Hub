# MCP Development Servers Guide

**Policy-compliant MCP servers recommended for development workflows with Claude Code**

[Back to Main](../README.md)

---

## Overview

Model Context Protocol (MCP) servers extend Claude Code with local tool surfaces. This guide covers Nexus-Hub's recommended servers - all of which comply with the **MCP Registry Policy** in [AGENTS.md](../AGENTS.md). Every server listed here has a corresponding row in the [Reverse-Engineering Matrix](../docs/v1.0.0/mcp-reverse-engineering-matrix.md) documenting its classification and data-flow audit.

**What this guide deliberately does NOT include**: search-as-service, embeddings-as-service, scraping-as-service, and generation-as-service MCPs (context7, exa, firecrawl, magic-ui, claude-context, deepwiki, tavily, and similar). These are hard-no under the policy because they transmit query text, source code, or prompts to third-party data processors that the user has no pre-existing commercial relationship with. Where the capability is genuinely useful, Nexus-Hub reverse-engineers the pattern into an internal MCP or a skill - see the "Reverse-engineered replacements" section below.

---

## Recommended servers by workflow stage

All recommendations below fall into three policy buckets: **internal** (Nexus-Hub ships the server), **already-local** (Anthropic-official, zero outbound), and **vendor-intrinsic** (your-own-account wrapper). See the matrix for each entry's full audit.

### Research and code navigation

#### `nexus-skill-server` (internal)

**Purpose**: Retrieval over Nexus-Hub's skill catalog. Lets the agent match a user request to the most relevant skill and load its full instructions on demand.

**Tools**: `search_skills`, `get_skill`, `list_categories`, `list_bundles`, `get_bundle`.

**Data flow**: 100% local. Reads `data/skills.json` from disk. No network.

**When to use**: always-on. Claude Code consults it at the start of every non-trivial task.

---

#### `nexus-code-search` (internal, new in v1.0.0)

**Purpose**: Local code search over a proprietary repo. Keyword-based inverted index + rapidfuzz scoring in v1.0.0; dense / hybrid retrieval planned for v1.1.0.

**Tools**: `index_codebase`, `search_code`, `clear_index`, `get_indexing_status`.

**Data flow**: 100% local. Index stored at `<repo>/.nexus/code-index/`. No API keys required. No model downloads. No outbound calls.

**When to use**: when the repo exceeds the model's context window and the agent needs to retrieve relevant chunks. Replaces the need for external semantic-code-search services.

**Reverse-engineering note**: this is the Nexus-Hub internal equivalent of the "semantic code search" category. See the [matrix row](../docs/v1.0.0/mcp-reverse-engineering-matrix.md) for the RE pedigree.

---

#### `nexus-web-fetch` (internal, new in v1.0.0)

**Purpose**: Direct HTTPS fetch + readability extraction against a user-specified URL. Replaces third-party web-scraping services that route fetches through their own infrastructure.

**Tools**: `fetch_url(url, render_js=False, extract_mode="readability")`.

**Data flow**: HTTPS to the user-specified URL. RFC 1918, localhost, link-local, and `file://` blocked by default for SSRF safety. No third-party intermediary. No API keys.

**When to use**: single-URL research fetches (a known-public docs page, a spec, a blog post). For large-scale crawling, use a local Playwright / Scrapy workflow instead - this MCP is scoped to one URL at a time.

---

#### `memory` (Anthropic-official, local)

**Purpose**: Persistent entity / fact store for the current session.

**Tools**: documented in the upstream `@modelcontextprotocol/server-memory` reference.

**Data flow**: Local JSON store. No network.

---

#### `sequential-thinking` (Anthropic-official, local)

**Purpose**: Structured step-by-step reasoning scaffold for complex problems.

**Data flow**: None. Purely in-process.

---

### Debug and inspect

#### `filesystem` (Anthropic-official, local)

**Purpose**: Scoped read and write of files under a user-specified directory.

**Data flow**: None at the MCP layer. File contents flow to Claude via standard tool-result channels.

**Usage note**: Replace `/path/to/your/project` in the args with your actual repo root.

---

#### `sqlite` (Anthropic-official, local)

**Purpose**: Query a SQLite database file.

**Data flow**: None at the MCP layer (SQLite is a local file).

---

### Deploy and operate (vendor-intrinsic wrappers)

The following servers wrap a vendor API that the user already has a commercial relationship with. Data goes to the user's own account at that vendor - not to a new third party. Each `_comment` in `catalog/mcp-configs/mcp-servers.json` carries the full 5-question audit.

| Server | Vendor | Keys required | Data destination |
|---|---|---|---|
| `github` | GitHub | `GITHUB_TOKEN` (PAT) | api.github.com with user's PAT scope |
| `postgres` | user's own DB | `DATABASE_URL` | user's Postgres instance |
| `supabase` | Supabase | `SUPABASE_ACCESS_TOKEN` | supabase.com (user's project) |
| `railway` | Railway | `RAILWAY_API_TOKEN` | railway.app (user's account) |
| `vercel` | Vercel | `VERCEL_TOKEN` | vercel.com (user's account) |
| `cloudflare` | Cloudflare | `CLOUDFLARE_API_TOKEN` + `CLOUDFLARE_ACCOUNT_ID` | api.cloudflare.com (user's account) |

**When to use**: only if you are already a customer of the vendor. Otherwise drop - the policy does NOT endorse adding a vendor wrapper you don't already use.

---

## Reverse-engineered replacements

The following capabilities were popular in the wider MCP ecosystem but are **not** shipped in Nexus-Hub's registry because they would introduce a new third-party data processor. Each has a policy-compliant replacement:

| Popular pattern | Nexus-Hub replacement | Type |
|---|---|---|
| Library documentation lookup (context7 and similar) | `local-docs-lookup` skill | Skill (no MCP) |
| UI component generation (magic-ui and similar) | `ui-component-generation` skill | Skill (no MCP) |
| Web scraping / crawling (firecrawl and similar) | `nexus-web-fetch` MCP (single-URL scope, SSRF-guarded) | Internal MCP |
| Semantic code search (claude-context and similar) | `nexus-code-search` MCP (keyword in v1.0.0, dense in v1.1.0) + `code-semantic-search` skill | Internal MCP + skill |
| Neural web search (exa, tavily, and similar) | Not replaced. Drop-outright under the policy: the web itself cannot be recreated locally, and the trust cost of routing agent-composed queries through a third-party search service exceeds the benefit for a regulated-data profile. | n/a |

See the [Reverse-Engineering Matrix](../docs/v1.0.0/mcp-reverse-engineering-matrix.md) for the full classification per capability.

---

## Quick setup

Copy the entries you need from `catalog/mcp-configs/mcp-servers.json` into your `.claude/settings.json` under the `mcpServers` key, or into a project-level `.mcp.json`. Set the required env vars in your shell profile or `.env` file before starting Claude Code. Never hardcode tokens.

Example (keep active MCPs under 10 to preserve context window):

```json
{
  "mcpServers": {
    "nexus-skill-server": {
      "command": "python",
      "args": ["-m", "nexus_skill_server"],
      "env": {"NEXUS_HUB_ROOT": "${NEXUS_HUB_ROOT}"}
    },
    "nexus-code-search": {
      "command": "python",
      "args": ["-m", "nexus_code_search"],
      "env": {"NEXUS_HUB_ROOT": "${NEXUS_HUB_ROOT}"}
    },
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "/path/to/your/project"]
    }
  }
}
```

## Permission configuration

Add MCP tool permissions to `.claude/settings.json`:

```json
{
  "permissions": {
    "allow": [
      "mcp__nexus-skill-server__*",
      "mcp__nexus-code-search__*",
      "mcp__filesystem__*",
      "mcp__memory__*",
      "mcp__sequential-thinking__*"
    ],
    "ask": [
      "mcp__nexus-web-fetch__*",
      "mcp__github__*",
      "mcp__postgres__*",
      "mcp__supabase__*"
    ]
  }
}
```

Vendor wrappers default to `ask` because they make outbound calls with user credentials - even though the vendor is the intrinsic destination, the agent should surface the action before executing.

## Scope recommendations

| Server | Scope | Rationale |
|---|---|---|
| `nexus-skill-server` | User | Catalog is shared across projects |
| `nexus-code-search` | Project | Index is repo-specific |
| `nexus-web-fetch` | User | URL fetch is cross-project |
| `filesystem` | Project | Scoped to the project root |
| `memory` / `sequential-thinking` / `sqlite` | User | Cross-project |
| Vendor wrappers (`github`, `supabase`, `postgres`, `railway`, `vercel`, `cloudflare`) | User | Credentials are account-level |

**Project scope**: `.mcp.json` in project root (committed to git, shared with team).
**User scope**: `~/.claude/.mcp.json` (personal, not committed).

---

## Related Resources

- [AGENTS.md](../AGENTS.md) - MCP Registry Policy (decision tree + 5-question audit)
- [Reverse-Engineering Matrix](../docs/v1.0.0/mcp-reverse-engineering-matrix.md) - Per-server classification + audit
- [Claude Code Guide](CLAUDE_CODE_GUIDE.md) - Complete Claude Code setup
- [Subagents Guide](SUBAGENTS_GUIDE.md) - Agent configuration
