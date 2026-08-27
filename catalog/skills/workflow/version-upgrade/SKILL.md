---
name: version-upgrade
description: Comprehensive version upgrade workflow for releasing new versions. Automatically analyzes git history, updates version numbers across all files, documentation, changelogs, and generates commit messages. Use when upgrading app version, releasing new version, bumping version numbers, or preparing a release.
summary_l0: "Automate version upgrades with changelog generation and cross-file version bumps"
overview_l1: "This skill provides a comprehensive version upgrade workflow for releasing new versions, automatically analyzing git history, updating version numbers across all files, documentation, and changelogs, and generating commit messages. Use it when upgrading app version, releasing a new version, bumping version numbers, or preparing a release. Key capabilities include semantic version bump determination from git history, cross-file version number updates, changelog generation from conventional commits, documentation version synchronization, release commit message generation, and tag creation. The expected output is a complete version release with updated version numbers across all files, generated changelog, updated documentation, and a release commit. Trigger phrases: version upgrade, release version, bump version, prepare release, new version, version bump, changelog update."
---

# Version Upgrade Workflow

Systematically upgrade application version numbers across all configuration files, documentation, and generate comprehensive release artifacts including changelogs and commit messages.

## When to Use This Skill

Use this skill when you need to:

- Upgrade version from X.X.X to Y.Y.Y
- Release a new version of your application
- Bump version numbers (major, minor, patch)
- Prepare a release with proper documentation
- Update all version references consistently
- Generate release commit messages

**Trigger phrases**: "upgrade version", "bump version", "release version", "update to version", "version X.X.X to Y.Y.Y", "prepare release", "new version"

## What This Skill Does

### Version Upgrade Process

1. **Determine Target Version** - Accept version type OR direct version number
2. **Analyze Git Changes** - Auto-analyze commits since last tag (DO NOT ask user)
3. **Generate CHANGELOG** - Auto-generate entries from commit analysis
4. **Update All Files** - Configuration, documentation, source code
5. **Deep Scan** - Find ALL version references in codebase
6. **Validation** - Verify all references are consistent
7. **Commit Message** - Generate ready-to-copy commit message

## Instructions

Step 0 gates plan-driven releases; Steps 1 onward are the version mechanics and apply to every invocation.

### Step 0: Verify the integration gate (plan-driven releases)

When this skill runs as part of a plan-driven release, verify FOUR things before touching a single version-carrying file. A version bump is the point after which every later step assumes the release is happening, so an unwind costs more than a wait.

1. The plan branch merged into the integration branch.
2. Every required check on that integration pull request reached success, and the post-merge work (if any) succeeded. A pending check is not a green check.
3. The working tree is clean and the local integration branch matches its remote.
4. The proposed release notes were derived from the ACTUAL diff over the real tag range, not from the plan. Notes written from the plan describe what was intended, not what shipped.

If any of the four fails, stop and say which one.

This step is a no-op for an ad-hoc version bump outside a plan; a one-off patch has no integration pull request to gate on. See `[[git-branching-workflow]]` for the branch model and `[[cicd-architect]]` for what "green" means.

### Step 1: Determine Target Version

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

### Step 2: Identify Current Version and Last Tag

Find the current version in the project:

```bash
# Check these locations:
# - pyproject.toml (version = "X.Y.Z")
# - package.json (version field)
# - CHANGELOG.md (latest version header)
# - README.md (version in header/badge)
# - Source code (__version__, VERSION constant)

# Find last git tag
git describe --tags --abbrev=0
```

Tell the user: "Current version found: X.Y.Z. New version will be: A.B.C"

### Step 3: Analyze Git Changes (Auto-Analysis)

**IMPORTANT**: Automatically analyze changes since the last release. Do NOT ask the user to describe changes.

```bash
# Find commits since last tag
git log {last_tag}..HEAD --oneline --no-merges

# Get detailed file changes
git diff {last_tag}..HEAD --stat
```

For each commit, analyze the commit message and changed files to categorize:
- **Added**: New features, new files, new functionality
- **Changed**: Modifications, improvements, refactoring
- **Fixed**: Bug fixes, corrections
- **Removed**: Deleted features, deprecated code removal

Generate proposed CHANGELOG entries from this analysis.

### Step 4: Present Proposed Changes

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

### Step 5: Update Configuration Files

#### Python (pyproject.toml)
```toml
[project]
version = "Y.Y.Y"  # Update from X.X.X
```

#### Python (__version__.py or __init__.py)
```python
__version__ = "Y.Y.Y"
```

#### JavaScript (package.json)
```json
{
  "version": "Y.Y.Y"
}
```

#### Java (pom.xml)
```xml
<version>Y.Y.Y</version>
```

#### C# (*.csproj)
```xml
<Version>Y.Y.Y</Version>
<AssemblyVersion>Y.Y.Y.0</AssemblyVersion>
<FileVersion>Y.Y.Y.0</FileVersion>
```

#### Go (version.go)
```go
const Version = "Y.Y.Y"
```

### Step 6: Update README.md

#### Update Title/Badge
```markdown
# Project Name - vY.Y.Y

[![Version](https://img.shields.io/badge/version-Y.Y.Y-blue.svg)]
```

#### Replace "What's New" Section
Use the top 3-5 most significant items from the CHANGELOG:

```markdown
## What's New in Version Y.Y.Y

- **Feature 1**: Description of major feature or change
- **Feature 2**: Description of another significant change
- **Bug Fix**: Description of important bug fix

See [CHANGELOG.md](CHANGELOG.md) for complete version history.
```

### Step 7: Update CHANGELOG.md

Add new version entry at the top (below [Unreleased]) using the approved content from Step 4:

```markdown
## [Y.Y.Y] - YYYY-MM-DD

### Added
- New feature A with description
- New feature B with description

### Changed
- Changed behavior X
- Updated dependency Y to version Z

### Fixed
- Fixed bug where [description]
- Resolved issue with [description]

### Removed
- Removed deprecated function X
- Removed unused file Y
```

Use today's date in YYYY-MM-DD format.

### Step 8: Update DEVLOG.md (if exists)

Add release entry:

```markdown
## Release Y.Y.Y - YYYY-MM-DD

### Summary
Brief summary of this release and its significance.

### Key Changes
1. **Major Change 1**: Detailed explanation
2. **Major Change 2**: Detailed explanation
```

### Step 9: Update Help Menus and About Dialogs (if applicable)

Check for version displays in:
- CLI help messages
- GUI about dialogs
- API version endpoints
- Documentation headers

### Step 10: Deep Codebase Scan

**CRITICAL**: Perform a comprehensive search for ALL version references that might have been missed.

```bash
# Find all files containing version references
grep -r "X.X.X" --include="*.md" --include="*.toml" --include="*.json" --include="*.yaml" --include="*.yml" --include="*.py" --include="*.js" --include="*.ts" --include="*.java" --include="*.cs" --include="*.go" --include="*.xml" .

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
- Help menus, about dialogs, CLI version flags

Report any files found that contain version references and whether they were updated.

### Step 11: Validate Version Consistency

```bash
# Verify all version references match Y.Y.Y
echo "=== Version Validation ==="
grep -r "Y.Y.Y" --include="*.md" --include="*.toml" --include="*.json" . | head -20

# Check for any remaining old version references
echo "=== Checking for old version X.X.X ==="
grep -r "X.X.X" --include="*.md" --include="*.toml" --include="*.json" .
# Should return empty if all updated
```

Final Checklist:
- [ ] pyproject.toml / package.json
- [ ] README.md header
- [ ] CHANGELOG.md latest entry
- [ ] Source code __version__
- [ ] All nested __init__.py files
- [ ] All sub-README files
- [ ] Any other version references found in deep scan

Report any mismatches found.

### Step 12: Generate Summary

Present the upgrade summary:

```markdown
## Version Upgrade Summary

**Previous Version**: X.Y.Z
**New Version**: A.B.C
**Type**: MAJOR/MINOR/PATCH

### Files Updated
- [ ] pyproject.toml
- [ ] README.md
- [ ] CHANGELOG.md
- [ ] DEVLOG.md
- [ ] Source code version
- [ ] [Any additional files from deep scan]

### Changes Documented
- Added: X items
- Changed: Y items
- Fixed: Z items
- Removed: W items

### Ready for Release
All version references updated and consistent.
```

### Step 13: Generate Commit Message

Generate a ready-to-use commit message for the user:

**Format:**
```
vX.X.X: [One sentence summarizing the main changes]

Changes:
- [Bullet point from Added]
- [Bullet point from Changed]
- [Bullet point from Fixed]
- [etc.]
```

**Rules:**
- First line: `vX.X.X:` followed by a concise summary (under 72 chars)
- Blank line after the first line
- "Changes:" header followed by bullet points
- Include all significant changes from CHANGELOG (Added, Changed, Fixed, Removed)
- Keep each bullet point concise
- **DO NOT** add "Created by Claude Code" or any AI attribution footer
- **DO NOT** add "Co-Authored-By" lines

**Example:**
```
v0.2.2: Add figure settings management and improve UI components

Changes:
- Add FigureSettings class for figure configuration management
- Add FigureSettingsDialog for user-friendly settings editing
- Add ModernDateEdit widget for improved date selection
- Improve Matplotlib theming with enhanced theme adapter
- Update default parameters in calibration settings
- Fix color picker initialization bug
```

Present this commit message in a code block so the user can easily copy/paste it:

```
Here's your commit message (ready to copy/paste):
```

## After the Upgrade

After presenting the commit message, ask:

"Would you like me to create a git tag for this release? (The commit should be done manually using the message above)"

Only proceed with tag creation if explicitly requested.

## Version Number Format

Follow Semantic Versioning (SemVer):

| Change Type | Version Bump | Example |
|-------------|--------------|---------|
| Breaking changes | Major (X+1.0.0) | 1.0.0 → 2.0.0 |
| New features (backward compatible) | Minor (X.Y+1.0) | 1.2.0 → 1.3.0 |
| Bug fixes (backward compatible) | Patch (X.Y.Z+1) | 1.2.3 → 1.2.4 |

### Pre-release Versions
```
Y.Y.Y-alpha.1
Y.Y.Y-beta.2
Y.Y.Y-rc.1
```

### Build Metadata
```
Y.Y.Y+build.123
Y.Y.Y+20231215
```

## Language-Specific Checklists

Per-ecosystem version-carrying files (Python, Node, Rust, Go, and others) and one end-to-end worked run: [`references/per-language-checklists.md`](references/per-language-checklists.md).

The rule they serve, in one line: find EVERY file that states the version and bump them in one atomic change, because a half-bumped tree is worse than an un-bumped one.

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "I bumped the version in package.json, the upgrade is done" | Version strings live in many places (README, About dialog, docs headers, CHANGELOG); updating one and missing the rest ships a build that reports contradictory versions to users. |
| "I will write the CHANGELOG entry from memory" | A CHANGELOG built from memory omits the quiet fixes and breaking changes; derive it from the actual commit range so users see every change that affects them. |
| "It is just a patch bump, SemVer rules do not really matter" | Mislabeling a breaking change as a patch silently breaks downstream consumers who pinned a caret range; the MAJOR/MINOR/PATCH choice is a contract, not a formality. |

## Verification

Before finalizing the version upgrade:

- [ ] All version references updated to Y.Y.Y
- [ ] No references to old version X.X.X remain
- [ ] README "What's New" section updated
- [ ] CHANGELOG entry complete with date
- [ ] DEVLOG release notes added
- [ ] Help menus/About dialogs updated
- [ ] .gitignore reviewed and updated
- [ ] Temp files removed
- [ ] Deprecated content removed
- [ ] All documentation links valid
- [ ] Commit message generated and ready to copy
- [ ] Version follows SemVer guidelines

## Related Skills

- [[code-commit-workflow]] -- commit workflow and conventions for the version-bump commit
- [[pre-commit-checklist]] -- pre-commit validation before the upgrade is recorded
- [[documentation-consistency]] -- verify every version reference and doc link stays in sync after the bump
- [[release-notes-writer]] -- generate the user-facing release notes that accompany the new version

---

**Version**: 2.0.0
**Last Updated**: December 2025
**Based on**: Semantic Versioning 2.0.0


### Iterative Refinement Strategy
This skill is optimized for an iterative approach:
1. **Execute**: Perform the core steps defined above.
2. **Review**: Critically analyze the output (coverage, quality, completeness).
3. **Refine**: If targets aren't met, repeat the specific implementation steps with improved context.
4. **Loop**: Continue until the definition of done is satisfied.
