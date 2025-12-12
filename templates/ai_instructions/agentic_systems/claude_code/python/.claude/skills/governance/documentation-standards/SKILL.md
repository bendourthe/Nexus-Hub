---
name: documentation-standards
description: Universal documentation structure standards for README, CHANGELOG, DEVLOG, and project documentation files. Use when creating or updating documentation, setting up new projects, or when user asks about documentation best practices.
---

# Documentation Standards

Universal documentation templates and guidelines for project documentation.

## README.md Template

```markdown
# [Project Name] - v[X.Y.Z]

## What's New
- [Key recent changes - keep this section short and current]

## Overview
[2-3 sentence description of what this project does and why it exists]

## Features
- [Core capability 1]
- [Core capability 2]
- [Core capability 3]

## Installation

### Prerequisites
- [Requirement 1] (version X.X+)
- [Requirement 2]

### Setup
```bash
# Clone repository
git clone [repo-url]
cd [project-name]

# Install dependencies
[installation command]

# Configure environment
cp .env.example .env
# Edit .env with your settings
```

## Usage

### Quick Start
```[language]
# Basic usage example
[code example]
```

### Configuration
| Variable | Description | Default |
|----------|-------------|---------|
| `VAR_NAME` | Description | `default` |

## Development

### Setup Development Environment
```bash
[development setup commands]
```

### Running Tests
```bash
[test command]
```

### Code Style
[Brief style guide or link to detailed guide]

## API Reference
[Link to API documentation or brief overview]

## Contributing
[Brief contribution guidelines or link to CONTRIBUTING.md]

## License
[License type] - See [LICENSE](LICENSE) for details.
```

## CHANGELOG.md Template

Based on [Keep a Changelog](https://keepachangelog.com/):

```markdown
# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- [New features not yet released]

### Changed
- [Changes to existing functionality]

### Deprecated
- [Features to be removed in future]

### Removed
- [Removed features]

### Fixed
- [Bug fixes]

### Security
- [Security vulnerability fixes]

## [X.Y.Z] - YYYY-MM-DD

### Added
- Feature A with brief description
- Feature B (#issue-number)

### Changed
- Improved X for better performance

### Fixed
- Bug in Y that caused Z (#issue-number)

## [Previous versions...]
```

### CHANGELOG Rules

1. **Keep `[Unreleased]` at top** - accumulate changes here
2. **Date on release** - add date when version is released
3. **Categorize properly** - use correct section (Added, Fixed, etc.)
4. **Be concise** - one line per change, link to issues
5. **Write for users** - explain impact, not implementation
6. **Chronological order** - newest version at top

## DEVLOG.md Template

Development log for tracking progress and decisions:

```markdown
# Development Log

## Current Task List

### High Priority
- [ ] [Urgent task 1]
- [ ] [Urgent task 2]

### Medium Priority
- [ ] [Important enhancement 1]
- [ ] [Important enhancement 2]

### Low Priority
- [ ] [Future feature 1]
- [ ] [Nice-to-have 1]

## Development History

### YYYY-MM-DD: [Topic/Feature]

**Context**: [Why this work was needed]

**Decisions Made**:
- Decision 1: [Choice made and reasoning]
- Decision 2: [Choice made and reasoning]

**Implementation Notes**:
- [Key implementation detail 1]
- [Key implementation detail 2]

**Challenges Encountered**:
- **Challenge**: [Description]
  - *Solution*: [How it was resolved]
  - *Trade-offs*: [What was sacrificed]

### Project Architecture

**Initial Design**: [Key architectural decisions]
**Tech Stack Choices**: [Why these technologies]
**Patterns Applied**: [Design patterns used]

## Troubleshooting History

### Issue: [Brief description]
- **Symptoms**: [What was observed]
- **Root Cause**: [What caused it]
- **Resolution**: [How it was fixed]
- **Prevention**: [How to avoid in future]
```

## Documentation Best Practices

### General Principles

1. **Write for the reader** - assume they're new to the project
2. **Keep it current** - outdated docs are worse than no docs
3. **Use examples** - show, don't just tell
4. **Be concise** - respect the reader's time
5. **Structure consistently** - use the same format across files

### What to Document

| Document | Purpose | Update Frequency |
|----------|---------|------------------|
| README | Project overview, setup | When project changes significantly |
| CHANGELOG | Version history | Every release |
| DEVLOG | Development decisions | During active development |
| API docs | Interface contracts | When APIs change |
| Architecture | System design | When architecture changes |

### What NOT to Document

- Implementation details that change frequently
- Information that can be derived from code
- Personal preferences (use linters instead)
- Duplicate information maintained elsewhere

### Documentation Anti-Patterns

- ❌ Giant walls of text without structure
- ❌ Copy-pasting code without explanation
- ❌ Outdated examples that don't work
- ❌ Assuming reader knows project history
- ❌ Mixing user docs with developer docs

## File Organization

```
docs/
├── README.md              # Project overview (or in root)
├── CHANGELOG.md           # Version history (or in root)
├── CONTRIBUTING.md        # How to contribute
├── architecture/
│   ├── overview.md        # System architecture
│   └── decisions/         # Architecture Decision Records
├── api/
│   ├── overview.md        # API documentation
│   └── endpoints/         # Individual endpoint docs
├── guides/
│   ├── getting-started.md # Onboarding guide
│   └── deployment.md      # Deployment guide
└── internal/
    └── DEVLOG.md          # Development log
```
