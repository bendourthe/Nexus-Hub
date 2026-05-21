---
description: Audit and refactor a repository's project artifacts (root files, scripts, configs, CI/CD, source layout) to follow standard conventions. Moves misplaced files, fixes all references, archives outdated artifacts tied to prior major versions, and verifies nothing breaks. Use when a repo has too many files in root, scripts/configs/CI are scattered, prior-version project artifacts should be archived, or the project is being prepared for public release.
---

# Refactor Project Command

Audit a repository's project artifacts against its declared layout rules, propose a safe reorganization plan that also archives outdated artifacts tied to prior major versions, and execute it — moving files, fixing all path references, archiving where appropriate, and verifying that nothing breaks.

This command replaces and broadens the former `/refactor-project-layout`. The old name still resolves to this command via a thin alias so existing references continue to work.

This command is safe-first: it never moves, deletes, or archives anything until the user explicitly approves the plan in Phase 5.

## Scope

`/refactor-project` operates across the entire repository **except** the `docs/` tree (which is owned by `/refactor-docs`). It covers:

1. **Root files** — `README.md`, `CHANGELOG.md`, `SECURITY.md`, AI instruction files, installer entry points, lockfiles, ignore files, and any unclassified file at the repo root.
2. **Scripts and automation** — `scripts/`, language-specific build scripts, generators, helpers.
3. **Configs** — `package.json`, `pyproject.toml`, `tsconfig.json`, `.eslintrc`, `ruff.toml`, `Makefile`, `Dockerfile`, lint/format/test runner configs.
4. **CI/CD** — `.github/workflows/`, `Jenkinsfile`, `.gitlab-ci.yml`, `azure-pipelines.yml`, `circleci/`.
5. **Source layout** — top-level shape of `src/`, `lib/`, `app/`, `extensions/`, monorepo package directories.
6. **Archivable artifacts** — release notes, deploy checklists, generated reports, snapshot bundles, and other prior-version artifacts that live outside `docs/`.

## Platform Invocation

| Platform | How to Invoke |
|----------|---------------|
| **Claude Code** | `/refactor-project` (or legacy `/refactor-project-layout`) |
| **Codex / Cursor / Aider** | "Refactor the project layout and archive prior-version artifacts" (uses `project-refactor` skill) |
| **Gemini CLI** | "Apply the project-refactor skill to clean up project structure" |
| **GitHub Copilot** | `#file:.claude/skills/project-refactor/SKILL.md` then describe the task |

> On Codex, Gemini, and Copilot, the `project-refactor` skill must first be imported into the platform's skills directory. Use `/import-skills` in Claude Code to install it, or copy `catalog/skills/code-cleanup/project-refactor/` manually.

## Flags

| Flag | Behavior |
|------|----------|
| *(none)* | Propose-only. Runs Phases 1-4 and stops at the gate. **Default.** |
| `--apply` | After Phase 4, run Phase 5 (gate) -> 6 (execute) -> 7 (verify). |
| `--scope <root\|scripts\|configs\|ci\|src\|all>` | Restrict the refactor to one area. Default `all`. |
| `--archive-prior-versions` | Detect artifacts tied to prior major versions (release notes, deploy checklists, snapshot bundles, generated reports) and propose archiving them under `archive/versions/v<M>/`. Off by default. |
| `--active-version <vSEMVER>` | Override the auto-detected active version (otherwise resolved from `CHANGELOG.md`, latest git tag, or `docs/versions/`). |
| `--no-references` | Skip cross-repo reference repair (use only when the refactor is purely intra-directory and the user is confident no references exist). |

---

## Phase 1: Load Layout Rules and Detect Active Version

### 1a. Read Declared Rules

Check for a "Repository Layout Rules" section in these files (in priority order):

1. `CLAUDE.md` (project root) — project-specific overrides
2. `AGENTS.md` (project root) — canonical agent guidance file
3. `GEMINI.md` (project root) — if present
4. `~/.claude/CLAUDE.md` — user global defaults

Extract each rule as a mapping: `what → where`. Capture rules covering root files, scripts, configs, CI/CD, source layout, and archive locations.

### 1b. Apply Defaults If No Rules Found

If no "Repository Layout Rules" section is found, present these Nexus-Hub defaults and ask the user to confirm or modify:

```
Proposed default layout rules:

1. Community files (README.md, CHANGELOG.md, SECURITY.md, CODE_OF_CONDUCT.md,
   .gitignore, .gitattributes, llms.txt) -> root
2. AI instruction files (CLAUDE.md, AGENTS.md, GEMINI.md, .cursorrules,
   .copilot-instructions.md) -> root
3. Installer binaries (install.bat, install.sh, install.exe, *.msi) -> root
4. Build / lint / test configs (package.json, pyproject.toml, tsconfig.json,
   Makefile, Dockerfile, docker-compose*.yml) -> root
5. Machine-readable catalogs (*.json data files) -> data/
6. Scripts and automation -> scripts/
7. CI/CD pipelines -> .github/workflows/, .gitlab-ci.yml, azure-pipelines.yml
8. Source code -> src/ (or top-level package dirs for monorepos)
9. Development log (DEVLOG.md) -> docs/DEVLOG.md
10. Per-version project artifacts (release notes, deploy checklists, snapshot
    bundles, generated reports) -> archive/versions/v<MAJOR>/v<SEMVER>/ once
    the version is no longer in flight.

Confirm, or describe changes before I proceed.
```

Wait for the user's response before continuing.

### 1c. Detect Active Version

Resolve the active version in this order, stop at the first that succeeds:

1. `--active-version` flag if passed.
2. Most recent `## [X.Y.Z]` heading in `CHANGELOG.md`. Skip `## [Unreleased]`.
3. Latest git tag: `git tag --sort=-v:refname | head -n 1`.
4. Latest canonical `docs/versions/v*/v*/` directory by mtime.
5. Latest legacy `docs/v*/` directory by mtime.
6. Fallback `vUnknown` with explicit user confirmation.

Derive the active major (`vN`). Any project artifact tied to a prior major (`v<M>` where `M < N`) becomes a candidate for archival when `--archive-prior-versions` is set.

---

## Phase 2: Inventory and Classify

List every file in the targeted scope (root + scripts + configs + CI + src layout, minus `docs/` and `.git/`, `node_modules/`, `.venv/`, etc.). Classify each against the loaded rules.

### Classification Categories

| Category | Description |
|----------|-------------|
| **Stay** | Matched by a "→ <its current dir>" rule — do not move |
| **Move** | Matched by a rule that names a different destination |
| **Archive** | Tied to a prior major version (release notes, deploy checklists, generated reports, snapshot bundles) AND `--archive-prior-versions` is set |
| **Ambiguous** | No rule matches — user must decide |

### Detecting prior-version artifacts

A file is **prior-version** when any of these signals apply:

- Filename contains a version string `v<M>.*` (or `<M>.*`) where `M < active_major` (e.g., `RELEASE_NOTES-v1.2.0.md`, `deploy-v0.9-checklist.md`, `report-1.0.0.docx`).
- File body opens with a version banner matching `# Release Notes - v<M>.<N>.<P>` or similar for a prior major.
- File path includes a numeric version segment matching a prior major and the file is not under `docs/` (which is `/refactor-docs`' jurisdiction).

Prior-version artifacts default to **Archive** when `--archive-prior-versions` is set, **Stay** otherwise. Never auto-classify root community files (README, CHANGELOG, SECURITY, etc.) as Archive — these always stay at root regardless of age.

### Output Table

Present the inventory before any analysis:

```
## Project Artifact Inventory

| File | Classification | Proposed Destination | Rule Applied |
|------|---------------|---------------------|--------------|
| README.md | Stay | root | community files rule |
| RELEASE_NOTES-v1.2.0.md | Archive | archive/versions/v1/v1.2.0/RELEASE_NOTES.md | prior-version artifact |
| generate_report.py | Move | scripts/generate_report.py | scripts rule |
| skills.json | Move | data/skills.json | JSON catalogs rule |
| .github/workflows/deploy-v0.yml | Archive | archive/versions/v0/ci/deploy.yml | prior-version artifact |
| custom_helper.py | Ambiguous | ? | No matching rule |

Files to move: X    Files to archive: Y    Ambiguous: Z (requires your input)
```

Resolve ambiguous files by asking the user for each one.

---

## Phase 3: Impact Analysis (Safety Check)

For every file that will move or be archived, find all references to it across the repository before touching anything. Search across `.md`, `.py`, `.sh`, `.ps1`, `.bat`, `.json`, `.yaml`, `.yml`, `.toml`, `.cfg`, `.ini`, `.txt`, and language-specific source files.

For each file, search for these patterns:
- Bare filename
- Relative path: any path ending in `/X` or `./X`
- Root-relative path: `/X`
- Quoted strings: `"X"`, `'X'`
- Markdown links: `](X)`, `](./X)`, `](../X)`
- Import statements (Python: `from X import ...`; JS/TS: `import ... from "X"`; etc.) where applicable

**CI/CD references are HIGH priority**: any reference inside `.github/workflows/`, `Jenkinsfile`, `azure-pipelines.yml`, `.gitlab-ci.yml`, `circleci/config.yml` triggers HIGH risk and is always surfaced for manual review.

Mark each reference as **Auto-fix** (simple string replacement) or **Manual review** (complex, context-dependent, or in CI/CD).

### Impact Summary

```
Impact Analysis:

Files to move:        X
Files to archive:     Y
References found:     Z (across W files)
  Auto-fixable:       Z1
  Manual review:      Z2 (including N CI/CD refs)

Estimated risk: LOW / MEDIUM / HIGH
```

Risk level:
- **LOW** — all references auto-fixable; no CI/CD references
- **MEDIUM** — 1-5 manual review items, no CI/CD references
- **HIGH** — 6+ manual review items OR any CI/CD reference

---

## Phase 4: Stop Here in Propose-Only Mode

If `--apply` was not passed, print a summary and stop:

```
Refactor plan written. To apply, re-run with --apply.

  Move:    X files
  Archive: Y files (to archive/versions/<v>)
  Refs:    Z references queued (W files)
```

In propose-only mode the gate (Phase 5) and execute (Phase 6) phases never run.

---

## Phase 5: Confirmation Gate (only with --apply)

Present the complete plan:

```
## Refactor Plan

### Files to Move (X total)
| Source | Destination |
|--------|-------------|
| generate_report.py | scripts/generate_report.py |
| skills.json | data/skills.json |
| ... | ... |

### Files to Archive (Y total, prior-version artifacts)
| Source | Destination |
|--------|-------------|
| RELEASE_NOTES-v1.2.0.md | archive/versions/v1/v1.2.0/RELEASE_NOTES.md |
| deploy-v0.9-checklist.md | archive/versions/v0/v0.9.0/deploy-checklist.md |

### References to Update (Z changes across W files)
[truncated preview; full list in the propose-only report]

### Manual Review Required (Z2 items, including N CI/CD refs)
[list]

Proceed?
1. Yes — execute all changes
2. Partial — choose Move / Archive / both, exclude specific files
3. No — cancel
```

Wait for explicit approval. On Partial, walk Move and Archive separately.

---

## Phase 6: Execute (only after user confirms)

### 6a. Create archive root if needed

If any file is being archived, ensure `archive/` exists at the repo root and `archive/versions/` exists beneath it. Create `archive/README.md` if absent with a one-paragraph header explaining the layout: `archive/versions/v<MAJOR>/v<SEMVER>/<topic>/<file>`.

### 6b. Apply moves and archives (copy + verify + delete)

For each move/archive operation:

1. Create destination directory if absent.
2. Copy source -> destination.
3. Verify: destination exists AND byte size matches source (sha256 prefix matches for files > 1 KB).
4. If verified, delete source. Otherwise, leave source in place and log the failure.
5. Log: `✓ Moved: <src> -> <dst>` or `✓ Archived: <src> -> <dst>`.

Never use atomic `mv` across directories — networked filesystems can report success silently. Copy + verify + delete is always safe.

### 6c. Apply reference updates

For each referencing file:

1. Read the current content.
2. Apply planned string replacements in order.
3. Write the updated content.
4. Log: `✓ Updated: <file> (N references)`.

Skip Manual-review items; they are surfaced to the user at the end.

---

## Phase 7: Verify

### 7a. Existence Check

Confirm every moved/archived file exists at its new path and no longer exists at its old path.

### 7b. Stale Reference Scan

Re-run the Phase 3 grep patterns against the old paths. Any remaining hits are stale references.

```
## Verification Results

Files moved:        X / X ✓
Files archived:     Y / Y ✓
References fixed:   Z / Z ✓
Stale references:   N
  [list]
```

### 7c. Structural Compliance Check

List the post-refactor directory shape and confirm it matches the declared rules. Flag any remaining misplaced files.

### 7d. CI/CD Sanity Check

For every CI/CD reference that was updated, re-read the file and confirm the substitution succeeded. Where the substitution required Manual review, the file is surfaced for human inspection.

### 7e. Git Sanity Check

Run `git status` to confirm:
- Moves and archives appear as renames where possible (not as deletes + adds).
- No unintended files were modified or deleted.

---

## Phase: Iterative Refinement (Loop)

After Phase 7, perform up to 3 internal review passes:

1. **Analyze**: Are any stale references remaining? Did any CI/CD reference fail to update?
2. **Refine**: Apply targeted fixes; revert archives that turned out to have unresolved external references.
3. **Stop**: When the stale-reference scan returns zero hits, or after 3 iterations.

Surface unresolved items to the user at the end.

---

## Edge Cases

### Conflict at destination

If moving `DEVLOG.md` from root would conflict with an existing `docs/DEVLOG.md`, stop and ask:

```
docs/DEVLOG.md already exists. How should I proceed?
1. Merge — prepend root content above the existing file
2. Replace — overwrite
3. Keep both — rename moved file to docs/DEVLOG-root.md
4. Cancel this file move
```

### Binary files and non-text assets

For non-text files (images, compiled binaries, `.exe`, `.dll`): apply move/archive with verify (size + sha256 prefix) and skip the reference scan for those file types.

### CI/CD files

If a file in `.github/workflows/`, `Jenkinsfile`, `azure-pipelines.yml`, or similar is being moved or archived, flag the operation as HIGH risk. Require explicit user confirmation at Phase 5 for each CI/CD file individually.

### Monorepos

If the repository has multiple packages under `packages/`, `apps/`, or `services/`, apply layout rules only to the true project root unless the user explicitly scopes with `--scope`.

### Prior-version CI/CD pipelines

Workflows specifically scoped to a prior major (e.g., `.github/workflows/release-v0.yml`) qualify as Archive when `--archive-prior-versions` is set. Move target: `archive/versions/v<M>/ci/<file>.yml`. Always require explicit Phase 5 confirmation; never silently archive a workflow file.

### Empty source directory after moves

If a source directory becomes empty after files are moved, ask for explicit confirmation before removing it. Never auto-delete directories.

---

## Related Commands

- `/refactor-docs` — reorganize the `docs/` tree (complementary scope; this command covers everything *outside* docs).
- `/update-documentation` — sync documentation content after a layout change.
- `/update-gitignore` — refresh `.gitignore` after files move into ignored directories.
- `/update-version` — bump version metadata across the repo as part of a release.
- `/review-codebase` — broader structural review before or after layout changes.
- `/setup-project` — establish layout rules for a new project.
