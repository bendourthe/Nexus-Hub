# DevAI Skill Server (MCP)

An MCP (Model Context Protocol) server that enables AI coding assistants to discover and retrieve DevAI-Hub skills through semantic search and tiered content loading.

## Features

- **Semantic skill discovery**: Search 162+ skills by keyword or natural language
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

### Via DevAI-Hub Installer (recommended)

Run the DevAI-Hub installer. Phase 5 automatically installs the MCP server and registers it in Claude Code.

### Manual Installation

```bash
cd extensions/devai-skill-server
pip install -e .
```

Add to `~/.claude/settings.json`:

```json
{
  "mcpServers": {
    "devai-skill-server": {
      "command": "python",
      "args": ["-m", "devai_skill_server"],
      "env": {
        "DEVAI_HUB_ROOT": "/path/to/DevAI-Hub"
      }
    }
  }
}
```

## Configuration

| Environment Variable | Default | Description |
|---------------------|---------|------------|
| `DEVAI_HUB_ROOT` | (auto-detect) | Path to DevAI-Hub repository root |
| `DEVAI_EMBEDDING_PROVIDER` | `none` | Embedding backend: `none`, `local`, `openai`, `jina`, `voyage` |
| `DEVAI_CACHE_DIR` | `~/.devai-hub/cache/` | Cache directory for embedding vectors |

## Detail Levels

| Level | Content | Tokens | Use Case |
|-------|---------|--------|----------|
| **L0** | One-line summary | ~10 | Ranking, quick scan |
| **L1** | Paragraph overview with trigger phrases | ~200 | Decide whether to load full skill |
| **L2** | Full SKILL.md content | 500-7000 | Apply the skill to a task |

## Running Tests

```bash
cd extensions/devai-skill-server
pip install -e ".[dev]"
pytest
```
