# Agent Permission Baseline: Platform Research

_Last updated: 2026-08-15_

This document records the read-only baseline that auto-approves a curated set of low-risk operations on four integrations. It does not change or bypass the approval modes owned by provider extensions or command-line tools.

## Shipped Read-Only Baseline

The baseline remains a four-platform artifact in v3.17.0. Phase 1 hardened its contents to the side-effect level, removed the `jq`-only merge path, made Bash and PowerShell installers use the same merge helper, propagated retired Nexus-Hub rules without deleting user-authored entries, and wired permission installation at both global and workspace scope.

Before that hardening, some entries labelled read-only could mutate local state, remote state, or configuration. Examples included broad dual-mode command globs, mutation-capable `find`, `sed`, `ip`, and `sysctl` shapes, and PowerShell object-returning cmdlets whose methods can mutate. The new validator treats invocation shape and admitted side effects, not a command's name, as the safety boundary.

| Platform | Shipped baseline | Enforcement shape | Important limit |
|---|---|---|---|
| Claude Code | Yes | `allow`, `ask`, and `deny` rules with separate `Bash(...)` and `PowerShell(...)` prefixes | Explicit wildcard redirect behavior remains unverified; built-in read-only commands do receive semantic redirect analysis. |
| OpenAI Codex | Yes | TOML sandbox, filesystem, network, and approval-policy scopes | No equivalent per-command Bash allowlist; containment is sandbox-oriented. |
| Gemini / Antigravity 1.0 | Yes | `run_shell_command(...)` and tool patterns | The shipped set is POSIX-shaped and contains no PowerShell or `cmd.exe` baseline beyond a bare `dir` case. |
| GitHub Copilot | Yes | Instruction-file loading and host settings | The shipped baseline does not provide Claude-style per-command patterns. |
| Other registered integrations | No | None from the baseline | No read-only baseline is shipped. |

## PowerShell Findings

Nexus-Hub has shipped a PowerShell allowlist since v1.1.0. That release established four behaviors that remain part of the security model:

- Claude Code exposes PowerShell as a distinct tool and matches it with a separate `PowerShell(...)` rule prefix.

- A `PreToolUse:PowerShell` hook that returns `updatedInput` without an explicit `permissionDecision` is treated as approval and can execute silently. The analogous Bash path falls through to the default ask behavior. Nexus-Hub therefore returns an explicit decision rather than relying on input rewriting alone.

- The PowerShell approval dialog places `updatedInput` behind a collapsed details surface. Nexus-Hub also writes the explanation to `permissionDecisionReason` so the safety-relevant description remains visible.

- `ForEach-Object` is deliberately absent from auto-approve because property-access and method-invocation forms cannot be separated reliably from syntax alone.

Phase 1 added two matcher conclusions. Claude Code independently evaluates compound commands separated by `;` for both Bash and PowerShell, so every subcommand needs permission. Output redirection is semantically handled for Claude's built-in read-only set, but the documentation does not establish the same behavior for explicit wildcard allow rules; that case remains UNVERIFIED and is tracked as NI-1. Nexus-Hub's own Bash and PowerShell hook paths reject redirects before returning an allow decision.

The Windows-shell coverage gap is platform-specific. Claude receives a dedicated PowerShell ruleset. Gemini's shipped baseline has no PowerShell or `cmd.exe` set, so a Windows Gemini user receives a POSIX-shaped allowlist plus a limited `dir` entry. Adding a Windows-native Gemini baseline is deferred because expanding coverage requires a separate risk decision from hardening existing rules.

## Matcher and Hook Boundaries

Two independent paths can approve an operation:

1. The platform's native matcher reads the merged configuration. Nexus-Hub cannot add semantic checks to this path, so every distributed rule must be safe on its own.

2. Nexus-Hub `PreToolUse` hooks may return an allow decision after additional syntax checks. These hooks reject command separators, redirects, substitutions, multiline forms, and other execution shapes according to their shell-specific contracts.

The native path is why broad patterns such as `Bash(find *)`, `Bash(echo *)`, and wildcarded dual-mode PowerShell cmdlets were removed even when a hook could have rejected a dangerous concrete invocation. The hook is defense in depth, not justification for an unsafe native rule.

## Remaining Coverage Gaps

- The read-only baseline covers four integrations; the other twelve registered integrations receive no Nexus-Hub baseline posture.

- Gemini's baseline has no PowerShell or general `cmd.exe` coverage.

- Claude explicit wildcard-rule behavior for output redirection is still unverified even though the built-in command set handles redirects semantically.

## Primary Evidence

- [Platform read-contract log](policy/platform-read-contracts.md)

- [Phase 1 matcher findings](releases/v3/v3.17/development/permission-matcher-findings.md)

- [Claude Code permissions](https://code.claude.com/docs/en/permissions)

- [OpenAI Codex configuration reference](https://developers.openai.com/codex/config-reference/)

- [VS Code agent approvals](https://code.visualstudio.com/docs/agents/approvals)
