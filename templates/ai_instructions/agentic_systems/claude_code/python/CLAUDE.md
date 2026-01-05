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

### Task Types → Skills Activated
| Task Type | Core Skills | Specialist Skills |
|-----------|-------------|-------------------|
| Bug Fix | code-standards, quality-checklist | context-manager, refactoring-expert |
| New Feature | workflow-methodology, testing-framework | task-coordinator, workflow-orchestrator |
| Refactoring | code-standards, implementation-patterns | refactoring-expert, legacy-modernizer |
| Documentation | documentation-standards | api-documentation, technical-documentation |
| Testing | unit-tests, test-cases | performance-testing, mutation-testing |
| Infrastructure | cicd-integration | kubernetes-expert, terraform-specialist, cicd-architect |
| Database | code-standards | sql-expert |
| Dependencies | security | dependency-manager, dependency-security-audit |

### Efficiency Modes
- **Quick Mode** (simple fixes): Minimal docs, focus on core fix
- **Full Mode** (new projects): Complete architecture, comprehensive testing

### Workflow Skills (for complex tasks)
- **task-coordinator** - Break down multi-step implementations
- **context-manager** - Navigate large codebases
- **workflow-orchestrator** - Chain skills with quality gates

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
