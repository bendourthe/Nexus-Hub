---
name: version-upgrade
description: Comprehensive version upgrade workflow for releasing new versions. Updates version numbers across all files, documentation, changelogs, and generates commit messages. Use when upgrading app version, releasing new version, bumping version numbers, or preparing a release.
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

1. **Configuration Files** - Update version in all config files
2. **Documentation** - Update README, docs, help menus
3. **Changelog** - Document all changes since last version
4. **Development Log** - Update DEVLOG with release notes
5. **Cleanup** - Remove temp files, deprecated content
6. **Validation** - Verify all references are consistent
7. **Commit Message** - Generate comprehensive commit message

## Instructions

### Step 1: Identify All Version Locations

Search for current version across the codebase:

```bash
# Find all files containing the current version
grep -r "X.X.X" --include="*.md" --include="*.toml" --include="*.json" --include="*.yaml" --include="*.yml" --include="*.py" --include="*.js" --include="*.ts" --include="*.java" --include="*.cs" --include="*.go" --include="*.xml" .

# Common locations by language:
# Python: pyproject.toml, setup.py, __init__.py, __version__.py
# JavaScript: package.json, package-lock.json
# Java: pom.xml, build.gradle
# C#: *.csproj, AssemblyInfo.cs
# Go: version.go, go.mod (module version)
# General: README.md, CHANGELOG.md, docs/*, config files
```

### Step 2: Update Configuration Files

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

### Step 3: Update README.md

#### Update Title/Badge
```markdown
# Project Name - vY.Y.Y

[![Version](https://img.shields.io/badge/version-Y.Y.Y-blue.svg)]
```

#### Replace "What's New" Section
Remove the previous "What's New" section entirely and add:

```markdown
## What's New in Version Y.Y.Y

- **Feature 1**: Description of major feature or change
- **Feature 2**: Description of another significant change
- **Bug Fix**: Description of important bug fix
- **Improvement**: Description of improvement

See [CHANGELOG.md](CHANGELOG.md) for complete version history.
```

#### Update Installation Instructions
Ensure any version-specific installation commands are updated:
```markdown
pip install package-name==Y.Y.Y
npm install package-name@Y.Y.Y
```

### Step 4: Update CHANGELOG.md

Add new version entry at the top (below [Unreleased]):

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

### Security
- Patched vulnerability in [component]

### Deprecated
- Function X will be removed in version Z.Z.Z
```

### Step 5: Update DEVLOG.md

Add release entry:

```markdown
## Release Y.Y.Y - YYYY-MM-DD

### Summary
Brief summary of this release and its significance.

### Key Changes
1. **Major Change 1**: Detailed explanation
2. **Major Change 2**: Detailed explanation

### Migration Notes
- Any breaking changes requiring user action
- Configuration changes needed

### Known Issues
- List any known issues in this release

### Contributors
- @contributor1 - Feature A
- @contributor2 - Bug fix B
```

### Step 6: Update Help Menus and About Dialogs

#### CLI Help Text
```python
# Update version in CLI help
parser = argparse.ArgumentParser(
    description="Application Name vY.Y.Y"
)
parser.add_argument('--version', action='version', version='Y.Y.Y')
```

#### GUI About Dialog
```python
# Update About dialog
about_text = """
Application Name
Version Y.Y.Y

Copyright (c) YYYY Author Name
"""
```

#### Man Pages / Documentation
Update any man pages, help files, or documentation that reference the version.

### Step 7: Update .gitignore (If Needed)

Review and update .gitignore for any new patterns:

```gitignore
# Add new patterns for this version
*.new-extension
new-temp-directory/

# Remove obsolete patterns
# -old-pattern-no-longer-needed
```

### Step 8: Clean Up Temp Files

Remove temporary files that should not be in the release:

```bash
# Common temp file patterns
rm -rf tests/temp/*
rm -rf temp/
rm -rf __pycache__/
rm -rf *.pyc
rm -rf .pytest_cache/
rm -rf .coverage
rm -rf htmlcov/
rm -rf dist/
rm -rf build/
rm -rf *.egg-info/
rm -rf node_modules/.cache/
rm -rf .next/
rm -rf .nuxt/
```

### Step 9: Check for Deprecated Content

#### Find References to Non-Existent Files
```bash
# Find markdown links and verify targets exist
grep -roh '\[.*\]([^)]*\.md)' --include="*.md" . | \
  sed 's/.*(\([^)]*\))/\1/' | \
  while read file; do
    if [ ! -f "$file" ]; then
      echo "Broken link: $file"
    fi
  done
```

#### Review for Outdated References
Check documentation for:
- References to removed features
- Outdated screenshots
- Obsolete API endpoints
- Deprecated function names
- Old configuration options

### Step 10: Validate Version Consistency

```bash
# Verify all version references match Y.Y.Y
echo "=== Version Validation ==="
grep -r "Y.Y.Y" --include="*.md" --include="*.toml" --include="*.json" . | head -20

# Check for any remaining old version references
echo "=== Checking for old version X.X.X ==="
grep -r "X.X.X" --include="*.md" --include="*.toml" --include="*.json" .
# Should return empty if all updated
```

### Step 11: Generate Commit Message

Create a temp file with the comprehensive commit message:

```bash
# Create commit message file
cat > temp/COMMIT_MESSAGE.txt << 'EOF'
vY.Y.Y: [Brief description of the release]

## Version Updates
- Updated version from X.X.X to Y.Y.Y in all configuration files
- Updated README.md with new "What's New" section
- Updated CHANGELOG.md with complete release notes
- Updated DEVLOG.md with release documentation

## Features Added
- [Feature 1]: [Description]
- [Feature 2]: [Description]

## Bug Fixes
- Fixed [issue description]
- Resolved [issue description]

## Documentation
- Updated installation instructions
- Refreshed API documentation
- Updated help menus and about dialogs

## Cleanup
- Removed deprecated [files/functions]
- Cleaned up temp files
- Updated .gitignore patterns

## Breaking Changes
- [If any, list them here]

## Files Modified
- pyproject.toml (version bump)
- README.md (What's New section)
- CHANGELOG.md (release notes)
- DEVLOG.md (release documentation)
- [Other modified files]

---
Release prepared with version-upgrade skill
EOF
```

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

### Python Checklist
- [ ] pyproject.toml version updated
- [ ] __version__.py or __init__.py updated
- [ ] setup.py version updated (if exists)
- [ ] requirements.txt reviewed
- [ ] docs/conf.py version updated (Sphinx)

### JavaScript/TypeScript Checklist
- [ ] package.json version updated
- [ ] package-lock.json regenerated
- [ ] yarn.lock regenerated (if using Yarn)
- [ ] docs version updated

### Java Checklist
- [ ] pom.xml version updated
- [ ] build.gradle version updated (if Gradle)
- [ ] META-INF/MANIFEST.MF updated

### C# Checklist
- [ ] *.csproj Version updated
- [ ] AssemblyInfo.cs updated
- [ ] NuGet package version updated

### Go Checklist
- [ ] version.go constant updated
- [ ] go.mod reviewed
- [ ] Git tag created

## Quality Checklist

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
- [ ] Commit message generated in temp/COMMIT_MESSAGE.txt
- [ ] Version follows SemVer guidelines

## Example Workflow

```
User: Upgrade version from 0.2.6 to 0.2.7

Claude:
1. Searching for all occurrences of "0.2.6"...
2. Found version in: pyproject.toml, README.md, __init__.py
3. Updating pyproject.toml: 0.2.6 → 0.2.7
4. Updating README.md:
   - Title badge: 0.2.6 → 0.2.7
   - Replacing "What's New in 0.2.6" with "What's New in 0.2.7"
5. Updating __init__.py: __version__ = "0.2.7"
6. Adding CHANGELOG entry for [0.2.7] - 2025-12-09
7. Adding DEVLOG release entry
8. Checking for broken documentation links...
9. Removing temp files from tests/temp/
10. Generating commit message in temp/COMMIT_MESSAGE.txt
11. Validating no "0.2.6" references remain...

Version upgrade complete! Review temp/COMMIT_MESSAGE.txt and commit when ready.
```

## Related Skills

- `code-commit-workflow` - Commit workflow and conventions
- `pre-commit-checklist` - Pre-commit validation
- `documentation` - Documentation standards

---

**Version**: 1.0.0
**Last Updated**: December 2025
**Based on**: Semantic Versioning 2.0.0
