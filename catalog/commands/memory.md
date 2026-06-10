---
description: Audit, prune, and manage CLAUDE.md and memory files across the project. Use to "manage my memory", "clean up CLAUDE.md", "prune stale memories", "audit memory files", "reorganize memory", "my CLAUDE.md is too big". SKIP - editing project documentation (use /update docs) or configuring harness settings and hooks (use /update config).
---

# /memory Command

Audit, prune, and reorganize the project's memory surface - CLAUDE.md and the memory files - when they grow too large, accumulate stale information, or need restructuring. `/memory` has no scopes; it runs the full audit-and-propose flow directly.

This is a thin dispatcher following the contract in [`command-scope-mechanism.md`](../style-guides/command-scope-mechanism.md). The substantive audit and pruning logic lives in the retained skill; this file only delegates.

## Delegation

Dispatch directly to the retained skill:

      (any invocation) -> manage-memory

The skill audits CLAUDE.md and the memory files, flags stale or oversized entries, proposes a reorganization, and applies changes only after explicit confirmation. Pass any remaining arguments through unchanged.

## Notes

- This command replaces `/manage-memory` (removed in v3.2.0).
- Keep this dispatcher thin. The memory-management procedure lives entirely in the `manage-memory` skill.
