---
name: session
description: "Run the /session command. Manage the development session - resume where you left off, wrap up cleanly at the end, or generate a standalone session-history document. Use to \"continue the session\", \"pick up where we left off\", \"wrap up this session\", \"close out for the day\", \"write the session history\", \"document what we did this session\". SKIP - implementing a plan phase (use /implement) or syncing docs without a session boundary (use /update docs)."
disable-model-invocation: true
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

      continue  -> session-handoff (resume: follow the resume steps for .nexus-hub/handoff.md when it exists) + dev-progress-tracker (read docs/todos.md), then summarize what was in progress and surface the next actions
      wrap-up   -> the wrap-up sequence below (the full end-of-session cleanup, sync, and wrap-up commit flow)
      history   -> session-history (standalone chronological session-history document)

Pass any remaining arguments through unchanged. Heavy logic stays in the retained skills; this file only resolves scope and delegates.

## wrap-up scope

No single skill owns the wrap-up, so it runs these steps in order. Show the planned steps first and let the user drop any of them.

1. **History first**, while the conversation context is live: apply `session-history`.
2. **Hygiene**: `/update gitignore`, then remove debug artifacts and temporary files this session created.
3. **Docs sync**: `/update docs`, then `/update devlog`.
4. **Progress and gaps**: update `docs/todos.md` with `dev-progress-tracker`, and sweep deferred work with `known-gaps-tracker`.
5. **Memory**: `/memory` when instruction or memory files changed this session.
6. **Version (ask first)**: count commits since the last tag, recommend MAJOR / MINOR / PATCH from their conventional-commit prefixes, and run `/update version` only on confirmation.
7. **Commit**: `/update commit` produces the wrap-up commit message.

## Notes

- `history` is also the sub-step the `/implement` per-phase sequence invokes to document each phase; calling `/session history` directly produces the same standalone document on demand.
- This command replaces `/continue-session`, `/wrap-up-session`, and `/generate-session-history` (removed in v3.2.0).
- Keep this dispatcher thin. The session procedures live in the retained skills; this file owns only scope resolution and delegation.
