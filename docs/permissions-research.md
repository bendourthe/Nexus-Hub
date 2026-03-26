# Auto-Approve Permissions: Platform Research

_Last updated: 2026-03-26_

This document summarizes how four major AI coding platforms handle permission configuration, auto-approve rules, and tool allowlisting. The goal is to identify the granularity each platform offers and where parity gaps exist.

---

## 1. Claude Code

- **Config path**: `~/.claude/settings.json` (user), `.claude/settings.json` (project), `.claude/settings.local.json` (local, gitignored)
- **Format**: JSON
- **Permission model**: Three-tier rule evaluation: deny > ask > allow (first match wins; deny always takes precedence)
- **Rule types**: `allow`, `ask`, `deny` arrays under the `permissions` key

### Supported rule patterns

| Scope | Example | Notes |
|-------|---------|-------|
| Tool-level | `"Read"`, `"Glob"`, `"Grep"`, `"WebSearch"` | Matches all uses of that tool |
| Command-level | `"Bash(git log *)"`, `"Bash(npm run *)"` | Glob patterns with `*` wildcard |
| Path-level | `"Edit(/src/**/*.ts)"`, `"Read(~/.env)"` | Gitignore-style path patterns |
| Domain-level | `"WebFetch(domain:github.com)"` | Per-domain fetch allowlisting |
| MCP tools | `"mcp__server__tool_name"` | Scoped to a specific MCP server and tool |

### Permission modes

`default`, `acceptEdits`, `plan` (read-only), `auto` (AI-powered safety), `dontAsk`, `bypassPermissions`.

### Assessment

- **Granularity**: Excellent. Supports per-tool, per-command, per-path, and per-domain allowlists.
- **Session persistence**: "Yes, don't ask again" saves rules to `settings.json` permanently.

### Sources

- <https://docs.claude.com/en/docs/permissions>
- <https://docs.claude.com/en/docs/settings>

---

## 2. OpenAI Codex CLI

- **Config path**: `~/.codex/config.toml` (user), `.codex/config.toml` (project, loaded only when trusted)
- **Format**: TOML
- **Permission model**: Named permission profiles with filesystem and network scopes

### Filesystem access

Configured by path with read/write/none levels. Special tokens include `:project_roots` and `:minimal`.

### Network access

Controlled via `enabled`, `mode` ("limited" or "full"), `allowed_domains`, and `denied_domains`.

### Approval policies

Options: `"on-request"` (prompts the user), `"untrusted"` (minimal auto-approval), `"never"` (full auto), or a granular object with per-category toggles (`sandbox_approval`, `rules`, `mcp_elicitations`, `request_permissions`, `skill_approval`).

### Limitations

No per-command Bash allowlisting at the config level. Codex relies on filesystem and network scoping as an alternative to command-level patterns.

### Assessment

- **Granularity**: Good. Filesystem and network concerns are cleanly separated, but there is no command-level pattern matching.

### Sources

- <https://developers.openai.com/codex/config-reference>
- <https://developers.openai.com/codex/agent-approvals-security>

---

## 3. Google Gemini CLI

- **Config path**: `~/.gemini/settings.json` (user), `.gemini/settings.json` (project), enterprise at `/etc/gemini-cli/settings.json` (Linux) or `C:\ProgramData\gemini-cli\settings.json` (Windows)
- **Format**: JSON
- **Permission model**: Tool allowlists for built-in tools and MCP servers

### Supported rule patterns

| Scope | Example | Notes |
|-------|---------|-------|
| Shell command | `"run_shell_command(git status)"` | Pattern-matched command strings |
| Built-in tool | `"ReadFileTool"`, `"code_search"`, `"web_search"` | Full tool name |
| MCP scoping | `includeTools` / `excludeTools` per MCP server | Positive and negative lists |
| Domain | `allowedDomains` array | For browser agent only |

### Enterprise policy

TOML-based policy files in `~/.gemini/policies/` allow organization-wide enforcement.

### Known limitation

Allowlists do not apply to piped commands (tracked in GitHub issue #11510).

### Assessment

- **Granularity**: Moderate. Supports per-tool and command patterns, but shell command patterns are simpler than Claude Code's glob-style matching.

### Sources

- <https://geminicli.com/docs/reference/configuration/>
- <https://google-gemini.github.io/gemini-cli/docs/cli/enterprise.html>

---

## 4. GitHub Copilot (VS Code / CLI)

- **Config paths**:
  - CLI: `~/.copilot/config.json`
  - MCP: `~/.copilot/mcp-config.json`
  - VS Code: `settings.json`
  - Repo (shared): `.github/copilot/settings.json`
  - Repo (local, gitignored): `.github/copilot/settings.local.json`
- **Format**: JSON
- **Permission model**: Runtime CLI flags and VS Code settings toggles

### VS Code settings

| Setting | Purpose |
|---------|---------|
| `chat.tools.terminal.autoApprove` | Auto-approve terminal commands |
| `chat.tools.edits.autoApprove` | Auto-approve file edits |
| `chat.autopilot.enabled` | Enable full autopilot mode |
| `github.copilot.chat.codeGeneration.useInstructionFiles` | Load repo instruction files |

### CLI flags

| Flag | Purpose |
|------|---------|
| `--allow-all-tools` | Approve all tool calls |
| `--allow-tool "git"` | Allow a specific tool |
| `--deny-tool "rm"` | Deny a specific tool |
| `--allow-url "github.com"` | Allow fetch to a domain |

### Autopilot mode

Auto-approves all tool calls, auto-retries errors, and auto-responds to questions (no manual prompts required).

### Limitations

- No persistent per-command config file; relies on VS Code settings and runtime flags.
- No domain allowlisting in persistent config.

### Assessment

- **Granularity**: Limited. Primarily binary auto-approve toggles per tool category with no allowlist-style patterns.

### Sources

- <https://docs.github.com/en/copilot/how-tos/copilot-cli>
- <https://code.visualstudio.com/docs/copilot/agents/agent-tools>

---

## Comparative Summary

| Platform | Config Format | User Config Path | Per-Command Allow | Per-Path Allow | Per-Domain Allow | Read vs Write Distinction | Granularity Rating |
|----------|--------------|------------------|-------------------|----------------|------------------|---------------------------|-------------------|
| Claude Code | JSON | `~/.claude/settings.json` | Yes (glob patterns) | Yes (gitignore-style) | Yes (`WebFetch(domain:...)`) | Yes (separate tool rules) | Excellent |
| Codex CLI | TOML | `~/.codex/config.toml` | No | Yes (filesystem scoping) | Yes (`allowed_domains`) | Yes (read/write/none) | Good |
| Gemini CLI | JSON | `~/.gemini/settings.json` | Partial (simple patterns) | No | Yes (`allowedDomains`) | No | Moderate |
| Copilot | JSON | `~/.copilot/config.json` | No | No | CLI flags only (not persistent) | No | Limited |

---

## Parity Gaps

### Claude Code

No significant gaps. The three-tier deny/ask/allow model with glob patterns, path scoping, and domain allowlisting provides full parity across all permission dimensions.

### Codex CLI

No per-command Bash allowlisting. Users cannot write a rule like "allow `git log` but deny `git push`" at the config level. The workaround is filesystem and network scoping, which controls what the agent can access rather than which commands it can run. This is a deliberate design choice that trades command-level precision for sandbox-style containment.

### Gemini CLI

No read-vs-write distinction at the config level. A tool is either allowed or not; there is no way to permit reading a file while blocking edits to it. Additionally, piped commands bypass allowlists entirely (GitHub issue #11510), meaning a rule like `run_shell_command(git status)` does not cover `git status | head -5`.

### Copilot

The most limited of the four platforms. There is no per-command, per-path, or per-domain allowlisting in persistent configuration. The agent cannot distinguish read-only operations from write operations. CLI flags like `--allow-tool` and `--deny-tool` exist but are session-scoped and not saved to config. Instruction files (`.github/copilot-instructions.md`) are the closest safe equivalent for guiding agent behavior, but they are advisory rather than enforced.
