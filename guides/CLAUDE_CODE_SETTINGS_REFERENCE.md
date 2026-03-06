# Claude Code Settings Reference

**Comprehensive reference for the Claude Code settings system**

[Back to Main](../README.md)

---

## Overview

Claude Code uses a 5-level settings hierarchy that controls permissions, model selection, hooks, MCP servers, and UI customization. Settings are merged across levels, with more specific scopes taking precedence.

---

## Settings Hierarchy (Precedence Order)

| Level | Location | Scope | Shared |
|-------|----------|-------|--------|
| 1. CLI flags | Command line | Session | No |
| 2. Project-local | `.claude/settings.local.json` | Project (gitignored) | No |
| 3. Project-shared | `.claude/settings.json` | Project (committed) | Yes |
| 4. User-local | `~/.claude/settings.local.json` | User (private) | No |
| 5. User-global | `~/.claude/settings.json` | User (all projects) | No |

**Merge rules**: Array settings (like permission rules) merge across all levels. Scalar settings use the most specific (highest precedence) value.

---

## Permissions Framework

### Permission Rules

Permissions control which tools Claude Code can use and what operations it can perform. Rules follow an allow/ask/deny model:

```json
{
  "permissions": {
    "allow": [
      "Read",
      "Glob",
      "Grep",
      "Bash(npm run *)",
      "Edit(src/**)",
      "WebFetch(domain:docs.python.org)"
    ],
    "ask": [
      "Bash",
      "Write",
      "Edit"
    ],
    "deny": [
      "Bash(rm -rf *)",
      "WebFetch(domain:*.internal.corp)"
    ]
  }
}
```

### Tool Pattern Syntax

| Pattern | Matches |
|---------|---------|
| `Bash` | All bash commands |
| `Bash(npm run *)` | Bash commands starting with "npm run" |
| `Edit(src/**)` | Edit operations on files under src/ |
| `WebFetch(domain:*.example.com)` | Web fetches to example.com subdomains |
| `mcp__server__tool` | Specific MCP tool |
| `mcp__server__*` | All tools from an MCP server |

### Precedence

- **Deny rules always win** regardless of scope level
- Within the same scope, deny > ask > allow
- More specific patterns override broader ones

---

## MCP Server Configuration

### File Locations

| Scope | File | Use Case |
|-------|------|----------|
| Project | `.mcp.json` | Team-shared servers |
| User | `~/.claude/.mcp.json` | Personal servers |
| Agent | `.claude/agents/NAME.md` (frontmatter) | Agent-specific servers |

### Configuration Format

```json
{
  "mcpServers": {
    "server-name": {
      "command": "npx",
      "args": [
        "package-name@latest"
      ],
      "env": {
        "API_KEY": "value"
      }
    }
  }
}
```

### Transport Types

| Type | Description | Use Case |
|------|-------------|----------|
| `stdio` | Local process (command + args) | Local tools (Playwright, Context7) |
| `http` | Remote HTTP endpoint | Cloud services (Tavily) |

---

## Model Configuration

```json
{
  "model": "claude-sonnet-4-6",
  "smallFastModel": "claude-haiku-4-5"
}
```

### Effort Levels

| Level | Behavior | Use Case |
|-------|----------|----------|
| `high` | Maximum reasoning depth | Complex architecture, debugging |
| `medium` | Balanced speed and quality | General development |
| `low` | Fastest responses | Simple edits, formatting |

Set via `/model` command or `CLAUDE_CODE_EFFORT_LEVEL` environment variable.

---

## Hook Configuration

Hooks are shell commands that run at specific lifecycle events:

### Hook Types

| Type | When It Runs | Use Case |
|------|-------------|----------|
| `PreToolUse` | Before a tool is called | Validation, guards |
| `PostToolUse` | After a tool completes | Formatting, linting |
| `Notification` | When Claude sends a notification | Alerts |
| `Stop` | When a conversation turn ends | Summaries, logging |

### Configuration Format

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "bash .claude/hooks/git-guardrails.sh"
          }
        ]
      }
    ],
    "PostToolUse": [
      {
        "matcher": "Write|Edit",
        "hooks": [
          {
            "type": "command",
            "command": "bash .claude/hooks/auto-format-on-write.sh"
          }
        ]
      }
    ],
    "Stop": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "bash .claude/hooks/usage-display.sh"
          }
        ]
      }
    ]
  }
}
```

### Matcher Patterns

- Empty string `""` matches all events
- Tool name like `"Bash"` matches that specific tool
- Pipe-separated names like `"Write|Edit"` match any listed tool

### Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success (proceed normally) |
| 2 | Block the operation (PreToolUse only) |
| Other | Warning (logged, does not block) |

---

## Sandbox Settings

Control how bash commands are isolated:

```json
{
  "sandbox": {
    "enabled": true,
    "directories": {
      "allow": [
        "/home/user/project",
        "/tmp"
      ],
      "deny": [
        "/etc",
        "/var"
      ]
    }
  }
}
```

---

## UI Customization

### Spinner Verbs

Customize the loading spinner text:

```json
{
  "spinnerVerbs": [
    "Analyzing code",
    "Thinking deeply",
    "Reviewing patterns",
    "Consulting documentation"
  ]
}
```

### Custom Tips

Add project-specific tips that appear in the interface:

```json
{
  "tips": [
    "Use /compact at 50% context to stay efficient",
    "Run /usage to check your remaining limits"
  ]
}
```

### Output Style

```json
{
  "outputStyle": "Explanatory"
}
```

Options: `"Concise"`, `"Explanatory"`, `"Verbose"`

### Auto-Compact

```json
{
  "autoCompactThreshold": 80
}
```

Automatically compact context when usage exceeds the threshold percentage.

---

## Environment Variable Integration

Pass environment variables to Claude Code sessions:

```json
{
  "env": {
    "DATABASE_URL": "postgres://localhost:5432/dev",
    "NODE_ENV": "development"
  }
}
```

---

## Useful Commands

| Command | Description |
|---------|-------------|
| `/config` | View and edit current configuration |
| `/permissions` | Review active permission rules |
| `/mcp` | List configured MCP servers and their status |
| `/model` | Switch model or adjust effort level |
| `--doctor` | Diagnose configuration issues |

---

## Common Configuration Examples

### Development Team Settings

Shared `.claude/settings.json` for a team:

```json
{
  "permissions": {
    "allow": [
      "Read",
      "Glob",
      "Grep",
      "Bash(npm run *)",
      "Bash(pytest *)",
      "Edit(src/**)",
      "Write(src/**)"
    ],
    "deny": [
      "Bash(rm -rf *)",
      "Bash(git push --force*)"
    ]
  },
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "bash .claude/hooks/git-guardrails.sh"
          }
        ]
      }
    ]
  }
}
```

### CI/CD Settings

For automated pipeline use:

```json
{
  "permissions": {
    "allow": [
      "Read",
      "Glob",
      "Grep",
      "Bash(npm test)",
      "Bash(npm run build)",
      "Edit(src/**)"
    ],
    "deny": [
      "Bash(git push*)",
      "Bash(npm publish*)",
      "WebFetch"
    ]
  }
}
```

### Security-Focused Settings

For security-sensitive projects:

```json
{
  "permissions": {
    "allow": [
      "Read",
      "Glob",
      "Grep"
    ],
    "ask": [
      "Bash",
      "Edit",
      "Write"
    ],
    "deny": [
      "WebFetch",
      "Bash(curl *)",
      "Bash(wget *)",
      "Bash(pip install *)"
    ]
  },
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Write|Edit",
        "hooks": [
          {
            "type": "command",
            "command": "bash .claude/hooks/secret-scan.sh"
          }
        ]
      }
    ]
  }
}
```

---

## Related Resources

- [Claude Code CLI Reference](CLAUDE_CODE_CLI_REFERENCE.md) - Command-line flags and environment variables
- [Claude Code Guide](CLAUDE_CODE_GUIDE.md) - Complete Claude Code setup
- [MCP Development Servers](MCP_DEVELOPMENT_SERVERS.md) - MCP server recommendations
