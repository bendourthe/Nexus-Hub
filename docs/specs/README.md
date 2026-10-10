# Per-Platform Capability Specs

This directory documents, one file per platform, exactly what Nexus-Hub installs onto each supported AI coding assistant and where it lands. Each spec is the human-readable companion to a `scripts/lib/integrations/<platform>.py` subclass: it records the install surface (global and workspace scopes), the distributed content (skills / commands / agents / rules / hooks), the instruction-file location and merge mode, and the platform's known quirks.

These specs are descriptive, not executable. The authoritative behavior lives in the integration subclasses under `scripts/lib/integrations/` and the platform-coverage table in `AGENTS.md`; when an integration's `config` changes, update the matching spec here.

## Platforms

| Spec | Integration key(s) | Distribution tier | Slash surface |
|------|--------------------|-------------------|---------------|
| [claude-code.md](claude-code.md) | `claude` | Full file-tree (original 4) | Yes (`commands/`) |
| [codex.md](codex.md) | `codex` | Full file-tree (original 4) | Yes (`prompts/`) |
| [gemini.md](gemini.md) | `gemini`, `gemini-cli` | Full file-tree (original 4); `gemini-cli` enterprise-only post-2026-06-18 | Yes (`workflows/`) |
| [antigravity.md](antigravity.md) | `antigravity`, `antigravity2` | 1.0 original 4; 2.0 + CLI extended (registry) | Yes (`global_workflows/` / `workflows/`) |
| [copilot.md](copilot.md) | `copilot` | Behavioral guardrails only (`.github/`) | No |
| [cursor.md](cursor.md) | `cursor` | Behavioral guardrails only (`.cursor/rules/`) | No |
| [opencode.md](opencode.md) | `opencode` | Behavioral guardrails (`AGENTS.md`) + skills mirror | No |
| [nexus-ai.md](nexus-ai.md) | `nexus-ai` | Full file-tree (extended, registry) | Yes (`commands/`) |

## Distribution tiers

- **Install mechanism**: every platform installs through the integration registry (`invoke_registry_platform` in `scripts/installer.sh` / `installer.ps1`, dispatching to the subclasses under `scripts/lib/integrations/`). Claude Code is the one platform that also keeps a custom installer block: that block copies its catalog tree, while the registry renders its marker-merged `CLAUDE.md`. No other platform uses installer copy blocks.
- **"Original 4" and "extended" in the table above** are historical labels for when a platform joined the roster (the original Claude, Gemini / Antigravity 1.0, Codex, and Copilot set versus the v2.2.0+ additions). They no longer describe different install mechanisms.
- **What each platform receives** (full file tree, skills-bearing, slash-command-only, or behavioral guardrails only) is defined in the "Platform coverage tiers" section of [`docs/policy/platform-read-contracts.md`](../policy/platform-read-contracts.md), which is re-verified at each release; each spec below records its own platform's surfaces.

## How to read a spec

Each spec has the same sections:

1. **Header** - integration key(s), distribution tier, instruction merge mode.
2. **Install surface** - the global and workspace target directories.
3. **Distributed content** - which catalog subtrees mirror, and under what subdirectory name.
4. **Instruction file** - the rendered instruction file, its template, and whether Nexus-Hub owns the whole file (`dedicated`) or merges into a marker block (`shared`).
5. **Quirks and notes** - platform-specific behavior worth knowing.
6. **Source of truth** - the subclass and config this spec mirrors.

## Source of truth

All eight specs are derived from the live integration `config` dicts (dumped from `scripts/lib/integrations/__init__.py::INTEGRATION_REGISTRY`) and the `AGENTS.md` "Platform coverage caveats" section. They are accurate as of v2.4.0.
