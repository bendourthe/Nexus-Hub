# Claude Code CLI Flags Reference

**Comprehensive reference for Claude Code command-line flags and environment variables**

[Back to Main](../../README.md)

---

## Overview

Claude Code supports a rich set of command-line flags for controlling behavior, permissions, model selection, and integration with CI/CD systems. Flags are evaluated at startup and override settings from configuration files.

---

## Session Management

| Flag | Description | Example |
|------|-------------|---------|
| `--resume` | Resume the most recent conversation | `claude --resume` |
| `--continue` | Continue a specific session by ID | `claude --continue SESSION_ID` |
| `--print`, `-p` | Non-interactive mode: process input and exit | `echo "explain this" | claude -p` |

---

## Model and Configuration

| Flag | Description | Example |
|------|-------------|---------|
| `--model` | Override the default model | `claude --model claude-sonnet-4-6` |
| `--permission-mode` | Set permission mode (default, plan, bypassPermissions) | `claude --permission-mode plan` |
| `--max-turns` | Maximum number of agent turns | `claude -p --max-turns 10 "fix tests"` |
| `--max-budget-usd` | Maximum budget in USD for the session | `claude --max-budget-usd 5.00` |

---

## Permissions and Security

| Flag | Description | Example |
|------|-------------|---------|
| `--allowedTools` | Comma-separated list of allowed tools | `claude --allowedTools "Bash,Read,Write"` |
| `--disallowedTools` | Comma-separated list of denied tools | `claude --disallowedTools "WebFetch"` |
| `--permission-prompt-tool` | External tool for permission prompts (MCP) | `claude --permission-prompt-tool mcp__auth__prompt` |
| `--dangerously-skip-permissions` | Skip all permission checks (dangerous) | `claude --dangerously-skip-permissions` |

---

## Output and Format

| Flag | Description | Example |
|------|-------------|---------|
| `--output-format` | Output format: `text`, `json`, `stream-json` | `claude -p --output-format json "list files"` |
| `--verbose` | Enable verbose logging | `claude --verbose` |
| `--no-user-input` | Disable all user input prompts | `claude -p --no-user-input "run tests"` |

---

## System Prompt

| Flag | Description | Example |
|------|-------------|---------|
| `--system-prompt` | Override the system prompt entirely | `claude -p --system-prompt "You are a test expert"` |
| `--append-system-prompt` | Append to the default system prompt | `claude -p --append-system-prompt "Always use pytest"` |

---

## Agent and Subagent

| Flag | Description | Example |
|------|-------------|---------|
| `--agent` | Run a specific named agent | `claude --agent my-custom-agent` |
| `--subagent-model` | Override the model used for subagents | `claude --subagent-model claude-haiku-4-5` |

---

## MCP and Plugins

| Flag | Description | Example |
|------|-------------|---------|
| `--mcp-config` | Path to MCP configuration file | `claude --mcp-config ./custom-mcp.json` |
| `--plugin` | Enable a plugin by name | `claude --plugin my-plugin` |

---

## Directory and Workspace

| Flag | Description | Example |
|------|-------------|---------|
| `--cwd` | Set the working directory | `claude --cwd /path/to/project` |
| `--add-dir` | Add additional working directories | `claude --add-dir /docs --add-dir /tests` |

---

## Budget and Limits

| Flag | Description | Example |
|------|-------------|---------|
| `--max-budget-usd` | Maximum spend for the session in USD | `claude --max-budget-usd 2.50` |
| `--max-turns` | Maximum number of agent turns | `claude -p --max-turns 5 "quick fix"` |

---

## Integration

| Flag | Description | Example |
|------|-------------|---------|
| `--ci` | CI mode: non-interactive with JSON output | `claude --ci "run all tests"` |
| `--headless` | Headless mode for programmatic use | `claude --headless --output-format json` |

---

## Key Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `ANTHROPIC_API_KEY` | API key for direct API access | (none) |
| `CLAUDE_CODE_EFFORT_LEVEL` | Set reasoning effort: `high`, `medium`, `low` | `high` |
| `CLAUDE_CODE_MAX_OUTPUT_TOKENS` | Maximum output tokens per response | (model default) |
| `CLAUDE_CODE_USE_BEDROCK` | Use AWS Bedrock as the backend | `false` |
| `CLAUDE_CODE_USE_VERTEX` | Use Google Vertex AI as the backend | `false` |
| `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS` | Enable experimental agent teams feature | `false` |
| `DISABLE_AUTOUPDATER` | Disable automatic updates | `false` |
| `CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC` | Disable telemetry and non-essential network calls | `false` |

---

## Common Usage Patterns

### CI/CD Integration

Run Claude Code in a CI pipeline with budget controls and non-interactive mode:

```bash
claude -p --ci --max-budget-usd 1.00 --max-turns 20 "Run tests and fix any failures"
```

### Headless Operation

Use Claude Code programmatically with JSON output:

```bash
echo "Analyze this codebase for security issues" | claude -p --headless --output-format json --no-user-input
```

### Budget-Controlled Runs

Limit spending for exploratory tasks:

```bash
claude --max-budget-usd 0.50 --max-turns 10
```

### Multi-Directory Workspaces

Work across multiple directories simultaneously:

```bash
claude --add-dir ../shared-libs --add-dir ../docs "Update shared library references"
```

### Model Selection for Cost Optimization

Use faster, cheaper models for simple tasks:

```bash
claude --model claude-haiku-4-5 -p "Format this JSON file"
```

Use the strongest model for complex reasoning:

```bash
claude --model claude-opus-4-6 "Design a new authentication system"
```

### Custom System Prompt for Specialized Tasks

```bash
claude -p --append-system-prompt "You are a security auditor. Flag all potential vulnerabilities." "Review src/"
```

---

## Flag Precedence

Command-line flags have the highest precedence, overriding all configuration files:

1. **CLI flags** (highest)
2. Project-local settings (`.claude/settings.local.json`)
3. Project-shared settings (`.claude/settings.json`)
4. User-local settings (`~/.claude/settings.local.json`)
5. User-global settings (`~/.claude/settings.json`)

---

## Related Resources

- [Claude Code Settings Reference](CLAUDE_CODE_SETTINGS_REFERENCE.md) - Settings hierarchy and configuration
- [Claude Code Guide](CLAUDE_CODE_GUIDE.md) - Complete Claude Code setup
- [MCP Development Servers](MCP_DEVELOPMENT_SERVERS.md) - MCP server recommendations
