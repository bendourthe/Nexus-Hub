# Security Policy

## Reporting a Vulnerability

If you discover a security vulnerability in DevAI-Hub, please report it by [opening a GitHub issue](https://github.com/bendourthe/DevAI-Hub/issues/new) with the label `security`.

Include:

1. A description of the vulnerability
2. Steps to reproduce
3. Potential impact
4. Suggested fix (if any)

We will respond promptly and aim to provide a fix within **7 days for critical issues**.

## Supported Versions

| Version | Supported |
|---------|-----------|
| 0.8.x   | Yes       |
| < 0.8   | No        |

## Scope

This policy covers:

- **Installer scripts** (`scripts/installer.ps1`, `scripts/installer.sh`) — file copy operations and system path modifications
- **Runtime hooks** (`catalog/hooks/`) — shell scripts executed by Claude Code during sessions
- **VS Code extension** (`extensions/claude-usage-monitor/`) — reads OAuth token from `~/.claude/.credentials.json`
- **Report generator** (`scripts/generate_report.py`) — file I/O and template rendering

Out of scope: the content of Markdown skill files and documentation templates (these contain no executable code).

## Security Considerations

### Hook Scripts

The hooks in `catalog/hooks/` run inside Claude Code sessions with the permissions of the current user. Before installing hooks, review each script to ensure it meets your organization's security requirements.

### OAuth Token Access

The VS Code extension and the `usage-display.sh` hook read your Claude Code OAuth token from `~/.claude/.credentials.json` to query usage data from the Anthropic API. This token is never transmitted to any service other than `api.anthropic.com`.

### Secret Scanning

The `secret-scan.sh` hook (PreToolUse on Write/Edit) scans file content for common secret patterns before Claude Code writes to disk. It does not transmit data anywhere.

## Privacy

DevAI-Hub collects no telemetry, analytics, or usage data. All operations are local to your machine.
