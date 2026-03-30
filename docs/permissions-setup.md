# Auto-Approve Permissions Setup Guide

## Purpose

DevAI-Hub ships pre-built permission configs that auto-approve safe, read-only operations for four AI coding platforms. This eliminates repetitive approval prompts for file reads, code searches, web lookups, and git history commands, while keeping write operations, destructive commands, and git mutations gated behind approval prompts.

## What Is Auto-Approved

The following categories are auto-approved across all supported platforms:

| Category | Examples | Platforms |
|----------|----------|-----------|
| File reading | Read files, list directories, glob search, grep search | All four |
| Web search | General web search queries | Claude, Gemini |
| Web fetch (trusted domains) | Fetch from ~70 curated documentation and registry domains | Claude, Codex, Gemini |
| Git read-only | `git log`, `git diff`, `git show`, `git status`, `git branch`, `git tag`, `git remote`, `git rev-parse`, `git ls-files` | Claude, Gemini |
| Filesystem read | Read access to project directories | Codex |

## What Is NOT Auto-Approved

These operations always require explicit approval:

- File writes, edits, or creation
- Destructive commands (`rm`, `del`, `format`, etc.)
- Git mutations (`git push`, `git commit`, `git reset`, `git checkout`, `git merge`, `git rebase`)
- Package installs (`npm install`, `pip install`, `dotnet add`, etc.)
- Arbitrary shell execution outside the allowlisted patterns
- Network access to domains not in the trusted list

## Installation

### Via the DevAI-Hub Installer (Recommended)

Permissions are automatically configured during Phase 1 (Global Installation) of the standard installer. No additional steps needed.

```powershell
# Windows
powershell -File scripts/installer.ps1

# macOS / Linux
bash scripts/installer.sh
```

### Standalone Bootstrap

To install or update permissions independently of the full installer:

```powershell
# Preview what would change (no files modified)
.\scripts\Install-DevAI-Permissions.ps1 -DryRun

# Install permissions for all detected platforms
.\scripts\Install-DevAI-Permissions.ps1

# Install for specific platforms only
.\scripts\Install-DevAI-Permissions.ps1 -Platforms CLAUDE,GEMINI

# Revert to pre-installation state
.\scripts\Install-DevAI-Permissions.ps1 -Uninstall
```

## Config Locations After Installation

| Platform | Config File | What Was Modified |
|----------|------------|-------------------|
| Claude Code | `~/.claude/settings.json` | `permissions.allow` array |
| OpenAI Codex | `~/.codex/config.toml` | `approval_policy`, `permissions.default.filesystem`, `permissions.default.network` |
| Google Gemini | `~/.gemini/settings.json` | `tools.allowed` array, `allowedDomains` array |
| GitHub Copilot | VS Code `settings.json` | `github.copilot.chat.codeGeneration.useInstructionFiles` flag |

## How to Customize

### Adding or Removing Trusted Domains

Edit `configs/permissions/trusted-domains.json` in the DevAI-Hub repo, then re-run the installer or standalone bootstrap. Domains are organized by category (code hosting, package registries, language docs, cloud providers, AI/ML, DevOps, Q&A, standards bodies, security advisories, API specs).

To add a domain to a single platform without re-running the installer, edit the platform's config file directly. For Claude Code:

```json
// In ~/.claude/settings.json, add to permissions.allow:
"WebFetch(domain:your-internal-docs.example.com)"
```

### Adding or Removing Auto-Approved Commands

For Claude Code, add entries to `permissions.allow` in `~/.claude/settings.json`:

```json
"Bash(your-custom-command *)"
```

For Gemini CLI, add entries to `tools.allowed` in `~/.gemini/settings.json`:

```json
"run_shell_command(your-custom-command)"
```

For Codex CLI, filesystem and network scoping are configured in `~/.codex/config.toml`. Per-command allowlisting is not supported at the config level.

For Copilot, per-command auto-approve is not supported. Use instruction files (`.github/copilot-instructions.md`) for behavioral guidance.

### Removing All DevAI-Hub Permissions

```powershell
.\scripts\Install-DevAI-Permissions.ps1 -Uninstall
```

This removes only the entries added by DevAI-Hub. Any custom permissions you added manually are preserved.

## Description Box and Permission Interaction

DevAI-Hub uses a `format-bash-description.py` PreToolUse hook that conditionally prepends a bordered description box to Bash commands. Because PreToolUse hooks run before permission evaluation, prepending a description box to every command would cause `Bash(git log *)` style patterns to never match (the matcher would see `# === Description ===...` instead of the actual command).

To solve this, the hook selectively adds the description box only to commands that are NOT in the auto-approve allow list:

1. The hook strips any model-generated description box to recover the actual command
2. It reads allow patterns from all settings levels (global, global-local, project-shared, project-local)
3. For compound commands (`&&`, `||`, `;`), it checks each subcommand independently
4. If ALL subcommands match a configured allow pattern: the hook returns the clean command without the description box, so the permission matcher sees the real command and auto-approves it
5. If any subcommand is not in the allow list: the hook prepends the description box so it is visible in the approval dialog when the user is prompted

### Windows Compatibility

The hook configuration in `settings.json` must use `python` (not `python3`) on Windows, because Python on Windows does not provide a `python3` alias. The PowerShell installer handles this translation automatically. On macOS/Linux, the bash installer uses `python3`.

### Pattern Syntax

Claude Code permission patterns use glob matching with `*` as the wildcard:

| Pattern | Matches |
|---------|---------|
| `Bash(git log *)` | Any command starting with `git log ` |
| `Bash(pwd)` | Exactly `pwd` with no arguments |
| `Bash(cd *)` | Any command starting with `cd ` |

Use space before `*` (current syntax). The legacy colon syntax `Bash(cd:*)` is deprecated; the hook normalises it internally but new entries should use the space format.

## Per-Platform Notes and Limitations

### Claude Code
Full parity. All categories (file reads, search, web fetch with domain scoping, git read-only) are supported with granular allowlisting. This is the most capable permission system of the four platforms.

### OpenAI Codex CLI
Good parity for filesystem and network scoping. Codex uses path-based read/write permissions and a domain allowlist for network access. However, it does not support per-command Bash allowlisting at the config level. The `approval_policy = "on-request"` setting ensures write operations still require approval.

### Google Gemini CLI
Moderate parity. Supports tool-level and shell command patterns (e.g., `run_shell_command(git log)`) plus domain allowlisting. Known limitation: allowlists do not apply to piped commands (upstream issue #11510). No explicit read-vs-write distinction at the config level.

### GitHub Copilot
Most limited. Copilot lacks per-command, per-path, and per-domain allowlisting in persistent configuration. The only safe config option is enabling `useInstructionFiles`, which tells Copilot to respect `.github/copilot-instructions.md` for behavioral guardrails. Blanket auto-approve (`chat.autopilot.enabled: true`) is deliberately NOT set because it cannot distinguish read-only from write operations.

## Uninstall / Revert

The installer creates timestamped backups before modifying any config file (e.g., `settings.json.bak.20260326-143000`). To revert:

1. Run `.\scripts\Install-DevAI-Permissions.ps1 -Uninstall` to remove DevAI-Hub permission entries.
2. Alternatively, restore from backup: copy the `.bak.*` file back to the original filename.
