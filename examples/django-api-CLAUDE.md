# Django REST API Project

A Django REST API project using Python 3.12+, Django 5.x, and Django REST Framework. Data persistence via PostgreSQL. Background tasks via Celery + Redis. Containerized with Docker Compose.

## Tech Stack
- **Language**: Python 3.12
- **Package Manager**: uv (or pip with requirements.txt)
- **Build**: N/A (interpreted)
- **Test**: pytest + pytest-django
- **Lint/Format**: ruff (lint + format), mypy (type checking)

## Project Layout
```
myproject/
  settings/         # base.py, development.py, production.py
  urls.py
  wsgi.py
apps/
  <app_name>/
    models.py
    views.py        # ViewSets preferred
    serializers.py
    urls.py
    tests/
      test_models.py
      test_views.py
    admin.py
    apps.py
tests/              # Integration and E2E tests
Dockerfile
docker-compose.yml
requirements/
  base.txt
  development.txt
  production.txt
```

## Key Commands
```bash
# Start dev server
python manage.py runserver

# Run tests
pytest --tb=short -q

# Lint and format
ruff check . && ruff format .

# Type check
mypy .

# Database migrations
python manage.py makemigrations && python manage.py migrate

# Docker dev environment
docker compose up -d
```

## Non-Obvious Tooling
- Use `select_related` and `prefetch_related` aggressively to avoid N+1 queries
- DRF ViewSets + Routers are preferred over function-based views
- Use `django-environ` for environment variable management; never hardcode secrets
- Celery tasks should be idempotent; always add `task_id` checks for deduplication
- Use `pytest-factory-boy` for test fixtures; avoid raw `Model.objects.create()` in tests
- Django Debug Toolbar is dev-only; ensure it is gated by `DEBUG=True`

## Python Conventions
- Type-annotate all function signatures (return types included)
- Use `@dataclass` or Pydantic models for data transfer objects outside the ORM layer
- Serializers must validate at the field level first, then cross-field in `validate()`
- Never use `filter()` in views without pagination — always apply `PageNumberPagination`
- Keep views thin: business logic belongs in service modules (`apps/<app>/services.py`)
- Authentication: use DRF `IsAuthenticated` permission class by default; document any public endpoints explicitly

## Communication Style
- Place punctuation outside quotation marks (logical punctuation)
- No em-dashes; use parentheses, commas, or separate sentences
- Professional teaching tone
- Never hard-wrap paragraph text at a fixed column width; write each paragraph or bullet point as a single continuous line and let the editor or terminal handle visual wrapping

## Critical Rules
- Verify work before marking complete
- Find root causes; no temporary fixes
- Destructive git commands require user confirmation
- Never add `Co-Authored-By` lines, AI attribution footers, or AI-generated signatures to commit messages
- **MANDATORY: Every Bash/shell command approval MUST be preceded by a one-sentence plain-language explanation** of what the command does and what its impact will be. This applies to ALL commands regardless of complexity. No exceptions.
- Ask clarifying questions before coding if requirements are ambiguous
- Never commit `.env` files or any file containing credentials

## Output Minimization
- Prefer `pytest -q` and `ruff --quiet` — report only counts, errors, and key results
- Summarize long command output; do not echo full migration or collectstatic logs

## Context References
- Skills: `.claude/skills/` (auto-activated by task context)
- Architecture: `.claude/context/architecture.md`
- Decisions: `.claude/memory/decisions.md`
- Rules: `.claude/rules/python/` (Python-specific coding standards)
- Agents: `.claude/agents/` (specialized subagents for code review, TDD, security)
