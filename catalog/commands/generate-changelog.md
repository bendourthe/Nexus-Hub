---
description: Generate a complete CHANGELOG.md from the repository's git history, tags, and commit messages following the Keep a Changelog format.
---

# Generate Changelog Command

Generate a comprehensive `CHANGELOG.md` file following the [Keep a Changelog](https://keepachangelog.com/en/1.0.0/) format and [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

When run on a repository with existing tagged releases, the command reconstructs the full changelog from git history. When run on a repository that already has a CHANGELOG.md, it offers to regenerate or update.

## Phase 1: Detect Mode

1. Check if `CHANGELOG.md` exists in the repository root.
2. **If it exists**: Ask the user:
   - **Regenerate**: Overwrite with a fresh changelog built from git history (back up existing file to `CHANGELOG.backup.md` first).
   - **Update**: Only add/refresh the `[Unreleased]` section with commits since the latest tag. Leave existing version entries untouched.
3. **If it does not exist**: Proceed with full generation from scratch.

## Phase 2: Collect Git History

Run the following git commands to gather source material:

1. **List all version tags** (sorted by version):
   ```bash
   git tag -l --sort=version:refname
   ```
   Normalize tag formats: strip leading `v` or `release-` prefixes to extract the bare version number (e.g., `v1.2.0` becomes `1.2.0`).

2. **Get full commit history** (chronological):
   ```bash
   git log --format="%H|%ai|%an|%s" --reverse
   ```

3. **For each pair of consecutive tags** (oldest to newest), get the commits in that range:
   ```bash
   git log <older-tag>..<newer-tag> --oneline --no-merges
   ```

4. **For commits before the first tag** (the initial development period):
   ```bash
   git log <first-tag> --oneline --no-merges --reverse
   ```

5. **For commits after the latest tag** (unreleased work):
   ```bash
   git log <latest-tag>..HEAD --oneline --no-merges
   ```

6. **Get the release date for each tag**:
   ```bash
   git log -1 --format="%ai" <tag>
   ```
   Extract the `YYYY-MM-DD` portion.

7. **Detect GitHub remote** (for comparison links in the footer):
   ```bash
   git remote get-url origin
   ```
   Parse the owner/repo from HTTPS or SSH URLs.

## Phase 3: Categorize Changes

For each version boundary, categorize commits into Keep a Changelog sections.

### Conventional Commit Parsing

Parse commit messages that follow the `type(scope): description` pattern:

| Commit Prefix | Changelog Category |
|---|---|
| `feat`, `feature` | **Added** |
| `fix`, `bugfix` | **Fixed** |
| `docs` | **Changed** |
| `style` | **Changed** |
| `refactor` | **Changed** |
| `perf` | **Changed** |
| `test` | **Changed** |
| `build`, `ci` | **Changed** |
| `chore` | **Changed** |
| `revert` | **Removed** |
| `deprecate` | **Deprecated** |

If the commit message contains `BREAKING CHANGE` or uses the `!` suffix (e.g., `feat!:`), flag it prominently under **Changed** with a `**BREAKING**:` prefix.

### Keyword-Based Inference (Non-Conventional Commits)

For commit messages that do not follow conventional commit format, infer the category from keywords:

| Keywords in Message | Changelog Category |
|---|---|
| "add", "create", "implement", "introduce", "new" | **Added** |
| "fix", "resolve", "correct", "patch", "repair" | **Fixed** |
| "update", "change", "modify", "improve", "enhance", "refactor", "rename", "move", "migrate" | **Changed** |
| "remove", "delete", "drop", "deprecate", "revert" | **Removed** |
| "security", "vulnerability", "CVE" | **Security** |

For ambiguous commits that match no keywords, use `git show --stat <hash>` to check:
- Mostly new files → **Added**
- Mostly deleted files → **Removed**
- Otherwise → **Changed**

### Entry Formatting

- Write each entry as a single bullet point describing the change in imperative mood.
- If a scope is present (from conventional commits), **bold** it as a prefix: `- **auth**: Add token refresh endpoint`.
- Group related commits into a single, richer entry when they clearly belong to the same feature or fix.
- Omit trivial commits (typo fixes, merge commits, version bumps) unless they are the only commits in a version.

## Phase 4: Generate CHANGELOG

Assemble the complete file in this structure:

### File Header

```markdown
# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---
```

### Version Sections (Reverse Chronological)

```markdown
## [Unreleased]

### Added
- [Entries from commits after latest tag]

### Changed
- [Entries]

### Fixed
- [Entries]

---

## [X.Y.Z] - YYYY-MM-DD

### Added
- [Entries from commits between tags]

### Changed
- [Entries]

### Fixed
- [Entries]

---
```

**Rules**:
- Only include category subsections (`### Added`, `### Changed`, etc.) that have entries. Do not include empty sections.
- Use `---` horizontal rules between version sections for readability.
- The `[Unreleased]` section is always present (even if empty, to establish the pattern for future updates).
- Each version header links to a comparison URL in the footer.

### Footer (Comparison Links)

If a GitHub remote was detected, add comparison links at the bottom:

```markdown
[Unreleased]: https://github.com/owner/repo/compare/vX.Y.Z...HEAD
[X.Y.Z]: https://github.com/owner/repo/compare/vA.B.C...vX.Y.Z
[A.B.C]: https://github.com/owner/repo/releases/tag/vA.B.C
```

The oldest version links to its release tag. Each subsequent version links to a comparison with the previous version.

## Phase 5: Edge Cases

Handle these scenarios:

- **No tags at all**: Group commits by month. Use `## YYYY-MM` as section headers instead of version numbers. Add a note at the top: `*This project does not use version tags. Entries are grouped by month.*`
- **Very large repositories (1000+ commits)**: For versions with more than 50 commits, focus on merge commits and significant changes. Summarize maintenance work as a single "Various maintenance and cleanup" entry.
- **Squash-merged repositories**: Each squash-merge commit becomes one entry. Parse the PR title from the commit message if present.
- **Mixed tag formats**: Normalize `v1.0.0`, `1.0.0`, `release-1.0.0`, `release/1.0.0` to bare `1.0.0` for display, but use the original tag name in git commands and footer links.
- **Pre-release tags**: Include `alpha`, `beta`, `rc` tags as separate sections, ordered correctly.
- **Monorepo**: If the user specifies a path filter, only include commits that touch files under that path (use `git log -- <path>`).
- **Existing CHANGELOG with manual edits**: When in "Update" mode, only touch the `[Unreleased]` section. Never modify existing version entries.

## Phase 6: Write and Summarize

1. Write the complete CHANGELOG to `CHANGELOG.md` in the repository root.
2. If an existing file was backed up, confirm: `Backed up existing CHANGELOG to CHANGELOG.backup.md`.
3. Output a summary:

```
Generated CHANGELOG.md:
- Versions: X tagged releases + [Unreleased]
- Commits processed: Y
- Date range: YYYY-MM-DD to YYYY-MM-DD
- Sources: git tags, commit messages [, GitHub remote for comparison links]
```

4. Ask the user if they want to review or adjust any entries before finalizing.


## Phase: Iterative Refinement (Loop)

**CRITICAL**: This is an iterative process. You cannot assume the first pass is perfect.
Perform the following refinement loop up to **3 times** (or as specified by the user's input, e.g., "5 iterations"):

1.  **Analyze**: Look at the generated output.
    *   Does every tagged release have a section?
    *   Are versions in strict reverse chronological order?
    *   Are category sections (`### Added`, `### Changed`, etc.) only present when non-empty?
    *   Are footer comparison links correct and complete?
    *   Are dates accurate (matching git tag dates)?
    *   Are entries written in imperative mood?
    *   Are related commits grouped into cohesive entries?
2.  **Refine**:
    *   Fix any issues found.
    *   Enrich sparse entries by checking `git show --stat` for context.
    *   Merge duplicate or closely related entries.
    *   Remove trivial noise entries (merge commits, version bumps).
3.  **Stop**:
    *   If you are confident the result is excellent.
    *   OR if you have reached the maximum iteration count.
