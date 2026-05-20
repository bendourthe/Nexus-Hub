# Nexus Skill Server (MCP)

> Part of [Nexus-Hub](../../README.md), the skill harness for AI coding assistants. See the parent README for installation and platform coverage.

An MCP (Model Context Protocol) server that enables AI coding assistants to discover and retrieve Nexus-Hub skills through semantic search and tiered content loading.

## Features

- **Semantic skill discovery**: Search 174+ skills by keyword or natural language
- **Tiered loading (L0/L1/L2)**: Fetch one-line summaries, paragraph overviews, or full skill content
- **BM25 keyword search**: Zero-config, zero-dependency search engine
- **Bundle support**: Query role-based skill bundles (e.g., "ai-engineer", "security-specialist")
- **Optional embeddings**: Pluggable providers for semantic search (v0.2)

## MCP Tools

| Tool | Description |
|------|------------|
| `search_skills` | Search skills by query. Returns ranked results at L0, L1, or L2 detail. |
| `get_skill` | Retrieve a specific skill by name at any detail level. |
| `list_categories` | List all skill categories with counts. |
| `list_bundles` | List all role-based skill bundles. |
| `get_bundle` | Get skills in a specific bundle. |

## Setup

### Via Nexus-Hub Installer (recommended)

Run the Nexus-Hub installer. Phase 5 automatically installs the MCP server and registers it in Claude Code.

### Manual Installation

```bash
cd extensions/nexus-skill-server
pip install -e .
```

Add to `~/.claude/settings.json`:

```json
{
  "mcpServers": {
    "nexus-skill-server": {
      "command": "python",
      "args": ["-m", "nexus_skill_server"],
      "env": {
        "NEXUS_HUB_ROOT": "/path/to/Nexus-Hub"
      }
    }
  }
}
```

## Configuration

| Environment Variable | Default | Description |
|---------------------|---------|------------|
| `NEXUS_HUB_ROOT` | (auto-detect) | Path to Nexus-Hub repository root |
| `NEXUS_EMBEDDING_PROVIDER` | `none` | Embedding backend: `none`, `local`, `openai`, `jina`, `voyage` |
| `NEXUS_CACHE_DIR` | `~/.nexus-hub/cache/` | Cache directory for embedding vectors |

## Detail Levels

| Level | Content | Tokens | Use Case |
|-------|---------|--------|----------|
| **L0** | One-line summary | ~10 | Ranking, quick scan |
| **L1** | Paragraph overview with trigger phrases | ~200 | Decide whether to load full skill |
| **L2** | Full SKILL.md content | 500-7000 | Apply the skill to a task |

## Running Tests

```bash
cd extensions/nexus-skill-server
pip install -e ".[dev]"
pytest
```
