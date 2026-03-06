---
description: Audit, prune, and manage CLAUDE.md and memory files across the project. Use when memory files grow too large, contain stale information, or need reorganization.
---
# Memory Management

Audit, prune, and manage CLAUDE.md and memory files to keep project context clean and effective.

## Instructions

You are helping the user manage their Claude Code memory and instruction files. Follow these phases:

### Phase 1: Inventory

Scan and report on all memory-related files in the project:

1. **Find all CLAUDE.md files** in the project tree (root, `.claude/`, subdirectories)
2. **Find all memory files** in `.claude/memory/` and `~/.claude/memory/`
3. **Find agent memory files** in `.claude/agent-memory/` if present
4. **Report a summary table**:

```
| File | Location | Lines | Size | Last Modified |
|------|----------|-------|------|---------------|
```

Flag any files exceeding 200 lines (the auto-injection limit) with a warning.

### Phase 2: Health Check

For each file found, assess:

1. **Size compliance**: Is it under 200 lines? If not, recommend splitting into topic files
2. **Freshness**: Are there entries that reference outdated patterns, removed files, or old decisions?
3. **Duplicates**: Are the same facts recorded in multiple places?
4. **Relevance**: Are entries still applicable to the current codebase state?

Present findings as a categorized list:
- **Stale entries** (reference things that no longer exist)
- **Duplicate entries** (same info in multiple files)
- **Oversized files** (above 200-line limit)
- **Orphaned files** (memory files for removed features)

### Phase 3: Recommendations

Based on the health check, propose specific actions:

1. **Entries to remove** (stale or duplicate)
2. **Files to split** (oversized; suggest topic-based filenames)
3. **Entries to consolidate** (scattered related info)
4. **Files to archive or delete** (orphaned)

### Phase 4: Execute (with approval)

**Ask the user for approval before making any changes.**

For each approved action:
- Remove stale entries
- Split oversized files into topic files linked from the main MEMORY.md
- Consolidate duplicates into a single authoritative location
- Archive or delete orphaned files

After changes, re-run the inventory to confirm compliance.

## Monorepo Considerations

For monorepo projects:
- **Root CLAUDE.md**: Shared conventions, loaded by all sessions
- **Package CLAUDE.md**: Package-specific context, loaded via ancestor walking
- **Memory scoping**: User memory (`~/.claude/`) vs project memory (`.claude/`) vs local memory (`.claude/agent-memory-local/`)

Explain the loading precedence to the user:
1. Ancestor CLAUDE.md files load immediately (walking up from cwd)
2. Descendant CLAUDE.md files load lazily (only when entering that directory)
3. Memory files: user scope (global), project scope (shared), local scope (gitignored)

## Output Format

Present the final report as:

```markdown
## Memory Management Report

### Inventory
[Summary table]

### Issues Found
- [x] 3 stale entries in .claude/memory/MEMORY.md
- [x] 1 oversized file (287 lines)
- [ ] 0 duplicates
- [x] 1 orphaned memory file

### Actions Taken
1. Removed 3 stale entries from MEMORY.md
2. Split MEMORY.md into MEMORY.md (180 lines) + debugging.md (95 lines)
3. Deleted orphaned .claude/memory/old-feature.md

### Current Status
All memory files compliant (under 200 lines, no stale entries).
```
