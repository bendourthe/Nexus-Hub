# Decision: One platform-neutral owner for the project-root AGENTS.md block

Status: proposed - supported Claude Code project sessions consume a shared `AGENTS.md` block written once from `templates/ai-instructions/base-agents.md`, and every unknown case keeps the managed `CLAUDE.md`

## Problem

Claude Code v2.1.277 and later can read a repository's `AGENTS.md` in place of `CLAUDE.md`. Nexus-Hub still wrote a project `CLAUDE.md` for Claude and, separately, a project-root `AGENTS.md` for Codex, Cursor, OpenCode, Antigravity 2.0, OpenClaw, and Windsurf, each from its own template and all into the same marker block. A user of Claude and one other tool therefore carried two near-identical managed bodies, and the root block's content depended on which integration installed last.

## Decision

- Add `templates/ai-instructions/base-agents.md`, a platform-neutral body, as the single template for the project-root `AGENTS.md` block. A section-by-section inventory (`docs/releases/v4/v4.15/development/v4.15.2-shared-agents-inventory.md`) shows the only platform-specific line in the Codex, Cursor, and OpenCode templates was a skills-folder pointer; the shared body names each tool's own skills folder generically.
- Codex, Cursor, OpenCode, and Claude (on its supported path) are consumers. Each records itself in the install manifest's shared list; a teardown removes the block only when no other consumer remains.
- Claude decides its path from a recorded capability decision (`.nexus-hub/claude-instruction-decision.json`): version floor (2.1.277, or 2.1.281 for hosted and telemetry-off surfaces), the effective `instructionFiles` value from user and managed settings (never project settings), a disabled built-in reader, and any `CLAUDE.md` in the working directory or above. On the AGENTS.md path Claude writes no project `CLAUDE.md` and keeps its Claude-only sections in a native `.claude/rules/` sidecar. Every unknown, unreadable, conflicting, or blocked input selects `CLAUDE.md`.
- Existing project `CLAUDE.md` files are never removed implicitly. An explicit `NEXUS_HUB_CLAUDE_MIGRATE=1` removes only the managed block: a managed-only file is deleted, a mixed file keeps every user byte and stays on `CLAUDE.md` precedence, a user-authored file is untouched.
- Antigravity 2.0, OpenClaw, and the Windsurf root file keep their own writers. Their platform-specific content has no verified sidecar or global owner, so migrating them would drop content; this is recorded as a blocked migration, not silently fixed.

## Consequences

A fresh supported Claude project install produces one managed project body. A repository that already has a `CLAUDE.md` is unchanged and is reported as unresolved precedence rather than converged. The convergence is "converged with documented exceptions": four vendor-documented differences remain (see `docs/policy/platform-read-contracts.md`, 2026-11-15). The shared body is a second copy of universal text that also lives in the per-platform templates; the template parity guard and the shared-resource tests hold them together.

## Alternatives considered

- **Detect the Claude path only and leave the other writers alone.** Rejected: the competing writers and the teardown ambiguity (one integration removing a block another still needs) remain.
- **Symlink `CLAUDE.md` to `AGENTS.md`.** Rejected: the vendor documents that Edit and Write refuse to write through a symlink and that Windows clones can check a symlink out as plain text.
- **Write a `CLAUDE.md` containing `@AGENTS.md`.** Rejected for fresh supported installs because it keeps the second file the change exists to remove; it remains the documented option for sessions that cannot read `AGENTS.md` directly.
- **Seed `instructionFiles` in project settings.** Rejected: the vendor ignores the key in project and local settings, and the default already matches.
- **Migrate every root writer in one step.** Rejected: three of them carry platform-specific guidance with no reachable owner, and dropping it would be a silent regression.
- **Do nothing.** Rejected: it leaves duplicate bodies and last-writer-wins content in the shared block.
