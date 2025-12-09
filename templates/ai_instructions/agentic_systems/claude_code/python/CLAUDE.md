# Project: [Your Project Name]

## Overview
[2-3 sentence description of what this project does]

## Tech Stack
- **Language**: Python 3.12+
- **Package Manager**: uv (or pip with venv)
- **Linting/Formatting**: ruff
- **Testing**: pytest
- **Type Checking**: mypy

## Project Structure
```
src/                  - Application source code
├── config/           - Configuration
├── core/             - Core application logic
├── gui/              - GUI components (if applicable)
├── utils/            - Utility functions
tests/                - Test suites
├── temp/             - Temporary tests (auto-deleted)
docs/                 - Documentation
```

## Key Files
- `pyproject.toml` - Dependencies and configuration
- `CHANGELOG.md` - Version history
- `DEVLOG.md` - Development documentation
- `README.md` - Project documentation
- `.gitignore` - Git ignore rules

## Critical Commands
```bash
# Development
uv run python src/main.py

# Testing
uv run pytest tests/ -v
python tests/run_all_tests.py

# Code Quality
uv run ruff check .
uv run ruff format .
uv run mypy src/
```

## Quick Reference

### Task Types → Focus Areas
| Task Type | Skills Activated |
|-----------|------------------|
| Bug Fix | interaction-principles, code-standards, quality-checklist |
| New Feature | project-setup, workflow-methodology, testing-framework |
| Refactoring | code-standards, implementation-patterns |
| Documentation | documentation-standards |
| Version/Git | version-control |

### Efficiency Modes
- **Quick Mode** (simple fixes): Minimal docs, focus on core fix
- **Full Mode** (new projects): Complete architecture, comprehensive testing

## Context References
- Architecture: @.claude/context/architecture.md
- Decisions: @.claude/memory/decisions.md

## Critical Rules

**NEVER:**
- Auto-modify version numbers (ask first)
- Suggest git commands unless explicitly requested
- Create separate markdown files (use DEVLOG.md)
- Run commands in chat (request user to run in terminal)

**ALWAYS:**
- Ask clarifying questions before proceeding
- Explain reasoning and teach concepts
- Use iterative testing with tests/temp/
- Document progress in DEVLOG.md
- Follow the quality checklist before delivering code
