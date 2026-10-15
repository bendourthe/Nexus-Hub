---
name: memory
description: "Run the /memory command. Audit, prune, and manage CLAUDE.md and memory files across the project. Use to \"manage my memory\", \"clean up CLAUDE.md\", \"prune stale memories\", \"audit memory files\", \"reorganize memory\", \"my CLAUDE.md is too big\". SKIP - editing project documentation (use /update docs) or configuring harness settings and hooks (use /update config)."
disable-model-invocation: true
---

# /memory Command

Audit, prune, and reorganize the project's memory surface - CLAUDE.md and the memory files - when they grow too large, accumulate stale information, or need restructuring. `/memory` has no scopes; it runs the full audit-and-propose flow directly.

No catalog skill owns this audit, so the procedure lives here. Pass any remaining arguments (a path or file to focus on) through as the audit scope.

## Procedure

1. **Inventory.** Find every instruction and memory file in scope: `CLAUDE.md`, `AGENTS.md`, `GEMINI.md`, or the active platform's equivalent at the root and in subdirectories, plus the memory directories (`.claude/memory/`, the user-level memory directory, and any agent-memory directory). Report a table of file, location, line count, size, and last-modified date, and flag every file over 200 lines.
2. **Health check.** For each file, list stale entries (they reference files, patterns, or decisions that no longer exist), duplicate entries (the same fact in more than one place), oversized files, and orphaned files (memory for removed features). Verify staleness against the current tree; do not guess.
3. **Recommend.** Propose specific actions: entries to remove, files to split into topic files linked from the main index, entries to consolidate into one authoritative location, and files to archive or delete.
4. **Execute with approval.** Ask before changing anything. Apply only the approved actions, then re-run the inventory and report what changed and the resulting line counts.

Lasting facts recorded in the local persistent agent-memory store are a different surface, owned by the `agent-memory` skill; this command does not edit that store.

## Notes

- This command replaces `/manage-memory` (removed in v3.2.0).
- The `manage-memory` skill this command once delegated to was removed in v3.0.0 without a successor, so the procedure above is the command's own.
