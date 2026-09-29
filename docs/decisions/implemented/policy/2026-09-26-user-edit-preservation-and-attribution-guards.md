# Decision: Detect user edits before any overwrite, and block AI attribution on every publishing route

Status: implemented - an always-loaded rule, the user-edit-preservation skill and helper, document-skill revision sections, and two essential hooks shipped in v4.13.1

## Problem

An agent regenerated a deck from its own script and copied it over the user's synced file, erasing the user's slide edit without a word. The v4.13.1 replay reproduced this on the unmodified tree: 3 of 4 before-fix runs lost the user's edit. Nothing told the agent the file had changed since it last wrote it, and nothing stopped a generator script's own copy. Separately, the attribution rule only covered commit messages, while harness defaults add agent co-author trailers and generated-with footers to pull requests, issues, releases, and changelogs.

## Decision

1. **Always-loaded rule.** Every substantive instruction template's `## Autonomous Operation` says to run `edit_guard.py check` from `user-edit-preservation` before changing a file the agent read or wrote, never an ad-hoc comparison, and on a change to keep the user's version, suggest separately, and ask first. `## User Attribution` bans any reference to AI contributions on every surface, even when a harness asks for one.
2. **Procedure skill and helper.** `user-edit-preservation` (in every install profile through `core-developer`) owns the procedure. Its `edit_guard.py` records a per-part fingerprint and an owner-only copy after reads and writes, reports changes (including non-text Office changes), compares with the agent's own copy when there is no record (`diff --against`), and releases a block only through `accept` after a `diff` of the same content.
3. **Document skills revise in place.** Six document skills and `/presentify` carry an `Existing-Deliverable Revision` section; 16 reference save calls are wrapped in `guard_existing()` and `record_saved()`.
4. **Two essential hooks.** `user-edit-guard` (PreToolUse and PostToolUse; blocks outside a git worktree, warns inside; reads scripts the agent runs for document paths; fails closed outside a worktree when it cannot decide) and `attribution-guard` (PreToolUse on git, gh, gh api, and GitHub MCP routes). Both are thin `.sh`/`.ps1` adapters over Python that ships with the install, stay on under the minimal profile, and honor only the user's `NEXUS_DISABLED_HOOKS`.

## Alternatives considered

- **Rule only, no hooks.** Rejected: in the replay, a rule-only run compared timestamps by hand and overwrote a moved picture and notes. The rule is the only protection on hookless platforms, so it stays, but it is not enough alone.
- **Hooks only, no rule or skill.** Rejected: many platforms run no hooks (and two hook-capable adapters do not yet receive these hooks, WN-4), and a hook cannot see a destination computed at run time.
- **Block every write to any existing unrecorded file.** Rejected: inside a git worktree the history already protects the user, and blocking there would stall ordinary development. The hook warns inside a worktree and blocks outside one.
- **Content-hash the whole file.** Rejected: Office AutoSave and sync rewrite `docProps/*` metadata, which would report false changes; fingerprints cover content parts only.
- **Attribution checking by text search anywhere in a body.** Rejected: it would block text that describes the patterns (changelogs, this record). Only trailer- and footer-position attribution blocks; a sentence naming a tool as its subject passes.

## Consequences

Measured and enforced at the v4.13.1 release:

- The replay's final round preserves the user's edit in every run with and without the hook (met: 18 of 18 Claude, 5 of 5 Codex; see `docs/releases/v4/v4.13/development/v4.13.1-incident-replay.md`).
- The agent reports the user's edit in every run (not met: edits made between sessions and moved pictures went unreported; v4.13.1 known gaps WN-1 and WN-2).
- `test_user_edit_guard.py`, `test_attribution_guard.py`, `test_edit_guard.py`, and the hook parity suite pass on bash and Windows PowerShell 5.1.

## Risks

- **A user edit within 5 seconds of the agent's own write** is treated as agent-caused (the settle window for parallel formatter hooks). Accepted; covered by a test that a later edit still blocks.
- **Computed paths, shell-variable destinations, and unrecognized writers** are invisible to the hook (WN-6). Inline `python -c`, `node -e`, and `pwsh -Command` code is read for literal document paths since the Phase 9 deep pass. The rule and skill are the protection for the rest.
- **The owner-only copy store** holds copies of files the agent read, under `~/.nexus-hub/cache/edit-guard`, pruned after 30 days; secret-looking paths and files over 10 MB are fingerprinted without a copy.
