# Agent Permissions and Autonomy: Platform Research

_Last updated: 2026-08-14_

This document separates two permission surfaces that solve different problems. The read-only baseline auto-approves a curated set of low-risk operations on four integrations. The time-bounded autonomy capability temporarily raises one supported project's authority through a verified platform-native mode. An autonomy descriptor does not imply read-only-baseline coverage, and baseline coverage does not imply that a full autonomy mode exists.

The machine-readable source for autonomy verdicts is [`docs/policy/platform-read-contracts.json`](policy/platform-read-contracts.json). Its human-readable table and evidence links are in [`docs/policy/platform-read-contracts.md`](policy/platform-read-contracts.md). The v3.17.0 implementation accepts only JSON, JSONC, or TOML descriptors backed by current first-party documentation.

## Shipped Read-Only Baseline

The baseline remains a four-platform artifact in v3.17.0. Phase 1 hardened its contents to the side-effect level, removed the `jq`-only merge path, made Bash and PowerShell installers use the same merge helper, propagated retired Nexus-Hub rules without deleting user-authored entries, and wired permission installation at both global and workspace scope.

Before that hardening, some entries labelled read-only could mutate local state, remote state, or configuration. Examples included broad dual-mode command globs, mutation-capable `find`, `sed`, `ip`, and `sysctl` shapes, and PowerShell object-returning cmdlets whose methods can mutate. The new validator treats invocation shape and admitted side effects, not a command's name, as the safety boundary.

| Platform | Shipped baseline | Enforcement shape | Important limit |
|---|---|---|---|
| Claude Code | Yes | `allow`, `ask`, and `deny` rules with separate `Bash(...)` and `PowerShell(...)` prefixes | Explicit wildcard redirect behavior remains unverified; built-in read-only commands do receive semantic redirect analysis. |
| OpenAI Codex | Yes | TOML sandbox, filesystem, network, and approval-policy scopes | No equivalent per-command Bash allowlist; containment is sandbox-oriented. |
| Gemini / Antigravity 1.0 | Yes | `run_shell_command(...)` and tool patterns | The shipped set is POSIX-shaped and contains no PowerShell or `cmd.exe` baseline beyond a bare `dir` case. |
| GitHub Copilot | Yes | Instruction-file loading and host settings | The shipped baseline does not provide Claude-style per-command patterns. |
| Other registered integrations | No | None from the baseline | Autonomy coverage was widened separately; read-only-baseline coverage was not. |

## Time-Bounded Autonomy Roster

Only a `MATCH` verdict receives an autonomy descriptor. `DRIFT` means a real lever exists but cannot be represented safely by the current one-file descriptor contract. `UNVERIFIED` means current first-party evidence did not establish a general seedable mode.

| Platform (registry id) | Verdict | Supported tier or tiers | Config scope | Reason |
|---|---|---|---|---|
| Aider (`aider`) | DRIFT | None | Project or global YAML | `yes-always` is YAML-only and has no edits-only tier. |
| Antigravity 1.0 (`antigravity`) | UNVERIFIED | None | UI only | No seedable file path and key were verified. |
| Antigravity 2.0 + CLI (`antigravity2`) | MATCH | Full | Global JSON | `toolPermission: "always-proceed"`; the intermediate mode is broader than edits-only. |
| Claude Code (`claude`) | MATCH | Edits, full | Project-local JSON | `acceptEdits` and `bypassPermissions` are documented modes. |
| OpenAI Codex (`codex`) | MATCH | Edits, full | Trusted-project TOML | Edits retains on-request approval in a workspace-write sandbox; full removes prompts and sandboxing. |
| GitHub Copilot / VS Code (`copilot`) | MATCH | Full | Project VS Code JSON | `chat.permissions.default: "autopilot"`; no edits-only mode value is documented. |
| Cursor (`cursor`) | MATCH | Full | Global JSON | `approvalMode: "unrestricted"`; the documented project file is permissions-only. |
| Gemini Code Assist (`gemini`) | UNVERIFIED | None | Global tool lists | Narrow tool lists exist, but no persistent general autonomy mode was verified. |
| Gemini CLI (`gemini-cli`) | DRIFT | None | Project JSON plus CLI flag | File-backed `auto_edit` exists, but full YOLO is CLI-only, so one descriptor cannot express both tiers. |
| Hermes (`hermes`) | UNVERIFIED | None | Global YAML | Documented gates cover narrow skill and memory writes, not general autonomy. |
| Kimi Code CLI (`kimi`) | MATCH | Full | Global TOML | `default_permission_mode = "auto"`; no project-scoped edits-only value is documented. |
| Nexus-AI (`nexus-ai`) | UNVERIFIED | None | No public contract | No publicly auditable user-facing autonomy setting is available. |
| OpenClaw (`openclaw`) | DRIFT | None | Global JSON5 plus host-local state | Full execution depends on two independent files, so a one-file descriptor would misreport authority. |
| OpenCode (`opencode`) | MATCH | Edits, full | Project-root JSON or JSONC | Per-tool `edit: "allow"` supports edits-only; `permission: "allow"` supports full. |
| Qwen Code (`qwen`) | MATCH | Edits, full | Project JSON | `auto-edit` and `yolo` are documented approval modes. |
| Windsurf (`windsurf`) | UNVERIFIED | None | No confirmed mode file | Current first-party documentation exposes no seedable general permission-mode key. |

**Current count:** 8 MATCH, 3 DRIFT, 5 UNVERIFIED, 16 registered integrations.

Some verified levers are global because that is the only platform-native surface the vendor documents. Nexus-Hub still treats the operation as project-bound: the core requires a project context, a clean non-protected branch, a bounded TTL, a diff and explicit consent, backup and audit records, and exact restoration. A descriptor that declares global scope is rejected by the core rather than silently widening authority.

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

The native path is why broad patterns such as `Bash(find *)`, `Bash(echo *)`, and wildcarded dual-mode PowerShell cmdlets were removed even when a hook could have rejected a dangerous concrete invocation. The hook is defense in depth, not justification for an unsafe native rule. Phase 4 also verified that Claude Code continues to run blocking `PreToolUse` hooks under its no-prompt modes for both Bash and Write tool calls.

## Remaining Coverage Gaps

- The read-only baseline covers four integrations; the other twelve registered integrations receive no Nexus-Hub baseline posture.

- Gemini's baseline has no PowerShell or general `cmd.exe` coverage.

- Claude explicit wildcard-rule behavior for output redirection is still unverified even though the built-in command set handles redirects semantically.

- Aider, Gemini CLI, and OpenClaw have real permission controls that do not fit the one-file descriptor contract. Nexus-Hub skips them instead of approximating their behavior.

- Antigravity 1.0, Gemini Code Assist, Hermes, Nexus-AI, and Windsurf have no currently verified seedable general autonomy mode.

- Cursor and Kimi expose only global full-autonomy levers in current documentation. The v3.17.0 core rejects global-scope descriptors, so descriptor presence does not override the workspace-only product rule.

## Primary Evidence

- [Platform read-contract and autonomy-verification log](policy/platform-read-contracts.md)

- [Phase 1 matcher findings](v3/v3.17/development/permission-matcher-findings.md)

- [Claude Code permissions](https://code.claude.com/docs/en/permissions)

- [OpenAI Codex configuration reference](https://developers.openai.com/codex/config-reference/)

- [VS Code agent approvals](https://code.visualstudio.com/docs/agents/approvals)

- [OpenCode permissions](https://opencode.ai/docs/permissions)

- [Qwen Code settings](https://qwenlm.github.io/qwen-code-docs/en/users/configuration/settings/)
