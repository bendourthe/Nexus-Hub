---
name: create-claude-md
description: Generate comprehensive CLAUDE.md configuration file for optimal Claude Code performance
version: 1.0.0
author: Benjamin Dourthe
language: Multi-language
category: Configuration
tags: [configuration, claude-md, setup, standards, best-practice]
priority: CRITICAL
based_on: Claude Code Best Practices 2025
---

# Create CLAUDE.md

Generate a comprehensive CLAUDE.md file - the single most important tool for guiding Claude Code's behavior in your project.

## When to Use This Skill

Use this skill when you need to:
- ✅ Set up a new project with Claude Code
- ✅ Define project-specific standards and patterns
- ✅ Establish team coding conventions
- ✅ Configure Claude's behavior for your tech stack
- ✅ Document bash commands and workflows
- ✅ Maintain consistency across team members
- ✅ Onboard new developers with AI assistance

**Every project using Claude Code should have a CLAUDE.md file.**

## What This Skill Does

The CLAUDE.md file is automatically read by Claude Code at the start of every session, providing persistent context without consuming conversation tokens.

### What Goes in CLAUDE.md

1. **Project Overview**: Architecture, tech stack, purpose
2. **Coding Standards**: Style guides, patterns, conventions
3. **Bash Commands**: Common operations, scripts, workflows
4. **Testing Procedures**: How to run tests, expected formats
5. **File Structure**: Directory organization, naming conventions
6. **Development Workflow**: Git flow, review process, deployment
7. **Architecture Decisions**: Key design choices and rationale
8. **Domain Context**: Business logic, terminology, constraints

### What CLAUDE.md Achieves

- 🎯 **Consistency**: All Claude sessions follow same standards
- ⚡ **Efficiency**: No need to repeat instructions every session
- 📚 **Knowledge Transfer**: Documents team practices
- 🛡️ **Quality**: Enforces standards automatically
- 🚀 **Onboarding**: New team members get instant context

## Prerequisites

- Claude Code installed and configured
- Project directory created
- Basic understanding of project requirements
- (Optional) Existing coding standards documentation

## Instructions

### Step 1: Gather Project Information

Before generating CLAUDE.md, collect:

1. **Language and Framework**
   - Primary language (Python, JavaScript, Java, etc.)
   - Framework (Django, React, Spring Boot, etc.)
   - Version requirements

2. **Architecture and Patterns**
   - Project structure (monolith, microservices, monorepo)
   - Design patterns in use
   - Key architectural decisions

3. **Standards and Conventions**
   - Code style guide (PEP 8, Airbnb, Google Style, etc.)
   - Naming conventions
   - File organization rules

4. **Common Operations**
   - Development server commands
   - Test commands
   - Build and deployment commands
   - Database migration commands

5. **Team Workflow**
   - Git branching strategy
   - PR/review process
   - CI/CD pipeline details

### Step 2: Generate CLAUDE.md

Use this skill with the gathered information:

```
"Use the create-claude-md skill to generate a CLAUDE.md file for this project.

Project Details:
- Language: [Python/JavaScript/Java/etc.]
- Framework: [Django/React/Spring/etc.]
- Type: [Web API/CLI tool/Library/etc.]
- Architecture: [Monolith/Microservices/etc.]

Key Standards:
- Style Guide: [PEP 8/Airbnb/Google/etc.]
- Testing: [pytest/Jest/JUnit/etc.]
- Documentation: [Sphinx/JSDoc/JavaDoc/etc.]

Common Commands:
- Dev server: [command]
- Run tests: [command]
- Build: [command]

Team Workflow:
- Git: [trunk-based/gitflow/etc.]
- CI/CD: [GitHub Actions/GitLab CI/etc.]

Generate a comprehensive CLAUDE.md file."
```

### Step 3: Review and Customize

Claude will generate a CLAUDE.md file. Review and customize:

**Check These Sections**:
- [ ] Project overview is accurate
- [ ] All bash commands are correct
- [ ] Coding standards match team preferences
- [ ] File structure reflects actual layout
- [ ] Testing procedures are complete
- [ ] Architecture decisions are documented

**Add Project-Specific Details**:
- Domain-specific terminology
- Business logic constraints
- API design principles
- Security requirements
- Performance targets

### Step 4: Place in Project Root

```bash
# CLAUDE.md must be in the project root directory
mv CLAUDE.md /path/to/project/root/

# Verify location
ls -la CLAUDE.md  # Should be at project root
```

### Step 5: Test Configuration

Start a new Claude Code session and verify it loads:

```
"What coding standards should I follow for this project?"
```

Expected response should reference CLAUDE.md contents:
```
"Based on the CLAUDE.md file, this project follows:
- [Style guide specified]
- [Testing framework specified]
- [Architecture patterns specified]"
```

### Step 6: Commit to Version Control

```bash
git add CLAUDE.md
git commit -m "Add Claude Code configuration"
git push
```

**Important**: CLAUDE.md should be version-controlled so all team members use the same configuration.

## CLAUDE.md Template Structure

### Minimal CLAUDE.md (Quick Start)

```markdown
# Project Name

## Tech Stack
- Language: Python 3.11
- Framework: FastAPI
- Database: PostgreSQL
- Testing: pytest

## Coding Standards
- Follow PEP 8
- Type hints required for all functions
- Docstrings for all public functions

## Common Commands
```bash
# Development
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
pip install -e ".[dev]"
uvicorn src.main:app --reload

# Testing
pytest tests/

# Linting
black src/ tests/
mypy src/
\`\`\`

## Project Structure
```
src/
  main.py           # FastAPI app entry point
  api/              # API route handlers
  models/           # Database models
  schemas/          # Pydantic schemas
tests/
  test_api.py       # API tests
```
```

### Comprehensive CLAUDE.md (Full Featured)

```markdown
# Project Name - [Brief Description]

## Table of Contents
1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Tech Stack](#tech-stack)
4. [Development Setup](#development-setup)
5. [Coding Standards](#coding-standards)
6. [Testing](#testing)
7. [Common Operations](#common-operations)
8. [Deployment](#deployment)
9. [Architecture Decisions](#architecture-decisions)

## Overview
[2-3 paragraphs describing project purpose, key features, and context]

## Architecture
- **Pattern**: [Microservices/Monolith/Serverless]
- **Data Flow**: [Request → API → Service → Database]
- **Key Components**:
  - API Layer: REST endpoints using FastAPI
  - Service Layer: Business logic
  - Data Layer: PostgreSQL with SQLAlchemy ORM

## Tech Stack
### Core
- **Language**: Python 3.11+
- **Framework**: FastAPI 0.104+
- **Database**: PostgreSQL 14+
- **Cache**: Redis 7+

### Development
- **Testing**: pytest, pytest-asyncio
- **Linting**: black, flake8, mypy
- **Docs**: Sphinx with autodoc

### Infrastructure
- **Container**: Docker + Docker Compose
- **CI/CD**: GitHub Actions
- **Hosting**: AWS ECS

## Development Setup

### Prerequisites
```bash
# Required
python 3.11+
postgresql 14+
redis 7+

# Optional (Docker alternative)
docker
docker-compose
```

### Local Setup
```bash
# 1. Clone and enter directory
git clone [repo-url]
cd project-name

# 2. Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Unix
# .venv\Scripts\activate  # Windows

# 3. Install dependencies
pip install -e ".[dev]"

# 4. Setup database
cp .env.example .env  # Edit with your values
alembic upgrade head

# 5. Run development server
uvicorn src.main:app --reload --port 8000
```

### Docker Setup (Alternative)
```bash
docker-compose up -d
docker-compose logs -f api
```

## Coding Standards

### Python Style
- **PEP 8 Compliance**: Enforced by black and flake8
- **Line Length**: 88 characters (black default)
- **Type Hints**: Required for all public functions
- **Docstrings**: Google style for all public APIs

### Naming Conventions
- **Functions**: `snake_case`
- **Classes**: `PascalCase`
- **Constants**: `UPPER_SNAKE_CASE`
- **Private**: Prefix with underscore (`_private_function`)

### Import Organization
1. Standard library
2. Third-party packages
3. Local application imports

```python
# Example
import os
from typing import List

import fastapi
from sqlalchemy import select

from src.models import User
from src.schemas import UserSchema
```

### Error Handling
- Use specific exceptions, not bare `except:`
- Log errors with context
- Return meaningful error messages to clients
- Don't expose internal details in API responses

### Testing Standards
- **Coverage Target**: 80%+
- **Test Naming**: `test_[function]_[scenario]_[expected]`
- **Structure**: Arrange-Act-Assert pattern
- **Fixtures**: Use pytest fixtures for common setup

## Testing

### Running Tests
```bash
# All tests
pytest

# With coverage
pytest --cov=src --cov-report=html

# Specific test file
pytest tests/test_api.py

# Specific test function
pytest tests/test_api.py::test_create_user_success

# Watch mode
pytest-watch

# Parallel execution
pytest -n auto
```

### Test Structure
```
tests/
  conftest.py           # Shared fixtures
  test_api/
    test_users.py       # User endpoint tests
    test_auth.py        # Auth endpoint tests
  test_services/
    test_user_service.py
  test_models/
    test_user_model.py
```

### Writing Tests
```python
def test_function_scenario_expected():
    """Test [function] when [scenario] should [expected outcome]."""
    # Arrange
    user = create_test_user()

    # Act
    result = process_user(user)

    # Assert
    assert result.status == "active"
    assert result.email_verified is True
```

## Common Operations

### Development
```bash
# Start development server
uvicorn src.main:app --reload

# Format code
black src/ tests/
isort src/ tests/

# Lint
flake8 src/ tests/
mypy src/

# Type check
mypy src/
```

### Database
```bash
# Create migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1

# Reset database (CAUTION)
alembic downgrade base
alembic upgrade head
```

### Docker
```bash
# Build and start
docker-compose up --build

# View logs
docker-compose logs -f [service-name]

# Execute command in container
docker-compose exec api bash

# Stop all services
docker-compose down

# Clean up volumes
docker-compose down -v
```

### Git Workflow
```bash
# Start new feature
git checkout main
git pull origin main
git checkout -b feature/description

# Commit changes
git add .
git commit -m "feat: description"

# Push and create PR
git push origin feature/description
# Then create PR on GitHub

# Update branch with main
git checkout main
git pull origin main
git checkout feature/description
git rebase main
```

## Deployment

### CI/CD Pipeline
- **Trigger**: Push to main or PR creation
- **Steps**:
  1. Lint and type check
  2. Run tests with coverage
  3. Build Docker image
  4. Push to ECR (main only)
  5. Deploy to staging (main only)
  6. Deploy to production (tags only)

### Manual Deployment
```bash
# Build production image
docker build -t project-name:latest .

# Tag for registry
docker tag project-name:latest [registry]/project-name:latest

# Push to registry
docker push [registry]/project-name:latest

# Deploy (depends on platform)
[deployment-specific-commands]
```

## Architecture Decisions

### ADR 001: FastAPI over Django
**Decision**: Use FastAPI for API layer
**Rationale**:
- High performance (async support)
- Automatic OpenAPI documentation
- Modern Python features (type hints)
- Smaller codebase for API-only service

### ADR 002: PostgreSQL for Primary Database
**Decision**: PostgreSQL as primary datastore
**Rationale**:
- ACID compliance required
- Complex query support needed
- JSON support for flexible schema
- Team expertise and tooling

### ADR 003: Redis for Caching
**Decision**: Redis for caching and rate limiting
**Rationale**:
- Fast in-memory operations
- Built-in data structures
- Pub/sub for real-time features
- Proven reliability at scale

## Domain Context

### Business Logic
- **Users**: Three types (admin, member, guest)
- **Permissions**: Role-based access control
- **Billing**: Monthly subscription model
- **Data**: GDPR compliance required

### Terminology
- **Workspace**: Top-level organization container
- **Project**: Collection of related resources
- **Resource**: Individual managed item
- **Member**: User with workspace access

### Constraints
- **Performance**: 95th percentile < 200ms
- **Availability**: 99.9% uptime SLA
- **Security**: SOC 2 compliance required
- **Data**: EU data residency required

---

Last Updated: [Date]
Maintained by: [Team Name]
```

## Language-Specific Templates

### For Python Projects
Include:
- Virtual environment setup
- pip/poetry commands
- pytest configuration
- Black/isort/mypy commands
- Type hints requirements

### For JavaScript Projects
Include:
- npm/yarn commands
- ESLint/Prettier configuration
- Jest/Cypress test commands
- Build and bundle commands
- Node version requirements

### For Java Projects
Include:
- Maven/Gradle commands
- JUnit test execution
- Spring Boot profiles
- Build and package commands
- Java version requirements

### For C# Projects
Include:
- dotnet CLI commands
- NUnit/xUnit test execution
- Solution/project structure
- NuGet package management
- .NET version requirements

## Advanced: Dynamic CLAUDE.md

For projects with multiple environments or configurations:

```markdown
# Environment-Specific Commands

## Development
```bash
export ENV=development
npm run dev
```

## Staging
```bash
export ENV=staging
npm run build
npm run deploy:staging
```

## Production
```bash
export ENV=production
npm run build
npm run deploy:prod
```
```

## Common Mistakes to Avoid

### ❌ Mistake 1: Too Vague
```markdown
# CLAUDE.md
Use Python best practices.
Run tests before committing.
```

**✅ Correct**:
```markdown
# CLAUDE.md
Follow PEP 8 with 88-char lines (black formatter).
Run `pytest tests/ --cov=src` and ensure 80%+ coverage.
```

### ❌ Mistake 2: Missing Commands
```markdown
Test the code before committing.
```

**✅ Correct**:
```markdown
```bash
# Run full test suite
pytest tests/ -v

# Run with coverage
pytest --cov=src --cov-report=html

# Must pass before commit
```
```

### ❌ Mistake 3: Outdated Information
- CLAUDE.md not updated when dependencies change
- Old commands that no longer work
- References to removed features

**✅ Solution**: Treat CLAUDE.md as living documentation, update alongside code changes.

## Success Criteria

After creating CLAUDE.md, verify:

- [ ] File exists in project root directory
- [ ] All bash commands are accurate and tested
- [ ] Coding standards are clearly specified
- [ ] File structure is documented
- [ ] Testing procedures are complete
- [ ] Architecture decisions are captured
- [ ] Domain context is explained
- [ ] Common operations are documented
- [ ] File is committed to version control
- [ ] Team members have reviewed and approved
- [ ] Claude Code successfully loads and follows guidelines

## Integration with Other Skills

**Use Before**:
- `setup-[language]-system-prompt`: Establishes foundation
- `plan-before-code`: Defines workflow

**Use With**:
- Any development work in the project
- All other skills reference CLAUDE.md

**Update When**:
- Dependencies change
- Coding standards evolve
- New workflows are established
- Architecture decisions are made

## Maintenance

### Keep CLAUDE.md Updated

Update when:
- New dependencies added
- Commands change
- Standards evolve
- New team practices emerge
- Architecture changes

### Review Periodically

- Monthly: Review for outdated information
- Quarterly: Major review and cleanup
- After major releases: Update with new patterns
- When onboarding: Get fresh perspective on clarity

## Additional Resources

- [Claude Code Documentation](https://docs.claude.com/claude-code)
- [CLAUDE.md Best Practices](https://www.anthropic.com/engineering/claude-code-best-practices)
- [Example CLAUDE.md Files](https://github.com/search?q=CLAUDE.md)

---

**Version**: 1.0.0
**Last Updated**: October 2025
**Based on**: Claude Code Best Practices 2025
**Priority**: 🔥 CRITICAL - Essential for every Claude Code project
