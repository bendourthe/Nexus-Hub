---
name: version-control-governance
description: Version control and semantic versioning governance rules. Use when discussing git operations, version updates, CHANGELOG modifications, release management, or when user asks about versioning strategy.
---

# Version Control Governance

These are the rules and principles governing version control operations.

## Core Principle

**CRITICAL: Never auto-modify versions. Always request user approval.**

## What I Will NOT Do Automatically

- Modify CHANGELOG.md versions
- Update pyproject.toml / package.json versions
- Change README.md version numbers
- Create git tags or releases
- Run `git add`, `git commit`, or `git push`
- Suggest git branch/merge/rebase operations

## Version Update Protocol

When changes warrant a version update:

1. **Assess**: "These changes might warrant a version update from X.Y.Z"
2. **Recommend**: "I suggest updating to [version] because [reason]"
3. **Request**: "Should I update the version? Or would you prefer to handle manually?"
4. **Wait**: Never proceed without explicit approval

## Semantic Versioning Rules

Follow [SemVer 2.0.0](https://semver.org/):

### MAJOR (X.0.0) - Breaking Changes
- Incompatible API changes
- Removed features
- Changed behavior that breaks existing usage

### MINOR (0.Y.0) - New Features
- New functionality (backwards-compatible)
- New API endpoints
- Feature enhancements
- Deprecation notices (not removal)

### PATCH (0.0.Z) - Bug Fixes
- Bug fixes
- Documentation corrections
- Security patches (non-breaking)
- Performance improvements (non-breaking)

## Git Operations Policy

### Only When Explicitly Requested

If user asks for git help, provide guidance:

```bash
# Stage changes
git add src/ tests/

# Commit with message
git commit -m "feat(auth): add OAuth2 authentication"

# Push to remote
git push origin feature/oauth-auth
```

### Never Suggest Unprompted

- `git init`
- `git commit --amend`
- `git rebase`
- `git reset --hard`
- `git push --force`

## CHANGELOG Management

### Structure

```markdown
# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

### Added
- New features

### Changed
- Changes to existing functionality

### Deprecated
- Features to be removed in future versions

### Removed
- Removed features

### Fixed
- Bug fixes

### Security
- Vulnerability fixes

## [1.2.3] - 2025-01-15

### Added
- Feature description
```

### Rules

- Keep `[Unreleased]` section at top for ongoing changes
- Date format: YYYY-MM-DD
- List changes under appropriate category
- Link to issues/PRs when relevant
- Don't modify historical entries

## DEVLOG Updates

I CAN update DEVLOG.md without permission for:
- Task list updates
- Development history
- Challenges and solutions
- Technical decisions

I will NOT include:
- Commit hashes
- Git workflow assumptions
- Version control strategies

## Commit Message Conventions

If asked to help with commits, use [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Types
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation
- `style`: Formatting (no code change)
- `refactor`: Code restructuring
- `test`: Adding tests
- `chore`: Maintenance tasks

### Examples
```
feat(api): add user authentication endpoint

Implements JWT-based authentication with refresh tokens.

Closes #123
```

## Version Release Commit Message Format

When generating commit messages for version releases, use this format:

**Format:**
```
vX.X.X: [One sentence summarizing the main changes]

Changes:
- [Bullet point 1]
- [Bullet point 2]
- [Bullet point 3]
```

**Rules:**
- First line: `vX.X.X:` followed by a concise summary (under 72 chars)
- Blank line after the first line
- "Changes:" header followed by bullet points
- Include all significant changes from CHANGELOG
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

## Version Files to Update

When approved to update version:

| Language | Files |
|----------|-------|
| Python | `pyproject.toml`, `__version__.py`, `CHANGELOG.md` |
| JavaScript | `package.json`, `CHANGELOG.md` |
| Java | `pom.xml`, `build.gradle`, `CHANGELOG.md` |
| C# | `*.csproj`, `Directory.Build.props`, `CHANGELOG.md` |
| Go | `version.go`, `CHANGELOG.md` |

## Deep Codebase Scan

When updating versions, perform a comprehensive search for ALL version references:

**Check these locations:**
- Root: `pyproject.toml`, `README.md`, `CHANGELOG.md`, `setup.py`, `setup.cfg`
- Source: `src/__init__.py`, `src/*/__init__.py` (all nested packages)
- Any `__version__.py` files
- Any sub-package `README.md` files
- `VERSION` file (if exists)
- `manifest.json`, `package-lock.json`
- `.bumpversion.cfg`, `.version`
- Documentation config files (`conf.py`, `mkdocs.yml`)
- Help menus, about dialogs, CLI version flags

## Release Checklist

When user requests a release:

1. [ ] All tests passing
2. [ ] CHANGELOG updated with release date
3. [ ] Version numbers consistent across ALL files (deep scan)
4. [ ] Documentation updated
5. [ ] Git tag created (with user approval)
6. [ ] Release notes prepared
7. [ ] Commit message generated (ready to copy)
