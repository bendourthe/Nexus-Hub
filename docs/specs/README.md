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

- **Original 4** (legacy installer copy blocks): Claude Code, Gemini / Antigravity 1.0, Codex, GitHub Copilot. These install via the explicit copy blocks in `scripts/installer.sh` / `installer.ps1` and also have a registry subclass standing by for the parity migration tracked in `docs/archive/v2/v2.1/known-gaps.md` (DF-001).
- **Extended** (v2.2.0+, via the integration registry under `scripts/lib/integrations/`): Antigravity 2.0 + CLI, Gemini CLI (enterprise-only post-2026-06-18), Nexus-AI.
- **Behavioral guardrails only**: Cursor (`.cursor/rules/*.mdc` + repo-root `AGENTS.md`) and OpenCode (`AGENTS.md`) receive instruction-file guidance rather than a full per-file catalog copy (OpenCode additionally mirrors `skills/`).

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
