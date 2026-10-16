# Subagent default usage

**Version**: v4.14.0. **Date**: 2026-10-16. This records the automatic Claude subagent default at both installation scopes and the user controls that retain precedence.

Activation: This is opt-out. The existing Claude installer path copies or updates its template and seeds absent environment keys into `~/.claude/settings.json`, including upgrades that already have `model` and `effortLevel`. Fresh project settings created by `nexus-hub init` also contain `env.CLAUDE_CODE_SUBAGENT_MODEL: sonnet` in `.claude/settings.json`. Init preserves an existing project file. Existing values are retained; a non-object `env` is retained with a warning rather than replaced.

Validation: Read the configured value with the PowerShell commands below. Expect `sonnet` after an applicable global install/upgrade or a fresh project initialization, unless the user already chose a value. These commands inspect configuration; they do not claim that a running session or an explicitly configured agent uses that model.

Rollback: Set `env.CLAUDE_CODE_SUBAGENT_MODEL` to `inherit` in the global file and any project file that declares it, preserving all other keys. Environment `inherit` disables this default. An explicit alternative alias is also retained. Removing the key can allow a later install to seed it again, so `inherit` is the durable opt-out. Removing it only from the project file does not establish that the global default is disabled.

Authority: Installing this value writes configuration and does not itself make a model request or grant tool permissions. Without an independently configured force override, it does not override definition pins or change the built-in Explore and Plan selections. Explicit invocation choices retain their documented precedence. An existing force override can defeat definition pins; Nexus-Hub does not seed it. Availability and configured fallback chains remain provider behavior, not a promise of silent parent-model fallback.

Docs: [Claude subagent model selection](https://code.claude.com/docs/en/sub-agents#choose-a-model), [model environment variables](https://code.claude.com/docs/en/model-config#environment-variables), and [configured fallback chains](https://code.claude.com/docs/en/model-config#fallback-model-chains).

## Quality and cost

The `opus` session baseline is unchanged, and all 23 shipped reasoning-sensitive agents have explicit `opus` definition pins. An unpinned custom agent that previously inherited a higher tier can now use Sonnet, which changes its quality and potential cost. The result depends on its previous model and workload; no measured saving or output-quality equivalence is claimed. Other platform adapters retain their native model selection rather than receiving a Claude-only alias.

## Validation commands

Machine: the user's Windows computer. Terminal: PowerShell 5.1. Directory: the initialized project root. Prerequisites: the applicable global installation and project settings file exist.

```powershell
$globalConfig = Get-Content -LiteralPath (Join-Path $HOME '.claude/settings.json') -Raw -Encoding UTF8 | ConvertFrom-Json
$globalConfig.env.CLAUDE_CODE_SUBAGENT_MODEL
$projectConfig = Get-Content -LiteralPath '.claude/settings.json' -Raw -Encoding UTF8 | ConvertFrom-Json
$projectConfig.env.CLAUDE_CODE_SUBAGENT_MODEL
```

Expected output for new seeded files is `sonnet` on each line. Existing overrides display their own value; an existing project file may omit the key. Start a new Claude Code session to load changed settings. This configuration check does not measure the model used by an authenticated invocation.

## Governance

This automatic default adds no opt-in capability. The plan expressly requires the five-element record above for its opt-out behavior; the current update-command gate otherwise applies to opt-in surfaces. Both requirements are recorded without expanding that gate's policy scope.
