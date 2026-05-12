---
description: Guide the user through a comprehensive version upgrade following semantic versioning, including project cleanup, layout refactoring, gitignore audit, documentation sync, and changelog generation.
---
# Update Version Command

Guide the user through a comprehensive version upgrade following semantic versioning. This command acts as a release preparation orchestrator: it cleans up the project structure, audits tracked files, bumps the version, updates all documentation, and validates consistency before producing a ready-to-commit result.

## Instructions

You are helping the user prepare a release. Follow these phases systematically. Each phase builds on the previous one; do not skip phases unless explicitly noted.

---

## Phase A: Analysis and Planning (read-only, no changes yet)

### Step A1: Determine Target Version

Accept one of:
- **Version type**: "PATCH", "MINOR", or "MAJOR"
- **Direct version**: e.g., "0.2.2", "1.0.0", etc.

If the user has not specified, ask:

```
What type of changes are you releasing?

Options:
1. PATCH (bug fixes, docs) - X.Y.Z → X.Y.(Z+1)
2. MINOR (new features, non-breaking) - X.Y.Z → X.(Y+1).0
3. MAJOR (breaking changes) - X.Y.Z → (X+1).0.0

Or specify a direct version number (e.g., "0.2.2")
```

If user specifies a direct version, use that. If they specify a type, calculate the new version.

### Step A2: Identify Current Version

Find the current version in the project:

```
Check these locations:
- pyproject.toml (version = "X.Y.Z")
- package.json (version field)
- CHANGELOG.md (latest version header)
- README.md (version in header/badge)
- Source code (__version__, VERSION constant)
```

Also find the last git tag:
```bash
git describe --tags --abbrev=0
```

Tell the user: "Current version found: X.Y.Z. New version will be: A.B.C"

### Step A3: Analyze Git Changes (Auto-Analysis)

**IMPORTANT**: Automatically analyze changes since the last release. Do NOT ask the user to describe changes.

1. Find commits since last tag:
```bash
git log {last_tag}..HEAD --oneline --no-merges
```

2. Get detailed file changes:
```bash
git diff {last_tag}..HEAD --stat
```

3. For each commit, analyze the commit message and changed files to categorize:
   - **Added**: New features, new files, new functionality
   - **Changed**: Modifications, improvements, refactoring
   - **Fixed**: Bug fixes, corrections
   - **Removed**: Deleted features, deprecated code removal

4. Generate proposed CHANGELOG entries from this analysis.

### Step A4: Present Proposed Changes

Show the user the auto-generated CHANGELOG entries:

```markdown
## Proposed CHANGELOG for [NEW_VERSION]

### Added
- [Auto-detected additions]

### Changed
- [Auto-detected changes]

### Fixed
- [Auto-detected fixes]

### Removed
- [Auto-detected removals]
```

Ask: "Does this accurately reflect the changes? I can adjust any entries before proceeding."

Wait for user confirmation before continuing.

---

## Phase B: Cleanup and Housekeeping (structural changes, pre-version-bump)

These steps ensure the project structure and git tracking are clean before the version bump. This prevents the release commit from including misplaced files or artifacts.

### Step B1: Refactor Project Layout

Run the full `/refactor-project-layout` workflow to audit the root directory against declared layout rules and move misplaced files to their correct locations.

**Process** (follows the refactor-project-layout command):

1. **Load layout rules** from `CLAUDE.md`, `GEMINI.md`, or user global defaults.
2. **Inventory root files** and classify each as Stay, Move, or Ambiguous.
3. **Impact analysis**: For every file that will move, find all references across the codebase. Map old paths to new paths.
4. **Present the refactor plan** to the user. Wait for explicit approval before moving any files.
5. **Execute**: Move files, update all references, verify moves completed correctly.

If no files need moving (layout is already clean), explicitly state this and proceed to B2.

**Skip condition**: If the user says "skip layout refactor" or the project has no declared layout rules, skip this step.

### Step B2: Verify Refactor Integrity

After any file moves in B1, verify that nothing is broken:

1. **Build/test check**: If the project defines build or test commands (in `CLAUDE.md` Key Commands, `package.json` scripts, `pyproject.toml`, `Makefile`, etc.), run them and confirm they pass.
2. **Script executability**: For shell scripts (`.sh`, `.bash`) and PowerShell scripts (`.ps1`) that were moved or had references updated, confirm they exist at the new path and have correct permissions.
3. **Internal link validation**: Scan all Markdown files for relative links (`](path)`, `](./path)`) and confirm each target file exists.
4. **Import/require resolution**: For source code files that had path references updated, verify the imports or requires still resolve (language-dependent: check Python imports, JS/TS requires, Go imports, etc.).
5. **Installer dry-run**: If the project has installers (`install.sh`, `install.bat`, `installer.ps1`), run a dry-run or syntax check to confirm they are not broken.

**If any check fails**: Stop, report the failure with the specific file and error, fix the broken reference, and re-verify before proceeding.

If B1 was skipped (no files moved), skip B2 as well.

### Step B3: Update .gitignore

Run the full `/update-gitignore --fix` workflow to audit tracked files and clean up the git index. The `--fix` flag tells the sub-command to apply approved changes automatically rather than producing a report-only audit.

**Process** (follows the update-gitignore command):

1. **Codebase fingerprinting**: Detect languages, frameworks, and build tools.
2. **Audit current `.gitignore`**: Compare existing patterns against recommended patterns for the detected stack.
3. **Tracked file analysis**: Identify files that should not be tracked (secrets G0, build artifacts G1, IDE/OS metadata G2, LFS candidates G3).
4. **Untracked file analysis**: Identify untracked files that need ignore patterns.
5. **Present findings** with severity classification.
6. **Apply fixes** after user approval: Add missing `.gitignore` patterns, run `git rm --cached` for wrongly-tracked files.

If the `.gitignore` is already comprehensive and no wrongly-tracked files are found, explicitly state this and proceed.

**Skip condition**: If the user says "skip gitignore audit", skip this step.

### Step B4: Reorganize `docs/`

Run the full `/refactor-docs` workflow (propose-only by default; the command's own confirmation gate decides what gets applied).

**Process** (follows the refactor-docs command):

1. **Inventory**: walk `docs/` and emit a per-file manifest (path, size, mtime, sha256 prefix, version dir, topic dir).
2. **Reference graph**: scan the repo outside `docs/` for inbound references to each docs file.
3. **Categorize**: assign Cat 1 (delete) / Cat 2 (archive) / Cat 3 (stale-flag) / Cat 4 (active) using eight weighted heuristics. Signals 2 (external references) and 6 (CHANGELOG citation) are hard floors.
4. **Propose**: build a target tree under `docs/archive/<source-version>/<topic>/` for Cat 2 items.
5. **Confirm**: present the plan at the gate. User picks Y / Partial / N.
6. **Execute** (on approval): create `docs/archive/`, move Cat 2 with copy-verify-delete, delete Cat 1, leave Cat 3 in place with a refresh flag.
7. **Repair references**: rewrite inbound links to moved files.
8. **Verify**: seven binary checks; loop up to 3 times on residual breakage.

The report lands at `docs/<next-version>/docs-cleanup-report.md` regardless of whether the apply step ran. On user rejection at the gate, skip Step B4's apply and continue to the Phase B summary; the audit report is still preserved.

**Skip condition**: If the user says "skip docs cleanup", skip this step.

### User Confirmation Gate (after Phase B)

After completing B1-B4, present a summary of all structural changes:

```markdown
## Phase B Summary: Cleanup Complete

### Layout Refactor
- Files moved: X (list each: old → new)
- References updated: Y (across Z files)
- Verification: PASSED / FAILED [details]

### Gitignore Audit
- Patterns added: X
- Files removed from index: Y
- Severity breakdown: G0: _, G1: _, G2: _, G3: _

### Docs Cleanup
- Cat 1 deleted: X
- Cat 2 archived: Y (under docs/archive/)
- Cat 3 flagged for refresh: Z (no file action)
- Reference repairs: W (across V files)
- Verification: PASSED / FAILED [details]

Proceed to version bump?
```

Wait for explicit user approval before continuing to Phase C.

---

## Phase C: Version Bump (the core version change)

### Step C1: Update Configuration Files

Update the version in all config files:

**Python (pyproject.toml)**:
```toml
[project]
version = "NEW_VERSION"
```

**JavaScript (package.json)**:
```json
{
  "version": "NEW_VERSION"
}
```

**Source Code**:
```python
__version__ = "NEW_VERSION"
```

Update all locations identified in Step A2.

### Step C2: Update CHANGELOG.md

Update the changelog following the [Keep a Changelog](https://keepachangelog.com/en/1.0.0/) format:

1. **If an `[Unreleased]` section exists**: Convert it to the new version header `## [NEW_VERSION] - YYYY-MM-DD` and create a fresh empty `[Unreleased]` section above it.
2. **If no `[Unreleased]` section exists**: Insert the new version entry below the file header.
3. Use the approved content from Step A4 for the entry body.
4. Only include category subsections (`### Added`, `### Changed`, `### Fixed`, `### Removed`) that have entries. Do not include empty sections.
5. Add `---` horizontal rules between version sections for readability.
6. **Update footer comparison links** (if the project uses GitHub):
   - Update the `[Unreleased]` link to compare from the new version tag to HEAD
   - Add a new comparison link for the new version vs. the previous version

```markdown
## [Unreleased]

---

## [NEW_VERSION] - YYYY-MM-DD

### Added
- [Features from Step A4]

### Changed
- [Modifications from Step A4]

### Fixed
- [Bug fixes from Step A4]

---

## [PREVIOUS_VERSION] - YYYY-MM-DD
...
```

**Footer links** (if GitHub remote detected):
```markdown
[Unreleased]: https://github.com/owner/repo/compare/vNEW_VERSION...HEAD
[NEW_VERSION]: https://github.com/owner/repo/compare/vPREVIOUS_VERSION...vNEW_VERSION
```

Use today's date in YYYY-MM-DD format.

### Step C3: Update README.md

Update version references in README and add or update the "What's New" section:

```markdown
# Project Name - vNEW_VERSION

## What's New in Version NEW_VERSION
- [Key highlights from CHANGELOG — top 3-5 most significant items]
```

Use the top 3-5 most significant items from the CHANGELOG for "What's New". If a "What's New" section already exists, replace its content. If it does not exist, add it in a prominent location (after the project description, before installation instructions).

### Step C4: Update Help/About Menus (if applicable)

Check for version displays in:
- CLI help messages
- GUI about dialogs
- API version endpoints
- Documentation headers

Update any found version references to the new version.

---

## Phase D: Documentation Sync (post-version-bump, reflects final state)

These steps ensure all documentation reflects the new version, moved files, and new features.

### Step D1: Update Documentation

Run the full `/update-documentation` workflow to audit and fix all documentation files.

**Process** (follows the update-documentation command):

1. **Discover and classify** all documentation files (READMEs, guides, manuals). Exclude CHANGELOG.md, DEVLOG.md, command definitions, skill definitions, and templates.
2. **Build ground truth** from the current codebase: project structure, dependencies, features, architecture.
3. **Compare documentation vs. reality**: Check structure accuracy, feature accuracy, installation/setup accuracy, API/config accuracy, internal links, and stale references.
4. **Present findings** with severity classification (Critical, High, Medium, Low).
5. **Update affected files** after user approval: targeted edits to fix inaccuracies, add missing sections, fix stale paths and broken links.

This step catches documentation that became stale due to:
- Files moved in Phase B (new paths not reflected in docs)
- New features added since the last release
- Removed or renamed features
- Changed configuration or API surfaces

If all documentation is already accurate, explicitly state this.

### Step D2: Update DEVLOG

Run the full `/update-devlog` workflow to generate a comprehensive release entry.

**Process** (follows the update-devlog command):

1. **Analyze context**: Read existing `docs/DEVLOG.md`, analyze git history since the last entry, and review all changes made in this release preparation (Phases B through D1).
2. **Synthesize entry**: Create a comprehensive entry that captures:
   - The release goal and scope
   - Structural changes (layout refactor, gitignore cleanup)
   - Feature changes (from the CHANGELOG)
   - Documentation updates
   - Lessons learned and notable decisions
3. **Append** the entry to `docs/DEVLOG.md`, matching the existing format and tone.

The DEVLOG entry should capture the "why" and "how" behind the release, not just repeat the CHANGELOG. It should reference the cleanup work, structural changes, and documentation fixes performed during this release preparation.

If `docs/DEVLOG.md` does not exist, create it.

---

## Phase E: Validation and Finalization

### Step E1: Deep Codebase Scan

**CRITICAL**: Perform a comprehensive search for ALL version references that might have been missed, plus any stale file paths from the layout refactor.

**Version string search patterns:**
```bash
# Find version strings in Python files
grep -r "__version__" --include="*.py"

# Find version in config files
grep -r "version.*=" --include="*.toml" --include="*.json" --include="*.yaml" --include="*.cfg"

# Find version in documentation
grep -r "v[0-9]\+\.[0-9]\+\.[0-9]\+" --include="*.md"
```

**Check these specific locations:**
- Root: `pyproject.toml`, `README.md`, `CHANGELOG.md`, `setup.py`, `setup.cfg`
- Source: `src/__init__.py`, `src/*/__init__.py` (all nested packages)
- Any `__version__.py` files
- Any sub-package `README.md` files
- `VERSION` file (if exists)
- `manifest.json`, `package-lock.json`
- `.bumpversion.cfg`, `.version`
- Documentation config files (`conf.py`, `mkdocs.yml`)

**Stale path search** (if files were moved in Phase B):
- Search for old file paths that should have been updated to new paths
- Check Markdown links, script references, and config files

Report any files found that contain version references or stale paths and whether they were updated.

### Step E2: Validate Consistency

Verify all version references match:

```
Final Checklist:
- [ ] pyproject.toml / package.json
- [ ] README.md header and "What's New" section
- [ ] CHANGELOG.md latest entry
- [ ] Source code __version__
- [ ] All nested __init__.py files
- [ ] All sub-README files
- [ ] Help/about menus
- [ ] Any other version references found in deep scan
- [ ] No stale file paths from layout refactor
- [ ] No wrongly-tracked files in git index
- [ ] All documentation links resolve to existing files
```

Report any mismatches found.

### Step E3: Generate Summary

Present the upgrade summary covering all phases:

```markdown
## Version Upgrade Summary

**Previous Version**: X.Y.Z
**New Version**: A.B.C
**Type**: MAJOR/MINOR/PATCH

### Phase B: Cleanup
- Layout refactor: [X files moved / no changes needed]
- Refactor verification: [PASSED / N/A]
- Gitignore audit: [X patterns added, Y files untracked / no changes needed]

### Phase C: Version Bump
- [ ] Configuration files updated
- [ ] CHANGELOG.md (new version entry + footer links)
- [ ] README.md (version references + "What's New in Version X.Y.Z")
- [ ] Help/about menus (if applicable)

### Phase D: Documentation
- [ ] Documentation files audited and updated (X files)
- [ ] docs/DEVLOG.md (release entry)

### Phase E: Validation
- Version consistency: [PASSED / X mismatches found]
- Stale references: [NONE / X remaining]

### Changes Documented
- Added: X items
- Changed: Y items
- Fixed: Z items
- Removed: W items

### Ready for Release
All version references updated and consistent.
```

### Step E4: Generate Commit Message

Generate a ready-to-use commit message for the user:

**Format (sectioned-bullet style for any release that touches multiple categories):**
```
vX.X.X: [One sentence summarizing the main changes]

[1-2 sentence intro paragraph stating what this release delivers and why.]

Added:
- [Bullet from CHANGELOG Added]
- [Bullet from CHANGELOG Added]

Changed:
- [Bullet from CHANGELOG Changed]

Fixed:
- [Bullet from CHANGELOG Fixed]

Tests:
- [Test counts and coverage if relevant]
```

For a small PATCH that only changes one category (e.g., only `Fixed:`), it's fine to use a single section header instead of all four.

**Rules:**
- First line: `vX.X.X:` followed by a concise summary (under 72 chars). The 72-char cap on the subject line is a hard limit, not a wrap.
- Blank line after the first line, then a 1-2 sentence intro paragraph stating what the release delivers and why, then another blank line before the first section header.
- **Sectioned-bullet structure (CRITICAL)**: organize the body as **labeled sections with bullets**, NOT as multiple flowing paragraphs. Use the CHANGELOG section names (`Added:`, `Changed:`, `Fixed:`, `Removed:`) as headers, each ending in a colon. Add a `Tests:` section if the release affects test coverage. Add structural changes from Phase B (`Layout:`, `Gitignore:`) as their own sections if relevant.
- Include all significant changes from CHANGELOG (Added, Changed, Fixed, Removed). Map each CHANGELOG entry to one bullet under the matching section header.
- **No hard-wrapping (CRITICAL)**: every paragraph and every bullet point in the body MUST be a single continuous line in the source, regardless of length. Do NOT insert line breaks at any column width (50, 72, 80, 100, etc.). The 72-char "convention" from older git tooling docs is obsolete - modern Git, GitHub, GitLab, and `git log` all soft-wrap on display. The subject line is the only exception.
- **Whitespace**: exactly one blank line between sections; never two or more. Within a section, bullets are contiguous (no blank lines between them).
- **DO NOT** add "Created by Claude Code" or any AI attribution footer
- **DO NOT** add "Co-Authored-By" lines

**Example (sectioned-bullet style for a release touching multiple categories):**
```
v0.9.0: figure settings management and project layout refactor

Adds figure-level settings management (a new dataclass plus a Qt dialog for editing them) and refactors the repo layout so data files live under `data/` and scripts under `scripts/`. Documentation and `.gitignore` updated to match the new structure.

Added:
- `FigureSettings` class for figure configuration management.
- `FigureSettingsDialog` for user-friendly settings editing.

Changed:
- Project layout refactor: move data files to `data/`, scripts to `scripts/`.
- `.gitignore` updated with Python and Node.js patterns.
- Documentation updated to reflect the new layout.

Fixed:
- Color picker initialization bug.
```

**Counter-example (do not produce a single flat `Changes:` section that mixes Added / Changed / Fixed bullets together):**
```
v0.9.0: Add figure settings management and restructure project layout

Changes:
- Add FigureSettings class
- Add FigureSettingsDialog
- Refactor project layout: move data to data/, scripts to scripts/
- Update .gitignore
- Update documentation
- Fix color picker bug
```

Present this commit message in a code block so the user can easily copy/paste it.

---

## Phase: Iterative Refinement (Loop)

**IMPORTANT**: This loop runs as part of Phase E, before presenting the final summary (E3) and commit message (E4). It is not a post-commit activity.

**CRITICAL**: This is an iterative process. You cannot assume the first pass is perfect.
Perform the following refinement loop up to **3 times** (or as specified by the user's input, e.g., "5 iterations"):

1.  **Analyze**: Look at the generated output.
    *   Is it complete?
    *   Are there any obvious errors?
    *   Does it meet the user's requirements?
    *   Are there stale file paths from the layout refactor?
    *   Are there wrongly-tracked files remaining after gitignore cleanup?
    *   Do all documentation links resolve to existing files?
    *   Do all version references match the new version?
2.  **Refine**:
    *   Fix any issues found.
    *   Add missing components.
    *   Re-verify affected files.
3.  **Stop**:
    *   If you are confident the result is excellent.
    *   OR if you have reached the maximum iteration count.

## After the Upgrade

After presenting the commit message, ask:

"Would you like me to create a git tag for this release? (The commit should be done manually using the message above)"

Only proceed with tag creation if explicitly requested.

---

## Language-Specific Notes

### Python
- Check `__init__.py` for `__version__` in all packages
- Update `setup.py` if present (legacy)
- Check `src/packagename/__version__.py` pattern
- Verify wheel/sdist names will be correct

### JavaScript/TypeScript
- Update `package.json`
- Check `package-lock.json` regeneration needs
- Verify npm publish readiness

### Java
- Update `pom.xml` or `build.gradle`
- Check manifest files

### C#/.NET
- Update `.csproj` version
- Check `AssemblyInfo.cs` if present
- Check `Directory.Build.props`

### Go
- Update version constant in source
- Check `go.mod` module version

---

## Guidelines

- Never auto-commit or push without explicit user approval
- Always show the user what will change before making changes
- Verify version consistency across all files
- Use today's date for CHANGELOG entries
- Follow semantic versioning strictly
- Auto-analyze git history instead of asking user to describe changes
- Always perform deep codebase scan to catch missed version references
- Always generate a copy-paste ready commit message
- Each sub-command (layout refactor, gitignore, documentation, devlog) runs its full workflow but defers user-confirmation prompts to the parent command's confirmation gates
- If a phase has nothing to do (e.g., no files need moving, gitignore is already clean), state this explicitly and proceed to the next phase
