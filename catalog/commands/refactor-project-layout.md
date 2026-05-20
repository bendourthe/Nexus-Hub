---
description: Audit and refactor a repository's root directory to follow standard layout rules — moving files into the correct subdirectories and fixing all references automatically.
---

# Refactor Project Layout Command

Audit a repository's root directory against its declared layout rules, propose a safe reorganization plan, and execute it — moving files, fixing all path references, and verifying that nothing breaks.

This command is safe-first: it never moves or deletes anything until the user explicitly approves the plan in Phase 4.

## Platform Invocation

This command is a Claude Code slash command. On other platforms, invoke the underlying skill directly:

| Platform | How to Invoke |
|----------|---------------|
| **Claude Code** | `/refactor-project-layout` |
| **Codex** | "Refactor the project layout according to the layout rules" (uses `project-layout-refactor` skill) |
| **Gemini CLI** | "Apply the project-layout-refactor skill to clean up the root directory" |
| **GitHub Copilot** | `#file:.claude/skills/project-layout-refactor/SKILL.md` then describe the task |

> On Codex, Gemini, and Copilot, the `project-layout-refactor` skill must first be imported into the platform's skills directory (`.codex/skills/`, `.gemini/skills/`, or referenced via `#file:`). Use `/import-skills` in Claude Code to install it, or copy `catalog/skills/code-cleanup/project-layout-refactor/` manually.

## Phase 1: Load Layout Rules

### 1a. Read Declared Rules

Check for a "Repository Layout Rules" section in these files (in priority order):

1. `CLAUDE.md` (project root) — project-specific overrides
2. `GEMINI.md` (project root) — if present
3. `~/.claude/CLAUDE.md` — user global defaults

Extract each rule as a mapping: `what → where`. Example:

```
installer binaries (install.bat, install.sh, install.exe) → root
DEVLOG.md → docs/DEVLOG.md
JSON catalog files (skills.json, bundles.json, etc.) → data/
community files (README.md, CHANGELOG.md, CLAUDE.md, SECURITY.md, CODE_OF_CONDUCT.md, .gitignore, llms.txt) → root
skills source → catalog/skills/
```

### 1b. Apply Defaults If No Rules Found

If no "Repository Layout Rules" section is found, present these Nexus-Hub defaults and ask the user to confirm or modify before continuing:

```
Proposed default layout rules:

1. Installer binaries (install.bat, install.sh, install.exe, *.msi) → root
2. Development log (DEVLOG.md) → docs/DEVLOG.md
3. Machine-readable catalogs (*.json data files) → data/
4. Community files (README.md, CHANGELOG.md, SECURITY.md, CODE_OF_CONDUCT.md, .gitignore, llms.txt) → root
5. AI instruction files (CLAUDE.md, GEMINI.md, .cursorrules, .copilot-instructions.md) → root
6. Scripts and automation → scripts/
7. Source code → src/

Confirm, or describe changes to these rules before I proceed.
```

Wait for the user's response before continuing.

---

## Phase 2: Inventory Root Files

List every file directly in the root directory (ignore directories). Classify each against the loaded rules.

### Classification Categories

| Category | Description |
|----------|-------------|
| **Stay** | Matched by a "→ root" rule — do not move |
| **Move** | Matched by a rule that names a non-root destination |
| **Ambiguous** | No rule matches — user must decide |

### Output Table

Present the inventory as a table before any analysis:

```
## Root File Inventory

| File | Classification | Proposed Destination | Rule Applied |
|------|---------------|---------------------|--------------|
| README.md | Stay | root | community files rule |
| DEVLOG.md | Move | docs/DEVLOG.md | DEVLOG rule |
| skills.json | Move | data/skills.json | JSON catalogs rule |
| report.py | Ambiguous | ? | No matching rule |
| ... | ... | ... | ... |

Files to move: X
Ambiguous files: Y (requires your input)
```

Resolve ambiguous files by asking the user for each one:

```
report.py — no rule matches this file. Where should it go?
1. Keep at root
2. Move to scripts/
3. Move to src/
4. Specify a custom path
```

---

## Phase 3: Impact Analysis (Safety Check)

For every file that will move, find all references to it across the entire codebase before touching anything.

### Search Strategy

Run targeted searches across these file types: `.md`, `.py`, `.sh`, `.ps1`, `.bat`, `.json`, `.yaml`, `.yml`, `.toml`, `.cfg`, `.ini`, `.txt`

For each file `X` moving from `old-path` to `new-path`, search for these reference patterns:
- Bare filename: `X`
- Relative path: any path ending in `/X` or `./X`
- Root-relative path: `/X`
- Quoted strings: `"X"`, `'X'`
- Markdown links: `](X)`, `](./X)`, `](../X)`

Build a reference map entry for each hit:

```
DEVLOG.md → docs/DEVLOG.md
  References:
  - catalog/commands/generate-devlog.md:123  "DEVLOG.md"  →  "docs/DEVLOG.md"
  - catalog/hooks/auto-devlog.sh:40          DEVLOG="$GIT_ROOT/DEVLOG.md"  →  DEVLOG="$GIT_ROOT/docs/DEVLOG.md"
  - README.md:45                             [DEVLOG](DEVLOG.md)  →  [DEVLOG](docs/DEVLOG.md)
```

### Auto-Fix vs. Manual Review

Mark each reference as:
- **Auto-fix** — a simple string replacement with no ambiguity
- **Manual review** — pattern is complex, context-dependent, or ambiguous (e.g., dynamically constructed paths, regex patterns)

### Impact Summary

```
Impact Analysis:

Files to move:      X
References found:   Y (across Z files)
  Auto-fixable:     Y1
  Manual review:    Y2

Estimated risk: LOW / MEDIUM / HIGH
```

Risk level:
- **LOW** — all references auto-fixable
- **MEDIUM** — 1–5 manual review items
- **HIGH** — 6+ manual review items or references in CI/CD or build configs

---

## Phase 4: Confirmation

Present the complete plan. Do not make any changes until the user explicitly approves.

```
## Refactor Plan

### Files to Move (X total)
| Source | Destination |
|--------|-------------|
| DEVLOG.md | docs/DEVLOG.md |
| skills.json | data/skills.json |
| ... | ... |

### References to Update (Y changes across Z files)

**catalog/commands/generate-devlog.md** (2 changes)
  Line 28:  `DEVLOG.md`          →  `docs/DEVLOG.md`
  Line 123: `"DEVLOG.md"`        →  `"docs/DEVLOG.md"`

**README.md** (1 change)
  Line 45: `[DEVLOG](DEVLOG.md)` →  `[DEVLOG](docs/DEVLOG.md)`

### Manual Review Required (Y2 items)
  [list of items needing human judgment]

Proceed?
1. Yes — execute all changes
2. Partial — let me choose specific files to move
3. No — cancel
```

Wait for explicit approval before proceeding to Phase 5.

---

## Phase 5: Execute

For each approved file move, follow this exact sequence:

1. **Create destination directory** (if it does not already exist)
2. **Copy** the file to its new location
3. **Verify** the copy: confirm the file exists at the destination and has the same byte size as the original
4. **Delete** the original only after verification passes
5. **Log** the action: `✓ Moved: source → destination`

If verification fails at step 3, stop immediately, restore the original, and report the failure before continuing with other files.

After all moves complete, apply reference updates:

For each referencing file:
1. Read the current content
2. Apply the planned string replacements (in order, to avoid cascading conflicts)
3. Write the updated content
4. Log: `✓ Updated: filepath (N references)`

---

## Phase 6: Verify

### 6a. Existence Check

Confirm every moved file exists at its new path and no longer exists at its old path. Report any discrepancies.

### 6b. Stale Reference Scan

Re-run the same grep patterns from Phase 3 against the old paths. Any remaining hits are stale references that were missed.

```
## Verification Results

Files moved:       X / X ✓
References fixed:  Y / Y ✓

Stale references remaining: Z
  [list any remaining hits with file:line context]
```

### 6c. Structural Compliance Check

List the root directory after the refactor and confirm it matches the declared rules. Flag any files that are still misplaced.

### 6d. Git Sanity Check

Run `git status` to confirm:
- Moved files appear as renames (not as deletions + additions where possible)
- No unintended files were modified
- No unintended files were deleted

---

## Phase: Iterative Refinement (Loop)

**CRITICAL**: Stale references can be missed on the first pass.
Perform the following refinement loop up to **3 times**:

1. **Analyze**: Are there any stale references remaining from Phase 6b?
2. **Refine**: If yes, apply targeted fixes to remaining hits.
3. **Stop**: When the stale-reference scan returns zero hits, or after 3 iterations.

After the final iteration, report any references that could not be auto-fixed and require manual attention.

---

## Edge Cases

### Files With the Same Name in Multiple Locations

If moving `DEVLOG.md` from root would conflict with an existing `docs/DEVLOG.md`, stop and ask:

```
docs/DEVLOG.md already exists. How should I proceed?
1. Merge — prepend root DEVLOG.md content above the existing docs/DEVLOG.md
2. Replace — overwrite docs/DEVLOG.md with root DEVLOG.md
3. Keep both — rename the moved file to docs/DEVLOG-root.md
4. Cancel this file move
```

### Binary Files and Non-Text Assets

For non-text files (images, compiled binaries, `.exe`, `.dll`): apply the move-and-verify protocol but skip the reference scan for those file types.

### Files Referenced by CI/CD Pipelines

If a file is referenced in `.github/workflows/`, `Jenkinsfile`, `azure-pipelines.yml`, or similar CI configs, flag these as HIGH priority for manual review — automated pipeline failures are hard to diagnose remotely.

### Monorepos

If the repository has multiple packages under a single root (e.g., `packages/`, `apps/`), apply layout rules only to the true project root unless the user explicitly scopes the refactor to a subdirectory.

---

## Related Commands

- `/update-documentation` — update documentation to reflect the new structure after the refactor
- `/review-codebase` — broader structural review before or after layout changes
- `/setup-project` — establish layout rules for a new project
