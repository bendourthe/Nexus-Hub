# Claude Code Settings Reference

**Comprehensive reference for the Claude Code settings system**

[Back to Main](../../README.md)

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
| `xhigh` | Extended reasoning with adaptive thinking | Most interactive coding work, balanced intelligence and cost |
| `high` | Strong reasoning at lower aggregate cost than `xhigh` (Nexus-Hub shipped default) | Plan-driven multi-step work, multi-agent fan-out, and long-running loops |
| `max` | Deepest reasoning at highest cost | One-shot hard problems, off-peak analysis - never on loops |
| `medium` | Balanced speed and quality | Tightly scoped or cost-sensitive tasks, general development |
| `low` | Fastest responses | Simple edits, formatting, latency-sensitive interactive work |

The Nexus-Hub installer writes `effortLevel: high` by default, and pins the matching `env.CLAUDE_CODE_EFFORT_LEVEL` alongside it. Both values are **declared** in [`configs/platform-defaults.json`](../../configs/platform-defaults.json), the single source for per-platform install defaults; `catalog/hooks/settings.json` is generated from it and must not be hand-edited (a drift check fails the build if it is). If the value quoted here ever disagrees with that file, the file is right. Because the environment variable is the highest-precedence lever, changing the effort for a single session via the `/effort` command (interactive slider or direct set, e.g. `/effort xhigh`) or the `--effort` CLI flag holds only for that session; edit both keys in your `settings.json` to move your standing default. For the full decision guidance, see the **Effort-Level Strategy** section of [catalog/skills/ai-development/prompt-engineering/SKILL.md](../../catalog/skills/ai-development/prompt-engineering/SKILL.md).

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

### Workflow-phase automation recipe

GitHub Spec Kit's extension system registers per-command lifecycle hooks (18 points: `before_specify`, `after_tasks`, `before_/after_plan`, ...) in a `.specify/extensions.yml` registry. That registry presupposes Spec Kit's third-party extension runtime, which Nexus-Hub deliberately declines (see the v3.6.0 Spec Kit comparison, candidate N1b). Nexus-Hub does **not** add new harness event types and does **not** import that registry. Instead, it approximates the same "run automation at a workflow-phase boundary" intent on the Claude-style event surface it already uses.

The four events relevant to workflow-phase automation are `SessionStart`, `PreToolUse`, `PostToolUse`, and `Stop`. The key idea: in the `/plan`, `/implement`, and `/spec` workflows a phase boundary surfaces as a specific **tool call**, so you key a `PreToolUse` / `PostToolUse` matcher on that tool and let the hook script inspect the tool input to decide whether it is really at a boundary.

| Spec Kit per-command intent | Nexus-Hub equivalent | How |
|---|---|---|
| `before_plan` / `after_plan` | `PreToolUse` / `PostToolUse` on `Write`/`Edit` | Match `Write`/`Edit`; the hook reads `tool_input.file_path` and acts only when it targets a plan artifact (`docs/**/plans/*.md`). |
| `after_tasks` / `after_specify` | `PostToolUse` on `Write` | Same, gated on the `tasks.md` / `spec.md` artifact basename. |
| `after_implement` (phase commit) | `PostToolUse` on `Bash` | Match `Bash`; the hook reads `tool_input.command` and fires on `git commit`. |
| session-level setup/teardown | `SessionStart` / `Stop` | Run once at session start, or at each turn end (for example, a post-phase docs reminder). |

Authoring rules for a workflow-phase hook (mirroring `old-version-docs-guard.sh` and `secret-scan.sh`):

- Be advisory by default: exit 0 and never block a phase. Only escalate to a blocking exit code behind an explicit opt-in env var.
- Read the JSON payload from stdin and extract the field with `jq` (`.tool_input.file_path` / `.tool_input.command`). No-op silently when `jq` is absent.
- Normalize Windows path separators (`\\` to `/`) before matching.
- Honor the standard runtime controls: `NEXUS_DISABLED_HOOKS` (disable by name) and `NEXUS_HOOK_PROFILE=minimal` (skip advisory hooks).

A runnable example ships as `catalog/hooks/workflow-phase-notice.sh` (tested in `catalog/hooks/tests/test_workflow_phase_notice.py`). It emits an advisory marker when a `Write`/`Edit` targets a plan, spec, tasks, or release (`CHANGELOG.md`) artifact, and is silent otherwise. It is registered in the default `catalog/hooks/settings.json` with this `PostToolUse` block:

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Write|Edit",
        "hooks": [
          {
            "type": "command",
            "command": "bash .claude/hooks/workflow-phase-notice.sh"
          }
        ]
      }
    ]
  }
}
```

Because it is advisory only (exit 0, never blocks a phase), it is safe to leave on. Disable it for a session with `export NEXUS_DISABLED_HOOKS=workflow-phase-notice`, or skip all advisory hooks with `export NEXUS_HOOK_PROFILE=minimal`.

This adopts the *discipline* (phase-boundary automation on Nexus-Hub's own hook surface) without adopting Spec Kit's per-command hook *machinery*. See the "lifecycle-hook scope creep" risk note in the v3.6.0 Spec Kit comparison (Section 9) for why the line is drawn here.

### Code-search routing guard

`code-search-routing` is a `PreToolUse` advisory hook for `Grep`, `Glob`, and conservative Bash search patterns. It recommends the local `nexus-code-search` MCP tools before native repository discovery bypasses the index. The Bash matcher covers direct or piped `grep` / `rg`, plus non-destructive `find` commands with name or path predicates; `cat` is treated as search only when its pipeline contains `grep` or `rg`. It never intercepts `Read`, because a prior read is part of the edit-safety contract.

The default is soft: the hook writes the indexed equivalent to stderr and exits 0. Set `NEXUS_CODE_SEARCH_ROUTING=block` to make a matched redirect exit 2, or `NEXUS_CODE_SEARCH_ROUTING_DEBUG=1` to log local matcher decisions. Disable only this hook with `NEXUS_DISABLED_HOOKS=code-search-routing`, or skip it with every advisory hook under `NEXUS_HOOK_PROFILE=minimal`. None of these controls grants access to an index or repository path; they change routing advice only, and native search remains necessary when no index exists or raw filesystem semantics matter.

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Grep|Glob|Bash",
        "hooks": [
          {
            "type": "command",
            "command": "bash .claude/hooks/code-search-routing.sh"
          }
        ]
      }
    ]
  }
}
```

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
