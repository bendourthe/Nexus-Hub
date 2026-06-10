---
description: Manage the development session - resume where you left off, wrap up cleanly at the end, or generate a standalone session-history document. Use to "continue the session", "pick up where we left off", "wrap up this session", "close out for the day", "write the session history", "document what we did this session". SKIP - implementing a plan phase (use /implement) or syncing docs without a session boundary (use /update docs).
---

# /session Command

Manage the development session boundary. `/session` resumes work from prior context, wraps up a session cleanly (capture history, clean up, sync docs, refresh memory, optionally bump the version, produce a wrap-up commit message), and produces a standalone session-history document. Bare invocation asks for a scope.

This is a thin dispatcher following the contract in [`command-scope-mechanism.md`](../style-guides/command-scope-mechanism.md). The substantive session logic lives in the retained skills; this file resolves scope and delegates.

## Scope resolution

Resolve SCOPE from the first positional argument (`$ARGUMENTS`). Recognized scopes: `continue`, `wrap-up`, `history`.

- If `$ARGUMENTS` names a recognized scope, set SCOPE and skip the menu.
- Otherwise, present this menu and wait for a selection before doing any work:

      What scope?
        1. continue  (recommended) - resume from prior context: what was in progress and what comes next
        2. wrap-up   - end-of-session sequence: history, cleanup, docs sync, memory refresh, optional version bump, wrap-up commit
        3. history   - generate a standalone session-history document for the current (or a reconstructed) session

      Reply with a number or a scope name.

## Delegation

Dispatch the resolved scope to the retained skill:

      continue  -> continue-session (reconstruct prior context and surface the next actions)
      wrap-up   -> wrap-up-session (the full end-of-session cleanup, sync, and wrap-up commit flow)
      history   -> generate-session-history (standalone chronological session-history document)

Pass any remaining arguments through unchanged. Heavy logic stays in the retained skills; this file only resolves scope and delegates.

## Notes

- `history` is also the sub-step the `/implement` per-phase sequence invokes to document each phase; calling `/session history` directly produces the same standalone document on demand.
- This command replaces `/continue-session`, `/wrap-up-session`, and `/generate-session-history` (removed in v3.2.0).
- Keep this dispatcher thin. The session procedures live in the retained skills; this file owns only scope resolution and delegation.
