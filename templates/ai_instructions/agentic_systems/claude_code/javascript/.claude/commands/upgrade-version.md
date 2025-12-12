# Version Upgrade Assistant

Guide the user through a comprehensive version upgrade following semantic versioning.

## Instructions

You are helping the user upgrade their project version. Follow these steps systematically.

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

### Step 2: Identify Current Version

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

### Step 3: Analyze Git Changes (Auto-Analysis)

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

### Step 6: Update README.md

Update version references in README:

```markdown
# Project Name - vNEW_VERSION

## What's New
- [Key highlights from CHANGELOG]
```

Use the top 3-5 most significant items from the CHANGELOG for "What's New".

### Step 7: Update CHANGELOG.md

Add the new version entry using the approved content from Step 4:

```markdown
## [NEW_VERSION] - YYYY-MM-DD

### Added
- [Features]

### Changed
- [Modifications]

### Fixed
- [Bug fixes]

### Removed
- [Deprecated items removed]
```

Use today's date in YYYY-MM-DD format.

### Step 8: Update DEVLOG.md (if exists)

Move completed tasks and update status:

```markdown
## Development History

### [NEW_VERSION] Release - YYYY-MM-DD
- Completed: [list of completed items]
- Deferred: [items moved to next release]
```

### Step 9: Update Help/About Menus (if applicable)

Check for version displays in:
- CLI help messages
- GUI about dialogs
- API version endpoints
- Documentation headers

### Step 10: Deep Codebase Scan

**CRITICAL**: Perform a comprehensive search for ALL version references that might have been missed.

**Search patterns to use:**
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

Report any files found that contain version references and whether they were updated.

### Step 11: Validate Consistency

Verify all version references match:

```
Final Checklist:
- [ ] pyproject.toml / package.json
- [ ] README.md header
- [ ] CHANGELOG.md latest entry
- [ ] Source code __version__
- [ ] All nested __init__.py files
- [ ] All sub-README files
- [ ] Any other version references found in deep scan
```

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

## Guidelines

- Never auto-commit or push without explicit user approval
- Always show the user what will change before making changes
- Verify version consistency across all files
- Use today's date for CHANGELOG entries
- Follow semantic versioning strictly
- Auto-analyze git history instead of asking user to describe changes
- Always perform deep codebase scan to catch missed version references
- Always generate a copy-paste ready commit message
