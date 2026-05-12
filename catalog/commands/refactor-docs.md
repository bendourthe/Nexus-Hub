---
description: Audit a project's docs/ folder, classify every file as Cat 1 (delete) / Cat 2 (archive) / Cat 3 (stale-flag) / Cat 4 (active), propose a version-first reorganization with a docs/archive/ subtree, and apply changes only after explicit user confirmation.
---

# Refactor Docs

Audit the project's `docs/` folder, categorize every file by disposition, propose a version-first reorganization with an `archive/` subtree, and apply changes only after the user explicitly approves at a confirmation gate.

This command is safe-first: it **never** moves, deletes, or renames a file until the user explicitly confirms the plan in Phase 7. Propose-only is the default mode.

This command activates the `docs-layout-refactor` skill. The skill carries the categorization heuristics, archive convention, and bundled helper script. The command file carries the phased orchestration and the integration contracts with `/wrap-up-session`, `/update-version`, `/run-deep-review`, and `/review-codebase`.

## Platform Invocation

| Platform | How to Invoke |
|----------|---------------|
| **Claude Code** | `/refactor-docs` |
| **Codex / Cursor / Aider** | "Audit and reorganize the docs/ folder using the docs-layout-refactor skill" |
| **Gemini CLI** | "Run the refactor-docs workflow to categorize and reorganize this project's docs/ tree" |
| **GitHub Copilot** | `#file:.claude/commands/refactor-docs.md` then: "Follow this workflow to audit and refactor docs/" |

---

## Flags

| Flag | Behavior |
|------|----------|
| *(none)* | Propose-only. Runs Phases 0-6 and stops at the gate. **Default.** |
| `--apply` | After Phase 6, run Phase 7 (gate) -> 8 (execute) -> 9 (reference repair) -> 10 (verify). |
| `--mode audit\|full` | `audit` skips the gate entirely (used when chained from `/wrap-up-session`, `/run-deep-review`). `full` is equivalent to `--apply`. |
| `--scope <subpath>` | Restrict analysis to `docs/<subpath>` (e.g., `--scope v0.8.1`). |
| `--output <path>` | Override the report path. Default: `docs/<next-version>/docs-cleanup-report.md`. |
| `--keep-current-version` | Never touch the in-flight version directory. **Default ON.** |
| `--migrate-known-gaps` | After Phase 8, append Cat 3 entries to `docs/<next-version>/known-gaps.md`. |

---

## Category Classification

All findings use the four-category scale defined by the `docs-layout-refactor` skill.

| Cat | Disposition | Required Action |
|-----|-------------|-----------------|
| **Cat 1** | Safe to delete outright | `rm` after confirmation; no reference repair needed |
| **Cat 2** | Archive | Move to `docs/archive/<source-version>/<topic>/<file>.md`; repair inbound refs |
| **Cat 3** | Stale but load-bearing | Leave in place; flag for refresh in the report |
| **Cat 4** | Transient or currently active | No change; revisit in a later run |

---

## Pre-Analysis: Collect Before Writing

Complete all analysis phases (0-5) before writing a single line to the report. Accumulate findings into an internal working set, then emit the report in one pass. This prevents early sections from contradicting later discoveries.

For each file, record:

- **path**: repo-relative POSIX path
- **inventory fields**: size, mtime, mtime_age_days, sha256_prefix, version_dir, topic_dir, extension, line_count, is_binary
- **inbound_refs**: list of `{referrer, line}` pairs from the reference graph
- **category**: Cat 1 / 2 / 3 / 4
- **destination**: archive path (Cat 2) or `(delete)` / `(keep)` / `(flag)`
- **signals_matched**: list of heuristic numbers (1-8) that fired
- **notes**: free-form text for edge cases

**Always exclude from all analysis:**

- `docs/archive/` (already curated; opt-in via `--include-archive` on the helper)
- Symlinks
- The repo's `.git/`, `node_modules/`, `.venv/`, etc. (the helper already excludes these)
- Test fixture files that mention `docs/` patterns deliberately - flag explicitly, do not move

---

## Phase 0: Resolve Scope, Mode, and Output Path

### 0.1 Parse Flags

Read the invocation. Set:

- `mode = "audit"` if `--mode audit`, `"full"` if `--mode full` or `--apply`, else `"propose"` (default).
- `scope = "docs/<subpath>"` if `--scope` else `"docs/"`.
- `output_path` per Phase 0.3 below, or `--output` override.
- `keep_current = True` by default; only `--no-keep-current-version` disables.
- `migrate_known_gaps = True` if `--migrate-known-gaps`.

### 0.2 Detect Active and Next Version

Try in order, stop at the first that succeeds:

1. Most recent version heading in `CHANGELOG.md` (`## [1.2.1]` -> `v1.2.1`). Skip `## [Unreleased]`.
2. Latest git tag: `git tag --sort=-v:refname | head -n 1`.
3. Latest `docs/v*/` directory by mtime.
4. Fallback `vUnknown` only with explicit user confirmation.

Compute the next version: bump MINOR, reset PATCH to 0 (e.g., `v1.2.1` -> `v1.3.0`).

### 0.3 Resolve Output Path

Default: `docs/<next-version>/docs-cleanup-report.md`. If `<next-version>` cannot be resolved, fall back to `docs/docs-cleanup-<YYYY-MM-DD>.md`.

Create the output directory if it does not exist.

### 0.4 Announce the Plan

```
Refactor-docs scope:

  Docs root:        docs/
  Scope:            <full | docs/<subpath>>
  Mode:             <propose-only | apply | audit>
  Active version:   <vX.Y.Z> (from <source>)
  Next version:     <vX.Y+1.0>
  Output:           docs/<next-version>/docs-cleanup-report.md
  Keep active dir:  yes
```

If `mode == "audit"`, also state: "audit-only - the report will be written but no confirmation gate or apply step will run."

---

## Phase 1: Inventory (Tree Fingerprinting)

Invoke the bundled helper:

```bash
python catalog/skills/code-cleanup/docs-layout-refactor/scripts/audit-docs.py \
    inventory \
    --root <docs_root> \
    --repo-root .
```

(On Windows or when Python is missing from PATH, use the `.ps1` wrapper:
`pwsh -File catalog/skills/code-cleanup/docs-layout-refactor/scripts/audit-docs.ps1 inventory ...`)

Capture every NDJSON line into the working set. Each record provides the inventory fields listed in Pre-Analysis.

---

## Phase 2: Reference Graph

Invoke the helper again:

```bash
python catalog/skills/code-cleanup/docs-layout-refactor/scripts/audit-docs.py \
    refgraph \
    --root <docs_root> \
    --repo-root .
```

Output is a single JSON object: `{docs_path: [{referrer, line}, ...]}`. Attach the `inbound_refs` array to each record in the working set.

---

## Phase 3: Categorization

Apply the eight weighted heuristics from the skill (SKILL.md "Step 4 - Categorization"). Signals 2 (external references) and 6 (CHANGELOG citation) are **hard floors**: they can only raise a category, never lower it.

For each record, compute weights, apply the hard floors, and assign Cat 1 / 2 / 3 / 4. Capture the list of signals that fired in `signals_matched`.

### Edge-case overrides (apply after weighted scoring)

| Case | Override |
|---|---|
| `docs/DEVLOG.md` at root | Force Cat 3 if mtime within 60 days. Add "candidate split by version" note if size > 200 KB. |
| File in the active version dir (and `keep_current == True`) | Force Cat 4. |
| File referenced by a skill or command outside `docs/` | Force at least Cat 3. Add `blocked: external reference at <path>:<line>` note. |
| Binary asset (`.png`, `.pdf`, `.xlsx`, etc.) | Cat 1 -> Cat 2 (never delete binaries automatically). |
| File or owning directory cited in `CHANGELOG.md` | Force at least Cat 2. |
| File inside `docs/archive/` | Skip entirely (already curated). |
| Symlink | Skip with warning; never move or delete. |
| Empty version directory | Cat 1 candidate but **requires a second explicit user confirmation** in Phase 8. |

---

## Phase 4: Target-Layout Proposal

For each Cat 2 file, compute the archive destination per the convention documented in [references/archive-layout.md](../skills/code-cleanup/docs-layout-refactor/references/archive-layout.md):

```
docs/archive/<source-version>/<topic>/<file>.md
```

- `<source-version>` = `version_dir` from the inventory.
- `<topic>` = `topic_dir`, or `misc` if the file sits at the version-dir root.
- For top-level docs subdirs (`docs/git/`, `docs/security/`, etc.), the layout is `docs/archive/<top-level-subdir>/<file>.md` (date-keyed exception).

Resolve collisions by suffixing with `-<source-version>` (e.g., `plans/implementation-plan-v0.8.1.md`). Never silently overwrite.

For the active tree, propose any renames or topical regroupings that bring older version dirs in line with the active layout. Mirror the active version's directory shape.

Build a target-tree preview as a Markdown tree block for the report.

---

## Phase 5: Report Generation

Write the report to `output_path`. Required sections:

```markdown
# Docs Cleanup Report — <project> — <YYYY-MM-DD>

**Active version:** <vX.Y.Z>
**Mode:** <propose-only | apply | audit>
**Scope:** <docs/ | docs/<subpath>>
**Report generated by:** /refactor-docs (docs-layout-refactor skill v1.0.0)

## Summary

| Category | Count |
|---|---|
| Cat 1 (delete) | N |
| Cat 2 (archive) | N |
| Cat 3 (stale-flag) | N |
| Cat 4 (active) | N |
| **Total** | **N** |

## Dispositions

| Path | Cat | Signals | Destination | Notes |
|---|---|---|---|---|
| docs/v0.8.1/comparison-foo.md | 2 | 1, 3 | docs/archive/v0.8.1/misc/comparison-foo.md | |
| docs/v0.9.5/comparison-orphan.md | 1 | 4, 8 | (delete) | mtime 220d, no inbound refs |
| docs/v1.1.5/known-gaps.md | 4 | 2 | (keep) | inbound refs from AGENTS.md:312 |
| ... |

## Cat 3 refresh queue

| Path | Why stale | Suggested action |
|---|---|---|
| ... |

## Target tree preview

\`\`\`
docs/
├── DEVLOG.md
├── archive/
│   ├── README.md
│   ├── v0.8.1/
│   │   └── misc/comparison-foo.md
│   └── ...
├── v1.0.0/                # kept (active - 1)
└── v1.1.5/                # kept (active)
\`\`\`

## Self-classification

This report classifies itself as Cat 4 (transient/active). A future
/refactor-docs run will promote it to Cat 2 once <next-version> is no
longer active.
```

The report is always written, in all modes. It is the deliverable in propose-only mode and the audit trail in apply mode.

---

## Phase 6: Stop Here in Propose-Only Mode

If `mode == "propose"`: print a one-line summary to the terminal and stop.

```
Report written to <output_path>.
  Cat 1: N    Cat 2: N    Cat 3: N    Cat 4: N

To apply the plan, re-run with --apply.
```

If `mode == "audit"`: same behavior. The chained command (`/wrap-up-session`, `/run-deep-review`) consumes the report as input.

If `mode == "full"` (`--apply` or `--mode full`): proceed to Phase 7.

---

## Phase 7: Confirmation Gate (only when `mode == "full"`)

Present the full plan to the user. Do not apply any changes until explicit approval.

```
## Proposed Changes

### 1. Archive (Cat 2): N files
   <preview of moves: source -> destination, capped at 15 rows; spill to report>

### 2. Delete (Cat 1): N files
   <preview of deletions, capped at 15 rows; spill to report>

### 3. Flag (Cat 3): N files
   <preview of refresh queue, capped at 10 rows; spill to report>
   (no file mutation; report-only)

### 4. Keep (Cat 4): N files
   (no change)

### 5. Archive root
   <create docs/archive/ and docs/archive/README.md if absent>

### 6. Reference repair
   Inbound references to be rewritten: N (across M files outside docs/)

Proceed?
  1. Yes - apply all changes
  2. Partial - let me select which categories to apply (Cat 1 / Cat 2 separately)
  3. No  - cancel (report already written)
```

Wait for explicit user approval. On Partial, walk Cat 1 and Cat 2 separately.

---

## Phase 8: Execute (only after user confirms)

Apply changes in this order:

### 8a. Create archive root

If `docs/archive/` does not exist, create it. If `docs/archive/README.md` does not exist, write it from the template in [references/archive-layout.md](../skills/code-cleanup/docs-layout-refactor/references/archive-layout.md). If it exists, append new rows to its index table.

### 8b. Move Cat 2 files

For each Cat 2 file, use the **copy + verify + delete** protocol:

1. Determine destination per Phase 4.
2. Create destination directory if absent.
3. Copy source -> destination.
4. Verify: destination exists AND byte size matches source.
5. If verified, delete source. Otherwise, leave source in place and log the failure.
6. Log: `✓ Archived: <source> -> <destination>`.

Append a row to `docs/archive/README.md` index table for each successful move.

### 8c. Delete Cat 1 files

For each Cat 1 file, run the deletion. Log: `✓ Deleted: <path>`.

If a version directory becomes empty after deletions, **ask for a second explicit user confirmation** before removing the empty directory. Never auto-delete empty version dirs.

### 8d. Cat 3 and Cat 4

No file actions. The report already lists them.

### 8e. `--migrate-known-gaps` (only when flag was set)

Append a `## Stale documentation flagged by /refactor-docs` section to `docs/<next-version>/known-gaps.md`. If the file does not exist, create it from the `known-gaps-tracker` skill's template. One bullet per Cat 3 entry, in the format:

```markdown
- **DF-<n>**: `<path>` is stale (signals: <list>). Suggested action: <action from Cat 3 refresh queue>.
```

Match by file path to avoid duplicates. Recompute the Summary table at the top of `known-gaps.md`.

---

## Phase 9: Reference Repair

Re-run `audit-docs.py refgraph` against the new tree.

For every Cat 2 file that moved, rewrite inbound references:

- Markdown links: `[label](docs/v0.8.1/foo.md)` -> `[label](docs/archive/v0.8.1/misc/foo.md)`.
- Raw paths in `.json`, `.yaml`, `.toml`, `.sh`, `.ps1`, `.py`, `.md`: same substitution.

For Cat 1 deletions: refgraph should report zero remaining inbound references. If any persist, surface them and **revert the deletion**. Never leave dangling references.

---

## Phase 10: Verify

Run each binary check. Loop back to Phase 9 up to 3 times on any FAIL.

```
## Verification Results

[ ] No broken internal markdown links
[ ] All originals accounted for (set equality)
[ ] docs/archive/README.md exists and is complete
[ ] No external references to deleted files
[ ] git status mutation count matches plan
[ ] Active-version dir untouched (only report added)
[ ] Report self-classified as Cat 4
```

If any check FAILS after 3 refinement iterations, surface the unresolved items and stop. Do not declare the operation complete.

---

## Phase: Iterative Refinement (Loop)

After Phase 10, perform up to 3 internal review passes:

1. **Analyze**: Are any inbound references still broken? Are any Cat 1 files referenced by surviving files? Is `docs/archive/README.md` consistent with the actual archive tree?
2. **Refine**: Apply targeted reference fixes; revert Cat 1 deletions that turned out to have external refs.
3. **Stop**: When all checks pass, or after 3 iterations.

After the final iteration, surface any items that could not be auto-resolved.

---

## Edge Cases

### Active-version dir contains "stale-looking" files

The active version dir is **always Cat 4** when `--keep-current-version` is on (default). Files there are by definition transient. Re-run `/refactor-docs` after the next version bump and they will be reclassified.

### `docs/archive/` already exists

Treat it as authoritative. Never re-classify anything inside. Append to its `README.md` index rather than rewriting it.

### Two source files target the same archive path

Suffix the older copy with `-<source-version>`. Never silently overwrite.

### File referenced by skills or commands outside `docs/`

Force to Cat 3. Surface the external reference (`<path>:<line>`) in the report. Do not move or delete.

### Project has no `CHANGELOG.md`

Skip signal 6 (CHANGELOG citation) entirely. Note this in the report header. The remaining heuristics still produce a usable classification.

### Project has no version directories

Fall back to topic-based archival. Skip the version-keyed layout for the archive root and use `docs/archive/<topic>/<file>.md`. The Cat 1 deletion list still applies.

### `python` not on PATH

The `.ps1` wrapper detects this and falls back to `py -3` or `python3`. If none are available, surface a clear error: `Python 3.8+ is required to run audit-docs.py`. Do not attempt to walk the docs tree manually - the agent should refuse rather than produce a partial inventory.

### Git repo not initialized

Refgraph still works (it scans files directly, not git index). But the "git status mutation count" verification check will fail. Surface a P2 warning and skip that check.

---

## Related Commands

- `/wrap-up-session` — invokes `/refactor-docs --mode audit` as Step 2c.
- `/update-version` — invokes `/refactor-docs` (propose-only) as Step B4.
- `/run-deep-review` — invokes `/refactor-docs --mode audit` as subsection 4.11.
- `/review-codebase` — optional reference if `docs/` has more than 3 version directories.
- `/refactor-project-layout` — reorganize repo root files; complementary, not overlapping.
- `/update-documentation` — content accuracy; complementary, not overlapping.
- `/generate-changelog` — generate release notes; complementary.
